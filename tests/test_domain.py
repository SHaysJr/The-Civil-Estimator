from decimal import Decimal
from domain.labor import CrewMember, crew_daily_cost
from domain.equipment import Equipment, equipment_cost
from domain.costing import compute_line
from domain.section import compute_section


def test_crew_daily_cost():
    crew=[CrewMember.make('Supervisor',1,40.50,60.75)]
    assert crew_daily_cost(crew)==Decimal('445.50')


def test_equipment_day_tier_and_fuel():
    item=Equipment.make('EX','Excavator',600,1800,5400,100,.60)
    result=equipment_cost(item,2)
    assert result['tier']=='day'
    assert result['rental']==Decimal('1200.00')
    assert result['fuel']==Decimal('120.00')
    assert result['total']==Decimal('1320.00')


def test_legacy_markup_logic_and_tax_variant():
    r=compute_line(description='x',unit='EA',quantity=1,unit_cost=100,production_rate=None,
                   overhead_rate=.10,profit_rate=.20,tax_rate=.10)
    assert r.subtotal==Decimal('100.00')
    assert r.overhead==Decimal('10.00')
    assert r.profit==Decimal('20.00')
    assert r.total==Decimal('130.00')
    assert r.taxed_subtotal==Decimal('110.00')
    assert r.taxed_total==Decimal('143.00')


def test_section_allocates_labor_and_equipment_by_days():
    crew=[CrewMember.make('Labor',1,10,15)] # 8*10+2*15 = 110/day
    eq=[Equipment.make('E','Eq',100,300,900,0,0)]
    lines=[
        {'description':'A','unit':'LF','quantity':100,'unit_cost':1,'production_rate':100},
        {'description':'B','unit':'LF','quantity':200,'unit_cost':1,'production_rate':100},
    ]
    s=compute_section(scope_name='Test',lines=lines,crew=crew,equipment=eq,overhead_rate=0,profit_rate=0,tax_rate=0)
    assert s.days==Decimal('3')
    assert s.crew_daily_cost==Decimal('110.00')
    assert s.equipment_total==Decimal('300.00')
    assert s.line_results[0].labor==Decimal('110.00')
    assert s.line_results[1].labor==Decimal('220.00')
    assert s.line_results[0].equipment==Decimal('100.00')
    assert s.line_results[1].equipment==Decimal('200.00')

from domain.bedding import compute_bedding, bedding_volume_per_lf_cf
from domain.depth_pricing import depth_adjusted_unit_cost


def test_bedding_geometry_matches_ms_workbook_example():
    # MS workbook MDOT baseline, 12-in RCP: OD 16.5, 6-in bedding,
    # haunch to springline, 18-in side clearance.
    per_lf = bedding_volume_per_lf_cf(
        pipe_od_in=16.5, depth_below_in=6, haunch_to_springline=True,
        envelope_above_crown_in=0, trench_side_clearance_in=18,
    )
    assert abs(per_lf - Decimal('4.45286579866335')) < Decimal('0.0000001')
    result = compute_bedding(
        length_lf=100, pipe_od_in=16.5, depth_below_in=6,
        haunch_to_springline=True, envelope_above_crown_in=0,
        trench_side_clearance_in=18, unit_cost_per_cy=50,
    )
    assert abs(result.quantity_cy - Decimal('16.492095550605')) < Decimal('0.000001')
    assert result.total_cost == Decimal('824.60')


def test_depth_pricing_legacy_increment():
    assert depth_adjusted_unit_cost(10, '0-6') == 10.0
    assert depth_adjusted_unit_cost(10, '10-12') == 11.5

from domain.assemblies import companion_quantity


def test_companion_quantity_fractional_primary_units_rounds_each_up():
    assert companion_quantity(120, 6, 'EA') == Decimal('20')
    assert companion_quantity(121, 6, 'EA') == Decimal('21')


def test_companion_quantity_one_to_one_fitting_hardware():
    assert companion_quantity(3, 1, 'EA') == Decimal('3')
