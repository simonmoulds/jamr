#!/usr/bin/env python3

import os
import numpy as np
import netCDF4 

import logging

from subprocess import PIPE

import grass.script as gscript

from grass.script import array as garray 
from grass.script import core as grass 

from grass.pygrass.modules.shortcuts import raster as r

from jamr.process.ancillarydataset import AncillaryDataset
from jamr.utils.grass_utils import *
from jamr.utils.utils import (raster2array, add_lat_lon_dims_2d, F8_FILLVAL)
from jamr.utils.constants import (F8_FILLVAL,
                                  ZHANGSCHAAP_FACTORS, 
                                  CRITICAL_POINT_SUCTION, 
                                  WILTING_POINT_SUCTION,
                                  JULES_SOIL_VARIABLES)


LOGGER = logging.getLogger(__name__)


class SoilPropsFactory:
    @staticmethod
    def create_soil_props(method, config, inputdata, overwrite):
        if method == 'Cosby':
            return SoilProperties('Cosby', config, inputdata, overwrite)
        # elif method == 'TomasellaHodnett':
        #     return TomasellaHodnett()
        else:
            raise ValueError(f'Unknown soil properties method: {method}')


class PTF(AncillaryDataset):
    def __init__(self, 
                 method,
                 config,
                 inputdata,
                 soilhorizon,
                 overwrite):

        # Implement a new __init__() method 
        self.method = method
        self.config = config 
        self.inputdata = inputdata
        self.soilhorizon = soilhorizon
        self.overwrite = overwrite
        self.region_name = config['region']['name']
        # Copy mapnames
        self.clay_content = soilhorizon.mapnames.clay_content 
        self.sand_content = soilhorizon.mapnames.sand_content 
        self.silt_content = soilhorizon.mapnames.silt_content 
        self.soil_organic_carbon = soilhorizon.mapnames.soil_organic_carbon
        self.ph_index = soilhorizon.mapnames.ph_index
        self.cation_exchange_capacity = soilhorizon.mapnames.cation_exchange_capacity
        self.bulk_density = soilhorizon.mapnames.bulk_density
        self.horizon = soilhorizon.horizon.replace('-', '_')
        # Variables computed by this class
        # self.variables = JULES_SOIL_VARIABLES
        grass_remove_mask()


