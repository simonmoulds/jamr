#!/usr/bin/env python3

# r.mask -r

# # ===========================================================
# # Import tropical forest area, infill
# # ===========================================================

# unzip -o ${DATADIR}/official_teow.zip -d ${AUXDIR}
# gdal_rasterize \
#     -at -te -180 -90 180 90 \
#     -ts 43200 21600 \
#     -a BIOME \
#     ../data/aux/official/wwf_terr_ecos.shp \
#     ../data/aux/wwf_terr_ecos_0.008333Deg.tif
# g.region region=globe_0.008333Deg
# r.in.gdal \
#     -a \
#     input=${AUXDIR}/wwf_terr_ecos_0.008333Deg.tif \
#     output=wwf_terr_ecos_globe_0.008333Deg \
#     ${OVERWRITE}
# r.null map=wwf_terr_ecos_globe_0.008333Deg setnull=0
# r.grow.distance \
#     input=wwf_terr_ecos_globe_0.008333Deg \
#     value=wwf_terr_ecos_globe_0.008333Deg_interp \
#     ${OVERWRITE}
# r.mapcalc \
#     "tropical_broadleaf_forest_globe_0.008333Deg = if((wwf_terr_ecos_globe_0.008333Deg_interp == 1) | (wwf_terr_ecos_globe_0.008333Deg_interp == 2), 1, 0)" \
#     ${OVERWRITE}

# # ===========================================================
# # Read C4 fraction data
# # ===========================================================

# # Run R script to make C4 fraction:
# NATFILE=${AUXDIR}/c4_nat_veg_frac_0.008333Deg.tif
# CROPFILE=${AUXDIR}/c4_crop_frac_0.008333Deg.tif
# if [[ ! -f ${NATFILE} || ! -f ${CROPFILE} || ${OVERWRITE} == '--overwrite' ]]   
# then    
#     Rscript $SRCDIR/rscript/make_c4_fraction.R
#     g.region region=globe_0.008333Deg
    
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${AUXDIR}/c4_nat_veg_frac_0.008333Deg.tif \
# 	output=c4_nat_veg_frac_globe_0.008333Deg \
# 	--overwrite
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${AUXDIR}/c4_crop_frac_0.008333Deg.tif \
# 	output=c4_crop_frac_globe_0.008333Deg \
# 	--overwrite
# fi

# # ===========================================================
# # Make JULES land cover fraction maps
# # ===========================================================

# chmod 755 $SRCDIR/bash/make_land_cover_fraction_lookup_tables.sh
# bash $SRCDIR/bash/make_land_cover_fraction_lookup_tables.sh

# declare -a YEARS=({1992..2015})
# # declare -a YEARS=(2015)

# # get elevation for land cells
# g.region region=globe_0.002778Deg

# # setting mask will ensure values outside land mask are set to null
# # esacci_land_frac_globe_0.002778Deg computed in grass_make_jules_land_frac.sh
# # r.external -a input=${AUXDIR}/dem/merit_dem_globe_0.002778Deg.tif output=merit_dem_globe_0.002778Deg --overwrite
# r.mask raster=esacci_land_frac_globe_0.002778Deg
# r.mapcalc \
#     "merit_dem_globe_0.002778Deg_surf_hgt = merit_dem_globe_0.002778Deg" \
#     --overwrite

# # land sea mask @ 0.002778Deg
# r.mapcalc \
#     "land_sea_mask = esacci_land_frac_globe_0.002778Deg" \
#     --overwrite
# r.mask -r

# # resample land elevation map to 1km maps, disregarding non-land cells
# g.region region=globe_0.008333Deg
# r.resamp.stats \
#     -w \
#     input=merit_dem_globe_0.002778Deg_surf_hgt \
#     output=merit_dem_globe_0.008333Deg_surf_hgt \
#     method=average \
#     --overwrite

# # Loop through years and create land cover fractions/surface heights
# for YEAR in "${YEARS[@]}"
# do
#     g.region region=globe_0.002778Deg
    
#     # r.external \
#     r.in.gdal \
# 	-a \
# 	input=${ESACCIDIR}/ESACCI-LC-L4-LCCS-Map-300m-P1Y-${YEAR}-v2.0.7.tif \
# 	output=esacci_lc_${YEAR}_w_sea \
# 	$OVERWRITE

