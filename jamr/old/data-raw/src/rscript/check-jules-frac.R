## Author : Simon Moulds
## Date   : March 2020

library(raster)
library(magrittr)

check_cells_valid = function(x, rgn) {
    all(!is.na(x[rgn]))
}

## jules_land_frac
land_frac_0.250000 = raster("../data/jules_land_frac/jules_land_frac_0.250000Deg.tif")
land_frac_0.100000 = raster("../data/jules_land_frac/jules_land_frac_0.100000Deg.tif")
land_frac_0.083333 = raster("../data/jules_land_frac/jules_land_frac_0.083333Deg.tif")
land_frac_0.050000 = raster("../data/jules_land_frac/jules_land_frac_0.050000Deg.tif")
land_frac_0.016666 = raster("../data/jules_land_frac/jules_land_frac_0.016666Deg.tif")

## jules_frac
frac_0.250000 = stack(list.files("../data/jules_frac", pattern="^lc_.*_2015_0.250000Deg.tif$", full.names=TRUE))
frac_0.100000 = stack(list.files("../data/jules_frac", pattern="^lc_.*_2015_0.100000Deg.tif$", full.names=TRUE))
frac_0.083333 = stack(list.files("../data/jules_frac", pattern="^lc_.*_2015_0.083333Deg.tif$", full.names=TRUE))
frac_0.050000 = stack(list.files("../data/jules_frac", pattern="^lc_.*_2015_0.050000Deg.tif$", full.names=TRUE))
frac_0.016666 = stack(list.files("../data/jules_frac", pattern="^lc_.*_2015_0.016666Deg.tif$", full.names=TRUE))

## jules_frac (crop)
library(ncdf4)
nc = nc_open("../apps/India_0.250000Deg/jules_frac_5pft_crop_2015_merit_india_0.250000Deg.nc")
cfrac = ncvar_get(nc, "frac")
nc_close(nc)

nc = nc_open("../apps/India_0.250000Deg/jules_frac_5pft_2015_merit_india_0.250000Deg.nc")
frac = ncvar_get(nc, "frac")
nc_close(nc)

cfrac_tot = apply(cfrac, 1:2, sum)
frac_tot = apply(cfrac, 1:2, sum)

check_cells_valid(frac_0.250000[[1]], land_frac_0.250000)
check_cells_valid(frac_0.100000[[1]], land_frac_0.100000)
check_cells_valid(frac_0.083333[[1]], land_frac_0.083333)
check_cells_valid(frac_0.050000[[1]], land_frac_0.050000)
## check_cells_valid(frac_0.016666[[1]], land_frac_0.016666)

## (0-1)
summary(frac_0.250000[[1]])
summary(frac_0.100000[[1]])
summary(frac_0.083333[[1]])
summary(frac_0.050000[[1]])
## summary(frac_0.016666[[1]])

## jules_overbank_props

## The conditioned MERIT DEM does not contain values north of 80N
## In addition, cells containing 100% water have a value of NA, because
## the computation takes the log of zero.

logn_mean_0.250000 = raster("../data/jules_overbank_props/merit_dem_logn_mean_0.250000Deg.tif")
logn_mean_0.100000 = raster("../data/jules_overbank_props/merit_dem_logn_mean_0.100000Deg.tif")
logn_mean_0.083333 = raster("../data/jules_overbank_props/merit_dem_logn_mean_0.083333Deg.tif")
logn_mean_0.050000 = raster("../data/jules_overbank_props/merit_dem_logn_mean_0.050000Deg.tif")
logn_mean_0.016666 = raster("../data/jules_overbank_props/merit_dem_logn_mean_0.016666Deg.tif")

check_cells_valid(logn_mean_0.250000, land_frac_0.250000)
check_cells_valid(logn_mean_0.100000, land_frac_0.100000)
check_cells_valid(logn_mean_0.083333, land_frac_0.083333)
check_cells_valid(logn_mean_0.050000, land_frac_0.050000)
## check_cells_valid(logn_mean_0.016666[[1]], land_frac_0.016666)

## x_vals = getValues(logn_mean_0.250000)
## rgn_vals = getValues(land_frac_0.250000)
## pts = as(land_frac_0.250000, "SpatialPoints")
## plot(land_frac_0.250000)
## points(pts[(rgn_vals>0) & (is.na(x_vals))])
## na_pts = pts[(rgn_vals>0) & (is.na(x_vals))] %>% as.data.frame
## min(na_pts$y)
## frac_0.250000[[16]][SpatialPoints(coords=na_pts[na_pts$y<80,])]