def cosby_brooks_corey_b(b, clay_content, sand_content, overwrite): 
    p = gscript.start_command('r.mapcalc', 
                              expression=f'{b} = (3.10 + 0.157 * {clay_content} - 0.003 * {sand_content})',
                              overwrite=overwrite, 
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


def cosby_brooks_corey_psi_m(psi_m, clay_content, sand_content, overwrite):
    p = gscript.start_command('r.mapcalc', 
                              expression=f'{psi_m} = 0.01 * (10 ^ (2.17 - (0.0063 * {clay_content}) - (0.0158 * {sand_content})))',
                              overwrite=overwrite, 
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


def cosby_brooks_corey_ksat(ksat, clay_content, sand_content, overwrite):
    p = gscript.start_command('r.mapcalc',
                              expression=f'{ksat} = (25.4 / (60 * 60)) * (10 ^ (-0.60 - (0.0064 * {clay_content}) + (0.0126 * {sand_content})))',
                              overwrite=overwrite,
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


def cosby_brooks_corey_theta_sat(theta_sat, clay_content, sand_content, overwrite):
    p = gscript.start_command('r.mapcalc',
                              expression=f'{theta_sat} = 0.01 * (50.5 - 0.037 * {clay_content} - 0.142 * {sand_content})', 
                              overwrite=overwrite,
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


def cosby_theta_res(theta_res, overwrite):
    p = gscript.start_command('r.mapcalc',
                              expression=f'{theta_res} = 0', 
                              overwrite=overwrite,
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


def brooks_corey_eqn(theta, theta_sat, psi_m, b, suction, overwrite):
    p = gscript.start_command('r.mapcalc',
                              expression=f'{theta} = {theta_sat} * ({psi_m} / {suction}) ^ (1 / {b})',
                              overwrite=overwrite,
                              stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0


class CosbyPTF(PTF):
    def __init__(self,
                 config,
                 inputdata,
                 soilhorizon,
                 overwrite):
        super().__init__('cosby', config, inputdata, soilhorizon, overwrite)
        self.variables = JULES_SOIL_VARIABLES
        self._set_mapnames() 

    def _set_mapnames(self):
        for variable in self.variables:
            vars(self)[f'{variable}_mapname_native'] = f'{variable}_{self.method}_{self.horizon}_{self.region_name}_native'
            vars(self)[f'{variable}_mapname'] = f'{variable}_{self.method}_{self.horizon}_{self.region_name}'

    def compute(self, landfrac_mapname):
        
        # Apply mask based on supplied land fraction map 
        r.mask(raster=landfrac_mapname, maskcats=1)

        # Compute soil properties 
        self.brooks_corey_b()
        self.air_entry_pressure() 
        self.saturated_hydraulic_conductivity()
        self.saturated_water_content()
        self.critical_water_content()
        self.wilting_point()
        self.residual_water_content()

        # Remove mask
        r.mask(flags='r')

    def brooks_corey_b(self):
        LOGGER.info(f'Computing Brooks Corey b for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        cosby_brooks_corey_b(
            self.b_mapname_native, self.soilhorizon.mapnames.clay_content, 
            self.soilhorizon.mapnames.sand_content, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.b_mapname_native, output_map=self.b_mapname, method='average')

    def air_entry_pressure(self): 
        LOGGER.info(f'Computing air entry pressure for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        cosby_brooks_corey_psi_m(
            self.psi_m_mapname_native, self.soilhorizon.mapnames.clay_content, 
            self.soilhorizon.mapnames.sand_content, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.psi_m_mapname_native, output_map=self.psi_m_mapname, method='average')

    def saturated_hydraulic_conductivity(self):
        LOGGER.info(f'Computing saturated hydraulic conductivity for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        cosby_brooks_corey_ksat(
            self.ksat_mapname_native, self.soilhorizon.mapnames.clay_content, 
            self.soilhorizon.mapnames.sand_content, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.ksat_mapname_native, output_map=self.ksat_mapname, method='average')

    def saturated_water_content(self):
        LOGGER.info(f'Computing saturated water content for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        cosby_brooks_corey_theta_sat(
            self.theta_sat_mapname_native, self.soilhorizon.mapnames.clay_content, 
            self.soilhorizon.mapnames.sand_content, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.theta_sat_mapname_native, output_map=self.theta_sat_mapname, method='average')

    def critical_water_content(self):
        LOGGER.info(f'Computing critical water content for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        brooks_corey_eqn(
            self.theta_crit_mapname_native, self.theta_sat_mapname_native, self.psi_m_mapname_native, 
            self.b_mapname_native, CRITICAL_POINT_SUCTION, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.theta_crit_mapname_native, output_map=self.theta_crit_mapname, method='average')

    def wilting_point(self):
        LOGGER.info(f'Computing wilting point for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        brooks_corey_eqn(
            self.theta_wilt_mapname_native, self.theta_sat_mapname_native, self.psi_m_mapname_native, 
            self.b_mapname_native, WILTING_POINT_SUCTION, self.overwrite
        )
        self._set_target_region()
        self._resample(input_map=self.theta_wilt_mapname_native, output_map=self.theta_wilt_mapname, method='average')

    def residual_water_content(self):
        LOGGER.info(f'Computing residual water content for soil horizon {self.horizon}')
        self._set_native_region(self.clay_content)
        cosby_theta_res(self.theta_res_mapname_native, self.overwrite) 
        self._set_target_region()
        self._resample(input_map=self.theta_res_mapname_native, output_map=self.theta_res_mapname, method='average')


class VanGenuchtenPTF(PTF):
    def __init__(self, 
                 method,
                 config,
                 soilhorizon,
                 overwrite):

        super().__init__(method, config, soilhorizon, overwrite)
        self._set_mapnames() 

    def _set_mapnames(self):
        self.n_mapname = f'n_{self.method}_{self.horizon}_{self.region_name}'
        self.alpha_mapname = f'alpha_{self.method}_{self.horizon}_{self.region_name}'
        self.psi_mapname = f'psi_{self.method}_{self.horizon}_{self.region_name}'
        self.b_mapname = f'b_{self.method}_{self.horizon}_{self.region_name}'
        self.ksat_mapname = f'ksat_{self.method}_{self.horizon}_{self.region_name}' 
        self.theta_sat_mapname = f'theta_sat_{self.method}_{self.horizon}_{self.region_name}' 
        self.theta_crit_mapname = f'theta_crit_{self.method}_{self.horizon}_{self.region_name}'
        self.theta_wilt_mapname = f'theta_wilt_{self.method}_{self.horizon}_{self.region_name}' 
        self.theta_res_mapname = f'theta_res_{self.method}_{self.horizon}_{self.region_name}'

    def compute(self, landfrac_mapname):
        # grass_set_region_from_raster(raster=self.clay_content,
        #                              n=self.config['region']['north'],
        #                              s=self.config['region']['south'],
        #                              e=self.config['region']['east'],
        #                              w=self.config['region']['west'])
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
                 config, 
                 soilhorizon,
                 overwrite):

        super().__init__('tomasellahodnett', config, soilhorizon, overwrite)

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
    """Data set class to compute maps of USDA soil texture categories."""
    def __init__(self, 
                 config,
                 soilhorizon,
                 overwrite):
 
        self.clay_content = soilhorizon.mapnames.clay_content 
        self.sand_content = soilhorizon.mapnames.sand_content 
        self.silt_content = soilhorizon.mapnames.silt_content 
        self.horizon = soilhorizon.horizon 
        self.region_name = config['region']['name']
        self.overwrite = overwrite 
        self._set_mapnames() 

    def compute(self):
        grass_set_region_from_raster(raster=self.clay_content,
                                     n=self.config['region']['north'],
                                     s=self.config['region']['south'],
                                     e=self.config['region']['east'],
                                     w=self.config['region']['west'])
        self._usda_texture_class()

    def _set_mapnames(self):
        self.usda_clay_mapname = f'usda_clay_{self.horizon}_{self.region_name}'
        self.usda_sandy_clay_mapname = f'usda_sandy_clay_{self.horizon}_{self.region_name}'
        self.usda_silty_clay_mapname = f'usda_silty_clay_{self.horizon}_{self.region_name}'
        self.usda_sandy_clay_loam_mapname = f'usda_sandy_clay_loam_{self.horizon}_{self.region_name}'
        self.usda_clay_loam_mapname = f'usda_clay_loam_{self.horizon}_{self.region_name}'
        self.usda_silty_clay_loam_mapname = f'usda_silty_clay_loam_{self.horizon}_{self.region_name}'
        self.usda_sandy_loam_mapname = f'usda_sandy_loam_{self.horizon}_{self.region_name}'
        self.usda_loam_mapname = f'usda_loam_{self.horizon}_{self.region_name}'
        self.usda_silt_loam_mapname = f'usda_silt_loam_{self.horizon}_{self.region_name}'
        self.usda_silt_mapname = f'usda_silt_{self.horizon}_{self.region_name}'
        self.usda_loamy_sand_mapname = f'usda_loamy_sand_{self.horizon}_{self.region_name}'
        self.usda_sand_mapname = f'usda_sand_{self.horizon}_{self.region_name}'

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
                 config,
                 soilhorizon,
                 overwrite):

        super().__init__('zhangschaap', config, soilhorizon, overwrite)

    def compute(self):
        grass_set_region_from_raster(raster=self.clay_content,
                                     n=self.config['region']['north'],
                                     s=self.config['region']['south'],
                                     e=self.config['region']['east'],
                                     w=self.config['region']['west'])
        self.usda = USDATextureClass(self.config, self.soilhorizon, self.overwrite)
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
        # Step 1: native resolution
        self._zhang_schaap_equation(self.alpha_mapname, ZHANGSCHAAP_FACTORS['alpha'])
        # Step 2: target resolution

    def van_genuchten_n(self):
        self._zhang_schaap_equation(self.n_mapname, ZHANGSCHAAP_FACTORS['n'])

    def residual_water_content(self):
        self._zhang_schaap_equation(self.theta_res_mapname, ZHANGSCHAAP_FACTORS['theta_res'])

    def saturated_water_content(self):
        self._zhang_schaap_equation(self.theta_sat_mapname, ZHANGSCHAAP_FACTORS['theta_sat'])

    def saturated_hydraulic_conductivity(self):
        self._zhang_schaap_equation(self.ksat_mapname, ZHANGSCHAAP_FACTORS['ksat'])


class PTFFactory:
    @staticmethod
    def create_ptf(method, config, inputdata, horizon, overwrite):
        if method == 'Cosby':
            return CosbyPTF(config, inputdata, horizon, overwrite)
        # elif method == 'TomasellaHodnett':
        #     return TomasellaHodnettPTF(config, inputdata, horizon, overwrite)
        # elif method == 'ZhangSchaap':
        #     return ZhangSchaapPTF(config, inputdata, horizon, overwrite)
        else:
            raise ValueError(f'Unknown soil properties method: {method}')


class SoilProperties:
    def __init__(self, method, config, inputdata, overwrite):
        self.method = method
        self.config = config 
        self.inputdata = inputdata 
        self.overwrite = overwrite 
        self.variables = JULES_SOIL_VARIABLES

    def initial(self):
        self.ptf = {} 
        for horizon_name, horizon in self.inputdata.soil.items():
            self.ptf[horizon_name] = PTFFactory().create_ptf(self.method, self.config, self.inputdata, horizon, self.overwrite)

    def compute(self, landfrac_mapname):
        # Compute maps at native resolution
        for ptf in self.ptf.values():
            ptf.compute(landfrac_mapname)

    def get_data_arrays(self, property):
        arr_list = []
        for ptf in self.ptf.values():
            arr = garray.array(mapname=vars(ptf)[f'{property}_mapname'])
            arr_list.append(arr)

        arr = np.stack(arr_list) 
        return arr
       

    def write_netcdf(self, landfrac_mapname):
        coords, bnds, land_frac = raster2array(landfrac_mapname)
        output_filename = os.path.join(self.config['main']['output_directory'], f'jamr_soil_props.nc')

        # TODO put in config?
        x_dim_name = 'x'
        y_dim_name = 'y'
        soil_dim_name = 'soil'

        nco = netCDF4.Dataset(output_filename, 'w', format='NETCDF4')
        ntype = len(self.ptf)
        nco = add_lat_lon_dims_2d(nco, x_dim_name, y_dim_name, coords[0], coords[1], bnds[0], bnds[1])

        nco.createDimension(soil_dim_name, ntype)
        var = nco.createVariable(soil_dim_name, 'i4', (soil_dim_name,))
        var.units = '1'
        var.standard_name = soil_dim_name
        var.long_name = soil_dim_name
        var[:] = np.arange(1, ntype+1)
        
        for property in self.variables:
            arr = self.get_data_arrays(property)
            mask = np.broadcast_to(np.logical_not(land_frac), arr.shape)
            arr = np.ma.array(arr, mask=mask, dtype=np.float64, fill_value=F8_FILLVAL)

            var = nco.createVariable(
                property, 'f8', (soil_dim_name, y_dim_name, x_dim_name),
                fill_value=F8_FILLVAL
            )
            var.units = '1'
            var.standard_name = property
            var.grid_mapping = 'latitude_longitude'
            var[:] = arr

             
        nco.close()