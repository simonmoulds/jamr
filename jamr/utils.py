#!/usr/bin/env python3

import os
# import re
# import glob
# import time
# import math
# import logging
# import warnings

# from pathlib import Path
# from collections import namedtuple
# # from dataclasses import dataclass

import grass.script as gscript
import grass.exceptions 

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r


def grass_remove_mask():
    try:
        r.mask(flags='r')
    except grass.exceptions.CalledModuleError:
        pass

    return 0

def grass_set_named_region(rgn):
    try:
        g.region(region=rgn)
    except grass.exceptions.CalledModuleError:
        pass
    
    return 0

def grass_maplist(type='raster', pattern='*', mapset='PERMANENT'):
    maplist = gscript.core.list_grouped(type, pattern=pattern)[mapset]
    return maplist

def grass_map_exists(type, mapname, mapset='PERMANENT'):
    maplist = grass_maplist(type, pattern=mapname, mapset=mapset)
    if len(maplist) == 1:
        return True 
    else:
        return False