## (0-1)
summary(logn_mean_0.250000[[1]])
summary(logn_mean_0.100000[[1]])
summary(logn_mean_0.083333[[1]])
summary(logn_mean_0.050000[[1]])
## summary(logn_mean_0.016666[[1]])

logn_stddev_0.250000 = raster("../data/jules_overbank_props/merit_dem_logn_stddev_0.250000Deg.tif")
logn_stddev_0.100000 = raster("../data/jules_overbank_props/merit_dem_logn_stddev_0.100000Deg.tif")
logn_stddev_0.083333 = raster("../data/jules_overbank_props/merit_dem_logn_stddev_0.083333Deg.tif")
logn_stddev_0.050000 = raster("../data/jules_overbank_props/merit_dem_logn_stddev_0.050000Deg.tif")
logn_stddev_0.016666 = raster("../data/jules_overbank_props/merit_dem_logn_stddev_0.016666Deg.tif")

check_cells_valid(logn_stddev_0.250000, land_frac_0.250000)
check_cells_valid(logn_stddev_0.100000, land_frac_0.100000)
check_cells_valid(logn_stddev_0.083333, land_frac_0.083333)
check_cells_valid(logn_stddev_0.050000, land_frac_0.050000)
## check_cells_valid(logn_stddev_0.016666[[1]], land_frac_0.016666)

## (0-1)
summary(logn_stddev_0.250000)
summary(logn_stddev_0.100000)
summary(logn_stddev_0.083333)
summary(logn_stddev_0.050000)
## summary(logn_stddev_0.016666)

## jules_pdm
slope_0.250000 = raster("../data/jules_pdm/merit_dem_slope_0.250000Deg.tif")
slope_0.100000 = raster("../data/jules_pdm/merit_dem_slope_0.100000Deg.tif")
slope_0.083333 = raster("../data/jules_pdm/merit_dem_slope_0.083333Deg.tif")
slope_0.050000 = raster("../data/jules_pdm/merit_dem_slope_0.050000Deg.tif")
slope_0.016666 = raster("../data/jules_pdm/merit_dem_slope_0.016666Deg.tif")

check_cells_valid(slope_0.250000, land_frac_0.250000)
check_cells_valid(slope_0.100000, land_frac_0.100000)
check_cells_valid(slope_0.083333, land_frac_0.083333)
check_cells_valid(slope_0.050000, land_frac_0.050000)
## check_cells_valid(slope_0.016666[[1]], land_frac_0.016666)

summary(slope_0.250000)
summary(slope_0.100000)
summary(slope_0.083333)
summary(slope_0.050000)
## summary(slope_0.016666)

## jules_top
fexp_0.250000 = raster("../data/jules_top/merit_dem_fexp_0.250000Deg.tif")
fexp_0.100000 = raster("../data/jules_top/merit_dem_fexp_0.100000Deg.tif")
fexp_0.083333 = raster("../data/jules_top/merit_dem_fexp_0.083333Deg.tif")
fexp_0.050000 = raster("../data/jules_top/merit_dem_fexp_0.050000Deg.tif")
fexp_0.016666 = raster("../data/jules_top/merit_dem_fexp_0.016666Deg.tif")

check_cells_valid(fexp_0.250000, land_frac_0.250000)
check_cells_valid(fexp_0.100000, land_frac_0.100000)
check_cells_valid(fexp_0.083333, land_frac_0.083333)
check_cells_valid(fexp_0.050000, land_frac_0.050000)
## check_cells_valid(fexp_0.016666[[1]], land_frac_0.016666)

summary(fexp_0.250000)
summary(fexp_0.100000)
summary(fexp_0.083333)
summary(fexp_0.050000)
## summary(fexp_0.016666)

topidx_mean_0.250000 = raster("../data/jules_top/merit_dem_topidx_mean_0.250000Deg.tif")
topidx_mean_0.100000 = raster("../data/jules_top/merit_dem_topidx_mean_0.100000Deg.tif")
topidx_mean_0.083333 = raster("../data/jules_top/merit_dem_topidx_mean_0.083333Deg.tif")
topidx_mean_0.050000 = raster("../data/jules_top/merit_dem_topidx_mean_0.050000Deg.tif")
topidx_mean_0.016666 = raster("../data/jules_top/merit_dem_topidx_mean_0.016666Deg.tif")

check_cells_valid(topidx_mean_0.250000, land_frac_0.250000)
check_cells_valid(topidx_mean_0.100000, land_frac_0.100000)
check_cells_valid(topidx_mean_0.083333, land_frac_0.083333)
check_cells_valid(topidx_mean_0.050000, land_frac_0.050000)
## check_cells_valid(topidx_mean_0.016666[[1]], land_frac_0.016666)

