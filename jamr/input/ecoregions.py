
import os
import zipfile
import logging

from subprocess import PIPE

import grass.script as gscript

from osgeo import gdal, gdalconst

from jamr.input.dataset import SFDS
from jamr.utils.grass_utils import *


LOGGER = logging.getLogger(__name__)


class TerrestrialEcoregions(SFDS):
    def __init__(self, config, overwrite):
        super().__init__(config, overwrite)

    def initial(self):
        self.preprocess() 
        self.read() 

    def get_input_filenames(self):
        self.filenames = [self.config['landcover']['teow']['data_file']]
    
    def set_mapnames(self):
        self.mapnames = ['tropical_broadleaf_forest_globe_0.008333Deg']

    def preprocess(self):

        scratch = self.config['main']['scratch_directory']
        os.makedirs(scratch, exist_ok=True) # Just in case it's not been created yet
        
        # Extract data from zip archive
        with zipfile.ZipFile(self.filename, 'r') as f:
            f.extractall(scratch)

        shpfile = os.path.join(scratch, 'official', 'wwf_terr_ecos.shp')
        preprocessed_filename = os.path.join(scratch, 'wwf_terr_ecos_0.008333Deg.tif')
        if not os.path.exists(preprocessed_filename) or self.overwrite:
            rasterize_opts = gdal.RasterizeOptions(
                outputBounds=[-180, -90, 180, 90], 
                outputType=gdalconst.GDT_Byte,
                width=43200, height=21600, 
                allTouched=True, attribute='BIOME'
            )
            gdal.Rasterize(preprocessed_filename, shpfile, options=rasterize_opts)

        self.preprocessed_filenames = [preprocessed_filename]

    def read(self):
        output_map = self.mapnames[0]
        if not grass_map_exists('raster', output_map, 'PERMANENT') or self.overwrite:
            p = gscript.start_command('r.in.gdal', 
                                      flags='a',
                                      input=self.preprocessed_filenames[0], 
                                      output='wwf_terr_ecos_globe_0.008333Deg',
                                      overwrite=self.overwrite,
                                      stderr=PIPE)
            stdout, stderr = p.communicate()

            # Set region to input map
            g.region(raster='wwf_terr_ecos_globe_0.008333Deg')
            p = gscript.start_command('r.null', map='wwf_terr_ecos_globe_0.008333Deg', setnull=0)
            stdout, stderr = p.communicate()
            
            p = gscript.start_command('r.grow.distance',
                                      input='wwf_terr_ecos_globe_0.008333Deg',
                                      value='wwf_terr_ecos_interp_globe_0.008333Deg',
                                      overwrite=self.overwrite,
                                      stderr=PIPE)
            stdout, stderr = p.communicate()

            p = gscript.start_command('r.mapcalc',
                                      expression=f'tropical_broadleaf_forest_globe_0.008333Deg = if((wwf_terr_ecos_interp_globe_0.008333Deg == 1) | (wwf_terr_ecos_interp_globe_0.008333Deg == 2), 1, 0)',
                                      overwrite=self.overwrite,
                                      stderr=PIPE)
            stdout, stderr = p.communicate()

