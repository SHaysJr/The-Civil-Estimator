from decimal import Decimal

from domain.assembly_sync import CompanionSpec, build_companion_lines


def spec(material_id=1, unit='EA', ratio=6, cost=10):
    return CompanionSpec(material_id, 'Companion', unit, Decimal(str(ratio)), Decimal(str(cost)))


def test_fence_post_quantity_resynchronizes_and_rounds_up():
    assert build_companion_lines(120, [spec()])[0].quantity == Decimal('20')
    assert build_companion_lines(121, [spec()])[0].quantity == Decimal('21')


def test_one_to_one_fitting_companions_follow_primary_quantity():
    gasket = spec(1, 'EA', 1, 4)
    restraint = CompanionSpec(2, 'Restraint', 'EA', Decimal('1'), Decimal('25'))
    lines = build_companion_lines(3, [gasket, restraint])
    assert [line.quantity for line in lines] == [Decimal('3'), Decimal('3')]


def test_existing_snapshot_price_can_be_preserved_during_sync():
    line = build_companion_lines(12, [spec(cost=99)], {1: 42.50})[0]
    assert line.quantity == Decimal('2')
    assert line.unit_cost == Decimal('42.5')


def test_negative_primary_quantity_is_rejected():
    try:
        build_companion_lines(-1, [spec()])
        assert False, 'Expected ValueError'
    except ValueError as exc:
        assert 'negative' in str(exc).lower()
