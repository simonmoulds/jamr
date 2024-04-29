#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain
g.region region=${REGION}

# Create tmp file to store JULES output files
TEMPFILE=/tmp/jules_filenames.txt
if [[ -f $TEMPFILE ]]
then
    rm -f $TEMPFILE
fi
touch $TEMPFILE

# ######################################################### #
# ######################################################### #
#
# JULES_PDM
#
# ######################################################### #
# ######################################################### #

SLOPE_FN=${OUTDIR}/geotiff/merit_dem_slope_${REGION}.tif
MERIT_FEXP_FN=${OUTDIR}/geotiff/merit_dem_fexp_${REGION}.tif

# Compute average slope, which is needed in the PDM and TOPMODEL schemes
g.region region=${REGION}
if [[ $TOPMODEL == 1 || $PDM == 1 ]]
then
    # Only do the computation if output files do not exist, or overwrite is set
    if [[ ! -f $SLOPE_FN || ! -f $MERIT_FEXP_FN || $OVERWRITE == '--overwrite' ]]
    then    
	r.resamp.stats \
	    -w \
	    input=merit_dem_slope_globe_0.004167Deg \
	    output=merit_dem_slope_${REGION} \
	    method=average \
	    --overwrite
	# set null values to zero (this should already be the case)
	r.null \
	    map=merit_dem_slope_${REGION} \
	    null=0
    fi    
fi

# Write slope to output directory
g.region region=${REGION}
if [[ $PDM == 1 ]]
then
    if [[ ! -f $SLOPE_FN || $OVERWRITE == '--overwrite' ]]
    then	
	r.out.gdal \
	    input=merit_dem_slope_${REGION} \
	    output=${SLOPE_FN} \
	    $OVERWRITE
    fi
    # Write filename to temp file
    echo "SLOPE_FN=$SLOPE_FN" >> $TEMPFILE
fi

# ######################################################### #
# ######################################################### #
#
# JULES_TOPMODEL
#
# ######################################################### #
# ######################################################### #

# Topographic index: geomorpho90m is preferred because it's
# consistent with MERIT, but we also include HydroSHEDS (via Toby Marthews)

MERIT_TOPIDX_STDEV_FN=${OUTDIR}/geotiff/merit_dem_topidx_stddev_${REGION}.tif
MERIT_TOPIDX_MEAN_FN=${OUTDIR}/geotiff/merit_dem_topidx_mean_${REGION}.tif
HYDRO_TOPIDX_STDEV_FN=${OUTDIR}/geotiff/hydrosheds_dem_topidx_stddev_${REGION}.tif
HYDRO_TOPIDX_MEAN_FN=${OUTDIR}/geotiff/hydrosheds_dem_topidx_mean_${REGION}.tif