#     # Mask sea values in esacci_lc_${YEAR}_w_sea by multiplying by
#     # land_sea_mask, in which non-land cells are null. 
#     r.mapcalc \
#     	"esacci_lc_${YEAR} = esacci_lc_${YEAR}_w_sea * land_sea_mask" \
#     	$OVERWRITE
	    
#     # tree broadleaf evergreen
#     # ########################
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_broadleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_broadleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.05 * esacci_lc_${YEAR}_40) + (0.90 * esacci_lc_${YEAR}_50) + (0.10 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.01 * esacci_lc_${YEAR}_150) + (0.30 * esacci_lc_${YEAR}_160) + (0.60 * esacci_lc_${YEAR}_170)" \
#     # 	$OVERWRITE
    
#     # tree broadleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_deciduous_x1000 \
# 	rules=$AUXDIR/tree_broadleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_broadleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_broadleaf_deciduous = (0.05 * esacci_lc_${YEAR}_30) + (0.05 * esacci_lc_${YEAR}_40) + (0.70 * esacci_lc_${YEAR}_60) + (0.70 * esacci_lc_${YEAR}_61) + (0.30 * esacci_lc_${YEAR}_62) + (0.30 * esacci_lc_${YEAR}_90) + (0.20 * esacci_lc_${YEAR}_100) + (0.10 * esacci_lc_${YEAR}_110) + (0.03 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_151) + (0.30 * esacci_lc_${YEAR}_160) + (0.05 * esacci_lc_${YEAR}_180) + (0.025 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # tree needleleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_evergreen_x1000 \
# 	rules=$AUXDIR/tree_needleleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_needleleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_needleleaf_evergreen = (0.70 * esacci_lc_${YEAR}_70) + (0.70 * esacci_lc_${YEAR}_71) + (0.30 * esacci_lc_${YEAR}_72) + (0.20 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.01 * esacci_lc_${YEAR}_150) + (0.06 * esacci_lc_${YEAR}_151) + (0.10 * esacci_lc_${YEAR}_180) + (0.025 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # tree needleleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_deciduous_x1000 \
# 	rules=$AUXDIR/tree_needleleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_tree_needleleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_tree_needleleaf_deciduous = (0.70 * esacci_lc_${YEAR}_80) + (0.70 * esacci_lc_${YEAR}_81) + (0.30 * esacci_lc_${YEAR}_82) + (0.10 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.02 * esacci_lc_${YEAR}_151)" \
#     # 	$OVERWRITE

#     # shrub broadleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_x1000 \
# 	rules=$AUXDIR/shrub_broadleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_broadleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.075 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_50) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.30 * esacci_lc_${YEAR}_121) + (0.01 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_152) + (0.20 * esacci_lc_${YEAR}_170)" \
#     # 	$OVERWRITE

#     # shrub broadleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_x1000 \
# 	rules=$AUXDIR/shrub_broadleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_broadleaf_deciduous = (0.50 * esacci_lc_${YEAR}_12) + (0.05 * esacci_lc_${YEAR}_30) + (0.10 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_50) + (0.15 * esacci_lc_${YEAR}_60) + (0.15 * esacci_lc_${YEAR}_61) + (0.25 * esacci_lc_${YEAR}_62) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_72) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_82) + (0.05 * esacci_lc_${YEAR}_90) + (0.10 * esacci_lc_${YEAR}_100) + (0.10 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.60 * esacci_lc_${YEAR}_122) + (0.03 * esacci_lc_${YEAR}_150) + (0.06 * esacci_lc_${YEAR}_152) + (0.10 * esacci_lc_${YEAR}_180)" \
#     # 	$OVERWRITE

#     # shrub needleleaf evergreen
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_x1000 \
# 	rules=$AUXDIR/shrub_needleleaf_evergreen_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_needleleaf_evergreen = (0.05 * esacci_lc_${YEAR}_30) + (0.075 * esacci_lc_${YEAR}_40) + (0.05 * esacci_lc_${YEAR}_70) + (0.05 * esacci_lc_${YEAR}_71) + (0.05 * esacci_lc_${YEAR}_72) + (0.05 * esacci_lc_${YEAR}_80) + (0.05 * esacci_lc_${YEAR}_81) + (0.05 * esacci_lc_${YEAR}_82) + (0.05 * esacci_lc_${YEAR}_90) + (0.05 * esacci_lc_${YEAR}_100) + (0.05 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.30 * esacci_lc_${YEAR}_121) + (0.01 * esacci_lc_${YEAR}_150) + (0.02 * esacci_lc_${YEAR}_152) + (0.05 * esacci_lc_${YEAR}_180)" \
#     # 	$OVERWRITE

