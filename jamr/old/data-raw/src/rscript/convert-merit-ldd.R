## Author : Simon Moulds
## Date   : March 2020

library(raster)
library(magrittr)

datadir = "/home/sm510/projects/jules_apps/data/aux/hydro"
resolutions = c("01min","03min","05min","06min","15min")
suffixes=c("0.016666","0.050000","0.083333","0.100000","0.250000")
for (k in 1:length(resolutions)) {
    res = resolutions[k]
    
    lddx = raster(file.path(datadir, paste0("nextxy_varx_", res, ".tif"))) %>% as.matrix
    lddy = raster(file.path(datadir, paste0("nextxy_vary_", res, ".tif"))) %>% as.matrix
    ldd = lddx
    ldd[] = NA

    for (i in 1:nrow(lddx)) {
        for (j in 1:ncol(lddx)) {        
            yc = lddy[i,j]
            xc = lddx[i,j]
            if (!is.na(yc)) {
                if ((yc == -9) | (yc == -10)) {
                    ldd[i,j] = 5            
                } else if (yc == i) {            
                    if (xc == (j + 1)) {
                        ldd[i,j] = 6
                    } else if (xc == (j - 1)) {
                        ldd[i,j] = 4
                    }                
                } else if (yc == (i + 1)) {
                    if (xc == j) {
                        ldd[i,j] = 2
                    } else if (xc == (j + 1)) {
                        ldd[i,j] = 3
                    } else if (xc == (j - 1)) {
                        ldd[i,j] = 1
                    }            

                } else if (yc == (i - 1)) {
                    if (xc == j) {
                        ldd[i,j] = 8
                    } else if (xc == (j + 1)) {
                        ldd[i,j] = 9                
                    } else if (xc == (j - 1)) {
                        ldd[i,j] = 7                
                    }            
                }
            }        
        }
    }

    ## the above conversion was to LISFLOOD; to avoid complication,
    ## we just recode the lisflood values
    ldd_jules=ldd
    ldd_jules[] = NA
    ldd_jules[ldd==1] = 6
    ldd_jules[ldd==2] = 5
    ldd_jules[ldd==3] = 4
    ldd_jules[ldd==4] = 7
    ldd_jules[ldd==5] = 0
    ldd_jules[ldd==6] = 3
    ldd_jules[ldd==7] = 8
    ldd_jules[ldd==8] = 1
    ldd_jules[ldd==9] = 2
    
    r = raster(file.path(datadir, paste0("nextxy_varx_", res, ".tif")))
    r[] = ldd_jules
    writeRaster(
        r,
        file.path(datadir, paste0("merit_ldd_jules_", suffixes[k], "Deg.tif")),
        overwrite=TRUE
    )
    
    ## ## 2. Channels
    ## rivwth = raster(file.path(datadir, paste0("rivwth_gwdlr_", res, ".tif")))   
    ## channel = rivwth > 0
    ## writeRaster(
    ##     channel,
    ##     file.path(datadir, paste0("merit_channel_", suffixes[k], "Deg.tif")),
    ##     overwrite=TRUE
    ## )    

    ## ## 3. Channel gradient
    ## ## Do in GRASS GIS

    ## ## 4. Channel Manning's n
    ## rivman = raster(file.path(datadir, paste0("rivman_", res, ".tif")))
    ## writeRaster(
    ##     rivman,
    ##     file.path(datadir, paste0("merit_channel_n_", suffixes[k], "Deg.tif")),
    ##     overwrite=TRUE
    ## )    

    ## ## 5. Channel length
    ## rivlen = raster(file.path(datadir, paste0("rivlen_", res, ".tif")))
    ## writeRaster(
    ##     rivlen,
    ##     file.path(datadir, paste0("merit_channel_length_", suffixes[k], "Deg.tif")),
    ##     overwrite=TRUE
    ## )    

    ## ## 6. Channel bottom depth
    ## rivhgt = raster(file.path(datadir, paste0("rivhgt_", res, ".tif")))
    ## writeRaster(
    ##     rivhgt,
    ##     file.path(datadir, paste0("merit_channel_depth_", suffixes[k], "Deg.tif")),
    ##     overwrite=TRUE
    ## )
    
    ## ## 7. Channel bottom depth
    ## rivwth = raster(file.path(datadir, paste0("rivwth_gwdlr_", res, ".tif")))
    ## writeRaster(
    ##     rivhgt,
    ##     file.path(datadir, paste0("merit_channel_width_", suffixes[k], "Deg.tif")),
    ##     overwrite=TRUE
    ## )        
}
    
    
