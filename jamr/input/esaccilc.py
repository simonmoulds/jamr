
import os
import logging

from typing import List 
from pathlib import Path
from collections import namedtuple
from subprocess import PIPE, DEVNULL

import grass.script as gscript

from jamr.input.dataset import SFDS, MFDS
from jamr.utils import *


LOGGER = logging.getLogger(__name__)


class ESACCIWB(SFDS):
    """Data set class to represent ESA Water Bodies product."""
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def get_input_filenames(self):
        self.filenames = [self.config['landfraction']['esa']['data_file']]

    def set_mapnames(self):
        self.mapnames = ['esa_water_bodies']

    def read(self):
        p = gscript.start_command('r.in.gdal', input=self.preprocessed_filename, output=self.mapname, stderr=PIPE)
        stdout, stderr = p.communicate()


class ESACCILC(MFDS):
    def __init__(self, config, overwrite):
        start_year = int(config['landcover']['esa']['start_year'])
        end_year = int(config['landcover']['esa']['end_year'])
        self.years = [yr for yr in range(start_year, end_year + 1)]
        self.categories = [
            10, 11, 12, 20, 30, 40, 50, 60, 61, 62, 70, 71, 72, 
            80, 81, 82, 90, 100, 110, 120, 121, 122, 130, 140, 
            150, 151, 152, 153, 160, 170, 180, 190, 200, 201, 202, 210, 220
        ]
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess()
        self.read()

    def _get_filename(self, year):
        if int(year) <= 2015:
            return f'ESACCI-LC-L4-LCCS-Map-300m-P1Y-{year}-v2.0.7.tif' 
        elif int(year) > 2015:
            return f'C3S-LC-L4-LCCS-Map-300m-P1Y-{year}-v2.1.1.tif'

    def get_input_filenames(self):
        datadir = self.config['landcover']['esa']['data_directory']
        files = {}
        for year in self.years:
            filename = self._get_filename(year)
            files[year] = os.path.join(datadir, filename)
        self.filenames = files 

    def set_mapnames(self):
        mapnames = {}
        for year in self.years:
            mapnames[year] = f'esacci_lc_{year}'
        self.mapnames = mapnames 

    def read(self):
        for year in self.years:
            filename = self.preprocessed_filenames[year]
            mapname = self.mapnames[year]
            # This approach allows us to hide stdout/stderr:
            # https://grass.osgeo.org/grass83/manuals/libpython/pygrass_modules.html
            p = gscript.start_command('r.in.gdal', input=filename, output=mapname, stderr=PIPE)
            stdout, stderr = p.communicate()

    def __getitem__(self, index):
        return self.mapnames[index]

    def __len__(self):
        return len(self.mapnames) 