## x_vals = getValues(topidx_mean_0.050000)
## rgn_vals = getValues(land_frac_0.050000)
## pts = as(land_frac_0.050000, "SpatialPoints")
## plot(land_frac_0.050000)
## points(pts[(rgn_vals>0) & (is.na(x_vals))])
## na_pts = pts[(rgn_vals>0) & (is.na(x_vals))] %>% as.data.frame
## min(na_pts$y)
## frac_0.050000[[16]][SpatialPoints(coords=na_pts[na_pts$y<80,])]

summary(topidx_mean_0.250000)
summary(topidx_mean_0.100000)
summary(topidx_mean_0.083333)
summary(topidx_mean_0.050000)
## summary(topidx_mean_0.016666)

topidx_stddev_0.250000 = raster("../data/jules_top/merit_dem_topidx_stddev_0.250000Deg.tif")
topidx_stddev_0.100000 = raster("../data/jules_top/merit_dem_topidx_stddev_0.100000Deg.tif")
topidx_stddev_0.083333 = raster("../data/jules_top/merit_dem_topidx_stddev_0.083333Deg.tif")
topidx_stddev_0.050000 = raster("../data/jules_top/merit_dem_topidx_stddev_0.050000Deg.tif")
topidx_stddev_0.016666 = raster("../data/jules_top/merit_dem_topidx_stddev_0.016666Deg.tif")

check_cells_valid(topidx_stddev_0.250000, land_frac_0.250000)
check_cells_valid(topidx_stddev_0.100000, land_frac_0.100000)
check_cells_valid(topidx_stddev_0.083333, land_frac_0.083333)
check_cells_valid(topidx_stddev_0.050000, land_frac_0.050000)
## check_cells_valid(topidx_stddev_0.016666[[1]], land_frac_0.016666)

summary(topidx_stddev_0.250000)
summary(topidx_stddev_0.100000)
summary(topidx_stddev_0.083333)
summary(topidx_stddev_0.050000)
summary(topidx_stddev_0.016666)

## jules_rivers_props
accum_0.250000 = raster("../data/jules_rivers_props/merit_accum_jules_0.250000Deg.tif")
accum_0.100000 = raster("../data/jules_rivers_props/merit_accum_jules_0.100000Deg.tif")
accum_0.083333 = raster("../data/jules_rivers_props/merit_accum_jules_0.083333Deg.tif")
accum_0.050000 = raster("../data/jules_rivers_props/merit_accum_jules_0.050000Deg.tif")
accum_0.016666 = raster("../data/jules_rivers_props/merit_accum_jules_0.016666Deg.tif")

check_cells_valid(accum_0.250000, land_frac_0.250000)
check_cells_valid(accum_0.100000, land_frac_0.100000)
check_cells_valid(accum_0.083333, land_frac_0.083333)
check_cells_valid(accum_0.050000, land_frac_0.050000)
## check_cells_valid(accum_0.016666[[1]], land_frac_0.016666)

summary(accum_0.250000)
summary(accum_0.100000)
summary(accum_0.083333)
summary(accum_0.050000)
## summary(accum_0.016666)

ldd_0.250000 = raster("../data/jules_rivers_props/merit_ldd_jules_0.250000Deg.tif")
ldd_0.100000 = raster("../data/jules_rivers_props/merit_ldd_jules_0.100000Deg.tif")
ldd_0.083333 = raster("../data/jules_rivers_props/merit_ldd_jules_0.083333Deg.tif")
ldd_0.050000 = raster("../data/jules_rivers_props/merit_ldd_jules_0.050000Deg.tif")
ldd_0.016666 = raster("../data/jules_rivers_props/merit_ldd_jules_0.016666Deg.tif")

check_cells_valid(ldd_0.250000, land_frac_0.250000)
check_cells_valid(ldd_0.100000, land_frac_0.100000)
check_cells_valid(ldd_0.083333, land_frac_0.083333)
check_cells_valid(ldd_0.050000, land_frac_0.050000)
## check_cells_valid(ldd_0.016666[[1]], land_frac_0.016666)

summary(ldd_0.250000)
summary(ldd_0.100000)
summary(ldd_0.083333)
summary(ldd_0.050000)
## summary(ldd_0.016666)

x_vals = getValues(ldd_0.250000)
rgn_vals = getValues(land_frac_0.250000)
pts = as(land_frac_0.250000, "SpatialPoints")
plot(land_frac_0.250000)
points(pts[(rgn_vals>0) & (is.na(x_vals))])
na_pts = pts[(rgn_vals>0) & (is.na(x_vals))] %>% as.data.frame
min(na_pts$y)
frac_0.250000[[16]][SpatialPoints(coords=na_pts[na_pts$y<80,])]