g.region region=${REGION}
if [[ $TOPMODEL == 1 ]]
then
    # compute topographic index using either MERIT or HydroSHEDS data
    if [[ ! -f $MERIT_TOPIDX_STDEV_FN || ! -f $MERIT_TOPIDX_MEAN_FN || $OVERWRITE == '--overwrite' ]]
    then
	
	# Topographic index based on geomorpho90m
	# #######################################
	
	r.resamp.stats \
	    -w \
	    input=merit_dem_topidx_globe_0.002083Deg \
	    output=merit_dem_topidx_mean_${REGION} \
	    method=average \
	    --overwrite	
	r.resamp.stats \
	    -w \
	    input=merit_dem_topidx_globe_0.002083Deg \
	    output=merit_dem_topidx_stddev_${REGION} \
	    method=stddev \
	    --overwrite	
	# ensure any null values are set to zero
	r.null \
	    map=merit_dem_topidx_mean_${REGION} \
	    null=0
	r.null \
	    map=merit_dem_topidx_stddev_${REGION} \
	    null=0	
	r.out.gdal \
	    input=merit_dem_topidx_mean_${REGION} \
	    output=${MERIT_TOPIDX_MEAN_FN} \
	    --overwrite
	r.out.gdal \
	    input=merit_dem_topidx_stddev_${REGION} \
	    output=${MERIT_TOPIDX_STDEV_FN} \
	    --overwrite
    fi

    if [[ ! -f $HYDRO_TOPIDX_STDEV_FN || ! -f $HYDRO_TOPIDX_MEAN_FN || $OVERWRITE == '--overwrite' ]]
    then	    
	# (ii) Marthews et al 2015
	r.resamp.stats \
	    -w \
	    input=hydrosheds_dem_topidx_globe_0.004167Deg \
	    output=hydrosheds_dem_topidx_mean_${REGION} \
	    method=average \
	    --overwrite
	r.resamp.stats \
	    -w \
	    input=hydrosheds_dem_topidx_globe_0.004167Deg \
	    output=hydrosheds_dem_topidx_stddev_${REGION} \
	    method=stddev \
	    --overwrite

	# ensure any null values are set to zero
	r.null \
	    map=hydrosheds_dem_topidx_mean_${REGION} \
	    null=0
	r.null \
	    map=hydrosheds_dem_topidx_stddev_${REGION} \
	    null=0
	
	r.out.gdal \
	    input=hydrosheds_dem_topidx_mean_${REGION} \
	    output=${HYDRO_TOPIDX_MEAN_FN} \
	    --overwrite
	r.out.gdal \
	    input=hydrosheds_dem_topidx_stddev_${REGION} \
	    output=${HYDRO_TOPIDX_STDEV_FN} \
	    --overwrite
    fi
    
    # Fexp is only calculated using MERIT data
    if [[ ! -f $MERIT_FEXP_FN || $OVERWRITE == '--overwrite' ]]
    then
	
	# decay factor describing how ksat decreases with
	# depth below the standard soil column (m-1)

	# TODO - find out whether this should be computed at fine scale and aggregated
	r.mapcalc \
	    "merit_dem_fexp_tmp_${REGION} = (1 + 150 * (merit_dem_slope_${REGION} / 100)) / 100" \
	    --overwrite
	r.mapcalc \
	    "merit_dem_fexp_${REGION} = min(merit_dem_fexp_tmp_${REGION}, 0.4)" \
	    --overwrite
	
	# ensure any null values are set to zero
	r.null \
	    map=merit_dem_fexp_${REGION} \
	    null=0	
	r.out.gdal \
	    input=merit_dem_fexp_${REGION} \
	    output=${MERIT_FEXP_FN} \
	    --overwrite
    fi    
    echo "MERIT_TOPIDX_STDEV_FN=$MERIT_TOPIDX_STDEV_FN" >> $TEMPFILE
    echo "MERIT_TOPIDX_MEAN_FN=$MERIT_TOPIDX_MEAN_FN" >> $TEMPFILE
    echo "MERIT_FEXP_FN=$MERIT_FEXP_FN" >> $TEMPFILE
    echo "HYDRO_TOPIDX_STDEV_FN=$HYDRO_TOPIDX_STDEV_FN" >> $TEMPFILE
    echo "HYDRO_TOPIDX_MEAN_FN=$HYDRO_TOPIDX_MEAN_FN" >> $TEMPFILE    
fi

# Clean up:
if [[ $TOPMODEL == 1 || $PDM == 1 ]]
then
    g.remove -f type=raster name=merit_dem_slope_${REGION} 2> /dev/null
fi

if [[ $TOPMODEL == 1 ]]
then
    g.remove -f type=raster name=merit_dem_fexp_${REGION} 2> /dev/null
    g.remove -f type=raster name=merit_dem_topidx_mean_${REGION} 2> /dev/null
    g.remove -f type=raster name=merit_dem_topidx_stddev_${REGION} 2> /dev/null
    g.remove -f type=raster name=hydrosheds_dem_topidx_mean_${REGION} 2> /dev/null
    g.remove -f type=raster name=hydrosheds_dem_topidx_stddev_${REGION} 2> /dev/null
fi

# ######################################################### #
# ######################################################### #
#
# JULES_RIVERS
#
# ######################################################### #
# ######################################################### #

# The river routing maps cannot be resampled, so firstly we need to know
# whether the user-specified region aligns with the maps. We do this outside
# of the routing control structure because the tests are useful when
# deciding which type of landmask to use.

# Obtain region parameters (ewres/nsres/n/s/e/w):
eval `g.region -g`

# First we test whether the region resolution is the same in both directions
if [ $ewres == $nsres ]
then
    TEST1=1
else
    TEST1=0
fi

