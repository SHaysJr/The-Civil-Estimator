from dataclasses import dataclass
from decimal import Decimal
from .costing import compute_line, line_days
from .equipment import Equipment, equipment_cost
from .labor import CrewMember, crew_daily_cost
from .money import dec, money


@dataclass(frozen=True)
class SectionResult:
    scope_name: str
    days: Decimal
    crew_daily_cost: Decimal
    equipment_total: Decimal
    line_results: tuple
    direct_cost: Decimal
    total: Decimal
    taxed_total: Decimal


def compute_section(*, scope_name, lines, crew, equipment, overhead_rate, profit_rate, tax_rate):
    line_day_values = [line_days(row['quantity'], row.get('production_rate')) for row in lines]
    section_days = sum(line_day_values, Decimal('0'))
    daily_crew = crew_daily_cost(crew)

    equipment_breakdown = [equipment_cost(item, section_days) for item in equipment]
    section_equipment_total = money(sum((x['total'] for x in equipment_breakdown), Decimal('0')))

    results = []
    for row, days in zip(lines, line_day_values):
        labor_alloc = money(daily_crew * days)
        equipment_alloc = money(section_equipment_total * (days / section_days)) if section_days > 0 else money(0)
        results.append(compute_line(
            description=row['description'], unit=row['unit'], quantity=row['quantity'],
            unit_cost=row['unit_cost'], production_rate=row.get('production_rate'),
            bedding_cost=row.get('bedding_cost', 0), labor_cost=labor_alloc,
            equipment_cost=equipment_alloc, overhead_rate=overhead_rate,
            profit_rate=profit_rate, tax_rate=tax_rate,
            is_tax_exempt=bool(row.get('is_tax_exempt', False)),
        ))

    direct = money(sum((r.subtotal for r in results), Decimal('0')))
    total = money(sum((r.total for r in results), Decimal('0')))
    taxed_total = money(sum((r.taxed_total for r in results), Decimal('0')))
    return SectionResult(
        scope_name=scope_name, days=section_days, crew_daily_cost=daily_crew,
        equipment_total=section_equipment_total, line_results=tuple(results),
        direct_cost=direct, total=total, taxed_total=taxed_total,
    )
