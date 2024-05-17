#!/usr/bin/env python3

import os
import re
import glob
import time
import math
import logging
import warnings

from typing import List 
from pathlib import Path
from collections import namedtuple
# from dataclasses import dataclass

import grass.script as gscript
import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from osgeo import gdal

import jamr.utils 
from jamr.dataset import DS, SFDS, MFDS, AncillaryDataset
from jamr.constants import REGIONS


# Configure logging 
log = logging.getLogger(__name__)

# TODO 
# - add POLARIS data [USA only]
# - add Saxton & Rawls PTFs https://doi.org/10.2136/sssaj2005.0117 [USA only]
# - add Toth et al PTFs [Europe only]

# SG_VARIABLES=['bdod', 'cec', 'clay', 'phh2o', 'sand', 'silt', 'soc']

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
                 soilhorizon,
                 region, 
                 overwrite):

        self.method = method
        self.clay_content = soilhorizon.mapnames.clay_content 
        self.sand_content = soilhorizon.mapnames.sand_content 
        self.silt_content = soilhorizon.mapnames.silt_content 
        self.soil_organic_carbon = soilhorizon.mapnames.soil_organic_carbon
        self.ph_index = soilhorizon.mapnames.ph_index
        self.cation_exchange_capacity = soilhorizon.mapnames.cation_exchange_capacity
        self.bulk_density = soilhorizon.mapnames.bulk_density
        self.horizon = soilhorizon.horizon.replace('-', '_')
        self.region = region 
        self.overwrite = overwrite 

    def _set_names(self):
        raise NotImplementedError()

