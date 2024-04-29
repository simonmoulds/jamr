#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

# Remove any existing mask
r.mask -r

# Get a list of MERIT DEM files (we process these separately)
if [ -f /tmp/merit_dem_filenames.txt ]
then
    rm -f /tmp/merit_dem_filenames.txt
fi
find \
    $MERITDIR \
    -regextype posix-extended \
    -regex '.*/[n|s][0-9]+[e|w][0-9]+_dem.tif$' \
    > /tmp/merit_dem_filenames.txt

# Resample elevation to three coarser resolutions
declare -a MERIT_RGNS=(0.0083333333333333 0.0041666666666666 0.0027777777777777)
while read LN
do    
    FN=${LN##*/}
    NM=${FN%.*}
    LON=$(echo $NM | sed 's/\([s|n].*\)\([e|w].*\)_dem/\2/g')
    LAT=$(echo $NM | sed 's/\([s|n].*\)\([e|w].*\)_dem/\1/g')
    FLAG=0
    for MERIT_RGN in "${MERIT_RGNS[@]}"
    do
	MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
	OUTFILE=$AUXDIR/dem/merit_dem_avg_${LON}_${LAT}_${MERIT_RGN_STR}.tif
	if [[ ! -f $OUTFILE ]]
	then
	    FLAG=1
	fi	
    done

    if [[ $FLAG == 1 || $OVERWRITE == '--overwrite' ]]
    then	
	r.in.gdal \
	    -a \
	    input=$LN \
	    output=merit_dem \
	    --overwrite
	
	for MERIT_RGN in "${MERIT_RGNS[@]}"
	do
	    MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
	    OUTFILE=$AUXDIR/dem/merit_dem_avg_${LON}_${LAT}_${MERIT_RGN_STR}.tif
	    g.region rast=merit_dem res=${MERIT_RGN}
	    # r.resamp.stats \
	    # 	-w \
	    # 	input=merit_dem \
	    # 	output=merit_dem_avg_${LON}_${LAT}_${MERIT_RGN_STR}.tif \
	    # 	method=average \
	    # 	--overwrite
	    r.resamp.stats \
	    	-w \
	    	input=merit_dem \
	    	output=merit_dem_avg_${MERIT_RGN_STR} \
	    	method=average \
	    	--overwrite
	    r.out.gdal \
	    	input=merit_dem_avg_${MERIT_RGN_STR} \
	    	output=$AUXDIR/dem/merit_dem_avg_${LON}_${LAT}_${MERIT_RGN_STR}.tif \
	    	createopt="COMPRESS=DEFLATE" \
	    	--overwrite
	done
    fi    
done < /tmp/merit_dem_filenames.txt

# Create global MERIT DEM @ two resolutions for computing slope, tile surface height
for MERIT_RGN in "${MERIT_RGNS[@]}"
do    
    MERIT_RGN_STR=globe_$(printf "%0.6f" ${MERIT_RGN})Deg
    OUTFILE=merit_dem_${MERIT_RGN_STR}.tif
    if [[ ! -f ${AUXDIR}/dem/${OUTFILE} || ${OVERWRITE} == '--overwrite' ]]
    then	
	g.region region=${MERIT_RGN_STR}
	if [ -f /tmp/merit_dem_filenames_jules_${MERIT_RGN_STR}.txt ]
	then
	    rm -f /tmp/merit_dem_filenames_jules_${MERIT_RGN_STR}.txt
	fi
	
	find \
	    ${AUXDIR}/dem \
	    -regextype posix-extended \
	    -regex ".*/merit_dem_avg_[e|w][0-9]+_[n|s][0-9]+_${MERIT_RGN_STR}.tif$" \
	    > /tmp/merit_dem_filenames_jules_${MERIT_RGN_STR}.txt

	eval `g.region -g`
	gdalbuildvrt \
	    -overwrite \
	    -te -180 -90 180 90 \
	    -tr $MERIT_RGN $MERIT_RGN \
	    -input_file_list /tmp/merit_dem_filenames_jules_${MERIT_RGN_STR}.txt \
	    ${AUXDIR}/dem/merit_dem_${MERIT_RGN_STR}.vrt
	
	# gdal_translate ${AUXDIR}/dem/merit_dem_${MERIT_RGN_STR}.vrt ${AUXDIR}/dem/merit_dem_${MERIT_RGN_STR}.tif	
	r.in.gdal \
	    -a \
	    input=${AUXDIR}/dem/merit_dem_${MERIT_RGN_STR}.vrt \
	    output=merit_dem_${MERIT_RGN_STR}_tmp \
	    --overwrite
	# fix subtle errors in bounds
	r.mapcalc \
	    "merit_dem_${MERIT_RGN_STR} = merit_dem_${MERIT_RGN_STR}_tmp" \
	    --overwrite	
	# write a copy to aux directory
	r.out.gdal \
	    input=merit_dem_${MERIT_RGN_STR} \
	    output=${AUXDIR}/dem/$OUTFILE \
	    createopt="COMPRESS=DEFLATE,BIGTIFF=YES" \
	    --overwrite	
	g.remove -f type=raster name=merit_dem_${MERIT_RGN_STR}_tmp	
    fi    
done
