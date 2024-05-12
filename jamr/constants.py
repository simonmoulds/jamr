#!/usr/bin/env python3

RESOLUTIONS = [0.5, 0.25, 0.1, 0.125, 1./12, 0.0625, 0.05, 1./24, 1./60, 0.01, 1./120, 1./240, 1./480, 1./360, 1./1200]

EXTENTS = {
    'globe': [-180, -90, 180, 90],
    'uk': [-8, 49, 2, 59],
    # 'europe': [],
    # 'south_america': [],
    # 'india': []
}

REGIONS = {}
for ext_name, ext in EXTENTS.items():
    for res in RESOLUTIONS:
        res_fmt = '{0:.6f}'.format(res)
        rgn_nm = f'{ext_name}_{res_fmt}Deg'
        REGIONS[rgn_nm] = {'extent': ext, 'res': res}

ESA_CCI_LC_YEARS = [y for y in range(1992, 2022)]

SOILGRIDS_VARIABLES = ['bdod', 'cec', 'clay', 'phh2o', 'sand', 'silt', 'soc']

SOILGRIDS_HORIZONS = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '100-200cm']