# Next, test whether the region resolution matches one of the resolutions
# for which routing maps are available
TEST2=$(python3 -c "print(1) if $ewres in [0.25, 0.1, 1/12, 0.05, 1/60, 1/120] else print(0)")

# Lastly, see whether the region aligns. We do this by asking GRASS to change
# the region to align with the relevant global region. If the bounding box
# changes as a result of this request, we infer that the regions do not align.
TEST3=0

if [[ $TEST2 == 1 ]]
then    
    nn=$n
    ss=$s
    ee=$e
    ww=$w
    g.region region=globe_$(printf "%0.6f" ${ewres})Deg
    r.mapcalc "tmp = 1" --overwrite
    g.region region=${REGION}    
    g.region align=tmp    
    eval `g.region -g`
    if [[ $nn == $n && $ss == $s && $ee == $e && $ww == $w ]]
    then
	TEST3=1
    fi
    g.remove -f type=raster name=tmp 2> /dev/null
fi
g.region region=${REGION}    
eval `g.region -g`
USEMERIT=$(python3 -c "print(1) if $ewres in [0.25, 0.1, 1/12, 0.05, 1/60] else print(0)")

# Set output filenames
MERIT_DRAINDIR_FN=${OUTDIR}/geotiff/merit_draindir_trip_${REGION}.tif
MERIT_ACCUM_FN=${OUTDIR}/geotiff/merit_accum_cell_${REGION}.tif
HYDRO_DRAINDIR_FN=${OUTDIR}/geotiff/hydrosheds_draindir_trip_${REGION}.tif
HYDRO_ACCUM_FN=${OUTDIR}/geotiff/hydrosheds_accum_cell_${REGION}.tif

if [[ $ROUTING == 1 ]]
then
    
    if [[ $TEST1 == 0 || $TEST2 == 0 || $TEST3 == 0 ]]
    then
	echo
	echo "ERROR: the specified region is incompatible with the available routing maps. Exiting..."
	echo
	exit
    fi

    g.region region=${REGION}    
    if [[ $USEMERIT == 1 ]]
    then
	
	if [[ ! -f $MERIT_DRAINDIR_FN || ! -f $MERIT_ACCUM_FN || $OVERWRITE == '--overwrite' ]]
	then
	    MERIT_REGION=globe_$(printf "%0.6f" ${ewres})Deg    
	    r.out.gdal \
		input=merit_draindir_trip_${MERIT_REGION} \
		output=${MERIT_DRAINDIR_FN} \
		--overwrite
	    r.out.gdal \
		input=merit_accum_cell_${MERIT_REGION} \
		output=${MERIT_ACCUM_FN} \
		--overwrite
	fi
	echo "DRAINDIR_FN=$MERIT_DRAINDIR_FN" >> $TEMPFILE
	echo "ACCUM_FN=$MERIT_ACCUM_FN" >> $TEMPFILE
    else	
	if [[ ! -f $HYDRO_DRAINDIR_FN || ! -f $HYDRO_ACCUM_FN || $OVERWRITE == '--overwrite' ]]
	then	    	
	    r.out.gdal \
		input=hydrosheds_draindir_trip_globe_0.008333Deg \
		output=${HYDRO_DRAINDIR_FN} \
		type=Byte \
		$OVERWRITE
	    r.out.gdal \
		input=hydrosheds_accum_cell_globe_0.008333Deg \
		output=${HYDRO_ACCUM_FN} \
		type=Int32 \
		$OVERWRITE
	fi
	echo "DRAINDIR_FN=$HYDRO_DRAINDIR_FN" >> $TEMPFILE
	echo "ACCUM_FN=$HYDRO_ACCUM_FN" >> $TEMPFILE
    fi    
fi

# ######################################################### #
# ######################################################### #
#
# JULES_LAND_FRAC
#
# ######################################################### #
# ######################################################### #

g.region region=$REGION

