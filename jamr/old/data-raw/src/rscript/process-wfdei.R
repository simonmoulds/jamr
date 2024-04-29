## Author : Simon Moulds
## Date   : Dec 2020

library(raster)
library(tidyverse)
library(magrittr)

r=raster("/mnt/scratch/scratch/data/WFDEI/WFDEI-elevation.nc") %>% setNames("layer")

df = as.data.frame(r, xy=TRUE)

## do not include Antarctica
df$layer[df$y <= -60] = NA
df$layer[!is.na(df$layer)] = 1
df$layer[is.na(df$layer)] = 0

r[] = df$layer

writeRaster(r, "../data/aux/mask/WFDEI_land_frac_globe_0.500000Deg.tif", overwrite=TRUE)
