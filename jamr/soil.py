#!/usr/bin/env python3

import os
import re
import glob
import time
import math
import warnings

import grass.script as gscript
import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from osgeo import gdal

from jamr.constants import REGIONS

# TODO 
# - add POLARIS data [USA only]
# - add Saxton & Rawls PTFs https://doi.org/10.2136/sssaj2005.0117 [USA only]
# - add Toth et al PTFs [Europe only]

SG_VARIABLES=['bdod', 'cec', 'clay', 'phh2o', 'sand', 'silt', 'soc']
SG_HORIZONS=['0-5cm', '5-15cm', '15-30cm', '30-60cm', '60-100cm', '100-200cm']

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


class PTF:
    def __init__(self, 
                 method,
                 clay_content, 
                 sand_content, 
                 silt_content,
                 soil_organic_carbon,
                 ph_index,
                 cation_exchange_capacity,
                 bulk_density,
                 horizon, 
                 region, 
                 overwrite):

        self.method = method
        self.clay_content = clay_content 
        self.sand_content = sand_content 
        self.silt_content = silt_content 
        self.soil_organic_carbon = soil_organic_carbon
        self.ph_index = ph_index
        self.cation_exchange_capacity = cation_exchange_capacity
        self.bulk_density = bulk_density
        self.horizon = horizon
        self.region = region 
        self.overwrite = overwrite 

    def _set_names(self):
        raise NotImplementedError()

