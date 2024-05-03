#!/usr/bin/env python3

# r.mask -r

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

# # ===========================================================
# # Region based on ESA CCI data
# # ===========================================================

# # There is some discrepancy between ESA_CCI_WB and ESA_CCI_LC. To get
# # around this we implement a two-step procedure:
# # (i)  Aggregate by taking the minimum value, which will in effect
# #      classify the 300m grid square as ocean if *any* fine resolution
# #      grid squares are classified as ocean.
# # (ii) Use the 2015 land cover map to identify ocean cells *if* the
# #      LC map contains water (code 210) *and* the map created in (i)
# #      is classified as ocean.

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
