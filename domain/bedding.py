from dataclasses import dataclass
from decimal import Decimal
from math import pi

from .money import dec, money


@dataclass(frozen=True)
class BeddingResult:
    quantity_cy: Decimal
    unit_cost_per_cy: Decimal
    total_cost: Decimal
    volume_per_lf_cf: Decimal
    trench_width_in: Decimal


def bedding_volume_per_lf_cf(*, pipe_od_in, depth_below_in, haunch_to_springline,
                             envelope_above_crown_in, trench_side_clearance_in) -> Decimal:
    """Match the geometry used by the MS/TN bedding estimating workbooks.

    The calculation is intentionally a pure geometry function. Regulatory choice of
    bedding class/material belongs in data, not in this function.
    """
    od = dec(pipe_od_in)
    depth = dec(depth_below_in)
    envelope = dec(envelope_above_crown_in)
    side = dec(trench_side_clearance_in)
    if od <= 0:
        return Decimal('0')

    width_in = od + Decimal('2') * side
    width_ft = width_in / Decimal('12')
    total = width_ft * (depth / Decimal('12'))

    if haunch_to_springline:
        # Workbook formula: width * half-OD height minus lower half-circle area.
        total += width_ft * (od / Decimal('2') / Decimal('12'))
        total -= Decimal(str(pi)) / Decimal('8') * (od / Decimal('12')) ** 2

    total += width_ft * (envelope / Decimal('12'))
    return total


def compute_bedding(*, length_lf, pipe_od_in, depth_below_in, haunch_to_springline,
                    envelope_above_crown_in, trench_side_clearance_in,
                    unit_cost_per_cy=0, prohibited=False) -> BeddingResult:
    if prohibited:
        return BeddingResult(Decimal('0'), money(unit_cost_per_cy), money(0), Decimal('0'), Decimal('0'))

    per_lf = bedding_volume_per_lf_cf(
        pipe_od_in=pipe_od_in,
        depth_below_in=depth_below_in,
        haunch_to_springline=haunch_to_springline,
        envelope_above_crown_in=envelope_above_crown_in,
        trench_side_clearance_in=trench_side_clearance_in,
    )
    length = dec(length_lf)
    qty_cy = (per_lf * length) / Decimal('27') if length > 0 else Decimal('0')
    unit_cost = money(unit_cost_per_cy)
    return BeddingResult(
        quantity_cy=qty_cy,
        unit_cost_per_cy=unit_cost,
        total_cost=money(qty_cy * unit_cost),
        volume_per_lf_cf=per_lf,
        trench_width_in=dec(pipe_od_in) + Decimal('2') * dec(trench_side_clearance_in),
    )
