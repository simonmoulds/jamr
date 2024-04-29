#!/bin/bash

export GRASS_MESSAGE_FORMAT=plain

r.mask -r

# ===========================================================
# Slope and topographic index (compute at high-res)
# ===========================================================

g.region region=globe_0.004167Deg
g.region -p

# r.external -a input=${AUXDIR}/dem/merit_dem_globe_0.004167Deg.tif output=merit_dem_globe_0.004167Deg --overwrite

# Slope - calculate with r.slope.aspect
r.slope.aspect \
    elevation=merit_dem_globe_0.004167Deg \
    slope=merit_dem_slope_globe_0.004167Deg \
    format=degrees \
    $OVERWRITE

# Topographic Wetness Index : geomorpho90m
g.region region=globe_0.002083Deg
r.in.gdal \
    -a \
    input=$GEOMORPHDIR/dtm_cti_merit.dem_m_250m_s0..0cm_2018_v1.0.tif \
    output=merit_dem_topidx_0.002083Deg_tmp \
    $OVERWRITE

r.mapcalc \
    "merit_dem_topidx_globe_0.002083Deg_init = merit_dem_topidx_0.002083Deg_tmp * 0.001" \
    $OVERWRITE
g.remove -f type=raster name=merit_dem_topidx_0.002083Deg_tmp

# Topographic Wetness Index : Marthews et al 2015
g.region region=globe_0.004167Deg
r.in.gdal \
    -a \
    input=$MARTHEWDIR/data-raw/ga2.tif \
    output=hydrosheds_dem_topidx_0.004167Deg_tmp \
    $OVERWRITE

r.mapcalc \
    "hydrosheds_dem_topidx_globe_0.004167Deg = hydrosheds_dem_topidx_0.004167Deg_tmp" \
    $OVERWRITE
g.remove -f type=raster name=hydrosheds_dem_topidx_0.004167Deg_tmp

# Attempt to fill holes in MERIT product using Hydrosheds product
g.region region=globe_0.002083Deg
r.mapcalc \
    "merit_dem_topidx_globe_0.002083Deg = if(isnull(merit_dem_topidx_globe_0.002083Deg_init),hydrosheds_dem_topidx_globe_0.004167Deg,merit_dem_topidx_globe_0.002083Deg_init)" \
    $OVERWRITE

# r.mapcalc \
#     "merit_dem_topidx_globe_0.002083Deg_fill = if(isnull(merit_dem_topidx_globe_0.002083Deg_init),hydrosheds_dem_topidx_globe_0.004167Deg.tif,merit_dem_topidx_globe_0.002083Deg_init)" \
#     $OVERWRITE
# r.mapcalc \
#     "merit_dem_topidx_globe_0.002083Deg = merit_dem_topidx_globe_0.002083Deg_fill" \
#     $OVERWRITE

