## Author : Simon Moulds
## Date   : Oct 2019

library(raster)
library(magrittr)

## To divide vegetation classes between C3/C4 types, we follow the method
## outlined in Zhang et al (2016):
## https://www.nature.com/articles/sdata2017165#data-records

## ####################################################### ##
## 1. C4 fraction: natural vegetation
## ####################################################### ##

unzip_cmd = paste(
    "unzip",
    "-o",
    "../data/ISLSCP_C4_1DEG_932.zip",
    "-d ../data/aux"
)

system(unzip_cmd)

gdal_translate_cmd = paste(
    "gdal_translate",
    "-a_srs EPSG:4326",
    "../data/aux/ISLSCP_C4_1DEG_932/data/c4_percent_1d.asc",
    "../data/aux/c4_percent_1d.tif"
)
system(gdal_translate_cmd)

r = raster("../data/aux/c4_percent_1d.tif")
r[r==-999] = NA
r[is.na(r)] = 0
r = r / 100

## write raster to file, so that we can then use gdal command line
## tools to disaggregate to other resolutions
writeRaster(
    r,
    "../data/aux/c4_percent_1d_corrected.tif",
    overwrite=TRUE
)

rgns = c(0.5, 0.25, 0.125, 0.1, 1/12, 0.0625, 0.05, 1/60, 0.01, 1/120)
rgns_str = formatC(rgns, digits=6, format="f", flag=0)

for (i in 1:length(rgns)) {
    gdalwarp_cmd = paste(
        "gdalwarp",
        "-overwrite",
        "-te -180 -90 180 90",
        paste0("-tr ", rgns[i], " ", rgns[i]),
        "-r near",
        "../data/aux/c4_percent_1d_corrected.tif",
        paste0("../data/aux/c4_nat_veg_frac_", rgns_str[i], "Deg.tif")
    )
    system(gdalwarp_cmd)
}

## ####################################################### ##
## 2. C4 fraction: cropland
## ####################################################### ##

## use crop types from MapSPAM (2005)
unzip_cmd = paste(
    "unzip",
    "-o",
    "../data/MapSPAM/spam2005V3r1_global_harv_area.geotiff.zip",
    "-d ../data/aux/mapspam_data"
)
system(unzip_cmd)

fs = list.files(
    "../data/aux/mapspam_data",
    pattern="^SPAM2005V3r1_global_H_T(A|H|I|L|R|S)_[A-Z]+_(A|H|I|L|R|S).tif$",
    full.names=TRUE
)

total_cropland_area = raster(fs[1])
total_cropland_area[] = 0
for (i in 1:length(fs)) {
    r = raster(fs[i])
    r[is.na(r)] = 0
    total_cropland_area = total_cropland_area + r
}
total_cropland_area[total_cropland_area == 0] = NA

## C4 crops: sugarcane, maize, millet (small, pearl), sorghum
c4_fs = list.files(
    "../data/aux/mapspam_data",
    pattern="^SPAM2005V3r1_global_H_T(A|H|I|L|R|S)_(SUGC|MAIZ|SMIL|PMIL|SORG)_(A|H|I|L|R|S).tif$",
    full.names=TRUE
)
total_c4_cropland_area = raster(c4_fs[1])
total_c4_cropland_area[] = 0
for (i in 1:length(c4_fs)) {
    r = raster(c4_fs[i])
    r[is.na(r)] = 0
    total_c4_cropland_area = total_c4_cropland_area + r
}

## extend to full geographic area
## frac_5arc = raster("../data/aux/hydro/flwdir_05min.tif")
ext = extent(-180, 180, -90, 90)
total_cropland_area = extend(total_cropland_area, ext)#ent(frac_5arc))
total_c4_cropland_area = extend(total_c4_cropland_area, ext)#ent(frac_5arc))

## make initial map at 5 arcminute resolution, because this
## is the native resolution of MapSPAM. Then, use gdalwarp
## to disaggregate
c4_crop_5arc = total_c4_cropland_area / total_cropland_area
c4_crop_5arc[is.na(c4_crop_5arc)] = 0

## writing to geotiff results in precision errors which causes the
## subsequent GDAL commands to throw an 'Invalid dfNorthLatitudeDeg'
## error. Writing to ascii, then translating to geotiff with GDAL
## while specifying output bounds seems to remove the error.
writeRaster(
    c4_crop_5arc,
    "../data/aux/c4_crop_frac_0.083333Deg_init.asc",
    overwrite=TRUE
)

system("gdalwarp -overwrite -te -180 -90 180 90 -t_srs EPSG:4326 ../data/aux/c4_crop_frac_0.083333Deg_init.asc ../data/aux/c4_crop_frac_0.083333Deg.tif")

for (i in 1:length(rgns)) {
    gdalwarp_cmd = paste(
        "gdalwarp",
        "-overwrite",
        "-te -180. -90. 180. 90.",
        paste0("-tr ", rgns[i], " ", rgns[i]),
        "-r near",
        "../data/aux/c4_crop_frac_0.083333Deg.tif",
        paste0("../data/aux/c4_crop_frac_", rgns_str[i], "Deg.tif")
    )
    if (!isTRUE(all.equal(rgns[i], 1/12))) {
        system(gdalwarp_cmd)
    }    
}
