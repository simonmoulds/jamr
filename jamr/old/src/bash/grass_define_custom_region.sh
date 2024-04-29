#!/bin/bash

if [[ -f $FILE && $FILE != '' ]]
then
    # Import file
    r.in.gdal \
	-a \
	input=$FILE \
	output=${REGION}_template \
	--overwrite

    # Set region using template file
    g.region \
	raster=${REGION}_template \
	save=${REGION} \
	--overwrite    
else
    # Otherwise, set the region using the supplied cli arguments
    g.region \
	n=$YMAX s=$YMIN e=$XMAX w=$XMIN \
	nsres=$YRES \
	ewres=$XRES \
	save=${REGION} \
	--overwrite
fi

g.region -p
