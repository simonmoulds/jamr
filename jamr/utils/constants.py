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

# SOILGRIDS_VARIABLES = ['bdod', 'cec', 'clay', 'phh2o', 'sand', 'silt', 'soc']
# SOILGRIDS_HORIZONS = ['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '100-200cm']
SG_VARIABLES = ['clay_content', 'sand_content', 'silt_content', 'bulk_density', 'cation_exchange_capacity', 'ph_index', 'soil_organic_carbon']
SG_VARIABLES_ABBR = { 
    'clay_content': 'clay',
    'sand_content': 'sand',
    'silt_content': 'silt',
    'bulk_density': 'bdod',
    'cation_exchange_capacity': 'cec',
    'ph_index': 'phh2o',
    'soil_organic_carbon': 'soc'
}
SG_HORIZONS=['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '60-100cm', '100-200cm']
SG_SUMMARY_STATISTICS = ['mean', 'Q0.50', 'Q0.05', 'Q0.95']
SG_RESOLUTIONS = [250, 1000, 5000]

# *BUT* - see https://jules.jchmr.org/sites/default/files/McGuireEtAl_soils_JULESAnnualMeeting_20200907v2b.pdf
# "The K0 & n-exponent values for Sa=Sand are too extreme for JULES to
# handle, causing gridded JULES to hang without crashing, so we replaced
# the Sa values with the LoSa values."
ZHANGSCHAAP_FACTORS={
    'alpha': [
        0.0085736519, 0.0101142735, 0.0250359697, 0.0099478343, 
        0.0055563345, 0.0124256821, 0.0063582607, 0.0034302367, 
        0.0164037225, 0.0060396053, 0.024619742, 0.0328446188
    ],
    'n': [
        1.2547490134, 1.273204146, 1.2366347276, 1.3908612189, 
        1.4341667317, 1.3051970186, 1.4214753311, 1.5517801798, 
        1.4569557234, 1.5771727061, 1.6968969844, 2.8953059015
    ],
    'theta_res': [
        0.1309948472, 0.1236437112, 0.147392179, 0.1072850999, 
        0.1196643822, 0.0933631331, 0.0902482845, 0.083186447, 
        0.0606397155, 0.0650483449, 0.0581702395, 0.0545506462
    ],
    'theta_sat': [
        0.4574695264, 0.4729208221, 0.3818242427, 0.4287550719,  
        0.4702973434, 0.3800973379, 0.4017669217, 0.4269400175,   
        0.3808945256, 0.4724838864, 0.3830712622, 0.3633494968
    ],
    'ksat': [
        14.7500629329, 9.6136374341, 11.3533844849, 7.0635116122, 
        11.108435216, 13.2312093416, 13.3386286706, 18.4713576853, 
        37.4503675019, 43.7471157565, 108.1993376227, 642.9544642258
    ]
}

CRITICAL_POINT_SUCTION = 3.364
WILTING_POINT_SUCTION = 152.9