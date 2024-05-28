#!/usr/bin/env python3

import os
import re
import glob
import time
# import grass.script as gscript

import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r

from osgeo import gdal

from jamr.constants import REGIONS

from jamr.utils import *
from jamr.dataset import AncillaryDataset


RGN = 1 / 360. 
RGN_STR = 'globe_0.002778Deg'


class LandFraction(AncillaryDataset):
    pass


class ESALandFraction(LandFraction):
    def __init__(self, 
                 config, 
                 inputdata,
                 region,
                 overwrite):

        super().__init__(config, region, overwrite)
        self.inputdata = inputdata
        self.set_mapnames() 

    def set_mapnames(self): 
        self.mapname = f'esacci_landfrac_{self.region}'

    def compute(self):
        # Resample waterbodies map to the landcover map resolution
        p = gscript.start_command('g.region', 
                                  raster=self.inputdata.landcover.mapnames[2015])
        stdout, stderr = p.communicate()
        
        p = gscript.start_command('r.resamp.stats', 
                                  input=self.inputdata.landcover.mapnames[2015],
                                  output='water_bodies_min_tmp',
                                  method='minimum',
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        # if not grass_map_exists('raster', self.mapname, 'PERMANENT') or self.overwrite:
        # FIXME resolution might be wrong here
        p = gscript.start_command('g.region', region=self.region, stderr=PIPE)
        stdout, stderr = p.communicate()

        p = gscript.start_command('r.mapcalc', 
                                  expression='ocean_min_tmp = if(water_bodies_min_tmp == 0, 1, 0)', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        esaccilc_ref_map = self.inputdata.landcover[2015]
        p = gscript.start_command('r.mapcalc', 
                                  expression=f'esacci_lc_water_tmp = if({esaccilc_ref_map} == 210, 1, 0)', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        p = gscript.start_command('r.mapcalc', 
                                  expression=f'ocean_tmp = if((ocean_min_tmp==1 && esacci_lc_water_tmp==1), 1, 0)', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()

        p = gscript.start_command('r.mapcalc', 
                                  expression=f'{self.mapname} = 1 - ocean_tmp', 
                                  overwrite=self.overwrite, 
                                  stderr=PIPE)
        stdout, stderr = p.communicate()
    
    def cleanup(self):
        # Idea here is to clean up any temporary maps
        pass










# def process_land_fraction(config, overwrite=False):
#     # There is some discrepancy between ESA_CCI_WB and ESA_CCI_LC. To get
#     # around this we implement a two-step procedure:
#     # (i)  Aggregate by taking the minimum value, which will in effect
#     #      classify the 300m grid square as ocean if *any* fine resolution
#     #      grid squares are classified as ocean.
#     # (ii) Use the 2015 land cover map to identify ocean cells *if* the
#     #      LC map contains water (code 210) *and* the map created in (i)
#     #      is classified as ocean.

#     # Read ESACCI water bodies dataset (@150m)
#     esa_data_file = config['landfraction']['esa']['data_file']
#     try:
#         r.in_gdal(input=esa_data_file, output='esa_ocean_land', flags='a', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass 

#     g.region(region='globe_0.002778Deg')

#     try:
#         r.resamp_stats(input='esa_ocean_land', output='water_bodies_min', method='minimum', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass

#     try:
#         r.mapcalc('ocean_min = if(water_bodies_min == 0, 1, 0)', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass

#     # Calculate ocean grid cells as cells in which ESA CCI LC is classified as water *and* ESA CCI WB (@300m) is classified as ocean 
#     esa_lc_data_directory = config['landcover']['esa']['data_directory']
#     esa_lc_data_file = get_esacci_landcover_map(esa_lc_data_directory, 2015)
#     try:
#         r.in_gdal(input=esa_lc_data_file, output='esacci_lc_ref', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass 

#     try:
#         r.mapcalc('esacci_lc_water = if(esacci_lc_ref == 210, 1, 0)', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass

#     try:
#         r.mapcalc('ocean = if((ocean_min==1 && esacci_lc_water==1), 1, 0)', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass 

#     try:
#         r.mapcalc(f'esacci_landfrac_{RGN_STR} = 1 - ocean', overwrite=overwrite)
#     except grass.exceptions.CalledModuleError:
#         pass 

#     return 0


# # Calculate ocean grid cells as cells in which ESA CCI LC is classified as
# # water *and* ESA CCI WB (@ 300m) is classified as ocean.
# r.mapcalc "ocean = if((ocean_min==1 && esacci_lc_water==1), 1, 0)" $OVERWRITE
# r.mapcalc \
#     "esacci_land_frac_${RGN_STR} = 1 - ocean" \
#     $OVERWRITE

# # Write output at multiple resolutions (used in the jules_frac routine)
# declare -a RGNS=(0.25 0.1 0.083333333333333 0.05 0.01666666666666 0.008333333333333)
# for RGN in "${RGNS[@]}"
# do
#     RGN_STR=globe_$(printf "%0.6f" ${RGN})Deg
#     g.region region=${RGN_STR}
#     r.resamp.stats \
# 	-w \
# 	input=esacci_land_frac_globe_0.002778Deg \
# 	output=esacci_land_frac_${RGN_STR}_tmp \
# 	method=average \
# 	--overwrite
#     r.mapcalc \
# 	"esacci_land_frac_${RGN_STR} = if(esacci_land_frac_${RGN_STR}_tmp>0,1,0)" \
# 	--overwrite
#     g.remove -f type=raster name=esacci_land_frac_${RGN_STR}_tmp
# done
# # (ii) Import land cover map (use 2015 as base year), and simplify
# #      to land/water mask (water is code 210)
# YEAR=2015
# r.in.gdal \
#     -a \
#     input=$ESACCIDIR/ESACCI-LC-L4-LCCS-Map-300m-P1Y-${YEAR}-v2.0.7.tif \
#     output=esacci_lc_${YEAR} \
#     $OVERWRITE


# g.region region=globe_0.002778Deg
# g.region -p
# r.mapcalc "ocean_min = if(water_bodies_min == 0, 1, 0)" $OVERWRITE
# r.mask -r


# # ===========================================================
# # Region based on ESA CCI data
# # ===========================================================

# RGN=0.002777777777777777
# RGN_STR=globe_$(printf "%0.6f" ${RGN})Deg

# # (i)  Aggregate 150m data to 300m by taking the minimum value.
# #      As ocean=0, land=1, inland=2, this means that coarse grid
# #      cells containing any number of fine resolution ocean grid
# #      cells will also be classified as ocean.
# gdalwarp \
#     -overwrite \
#     -te -180 -90 180 90 \
#     -tr 0.002777777777777777777 0.002777777777777777777 \
#     -r min \
#     $ESACCIDIR/ESACCI-LC-L4-WB-Ocean-Land-Map-150m-P13Y-2000-v4.0.tif \
#     $AUXDIR/land_frac/water_bodies_min_${RGN_STR}.tif

# # Import these external data sources
# r.in.gdal \
#     -a \
#     input=$AUXDIR/land_frac/water_bodies_min_${RGN_STR}.tif \
#     output=water_bodies_min \
#     $OVERWRITE

# g.region region=globe_0.002778Deg
# g.region -p
# r.mapcalc "ocean_min = if(water_bodies_min == 0, 1, 0)" $OVERWRITE

# # (ii) Import land cover map (use 2015 as base year), and simplify
# #      to land/water mask (water is code 210)
# YEAR=2015
# r.in.gdal \
#     -a \
#     input=$ESACCIDIR/ESACCI-LC-L4-LCCS-Map-300m-P1Y-${YEAR}-v2.0.7.tif \
#     output=esacci_lc_${YEAR} \
#     $OVERWRITE

# g.region region=globe_0.002778Deg
# g.region -p
# r.mapcalc "esacci_lc_water = if(esacci_lc_${YEAR} == 210, 1, 0)" $OVERWRITE

# # Calculate ocean grid cells as cells in which ESA CCI LC is classified as
# # water *and* ESA CCI WB (@ 300m) is classified as ocean.
# r.mapcalc "ocean = if((ocean_min==1 && esacci_lc_water==1), 1, 0)" $OVERWRITE
# r.mapcalc \
#     "esacci_land_frac_${RGN_STR} = 1 - ocean" \
#     $OVERWRITE

# # Write output at multiple resolutions (used in the jules_frac routine)
# declare -a RGNS=(0.25 0.1 0.083333333333333 0.05 0.01666666666666 0.008333333333333)
# for RGN in "${RGNS[@]}"
# do
#     RGN_STR=globe_$(printf "%0.6f" ${RGN})Deg
#     g.region region=${RGN_STR}
#     r.resamp.stats \
# 	-w \
# 	input=esacci_land_frac_globe_0.002778Deg \
# 	output=esacci_land_frac_${RGN_STR}_tmp \
# 	method=average \
# 	--overwrite
#     r.mapcalc \
# 	"esacci_land_frac_${RGN_STR} = if(esacci_land_frac_${RGN_STR}_tmp>0,1,0)" \
# 	--overwrite
#     g.remove -f type=raster name=esacci_land_frac_${RGN_STR}_tmp
# done





# # NOT USED:

# # ===========================================================
# # Region based on CaMa-Flood (MERIT)
# # ===========================================================

# declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)
# for MERIT_RGN in "${MERIT_RGNS[@]}"
# do
#     MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
#     g.region region=${MERIT_RGN_STR}
#     r.mapcalc \
# 	"cama_land_frac_${MERIT_RGN_STR} = if(isnull(merit_draindir_trip_${MERIT_RGN_STR}),0,1)" \
# 	$OVERWRITE
# done

# # ===========================================================
# # Region based on HydroSHEDS data (land fraction @ 1km)
# # ===========================================================

# HYDRO_RGN=0.0083333333333
# HYDRO_RGN_STR=globe_$(printf "%0.6f" ${HYDRO_RGN})Deg
# g.region region=${HYDRO_RGN_STR}
# r.mapcalc \
#     "hydrosheds_land_frac_${HYDRO_RGN_STR} = if(isnull(hydrosheds_draindir_trip_${HYDRO_RGN_STR}),0,1)" \
#     $OVERWRITE
# # # Import some additional data to check the correspondence between this
# # # ocean mask and other land masks
# # declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)
# # for MERIT_RGN in "${MERIT_RGNS[@]}"
# # do
# #     MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
# #     g.region region=${MERIT_RGN_STR}
# #     r.mapcalc \
# # 	"cama_land_frac_${MERIT_RGN_STR} = if(isnull(merit_draindir_trip_${MERIT_RGN_STR}),0,1)" \
# # 	$OVERWRITE
# #     r.out.gdal \
# # 	input=cama_land_frac_${MERIT_RGN_STR} \
# # 	output=${AUXDIR}/mask/cama_land_frac_${MERIT_RGN_STR}.tif \
# # 	format=GTiff \
# # 	type=Byte \
# # 	createopt="COMPRESS=DEFLATE" \
# # 	--overwrite
# #     r.resamp.stats \
# # 	-w \
# # 	input=land \
# # 	output=land_${MERIT_RGN_STR}_tmp \
# # 	method=average \
# # 	--overwrite
# #     r.mapcalc \
# # 	"land_${MERIT_RGN_STR} = if(land_${MERIT_RGN_STR}_tmp>0,1,0)" \
# # 	--overwrite
# #     r.out.gdal \
# # 	input=land_${MERIT_RGN_STR} \
# # 	output=${AUXDIR}/mask/land_sea_mask_${MERIT_RGN_STR}.tif \
# # 	format=GTiff \
# # 	type=Byte \
# # 	createopt="COMPRESS=DEFLATE" \
# # 	--overwrite
# # done

# # HYDRO_RGN=0.0083333333333
# # HYDRO_RGN_STR=globe_$(printf "%0.6f" ${HYDRO_RGN})Deg
# # g.region region=${HYDRO_RGN_STR}
# # r.mapcalc \
# #     "hydrosheds_land_frac_${HYDRO_RGN_STR} = if(isnull(hydrosheds_draindir_trip_${HYDRO_RGN_STR}),0,1)" \
# #     $OVERWRITE
# # r.out.gdal \
# #     input=hydrosheds_land_frac_${HYDRO_RGN_STR} \
# #     output=${AUXDIR}/mask/hydrosheds_land_frac_${HYDRO_RGN_STR}.tif \
# #     format=GTiff \
# #     type=Byte \
# #     createopt="COMPRESS=DEFLATE" \
# #     --overwrite
# # r.resamp.stats \
# #     -w \
# #     input=land \
# #     output=land_${HYDRO_RGN_STR}_tmp \
# #     method=average \
# #     --overwrite
# # r.mapcalc \
# #     "land_${HYDRO_RGN_STR} = if(land_${HYDRO_RGN_STR}_tmp>0,1,0)" \
# #     --overwrite
# # r.out.gdal \
# #     input=land_${HYDRO_RGN_STR} \
# #     output=${AUXDIR}/mask/land_sea_mask_${HYDRO_RGN_STR}.tif \
# #     format=GTiff \
# #     type=Byte \
# #     createopt="COMPRESS=DEFLATE" \
# #     --overwrite

# # WFDEI_RGN=0.5
# # WFDEI_RGN_STR=globe_$(printf "%0.6f" ${WFDEI_RGN})Deg
# # Rscript process-wfdei.R		# easiest to do this in R
# # g.region region=${WFDEI_RGN_STR}
# # r.in.gdal \
# #     input=../data/aux/mask/WFDEI_land_frac_globe_0.500000Deg.tif \
# #     output=wfdei_land_frac_$WFDEI_RGN_STR \
# #     --overwrite
# # r.resamp.stats \
# #     -w \
# #     input=land \
# #     output=land_${WFDEI_RGN_STR}_tmp \
# #     method=average \
# #     --overwrite
# # r.mapcalc \
# #     "land_${WFDEI_RGN_STR} = if(land_${WFDEI_RGN_STR}_tmp>0,1,0)" \
# #     --overwrite
# # r.out.gdal \
# #     input=land_${WFDEI_RGN_STR} \
# #     output=${AUXDIR}/mask/land_sea_mask_${WFDEI_RGN_STR}.tif \
# #     format=GTiff \
# #     type=Byte \
# #     createopt="COMPRESS=DEFLATE" \
# #     --overwrite
