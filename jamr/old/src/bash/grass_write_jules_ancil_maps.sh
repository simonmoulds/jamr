#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain
g.region region=${REGION}

# Create file to store JULES output files
TEMPFILE=${OUTDIR}/geotiff/filenames.txt
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

SLOPE_OUTFN=${OUTDIR}/geotiff/jamr_${SLOPE_VARNM}_${REGION}.tif
FEXP_OUTFN=${OUTDIR}/geotiff/jamr_${FEXP_VARNM}_${REGION}.tif

# Compute average slope, which is needed in the PDM and TOPMODEL schemes
g.region region=${REGION}
if [[ ${PDM} == 1 ]]
then
    # Only do the computation if output files do not exist, or overwrite is set
    if [[ ! -f ${SLOPE_OUTFN} || ! -f ${FEXP_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
    then
	# Load external file, and resample to current region
	r.external \
	    -a \
	    input=${SLOPE_FN} \
	    output=${SLOPE_VARNM} \
	    --overwrite	
	r.resamp.stats \
	    -w \
	    input=${SLOPE_VARNM} \
	    output=${SLOPE_VARNM}_${REGION} \
	    method=average \
	    --overwrite
	# Set null values to zero (this should already be the case)
	r.null \
	    map=${SLOPE_VARNM}_${REGION} \
	    null=0
	# Write output
	r.out.gdal \
	    input=${SLOPE_VARNM}_${REGION} \
	    output=${SLOPE_OUTFN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
	# Write filename to temp file
	echo "SLOPE_FN=${SLOPE_OUTFN}" >> ${TEMPFILE}
    fi    
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

MERIT_TI_SIG_OUTFN=${OUTDIR}/geotiff/jamr_${MERIT_TI_SIG_VARNM}_${REGION}.tif
MERIT_TI_MEAN_OUTFN=${OUTDIR}/geotiff/jamr_${MERIT_TI_MEAN_VARNM}_${REGION}.tif
HYDRO_TI_SIG_OUTFN=${OUTDIR}/geotiff/jamr_${HYDRO_TI_SIG_VARNM}_${REGION}.tif
HYDRO_TI_MEAN_OUTFN=${OUTDIR}/geotiff/jamr_${HYDRO_TI_MEAN_VARNM}_${REGION}.tif

g.region region=${REGION}
if [[ ${TOPMODEL} == 1 ]]
then
    # compute topographic index using either MERIT or HydroSHEDS data
    if [[ ! -f ${MERIT_TI_SIG_OUTFN} || ! -f ${MERIT_TI_MEAN_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
    then
	
	# Topographic index based on geomorpho90m
	# #######################################
	r.external \
	    -a \
	    input=${MERIT_TI_MEAN_FN} \
	    output=${MERIT_TI_MEAN_VARNM} \
	    --overwrite
	
	r.resamp.stats \
	    -w \
	    input=${MERIT_TI_MEAN_VARNM} \
	    output=${MERIT_TI_MEAN_VARNM}_${REGION} \
	    method=average \
	    --overwrite
	
	r.resamp.stats \
	    -w \
	    input=${MERIT_TI_MEAN_VARNM} \
	    output=${MERIT_TI_SIG_VARNM}_${REGION} \
	    method=stddev \
	    --overwrite
	
	# ensure any null values are set to zero
	r.null \
	    map=${MERIT_TI_MEAN_VARNM}_${REGION} \
	    null=0
	r.null \
	    map=${MERIT_TI_SIG_VARNM}_${REGION} \
	    null=0	
	r.out.gdal \
	    input=${MERIT_TI_MEAN_VARNM}_${REGION} \
	    output=${MERIT_TI_MEAN_OUTFN} \
	    --overwrite
	r.out.gdal \
	    input=${MERIT_TI_SIG_VARNM}_${REGION} \
	    output=${MERIT_TI_SIG_OUTFN} \
	    --overwrite
    fi

    if [[ ! -f ${HYDRO_TI_SIG_OUTFN} || ! -f ${HYDRO_TI_MEAN_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
    then	    
	# (ii) Marthews et al 2015
	r.external \
	    -a \
	    input=${HYDRO_TI_MEAN_FN} \
	    output=${HYDRO_TI_MEAN_VARNM} \
	    --overwrite
	
	r.resamp.stats \
	    -w \
	    input=${HYDRO_TI_MEAN_VARNM} \
	    output=${HYDRO_TI_MEAN_VARNM}_${REGION} \
	    method=average \
	    --overwrite
	
	r.resamp.stats \
	    -w \
	    input=${HYDRO_TI_MEAN_VARNM} \
	    output=${HYDRO_TI_SIG_VARNM}_${REGION} \
	    method=stddev \
	    --overwrite

	# ensure any null values are set to zero
	r.null \
	    map=${HYDRO_TI_MEAN_VARNM}_${REGION} \
	    null=0
	r.null \
	    map=${HYDRO_TI_SIG_VARNM}_${REGION} \
	    null=0	
	r.out.gdal \
	    input=${HYDRO_TI_MEAN_VARNM}_${REGION} \
	    output=${HYDRO_TI_MEAN_OUTFN} \
	    --overwrite
	r.out.gdal \
	    input=${HYDRO_TI_SIG_VARNM}_${REGION} \
	    output=${HYDRO_TI_SIG_OUTFN} \
	    --overwrite
    fi
    
    # Fexp is only calculated using MERIT data
    if [[ ! -f ${FEXP_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
    then
	# decay factor describing how ksat decreases with
	# depth below the standard soil column (m-1)
	r.external \
	    -a \
	    input=${FEXP_FN} \
	    output=${FEXP_VARNM} \
	    --overwrite
	r.resamp.stats \
	    -w \
	    input=${FEXP_VARNM} \
	    output=${FEXP_VARNM}_${REGION} \
	    method=average \
	    --overwrite
	# r.mapcalc \
	#     "${FEXP_VARNM}_tmp_${REGION} = (1 + 150 * (${SLOPE_VARNM}_${REGION} / 100)) / 100" \
	#     --overwrite
	# r.mapcalc \
	#     "${FEXP_VARNM}_${REGION} = min(${FEXP_VARNM}_tmp_${REGION}, 0.4)" \
	#     --overwrite	
	# ensure any null values are set to zero
	r.null \
	    map=${FEXP_VARNM}_${REGION} \
	    null=0	
	r.out.gdal \
	    input=${FEXP_VARNM}_${REGION} \
	    output=${FEXP_OUTFN} \
	    --overwrite
    fi    
    echo "MERIT_TI_SIG_FN=$MERIT_TI_SIG_OUTFN" >> $TEMPFILE
    echo "MERIT_TI_MEAN_FN=$MERIT_TI_MEAN_OUTFN" >> $TEMPFILE
    echo "HYDRO_TI_SIG_FN=$HYDRO_TI_SIG_OUTFN" >> $TEMPFILE
    echo "HYDRO_TI_MEAN_FN=$HYDRO_TI_MEAN_OUTFN" >> $TEMPFILE    
    echo "FEXP_FN=$FEXP_OUTFN" >> $TEMPFILE
fi

# Clean up:
if [[ ${TOPMODEL} == 1 || ${PDM} == 1 ]]
then
    g.remove -f type=raster name=${SLOPE_VARNM}_${REGION} 2> /dev/null
fi

if [[ ${TOPMODEL} == 1 ]]
then
    g.remove -f type=raster name=${FEXP_VARNM}_${REGION} 2> /dev/null
    g.remove -f type=raster name=${MERIT_TI_MEAN_VARNM}_${REGION} 2> /dev/null
    g.remove -f type=raster name=${MERIT_TI_SIG_VARNM}_${REGION} 2> /dev/null
    g.remove -f type=raster name=${HYDRO_TI_MEAN_VARNM}_${REGION} 2> /dev/null
    g.remove -f type=raster name=${HYDRO_TI_SIG_VARNM}_${REGION} 2> /dev/null
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
g.region region=${REGION}
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
MERIT_DIRECTION_OUTFN=${OUTDIR}/geotiff/jamr_${MERIT_DIRECTION_VARNM}_${REGION}.tif
MERIT_AREA_OUTFN=${OUTDIR}/geotiff/jamr_${MERIT_AREA_VARNM}_${REGION}.tif
HYDRO_DIRECTION_OUTFN=${OUTDIR}/geotiff/jamr_${HYDRO_DIRECTION_VARNM}_${REGION}.tif
HYDRO_AREA_OUTFN=${OUTDIR}/geotiff/jamr_${HYDRO_AREA_VARNM}_${REGION}.tif

if [[ ${ROUTING} == 1 ]]
then    
    if [[ ${TEST1} == 0 || ${TEST2} == 0 || ${TEST3} == 0 ]]
    then
	echo
	echo "ERROR: the specified region is incompatible with the available routing maps. Exiting..."
	echo
	exit
    fi

    g.region region=${REGION}    
    if [[ ${USEMERIT} == 1 ]]
    then	
	if [[ ! -f ${MERIT_DIRECTION_OUTFN} || ! -f ${MERIT_AREA_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
	then
	    r.external \
		-a \
		input=${MERIT_DIRECTION_BASENM}_${REGION}.tif \
		output=${MERIT_DIRECTION_VARNM}_${REGION} \
		--overwrite		
	    r.out.gdal \
		input=${MERIT_DIRECTION_VARNM}_${REGION} \
		output=${MERIT_DIRECTION_OUTFN} \
		--overwrite	    
	    r.external \
		-a \
		input=${MERIT_AREA_BASENM}_${REGION}.tif \
		output=${MERIT_AREA_VARNM}_${REGION} \
		--overwrite		
	    r.out.gdal \
		input=${MERIT_AREA_VARNM}_${REGION} \
		output=${MERIT_AREA_OUTFN} \
		--overwrite
	fi
	echo "DIRECTION_FN=$MERIT_DIRECTION_OUTFN" >> $TEMPFILE
	echo "AREA_FN=$MERIT_AREA_OUTFN" >> $TEMPFILE
	g.remove -f type=raster name=${MERIT_DIRECTION_VARNM}_${REGION} 2> /dev/null	
	g.remove -f type=raster name=${MERIT_AREA_VARNM}_${REGION} 2> /dev/null
	
    else	
	if [[ ! -f ${HYDRO_DIRECTION_FN} || ! -f ${HYDRO_AREA_FN} || ${OVERWRITE} == '--overwrite' ]]
	then
	    r.external \
		-a \
		input=${HYDRO_DIRECTION_BASENM}_${REGION}.tif \
		output=${HYDRO_DIRECTION_VARNM}_${REGION} \
		--overwrite		
	    r.out.gdal \
		input=${HYDRO_DIRECTION_VARNM}_${REGION} \
		output=${HYDRO_DIRECTION_OUTFN} \
		--overwrite	    
	    r.external \
		-a \
		input=${HYDRO_AREA_BASENM}_${REGION}.tif \
		output=${HYDRO_AREA_VARNM}_${REGION} \
		--overwrite		
	    r.out.gdal \
		input=${HYDRO_AREA_VARNM}_${REGION} \
		output=${HYDRO_AREA_OUTFN} \
		--overwrite
	fi
	echo "DIRECTION_FN=$HYDRO_DIRECTION_FN" >> $TEMPFILE
	echo "AREA_FN=$HYDRO_AREA_FN" >> $TEMPFILE
	g.remove -f type=raster name=${HYDRO_DIRECTION_VARNM}_${REGION} 2> /dev/null	
	g.remove -f type=raster name=${HYDRO_AREA_VARNM}_${REGION} 2> /dev/null
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
	MERIT_LAND_FRAC_OUTFN=${OUTDIR}/geotiff/jamr_${MERIT_LAND_FRAC_VARNM}_${REGION}.tif
	if [[ ! -f ${MERIT_LAND_FRAC_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
	then	    
	    r.external \
		-a \
		input=${MERIT_LAND_FRAC_BASENM}_${REGION}.tif \
		output=${MERIT_LAND_FRAC_BASENM}_${REGION} \
		--overwrite
	    r.out.gdal \
		input=${MERIT_LAND_FRAC_BASENM}_${REGION} \
		output=${MERIT_LAND_FRAC_OUTFN} \
		format=GTiff \
		--overwrite
	fi
	LAND_FRAC_MAP=${MERIT_LAND_FRAC_BASENM}_${REGION}
	echo "JULES_LAND_FRAC_FN=${MERIT_LAND_FRAC_OUTFN}" >> $TEMPFILE
	echo "PRODUCT=MERIT" >> $TEMPFILE	
    else
	HYDRO_LAND_FRAC_OUTFN=${OUTDIR}/geotiff/jamr_${HYDRO_LAND_FRAC_VARNM}_${REGION}.tif
	if [[ ! -f ${HYDRO_LAND_FRAC_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
	then
	    r.external \
		-a \
		input=${HYDRO_LAND_FRAC_BASENM}_${REGION}.tif \
		output=${HYDRO_LAND_FRAC_BASENM}_${REGION} \
		--overwrite
	    r.out.gdal \
		input=${HYDRO_LAND_FRAC_BASENM}_${REGION} \
		output=${HYDRO_LAND_FRAC_OUTFN} \
		format=GTiff \
		type=Byte \
		createopt="COMPRESS=DEFLATE" \
		--overwrite
	fi
	LAND_FRAC_MAP=${HYDRO_LAND_FRAC_BASENM}_${REGION}
	echo "JULES_LAND_FRAC_FN=$HYDRO_LAND_FRAC_OUTFN" >> $TEMPFILE
	echo "PRODUCT=HYDRO" >> $TEMPFILE
    fi    
else
    # in this case there is no routing, so either land fraction is
    # user-supplied, or it is derived from the land fraction
    # map based on ESA CCI data
    if [[ ${FILE_LAND_FRAC} == 1 ]]
    then
	CUSTOM_LAND_FRAC_OUTFN=${OUTDIR}/geotiff/jamr_custom_land_frac_${REGION}.tif
	r.in.gdal \
	    -a \
	    input=$FILE \
	    output=land_frac_${REGION} \
	    --overwrite
	r.mapcalc \
	    "custom_land_frac_${REGION} = if(land_frac_${REGION}>0,1,0)" \
	    --overwrite
	r.out.gdal \
	    input=custom_land_frac_${REGION} \
	    output=${CUSTOM_LAND_FRAC_OUTFN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
	g.remove -f type=raster name=land_frac_${REGION} 2> /dev/null
	g.remove -f type=raster name=custom_land_frac_${REGION} 2> /dev/null
	LAND_FRAC_MAP=custom_land_frac_${REGION}
	echo "JULES_LAND_FRAC_FN=$CUSTOM_LAND_FRAC_OUTFN" >> ${TEMPFILE}
	echo "PRODUCT=CUSTOM" >> ${TEMPFILE}	
    else	
	# otherwise base region on ESA CCI LC data
	ESA_LAND_FRAC_OUTFN=${OUTDIR}/geotiff/jamr_${ESA_LAND_FRAC_VARNM}_${REGION}.tif
	if [[ ! -f ${CUSTOM_LAND_FRAC_FN} || ${OVERWRITE} == '--overwrite' ]]
	then
	    r.external \
		-a \
		input=${ESA_LAND_FRAC_FN} \
		output=${ESA_LAND_FRAC_VARNM} \
		--overwrite
	    r.resamp.stats \
		-w \
		input=${ESA_LAND_FRAC_VARNM} \
		output=${ESA_LAND_FRAC_VARNM}_tmp_${REGION} \
		method=average \
		--overwrite
	    r.mapcalc \
		"${ESA_LAND_FRAC_VARNM}_${REGION} = if(${ESA_LAND_FRAC_VARNM}_tmp_${REGION}>0,1,0)" \
		--overwrite
	    r.out.gdal \
		input=${ESA_LAND_FRAC_VARNM}_${REGION} \
		output=${ESA_LAND_FRAC_OUTFN} \
		createopt="COMPRESS=DEFLATE" \
		--overwrite	    
	    LAND_FRAC_MAP=${ESA_LAND_FRAC_VARNM}_${REGION}
	    echo "JULES_LAND_FRAC_FN=${ESA_LAND_FRAC_OUTFN}" >> $TEMPFILE
	    echo "PRODUCT=ESA" >> ${TEMPFILE}
	    g.remove -f type=raster name=${ESA_LAND_FRAC_VARNM}_tmp_${REGION} 2> /dev/null
	    # g.remove -f type=raster name=${ESA_LAND_FRAC_VARNM}_${REGION} 2> /dev/null
	fi
    fi    
fi

# ######################################################### #
# ######################################################### #
#
# JULES_FRAC
#
# ######################################################### #
# ######################################################### #

g.region region=${REGION}

declare -a YEARS=({1992..2015})
# declare -a YEARS=(2015)

if [[ ${NINEPFT} == 1 || ${FIVEPFT} == 1 ]]
then
    # in this map all non-land pixels are null
    r.external \
	-a \
	input=${SURF_HGT_FN} \
	output=${SURF_HGT_VARNM} \
	--overwrite
    
    # resample elevation map to current resolution
    r.resamp.stats \
	-w \
	input=${SURF_HGT_VARNM} \
	output=${SURF_HGT_VARNM}_${REGION} \
	method=average \
	--overwrite

    # Loop through JULES land cover fractions
    for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass urban water bare_soil snow_ice tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous
    do
	# Here we decide whether or not we need to process the particular
	# lc type, depending on whether the user has specified to calculate
	# five PFT, nine PFT, or both types
	declare -a FIVEPFTONLY=(tree_broadleaf tree_needleleaf shrub)
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
		LC_OUTFN=${OUTDIR}/geotiff/jamr_${FRAC_VARNM}_${LC}_${YEAR}_${REGION}.tif
		LC_SURF_HGT_OUTFN=${OUTDIR}/geotiff/jamr_${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}.tif
		if [[ ! -f $LC_OUTFN || ! -f $LC_SURF_HGT_OUTFN || $OVERWRITE == '--overwrite' ]]
		then
		    r.external \
			-a \
			input=${FRAC_BASENM}_${LC}_${YEAR}_globe_0.008333Deg.tif \
			output=${FRAC_VARNM}_${LC}_${YEAR} \
			--overwrite
		    r.external \
			input=${WEIGHTED_ELEV_BASENM}_${LC}_${YEAR}_globe_0.008333Deg.tif \
			output=${WEIGHTED_ELEV_VARNM}_${LC}_${YEAR} \
			--overwrite
			
		    # average fraction of lc
		    r.resamp.stats \
			-w \
			input=${FRAC_VARNM}_${LC}_${YEAR} \
			output=${FRAC_VARNM}_${LC}_${YEAR}_${REGION} \
			method=average \
			--overwrite

		    # sum of fraction, which equates to the sum of weights
		    # for working out the weighted average elevation (i.e.
		    # the denominator in the equation)
		    # https://en.wikipedia.org/wiki/Weighted_arithmetic_mean
		    r.resamp.stats \
			-w \
			input=${FRAC_VARNM}_${LC}_${YEAR} \
			output=${FRAC_VARNM}_${LC}_${YEAR}_${REGION}_sum \
			method=sum \
			--overwrite

		    # sum of elevation multiplied by weights (i.e. lc fraction),
		    # which is the numerator in the weighted arithmetic mean
		    # equation
		    r.resamp.stats \
			-w \
			input=${WEIGHTED_ELEV_VARNM}_${LC}_${YEAR} \
			output=${WEIGHTED_ELEV_VARNM}_${LC}_${YEAR}_${REGION}_sum \
			method=sum \
			--overwrite

		    r.mapcalc \
			"${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION} = ${WEIGHTED_ELEV_VARNM}_${LC}_${YEAR}_${REGION}_sum / ${FRAC_VARNM}_${LC}_${YEAR}_${REGION}_sum" \
			--overwrite

		    # fill in missing data in frac and surf_hgt maps
		    r.mask \
			raster=${LAND_FRAC_MAP} \
			--overwrite
		    # for land cover maps, use nearest neighbour
		    r.grow.distance \
			input=${FRAC_VARNM}_${LC}_${YEAR}_${REGION} \
			value=${FRAC_VARNM}_${LC}_${YEAR}_${REGION}_filled \
			--overwrite		    
		    # fill surf hgt maps with mean elevation
		    # this will result in a relative elevation map with zeros where
		    # the land cover is not present
		    r.mapcalc \
			"${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}_filled = if(isnull(${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}),${SURF_HGT_VARNM}_${REGION},${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION})" \
			--overwrite
		    # OLD: fill surf hgt maps with zeros
		    # r.mapcalc \
		    # 	"${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}_filled = if(isnull(${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}),0,${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION})" \
		    # 	--overwrite
		    r.mapcalc \
			"${SURF_HGT_VARNM}_rel_${LC}_${YEAR}_${REGION} = ${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}_filled - ${SURF_HGT_VARNM}_${REGION}" \
			--overwrite		    
		    # write output maps
		    r.out.gdal \
			input=${FRAC_VARNM}_${LC}_${YEAR}_${REGION}_filled \
			output=${LC_OUTFN} \
			createopt="COMPRESS=DEFLATE" \
			--overwrite

		    r.out.gdal \
			input=${SURF_HGT_VARNM}_rel_${LC}_${YEAR}_${REGION} \
			output=${LC_SURF_HGT_OUTFN} \
			createopt="COMPRESS=DEFLATE" \
			--overwrite
		    r.mask -r

		    # clean up
		    g.remove \
			-f \
			type=raster \
			name=${FRAC_VARNM}_${LC}_${YEAR}_${REGION} 2> /dev/null
		    g.remove \
			-f \
			type=raster \
			name=${FRAC_VARNM}_${LC}_${YEAR}_${REGION}_filled 2> /dev/null
		    g.remove \
			-f \
			type=raster \
			name=${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION} 2> /dev/null	    
		    g.remove \
			-f \
			type=raster \
			name=${SURF_HGT_VARNM}_${LC}_${YEAR}_${REGION}_filled 2> /dev/null
		    g.remove \
			-f \
			type=raster \
			name=${SURF_HGT_VARNM}_rel_${LC}_${YEAR}_${REGION} 2> /dev/null
		    
		fi		
		echo "LC_${LC^^}_${YEAR}_FN=$LC_OUTFN" >> $TEMPFILE
		echo "LC_${LC^^}_${YEAR}_SURF_HGT_FN=$LC_SURF_HGT_OUTFN" >> $TEMPFILE
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
		SOIL_VAR_OUTFN=${OUTDIR}/geotiff/jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION}.tif
		if [[ ! -f ${SOIL_VAR_OUTFN} || ${OVERWRITE} == '--overwrite' ]]
		then		    
		    g.region region=${REGION}
		    r.external \
			-a \
			input=${SOIL_BASENM}_${VARIABLE}_${METHOD}_${HORIZON}_globe_0.008333Deg.tif \
			output=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON} \
			--overwrite		    
		    r.resamp.stats \
			-w \
			input=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON} \
			output=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION} \
			method=average \
			--overwrite		    
		    # fill in missing data using nearest neighbour
		    r.mask \
			raster=$LAND_FRAC_MAP \
			--overwrite
		    r.grow.distance \
			input=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION} \
			value=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION}_filled \
			--overwrite
		    r.out.gdal \
			input=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION}_filled \
			output=${SOIL_VAR_OUTFN} \
			createopt="COMPRESS=DEFLATE" \
			--overwrite
		    r.mask -r
		fi
		echo "SOIL_${VARIABLE^^}_${METHOD^^}_${HORIZON^^}_FN=${SOIL_VAR_OUTFN}" >> ${TEMPFILE}
		# clean up
		g.remove \
		    -f \
		    type=raster \
		    name=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION}_filled 2> /dev/null
		g.remove \
		    -f \
		    type=raster \
		    name=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON}_${REGION} 2> /dev/null
		g.remove \
		    -f \
		    type=raster \
		    name=jamr_${SOIL_VARNM}_${VARIABLE}_${METHOD}_${HORIZON} 2> /dev/null
	    done
	done

	for VARIABLE in ph clay
	do
	    SOIL_VAR_OUTFN=${OUTDIR}/geotiff/jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION}.tif
	    if [[ ! -f $SOIL_VAR_FN || $OVERWRITE == '--overwrite' ]]
	    then		    
		g.region region=${REGION}
		r.external \
		    -a \
		    input=${SOIL_BASENM}_${VARIABLE}_${HORIZON}_globe_0.008333Deg.tif \
		    output=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON} \
		    --overwrite		
		r.resamp.stats \
		    -w \
		    input=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON} \
		    output=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION} \
		    method=average \
		    --overwrite		
		# fill in missing data using nearest neighbour
		r.mask \
		    raster=${LAND_FRAC_MAP} \
		    --overwrite
		r.grow.distance \
		    input=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION} \
		    value=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION}_filled \
		    --overwrite
		r.out.gdal \
		    input=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION}_filled \
		    output=${SOIL_VAR_OUTFN} \
		    createopt="COMPRESS=DEFLATE" \
		    --overwrite
		r.mask -r		
	    fi	    
	    echo "SOIL_${VARIABLE^^}_${HORIZON^^}_FN=${SOIL_VAR_OUTFN}" >> $TEMPFILE
	    # clean up
	    g.remove \
		-f \
		type=raster \
		name=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION}_filled 2> /dev/null
	    g.remove \
		-f \
		type=raster \
		name=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON}_${REGION} 2> /dev/null
	    g.remove \
		-f \
		type=raster \
		name=jamr_${SOIL_VARNM}_${VARIABLE}_${HORIZON} 2> /dev/null
	done    
    done    
    
    # Soil albedo
    g.region region=${REGION}
    ALBEDO_FN=${OUTDIR}/geotiff/jamr_${ALBSOIL_VARNM}_${REGION}.tif
    if [[ ! -f ${ALBEDO_FN} || ${OVERWRITE} == '--overwrite' ]]
    then
	r.external \
	    -a \
	    input=${ALBSOIL_FN} \
	    output=jamr_${ALBSOIL_VARNM} \
	    --overwrite
	r.resamp.stats \
	    -w \
	    input=jamr_${ALBSOIL_VARNM} \
	    output=jamr_${ALBSOIL_VARNM}_${REGION} \
	    method=average \
	    --overwrite			
	# fill in missing data using nearest neighbour	
	r.mask \
	    raster=${LAND_FRAC_MAP} \
	    --overwrite
	r.grow.distance \
	    input=jamr_${ALBSOIL_VARNM}_${REGION} \
	    value=jamr_${ALBSOIL_VARNM}_${REGION}_filled \
	    $OVERWRITE
	r.out.gdal \
	    input=jamr_${ALBSOIL_VARNM}_${REGION}_filled \
	    output=${ALBEDO_FN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
	r.mask -r	
    fi    
    echo "ALBEDO_FN=${ALBEDO_FN}" >> $TEMPFILE
    g.remove \
	-f \
	type=raster \
	name=jamr_${ALBSOIL_VARNM}_${REGION}_filled 2> /dev/null
    g.remove \
	-f \
	type=raster \
	name=jamr_${ALBSOIL_VARNM}_${REGION} 2> /dev/null
    g.remove \
	-f \
	type=raster \
	name=jamr_${ALBSOIL_VARNM} 2> /dev/null
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
    LOGN_MEAN_OUTFN=${OUTDIR}/geotiff/jamr_${LOGN_MEAN_VARNM}_${REGION}.tif
    LOGN_STDEV_OUTFN=${OUTDIR}/geotiff/jamr_${LOGN_STDEV_VARNM}_${REGION}.tif
    if [[ ! -f ${LOGN_MEAN_FN} || ! -f ${LOGN_STDEV_FN} || ${OVERWRITE} == '--overwrite' ]]
    then
	r.external \
	    -a \
	    input=${LOGN_FN} \
	    output=${LOGN_VARNM} \
	    --overwrite
	
	# weighted resample to specified region
	r.resamp.stats \
	    -w \
	    input=${LOGN_VARNM} \
	    output=${LOGN_MEAN_VARNM}_${REGION} \
	    method=average \
	    --overwrite
	
	r.resamp.stats \
	    -w \
	    input=${LOGN_VARNM} \
	    output=${LOGN_STDEV_VARNM}_${REGION} \
	    method=stddev \
	    --overwrite
	
	# fill missing data with zeros
	r.null \
	    map=${LOGN_MEAN_VARNM}_${REGION} \
	    null=0
	r.null \
	    map=${LOGN_STDEV_VARNM}_${REGION} \
	    null=0
	
	# write output files
	r.out.gdal \
	    input=${LOGN_MEAN_VARNM}_${REGION} \
	    output=${LOGN_MEAN_OUTFN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
	r.out.gdal \
	    input=${LOGN_STDEV_VARNM}_${REGION} \
	    output=${LOGN_STDEV_OUTFN} \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite
    fi
    echo "LOGN_MEAN_FN=$LOGN_MEAN_OUTFN" >> $TEMPFILE
    echo "LOGN_STDEV_FN=$LOGN_STDEV_OUTFN" >> $TEMPFILE    
    g.remove -f type=raster name=${LOGN_MEAN_VARNM}_${REGION} 2> /dev/null
    g.remove -f type=raster name=${LOGN_STDEV_VARNM}_${REGION} 2> /dev/null
fi
