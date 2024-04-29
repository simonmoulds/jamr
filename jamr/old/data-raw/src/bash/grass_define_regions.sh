#!/bin/bash

# This script defines some regions which are used during the analysis

# 0.5 degrees (not currently used but useful to have)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:30 \
    save=globe_0.500000Deg \
    $OVERWRITE

# 0.25 degrees (CaMa-Flood)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:15 \
    save=globe_0.250000Deg \
    $OVERWRITE

# 0.1 degrees (CaMa-Flood)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:06 \
    save=globe_0.100000Deg \
    $OVERWRITE

# 0.083333 degrees (CaMa-Flood)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:05 \
    save=globe_0.083333Deg \
    $OVERWRITE

# 0.05 degrees (CaMa-Flood)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:03 \
    save=globe_0.050000Deg \
    $OVERWRITE

# 0.016667 degrees (CaMa-Flood)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:01 \
    save=globe_0.016667Deg \
    $OVERWRITE

# 0.008333 degrees (frac, soil)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:00:30 \
    save=globe_0.008333Deg \
    $OVERWRITE

# 0.004167 degrees (topography)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:00:15 \
    save=globe_0.004167Deg \
    $OVERWRITE

# 0.002083 degrees (250m soil)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:00:07.5 \
    save=globe_0.002083Deg \
    $OVERWRITE

# 0.000833 degrees (topography)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:00:03 \
    save=globe_0.000833Deg \
    $OVERWRITE

# 0.002778 degrees (ESA CCI LC)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:00:10 \
    save=globe_0.002778Deg \
    $OVERWRITE

# 0.041667 degrees (modis 4km lai - ants)
g.region \
    e=180E w=180W n=90N s=90S \
    res=0:02:30 \
    save=globe_0.041667Deg \
    $OVERWRITE

# NOT USED:

# # 0.125 degrees
# g.region \
#     e=180E w=180W n=90N s=90S \
#     res=0:07:30 \
#     save=globe_0.125000Deg \
#     $OVERWRITE

# # 0.0625 degrees
# g.region \
#     e=180E w=180W n=90N s=90S \
#     res=0:03:45 \
#     save=globe_0.062500Deg \
#     $OVERWRITE

# # 0.01 degrees
# g.region \
#     e=180E w=180W n=90N s=90S \
#     res=0:00:36 \
#     save=globe_0.010000Deg \
#     $OVERWRITE
