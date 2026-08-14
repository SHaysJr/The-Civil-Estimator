from dataclasses import dataclass
from decimal import Decimal

from .assemblies import companion_quantity
from .money import dec


@dataclass(frozen=True)
class CompanionSpec:
    material_id: int
    description: str
    unit: str
    ratio: Decimal
    unit_cost: Decimal
    pipe_type: str | None = None
    nominal_diameter_in: Decimal | None = None
    is_tax_exempt: bool = False


@dataclass(frozen=True)
class CompanionLine:
    material_id: int
    description: str
    unit: str
    quantity: Decimal
    unit_cost: Decimal
    ratio: Decimal
    pipe_type: str | None = None
    nominal_diameter_in: Decimal | None = None
    is_tax_exempt: bool = False


def build_companion_lines(primary_quantity, specs, preserved_unit_costs=None):
    """Build deterministic material-only companion lines for a primary item.

    ``preserved_unit_costs`` may map material IDs to snapshot unit costs from
    an existing estimate. This lets quantity edits refresh companion counts
    without silently pulling newer catalog pricing into an older bid.
    """
    qty = dec(primary_quantity)
    if qty < 0:
        raise ValueError('Primary quantity cannot be negative.')

    preserved_unit_costs = preserved_unit_costs or {}
    lines = []
    for spec in specs:
        ratio = dec(spec.ratio)
        unit_cost = preserved_unit_costs.get(int(spec.material_id), spec.unit_cost)
        lines.append(
            CompanionLine(
                material_id=int(spec.material_id),
                description=spec.description,
                unit=spec.unit,
                quantity=companion_quantity(qty, ratio, spec.unit),
                unit_cost=dec(unit_cost),
                ratio=ratio,
                pipe_type=spec.pipe_type,
                nominal_diameter_in=(dec(spec.nominal_diameter_in) if spec.nominal_diameter_in is not None else None),
                is_tax_exempt=bool(spec.is_tax_exempt),
            )
        )
    return lines
