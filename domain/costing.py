from dataclasses import dataclass
from decimal import Decimal
from .money import dec, money


@dataclass(frozen=True)
class LineResult:
    description: str
    unit: str
    quantity: Decimal
    days: Decimal
    material: Decimal
    bedding: Decimal
    labor: Decimal
    equipment: Decimal
    subtotal: Decimal
    overhead: Decimal
    profit: Decimal
    total: Decimal
    unit_price: Decimal
    taxed_subtotal: Decimal
    taxed_overhead: Decimal
    taxed_profit: Decimal
    taxed_total: Decimal
    taxed_unit_price: Decimal


def line_days(quantity, production_rate) -> Decimal:
    qty = dec(quantity)
    rate = dec(production_rate)
    if qty <= 0 or rate <= 0:
        return Decimal('0')
    return qty / rate


def compute_line(
    *, description, unit, quantity, unit_cost, production_rate,
    bedding_cost=0, labor_cost=0, equipment_cost=0,
    overhead_rate=0, profit_rate=0, tax_rate=0, is_tax_exempt=False,
) -> LineResult:
    qty = dec(quantity)
    days = line_days(qty, production_rate)
    material = money(qty * dec(unit_cost))
    bedding = money(bedding_cost)
    labor = money(labor_cost)
    equipment = money(equipment_cost)
    subtotal = money(material + bedding + labor + equipment)

    oh_rate = dec(overhead_rate)
    p_rate = dec(profit_rate)
    t_rate = Decimal('0') if is_tax_exempt else dec(tax_rate)

    # Legacy estimator: overhead and profit are both percentages of the base subtotal.
    overhead = money(subtotal * oh_rate)
    profit = money(subtotal * p_rate)
    total = money(subtotal + overhead + profit)
    unit_price = money(total / qty) if qty else money(0)

    taxed_subtotal = money(subtotal * (Decimal('1') + t_rate))
    taxed_overhead = money(taxed_subtotal * oh_rate)
    taxed_profit = money(taxed_subtotal * p_rate)
    taxed_total = money(taxed_subtotal + taxed_overhead + taxed_profit)
    taxed_unit_price = money(taxed_total / qty) if qty else money(0)

    return LineResult(
        description=description, unit=unit, quantity=qty, days=days,
        material=material, bedding=bedding, labor=labor, equipment=equipment,
        subtotal=subtotal, overhead=overhead, profit=profit, total=total,
        unit_price=unit_price, taxed_subtotal=taxed_subtotal,
        taxed_overhead=taxed_overhead, taxed_profit=taxed_profit,
        taxed_total=taxed_total, taxed_unit_price=taxed_unit_price,
    )
