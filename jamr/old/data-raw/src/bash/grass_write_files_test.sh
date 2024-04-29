#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

# We restrict to Ghana, to make much faster.
g.region n=12N s=4N e=2E w=4W res=0:00:30
eval `g.region -g`
g.region -g

# Create directory to store results
OUTDIR=../data/test
if [ ! -d $OUTDIR ]
then
    mkdir $OUTDIR
else
    # clean directory
    rm -f $OUTDIR/*
fi

# ##################################### #
# grass_make_water_likelihood_surface.sh
# ##################################### #

# This is for computing non-standard regions
find \
    $AUXDIR/dem \
    -regextype posix-extended \
    -regex '.*/merit_dem_con_[0-9]+[E|W]_[0-9]+[S|N]_0.0008333Deg.tif$' \
    > /tmp/merit_dem_con_filenames.txt

gdalbuildvrt \
    -overwrite \
    -te $w $s $e $n \
    -tr 0.0008333333333 0.0008333333333 \
    -input_file_list /tmp/merit_dem_con_filenames.txt \
    $OUTDIR/merit_dem_con_test.vrt

gdal_translate $OUTDIR/merit_dem_con_test.vrt $OUTDIR/merit_dem_con_test.tif

find \
    $AUXDIR/synthetic_water_layer \
    -regextype posix-extended \
    -regex '.*/synthetic_water_layer_[0-9]+[E|W]_[0-9]+[S|N]_0.0008333Deg.tif$' \
    > /tmp/synthetic_water_layer_filenames.txt

gdalbuildvrt \
    -overwrite \
    -te $w $s $e $n \
    -tr 0.0008333333333 0.0008333333333 \
    -input_file_list /tmp/synthetic_water_layer_filenames.txt \
    $OUTDIR/synthetic_water_layer_test.vrt

gdal_translate $OUTDIR/synthetic_water_layer_test.vrt $OUTDIR/synthetic_water_layer_test.tif

# ##################################### #
# grass_make_elevation.sh
# ##################################### #

g.region \
    raster=merit_dem_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_globe_0.008333Deg \
    output=$OUTDIR/merit_dem_globe_0.008333Deg.tif \
    --overwrite
g.region \
    raster=merit_dem_globe_0.004167Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_globe_0.004167Deg \
    output=$OUTDIR/merit_dem_globe_0.004167Deg.tif \
    --overwrite
g.region \
    raster=merit_dem_globe_0.008333Deg_surf_hgt \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_globe_0.008333Deg_surf_hgt \
    output=$OUTDIR/merit_dem_globe_0.008333Deg_surf_hgt.tif \
    --overwrite

# ##################################### #
# grass_make_jules_routing_props.sh
# ##################################### #

declare -a MERIT_RGNS=(0.25 0.1 0.0833333333333 0.05 0.016666666666)

for MERIT_RGN in "${MERIT_RGNS[@]}"
do
    MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
    g.region \
	raster=merit_accum_cell_${MERIT_RGN_STR} \
	n=$n s=$s e=$e w=$w
    r.out.gdal \
	input=merit_accum_cell_${MERIT_RGN_STR} \
	output=$OUTDIR/merit_accum_cell_${MERIT_RGN_STR}.tif \
	--overwrite
    g.region \
	raster=merit_draindir_trip_${MERIT_RGN_STR} \
	n=$n s=$s e=$e w=$w
    r.out.gdal \
	input=merit_draindir_trip_${MERIT_RGN_STR} \
	output=$OUTDIR/merit_draindir_trip_${MERIT_RGN_STR}.tif \
	--overwrite
done

g.region \
    raster=hydrosheds_draindir_trip_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=hydrosheds_draindir_trip_globe_0.008333Deg \
    output=$OUTDIR/hydrosheds_draindir_trip_globe_0.008333Deg.tif \
    --overwrite

g.region \
    raster=hydrosheds_accum_cell_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=hydrosheds_accum_cell_globe_0.008333Deg \
    output=$OUTDIR/hydrosheds_accum_cell_globe_0.008333Deg.tif \
    --overwrite

