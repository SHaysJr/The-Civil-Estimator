from decimal import Decimal

from db import connect
from domain import (
    CrewMember,
    DEPTH_BANDS,
    Equipment,
    companion_quantity,
    compute_aggregate_estimate,
    compute_bedding,
    compute_section,
    depth_adjusted_unit_cost,
    production_for_depth,
)


def list_projects():
    with connect() as conn:
        return conn.execute('SELECT * FROM projects ORDER BY updated_at DESC, id DESC').fetchall()


def get_project(project_id):
    with connect() as conn:
        return conn.execute('SELECT * FROM projects WHERE id=?', (project_id,)).fetchone()


def create_project(data):
    with connect() as conn:
        cur = conn.execute(
            '''INSERT INTO projects
            (name,customer,address_line,city,state,zip_code,estimator,bid_date,date_due,description,status,tax_rate,overhead_rate,profit_rate,bedding_jurisdiction)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                data['name'], data.get('customer', ''), data.get('address_line', ''), data.get('city', ''),
                data.get('state', ''), data.get('zip_code', ''), data.get('estimator', ''), data.get('bid_date', ''),
                data.get('date_due', ''), data.get('description', ''), data.get('status', 'active'),
                data.get('tax_rate', .10), data.get('overhead_rate', .10), data.get('profit_rate', .20),
                data.get('bedding_jurisdiction', ''),
            ),
        )
        conn.commit()
        return cur.lastrowid


def update_project(project_id, data):
    with connect() as conn:
        conn.execute(
            '''UPDATE projects SET name=?,customer=?,address_line=?,city=?,state=?,zip_code=?,estimator=?,bid_date=?,date_due=?,description=?,status=?,tax_rate=?,overhead_rate=?,profit_rate=?,bedding_jurisdiction=?,updated_at=CURRENT_TIMESTAMP WHERE id=?''',
            (
                data['name'], data.get('customer', ''), data.get('address_line', ''), data.get('city', ''),
                data.get('state', ''), data.get('zip_code', ''), data.get('estimator', ''), data.get('bid_date', ''),
                data.get('date_due', ''), data.get('description', ''), data.get('status', 'active'),
                data.get('tax_rate', .10), data.get('overhead_rate', .10), data.get('profit_rate', .20),
                data.get('bedding_jurisdiction', ''), project_id,
            ),
        )
        conn.commit()


def project_sections(project_id):
    with connect() as conn:
        return conn.execute('SELECT * FROM sections WHERE project_id=? ORDER BY sort_order,id', (project_id,)).fetchall()


def add_section(project_id, scope_name):
    with connect() as conn:
        cur = conn.execute('INSERT INTO sections(project_id,scope_name) VALUES (?,?)', (project_id, scope_name))
        conn.commit()
        return cur.lastrowid


def get_section(section_id):
    with connect() as conn:
        return conn.execute('SELECT * FROM sections WHERE id=?', (section_id,)).fetchone()


def catalog_materials(scope=None):
    with connect() as conn:
        if scope:
            return conn.execute('SELECT * FROM material_rates WHERE scope=? ORDER BY name', (scope,)).fetchall()
        return conn.execute('SELECT * FROM material_rates ORDER BY scope,name').fetchall()


def catalog_materials_with_companions(scope=None):
    rows = catalog_materials(scope)
    with connect() as conn:
        companion_rows = conn.execute(
            '''SELECT mc.material_id, mc.ratio, c.id companion_id, c.name companion_name, c.unit companion_unit
               FROM material_companions mc
               JOIN material_rates c ON c.id=mc.companion_material_id
               ORDER BY mc.material_id, c.name'''
        ).fetchall()
    grouped = {}
    for companion in companion_rows:
        grouped.setdefault(companion['material_id'], []).append(dict(companion))
    result = []
    for row in rows:
        item = dict(row)
        item['companions'] = grouped.get(row['id'], [])
        result.append(item)
    return result


def companion_rules():
    with connect() as conn:
        return conn.execute(
            '''SELECT mc.id, m.scope, m.name material_name, m.unit material_unit,
                      c.name companion_name, c.unit companion_unit, mc.ratio
               FROM material_companions mc
               JOIN material_rates m ON m.id=mc.material_id
               JOIN material_rates c ON c.id=mc.companion_material_id
               ORDER BY m.scope, m.name, c.name'''
        ).fetchall()


def labor_catalog():
    with connect() as conn:
        return conn.execute('SELECT * FROM labor_rates ORDER BY role_name').fetchall()


def equipment_catalog():
    with connect() as conn:
        return conn.execute('SELECT * FROM equipment_rates ORDER BY description').fetchall()


def add_crew(section_id, labor_rate_id, count):
    with connect() as conn:
        r = conn.execute('SELECT * FROM labor_rates WHERE id=?', (labor_rate_id,)).fetchone()
        if not r:
            raise ValueError('Labor rate not found.')
        conn.execute(
            '''INSERT INTO section_crew(section_id,labor_rate_id,count,role_name_snapshot,reg_hourly_rate_snapshot,ot_hourly_rate_snapshot)
               VALUES (?,?,?,?,?,?)''',
            (section_id, labor_rate_id, count, r['role_name'], r['reg_hourly_rate'], r['ot_hourly_rate']),
        )
        conn.commit()


def add_equipment(section_id, equipment_rate_id):
    with connect() as conn:
        r = conn.execute('SELECT * FROM equipment_rates WHERE id=?', (equipment_rate_id,)).fetchone()
        if not r:
            raise ValueError('Equipment rate not found.')
        conn.execute(
            '''INSERT INTO section_equipment(section_id,equipment_rate_id,machine_id_snapshot,description_snapshot,day_rate_snapshot,week_rate_snapshot,month_rate_snapshot,fuel_capacity_gal_snapshot,fuel_price_per_gal_snapshot)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            (
                section_id, equipment_rate_id, r['machine_id'], r['description'], r['day_rate'], r['week_rate'],
                r['month_rate'], r['fuel_capacity_gal'], r['fuel_price_per_gal'],
            ),
        )
        conn.commit()


