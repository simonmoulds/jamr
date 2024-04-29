#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

# remove any existing mask
r.mask -r

# MERIT
if [ -f /tmp/dem_filenames.txt ]
then
    rm -f /tmp/dem_filenames.txt
fi

if [[ ! -f $AUXDIR/dem/merit_dem_global.vrt || $OVERWRITE == '--overwrite' ]]
then
    > /tmp/dem_filenames.txt
    for FN in $MERITDIR/*.tif
    do
	echo $FN >> /tmp/dem_filenames.txt
    done
    gdalbuildvrt \
	-overwrite \
	-te -180 -90 180 90 \
	-tr 0.0008333333333 0.0008333333333 \
	-input_file_list /tmp/dem_filenames.txt \
	$AUXDIR/dem/merit_dem_global.vrt
fi

# g1wbm
if [ -f /tmp/g1wbm_filenames.txt ]
then
    rm -f /tmp/g1wbm_filenames.txt
fi

if [[ ! -f $AUXDIR/dem/g1wbm_global.vrt || $OVERWRITE == '--overwrite' ]]
then
    > /tmp/g1wbm_filenames.txt
    for DIR in $GWBMDIR/wat_*/
    do
	for FN in $DIR/*.tif
	do
	    echo $FN >> /tmp/g1wbm_filenames.txt
	done
    done    
    gdalbuildvrt \
	-overwrite \
	-te -180 -90 180 90 \
	-tr 0.0002777777777 0.0002777777777 \
	-input_file_list /tmp/g1wbm_filenames.txt \
	$AUXDIR/dem/g1wbm_global.vrt
fi

# OSM
if [ -f /tmp/osm_filenames.txt ]
then
    rm -f /tmp/osm_filenames.txt
fi

if [[ ! -f $AUXDIR/dem/osm_global.vrt || $OVERWRITE == '--overwrite' ]]
then
    > /tmp/osm_filenames.txt
    for FN in $OSMDIR/*.tif
    do
	echo $FN >> /tmp/osm_filenames.txt
    done    
    gdalbuildvrt \
	-overwrite \
	-te -180 -90 180 90 \
	-tr 0.0008333333333 0.0008333333333 \
	-input_file_list /tmp/osm_filenames.txt \
	$AUXDIR/dem/osm_global.vrt
fi

# ===========================================================
# Create reclassification rules file for g1wbm and OSM
# ===========================================================

# g1wbm
if [ -f /tmp/g1wbm_rcl_rules.txt ]
then
    rm -f /tmp/g1wbm_rcl_rules.txt
fi

echo "50 51 = 100
*           = 0" > /tmp/g1wbm_rcl_rules.txt

# OSM
# 2 = large lake/river;
# 3 = major river;
# 5 = small stream
if [ -f /tmp/osm_rcl_rules.txt ]
then
    rm -f /tmp/osm_rcl_rules.txt
fi

echo "2 = 25
3       = 20
5       = 5
*       = 0" > /tmp/osm_rcl_rules.txt

# ===========================================================
# Loop through each GSWO file, make water likelihood surface
# ===========================================================

# GSWO (the main program loops through these map tiles)
if [ -f /tmp/gswo_filenames.txt ]
then
    rm /tmp/gswo_filenames.txt    
fi

> /tmp/gswo_filenames.txt
for FN in $GSWODIR/occurrence/*.tif
do
    echo $FN >> /tmp/gswo_filenames.txt    
done

while read LN
do    
    # get GSWO filename, extract lat/lon information
    FN=${LN##*/}
    NM=${FN%.*}
    LON=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)/\2/g')
    LAT=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)/\3/g')

    # Names of output files
    DEMFILE=$AUXDIR/dem/merit_dem_con_${LON}_${LAT}_0.0008333Deg.tif
    SWLFILE=$AUXDIR/dem/synthetic_water_layer_${LON}_${LAT}_0.0008333Deg.tif

    # Only process if the files don't already exist in the file system
    if [[ ! -f  $DEMFILE || ! -f $SWLFILE || $OVERWRITE == '--overwrite' ]]
    then
	
	# read GSWO @ 0.00025 degree resolution
	r.in.gdal \
	    -a \
	    input=$LN \
	    output=gswo \
	    --overwrite

	# set region to match extent, set resolution, resample
	g.region rast=gswo res=0:00:01
	g.region -p

	# native GSWO resolution is 0.00025, hence do weighted resample
	r.null map=gswo setnull=255
	r.resamp.stats \
	    -w \
	    input=gswo \
	    output=gswo_1arcsec \
	    method=average \
	    --overwrite
	r.null map=gswo_1arcsec null=0

	# crop input maps using GDAL command line tools    
	if [ -f /tmp/clipper.shp ]
	then
	    rm -f /tmp/clipper.dbf /tmp/clipper.prj /tmp/clipper.shp /tmp/clipper.shx
	fi    
	gdaltindex /tmp/clipper.shp $LN

	gdalwarp \
	    -overwrite \
	    -cutline /tmp/clipper.shp \
	    -crop_to_cutline \
	    -wo "CUTLINE_ALL_TOUCHED=TRUE" \
	    $AUXDIR/dem/merit_dem_global.vrt \
	    $AUXDIR/dem/merit_dem_"${LON}"_"${LAT}"_0.0008333Deg.tif

	# remove existing temporary file
	if [ -f /tmp/g1wbm_tmp.tif ]
	then
	    rm /tmp/g1wbm_tmp.tif
	fi    
	gdalwarp \
	    -overwrite \
	    -cutline /tmp/clipper.shp \
	    -crop_to_cutline \
	    -wo "CUTLINE_ALL_TOUCHED=TRUE" \
	    $AUXDIR/dem/g1wbm_global.vrt \
	    /tmp/g1wbm_tmp.tif

	if [ -f /tmp/osm_tmp.tif ]
	then
	    rm /tmp/osm_tmp.tif
	fi    
	gdalwarp \
	    -overwrite \
	    -cutline /tmp/clipper.shp \
	    -crop_to_cutline \
	    -wo "CUTLINE_ALL_TOUCHED=TRUE" \
	    $AUXDIR/dem/osm_global.vrt \
	    /tmp/osm_tmp.tif

	# read MERIT DEM
	r.in.gdal \
	    -a \
	    input=$AUXDIR/dem/merit_dem_"${LON}"_"${LAT}"_0.0008333Deg.tif \
	    output=merit_dem \
	    --overwrite

	# read g1wbm, reclass
	r.in.gdal \
	    -a \
	    input=/tmp/g1wbm_tmp.tif \
	    output=g1wbm \
	    --overwrite

	r.reclass \
	    input=g1wbm \
	    output=g1wbm_prob \
	    rules=/tmp/g1wbm_rcl_rules.txt \
	    --overwrite

	# read osm, reclass
	r.in.gdal \
	    -a \
	    input=/tmp/osm_tmp.tif \
	    output=osm \
	    --overwrite

	r.reclass \
	    input=osm \
	    output=osm_prob \
	    rules=/tmp/osm_rcl_rules.txt \
	    --overwrite

	# compute synthetic water layer and "conditioned" dem
	r.mapcalc \
	    "water_prob = max(round(gswo_1arcsec*0.7), g1wbm_prob, osm_prob)" \
	    --overwrite
	# set any null values to zero (i.e. probability of water = 0)
	r.null map=water_prob null=0

	# change region back to native MERIT DEM resolution (3 arcsecond)
	g.region rast=gswo res=0:00:03
	g.region -p

	# aggregate water likelihood surface to 3 arcsec, taking
	# maximum value
	r.resamp.stats \
	    input=water_prob \
	    output=water_prob_3arcsec \
	    method=maximum \
	    --overwrite

	# compute conditioned DEM
	r.mapcalc \
	    "merit_dem_con = merit_dem - (3. + 0.17 * water_prob_3arcsec)" \
	    --overwrite

	# write water prob as byte, because it should have range 0-100
	r.out.gdal \
	    -f \
	    input=water_prob_3arcsec \
	    type=Byte \
	    output=$AUXDIR/dem/synthetic_water_layer_${LON}_${LAT}_0.0008333Deg.tif \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite

	r.out.gdal \
	    input=merit_dem_con \
	    output=$AUXDIR/dem/merit_dem_con_${LON}_${LAT}_0.0008333Deg.tif \
	    createopt="COMPRESS=DEFLATE" \
	    --overwrite		
    fi    
