##

library(raster)

datadir = '/mnt/scratch/scratch/data/MODIS/MCD43C3'
b1 = raster(file.path(datadir, 'MODIS_006_MCD43C3_2002_01_01_Albedo_WSA_Band1.tif'))
b2 = raster(file.path(datadir, 'MODIS_006_MCD43C3_2002_01_01_Albedo_WSA_Band2.tif'))
vis = raster(file.path(datadir, 'MODIS_006_MCD43C3_2002_01_01_Albedo_WSA_vis.tif'))
nir = raster(file.path(datadir, 'MODIS_006_MCD43C3_2002_01_01_Albedo_WSA_nir.tif'))
