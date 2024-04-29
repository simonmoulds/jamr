#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

# ############################################# #
# FOR TESTING (IGP) - COMMENT OUT IF NOT NEEDED #
# ############################################# #

# EAST=100E
# WEST=60E
# NORTH=35N
# SOUTH=20N

# # 0.008333 degrees
# g.region \
#     e=$EAST w=$WEST n=$NORTH s=$SOUTH \
#     res=0:00:30 \
#     save=globe_0.008333Deg \
#     --overwrite

# # 0.002083 degrees (250m soil)
# g.region \
#     e=$EAST w=$WEST n=$NORTH s=$SOUTH \
#     res=0:00:07.5 \
#     save=globe_0.002083Deg \
#     --overwrite

# # 0.004167 degrees (topography)
# g.region \
#     e=$EAST w=$WEST n=$NORTH s=$SOUTH \
#     res=0:00:15 \
#     save=globe_0.004167Deg \
#     --overwrite

# ######################################################### #
# ######################################################### #
#
# Define the GRASS region
#
# ######################################################### #
# ######################################################### #

REGION=globe_0.008333Deg
g.region region="${REGION}"
g.region -p

# ######################################################### #
# ######################################################### #
#
# JULES_PDM
#
# ######################################################### #
# ######################################################### #

# Compute average slope, which is needed in the PDM and TOPMODEL schemes
if [[ ! -f "${SLOPE_FN}" || ! -f "${FEXP_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then    
    # Only do the computation if output files do not exist, or overwrite is set
    r.resamp.stats \
	-w \
	input=merit_dem_slope_globe_0.004167Deg \
	output=merit_dem_slope_"${REGION}" \
	method=average \
	--overwrite
    # set null values to zero (this should already be the case)
    r.null \
	map=merit_dem_slope_"${REGION}" \
	null=0
fi    

# Write slope to output directory
if [[ ! -f "${SLOPE_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    echo "Writing $SLOPE_FN..."
    r.out.gdal \
	input=merit_dem_slope_"${REGION}" \
	output="${SLOPE_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
fi

# ######################################################### #
# ######################################################### #
#
# JULES_TOPMODEL
#
# ######################################################### #
# ######################################################### #

# NB write ti maps at native resolution for aggregation later

# Topographic index based on geomorpho90m
# #######################################
if [[ ! -f "${MERIT_TI_MEAN_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    g.region region=globe_0.002083Deg
    r.null \
	map=merit_dem_topidx_globe_0.002083Deg \
	null=0
    r.out.gdal \
	input=merit_dem_topidx_globe_0.002083Deg \
	output="${MERIT_TI_MEAN_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
fi

# Topographic index based on Marthews et al 2015
# ##############################################
echo "${HYDRO_TI_MEAN_FN}"
echo "${OVERWRITE}"
if [[ ! -f "${HYDRO_TI_MEAN_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    echo "Hello, world"
    g.region region=globe_0.004167Deg
    r.null \
	map=hydrosheds_dem_topidx_globe_0.004167Deg \
	null=0
    r.out.gdal \
	input=hydrosheds_dem_topidx_globe_0.004167Deg \
	output="${HYDRO_TI_MEAN_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
fi

# Fexp is computed with MERIT data
# ################################
if [[ ! -f "${FEXP_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    g.region region=globe_0.004167Deg
    r.mapcalc \
    	"merit_dem_fexp_tmp_globe_0.004167Deg = (1 + 150 * (merit_dem_slope_globe_0.004167Deg / 100)) / 100" \
    	--overwrite
    r.mapcalc \
    	"merit_dem_fexp_globe_0.004167Deg = min(merit_dem_fexp_tmp_globe_0.004167Deg, 0.4)" \
    	--overwrite    
    r.null \
	map=merit_dem_fexp_globe_0.004167Deg \
	null=0	
    r.out.gdal \
	input=merit_dem_fexp_globe_0.004167Deg \
	output="${FEXP_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
    g.remove \
	-f \
	type=raster \
	name=merit_dem_fexp_tmp_globe_0.004167Deg 2> /dev/null
fi    

# ######################################################### #
# ######################################################### #
#
# JULES_RIVERS
#
# ######################################################### #
# ######################################################### #

declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)

if [[ ! -f "${MERIT_DRAINDIR_FN}" || ! -f "${MERIT_ACCUM_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    for MERIT_RGN in "${MERIT_RGNS[@]}"
    do
	RGN_STR=globe_$(printf "%0.6f" "${MERIT_RGN}")Deg
	g.region region="${RGN_STR}"
	echo "Writing merit drainage direction @ 1km..."
	r.out.gdal \
	    input=merit_draindir_trip_"${RGN_STR}" \
	    output="${MERIT_DIRECTION_BASENM}"_"${RGN_STR}".tif \
	    type=Byte \
	    createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	    --overwrite
	echo "Writing merit accumulated area @ 1km..."
	r.out.gdal \
	    input=merit_accum_cell_"${RGN_STR}" \
	    output="${MERIT_AREA_BASENM}"_"${RGN_STR}".tif \
	    type=Int32 \
	    createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	    --overwrite
    done    
fi

if [[ ! -f "${HYDRO_DRAINDIR_FN}" || ! -f "${HYDRO_ACCUM_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    RGN_STR=globe_0.008333Deg
    g.region region="${RGN_STR}"
    echo "Writing hydrosheds drainage direction @ 1km..."
    r.out.gdal \
	input=hydrosheds_draindir_trip_globe_0.008333Deg \
	output="${HYDRO_DIRECTION_BASENM}"_"${RGN_STR}".tif \
	type=Byte \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
    echo "Writing hydrosheds accumulated area @ 1km..."
    r.out.gdal \
	input=hydrosheds_accum_cell_globe_0.008333Deg \
	output="${HYDRO_AREA_BASENM}"_"${RGN_STR}".tif \
	type=Int32 \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
fi

# ######################################################### #
# ######################################################### #
#
# JULES_LAND_FRAC
#
# ######################################################### #
# ######################################################### #

g.region region="${REGION}"

declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)

# If routing is used then we base JULES_LAND_FRAC on the routing data
if [[ ! -f "${MERIT_LAND_FRAC_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    for MERIT_RGN in "${MERIT_RGNS[@]}"
    do
	RGN_STR=globe_$(printf "%0.6f" "${MERIT_RGN}")Deg	
	r.out.gdal \
	    input=cama_land_frac_${RGN_STR} \
	    output="${MERIT_LAND_FRAC_BASENM}"_"${RGN_STR}".tif \
	    format=GTiff \
	    --overwrite
    done
fi

if [[ ! -f "${HYDRO_LAND_FRAC_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then
    HYDRO_RGN_STR=globe_0.008333Deg
    r.out.gdal \
	input=cama_land_frac_${HYDRO_RGN_STR} \
	output=${HYDRO_LAND_FRAC_FN} \
	format=GTiff \
	--overwrite
fi

# If routing is not used then JULES_LAND_FRAC is based on ESA data
if [[ ! -f "${ESA_LAND_FRAC_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then	
    r.resamp.stats \
	-w \
	input=esacci_land_frac_globe_0.002778Deg \
	output=esacci_land_frac_"${REGION}"_tmp \
	method=average \
	--overwrite
    r.mapcalc \
	"esacci_land_frac_${REGION} = if(esacci_land_frac_${REGION}_tmp>0,1,0)" \
	--overwrite
    r.out.gdal \
	input=esacci_land_frac_"${REGION}" \
	output="${ESA_LAND_FRAC_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
    g.remove \
	-f \
	type=raster \
	name=esacci_land_frac_"${REGION}"_tmp 2> /dev/null
fi
LAND_FRAC_MAP=esacci_land_frac_"${REGION}"

# ######################################################### #
# ######################################################### #
#
# JULES_FRAC
#
# ######################################################### #
# ######################################################### #

g.region region="${REGION}"

declare -a YEARS=({1992..2015})
# declare -a YEARS=(2015)

# # TODO: consider what to do about sea-level
# # -> currently we set null values (i.e. sea) to zero
# # -> 8/12/20: I think this is the right thing to do, here
# r.null map=merit_dem_globe_0.008333Deg_surf_hgt null=0
# r.resamp.stats \
#     -w \
#     input=merit_dem_globe_0.008333Deg_surf_hgt \
#     output=merit_dem_avg_surf_hgt_${REGION} \
#     method=average \
#     --overwrite

# merit_dem_globe_0.008333Deg_surf_hgt
if [[ ! -f ${SURF_HGT_FN} || "${OVERWRITE}" == '--overwrite' ]]
then
    r.mask raster=esacci_land_frac_${REGION}
    r.out.gdal \
	input=merit_dem_${REGION}_surf_hgt \
	output=${SURF_HGT_FN} \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
    r.mask -r
fi

# Loop through JULES land cover fractions
for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass urban water bare_soil snow_ice tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous
do
    for YEAR in "${YEARS[@]}"
    do		
	LC_FN="${FRAC_BASENM}"_"${LC}"_"${YEAR}"_"${REGION}".tif
	LC_WEIGHTED_ELEV_FN="${WEIGHTED_ELEV_BASENM}"_"${LC}"_"${YEAR}"_"${REGION}".tif
	if [[ ! -f "${LC_FN}" || ! -f "${LC_SURF_HGT_FN}" || "${OVERWRITE}" == '--overwrite' ]]
	then
	    # N.B we don't need to do any resampling here because
	    # the native resolution is 0.008333 degrees
	    # average fraction of lc
	    echo "Writing ESA CCI $YEAR $LC fraction @ 1km..."
	    r.out.gdal \
		input=lc_"${LC}"_"${YEAR}"_globe_0.008333Deg \
		output="${LC_FN}" \
		createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
		--overwrite
	    echo "Writing ESA CCI $YEAR $LC weighted elevation @ 1km..."
	    r.out.gdal \
		input=lc_"${LC}"_"${YEAR}"_globe_0.008333Deg_weighted_elev \
		output="${LC_WEIGHTED_ELEV_FN}" \
		createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
		--overwrite
	fi		
    done
done
		    
# ######################################################### #
# ######################################################### #
#
# JULES_SOIL_PROPS
#
# ######################################################### #
# ######################################################### #

g.region region="${REGION}"

declare -a METHODS=(cosby tomas rosetta3)
for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
do
    # b/hcap/hcon/satcon/sathh/sm_crit/sm_sat/sm_wilt
    for VARIABLE in b hcap hcon k_sat psi_m theta_crit theta_sat theta_wilt
    do
	for METHOD in "${METHODS[@]}"
	do
	    SOIL_VAR_FN="${SOIL_BASENM}"_"${VARIABLE}"_"${METHOD}"_"${HORIZON}"_"${REGION}".tif
	    if [[ ! -f "${SOIL_VAR_FN}" || "${OVERWRITE}" == '--overwrite' ]]
	    then		    
		echo "Writing SoilGrids $METHOD $VARIABLE @ $HORIZON @ 1km..."
		r.out.gdal \
		    input="${VARIABLE}"_"${METHOD}"_"${HORIZON}"_"${REGION}" \
		    output="${SOIL_VAR_FN}" \
		    createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
		    --overwrite
	    fi
	done
    done
    # ph/clay
    for VARIABLE in ph clay
    do
	SOIL_VAR_FN="${SOIL_BASENM}"_"${VARIABLE}"_"${HORIZON}"_"${REGION}".tif
	if [[ ! -f "${SOIL_VAR_FN}" || "${OVERWRITE}" == '--overwrite' ]]
	then		    
	    echo "Writing SoilGrids $VARIABLE @ $HORIZON @ 1km..."
	    r.out.gdal \
		input="${VARIABLE}"_"${HORIZON}"_"${REGION}" \
		output="${SOIL_VAR_FN}" \
		createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
		--overwrite
	fi	    
    done    
done    
    
g.region region="${REGION}"

if [[ ! -f "${ALBSOIL_FN}" || "${OVERWRITE}" == '--overwrite' ]]
then	
    echo "Writing background soil albedo @ 1km..."
    r.out.gdal \
	input=background_soil_albedo_${REGION} \
	output="${ALBSOIL_FN}" \
	createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	--overwrite
fi    

# ######################################################### #
# ######################################################### #
#
# JULES_OVERBANK
#
# ######################################################### #
# ######################################################### #

find \
    ${AUXDIR}/dem \
    -regextype posix-extended \
    -regex '.*/merit_dem_con_min_[0-9]+[E|W]_[0-9]+[N|S]_globe_0.008333Deg.tif$' \
    > /tmp/merit_dem_con_min_filenames.txt

find \
    ${AUXDIR}/dem \
    -regextype posix-extended \
    -regex '.*/merit_dem_con_mean_[0-9]+[E|W]_[0-9]+[N|S]_globe_0.008333Deg.tif$' \
    > /tmp/merit_dem_con_mean_filenames.txt

gdalbuildvrt \
    -overwrite \
    -te -180 -90 180 90 \
    -tr 0.0083333333333 0.0083333333333 \
    -input_file_list /tmp/merit_dem_con_min_filenames.txt \
    ${AUXDIR}/dem/merit_dem_con_min_globe_0.008333Deg.vrt

gdalbuildvrt \
    -overwrite \
    -te -180 -90 180 90 \
    -tr 0.0083333333333 0.0083333333333 \
    -input_file_list /tmp/merit_dem_con_mean_filenames.txt \
    ${AUXDIR}/dem/merit_dem_con_mean_globe_0.008333Deg.vrt

# convert to geotiff
gdal_translate ${AUXDIR}/dem/merit_dem_con_min_globe_0.008333Deg.vrt ${LOGN_DIR}/merit_dem_con_min_globe_0.008333Deg.tif

gdal_translate ${AUXDIR}/dem/merit_dem_con_mean_globe_0.008333Deg.vrt ${LOGN_DIR}/merit_dem_con_mean_globe_0.008333Deg.tif
    