class CosbyPTF(PTF):
    def __init__(self,
                 soilhorizon,
                 region,
                 overwrite):
        super().__init__('cosby', soilhorizon, region, overwrite)
        self._set_names() 

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
                 soilhorizon,
                 region,
                 overwrite):

        super().__init__(method, soilhorizon, region, overwrite)
        self._set_names() 

    def _set_names(self):
        self.n_mapname = f'n_{self.method}_{self.horizon}_{self.region}'
        self.alpha_mapname = f'alpha_{self.method}_{self.horizon}_{self.region}'
        self.psi_mapname = f'psi_{self.method}_{self.horizon}_{self.region}'
        self.b_mapname = f'b_{self.method}_{self.horizon}_{self.region}'
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
    	        f'A_{suffix}_{self.method}_{self.horizon}_{self.region} = ({self.alpha_mapname} * {suction}) ^ {self.n_mapname}',
                overwrite=self.overwrite
            )
            r.mapcalc(
                f'Se_{suffix}_{self.method}_{self.horizon}_{self.region} = (1 + A_{suffix}_{self.method}_{self.horizon}_{self.region}) '
                f'^ ((1 / {self.n_mapname}) - 1)',
                overwrite=self.overwrite
            )
            r.mapcalc(
    	        f'{theta_mapname} = (Se_{suffix}_{self.method}_{self.horizon}_{self.region} '
                f'* ({self.theta_sat_mapname} - {self.theta_res_mapname})) + {self.theta_res_mapname}',
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
                 soilhorizon,
                 region,
                 overwrite):

        super().__init__('tomasellahodnett', soilhorizon, region, overwrite)

    def van_genuchten_n(self): 
        try:
            r.mapcalc(
                (
                    f'{self.n_mapname} = exp((62.986 - (0.833 * {self.clay_content}) '
                    f'- (0.529 * ({self.soil_organic_carbon} / 10)) + (0.593 * {self.ph_index} / 10) '
                    f'+ (0.007 * {self.clay_content} * {self.clay_content}) '
                    f'- (0.014 * {self.sand_content} * {self.silt_content})) / 100)'
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
                    f'+ (2.440 * ({self.soil_organic_carbon} / 10)) - (0.076 * {self.cation_exchange_capacity}) '
                    f'- (11.331 * {self.ph_index} / 10) + (0.019 * {self.silt_content} * {self.silt_content})) / 100)'
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
                    f'- (31.42 * {self.bulk_density} * 0.001) + (0.018 * {self.cation_exchange_capacity}) '
                    f'+ (0.451 * {self.ph_index} / 10) - (0.0005 * {self.sand_content} * {self.clay_content}))'
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
                    f'+ (0.235 * {self.cation_exchange_capacity}) - (0.831 * {self.ph_index} / 10) '
                    f'+ (0.0018 * {self.clay_content} * {self.clay_content}) '
                    f'+ (0.0026 * {self.sand_content} * {self.clay_content}))'
                ),
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass

    def saturated_hydraulic_conductivity(self):
        # Tomasella & Hodnett do not provide a transfer function, so we use Cosby PTF instead
        try:
            r.mapcalc(
                f'{self.ksat_mapname} = (25.4 / (60 * 60)) '
                f'* (10 ^ (-0.60 - (0.0064 * {self.clay_content}) + (0.0126 * {self.sand_content})))',
                overwrite=self.overwrite
            )
        except grass.exceptions.CalledModuleError:
            pass


class USDATextureClass:
    def __init__(self, 
                 soilhorizon,
                 region,
                 overwrite):
 
        self.clay_content = soilhorizon.mapnames.clay_content 
        self.sand_content = soilhorizon.mapnames.sand_content 
        self.silt_content = soilhorizon.mapnames.silt_content 
        self.horizon = soilhorizon.horizon 
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
                f'& ({self.silt_content} >= {silt_min}) & ({self.silt_content} <= {silt_max}) '
                f'& ({self.clay_content} >= {clay_min}) & ({self.clay_content} <= {clay_max}), 1, 0)',
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
                 soilhorizon,
                 region,
                 overwrite):

        super().__init__('zhangschaap', soilhorizon, region, overwrite)

    def compute(self):
        self.usda = USDATextureClass(
            self.clay_content, self.sand_content, self.silt_content, 
            self.horizon, self.region, self.overwrite
        )
        self.usda.compute() 
        super().compute()

    def _zhang_schaap_equation(self, output, factors):
        try:
            r.mapcalc(
	            f'{output} = {self.usda.usda_clay_mapname} * {factors[0]} ' 
                f'+ {self.usda.usda_silty_clay_mapname} * {factors[1]} '
                f'+ {self.usda.usda_sandy_clay_mapname} * {factors[2]} '
                f'+ {self.usda.usda_clay_loam_mapname} * {factors[3]}'
                f'+ {self.usda.usda_silty_clay_loam_mapname} * {factors[4]}'
                f'+ {self.usda.usda_sandy_clay_loam_mapname} * {factors[5]}'
                f'+ {self.usda.usda_loam_mapname} * {factors[6]} '
                f'+ {self.usda.usda_silt_loam_mapname} * {factors[7]} '
                f'+ {self.usda.usda_sandy_loam_mapname} * {factors[8]} '
                f'+ {self.usda.usda_silt_mapname} * {factors[9]} '
                f'+ {self.usda.usda_loamy_sand_mapname} * {factors[10]} '
                f'+ {self.usda.usda_sand_mapname} * {factors[11]}',
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


SoilHorizonMaps = namedtuple(
    'SoilHorizonMaps', 
    ['clay_content', 'sand_content', 'silt_content', 'bulk_density', 'cation_exchange_capacity', 'ph_index', 'soil_organic_carbon'],
    defaults=(None,) * 7
)


class SoilGridsHorizon(MFDS):
    def __init__(self, soilgrids, horizon) -> None:
        self.soilgrids = soilgrids
        self.data_directory = soilgrids.data_directory
        self.scratch = soilgrids.scratch
        self.variables = soilgrids.variables 
        self.resolution = soilgrids.resolution
        self.summary_statistic = soilgrids.summary_statistic 
        self.horizon = horizon
        super().__init__(soilgrids.config, soilgrids.overwrite)

    @property
    def _filename_format(self):
        if self.resolution == 250: 
            return '{variable}_{horizon}_{statistic}.tif' 
        elif self.resolution == 1000:
            return '{variable}_{horizon}_{statistic}_1000.tif'
        elif self.resolution == 5000:
            return '{variable}_{horizon}_{statistic}_5000.tif'
        else:
            return None

    def get_input_filenames(self):
        filenames = {}
        for variable in self.variables:
            variable_abbr = SG_VARIABLES_ABBR[variable]
            filenames[variable] = self._filename_format.format(variable=variable_abbr, horizon=self.horizon, statistic=self.summary_statistic)        
        self.filenames = filenames

    def set_mapnames(self):
        mapnames = {} 
        horizon_fmt = self.horizon.replace('-', '_')
        for variable in self.variables:
            variable_abbr = SG_VARIABLES_ABBR[variable]
            mapnames[variable] = f'sg_{self.resolution}_{variable_abbr}_{horizon_fmt}_{self.summary_statistic}'
        self.mapnames = SoilHorizonMaps(**mapnames)

    def initial(self):
        self.preprocess()
        self.read()    

    def preprocess(self):
        preprocessed_filenames = {}
        opts = gdal.WarpOptions(format='GTiff', outputBounds=[-180, -90, 180, 90], xRes = 1 / 120., yRes = 1 / 120., dstSRS = 'EPSG:4326')
        for key, filename in self.filenames.items():
            basename, extension = Path(filename).stem, Path(filename).suffix 
            input_map = os.path.join(self.data_directory, filename)
            output_map = os.path.join(self.scratch, basename + '_ll' + extension)
            preprocessed_filenames[key] = output_map 
            if not os.path.exists(output_map) or self.overwrite:
                mymap = gdal.Warp(output_map, input_map, options=opts)
                mymap = None
        self.preprocessed_filenames = preprocessed_filenames

    def read(self):
        for key, filename in self.preprocessed_filenames.items():
            mapname = getattr(self.mapnames, key)
            try:
                r.in_gdal(input=filename, output=mapname, flags='a', overwrite=self.overwrite)
            except grass.exceptions.CalledModuleError:
                pass
            # TODO decide whether to fill with HWSD


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


class SoilGrids(MFDS):
    def __init__(self, 
                 config: dict, 
                 overwrite: bool) -> None:

        self.data_directory = config['soil']['soilgrids']['data_directory']
        self.scratch = config['main']['scratch_directory'] 
        self.variables = config['soil']['soilgrids']['variables']
        if not all([variable in SG_VARIABLES for variable in self.variables]):
            raise ValueError()

        self.horizons = config['soil']['soilgrids']['horizons']
        self.current_horizon = None
        if not all([horizon in SG_HORIZONS for horizon in self.horizons]):
            raise ValueError()

        self.resolution = config['soil']['soilgrids']['resolution']
        if not self.resolution in SG_RESOLUTIONS:
            raise ValueError()

        self.summary_statistic = config['soil']['soilgrids']['summary_statistic']
        if not self.summary_statistic in SG_SUMMARY_STATISTICS:
            raise ValueError() 

        super().__init__(config, overwrite)

    def get_input_filenames(self):
        pass

    def set_mapnames(self):
        pass

    def initial(self): 
        data = {}
        for horizon in self.horizons:
            self.current_horizon = horizon 
            horizon_obj = SoilGridsHorizon(self, horizon)
            horizon_obj.initial() 
            data[horizon] = horizon_obj

        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data) 

    def __setitem__(self, key, value):
        self.data[key] = value 

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)
    
    def items(self):
        return self.data.items() 
    
    def values(self):
        return self.data.values() 
    
    def keys(self):
        return self.data.keys()

