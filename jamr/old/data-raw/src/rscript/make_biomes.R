## Author : Simon Moulds
## Date   : Oct 2019

library(rgdal)
library(raster)
library(magrittr)
library(splancs)

## ==========================================================
## Interpolation function
## ==========================================================

fill_missing_with_nn = function(map, pts) {
    ## get values at points
    vals = map[pts]
    ## pixels with missing data have a value of NA
    missing_pts = pts[is.na(vals)]
    present_pts = pts[!is.na(vals)]
    ## use splancs to get nearest neighbours
    require(splancs)
    present_pts_spl =
        present_pts %>%
        as.data.frame %>%
        as.matrix %>%
        as.points
    missing_pts_spl =
        missing_pts %>%
        as.data.frame %>%
        as.matrix %>%
        as.points
    nn = n2dist(
        present_pts_spl,
        missing_pts_spl
    )
    ## convert splancs output to SpatialPoints
    nn_index =
        present_pts_spl[nn$neighs,] %>%
        SpatialPoints(
            proj4string=CRS(
                "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"
            )
        )
    ## assign missing values
    map[missing_pts] = map[nn_index]
    map
}

## ==========================================================
## Extract data and rasterize
## ==========================================================

print(getwd())
system("unzip -o ../data/official_teow.zip -d ../data/aux")

# 0.5 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 720 360 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.500000Deg.tif")

# 0.25 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 1440 720 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.250000Deg.tif")

# 0.125 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 2880 1440 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.125000Deg.tif")

# 0.1 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 3600 1800 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.100000Deg.tif")

# 0.083333 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 4320 2160 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.083333Deg.tif")

# 0.0625 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 5760 2880 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.062500Deg.tif")

# 0.05 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 7200 3600 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.050000Deg.tif")

# 0.016666 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 21600 10800 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.016667Deg.tif")

# 0.01 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 36000 18000 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.010000Deg.tif")

# 0.008333 degrees
system("gdal_rasterize -at -te -180 -90 180 90 -ts 43200 21600 -a BIOME ../data/aux/official/wwf_terr_ecos.shp ../data/aux/wwf_terr_ecos_0.008333Deg.tif")

## ## ==========================================================
## ## prepare land points to identify missing data
## ## ==========================================================

## ## rgns = c(0.5, 0.25, 0.125, 0.1, 1/12, 0.0625, 0.05)#, 1/60, 0.01, 1/120)
## rgns = c(0.25, 0.1, 1/12, 0.05)
## rgns_str = formatC(rgns, digits=6, format="f", flag=0)

## for (i in 1:length(rgns)) {

##     out_fn = file.path(
##         "../data/aux",
##         paste0("tropical_broadleaf_forest_", rgns_str[i], "Deg.tif")
##     )

##     land_frac = raster(
##         file.path(
##             "../data/aux/mask",
##             paste0("esacci_land_frac_globe_", rgns_str[i], "Deg.tif")
##         )
##     )    
##     biomes = raster(
##         file.path(
##             "../data/aux",
##             paste0("wwf_terr_ecos_", rgns_str[i], "Deg.tif")
##         )
##     )        
##     land_frac[land_frac == 0] = NA
##     land_frac_pts = as(land_frac, "SpatialPoints")    
##     biomes[biomes == 0] = NA
##     ## print("filling missing data...")
##     ## biomes = fill_missing_with_nn(biomes, land_frac_pts)
##     ## if (rgns[i] == 0.05) {
##     ##     biomes_0.05 = biomes
##     ## }        
##     tropical_broadleaf_forest = ((biomes == 1) | (biomes == 2))
##     writeRaster(
##         biomes,
##         file.path(
##             "../data/aux",
##             paste0("biomes_", rgns_str[i], "Deg.tif")
##         )
##     )
##     ## writeRaster(
##     ##     tropical_broadleaf_forest,
##     ##     file.path(
##     ##         "../data/aux",
##     ##         paste0("tropical_broadleaf_forest_", rgns_str[i], "Deg.tif")
##     ##     )
##     ## )
## }