## jules_soil_props
b_cosby_0.250000 = raster("../data/jules_soil_props/b_cosby_sl1_0.250000Deg.tif")
hcap_cosby_0.250000 = raster("../data/jules_soil_props/hcap_cosby_sl1_0.250000Deg.tif")
hcon_cosby_0.250000 = raster("../data/jules_soil_props/hcon_cosby_sl1_0.250000Deg.tif")
ksat_cosby_0.250000 = raster("../data/jules_soil_props/k_sat_cosby_sl1_0.250000Deg.tif")
lambda_cosby_0.250000 = raster("../data/jules_soil_props/lambda_cosby_sl1_0.250000Deg.tif")
psi_m_cosby_0.250000 = raster("../data/jules_soil_props/psi_m_cosby_sl1_0.250000Deg.tif")
theta_crit_0.250000 = raster("../data/jules_soil_props/theta_crit_cosby_sl1_0.250000Deg.tif")
theta_sat_0.250000 = raster("../data/jules_soil_props/theta_sat_cosby_sl1_0.250000Deg.tif")
theta_wilt_0.250000 = raster("../data/jules_soil_props/theta_wilt_cosby_sl1_0.250000Deg.tif")

b_cosby_0.100000 = raster("../data/jules_soil_props/b_cosby_sl1_0.100000Deg.tif")
hcap_cosby_0.100000 = raster("../data/jules_soil_props/hcap_cosby_sl1_0.100000Deg.tif")
hcon_cosby_0.100000 = raster("../data/jules_soil_props/hcon_cosby_sl1_0.100000Deg.tif")
ksat_cosby_0.100000 = raster("../data/jules_soil_props/k_sat_cosby_sl1_0.100000Deg.tif")
lambda_cosby_0.100000 = raster("../data/jules_soil_props/lambda_cosby_sl1_0.100000Deg.tif")
psi_m_cosby_0.100000 = raster("../data/jules_soil_props/psi_m_cosby_sl1_0.100000Deg.tif")
theta_crit_0.100000 = raster("../data/jules_soil_props/theta_crit_cosby_sl1_0.100000Deg.tif")
theta_sat_0.100000 = raster("../data/jules_soil_props/theta_sat_cosby_sl1_0.100000Deg.tif")
theta_wilt_0.100000 = raster("../data/jules_soil_props/theta_wilt_cosby_sl1_0.100000Deg.tif")

b_cosby_0.083333 = raster("../data/jules_soil_props/b_cosby_sl1_0.083333Deg.tif")
hcap_cosby_0.083333 = raster("../data/jules_soil_props/hcap_cosby_sl1_0.083333Deg.tif")
hcon_cosby_0.083333 = raster("../data/jules_soil_props/hcon_cosby_sl1_0.083333Deg.tif")
ksat_cosby_0.083333 = raster("../data/jules_soil_props/k_sat_cosby_sl1_0.083333Deg.tif")
lambda_cosby_0.083333 = raster("../data/jules_soil_props/lambda_cosby_sl1_0.083333Deg.tif")
psi_m_cosby_0.083333 = raster("../data/jules_soil_props/psi_m_cosby_sl1_0.083333Deg.tif")
theta_crit_0.083333 = raster("../data/jules_soil_props/theta_crit_cosby_sl1_0.083333Deg.tif")
theta_sat_0.083333 = raster("../data/jules_soil_props/theta_sat_cosby_sl1_0.083333Deg.tif")
theta_wilt_0.083333 = raster("../data/jules_soil_props/theta_wilt_cosby_sl1_0.083333Deg.tif")

b_cosby_0.050000 = raster("../data/jules_soil_props/b_cosby_sl1_0.050000Deg.tif")
hcap_cosby_0.050000 = raster("../data/jules_soil_props/hcap_cosby_sl1_0.050000Deg.tif")
hcon_cosby_0.050000 = raster("../data/jules_soil_props/hcon_cosby_sl1_0.050000Deg.tif")
ksat_cosby_0.050000 = raster("../data/jules_soil_props/k_sat_cosby_sl1_0.050000Deg.tif")
lambda_cosby_0.050000 = raster("../data/jules_soil_props/lambda_cosby_sl1_0.050000Deg.tif")
psi_m_cosby_0.050000 = raster("../data/jules_soil_props/psi_m_cosby_sl1_0.050000Deg.tif")
theta_crit_0.050000 = raster("../data/jules_soil_props/theta_crit_cosby_sl1_0.050000Deg.tif")
theta_sat_0.050000 = raster("../data/jules_soil_props/theta_sat_cosby_sl1_0.050000Deg.tif")
theta_wilt_0.050000 = raster("../data/jules_soil_props/theta_wilt_cosby_sl1_0.050000Deg.tif")