# SOIL_DATASETS = ['SOILGRIDS']
# SOIL_PTF_CLASSES = {
#     'COSBY': CosbyPTF,
#     'TOMASELLAHODNETT': TomasellaHodnettPTF,
#     'ZHANGSCHAAP': ZhangSchaapPTF
# }
# SOIL_PTFS = list(SOIL_PTF_CLASSES.keys())


# class SoilProperties:
#     def __init__(self, 
#                  config: dict, 
#                  soil: SoilGrids,
#                  region: str, 
#                  overwrite: bool) -> None:

#         self.config = config
#         # if dataset.upper() not in SOIL_DATASETS:
#         #     raise ValueError(f'Soil dataset {dataset} not recognised')
#         self.region = region 
#         self.overwrite = overwrite  
#         self.ptf_class = None
#         jamr.utils.grass_remove_mask() 
#         jamr.utils.grass_set_named_region()

#     # def _load_soil_data(self):
#     #     if self.dataset == 'SOILGRIDS':
#     #         self.soildata = SoilGrids(self.config, SG_VARIABLES, SG_HORIZONS, '1km', 'mean', self.overwrite)
#     #     self.soildata.initial()

#     def initial(self): 
#         if self.ptf_class is None: 
#             raise ValueError('PTF method class is not set')
        