#     # shrub neefleleaf deciduous
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_x1000 \
# 	rules=$AUXDIR/shrub_needleleaf_deciduous_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_x1000 \
# 	output=esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_shrub_needleleaf_deciduous = 0" \
#     # 	$OVERWRITE

#     # natural grass
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_natural_grass_x1000 \
# 	rules=$AUXDIR/natural_grass_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_natural_grass_x1000 \
# 	output=esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg = esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_natural_grass = (0.15 * esacci_lc_${YEAR}_30) + (0.25 * esacci_lc_${YEAR}_40) + (0.15 * esacci_lc_${YEAR}_60) + (0.15 * esacci_lc_${YEAR}_61) + (0.35 * esacci_lc_${YEAR}_62) + (0.15 * esacci_lc_${YEAR}_70) + (0.15 * esacci_lc_${YEAR}_71) + (0.30 * esacci_lc_${YEAR}_72) + (0.15 * esacci_lc_${YEAR}_80) + (0.15 * esacci_lc_${YEAR}_81) + (0.30 * esacci_lc_${YEAR}_82) + (0.15 * esacci_lc_${YEAR}_90) + (0.40 * esacci_lc_${YEAR}_100) + (0.60 * esacci_lc_${YEAR}_110) + (0.20 * esacci_lc_${YEAR}_120) + (0.20 * esacci_lc_${YEAR}_121) + (0.20 * esacci_lc_${YEAR}_122) + (0.60 * esacci_lc_${YEAR}_130) + (0.60 * esacci_lc_${YEAR}_140) + (0.05 * esacci_lc_${YEAR}_150) + (0.05 * esacci_lc_${YEAR}_151) + (0.05 * esacci_lc_${YEAR}_152) + (0.15 * esacci_lc_${YEAR}_153) + (0.20 * esacci_lc_${YEAR}_160) + (0.40 * esacci_lc_${YEAR}_180) + (0.15 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # managed grass
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_managed_grass_x1000 \
# 	rules=$AUXDIR/managed_grass_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_managed_grass_x1000 \
# 	output=esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg = esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_managed_grass = (1 * esacci_lc_${YEAR}_10) + (1 * esacci_lc_${YEAR}_11) + (0.50 * esacci_lc_${YEAR}_12) + (1 * esacci_lc_${YEAR}_20) + (0.60 * esacci_lc_${YEAR}_30) + (0.40 * esacci_lc_${YEAR}_40)" \
#     # 	$OVERWRITE

#     # urban
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_urban_x1000 \
# 	rules=$AUXDIR/urban_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_urban_x1000 \
# 	output=esacci_lc_${YEAR}_urban_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_urban_globe_0.008333Deg = esacci_lc_${YEAR}_urban_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_urban = (0.75 * esacci_lc_${YEAR}_190)" \
#     # 	$OVERWRITE

#     # bare soil
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_bare_soil_x1000 \
# 	rules=$AUXDIR/bare_soil_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_bare_soil_x1000 \
# 	output=esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg = esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_bare_soil = (0.10 * esacci_lc_${YEAR}_62) + (0.30 * esacci_lc_${YEAR}_72) + (0.30 * esacci_lc_${YEAR}_82) + (0.10 * esacci_lc_${YEAR}_90) + (0.20 * esacci_lc_${YEAR}_120) + (0.20 * esacci_lc_${YEAR}_121) + (0.20 * esacci_lc_${YEAR}_122) + (0.40 * esacci_lc_${YEAR}_130) + (0.40 * esacci_lc_${YEAR}_140) + (0.85 * esacci_lc_${YEAR}_150) + (0.85 * esacci_lc_${YEAR}_151) + (0.85 * esacci_lc_${YEAR}_152) + (0.85 * esacci_lc_${YEAR}_153) + (1 * esacci_lc_${YEAR}_200) + (1 * esacci_lc_${YEAR}_201) + (1 * esacci_lc_${YEAR}_202)" \
#     # 	$OVERWRITE

#     # water
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_water_x1000 \
# 	rules=$AUXDIR/water_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_water_x1000 \
# 	output=esacci_lc_${YEAR}_water_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_water_globe_0.008333Deg = esacci_lc_${YEAR}_water_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_water = (0.20 * esacci_lc_${YEAR}_160) + (0.20 * esacci_lc_${YEAR}_170) + (0.30 * esacci_lc_${YEAR}_180) + (0.05 * esacci_lc_${YEAR}_190) + (1 * esacci_lc_${YEAR}_210)" \
#     # 	$OVERWRITE

