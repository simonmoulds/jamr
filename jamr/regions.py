#!/usr/bin/env python3

import os
import math
import numpy as np

# import grass.script as gscript

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
# from grass.pygrass.modules.shortcuts import raster as r
# from grass.pygrass.modules.shortcuts import vector as v
# from grass.pygrass.modules.shortcuts import temporal as t

from jamr.constants import REGIONS


def to_dms(decimal_degrees):
    # convert degrees into dms and a sign indicator
    degrees = np.array(decimal_degrees)
    sign = np.where(degrees < 0, -1, 1)
    r, s = np.divmod(np.round(np.abs(degrees) * 3600, 1), 60)
    d, m = np.divmod(r, 60)
    # np.transpose([d, m, s]*sign)  # if you wanted signed results
    return np.transpose([d, m, s, sign])


def format_dms(dms):
    degrees = str(int(dms[0]))
    minutes = str(int(dms[1])).zfill(2)
    seconds = dms[2]
    if (seconds == 0):
        return degrees + ":" + minutes
    else:
        if (seconds.is_integer()):
            seconds = str(int(seconds)).zfill(2)
        else:
            seconds = "%05.2f" % seconds

        return degrees + ":" + minutes + ":" + seconds


def format_extent(extent):

    def _format_longitude(lon):
        if lon < 0:
            lon = str(int(abs(lon))) + 'W'
        else:
            lon = str(int(lon)) + 'E'
        return lon

    def _format_latitude(lat):
        if lat < 0:
            lat = str(int(abs(lat))) + 'S'
        else:
            lat = str(int(lat)) + 'N'
        return lat

    w, s, e, n = extent
    west = _format_longitude(max(-180, math.floor(w)))
    east = _format_longitude(min(180, math.ceil(e)))
    south = _format_latitude(max(-90, math.floor(s)))
    north = _format_latitude(min(90, math.ceil(n)))
    return west, east, south, north


def _set_region(region_name, res_decimal_degrees, extent = [-180, -90, 180, 90]):
    west, east, south, north = format_extent(extent)
    res_dms = to_dms(abs(res_decimal_degrees))
    res_dms = format_dms(res_dms)
    # gscript.run_command(
    #     "g.region", e=east, w=west, n=north, s=south, res=res, save=region_name
    # )
    g.region(e=east, w=west, n=north, s=south, res=res, save=region_name)
    return None


def set_regions(config):
    for region_name, region_def in REGIONS.items():
        res = _set_region(region_name, region_def['res'], region_def['extent'])
