## Author : Simon Moulds
## Date   : Oct 2019

library(dplyr)
library(magrittr)
library(rgdal)
library(raster)

wfdei_lines = readLines("/mnt/scratch/scratch/data/WFDEI/WFDEI-land-long-lat-height.txt") %>% `[`(8:length(.))
wfdei_pts = as.data.frame(matrix(data=NA, nrow=length(wfdei_lines), ncol=5))
                          
for (i in 1:length(wfdei_lines)) {
    ln = wfdei_lines[i]
    ln = ln %>%
        trimws %>%
        strsplit("\\s+") %>%
        `[[`(1) %>%
        `[`(1:5) %>%
        as.numeric
    wfdei_pts[i,] = ln
}

coords = wfdei_pts[,1:2] %>% setNames(c("x","y"))
coords = coords[coords$y >= -55.75,]
pts = SpatialPoints(
    coords=coords,
    proj4string=CRS("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")
)
r = raster(nrows=360, ncols=720, xmn=-180, xmx=180, ymn=-90, ymx=90)
r[pts] = 1

writeRaster(
    r,
    "../data/jules_land_frac/WFDEI-land-long-lat-height.tif",
    format="GTiff",
    overwrite=TRUE
)