done < /tmp/gswo_filenames.txt





# OLD:

# #!/bin/bash

# export GRASS_MESSAGE_FORMAT=plain

# # remove any existing mask
# r.mask -r
# r.external.out -r

# # ===========================================================
# # Make output data directories
# # ===========================================================

# if [ ! -d $AUXDIR/dem ]
# then
#     mkdir $AUXDIR/dem
# fi

# # ===========================================================
# # Build VRTs
# # ===========================================================

# # MERIT
# if [ -f /tmp/dem_filenames.txt ]
# then
#     rm -f /tmp/dem_filenames.txt
# fi

# if [[ ! -f $AUXDIR/dem/merit_dem_global.vrt || $OVERWRITE == '--overwrite' ]]
# then
#     > /tmp/dem_filenames.txt
#     for FN in $MERITDIR/*.tif
#     do
# 	echo $FN >> /tmp/dem_filenames.txt
#     done
#     gdalbuildvrt \
# 	-overwrite \
# 	-te -180 -90 180 90 \
# 	-tr 0.0008333333333 0.0008333333333 \
# 	-input_file_list /tmp/dem_filenames.txt \
# 	$AUXDIR/dem/merit_dem_global.vrt
# fi

# # g1wbm
# if [ -f /tmp/g1wbm_filenames.txt ]
# then
#     rm -f /tmp/g1wbm_filenames.txt
# fi

