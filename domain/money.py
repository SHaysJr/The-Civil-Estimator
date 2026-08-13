from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal('0.01')


def dec(value=0) -> Decimal:
    if value in (None, ''):
        return Decimal('0')
    return Decimal(str(value))


def money(value=0) -> Decimal:
    return dec(value).quantize(CENT, rounding=ROUND_HALF_UP)
