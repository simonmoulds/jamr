
import os
import xarray
import logging

from subprocess import PIPE

import grass.script as gscript

from osgeo import gdal

from jamr.input.dataset import SFDS
from jamr.utils.grass_utils import *


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
        ds = xarray.open_dataset(self.filename)
        for year in self.years:
            year_preprocessed_filenames = {}
            for variable in self.variables:
                da = ds[variable]
                da = da.transpose('years', 'lat', 'lon')

                preprocessed_netcdf_filename = os.path.join(scratch, f'C4_distribution_NUS_v2.2_{variable}_{year}.nc')
                preprocessed_gtiff_filename = os.path.join(scratch, f'C4_distribution_NUS_v2.2_{variable}_{year}.tif')
                year_preprocessed_filenames[variable] = preprocessed_gtiff_filename
                if not os.path.exists(preprocessed_gtiff_filename) or self.overwrite:
                    da0 = da.sel({'years': year})
                    da0 = da0.rename({'lat': 'latitude', 'lon': 'longitude'})
                    da0.to_netcdf(preprocessed_netcdf_filename)
                    translate_opts = gdal.TranslateOptions(
                        format='GTiff', outputSRS='EPSG:4326', 
                        outputBounds=[-180, 90, 180, -90], 
                        width=720, height=360, resampleAlg='bilinear'
                    )
                    input_file = "NETCDF:" + preprocessed_netcdf_filename + ":" + variable
                    gdal.Translate(preprocessed_gtiff_filename, preprocessed_netcdf_filename, options=translate_opts)


            preprocessed_filenames[year] = year_preprocessed_filenames

        self.preprocessed_filenames = preprocessed_filenames 

    def read(self):
        for year in self.years:
            for variable in self.variables:
                input_file = self.preprocessed_filenames[year][variable]
                mapname = self.mapnames[year][variable]
                print("Hello, world")
                p = gscript.start_command('r.in.gdal', 
                                          input=input_file, 
                                          output=mapname, 
                                          overwrite=True,
                                        #   overwrite=self.overwrite,
                                          stderr=PIPE)
                stdout, stderr = p.communicate()
                # Set null values to zero
                p = gscript.start_command('r.null', map=mapname, null=0, stderr=PIPE)
                stdout, stderr = p.communicate()