if [[ $TEST1 == 1 && $TEST2 == 1 && $TEST3 == 1 && $FILE_LAND_FRAC == 0 ]]
then
    # in this case routing is enabled and either MERIT or HydroSHEDS
    # is being used as the underlying routing maps
    eval `g.region -g`
    if [[ $USEMERIT == 1 ]]
    then
	MERIT_LAND_FRAC_FN=${OUTDIR}/geotiff/merit_jules_land_frac_${REGION}.tif
	if [[ ! -f $MERIT_LAND_FRAC_FN || $OVERWRITE == '--overwrite' ]]
	then	    
	    MERIT_REGION=globe_$(printf "%0.6f" ${ewres})Deg    
	    r.out.gdal \
		input=cama_land_frac_${MERIT_REGION} \
		output=${MERIT_LAND_FRAC_FN} \
		format=GTiff \
		--overwrite
	fi
	LAND_FRAC_MAP=cama_land_frac_${MERIT_REGION}
	echo "JULES_LAND_FRAC_FN=$MERIT_LAND_FRAC_FN" >> $TEMPFILE
	echo "PRODUCT=MERIT" >> $TEMPFILE	
    else
	HYDRO_LAND_FRAC_FN=${OUTDIR}/geotiff/hydro_jules_land_frac_${REGION}.tif
	if [[ ! -f $HYDRO_LAND_FRAC_FN || $OVERWRITE == '--overwrite' ]]
	then	    
	    HYDRO_REGION=globe_$(printf "%0.6f" ${ewres})Deg
	    r.out.gdal \
		input=hydrosheds_land_frac_${HYDRO_REGION} \
		output=${HYDRO_LAND_FRAC_FN} \
		format=GTiff \
		type=Byte \
		createopt="COMPRESS=DEFLATE" \
		--overwrite
	fi
	LAND_FRAC_MAP=hydrosheds_land_frac_${HYDRO_REGION}
	echo "JULES_LAND_FRAC_FN=$HYDRO_LAND_FRAC_FN" >> $TEMPFILE
	echo "PRODUCT=HYDRO" >> $TEMPFILE
    fi    
else
    # in this case there is no routing, so either land fraction is
    # user-supplied, or it is derived from the land fraction
    # map based on ESA CCI data
    CUSTOM_LAND_FRAC_FN=${OUTDIR}/geotiff/jules_custom_land_frac_${REGION}.tif
    if [[ $FILE_LAND_FRAC == 1 ]]
    then    
	r.in.gdal \
	    -a \
	    input=$FILE \
	    output=land_frac_${REGION} \
	    --overwrite
	r.mapcalc \
	    "custom_land_frac_${REGION} = if(land_frac_${REGION}>0,1,0)" \
	    $OVERWRITE
	r.out.gdal \
	    input=custom_land_frac_${REGION} \
	    output=${CUSTOM_LAND_FRAC_FN} \
	    createopt="COMPRESS=DEFLATE" \
	    $OVERWRITE
	g.remove -f type=raster name=land_frac_${REGION} 2> /dev/null
    else	
	# Write custom region
	if [[ ! -f $CUSTOM_LAND_FRAC_FN || $OVERWRITE == '--overwrite' ]]
	then	
	    r.resamp.stats \
		-w \
		input=esacci_land_frac_globe_0.002778Deg \
		output=esacci_land_frac_${REGION} \
		method=average \
		$OVERWRITE
	    r.mapcalc \
		"custom_land_frac_${REGION} = if(esacci_land_frac_${REGION}>0,1,0)" \
		$OVERWRITE
	    r.out.gdal \
		input=custom_land_frac_${REGION} \
		output=${CUSTOM_LAND_FRAC_FN} \
		createopt="COMPRESS=DEFLATE" \
		$OVERWRITE
	    
	    g.remove -f type=raster name=esacci_land_frac_${REGION} 2> /dev/null
	fi
    fi    
    LAND_FRAC_MAP=custom_land_frac_${REGION}
    echo "JULES_LAND_FRAC_FN=$CUSTOM_LAND_FRAC_FN" >> $TEMPFILE
    echo "PRODUCT=CUSTOM" >> $TEMPFILE	
fi

# ######################################################### #
# ######################################################### #
#
# JULES_FRAC
#
# ######################################################### #
# ######################################################### #

g.region region=${REGION}

# declare -a YEARS=({1992..2015})
declare -a YEARS=(2015)

