## Author : Simon Moulds
## Date   : Feb 2021

library(raster)
library(tidyverse)
library(magrittr)

datadir = "../../data/maps1k"

## ####################################################### ##
## JULES_LAND_FRAC
## ####################################################### ##

## TODO

## ####################################################### ##
## JULES_FRAC
## ####################################################### ##

## 5PFT
blt = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_broadleaf_2015_globe_0.008333Deg.tif"
    )
)

nlt = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_needleleaf_2015_globe_0.008333Deg.tif"
    )
)

c3g = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_c3_grass_2015_globe_0.008333Deg.tif"
    )
)

c4g = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_c4_grass_2015_globe_0.008333Deg.tif"
    )
)

shr = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_shrub_2015_globe_0.008333Deg.tif"
    )
)

bsl = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_bare_soil_2015_globe_0.008333Deg.tif"
    )
)

ice = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_snow_ice_2015_globe_0.008333Deg.tif"
    )
)

urb = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_urban_2015_globe_0.008333Deg.tif"
    )
)

wat = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_water_2015_globe_0.008333Deg.tif"
    )
)

## 9PFT
shr_dcd = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_shrub_deciduous_2015_globe_0.008333Deg.tif"
    )
)

shr_evr = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_shrub_evergreen_2015_globe_0.008333Deg.tif"
    )
)

blt_dcd = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_broadleaf_deciduous_2015_globe_0.008333Deg.tif"
    )
)

blt_evr_temp = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_broadleaf_evergreen_temperate_2015_globe_0.008333Deg.tif"
    )
)
    
blt_evr_trop = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_broadleaf_evergreen_tropical_2015_globe_0.008333Deg.tif"
    )
)

nlt_dcd = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_needleleaf_deciduous_2015_globe_0.008333Deg.tif"
    )
)

nlt_evr = raster(
    file.path(
        datadir,
        "jules_frac",
        "jamr_esa_cci_lc_frac_tree_needleleaf_evergreen_2015_globe_0.008333Deg.tif"
    )
)

## Check sum to one - OK
tot_5pft = stackApply(
    stack(blt, nlt, c3g, c4g, shr, bsl, ice, urb, wat),
    indices=rep(1, 9),
    fun=sum,
    na.rm=TRUE
)

## Check sum to one - OK
tot_9pft = stackApply(
    stack(blt_dcd, blt_evr_trop, blt_evr_temp, nlt_dcd, nlt_evr, c3g, c4g, shr_dcd, shr_evr, bsl, ice, urb, wat),
    indices=rep(1, 13),
    fun=sum,
    na.rm=TRUE
)

## ####################################################### ##
## JULES_RIVERS_PROPS
## ####################################################### ##

## TODO

## ####################################################### ##
## JULES_OVERBANK_PROPS
## ####################################################### ##

## TODO

## ####################################################### ##
## JULES_SOIL_PROPS
## ####################################################### ##

soil_vars = c(
    "b", "hcap", "hcon", "k_sat", "psi_m",
    "theta_crit", "theta_sat", "theta_wilt"
)
cosby_maps = list()
rosetta3_maps = list()
tomas_maps = list()

for (i in 1:length(soil_vars)) {
    var = soil_vars[i]
    cosby_maps[[var]] = raster(
        file.path(
            datadir,
            "jules_soil_props",
            paste0("jamr_soilgrids_", var, "_cosby_sl1_globe_0.008333Deg.tif")
        )
    )
    rosetta3_maps[[var]] = raster(
        file.path(
            datadir,
            "jules_soil_props",
            paste0("jamr_soilgrids_", var, "_rosetta3_sl1_globe_0.008333Deg.tif")
        )
    )
    tomas_maps[[var]] = raster(
        file.path(
            datadir,
            "jules_soil_props",
            paste0("jamr_soilgrids_", var, "_tomas_sl1_globe_0.008333Deg.tif")
        )
    )
}

## Checks

## Compare against 0.5 degree data from ANTS

get_nc_map = function(nc, var, ext) {
    map = raster(nrow=360, ncol=720)
    ncmap = raster(nc, var=var)
    map[] = getValues(ncmap)
    map = map %>% raster::crop(ext)
    map[map==-999] = NA
    map
}

