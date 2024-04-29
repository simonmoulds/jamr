#!/bin/bash

r.mask -r

# Base land/sea mask on ESA CCI data

# There is some discrepancy between ESA_CCI_WB and ESA_CCI_LC. To get
# around this we implement a two-step procedure:
# (i)  Aggregate by taking the minimum value, which will in effect
#      classify the 300m grid square as ocean if *any* fine resolution
#      grid squares are classified as ocean.
# (ii) Use the 2015 land cover map to identify ocean cells *if* the
#      LC map contains water (code 210) *and* the map created in (i)
#      is classified as ocean. 

RGN=0.002777777777777777
RGN_STR=globe_$(printf "%0.6f" ${RGN})Deg

# (i)  Aggregate 150m data to 300m by taking the minimum value.
#      As ocean=0, land=1, inland=2, this means that coarse grid
#      cells containing any number of fine resolution ocean grid
#      cells will also be classified as ocean. 
gdalwarp \
    -overwrite \
    -te -180 -90 180 90 \
    -tr 0.002777777777777 0.002777777777777 \
    -r min \
    ${ESACCIDIR}/ESACCI-LC-L4-WB-Ocean-Land-Map-150m-P13Y-2000-v4.0.tif \
    ../data/aux/mask/water_bodies_min_${RGN_STR}.tif

r.in.gdal \
    input=../data/aux/mask/water_bodies_min_${RGN_STR}.tif \
    output=water_bodies_min \
    $OVERWRITE

g.region region=globe_0.002778Deg
g.region -p
r.mapcalc \
    "ocean_min = if(water_bodies_min==0,1,0)" \
    $OVERWRITE

# (ii) Import land cover map (use 2015 as base year), and simplify
#      to land/water mask (water is code 210)
YEAR=2015
r.in.gdal \
    -a \
    input=${ESACCIDIR}/ESACCI-LC-L4-LCCS-Map-300m-P1Y-${YEAR}-v2.0.7.tif \
    output=esacci_lc_${YEAR} \
    $OVERWRITE

g.region region=globe_0.002778Deg
g.region -p
r.mapcalc \
    "esacci_lc_water = if(esacci_lc_${YEAR}==210,1,0)" \
    $OVERWRITE

# Calculate ocean grid cells as cells in which ESA CCI LC is classified as
# water *and* ESA CCI WB (@ 300m) is classified as ocean. 
r.mapcalc \
    "ocean = if(((ocean_min==1) && (esacci_lc_water==1)),1,0)" \
    $OVERWRITE

r.mapcalc \
    "esacci_land_frac_${RGN_STR} = 1 - ocean" \
    $OVERWRITE

r.out.gdal \
    input=esacci_land_frac_${RGN_STR} \
    output=${AUXDIR}/mask/land_sea_mask_${RGN_STR}.tif \
    format=GTiff \
    type=Byte \
    createopt="COMPRESS=DEFLATE" \
    $OVERWRITE

# # Import some additional data to check the correspondence between this
# # ocean mask and other land masks
# declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)
# for MERIT_RGN in "${MERIT_RGNS[@]}"
# do
#     MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
#     g.region region=${MERIT_RGN_STR}
#     r.mapcalc \
# 	"cama_land_frac_${MERIT_RGN_STR} = if(isnull(merit_draindir_trip_${MERIT_RGN_STR}),0,1)" \
# 	$OVERWRITE
#     r.out.gdal \
# 	input=cama_land_frac_${MERIT_RGN_STR} \
# 	output=${AUXDIR}/mask/cama_land_frac_${MERIT_RGN_STR}.tif \
# 	format=GTiff \
# 	type=Byte \
# 	createopt="COMPRESS=DEFLATE" \
# 	--overwrite
#     r.resamp.stats \
# 	-w \
# 	input=land \
# 	output=land_${MERIT_RGN_STR}_tmp \
# 	method=average \
# 	--overwrite
#     r.mapcalc \
# 	"land_${MERIT_RGN_STR} = if(land_${MERIT_RGN_STR}_tmp>0,1,0)" \
# 	--overwrite
#     r.out.gdal \
# 	input=land_${MERIT_RGN_STR} \
# 	output=${AUXDIR}/mask/land_sea_mask_${MERIT_RGN_STR}.tif \
# 	format=GTiff \
# 	type=Byte \
# 	createopt="COMPRESS=DEFLATE" \
# 	--overwrite	
# done

# HYDRO_RGN=0.0083333333333
# HYDRO_RGN_STR=globe_$(printf "%0.6f" ${HYDRO_RGN})Deg
# g.region region=${HYDRO_RGN_STR}
# r.mapcalc \
#     "hydrosheds_land_frac_${HYDRO_RGN_STR} = if(isnull(hydrosheds_draindir_trip_${HYDRO_RGN_STR}),0,1)" \
#     $OVERWRITE
# r.out.gdal \
#     input=hydrosheds_land_frac_${HYDRO_RGN_STR} \
#     output=${AUXDIR}/mask/hydrosheds_land_frac_${HYDRO_RGN_STR}.tif \
#     format=GTiff \
#     type=Byte \
#     createopt="COMPRESS=DEFLATE" \
#     --overwrite
# r.resamp.stats \
#     -w \
#     input=land \
#     output=land_${HYDRO_RGN_STR}_tmp \
#     method=average \
#     --overwrite
# r.mapcalc \
#     "land_${HYDRO_RGN_STR} = if(land_${HYDRO_RGN_STR}_tmp>0,1,0)" \
#     --overwrite
# r.out.gdal \
#     input=land_${HYDRO_RGN_STR} \
#     output=${AUXDIR}/mask/land_sea_mask_${HYDRO_RGN_STR}.tif \
#     format=GTiff \
#     type=Byte \
#     createopt="COMPRESS=DEFLATE" \
#     --overwrite	