if [[ $NINEPFT == 1 || $FIVEPFT == 1 ]]
then    
    # TODO: consider what to do about sea-level
    # -> currently we set null values (i.e. sea) to zero
    # -> 8/12/20: I think this is the right thing to do, here
    r.null map=merit_dem_globe_0.008333Deg_surf_hgt null=0
    r.resamp.stats \
	-w \
	input=merit_dem_globe_0.008333Deg_surf_hgt \
	output=merit_dem_avg_surf_hgt_${REGION} \
	method=average \
	--overwrite

    # Loop through JULES land cover fractions
    for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass urban water bare_soil snow_ice tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous
    do
	# Here we decide whether or not we need to process the particular
	# lc type, depending on whether the user has specified to calculate
	# five PFT, nine PFT, or both types
	declare -a FIVEPFTONLY=(tree_broadleaf tree_needleleaf shrub_evergreen shrub_deciduous)
	declare -a NINEPFTONLY=(tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous)
	
	COMPUTE_LC=1
	if [[ $NINEPFT == 1 && $FIVEPFT == 0 ]]
	then
	    # https://stackoverflow.com/a/28032613
	    INARRAY=$(echo ${FIVEPFTONLY[@]} | grep -o "$LC" | wc -w)
	    if [[ $INARRAY == 1 ]]
	    then
		COMPUTE_LC=0
	    fi
	    
	elif [[ $NINEPFT == 0 && $FIVEPFT == 1 ]]
	then
	    INARRAY=$(echo ${NINEPFTONLY[@]} | grep -o "$LC" | wc -w)
	    if [[ $INARRAY == 1 ]]
	    then
		COMPUTE_LC=0
	    fi
	fi	

	if [[ $COMPUTE_LC == 1 ]]
	then	    
	    for YEAR in "${YEARS[@]}"
	    do		
		LC_FN=${OUTDIR}/geotiff/lc_${LC}_${YEAR}_${REGION}.tif
		LC_SURF_HGT_FN=${OUTDIR}/geotiff/lc_${LC}_${YEAR}_${REGION}_surf_hgt_rel.tif
		if [[ ! -f $LC_FN || ! -f $LC_SURF_HGT_FN || $OVERWRITE == '--overwrite' ]]
		then
		    
		    # average fraction of lc
		    r.resamp.stats \
			-w \
			input=lc_${LC}_${YEAR}_globe_0.008333Deg \
			output=lc_${LC}_${YEAR}_${REGION} \
			method=average \
			$OVERWRITE

		    # sum of fraction, which equates to the sum of weights
		    # for working out the weighted average elevation (i.e.
		    # the denominator in the equation)
		    # https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
		    r.resamp.stats \
			-w \
			input=lc_${LC}_${YEAR}_globe_0.008333Deg\
			output=lc_${LC}_${YEAR}_${REGION}_sum \
			method=sum \
			$OVERWRITE

		    # sum of elevation multiplied by weights (i.e. lc fraction),
		    # which is the numerator in the weighted arithmetic mean
		    # equation
		    r.resamp.stats \
			-w \
			input=lc_${LC}_${YEAR}_globe_0.008333Deg_weighted_elev \
			output=lc_${LC}_${YEAR}_${REGION}_weighted_elev_sum \
			method=sum \
			$OVERWRITE

		    r.mapcalc \
			"lc_${LC}_${YEAR}_${REGION}_surf_hgt = lc_${LC}_${YEAR}_${REGION}_weighted_elev_sum / lc_${LC}_${YEAR}_${REGION}_sum" \
			$OVERWRITE

		    # fill in missing data in frac and surf_hgt maps
		    r.mask \
			raster=$LAND_FRAC_MAP \
			--overwrite

		    # for land cover maps, use nearest neighbour
		    r.grow.distance \
			input=lc_${LC}_${YEAR}_${REGION} \
			value=lc_${LC}_${YEAR}_${REGION}_filled \
			$OVERWRITE		    
		    
		    # fill surf hgt maps with zeros
		    r.mapcalc \
			"lc_${LC}_${YEAR}_${REGION}_surf_hgt_filled = if(isnull(lc_${LC}_${YEAR}_${REGION}_surf_hgt),0,lc_${LC}_${YEAR}_${REGION}_surf_hgt)" \
			$OVERWRITE
		    r.mapcalc \
			"lc_${LC}_${YEAR}_${REGION}_surf_hgt_rel = lc_${LC}_${YEAR}_${REGION}_surf_hgt_filled - merit_dem_avg_surf_hgt_${REGION}" \
			$OVERWRITE
		    r.mask -r
		    
		    # write output maps
		    r.out.gdal \
			input=lc_${LC}_${YEAR}_${REGION}_filled \
			output=${LC_FN} \
			createopt="COMPRESS=DEFLATE" \
			$OVERWRITE

		    r.out.gdal \
			input=lc_${LC}_${YEAR}_${REGION}_surf_hgt_rel \
			output=${LC_SURF_HGT_FN} \
			createopt="COMPRESS=DEFLATE" \
			$OVERWRITE

		    # clean up
		    g.remove -f type=raster name=lc_${LC}_${YEAR}_${REGION} 2> /dev/null
		    g.remove -f type=raster name=lc_${LC}_${YEAR}_${REGION}_filled 2> /dev/null
		    g.remove -f type=raster name=lc_${LC}_${YEAR}_${REGION}_surf_hgt 2> /dev/null	    
		    g.remove -f type=raster name=lc_${LC}_${YEAR}_${REGION}_surf_hgt_filled 2> /dev/null
		    g.remove -f type=raster name=lc_${LC}_${YEAR}_${REGION}_surf_hgt_rel 2> /dev/null
		fi		
		echo "LC_${LC^^}_${YEAR}_FN=$LC_FN" >> $TEMPFILE
		echo "LC_${LC^^}_${YEAR}_SURF_HGT_FN=$LC_SURF_HGT_FN" >> $TEMPFILE
	    done
	fi	
    done