load_nc_maps = function(nc, ext) {
    maps = list()
    maps[["b"]] = get_nc_map(nc, "field1381", ext)
    maps[["hcap"]] = get_nc_map(nc, "field335", ext)
    maps[["hcon"]] = get_nc_map(nc, "field336", ext)
    maps[["k_sat"]] = get_nc_map(nc, "field333", ext)
    maps[["psi_m"]] = get_nc_map(nc, "field342", ext)
    maps[["theta_crit"]] = get_nc_map(nc, "field330", ext)
    maps[["theta_sat"]] = get_nc_map(nc, "field332", ext)
    maps[["theta_wilt"]] = get_nc_map(nc, "field329", ext)
    maps
}

cosby_nc = "../../data/qrparm.soil_HWSD_cont_cosby2d.nc"
vg_nc = "../../data/qrparm.soil_HWSD_class3_van_genuchten2d.nc"
ext = extent(cosby_maps[[1]])
ants_cosby_maps = load_nc_maps(cosby_nc, ext)
ants_vg_maps = load_nc_maps(vg_nc, ext)

get_summary = function(x) {
    df = as.data.frame(matrix(data=NA, nrow=length(x), ncol=3))
    names(df) = c("min","max","mean")
    row.names(df) = names(x)
    for (i in 1:length(x)) {
        df$min[i] = cellStats(x[[i]], min) %>% round(digits=3)
        df$max[i] = cellStats(x[[i]], max) %>% round(digits=3)
        df$mean[i] = cellStats(x[[i]], mean) %>% round(digits=3)
    }
    df
}

## Compare Cosby maps
## OK
ants_cosby_summary = get_summary(ants_cosby_maps)
cosby_summary = get_summary(cosby_maps)

## Compare Rosetta3 maps (van Genuchten)
## OK, but sathh (psi_m) seems high compared to current JULES maps
ants_vg_summary = get_summary(ants_vg_maps)
rosetta3_summary = get_summary(rosetta3_maps)

## Compare Tomasella & Hodnett maps (van Genuchten)
## The values are the correct order of magnitude and
## probably OK, but we need to check against the data
## obtained by Toby Marthews for South America
ants_vg_summary = get_summary(tomas_maps)
tomas_summary = get_summary(tomas_maps)

## Check 2: theta_sat >= theta_crit >= theta_wilt
get_values = function(maps, key) {
    v = getValues(maps[[key]]) %>% `[`(!is.na(.))
    v
}

tomas_theta_sat = get_values(tomas_maps, "theta_sat")
tomas_theta_crit = get_values(tomas_maps, "theta_crit")
tomas_theta_wilt = get_values(tomas_maps, "theta_wilt")

all(tomas_theta_sat > tomas_theta_crit) # 1 grid point fails
tomas_theta_sat[!tomas_theta_sat >= tomas_theta_crit]
tomas_theta_crit[!tomas_theta_sat >= tomas_theta_crit]

cosby_theta_sat = get_values(cosby_maps, "theta_sat")
cosby_theta_crit = get_values(cosby_maps, "theta_crit")
cosby_theta_wilt = get_values(cosby_maps, "theta_wilt")

all(cosby_theta_sat > cosby_theta_crit) # OK

rosetta3_theta_sat = get_values(rosetta3_maps, "theta_sat")
rosetta3_theta_crit = get_values(rosetta3_maps, "theta_crit")
rosetta3_theta_wilt = get_values(rosetta3_maps, "theta_wilt")

all(rosetta3_theta_sat > rosetta3_theta_crit) # OK

## ####################################################### ##
## JULES_PDM
## ####################################################### ##

slope = raster(
    file.path(
        datadir,
        "jules_pdm",
        "jamr_merit_dem_slope_globe_0.008333Deg.tif"
    )
)

## Check order of magnitude - OK
cellStats(slope, max)
cellStats(slope, min)

## ####################################################### ##
## JULES_TOP
## ####################################################### ##

## ## TODO - check method against that used in ANTS

## fexp = raster(
##     file.path(
##         datadir,
##         "jules_top",        
##         "jamr_merit_dem_fexp_globe_0.008333Deg.tif"
##     )
## )

## cellStats(fexp, max)
## cellStats(fexp, min)
## cellStats(fexp, mean)

## ti_mean = raster(
##     file.path(
##         datadir,
##         "jules_top",        
##         "jamr_merit_dem_ti_mean_globe_0.002083Deg.tif"
##     )
## )

## cellStats(ti_mean, max)
## cellStats(ti_mean, min)