# if [[ ! -f $AUXDIR/dem/g1wbm_global.vrt || $OVERWRITE == '--overwrite' ]]
# then
#     > /tmp/g1wbm_filenames.txt
#     for DIR in $GWBMDIR/wat_*/
#     do
# 	for FN in $DIR/*.tif
# 	do
# 	    echo $FN >> /tmp/g1wbm_filenames.txt
# 	done
#     done    
#     gdalbuildvrt \
# 	-overwrite \
# 	-te -180 -90 180 90 \
# 	-tr 0.0002777777777 0.0002777777777 \
# 	-input_file_list /tmp/g1wbm_filenames.txt \
# 	$AUXDIR/dem/g1wbm_global.vrt
# fi

# # OSM
# if [ -f /tmp/osm_filenames.txt ]
# then
#     rm -f /tmp/osm_filenames.txt
# fi

# if [[ ! -f $AUXDIR/dem/osm_global.vrt || $OVERWRITE == '--overwrite' ]]
# then
#     > /tmp/osm_filenames.txt
#     for FN in $OSMDIR/*.tif
#     do
# 	echo $FN >> /tmp/osm_filenames.txt
#     done    
#     gdalbuildvrt \
# 	-overwrite \
# 	-te -180 -90 180 90 \
# 	-tr 0.0008333333333 0.0008333333333 \
# 	-input_file_list /tmp/osm_filenames.txt \
# 	$AUXDIR/dem/osm_global.vrt
# fi

# # ===========================================================
# # Create reclassification rules file for g1wbm and OSM
# # ===========================================================

# # g1wbm
# if [ -f /tmp/g1wbm_rcl_rules.txt ]
# then
#     rm -f /tmp/g1wbm_rcl_rules.txt
# fi

# echo "50 51 = 100
# *           = 0" > /tmp/g1wbm_rcl_rules.txt

# # OSM
# # 2 = large lake/river;
# # 3 = major river;
# # 5 = small stream
# if [ -f /tmp/osm_rcl_rules.txt ]
# then
#     rm -f /tmp/osm_rcl_rules.txt
# fi

# echo "2 = 25
# 3       = 20
# 5       = 5
# *       = 0" > /tmp/osm_rcl_rules.txt

# # ===========================================================
# # Loop through each GSWO file, make water likelihood surface
# # ===========================================================

