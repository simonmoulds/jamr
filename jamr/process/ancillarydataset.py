
from abc import abstractmethod
from subprocess import PIPE

import grass.script as gscript

from jamr.utils.grass_utils import (grass_remove_mask,
                              grass_set_region,
                              grass_set_region_from_raster)

class AncillaryDataset:
    def __init__(self, 
                 config, 
                 inputdata,
                 overwrite):

        self.config = config 
        self.inputdata = inputdata
        self.overwrite = overwrite
        self.region_name = config['region']['name']
        grass_remove_mask()
        self._set_mapnames() 

    @abstractmethod
    def _set_mapnames(self):
        pass 

    @abstractmethod 
    def compute(self):
        pass

    def _set_native_region(self, mapname):
        grass_set_region_from_raster(raster=mapname,
                                     n=self.config['region']['north'],
                                     s=self.config['region']['south'],
                                     e=self.config['region']['east'],
                                     w=self.config['region']['west'])
        
    def _set_target_region(self):
        # TODO set target region in config
        grass_set_region(ewres=0.008333333333, 
                         nsres=0.008333333333, 
                         n=self.config['region']['north'],
                         s=self.config['region']['south'],
                         e=self.config['region']['east'],
                         w=self.config['region']['west'])

    def _resample(self, input_map, output_map, method):
        # p = gscript.start_command('r.external.out', 
        #                           directory=self.config['main']['output_directory'], 
        #                           format='GTiff', 
        #                           option='COMPRESS=DEFLATE')
        p = gscript.start_command('r.resamp.stats',
                                  flags='w', # weighted average
                                  input=input_map,
                                  output=output_map,
                                  method=method,
                                  overwrite=self.overwrite,
                                  stderr=PIPE)
        stdout, stderr = p.communicate()
        # p = gscript.start_command('r.external.out', flags='r', stderr=PIPE)
        return 0
