from decimal import Decimal

DEPTH_BANDS = ('0-6', '6-8', '8-10', '10-12', '12-15', '15-18', '18+')
DEPTH_BAND_COLUMNS = {
    '0-6': 'production_rate_0_6',
    '6-8': 'production_rate_6_8',
    '8-10': 'production_rate_8_10',
    '10-12': 'production_rate_10_12',
    '12-15': 'production_rate_12_15',
    '15-18': 'production_rate_15_18',
    '18+': 'production_rate_18_plus',
}


def production_for_depth(material_row, depth_band):
    if not depth_band:
        return material_row['production_rate']
    if depth_band not in DEPTH_BAND_COLUMNS:
        raise ValueError('Invalid depth band.')
    return material_row[DEPTH_BAND_COLUMNS[depth_band]]


def depth_adjusted_unit_cost(base_unit_cost, depth_band, increment_per_band=0.50):
    """Legacy workbook convention: each deeper band adds $0.50/LF.

    This is only applied to rows explicitly flagged is_depth_priced.
    """
    if not depth_band:
        return float(base_unit_cost or 0)
    if depth_band not in DEPTH_BANDS:
        raise ValueError('Invalid depth band.')
    idx = DEPTH_BANDS.index(depth_band)
    return float(Decimal(str(base_unit_cost or 0)) + Decimal(str(increment_per_band)) * idx)