# ##################################### #
# grass_make_jules_land_frac.sh
# ##################################### #

for MERIT_RGN in "${MERIT_RGNS[@]}"
do
    MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
    g.region \
	raster=cama_land_frac_${MERIT_RGN_STR} \
	n=$n s=$s e=$e w=$w
    r.out.gdal \
	input=cama_land_frac_${MERIT_RGN_STR} \
	output=$OUTDIR/cama_land_frac_${MERIT_RGN_STR}.tif \
	--overwrite
done

g.region \
    raster=hydrosheds_land_frac_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=hydrosheds_land_frac_globe_0.008333Deg \
    output=$OUTDIR/hydrosheds_land_frac_globe_0.008333Deg.tif \
    --overwrite

# ##################################### #
# grass_make_jules_topography_props.sh
# ##################################### #

g.region \
    raster=merit_dem_slope_globe_0.004167Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_slope_globe_0.004167Deg \
    output=$OUTDIR/merit_dem_slope_globe_0.004167Deg.tif \
    --overwrite
g.region \
    raster=hydrosheds_dem_topidx_globe_0.004167Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=hydrosheds_dem_topidx_globe_0.004167Deg \
    output=$OUTDIR/hydrosheds_dem_topidx_globe_0.004167Deg.tif \
    --overwrite
g.region \
    raster=merit_dem_topidx_globe_0.002083Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_topidx_globe_0.002083Deg \
    output=$OUTDIR/merit_dem_topidx_globe_0.002083Deg.tif \
    --overwrite

# ##################################### #
# grass_make_jules_frac.sh
# ##################################### #

for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous urban water bare_soil snow_ice
do
    g.region \
	raster=lc_${LC}_2015_globe_0.008333Deg \
	n=$n s=$s e=$e w=$w
    r.out.gdal \
	input=lc_${LC}_2015_globe_0.008333Deg \
	output=$OUTDIR/lc_${LC}_2015_globe_0.008333Deg.tif \
	--overwrite

    g.region \
	raster=lc_${LC}_2015_globe_0.008333Deg_weighted_elev \
	n=$n s=$s e=$e w=$w
    r.out.gdal \
	input=lc_${LC}_2015_globe_0.008333Deg_weighted_elev \
	output=$OUTDIR/lc_${LC}_2015_globe_0.008333Deg_weighted_elev.tif \
	--overwrite

done

# ##################################### #
# grass_make_jules_soil_props.sh
# ##################################### #

r.out.gdal \
    input=background_albedo \
    output=$OUTDIR/background_albedo.tif \
    --overwrite

for LAYER in 1 2 3 4 5 6 7
do
    for VAR in ph clay
    do
	g.region \
	    raster=${VAR}_sl${LAYER} \
	    n=$n s=$s e=$e w=$w
	r.out.gdal \
	    input=${VAR}_sl${LAYER} \
	    output=$OUTDIR/${VAR}_sl${LAYER}.tif \
	    --overwrite
    done

    for VAR in hcap hcon k_sat theta_wilt theta_crit theta_sat b lambda psi_m alpha_m
    do
	for METHOD in cosby tomas
	do
	    g.region \
		raster=${VAR}_${METHOD}_sl${LAYER} \
		n=$n s=$s e=$e w=$w
	    r.out.gdal \
		input=${VAR}_${METHOD}_sl${LAYER} \
		output=$OUTDIR/${VAR}_${METHOD}_sl${LAYER}.tif \
		--overwrite
	done
    done
done

# ##################################### #
# grass_make_jules_overbank_props.sh
# ##################################### #

g.region \
    raster=merit_dem_logn_mean_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_logn_mean_globe_0.008333Deg \
    output=$OUTDIR/merit_dem_logn_mean_globe_0.008333Deg.tif \
    --overwrite

g.region \
    raster=merit_dem_logn_stdev_globe_0.008333Deg \
    n=$n s=$s e=$e w=$w
r.out.gdal \
    input=merit_dem_logn_stdev_globe_0.008333Deg \
    output=$OUTDIR/merit_dem_logn_stdev_globe_0.008333Deg.tif \
    --overwrite
