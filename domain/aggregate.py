from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .money import CENT, dec, money


@dataclass(frozen=True)
class AggregateEstimate:
    cubic_yards: Decimal
    tons: Decimal
    tons_per_cy: Decimal
    material_cost: Decimal
    delivery_cost: Decimal
    fuel_surcharge_cost: Decimal
    total_cost: Decimal


def area_depth_to_cubic_yards(*, area_sqft, depth_in) -> Decimal:
    """Convert a footprint area and fill depth into cubic yards of material.

    27 cubic feet per cubic yard; depth is entered in inches (12 in/ft).
    """
    area = dec(area_sqft)
    depth = dec(depth_in)
    if area < 0:
        raise ValueError('Area cannot be negative.')
    if depth <= 0:
        raise ValueError('Depth must be greater than zero.')
    return (area * depth / Decimal('12')) / Decimal('27')


def compute_aggregate_estimate(
    *, area_sqft, depth_in, tons_per_cy,
    per_ton_cost=0, per_ton_delivery_cost=0, fuel_surcharge_per_ton=0, fuel_surcharge_applies=False,
) -> AggregateEstimate:
    """Estimate tons and cost of a rock/sand fill from area, depth, and a material-specific yield rate.

    ``tons_per_cy`` is the conversion (density/compaction) rate for the chosen material -
    it varies by material (riprap, #57 stone, sand, etc.), so callers pass whatever rate
    applies to the selected material rather than a single fixed constant.
    """
    rate = dec(tons_per_cy)
    if rate <= 0:
        raise ValueError('Conversion rate (tons per cubic yard) must be greater than zero.')

    cubic_yards = area_depth_to_cubic_yards(area_sqft=area_sqft, depth_in=depth_in)
    tons = cubic_yards * rate

    material_cost = tons * dec(per_ton_cost)
    delivery_cost = tons * dec(per_ton_delivery_cost)
    fuel_surcharge_cost = tons * dec(fuel_surcharge_per_ton) if fuel_surcharge_applies else Decimal('0')
    total_cost = material_cost + delivery_cost + fuel_surcharge_cost

    return AggregateEstimate(
        cubic_yards=cubic_yards.quantize(CENT, rounding=ROUND_HALF_UP),
        tons=tons.quantize(CENT, rounding=ROUND_HALF_UP),
        tons_per_cy=rate,
        material_cost=money(material_cost),
        delivery_cost=money(delivery_cost),
        fuel_surcharge_cost=money(fuel_surcharge_cost),
        total_cost=money(total_cost),
    )