fi
		    
# ######################################################### #
# ######################################################### #
#
# JULES_SOIL
#
# ######################################################### #
# ######################################################### #

if [[ $COSBY == 1 || $TOMASELLA == 1 || $ROSETTA == 1 ]]
then
    # Create array containing soil PTFs to be written
    declare -a METHODS=()
    if [[ $COSBY == 1 ]]
    then
	METHODS+=(cosby)
    fi
    if [[ $TOMASELLA == 1 ]]
    then
	METHODS+=(tomas)
    fi
    if [[ $ROSETTA == 1 ]]
    then		
	METHODS+=(rosetta3)
    fi	    
    for HORIZON in sl1 sl2 sl3 sl4 sl5 sl6 sl7
    do
	# b/hcap/hcon/satcon/sathh/sm_crit/sm_sat/sm_wilt
	for VARIABLE in b hcap hcon k_sat psi_m theta_crit theta_sat theta_wilt
	do
	    for METHOD in "${METHODS[@]}"
	    do
		SOIL_VAR_FN=${OUTDIR}/geotiff/"${VARIABLE}"_"${METHOD}"_"${HORIZON}"_${REGION}.tif
		if [[ ! -f $SOIL_VAR_FN || $OVERWRITE == '--overwrite' ]]
		then		    
		    g.region region=${REGION}	    
		    r.resamp.stats \
			-w \
			input="${VARIABLE}"_"${METHOD}"_"${HORIZON}" \
			output="${VARIABLE}"_"${METHOD}"_"${HORIZON}"_${REGION} \
			method=average \
			--overwrite
		    
		    # fill in missing data using nearest neighbour
		    r.mask \
			raster=$LAND_FRAC_MAP \
			--overwrite
		    r.grow.distance \
			input=${VARIABLE}_${METHOD}_${HORIZON}_${REGION} \
			value=${VARIABLE}_${METHOD}_${HORIZON}_${REGION}_filled \
			$OVERWRITE
		    r.mask -r
		    r.out.gdal \
			input="${VARIABLE}"_"${METHOD}"_"${HORIZON}"_${REGION}_filled \
			output=${SOIL_VAR_FN} \
			createopt="COMPRESS=DEFLATE" \
			--overwrite
		fi
		echo "SOIL_${VARIABLE^^}_${METHOD^^}_${HORIZON^^}_FN=$SOIL_VAR_FN" >> $TEMPFILE
		g.remove -f type=raster name="${VARIABLE}"_"${METHOD}"_"${HORIZON}"_${REGION} 2> /dev/null
	    done
	done

	for VARIABLE in ph clay
	do
	    SOIL_VAR_FN=${OUTDIR}/geotiff/"${VARIABLE}"_"${HORIZON}"_${REGION}.tif
	    if [[ ! -f $SOIL_VAR_FN || $OVERWRITE == '--overwrite' ]]
	    then		    
		g.region region=${REGION}
		r.resamp.stats \
		    -w \
		    input="${VARIABLE}"_"${HORIZON}" \
		    output="${VARIABLE}"_"${HORIZON}"_${REGION} \
		    method=average \
		    --overwrite		
		# fill in missing data using nearest neighbour
		r.mask \
		    raster=$LAND_FRAC_MAP \
		    --overwrite
		r.grow.distance \
		    input=${VARIABLE}_${HORIZON}_${REGION} \
		    value=${VARIABLE}_${HORIZON}_${REGION}_filled \
		    $OVERWRITE
		r.mask -r		
		r.out.gdal \
		    input="${VARIABLE}"_"${HORIZON}"_${REGION}_filled \
		    output=${SOIL_VAR_FN} \
		    createopt="COMPRESS=DEFLATE" \
		    --overwrite
	    fi	    
	    echo "SOIL_${VARIABLE^^}_${HORIZON^^}_FN=$SOIL_VAR_FN" >> $TEMPFILE
	    g.remove -f type=raster name="${VARIABLE}"_"${HORIZON}"_${REGION} 2> /dev/null
	done    
    done    
    
    # Soil albedo
    g.region region=${REGION}
    ALBEDO_FN=${OUTDIR}/geotiff/background_albedo_${REGION}.tif
    if [[ ! -f $ALBEDO_FN || $OVERWRITE == '--overwrite' ]]
    then	
	r.resamp.stats \
	    -w \
	    input=background_albedo \
	    output=background_albedo_${REGION} \
	    method=average \
	    --overwrite			
	# fill in missing data using nearest neighbour	
	r.mask \
	    raster=$LAND_FRAC_MAP \
	    --overwrite
	r.grow.distance \
	    input=background_albedo_${REGION} \
	    value=background_albedo_${REGION}_filled \
	    $OVERWRITE
	r.mask -r	
	r.out.gdal \
	    input=background_albedo_${REGION}_filled \
	    output=${ALBEDO_FN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
    fi    
    echo "ALBEDO_FN=$ALBEDO_FN" >> $TEMPFILE
    g.remove -f type=raster name=background_albedo_${REGION} 2> /dev/null
fi

# ######################################################### #
# ######################################################### #
#
# JULES_OVERBANK
#
# ######################################################### #
# ######################################################### #

g.region region=${REGION}

if [[ $OVERBANK == 1 ]]
then    
    LOGN_MEAN_FN=${OUTDIR}/geotiff/merit_dem_logn_mean_${REGION}.tif
    LOGN_STDEV_FN=${OUTDIR}/geotiff/merit_dem_logn_stdev_${REGION}.tif
    if [[ ! -f $LOGN_MEAN_FN || ! -f $LOGN_STDEV_FN || $OVERWRITE == '--overwrite' ]]
    then
	# weighted resample to specified region
	r.resamp.stats \
	    -w \
	    input=merit_dem_logn_mean_globe_0.008333Deg_tmp \
	    output=merit_dem_logn_mean_${REGION} \
	    method=average \
	    --overwrite
	r.resamp.stats \
	    -w \
	    input=merit_dem_logn_stdev_globe_0.008333Deg_tmp \
	    output=merit_dem_logn_stdev_${REGION} \
	    method=average \
	    --overwrite
	# fill missing data with zeros
	r.null \
	    map=merit_dem_logn_mean_${REGION} \
	    null=0
	r.null \
	    map=merit_dem_logn_stdev_${REGION} \
	    null=0
	# write output files
	r.out.gdal \
	    input=merit_dem_logn_mean_${REGION} \
	    output=${LOGN_MEAN_FN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
	r.out.gdal \
	    input=merit_dem_logn_stdev_${REGION} \
	    output=${LOGN_STDEV_FN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
    fi
    echo "LOGN_MEAN_FN=$LOGN_MEAN_FN" >> $TEMPFILE
    echo "LOGN_STDEV_FN=$LOGN_STDEV_FN" >> $TEMPFILE    
    g.remove -f type=raster name=merit_dem_logn_mean_${REGION} 2> /dev/null
    g.remove -f type=raster name=merit_dem_logn_stdev_${REGION} 2> /dev/null
    g.remove -f type=raster name=merit_dem_logn_mean_${REGION}_filled 2> /dev/null
    g.remove -f type=raster name=merit_dem_logn_stdev_${REGION}_filled 2> /dev/null
fi
