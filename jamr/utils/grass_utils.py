#!/usr/bin/env python3

# import os
# import re
# import glob
# import time
# import math
# import logging
# import warnings

# from pathlib import Path
# from collections import namedtuple
# # from dataclasses import dataclass
from subprocess import PIPE

import grass.script as gscript

# import grass python libraries
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r


def grass_remove_mask():
    # try:
    #     r.mask(flags='r')
    # except grass.exceptions.CalledModuleError:
    #     pass
    p = gscript.start_command('r.mask', flags='r', stderr=PIPE)
    stdout, stderr = p.communicate()

    return 0

def grass_remove_tmp(type='raster'):
    p = gscript.start_command('g.remove', type='raster', pattern='*_tmp', flags='f', stderr=PIPE)
    stdout, stderr = p.communicate()

    return 0

def grass_set_named_region(rgn):
    # try:
    #     g.region(region=rgn)
    # except grass.exceptions.CalledModuleError:
    #     pass
    p = gscript.start_command('g.region', region=rgn, stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0

def grass_set_region_from_raster(raster, n=None, s=None, e=None, w=None):
    # This sets the region to the provided raster
    p = gscript.start_command('g.region', raster=raster)
    stdout, stderr = p.communicate()
    # Retrieve the region definition as a dictionary
    rgn_def = grass_region_definition()
    # Define a new region
    new_rgn_def = {
        'n': n if n else rgn_def['n'],
        's': s if s else rgn_def['s'],
        'e': e if e else rgn_def['e'],
        'w': w if w else rgn_def['w'],
        'align': raster,
        'ewres': rgn_def['ewres'], 
        'nsres': rgn_def['nsres'], 
    }
    grass_set_region(**new_rgn_def)
    return 0 

def grass_set_region(**kwargs):
    p = gscript.start_command('g.region', **kwargs, stderr=PIPE)
    stdout, stderr = p.communicate()
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

def grass_print_region():
    p = gscript.start_command('g.region', flags='p', stderr=PIPE)
    stdout, stderr = p.communicate()
    return 0

def grass_region_definition():
    rgn = gscript.core.region() 
    rgn_def = {k:v for k, v in rgn.items() if k in ['n', 'e', 's', 'w', 'ewres', 'nsres']}
    return rgn_def 

def grass_named_region_definition(rgn):
    # Get the current region 
    current_rgn_def = grass_region_definition()
    grass_set_named_region(rgn)
    rgn_def = grass_region_definition()
    grass_set_region(**current_rgn_def)
    return rgn_def

