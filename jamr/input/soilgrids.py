
import os
import logging

from pathlib import Path
from subprocess import PIPE
from collections import namedtuple

import grass.script as gscript

from osgeo import gdal

from jamr.utils import *
from jamr.input.dataset import MFDS
from jamr.utils.constants import (SG_VARIABLES,
                                  SG_VARIABLES_ABBR,
                                  SG_HORIZONS,
                                  SG_SUMMARY_STATISTICS,
                                  SG_RESOLUTIONS)


LOGGER = logging.getLogger(__name__)

# TODO 
# - add POLARIS data [USA only]
# - add Saxton & Rawls PTFs https://doi.org/10.2136/sssaj2005.0117 [USA only]
# - add Toth et al PTFs [Europe only]


SoilHorizonMaps = namedtuple(
    'SoilHorizonMaps', 
    ['clay_content', 'sand_content', 'silt_content', 'bulk_density', 'cation_exchange_capacity', 'ph_index', 'soil_organic_carbon'],
    defaults=(None,) * 7
)


class SoilGridsHorizon(MFDS):
    def __init__(self,
                 config, 
                 data_directory, 
                 scratch_directory, 
                 variables, 
                 resolution,
                 summary_statistic,
                 horizon,
                 overwrite) -> None:

        self.data_directory = data_directory
        self.scratch_directory = scratch_directory
        self.variables = variables 
        self.resolution = resolution
        self.summary_statistic = summary_statistic 
        self.horizon = horizon
        super().__init__(config, overwrite)

    @property
    def _filename_format(self):
        if self.resolution == 250: 
            return '{variable}_{horizon}_{statistic}.tif' 
        elif self.resolution == 1000:
            return '{variable}_{horizon}_{statistic}_1000.tif'
        elif self.resolution == 5000:
            return '{variable}_{horizon}_{statistic}_5000.tif'
        else:
            return None

    def get_input_filenames(self):
        filenames = {}
        for variable in self.variables:
            variable_abbr = SG_VARIABLES_ABBR[variable]
            filenames[variable] = self._filename_format.format(
                variable=variable_abbr, horizon=self.horizon, statistic=self.summary_statistic
            )
        self.filenames = filenames

    def set_mapnames(self):
        mapnames = {} 
        horizon_fmt = self.horizon.replace('-', '_')
        for variable in self.variables:
            variable_abbr = SG_VARIABLES_ABBR[variable]
            mapnames[variable] = f'sg_{self.resolution}_{variable_abbr}_{horizon_fmt}_{self.summary_statistic}'
        self.mapnames = SoilHorizonMaps(**mapnames)

    def initial(self):
        self.preprocess()
        self.read()    

    def preprocess(self):
        preprocessed_filenames = {}
        opts = gdal.WarpOptions(format='GTiff', outputBounds=[-180, -90, 180, 90], xRes = 1 / 120., yRes = 1 / 120., dstSRS = 'EPSG:4326')
        for key, filename in self.filenames.items():
            basename, extension = Path(filename).stem, Path(filename).suffix 
            input_map = os.path.join(self.data_directory, filename)
            output_map = os.path.join(self.scratch_directory, basename + '_ll' + extension)
            preprocessed_filenames[key] = output_map 
            if not os.path.exists(output_map) or self.overwrite:
                mymap = gdal.Warp(output_map, input_map, options=opts)
                mymap = None
        self.preprocessed_filenames = preprocessed_filenames

    def read(self):
        for key, filename in self.preprocessed_filenames.items():
            mapname = getattr(self.mapnames, key)
            p = gscript.start_command('r.in.gdal', input=filename, output=mapname, stderr=PIPE)
            stdout, stderr = p.communicate()


class SoilGrids(MFDS):
    """Data set class to load SoilGrids data.

    Use subclasses of this class for training/evaluating a model on a specific data set. E.g. use `CamelsUS` for the US
    CAMELS data set and `CamelsGB` for the CAMELS GB data set.

    Parameters
    ----------
    config : dict
        The run configuration.
    overwrite : bool
        Whether to overwrite files in the GRASS GIS database.
    """
    def __init__(self, 
                 config: dict, 
                 overwrite: bool) -> None:

        self.data_directory = config['soil']['soilgrids']['data_directory']
        self.scratch_directory = config['main']['scratch_directory'] 
        self.variables = config['soil']['soilgrids']['variables']
        if not all([variable in SG_VARIABLES for variable in self.variables]):
            raise ValueError()

        self.horizons = config['soil']['soilgrids']['horizons']
        self.current_horizon = None
        if not all([horizon in SG_HORIZONS for horizon in self.horizons]):
            raise ValueError()

        resolution = int(config['soil']['soilgrids']['resolution'])
        if not resolution in SG_RESOLUTIONS:
            raise ValueError()
        self.resolution = resolution 

        self.summary_statistic = config['soil']['soilgrids']['summary_statistic']
        if not self.summary_statistic in SG_SUMMARY_STATISTICS:
            raise ValueError() 

        super().__init__(config, overwrite)

    def get_input_filenames(self):
        pass

    def set_mapnames(self):
        pass

    def initial(self): 
        # The soilgrids data is repeated for several horizons. 
        data = {}
        for horizon in self.horizons:
            self.current_horizon = horizon 
            horizon_obj = SoilGridsHorizon(self.config, self.data_directory, self.scratch_directory, self.variables, self.resolution, self.summary_statistic, horizon, self.overwrite)
            horizon_obj.initial() 
            data[horizon] = horizon_obj

        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data) 

    def __setitem__(self, key, value):
        self.data[key] = value 

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)
    
    def items(self):
        return self.data.items() 
    
    def values(self):
        return self.data.values() 
    
    def keys(self):
        return self.data.keys()

