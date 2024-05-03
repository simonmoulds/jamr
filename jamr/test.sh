#!/usr/bin/env sh


# BOUNDS="-337500.000 1242500.000 152500.000 527500.000" # Example bounding box (homolosine) for Ghana
# CELL_SIZE="250 250"

# IGH="+proj=igh +lat_0=0 +lon_0=0 +datum=WGS84 +units=m +no_defs" # proj string for Homolosine projection
SG_URL="/vsicurl?max_retry=3&retry_delay=1&list_dir=no&url=https://files.isric.org/soilgrids/latest/data"

# gdal_translate -projwin $BOUNDS -projwin_srs "$IGH" -tr $CELL_SIZE \
#     -co "TILED=YES" -co "COMPRESS=DEFLATE" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
#     $SG_URL"/ocs/ocs_0-30cm_mean.vrt" \
#     "ocs_0-5cm_mean.tif"
gdal_translate \
    -co "TILED=YES" -co "COMPRESS=DEFLATE" -co "PREDICTOR=2" -co "BIGTIFF=YES" \
    $SG_URL"/ocs/ocs_0-30cm_mean.vrt" \
    "ocs_0-5cm_mean.tif"