# # GSWO (the main program loops through these map tiles)
# if [ -f /tmp/gswo_filenames.txt ]
# then
#     rm /tmp/gswo_filenames.txt    
# fi

# > /tmp/gswo_filenames.txt
# for FN in $GSWODIR/occurrence/*.tif
# do
#     echo $FN >> /tmp/gswo_filenames.txt    
# done

# while read LN
# do    
#     # get GSWO filename, extract lat/lon information
#     FN=${LN##*/}    
#     NM=${FN%.*}    
#     LON=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)/\2/g')    
#     LAT=$(echo $NM | sed 's/\(.*\)_\(.*\)_\(.*\)/\3/g')    
    
#     # ##################################################### #    
#     # Read GSWO @ 0.00025 degree resolution, resample to 1 arcsec
#     # ##################################################### #    
#     r.external -a input=${LN} output=gswo_${LON}_${LAT}_native --overwrite

#     # set region to match extent, set resolution, resample
#     g.region rast=gswo_"${LON}"_"${LAT}"_native res=0:00:01
#     g.region -p

#     # native GSWO resolution is 0.00025, hence do weighted resample

#     # first, we need to set 255 equal to null, keeping all other
#     # values the same. Quickest way to do this is using r.reclass
#     echo "255 = NULL
#     *         = *" > gswo_rcl_rules.txt
#     r.reclass \
# 	input=gswo_"${LON}"_"${LAT}"_native \
# 	output=gswo_"${LON}"_"${LAT}"_native_rcl \
# 	rules=gswo_rcl_rules.txt \
# 	--overwrite
    
#     # perform [weighted] resample
#     r.resamp.stats \
# 	-w \
# 	input=gswo_${LON}_${LAT}_native_rcl \
# 	output=gswo_${LON}_${LAT}_0.000277Deg_tmp \
# 	method=average \
# 	--overwrite
    
#     # return null values to zero
#     r.mapcalc \
# 	"gswo_${LON}_${LAT}_0.000277Deg.tif = if(isnull(gswo_${LON}_${LAT}_0.000277Deg_tmp.tif), 0, gswo_${LON}_${LAT}_0.000277Deg_tmp.tif)" \
# 	--overwrite

#     # ##################################################### #
#     # Crop MERIT DEM map based on GSWO region
#     # ##################################################### #
#     if [ -f /tmp/clipper.shp ]
#     then
# 	rm -f /tmp/clipper.dbf /tmp/clipper.prj /tmp/clipper.shp /tmp/clipper.shx
#     fi    
#     gdaltindex /tmp/clipper.shp $LN

#     # Remove if file exists already (belt and braces)
#     if [ -f $AUXDIR/dem/merit_dem_"${LON}"_"${LAT}"_0.000833Deg.tif ]
#     then
# 	rm -f $AUXDIR/dem/merit_dem_"${LON}"_"${LAT}"_0.000833Deg.tif
#     fi	
#     gdalwarp \
# 	-overwrite \
# 	-cutline /tmp/clipper.shp \
# 	-crop_to_cutline \
# 	-wo "CUTLINE_ALL_TOUCHED=TRUE" \
# 	$AUXDIR/dem/merit_dem_global.vrt \
# 	$AUXDIR/dem/merit_dem_"${LON}"_"${LAT}"_0.000833Deg.tif

#     # ##################################################### #
#     # Crop G1WBM map based on GSWO region
#     # ##################################################### #
#     if [ -f $AUXDIR/dem/g1wbm_"${LON}"_"${LAT}"_0.000277Deg.tif ]
#     then	
#        rm -f $AUXDIR/dem/g1wbm_"${LON}"_"${LAT}"_0.000277Deg.tif
#     fi       
#     gdalwarp \
# 	-overwrite \
# 	-cutline /tmp/clipper.shp \
# 	-crop_to_cutline \
# 	-wo "CUTLINE_ALL_TOUCHED=TRUE" \
# 	$AUXDIR/dem/g1wbm_global.vrt \
# 	$AUXDIR/dem/g1wbm_"${LON}"_"${LAT}"_0.000277Deg.tif

