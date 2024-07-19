
import os
import logging

from subprocess import PIPE

import grass.script as gscript

from osgeo import gdal

from jamr.input.dataset import SFDS
from jamr.utils.utils import *


LOGGER = logging.getLogger(__name__)


class C4Fraction(SFDS):
    def __init__(self, config, overwrite):
        self.years = [yr for yr in range(2001, 2020)]
        self.variables = ['C4_area', 'C4_grass_area', 'C4_crop_area']
        super().__init__(config, overwrite)
        
    def initial(self):
        self.preprocess()
        self.read()

    def get_input_filenames(self):
        self.filenames = [self.config['landcover']['c4']['data_file']]

    def set_mapnames(self):
        mapnames = {}
        for year in self.years: 
            year_mapnames = {} 
            for variable in self.variables:
                year_mapnames[variable] = f'c4_distribution_nus_v2.2_{variable}_{year}'
            mapnames[year] = year_mapnames
        self.mapnames = mapnames 

    def preprocess(self):
        scratch = self.config['main']['scratch_directory']
        os.makedirs(scratch, exist_ok=True) # Just in case it's not been created yet
        preprocessed_filenames = {}
        for variable in self.variables:
            preprocessed_filename = os.path.join(scratch, f'C4_distribution_NUS_v2.2_{variable}.tif')
            if not os.path.exists(preprocessed_filename) or self.overwrite:
                translate_opts = gdal.TranslateOptions(
                    format='GTiff', outputSRS='EPSG:4326', 
                    outputBounds=[-180, 90, 180, -90], 
                    # width=43200, height=21600, resampleAlg='bilinear'
                    width=720, height=360, resampleAlg='bilinear'
                )
                input_file = "NETCDF:" + self.filename + ":" + variable
                gdal.Translate(preprocessed_filename, input_file, options=translate_opts)

            preprocessed_filenames[variable] = preprocessed_filename

        self.preprocessed_filenames = preprocessed_filenames 

    def read(self):
        for variable in self.variables:
            input_file = self.preprocessed_filenames[variable]
            for i in range(len(self.years)):
                year = self.years[i]
                band = i + 1
                mapname = self.mapnames[year][variable]
                p = gscript.start_command('r.in.gdal', 
                                          input=input_file, 
                                          output=mapname, 
                                          band=band,
                                          stderr=PIPE)
                stdout, stderr = p.communicate()

