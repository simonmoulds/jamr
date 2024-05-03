#!/usr/bin/env python3


REGIONS = {
    'globe_0.500000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.5},
    'globe_0.250000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.25},
    'globe_0.100000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.1},
    'globe_0.125000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.125},
    'globe_0.083333Deg': {'extent': [-180, -90, 180, 90], 'res': 1./12},
    'globe_0.062500Deg': {'extent': [-180, -90, 180, 90], 'res': 0.0625},
    'globe_0.050000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.05},
    'globe_0.041667Deg': {'extent': [-180, -90, 180, 90], 'res': 1./24},
    'globe_0.016667Deg': {'extent': [-180, -90, 180, 90], 'res': 1./60},
    'globe_0.010000Deg': {'extent': [-180, -90, 180, 90], 'res': 0.01},
    'globe_0.008333Deg': {'extent': [-180, -90, 180, 90], 'res': 1./120},
    'globe_0.004167Deg': {'extent': [-180, -90, 180, 90], 'res': 1./240},
    'globe_0.002083Deg': {'extent': [-180, -90, 180, 90], 'res': 1./480},
    'globe_0.002778Deg': {'extent': [-180, -90, 180, 90], 'res': 1./360},
    'globe_0.000833Deg': {'extent': [-180, -90, 180, 90], 'res': 1./1200},
}

ESA_CCI_LC_YEARS = [y for y in range(1992, 2022)]

SOILGRIDS_VARIABLES = ['bdod', 'cec', 'clay', 'phh2o', 'sand', 'silt', 'soc']

SOILGRIDS_HORIZONS = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '100-200cm']