def bedding_jurisdictions(state=None):
    with connect() as conn:
        if state:
            return conn.execute(
                'SELECT DISTINCT state,jurisdiction FROM bedding_rules WHERE state=? ORDER BY jurisdiction',
                (state.upper(),),
            ).fetchall()
        return conn.execute('SELECT DISTINCT state,jurisdiction FROM bedding_rules ORDER BY state,jurisdiction').fetchall()


def bedding_rules_for(*, state=None, jurisdiction=None, system_type=None, pipe_material=None, nominal_diameter=None):
    sql = 'SELECT * FROM bedding_rules WHERE 1=1'
    args = []
    if state:
        sql += ' AND state=?'
        args.append(state.upper())
    if jurisdiction:
        sql += ' AND jurisdiction=?'
        args.append(jurisdiction)
    if system_type:
        sql += ' AND system_type=?'
        args.append(system_type)
    if pipe_material:
        sql += ' AND pipe_material=?'
        args.append(pipe_material)
    if nominal_diameter not in (None, ''):
        sql += ' AND (nominal_diameter_in=? OR applies_all_sizes=1)'
        args.append(float(nominal_diameter))
    sql += ' ORDER BY prohibited DESC, jurisdiction,bedding_class,nominal_diameter_in'
    with connect() as conn:
        return conn.execute(sql, args).fetchall()


def get_bedding_rule(rule_id):
    if not rule_id:
        return None
    with connect() as conn:
        return conn.execute('SELECT * FROM bedding_rules WHERE id=?', (rule_id,)).fetchone()


