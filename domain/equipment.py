from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
from .money import dec, money


@dataclass(frozen=True)
class Equipment:
    machine_id: str
    description: str
    day_rate: Decimal
    week_rate: Decimal
    month_rate: Decimal
    fuel_capacity_gal: Decimal
    fuel_price_per_gal: Decimal

    @classmethod
    def make(cls, machine_id, description, day_rate, week_rate, month_rate, fuel_capacity_gal=0, fuel_price_per_gal=0):
        return cls(
            machine_id, description, dec(day_rate), dec(week_rate), dec(month_rate),
            dec(fuel_capacity_gal), dec(fuel_price_per_gal)
        )


def _ceil(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def equipment_cost(item: Equipment, days) -> dict:
    """Return rental + fuel for a section duration.

    Mirrors the legacy estimator rule documented in CLAUDE.md:
    compare day_rate*days, week_rate*ceil(days/3), and
    month_rate*ceil(days/9), and choose the lowest rental total.
    Fuel is capacity * fuel price * section days.
    """
    d = max(dec(days), Decimal('0'))
    if d == 0:
        return {'rental': money(0), 'fuel': money(0), 'total': money(0), 'tier': 'none'}

    choices = [
        ('day', item.day_rate * d),
        ('week', item.week_rate * _ceil(d / Decimal('3'))),
        ('month', item.month_rate * _ceil(d / Decimal('9'))),
    ]
    # Ignore zero/nonexistent tiers unless all tiers are zero.
    positive = [c for c in choices if c[1] > 0]
    tier, rental = min(positive or choices, key=lambda pair: pair[1])
    fuel = item.fuel_capacity_gal * item.fuel_price_per_gal * d
    return {
        'rental': money(rental),
        'fuel': money(fuel),
        'total': money(rental + fuel),
        'tier': tier,
    }
