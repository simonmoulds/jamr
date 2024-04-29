#!/bin/bash

OUTDIR=$WD/data/jules_overbank_props

r.mask -r
    
find \
    ${AUXDIR}/dem \
    -regextype posix-extended \
    -regex '.*/merit_dem_con_[0-9]+[E|W]_[0-9]+[N|S]_0.0008333Deg.tif$' \
    > $TMPDIR/merit_dem_filenames.txt

# Create tiled maps at 1km, then join them together
while read LN
do
    FN=${LN##*/}
    NM=${FN%.*}
    LON=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)_\(.*\)_\(.*\)/\3/g')
    LAT=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)_\(.*\)_\(.*\)/\4/g')

    RGN=0.008333333333333
    RGN_STR=globe_$(printf "%0.6f" ${RGN})Deg
    OUTFILE1=${AUXDIR}/dem/merit_dem_logn_mean_${LON}_${LAT}_${RGN_STR}.tif
    OUTFILE2=${AUXDIR}/dem/merit_dem_logn_stdev_${LON}_${LAT}_${RGN_STR}.tif

    if [[ ! -f $OUTFILE1 || ! -f $OUTFILE2 || $OVERWRITE == '--overwrite' ]]
    then
	
	r.in.gdal \
	    -a \
	    input="${LN}" \
	    output=merit_dem_con \
	    --overwrite

	# To compute overbank parameters we keep the elevation values
	# for sea as null (this is how merit_dem_con_*.tif are configured
	# anyway) - FIXME - check this!!!
	g.region raster=merit_dem_con res=${RGN}
	g.region -p

	# N.B. removed '-w' flags because the coarse resolution
	# is a multiple of the native resolution
	r.resamp.stats \
	    -w \
	    input=merit_dem_con \
	    output=merit_dem_con_min_${RGN_STR} \
	    method=minimum \
	    --overwrite

	r.resamp.stats \
	    -w \
	    input=merit_dem_con \
	    output=merit_dem_con_mean_${RGN_STR} \
	    method=average \
	    --overwrite
	
	r.out.gdal \
	    input=merit_dem_con_min_${RGN_STR} \
	    output=${AUXDIR}/dem/merit_dem_con_min_${LON}_${LAT}_${RGN_STR}.tif \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite	

	r.out.gdal \
	    input=merit_dem_con_mean_${RGN_STR} \
	    output=${AUXDIR}/dem/merit_dem_con_mean_${LON}_${LAT}_${RGN_STR}.tif \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite	
    fi

done < $TMPDIR/merit_dem_filenames.txt