def add_line_from_catalog(
    section_id,
    material_rate_id,
    quantity,
    unit_cost_override=None,
    production_rate_override=None,
    depth_band=None,
    bedding_rule_id=None,
    bedding_unit_cost_per_cy=None,
):
    with connect() as conn:
        r = conn.execute('SELECT * FROM material_rates WHERE id=?', (material_rate_id,)).fetchone()
        if not r:
            raise ValueError('Material rate not found.')

        if r['is_depth_priced']:
            if depth_band not in DEPTH_BANDS:
                raise ValueError('Choose a depth band for this pipe item.')
            production = production_for_depth(r, depth_band)
            if production in (None, 0):
                raise ValueError(f'No production rate is available for depth band {depth_band}.')
            unit_cost = depth_adjusted_unit_cost(r['unit_cost'], depth_band)
        else:
            unit_cost = r['unit_cost']
            production = r['production_rate']

        if unit_cost_override not in (None, ''):
            unit_cost = float(unit_cost_override)
        if production_rate_override not in (None, ''):
            production = float(production_rate_override)

        bedding_cost = 0.0
        bedding_qty = 0.0
        bedding_unit_cost = 0.0
        bedding_confidence = None
        bedding_warning = None

        if bedding_rule_id not in (None, ''):
            rule = conn.execute('SELECT * FROM bedding_rules WHERE id=?', (int(bedding_rule_id),)).fetchone()
            if not rule:
                raise ValueError('Bedding rule not found.')
            if rule['prohibited']:
                raise ValueError(f"This selection is prohibited by the chosen rule: {rule['bedding_class']}")

            pipe_type = (r['pipe_type'] or '').upper()
            rule_material = (rule['pipe_material'] or '').upper()
            if pipe_type and pipe_type not in rule_material:
                raise ValueError('The selected bedding rule does not match this pipe material.')
            if r['nominal_diameter_in'] and not rule['applies_all_sizes']:
                if abs(float(r['nominal_diameter_in']) - float(rule['nominal_diameter_in'])) > 0.01:
                    raise ValueError('The selected bedding rule does not match this pipe diameter.')

            bedding_unit_cost = float(bedding_unit_cost_per_cy or r['bedding_unit_cost_per_cy'] or 0)
            bedding = compute_bedding(
                length_lf=quantity,
                pipe_od_in=rule['pipe_od_in'],
                depth_below_in=rule['depth_below_in'],
                haunch_to_springline=bool(rule['haunch_to_springline']),
                envelope_above_crown_in=rule['envelope_above_crown_in'],
                trench_side_clearance_in=rule['trench_side_clearance_in'],
                unit_cost_per_cy=bedding_unit_cost,
            )
            bedding_qty = float(bedding.quantity_cy)
            bedding_cost = float(bedding.total_cost)
            bedding_confidence = rule['data_confidence']
            if bedding_confidence and bedding_confidence.lower().startswith('assumed'):
                bedding_warning = 'VERIFY BEFORE BID: source workbook marks this bedding geometry as assumed.'

        cur = conn.execute(
            '''INSERT INTO line_items(
               section_id,material_rate_id,description,unit,quantity,unit_cost,production_rate,bedding_cost,depth_band,
               bedding_rule_id,bedding_quantity_cy,bedding_unit_cost_per_cy,bedding_confidence,bedding_warning,
               pipe_type,nominal_diameter_in,is_tax_exempt,auto_generated,parent_line_item_id,companion_ratio)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                section_id, material_rate_id, r['name'], r['unit'], quantity, unit_cost, production, bedding_cost,
                depth_band, int(bedding_rule_id) if bedding_rule_id not in (None, '') else None, bedding_qty,
                bedding_unit_cost, bedding_confidence, bedding_warning, r['pipe_type'], r['nominal_diameter_in'],
                r['is_tax_exempt'], 0, None, None,
            ),
        )
        parent_id = cur.lastrowid

        companions = conn.execute(
            '''SELECT mc.ratio, c.* FROM material_companions mc
               JOIN material_rates c ON c.id=mc.companion_material_id
               WHERE mc.material_id=? ORDER BY mc.id''',
            (material_rate_id,),
        ).fetchall()
        for companion in companions:
            companion_qty = float(companion_quantity(quantity, companion['ratio'], companion['unit']))
            conn.execute(
                '''INSERT INTO line_items(
                   section_id,material_rate_id,description,unit,quantity,unit_cost,production_rate,bedding_cost,
                   pipe_type,nominal_diameter_in,is_tax_exempt,auto_generated,parent_line_item_id,companion_ratio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (
                    section_id, companion['id'], companion['name'], companion['unit'], companion_qty,
                    companion['unit_cost'], None, 0, companion['pipe_type'], companion['nominal_diameter_in'],
                    companion['is_tax_exempt'], 1, parent_id, companion['ratio'],
                ),
            )

        conn.commit()
        return {'line_item_id': parent_id, 'companions_added': len(companions)}


def app_settings():
    with connect() as conn:
        return conn.execute('SELECT * FROM app_settings WHERE id=1').fetchone()


def aggregate_materials():
    with connect() as conn:
        return conn.execute('SELECT * FROM dirt_aggregate_rates ORDER BY name').fetchall()


def get_aggregate_material(material_id):
    with connect() as conn:
        return conn.execute('SELECT * FROM dirt_aggregate_rates WHERE id=?', (material_id,)).fetchone()


def aggregate_material_form(data):
    name = (data.get('name') or '').strip()
    if not name:
        raise ValueError('Material name is required.')
    try:
        tons_per_cy = float(data.get('tons_per_cy'))
    except (TypeError, ValueError):
        raise ValueError('Conversion rate (tons per cubic yard) must be a number.')
    if tons_per_cy <= 0:
        raise ValueError('Conversion rate (tons per cubic yard) must be greater than zero.')
    return {
        'name': name,
        'per_ton_cost': float(data.get('per_ton_cost') or 0),
        'per_ton_delivery_cost': float(data.get('per_ton_delivery_cost') or 0),
        'fuel_surcharge_applies': 1 if data.get('fuel_surcharge_applies') else 0,
        'tons_per_cy': tons_per_cy,
    }


def add_aggregate_material(data):
    row = aggregate_material_form(data)
    with connect() as conn:
        cur = conn.execute(
            '''INSERT INTO dirt_aggregate_rates(name,per_ton_cost,per_ton_delivery_cost,fuel_surcharge_applies,tons_per_cy)
               VALUES (?,?,?,?,?)''',
            (row['name'], row['per_ton_cost'], row['per_ton_delivery_cost'], row['fuel_surcharge_applies'], row['tons_per_cy']),
        )
        conn.commit()
        return cur.lastrowid


def update_aggregate_material(material_id, data):
    row = aggregate_material_form(data)
    with connect() as conn:
        conn.execute(
            '''UPDATE dirt_aggregate_rates SET name=?,per_ton_cost=?,per_ton_delivery_cost=?,fuel_surcharge_applies=?,tons_per_cy=?
               WHERE id=?''',
            (row['name'], row['per_ton_cost'], row['per_ton_delivery_cost'], row['fuel_surcharge_applies'], row['tons_per_cy'], material_id),
        )
        conn.commit()


def compute_aggregate_calculator(*, area_sqft, depth_in, material_id=None, tons_per_cy_override=None):
    """Square footage -> cubic yards -> tons/cost, using a material's conversion (companion) rate.

    Pass ``material_id`` to price against a saved material's rates, ``tons_per_cy_override``
    to swap in a different conversion rate for that same material's pricing (e.g. a supplier
    quotes a different yield), or both to price a one-off rate without touching the catalog.
    """
    material = get_aggregate_material(material_id) if material_id not in (None, '') else None
    if material_id not in (None, '') and not material:
        raise ValueError('Material not found.')

    if tons_per_cy_override not in (None, ''):
        tons_per_cy = float(tons_per_cy_override)
    elif material:
        tons_per_cy = material['tons_per_cy']
    else:
        raise ValueError('Choose a material or enter a conversion rate.')

    settings = app_settings()
    fuel_surcharge_per_ton = settings['fuel_surcharge_per_ton'] if settings else 0

    estimate = compute_aggregate_estimate(
        area_sqft=area_sqft,
        depth_in=depth_in,
        tons_per_cy=tons_per_cy,
        per_ton_cost=material['per_ton_cost'] if material else 0,
        per_ton_delivery_cost=material['per_ton_delivery_cost'] if material else 0,
        fuel_surcharge_per_ton=fuel_surcharge_per_ton,
        fuel_surcharge_applies=bool(material['fuel_surcharge_applies']) if material else False,
    )
    return {'material': material, 'estimate': estimate}


def delete_record(table, record_id):
    allowed = {'sections', 'section_crew', 'section_equipment', 'line_items', 'dirt_aggregate_rates'}
    if table not in allowed:
        raise ValueError('Invalid delete target.')
    with connect() as conn:
        if table == 'line_items':
            conn.execute('DELETE FROM line_items WHERE parent_line_item_id=?', (record_id,))
        conn.execute(f'DELETE FROM {table} WHERE id=?', (record_id,))
        conn.commit()


def compute_section_from_db(section_id):
    with connect() as conn:
        section = conn.execute('SELECT * FROM sections WHERE id=?', (section_id,)).fetchone()
        if not section:
            return None
        project = conn.execute('SELECT * FROM projects WHERE id=?', (section['project_id'],)).fetchone()
        crew_rows = conn.execute('SELECT * FROM section_crew WHERE section_id=? ORDER BY id', (section_id,)).fetchall()
        equip_rows = conn.execute('SELECT * FROM section_equipment WHERE section_id=? ORDER BY id', (section_id,)).fetchall()
        line_rows = conn.execute(
            '''SELECT li.*, br.jurisdiction AS bedding_jurisdiction_name,
               br.bedding_class AS bedding_class_name, br.bedding_material_spec, br.compaction_requirement,
               br.source_document AS bedding_source_document, parent.description AS parent_description
               FROM line_items li
               LEFT JOIN bedding_rules br ON br.id=li.bedding_rule_id
               LEFT JOIN line_items parent ON parent.id=li.parent_line_item_id
               WHERE li.section_id=? ORDER BY li.sort_order,li.id''',
            (section_id,),
        ).fetchall()

    crew = [
        CrewMember.make(r['role_name_snapshot'], r['count'], r['reg_hourly_rate_snapshot'], r['ot_hourly_rate_snapshot'])
        for r in crew_rows
    ]
    equipment = [
        Equipment.make(
            r['machine_id_snapshot'], r['description_snapshot'], r['day_rate_snapshot'], r['week_rate_snapshot'],
            r['month_rate_snapshot'], r['fuel_capacity_gal_snapshot'], r['fuel_price_per_gal_snapshot'],
        )
        for r in equip_rows
    ]
    lines = [dict(r) for r in line_rows]
    profit_rate = section['profit_rate'] if section['profit_rate'] is not None else project['profit_rate']
    result = compute_section(
        scope_name=section['scope_name'], lines=lines, crew=crew, equipment=equipment,
        overhead_rate=project['overhead_rate'], profit_rate=profit_rate, tax_rate=project['tax_rate'],
    )
    return {
        'section': section,
        'project': project,
        'crew_rows': crew_rows,
        'equipment_rows': equip_rows,
        'line_rows': line_rows,
        'result': result,
    }


def compute_project(project_id):
    project = get_project(project_id)
    section_rows = project_sections(project_id)
    computed = [compute_section_from_db(s['id']) for s in section_rows]
    total = sum((c['result'].total for c in computed), Decimal('0'))
    taxed = sum((c['result'].taxed_total for c in computed), Decimal('0'))
    direct = sum((c['result'].direct_cost for c in computed), Decimal('0'))
    days = sum((c['result'].days for c in computed), Decimal('0'))
    return {'project': project, 'sections': computed, 'direct': direct, 'total': total, 'taxed_total': taxed, 'days': days}
