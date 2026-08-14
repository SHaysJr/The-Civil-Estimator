from db import connect
from domain import DEPTH_BANDS, CompanionSpec, build_companion_lines, compute_bedding, depth_adjusted_unit_cost, production_for_depth


def get_primary_line(line_item_id):
    with connect() as conn:
        row = conn.execute('SELECT * FROM line_items WHERE id=?', (line_item_id,)).fetchone()
        if not row:
            raise ValueError('Line item not found.')
        if row['auto_generated']:
            raise ValueError('Automatic companion items are edited through their primary item.')
        return row


def _bedding_values(conn, material, quantity, bedding_rule_id, bedding_unit_cost_per_cy):
    if bedding_rule_id in (None, ''):
        return 0.0, 0.0, 0.0, None, None
    rule = conn.execute('SELECT * FROM bedding_rules WHERE id=?', (int(bedding_rule_id),)).fetchone()
    if not rule:
        raise ValueError('Bedding rule not found.')
    if rule['prohibited']:
        raise ValueError(f"This selection is prohibited by the chosen rule: {rule['bedding_class']}")
    pipe_type = (material['pipe_type'] or '').upper()
    rule_material = (rule['pipe_material'] or '').upper()
    if pipe_type and pipe_type not in rule_material:
        raise ValueError('The selected bedding rule does not match this pipe material.')
    if material['nominal_diameter_in'] and not rule['applies_all_sizes']:
        if abs(float(material['nominal_diameter_in']) - float(rule['nominal_diameter_in'])) > 0.01:
            raise ValueError('The selected bedding rule does not match this pipe diameter.')
    unit_cost = float(bedding_unit_cost_per_cy or material['bedding_unit_cost_per_cy'] or 0)
    result = compute_bedding(
        length_lf=quantity, pipe_od_in=rule['pipe_od_in'], depth_below_in=rule['depth_below_in'],
        haunch_to_springline=bool(rule['haunch_to_springline']), envelope_above_crown_in=rule['envelope_above_crown_in'],
        trench_side_clearance_in=rule['trench_side_clearance_in'], unit_cost_per_cy=unit_cost,
    )
    confidence = rule['data_confidence']
    warning = None
    if confidence and confidence.lower().startswith('assumed'):
        warning = 'VERIFY BEFORE BID: source workbook marks this bedding geometry as assumed.'
    return float(result.total_cost), float(result.quantity_cy), unit_cost, confidence, warning


def sync_line_companions(conn, parent):
    existing = conn.execute(
        'SELECT * FROM line_items WHERE parent_line_item_id=? AND auto_generated=1 ORDER BY id', (parent['id'],)
    ).fetchall()
    preserved = {int(row['material_rate_id']): row['unit_cost'] for row in existing if row['material_rate_id']}
    rules = conn.execute(
        '''SELECT mc.ratio, c.* FROM material_companions mc
           JOIN material_rates c ON c.id=mc.companion_material_id
           WHERE mc.material_id=? ORDER BY mc.id''', (parent['material_rate_id'],)
    ).fetchall()
    specs = [CompanionSpec(
        material_id=r['id'], description=r['name'], unit=r['unit'], ratio=r['ratio'], unit_cost=r['unit_cost'],
        pipe_type=r['pipe_type'], nominal_diameter_in=r['nominal_diameter_in'], is_tax_exempt=bool(r['is_tax_exempt'])
    ) for r in rules]
    generated = build_companion_lines(parent['quantity'], specs, preserved)
    conn.execute('DELETE FROM line_items WHERE parent_line_item_id=? AND auto_generated=1', (parent['id'],))
    for item in generated:
        conn.execute(
            '''INSERT INTO line_items(section_id,material_rate_id,description,unit,quantity,unit_cost,production_rate,bedding_cost,
               pipe_type,nominal_diameter_in,is_tax_exempt,auto_generated,parent_line_item_id,companion_ratio)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (parent['section_id'], item.material_id, item.description, item.unit, float(item.quantity), float(item.unit_cost),
             None, 0, item.pipe_type, float(item.nominal_diameter_in) if item.nominal_diameter_in is not None else None,
             int(item.is_tax_exempt), 1, parent['id'], float(item.ratio)),
        )
    return len(generated)


def update_line_item(line_item_id, quantity, unit_cost_override='', production_rate_override='', depth_band='',
                     bedding_rule_id='', bedding_unit_cost_per_cy=''):
    quantity = float(quantity)
    if quantity < 0:
        raise ValueError('Quantity cannot be negative.')
    with connect() as conn:
        line = conn.execute('SELECT * FROM line_items WHERE id=?', (line_item_id,)).fetchone()
        if not line:
            raise ValueError('Line item not found.')
        if line['auto_generated']:
            raise ValueError('Automatic companion items are edited through their primary item.')
        material = conn.execute('SELECT * FROM material_rates WHERE id=?', (line['material_rate_id'],)).fetchone()
        if not material:
            raise ValueError('Catalog material not found.')
        if material['is_depth_priced']:
            if depth_band not in DEPTH_BANDS:
                raise ValueError('Choose a depth band for this pipe item.')
            production = production_for_depth(material, depth_band)
            if production in (None, 0):
                raise ValueError(f'No production rate is available for depth band {depth_band}.')
            unit_cost = depth_adjusted_unit_cost(material['unit_cost'], depth_band)
        else:
            depth_band = None
            production = line['production_rate']
            unit_cost = line['unit_cost']
        if unit_cost_override not in (None, ''):
            unit_cost = float(unit_cost_override)
        if production_rate_override not in (None, ''):
            production = float(production_rate_override)
        bedding_cost, bedding_qty, bedding_uc, confidence, warning = _bedding_values(
            conn, material, quantity, bedding_rule_id, bedding_unit_cost_per_cy
        )
        conn.execute(
            '''UPDATE line_items SET quantity=?,unit_cost=?,production_rate=?,bedding_cost=?,depth_band=?,bedding_rule_id=?,
               bedding_quantity_cy=?,bedding_unit_cost_per_cy=?,bedding_confidence=?,bedding_warning=? WHERE id=?''',
            (quantity, unit_cost, production, bedding_cost, depth_band,
             int(bedding_rule_id) if bedding_rule_id not in (None, '') else None, bedding_qty, bedding_uc,
             confidence, warning, line_item_id),
        )
        parent = conn.execute('SELECT * FROM line_items WHERE id=?', (line_item_id,)).fetchone()
        count = sync_line_companions(conn, parent)
        conn.commit()
        return {'section_id': parent['section_id'], 'companions_synced': count}