#         self.ptf = {}
#         for i in range(len(self.soildata)):
#             soilhorizon = self.soildata[i]
#             horizon = soilhorizon.horizon 
#             self.ptf[horizon] = self.ptf_class(soilhorizon, self.region, self.overwrite)

#     def compute(self):
#         for ptf in self.ptf.values():
#             ptf.compute()


class CosbySoilProperties(AncillaryDataset):
    def __init__(self, config, soil, region, overwrite):
        super().__init__(config, region, overwrite)
        self.soildata = soil
        self.initial() 

    def initial(self):
        self.ptf = {} 
        for horizon_name, horizon in self.soildata.items():
            self.ptf[horizon_name] = CosbyPTF(horizon, self.region, self.overwrite)

    def compute(self):
        for ptf in self.ptf.values():
            ptf.compute()

             
# class TomasellaHodnettSoilProperties(SoilProperties):
#     def __init__(self, config, dataset, region, overwrite):
#         super().__init__(config, dataset, region, overwrite)
#         self.ptf_class = TomasellaHodnettPTF


# class ZhangSchaapSoilProperties(SoilProperties):
#     def __init__(self, config, dataset, region, overwrite):
#         super().__init__(config, dataset, region, overwrite)
#         self.ptf_class = ZhangSchaapPTF


# def process_soil_data(config, region, overwrite):

#     # Remove mask
#     try:
#         r.mask(flags='r')
#     except grass.exceptions.CalledModuleError:
#         pass

#     # Load SoilGrids data
#     soilgrids = SoilGrids(config, SG_VARIABLES, SG_HORIZONS, '1km', 'mean', overwrite)
#     soilgrids.initial()

#     for i in range(len(soilgrids)):
#         soilhorizon = soilgrids[i]

#         cosbyptf = CosbyPTF(
#             soilhorizon.maps.clay_content, 
#             soilhorizon.maps.sand_content,
#             soilhorizon.horizon,
#             region,
#             overwrite
#         )
#         cosbyptf.compute()

#         tomasellahodnett = TomasellaHodnettPTF(
#             soilhorizon.maps.clay_content, 
#             soilhorizon.maps.sand_content, 
#             soilhorizon.maps.silt_content, 
#             soilhorizon.maps.soil_organic_carbon, 
#             soilhorizon.maps.ph_index, 
#             soilhorizon.maps.cation_exchange_capacity, 
#             soilhorizon.maps.bulk_density, 
#             soilhorizon.horizon,
#             region, 
#             overwrite
#         )
#         tomasellahodnett.compute()

#         zhangschaap = ZhangSchaapPTF(
#             soilhorizon.maps.clay_content,
#             soilhorizon.maps.sand_content,
#             soilhorizon.maps.silt_content,
#             soilhorizon.horizon,
#             region,
#             overwrite
#         )
#         zhangschaap.compute() 

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