#     # snow/ice
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_snow_ice_x1000 \
# 	rules=$AUXDIR/snow_ice_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_snow_ice_x1000 \
# 	output=esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg = esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_snow_ice = (1 * esacci_lc_${YEAR}_220)" \
#     # 	$OVERWRITE

#     # no data
#     g.region raster=esacci_lc_${YEAR}
#     r.reclass \
# 	input=esacci_lc_${YEAR} \
# 	output=esacci_lc_${YEAR}_nodata_x1000 \
# 	rules=$AUXDIR/nodata_reclass.txt \
# 	$OVERWRITE
#     g.region region=globe_0.008333Deg
#     r.resamp.stats \
# 	input=esacci_lc_${YEAR}_nodata_x1000 \
# 	output=esacci_lc_${YEAR}_nodata_globe_0.008333Deg_x1000 \
# 	method=average \
# 	$OVERWRITE
#     r.mapcalc \
# 	"esacci_lc_${YEAR}_nodata_globe_0.008333Deg = esacci_lc_${YEAR}_nodata_globe_0.008333Deg_x1000 / 1000" \
# 	$OVERWRITE
#     # r.mapcalc \
#     # 	"esacci_lc_${YEAR}_nodata = (1 * esacci_lc_${YEAR}_0)" \
#     # 	$OVERWRITE
    
#     # ===================================================== #
#     # Convert to JULES land cover types
#     # ===================================================== #
#     g.region region=globe_0.008333Deg

#     # (i) 5 PFT    
#     r.mapcalc \
# 	"lc_tree_broadleaf_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_c4_grass_${YEAR}_globe_0.008333Deg = (esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg * c4_nat_veg_frac_globe_0.008333Deg) + (esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg * c4_crop_frac_globe_0.008333Deg)" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_c3_grass_${YEAR}_globe_0.008333Deg = (esacci_lc_${YEAR}_natural_grass_globe_0.008333Deg * (1-c4_nat_veg_frac_globe_0.008333Deg)) + (esacci_lc_${YEAR}_managed_grass_globe_0.008333Deg * (1-c4_crop_frac_globe_0.008333Deg))" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_urban_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_urban_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_water_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_water_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_bare_soil_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_bare_soil_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_snow_ice_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_snow_ice_globe_0.008333Deg" \
# 	$OVERWRITE

#     # weighted elevation
#     for LC in tree_broadleaf tree_needleleaf shrub c4_grass c3_grass urban water bare_soil snow_ice
#     do
# 	r.mapcalc \
# 	    "lc_${LC}_${YEAR}_globe_0.008333Deg_weighted_elev = lc_${LC}_${YEAR}_globe_0.008333Deg * merit_dem_globe_0.008333Deg_surf_hgt" \
# 	    $OVERWRITE
#     done

#     # (ii) 9 PFT
#     r.mapcalc \
# 	"lc_tree_broadleaf_evergreen_tropical_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg * tropical_broadleaf_forest_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_broadleaf_evergreen_temperate_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_evergreen_globe_0.008333Deg * (1-tropical_broadleaf_forest_globe_0.008333Deg)" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_broadleaf_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_broadleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_evergreen_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_evergreen_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_tree_needleleaf_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_tree_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_evergreen_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_evergreen_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_evergreen_globe_0.008333Deg" \
# 	$OVERWRITE

#     r.mapcalc \
# 	"lc_shrub_deciduous_${YEAR}_globe_0.008333Deg = esacci_lc_${YEAR}_shrub_broadleaf_deciduous_globe_0.008333Deg + esacci_lc_${YEAR}_shrub_needleleaf_deciduous_globe_0.008333Deg" \
# 	$OVERWRITE

#     # weighted elevation
#     for LC in tree_broadleaf_evergreen_tropical tree_broadleaf_evergreen_temperate tree_broadleaf_deciduous tree_needleleaf_evergreen tree_needleleaf_deciduous shrub_evergreen shrub_deciduous
#     do
# 	r.mapcalc \
# 	    "lc_${LC}_${YEAR}_globe_0.008333Deg_weighted_elev = lc_${LC}_${YEAR}_globe_0.008333Deg * merit_dem_globe_0.008333Deg_surf_hgt" \
# 	    $OVERWRITE
#     done
    
# done