#     # ##################################################### #
#     # Crop OSM map based on GSWO region
#     # ##################################################### #
#     if [ -f $AUXDIR/dem/osm_"${LON}"_"${LAT}"_0.000833Deg.tif ]
#     then
#     	rm -f $AUXDIR/dem/osm_"${LON}"_"${LAT}"_0.000833Deg.tif
#     fi    
#     gdalwarp \
# 	-overwrite \
# 	-cutline /tmp/clipper.shp \
# 	-crop_to_cutline \
# 	-wo "CUTLINE_ALL_TOUCHED=TRUE" \
# 	$AUXDIR/dem/osm_global.vrt \
#         $AUXDIR/dem/osm_"${LON}"_"${LAT}"_0.000833Deg.tif

#     # ##################################################### #
#     # Compute water probability surface
#     # ##################################################### #
    
#     # read g1wbm, reclass
#     r.external -a input=${AUXDIR}/dem/g1wbm_${LON}_${LAT}_0.000277Deg.tif output=g1wbm_${LON}_${LAT}_0.000277Deg --overwrite
#     r.reclass \
# 	input=g1wbm_"${LON}"_"${LAT}"_0.000277Deg \
# 	output=g1wbm_prob_"${LON}"_"${LAT}"_0.000277Deg \
# 	rules=/tmp/g1wbm_rcl_rules.txt \
# 	--overwrite

#     # read osm, reclass
#     r.external -a input=${AUXDIR}/dem/osm_${LON}_${LAT}_0.000833Deg.tif output=osm_${LON}_${LAT}_0.000833Deg --overwrite
#     r.reclass \
# 	input=osm_"${LON}"_"${LAT}"_0.000833Deg \
# 	output=osm_prob_"${LON}"_"${LAT}"_0.000833Deg \
# 	rules=/tmp/osm_rcl_rules.txt \
# 	--overwrite

#     # NB this map should contain no null cells
#     r.mapcalc \
# 	"water_prob_${LON}_${LAT}_0.000277Deg.tif = max(round(gswo_${LON}_${LAT}_0.000277Deg.tif * 0.7), g1wbm_prob_${LON}_${LAT}_0.000277Deg, osm_prob_${LON}_${LAT}_0.000833Deg)" \
# 	--overwrite    

#     # ##################################################### #
#     # Compute conditioned DEM
#     # ##################################################### #    

#     # change region back to native MERIT DEM resolution (3 arcsecond)
#     g.region rast=gswo_"${LON}"_"${LAT}"_native res=0:00:03
#     g.region -p

#     # aggregate water likelihood surface to 3 arcsec, taking
#     # maximum value
#     r.resamp.stats \
# 	input=water_prob_${LON}_${LAT}_0.000277Deg.tif \
# 	output=water_prob_${LON}_${LAT}_0.000833Deg.tif \
# 	method=maximum \
# 	--overwrite
    
#     r.external -a input=$AUXDIR/dem/merit_dem_${LON}_${LAT}_0.000833Deg.tif output=merit_dem_${LON}_${LAT}_0.000833Deg --overwrite

#     # compute conditioned dem
#     r.mapcalc \
# 	"merit_dem_con_${LON}_${LAT}_0.0008333Deg.tif = merit_dem_${LON}_${LAT}_0.000833Deg - (3. + 0.17 * water_prob_${LON}_${LAT}_0.000833Deg.tif)" \
# 	--overwrite

#     # clean up
#     g.remove -f type=raster name=gswo_${LON}_${LAT}_0.000277Deg.tif,gswo_${LON}_${LAT}_0.000277Deg_tmp.tif,water_prob_${LON}_${LAT}_0.000277Deg.tif
#     rm -f $AUXDIR/dem/gswo_${LON}_${LAT}_0.000277Deg.tif
#     rm -f $AUXDIR/dem/gswo_${LON}_${LAT}_0.000277Deg_tmp.tif
#     rm -f $AUXDIR/dem/water_prob_${LON}_${LAT}_0.000277Deg.tif
# done < /tmp/gswo_filenames.txt

# r.external.out -r