# WFDEI_RGN=0.5
# WFDEI_RGN_STR=globe_$(printf "%0.6f" ${WFDEI_RGN})Deg
# Rscript process-wfdei.R		# easiest to do this in R
# g.region region=${WFDEI_RGN_STR}
# r.in.gdal \
#     input=../data/aux/mask/WFDEI_land_frac_globe_0.500000Deg.tif \
#     output=wfdei_land_frac_$WFDEI_RGN_STR \
#     --overwrite
# r.resamp.stats \
#     -w \
#     input=land \
#     output=land_${WFDEI_RGN_STR}_tmp \
#     method=average \
#     --overwrite
# r.mapcalc \
#     "land_${WFDEI_RGN_STR} = if(land_${WFDEI_RGN_STR}_tmp>0,1,0)" \
#     --overwrite
# r.out.gdal \
#     input=land_${WFDEI_RGN_STR} \
#     output=${AUXDIR}/mask/land_sea_mask_${WFDEI_RGN_STR}.tif \
#     format=GTiff \
#     type=Byte \
#     createopt="COMPRESS=DEFLATE" \
#     --overwrite	





# OLD (based on MERIT DEM):

# # Get a list of MERIT DEM files (we process these separately)
# find \
#     $MERITDIR \
#     -regextype posix-extended \
#     -regex '.*/[n|s][0-9]+[e|w][0-9]+_dem.tif$' \
#     > /tmp/merit_dem_filenames.txt

# # while read LN
# # do
# #     FN=${LN##*/}
# #     NM=${FN%.*}
# #     LON=$(echo $NM | sed 's/\([s|n].*\)\([e|w].*\)_dem/\2/g')
# #     LAT=$(echo $NM | sed 's/\([s|n].*\)\([e|w].*\)_dem/\1/g')
# #     OUTFILE=${AUXDIR}/dem/land_sea_mask_${LON}_${LAT}_${RGN_STR}.tif
# #     echo $OUTFILE

# #     if [[ ! -f $OUTFILE || $OVERWRITE == '--overwrite' ]]
# #     then	
# # 	r.in.gdal \
# # 	    -a \
# # 	    input="${LN}" \
# # 	    output=merit_dem \
# # 	    --overwrite

# # 	g.region rast=merit_dem
# # 	r.mapcalc \
# # 	    "land_sea_mask = if(isnull(merit_dem),0,1)" \
# # 	    --overwrite
	
# # 	g.region raster=merit_dem ewres=${RGN} nsres=${RGN}
# # 	g.region -p

# # 	r.resamp.stats \
# # 	    input=land_sea_mask \
# # 	    output=land_sea_mask_avg_${RGN_STR} \
# # 	    method=average \
# # 	    --overwrite

# # 	r.mapcalc \
# # 	    "land_sea_mask_${RGN_STR} = if(land_sea_mask_avg_${RGN_STR}>0,1,0)" \
# # 	    --overwrite

# # 	r.out.gdal \
# # 	    input=land_sea_mask_${RGN_STR} \
# # 	    output=${OUTFILE} \
# # 	    type=Byte \
# # 	    createopt="COMPRESS=DEFLATE" \
# # 	    --overwrite
# #     fi
# # done < /tmp/merit_dem_filenames.txt

# # Merge files
# find \
#     ${AUXDIR}/dem \
#     -regextype posix-extended \
#     -regex ".*/land_sea_mask_e[0-9]+_[n|s][0-9]+_${RGN_STR}.tif$" \
#     > /tmp/land_sea_mask_east_filenames.txt

# find \
#     ${AUXDIR}/dem \
#     -regextype posix-extended \
#     -regex ".*/land_sea_mask_w[0-9]+_[n|s][0-9]+_${RGN_STR}.tif$" \
#     > /tmp/land_sea_mask_west_filenames.txt

# gdalbuildvrt \
#     -overwrite \
#     -input_file_list /tmp/land_sea_mask_east_filenames.txt \
#     ${AUXDIR}/dem/land_sea_mask_east_hem_${RGN_STR}.vrt

# gdalbuildvrt \
#     -overwrite \
#     -input_file_list /tmp/land_sea_mask_west_filenames.txt \
#     ${AUXDIR}/dem/land_sea_mask_west_hem_${RGN_STR}.vrt

# gdalwarp \
#     -overwrite \
#     -te -180 -90 180 90 \
#     -tr 0.002777777777777 0.002777777777777 \
#     ${AUXDIR}/dem/land_sea_mask_east_hem_${RGN_STR}.vrt ${AUXDIR}/dem/land_sea_mask_west_hem_${RGN_STR}.vrt \
#     ${AUXDIR}/dem/land_sea_mask_${RGN_STR}.tif

# # # while read LN
# # # do
# # #     gdal_translate -expand RGB $LN tmp.tif
# # #     mv tmp.tif $LN
# # # done < /tmp/land_sea_mask_filenames.txt

# # eval `g.region -g`
# # gdalbuildvrt \
# #     -overwrite \
# #     -te -180 -90 180 90 \
# #     -tr 0.002777777777777 0.002777777777777 \
# #     -input_file_list /tmp/land_sea_mask_filenames.txt \
# #     ${AUXDIR}/dem/land_sea_mask_${RGN_STR}.vrt

# # # Note that ANTS masks the Aral Sea and Lake Victoria - I don't know
# # # why exactly (esp. not the Aral Sea), but I'm sure they have a good
# # # reason. I need to investigate this further.

# # # No need to do this - just import VRT
# # # gdal_translate \
# # #     ${AUXDIR}/dem/land_sea_mask_${RGN_STR}.vrt \
# # #     ${AUXDIR}/dem/land_sea_mask_${RGN_STR}.tif
