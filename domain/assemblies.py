from decimal import Decimal, ROUND_CEILING

from .money import dec


def companion_quantity(primary_quantity, ratio, companion_unit):
    """Return the quantity of a companion item required.

    ``ratio`` is expressed as units of the primary item per one unit of the
    companion. Example: 6 LF of fence per 1 T-post => 120 LF requires 20 posts.
    Discrete EA items are rounded up so an estimate never contains a fraction
    of a fitting, gasket, post, restraint, etc.
    """
    qty = dec(primary_quantity)
    ratio_value = dec(ratio)
    if qty < 0:
        raise ValueError('Primary quantity cannot be negative.')
    if ratio_value <= 0:
        raise ValueError('Companion ratio must be greater than zero.')

    result = qty / ratio_value
    if (companion_unit or '').strip().upper() == 'EA':
        result = result.to_integral_value(rounding=ROUND_CEILING)
    return result