class CosbyPTF(PTF):
    def __init__(self, 
                 clay_content, 
                 sand_content, 
                 horizon,
                 region,
                 overwrite):
        super().__init__('cosby', clay_content, sand_content, None, None, None, None, None, horizon, region, overwrite)

    def _set_names(self):
        self.lambda_mapname = f'lambda_{self.method}_{self.horizon}_{self.region}'
        self.b_mapname = f'b_{self.method}_{self.horizon}_{self.region}'
        self.psi_mapname = f'psi_m_{self.method}_{self.horizon}_{self.region}' 
        self.ksat_mapname = f'ksat_{self.method}_{self.horizon}_{self.region}' 
        self.theta_sat_mapname = f'theta_sat_{self.method}_{self.horizon}_{self.region}' 
        self.theta_crit_mapname = f'theta_crit_{self.method}_{self.horizon}_{self.region}'
        self.theta_wilt_mapname = f'theta_wilt_{self.method}_{self.horizon}_{self.region}' 
        self.theta_res_mapname = f'theta_res_{self.method}_{self.horizon}_{self.region}'

    def compute(self):
        self.brooks_corey_b()
        self.air_entry_pressure() 
        self.saturated_hydraulic_conductivity()
        self.saturated_water_content()
        self.critical_water_content()
        self.wilting_point()
        self.residual_water_content()

    def brooks_corey_b(self):
        try:
            r.mapcalc(
                f'{self.b_mapname} = (3.10 + 0.157 * {self.clay_content} - 0.003 * {self.sand_content})', 
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def air_entry_pressure(self): 
        try:
            r.mapcalc(
                f'{self.psi_mapname} = 0.01 * (10 ^ (2.17 - (0.0063 * {self.clay_content}) - (0.0158 * {self.sand_content})))', 
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def saturated_hydraulic_conductivity(self):
        try:
            r.mapcalc(
                f'{self.ksat_mapname} = (25.4 / (60 * 60)) * (10 ^ (-0.60 - (0.0064 * {self.clay_content}) + (0.0126 * {self.sand_content})))',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def saturated_water_content(self):
        try:
            r.mapcalc(
                f'{self.theta_sat_mapname} = 0.01 * (50.5 - 0.037 * {self.clay_content} - 0.142 * {self.sand_content})', 
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def critical_water_content(self):
        try:
            r.mapcalc(
                f'{self.theta_crit_mapname} = {self.theta_sat_mapname} * ({self.psi_mapname} / {CRITICAL_POINT_SUCTION}) ^ (1 / {self.b_mapname})',
                overwrite=self.overwrite
            ) 
        except grass.exceptions.CalledModuleError:
            pass

    def wilting_point(self):
        try:
            r.mapcalc(
                f'{self.theta_wilt_mapname} = {self.theta_sat_mapname} * ({self.psi_mapname} / {WILTING_POINT_SUCTION}) ^ (1 / {self.b_mapname})',
                overwrite=self.overwrite
            ) 
        except grass.exceptions.CalledModuleError:
            pass

    def residual_water_content(self):
        try:
            # Assume residual water content is zero
            r.mapcalc(f'{self.theta_res_mapname} = 0', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass

class VanGenuchtenPTF(PTF):
    def __init__(self, 
                 method,
                 clay_content, 
                 sand_content, 
                 silt_content,
                 soil_organic_content,
                 ph_index,
                 cation_exchange_capacity,
                 bulk_density,
                 horizon,
                 region,
                 overwrite):

        super().__init__(
            method, clay_content, sand_content, silt_content, soil_organic_content, 
            ph_index, cation_exchange_capacity, bulk_density, horizon, region, overwrite
        )

    def _set_names(self):
        self.n_mapname = f'n_{self.method}_{self.horizon}_{self.region}'
        self.alpha_mapname = f'alpha_{self.method}_{self.horizon}_{self.region}'
        self.ksat_mapname = f'ksat_{self.method}_{self.horizon}_{self.region}' 
        self.theta_sat_mapname = f'theta_sat_{self.method}_{self.horizon}_{self.region}' 
        self.theta_crit_mapname = f'theta_crit_{self.method}_{self.horizon}_{self.region}'
        self.theta_wilt_mapname = f'theta_wilt_{self.method}_{self.horizon}_{self.region}' 
        self.theta_res_mapname = f'theta_res_{self.method}_{self.horizon}_{self.region}'

    def compute(self):
        self.van_genuchten_alpha()
        self.van_genuchten_n()
        self.residual_water_content()
        self.saturated_water_content()
        self.air_entry_pressure()
        self.pore_size_distribution()
        self.critical_water_content()
        self.wilting_point()

    def van_genuchten_alpha(self):
        raise NotImplementedError
    
    def van_genuchten_n(self):
        raise NotImplementedError 
    
    def residual_water_content(self):
        raise NotImplementedError 
    
    def saturated_water_content(self):
        raise NotImplementedError

    def air_entry_pressure(self):
        # From JULES docs (http://jules-lsm.github.io/vn5.4/namelists/ancillaries.nml.html#list-of-soil-parameters) 
        # sathh = 1 / alpha, where alpha has units m-1
        try:
            r.mapcalc(f'{self.psi_mapname} = 1 / {self.alpha_mapname}', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass

    def pore_size_distribution(self): 
        try:
            r.mapcalc(f'{self.b_mapname} = 1 / ({self.n_mapname} - 1)', overwrite=self.overwrite)
        except grass.exceptions.CalledModuleError:
            pass

    def van_genuchten_equation(self, suffix, suction, theta_mapname):
        try:
            r.mapcalc(
    	        f'A_{suffix}_{self.method}_{self.horizon}_{self.region} = ({self.alpha_mapname} * suction) ^ {self.n_mapname}',
                overwrite=self.overwrite
            )
            r.mapcalc(
                f'Se_{suffix}_{self.method}_{self.horizon}_{self.region} = (1 + A_{suffix}_{self.method}_{self.horizon}_{self.region}) '
                '^ ((1 / {self.n_mapname}) - 1)',
                overwrite=self.overwrite
            )
            r.mapcalc(
    	        f'{theta_mapname} = (Se_{suffix}_{self.method}_{self.horizon}_{self.region} '
                '* ({self.theta_sat_mapname} - {self.theta_res_mapname})) + {self.theta_res_mapname}',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def critical_water_content(self):
        self.van_genuchten_equation('crit', CRITICAL_POINT_SUCTION, self.theta_crit_mapname)

    def wilting_point(self):
        self.van_genuchten_equation('wilt', WILTING_POINT_SUCTION, self.theta_wilt_mapname)


class TomasellaHodnettPTF(VanGenuchtenPTF):
    def __init__(self, 
                 clay_content, 
                 sand_content, 
                 silt_content,
                 soil_organic_content,
                 ph_index,
                 cation_exchange_capacity,
                 bulk_density,
                 horizon,
                 region,
                 overwrite):

        super().__init__(
            'tomasellahodnett', clay_content, sand_content, silt_content, soil_organic_content, 
            ph_index, cation_exchange_capacity, bulk_density, horizon, region, overwrite
        )

    def van_genuchten_n(self): 
        try:
            r.mapcalc(
                (
                    f'{self.n_mapname} = exp((62.986 - (0.833 * {self.clay_content}) '
                    '- (0.529 * ({self.soil_organic_carbon} / 10)) + (0.593 * {self.ph_index} / 10) '
                    '+ (0.007 * {self.clay_content} * {self.clay_content}) '
                    '- (0.014 * {self.sand_content} * {self.silt_content})) / 100)'
                ),
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def van_genuchten_alpha(self):
        try: 
            r.mapcalc(
                (
                    f'{self.alpha_mapname} = 9.80665 * exp((-2.294 - (3.526 * {self.silt_content}) '
                    '+ (2.440 * ({self.soil_organic_carbon} / 10)) - (0.076 * {self.cation_exchange_capacity}) '
                    '- (11.331 * {self.ph_index} / 10) + (0.019 * {self.silt_content} * {self.silt_content})) / 100)'
                ),
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def saturated_water_content(self):
        try:
            r.mapcalc(
                (
    	            f'{self.theta_sat_mapname} = 0.01 * (81.799 + (0.099 * {self.clay_content}) '
                    '- (31.42 * {self.bulk_density} * 0.001) + (0.018 * {self.cation_exchange_capacity}) '
                    '+ (0.451 * {self.ph_index} / 10) - (0.0005 * {self.sand_content} * {self.clay_content}))'
                ),
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def residual_water_content(self):
        try:
            r.mapcalc(
                (
                    f'{self.theta_res_mapname} = 0.01 * (22.733 - (0.164 * {self.sand_content}) '
                    '+ (0.235 * {self.cation_exchange_capacity}) - (0.831 * {self.ph_index} / 10) '
                    '+ (0.0018 * {self.clay_content} * {self.clay_content}) '
                    '+ (0.0026 * {self.sand_content} * {self.clay_content}))'
                ),
                self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def saturated_hydraulic_conductivity(self):
        # Tomasella & Hodnett do not provide a transfer function, so we use Cosby PTF instead
        try:
            r.mapcalc(
                f'{self.ksat_mapname} = (25.4 / (60 * 60)) '
                '* (10 ^ (-0.60 - (0.0064 * {self.clay_content}) + (0.0126 * {self.sand_content})))',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass


class USDATextureClass:
    def __init__(self, 
                 clay_content, 
                 sand_content, 
                 silt_content,
                 horizon,
                 region,
                 overwrite):
 
        self.clay_content = clay_content 
        self.sand_content = sand_content 
        self.silt_content = silt_content 
        self.horizon = horizon 
        self.region = region 
        self.overwrite = overwrite 
        self._set_names() 

    def compute(self):
        self._usda_texture_class()

    def _set_names(self):
        self.usda_clay_mapname = f'usda_clay_{self.horizon}_{self.region}'
        self.usda_sandy_clay_mapname = f'usda_sandy_clay_{self.horizon}_{self.region}'
        self.usda_silty_clay_mapname = f'usda_silty_clay_{self.horizon}_{self.region}'
        self.usda_sandy_clay_loam_mapname = f'usda_sandy_clay_loam_{self.horizon}_{self.region}'
        self.usda_clay_loam_mapname = f'usda_clay_loam_{self.horizon}_{self.region}'
        self.usda_silty_clay_loam_mapname = f'usda_silty_clay_loam_{self.horizon}_{self.region}'
        self.usda_sandy_loam_mapname = f'usda_sandy_loam_{self.horizon}_{self.region}'
        self.usda_loam_mapname = f'usda_loam_{self.horizon}_{self.region}'
        self.usda_silt_loam_mapname = f'usda_silt_loam_{self.horizon}_{self.region}'
        self.usda_silt_mapname = f'usda_silt_{self.horizon}_{self.region}'
        self.usda_loamy_sand_mapname = f'usda_loamy_sand_{self.horizon}_{self.region}'
        self.usda_sand_mapname = f'usda_sand_{self.horizon}_{self.region}'

    def _texture_class(self, output, sand_min, sand_max, silt_min, silt_max, clay_min, clay_max):
        try:
            r.mapcalc(
                f'{output} = if(({self.sand_content} >= {sand_min}) & ({self.sand_content} <= {sand_max}) '
                '& ({self.silt_content} >= {silt_min}) & ({self.silt_content} <= {silt_max}) '
                '& ({self.clay_content} >= {clay_min}) & ({self.clay_content} <= {clay_max}), 1, 0)',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def _usda_texture_class(self):
        # if sand <= 45 and silt <= 40 and clay >= 40: texture = 'Clay'
        self._texture_class(self.usda_clay_mapname, sand_min=0, sand_max=45, silt_min=0, silt_max=40, clay_min=40, clay_max=100)
        # elif sand <= 65 and sand >= 45 and silt <= 20 and clay >= 35 and clay <= 55: texture = 'Sandy Clay' 
        self._texture_class(self.usda_sandy_clay_mapname, sand_min=45, sand_max=65, silt_min=0, silt_max=20, clay_min=35, clay_max=55)
        # elif sand <= 20 and silt >= 40 and silt <= 60 and clay >= 40 and clay <= 60:
        self._texture_class(self.usda_silty_clay_mapname, sand_min=0, sand_max=20, silt_min=40, silt_max=60, clay_min=40, clay_max=60)
        # elif sand >= 45 and sand <= 80 and silt <= 28 and clay >= 20 and clay <= 35: texture = "Sandy Clay Loam"
        self._texture_class(self.usda_sandy_clay_loam_mapname, sand_min=45, sand_max=80, silt_min=0, silt_max=28, clay_min=20, clay_max=35)
        # elif sand >= 20 and sand <= 45 and silt >= 15 and silt <= 53 and clay >= 27 and clay <= 40: texture = "Clay Loam"
        self._texture_class(self.usda_clay_loam_mapname, sand_min=20, sand_max=45, silt_min=15, silt_max=53, clay_min=27, clay_max=40)
        # elif sand <= 20 and silt >= 40 and silt <= 73 and clay >= 27 and clay <= 40: texture = "Silty Clay Loam"
        self._texture_class(self.usda_silty_clay_loam_mapname, sand_min=0, sand_max=20, silt_min=40, silt_max=73, clay_min=27, clay_max=40)
        # elif sand >= 43 and sand <= 85 and silt <= 50 and clay <= 20: texture = "Sandy Loam"
        self._texture_class(self.usda_sandy_loam_mapname, sand_min=43, sand_max=85, silt_min=0, silt_max=50, clay_min=0, clay_max=20)
        # elif sand >= 23 and sand <= 52 and silt >= 28 and silt <= 50 and clay >= 7 and clay <= 27: texture = "Loam"
        self._texture_class(self.usda_loam_mapname, sand_min=23, sand_max=52, silt_min=28, silt_max=50, clay_min=7, clay_max=27)
        # elif sand <= 50 and silt >= 50 and silt <= 88 and clay <= 27: texture = "Silt Loam"
        self._texture_class(self.usda_silt_loam_mapname, sand_min=0, sand_max=50, silt_min=50, silt_max=88, clay_min=0, clay_max=27)
        # elif sand <= 20 and silt >= 80 and clay <= 12: texture = "Silt"
        self._texture_class(self.usda_silt_mapname, sand_min=0, sand_max=20, silt_min=80, silt_max=100, clay_min=0, clay_max=12)
        # elif sand >= 70 and sand <= 90 and silt <= 30 and clay <= 15: texture = "Loamy Sand"
        self._texture_class(self.usda_loamy_sand_mapname, sand_min=70, sand_max=90, silt_min=0, silt_max=30, clay_min=0, clay_max=15)
        # elif sand >= 85 and silt <= 15 and clay <= 10: texture = "Sand"
        self._texture_class(self.usda_sand_mapname, sand_min=85, sand_max=100, silt_min=0, silt_max=15, clay_min=0, clay_max=10)

class ZhangSchaapPTF(VanGenuchtenPTF):
    def __init__(self, 
                 clay_content, 
                 sand_content, 
                 silt_content,
                 horizon,
                 region,
                 overwrite):

        super().__init__(
            'zhangschaap', clay_content, sand_content, silt_content, 
            None, None, None, None, horizon, region, overwrite
        )

    def compute(self):
        self.usda = USDATextureClass(
            self.clay_content, self.sand_content, self.silt_content, 
            self.horizon, self.region, self.overwrite
        )
        self.usda.compute() 
        super().compute()

    def _zhang_schaap_equation(self, output, factors):
# 	"theta_res_rosetta3_${HORIZON}_${RGN_STR} = Cl * 0.1309948472 + SiCl * 0.1236437112 + SaCl * 0.147392179 + ClLo * 0.1072850999 + SiClLo * 0.1196643822 + SaClLo * 0.0933631331 + Lo * 0.0902482845 + SiLo * 0.083186447 + SaLo * 0.0606397155 + Si * 0.0650483449 + LoSa * 0.0581702395 + Sa * 0.0581702395" \
        try:
            r.mapcalc(
	            f'{output} = {self.usda.usda_clay_mapname} * {factors[0]} ' 
                '+ {self.usda.usda_silty_clay_mapname} * {factors[1]} '
                '+ {self.usda.usda_sandy_clay_mapname} * {factors[2]} '
                '+ {self.usda.usda_clay_loam_mapname} * {factors[3]}'
                '+ {self.usda.usda_silty_clay_loam_mapname} * {factors[4]}'
                '+ {self.usda.usda_sandy_clay_loam_mapname} * {factors[5]}'
                '+ {self.usda.usda_loam_mapname} * {factors[6]} '
                '+ {self.usda.usda_silt_loam_mapname} * {factors[7]} '
                '+ {self.usda.usda_sandy_loam_mapname} * {factors[8]} '
                '+ {self.usda.usda_silt_mapname} * {factors[9]} '
                '+ {self.usda.usda_loamy_sand_mapname} * {factors[10]} '
                '+ {self.usda.usda_sand_mapname} * {factors[11]}',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def van_genuchten_alpha(self):
        self._zhang_schaap_equation(self.alpha_mapname, ZHANGSCHAAP_FACTORS['alpha'])

    def van_genuchten_n(self):
        self._zhang_schaap_equation(self.n_mapname, ZHANGSCHAAP_FACTORS['n'])

    def residual_water_content(self):
        self._zhang_schaap_equation(self.theta_res_mapname, ZHANGSCHAAP_FACTORS['theta_res'])

    def saturated_water_content(self):
        self._zhang_schaap_equation(self.theta_sat_mapname, ZHANGSCHAAP_FACTORS['theta_sat'])

    def saturated_hydraulic_conductivity(self):
        self._zhang_schaap_equation(self.ksat_mapname, ZHANGSCHAAP_FACTORS['ksat'])

#     # Remove mask
#     r.mask -r
    
#     # # Reset resolution
#     # NATIVE_RGN_STR=globe_0.002083Deg
#     # RGN_STR=globe_0.008333Deg
#     # g.region region=${RGN_STR}

#     # # Resample rosetta3 maps to 1k resolution
#     # for VARIABLE in b k_sat psi_m theta_crit theta_sat theta_wilt
#     # do
#     # 	r.resamp.stats \
#     # 	    input=${VARIABLE}_rosetta3_${HORIZON}_${NATIVE_RGN_STR}.tif \
#     # 	    output=${VARIABLE}_rosetta3_${HORIZON}_${RGN_STR}.tif \
#     # 	    method=average \
#     # 	    $OVERWRITE
#     # done            
# done

class SoilGrids:
    def __init__(self, config, overwrite):
        self.data_directory = config['soil']['soilgrids']['data_directory']
        self.scratch = config['main']['scratch_directory'] 
        self.variables = SG_VARIABLES 
        self.horizons = SG_HORIZONS
        self.overwrite = bool(overwrite)

    def reproject(self):
        opts = gdal.WarpOptions(format='GTiff', outputBounds=[-180, -90, 180, 90], xRes = 1 / 120., yRes = 1 / 120., dstSRS = 'EPSG:4326')
        for horizon in self.horizons:
            for variable in self.variables:
                input_map = os.path.join(self.data_directory, f'{variable}_{horizon}_mean_1000.tif')
                output_map = os.path.join(self.scratch, f'{variable}_{horizon}_mean_1000_ll.tif')
                if not os.path.exists(output_map) or self.overwrite:
                    mymap = gdal.Warp(output_map, input_map, options=opts)
                    mymap = None

    def read(self):
        for horizon in self.horizons:
            for variable in self.variables:
                try:
                    r.in_gdal(
                        input=os.path.join(self.scratch, f'{variable}_{horizon}_mean_1000_ll.tif'), 
                        output=f'{variable}_{horizon}', #_init',
                        flags='a',
                        overwrite=self.overwrite
                    )
                except grass.exceptions.CalledModuleError:
                    pass
                # TODO decide whether to fill with HWSD

    
def read_soilgrids_data(config, overwrite):

    sg = SoilGrids(config, overwrite)
    sg.reproject()
    sg.read()

    return 0

def process_soil_data(config, region, overwrite):

    # Remove mask
    try:
        r.mask(flags='r')
    except grass.exceptions.CalledModuleError:
        pass
    
    sg = SoilGrids(config, overwrite)
    sg.reproject()
    sg.read()

    # # Set user-defined region, check native resolution
    # g.region(region=region, align='globe_0.008333Deg')
    # c = gscript.region() 
    # if not math.isclose(c['res'], 1 / 120.):
    #     raise ValueError('Resolution does not match native SoilGrids resolution')

    # for horizon in SG_HORIZONS:
    #     cosby_ptf = CosbyPTF(f'clay_{horizon}', f'sand_{horizon}', horizon, rgn, overwrite)
    #     cosby_ptf.compute()  
        
    #     tomasella_hodnett_ptf = TomasellaHodnettPTF(
    #         f'clay_{horizon}', f'sand_{horizon}', f'silt_{horizon}', 
    #         f'soc_{horizon}', f'phh2o_{horizon}', f'cec_{horizon}', 'bld_{horizon}', 
    #         horizon, rgn, overwrite
    #     )
    #     tomasella_hodnett_ptf.compute()
       
    #     zhang_schaap_ptf = ZhangSchaapPTF(
    #         f'clay_{horizon}', f'sand_{horizon}', f'silt_{horizon}', 
    #         horizon, rgn, overwrite
    #     )
    #     zhang_schaap_ptf.compute()




#     # Remove mask
#     r.mask -r
    
#     # # Reset resolution
#     # NATIVE_RGN_STR=globe_0.002083Deg
#     # RGN_STR=globe_0.008333Deg
#     # g.region region=${RGN_STR}

#     # # Resample rosetta3 maps to 1k resolution
#     # for VARIABLE in b k_sat psi_m theta_crit theta_sat theta_wilt
#     # do
#     # 	r.resamp.stats \
#     # 	    input=${VARIABLE}_rosetta3_${HORIZON}_${NATIVE_RGN_STR}.tif \
#     # 	    output=${VARIABLE}_rosetta3_${HORIZON}_${RGN_STR}.tif \
#     # 	    method=average \
#     # 	    $OVERWRITE
#     # done            
# done

# # ========================================================= #
# # Compute dry heat capacity, dry thermal conductivity
# # ========================================================= #

# RGN_STR=globe_0.008333Deg
# g.region region=${RGN_STR}

# # See Zed Zulkafli's PhD thesis for equations

# # Units: J m-3 K-1
# cc=2373000
# cs=2133000
# csi=2133000
# lambda_air=0.025
# lambda_clay=1.16025
# lambda_sand=1.57025
# lambda_silt=1.57025
# for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
# do
#     for METHOD in cosby tomas rosetta3
#     do
# 	r.mapcalc \
# 	    "hcap_${METHOD}_${HORIZON}_${RGN_STR} = (1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * (CLYPPT_${HORIZON} * 0.01 * $cc + SNDPPT_${HORIZON} * 0.01 * $cs + SLTPPT_${HORIZON} * 0.01 * $csi)" \
# 	    $OVERWRITE

# 	r.mapcalc \
# 	    "hcon_${METHOD}_${HORIZON}_${RGN_STR} = ($lambda_air ^ theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * ($lambda_clay ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * CLYPPT_${HORIZON} * 0.01)) * ($lambda_sand ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * SNDPPT_${HORIZON} * 0.01)) * ($lambda_silt ^ ((1 - theta_sat_${METHOD}_${HORIZON}_${RGN_STR}) * SLTPPT_${HORIZON} * 0.01))" \
# 	    $OVERWRITE
#     done
# done    

# # ========================================================= #
# # Read VARIABLEs which are included in the SoilGrids data
# # ========================================================= #

# g.region region=${RGN_STR}

# # PHIHOX, CLYPPT
# for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
# do
#     r.mapcalc \
# 	"ph_${HORIZON}_${RGN_STR} = PHIHOX_${HORIZON} / 10" \
# 	$OVERWRITE
#     r.mapcalc \
# 	"clay_${HORIZON}_${RGN_STR} = CLYPPT_${HORIZON}" \
# 	$OVERWRITE
# done

# # ========================================================= #
# # Soil albedo
# # ========================================================= #

# # Use dataset of Houldcroft et al. (2009) (downloaded from JASMIN)
# g.region region=${RGN_STR}

# ncks -O --msa -d longitude,180.,360. -d longitude,0.,180. ../data/soil_albedo.nc tmp.nc
# ncap2 -O -s 'where(longitude > 180) longitude=longitude-360' tmp.nc $AUXDIR/soil_albedo_corr_long.nc
# rm -f tmp.nc

# # use GDAL tools to convert netCDF to geotiff
# gdal_translate \
#     -co "compress=lzw" \
#     NETCDF:\"$AUXDIR/soil_albedo_corr_long.nc\":soil_albedo tmp.tif

# # resample to match globe_0.008333Deg region, using nearest-neighbour resampling
# gdalwarp \
#     -overwrite \
#     -t_srs EPSG:4326 \
#     -co "compress=lzw" \
#     -te -180 -90 180 90 \
#     -ts 43200 21600 \
#     -r near \
#     tmp.tif $AUXDIR/soil/background_soil_albedo_${RGN_STR}.tif

# # clean up
# rm -f tmp.tif

# # import data to GRASS
# r.in.gdal \
#     -a \
#     input=$AUXDIR/soil/background_soil_albedo_${RGN_STR}.tif \
#     output=background_soil_albedo_${RGN_STR} \
#     $OVERWRITE

# NOT USED: 

# # ========================================================= #
# # Read in soil texture maps
# # ========================================================= #

# g.region region=globe_0.008333Deg
# g.region -p

# SOILGRID_VARS=(CLYPPT SNDPPT SLTPPT BLDFIE CECSOL ORCDRC PHIHOX)
# HWSD_VARS=(clay sand silt bulk_density cec_soil oc ph_h2o)

# # Read HWSD maps, which we use to fill gaps in the
# # SoilGrids data
# for i in `seq 0 6`
# do
#     VARIABLE=${HWSD_VARS[i]}
#     SOILGRID_VARIABLE=${SOILGRID_VARS[i]}
#     for LAYER in t s
#     do	
# 	r.in.gdal \
# 	    -a \
# 	    input=${HWSDDIR}/hwsd_sg_"${LAYER}"_"${VARIABLE}".tif \
# 	    output=hwsd_"${LAYER}"_"${VARIABLE}" \
# 	    $OVERWRITE
#     done
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl1 = hwsd_t_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl2 = hwsd_t_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl3 = hwsd_t_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl4 = hwsd_s_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl5 = hwsd_s_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl6 = hwsd_s_${VARIABLE}" \
#     	$OVERWRITE
#     r.mapcalc \
#     	"hwsd_${SOILGRID_VARIABLE}_sl7 = hwsd_s_${VARIABLE}" \
#     	$OVERWRITE
# done