b_cosby_0.016666 = raster("../data/jules_soil_props/b_cosby_sl1_0.016666Deg.tif")
hcap_cosby_0.016666 = raster("../data/jules_soil_props/hcap_cosby_sl1_0.016666Deg.tif")
hcon_cosby_0.016666 = raster("../data/jules_soil_props/hcon_cosby_sl1_0.016666Deg.tif")
ksat_cosby_0.016666 = raster("../data/jules_soil_props/k_sat_cosby_sl1_0.016666Deg.tif")
lambda_cosby_0.016666 = raster("../data/jules_soil_props/lambda_cosby_sl1_0.016666Deg.tif")
psi_m_cosby_0.016666 = raster("../data/jules_soil_props/psi_m_cosby_sl1_0.016666Deg.tif")
theta_crit_0.016666 = raster("../data/jules_soil_props/theta_crit_cosby_sl1_0.016666Deg.tif")
theta_sat_0.016666 = raster("../data/jules_soil_props/theta_sat_cosby_sl1_0.016666Deg.tif")
theta_wilt_0.016666 = raster("../data/jules_soil_props/theta_wilt_cosby_sl1_0.016666Deg.tif")

## Check netCDF soil/ice

## library(raster)
## ice = raster("../apps/India_0.250000Deg/jules_frac_5pft_2015_merit_india_0.250000Deg.nc", band=9)
## icev = getValues(ice)

## ths = raster("../apps/India_0.250000Deg/jules_soil_props_merit_india_0.250000Deg.nc", var="sm_sat")
## thsv = getValues(ths)

## unique(icev)
## thsv[icev==1]
## thsv[icev==0]

nco = nc_open("../apps/India_0.250000Deg/jules_land_frac_merit_india_0.250000Deg.nc")
land = ncvar_get(nco, "land_frac")
land = land > 0
nc_close(nco)

nco = nc_open("../apps/India_0.250000Deg/jules_pdm_merit_india_0.250000Deg.nc")
slope = ncvar_get(nco, "slope")
x = slope[land]
any(is.na(x))
nc_close(nco)

nco = nc_open("../apps/India_0.250000Deg/jules_latlon_merit_india_0.250000Deg.nc")
lon = ncvar_get(nco, "longitude")
lat = ncvar_get(nco, "latitude")
nc_close(nco)

nco = nc_open("../apps/India_0.250000Deg/jules_soil_props_merit_india_0.250000Deg.nc")
vars = c("sm_wilt","sm_crit","sm_sat","sathh","satcon","hcon","hcap","b","albsoil")
for (i in 1:length(vars)) {
    x = ncvar_get(nco, vars[i])
    if (any(is.na(x[land]))) {
        print("error")
    }
}
nc_close(nco)

nco = nc_open("../apps/India_0.250000Deg/jules_frac_5pft_2015_merit_india_0.250000Deg.nc")
frac = ncvar_get(nco, "frac")
for (i in 1:9) {
    lyr = frac[,,1]
    if (any(is.na(lyr[land]))) {
        print("error")
    }    
}
nc_close(nco)

## met
metnames = c("surface_pressure","2m_temperature","specific_humidity","10m_u_component_of_wind","10m_v_component_of_wind","mean_surface_downward_long_wave_radiation_flux","mean_surface_downward_short_wave_radiation_flux","large_scale_rain_rate","large_scale_snowfall_rate_water_equivalent","convective_rain_rate","convective_snowfall_rate_water_equivalent")
varnames = c("sp","t2m","q","u10","v10","msdwlwrf","msdwswrf","lsrr","lssfr","crr","csfr")
months = c("01","02","03","04","05","06","07","08","09","10","11","12")

for (j in 1:length(metnames)) {
    j=7
    for (k in 1:length(months)) {
        fn = paste0("era5_reanalysis_", metnames[j], "_india_2019", months[k], ".nc")
        nco = nc_open(file.path("~/JULES_India/data/drive", fn))
        var = ncvar_get(nco, varnames[j])
        nt = dim(var)[3]
        for (i in 1:nt) {
            vari = var[,,i]
            if (any(is.na(vari[land]))) {
                print("error")
            }
            print(range(vari))
        }
    }    
}

library(raster)
r = raster("/mnt/scratch/scratch/data/WFDEI/WFDEI_3h/Qair_WFDEI/Qair_WFDEI_197901.nc")
