
import os 

import grass.script as gscript

from jamr.input.soilgrids import SoilGrids
from jamr.input.elevation import MERITDEM
from jamr.input.esaccilc import ESACCIWB, ESACCILC
from jamr.input.c4fraction import C4Fraction
from jamr.input.ecoregions import TerrestrialEcoregions


class InputData:
    """Data set class to populate GRASS GIS database with input files.

    Parameters
    ----------
    config : dict
        The run configuration.
    overwrite : bool
        Whether to overwrite files in the GRASS GIS database.
    """
    def __init__(self, 
                 config, 
                 overwrite=False):

        # TODO allow user to specify dataset source (perhaps in config?)
        self.landcover = ESACCILC(config, overwrite)
        self.waterbodies = ESACCIWB(config, overwrite)
        self.soil = SoilGrids(config, overwrite)
        self.elevation = MERITDEM(config, overwrite)
        self.ecoregions = TerrestrialEcoregions(config, overwrite)
        self.c4fraction = C4Fraction(config, overwrite)
        self.overwrite = overwrite

    def initial(self):
        self.landcover.initial()
        self.waterbodies.initial()
        self.soil.initial()
        self.elevation.initial()
        self.ecoregions.initial()
        self.c4fraction.initial() 

    def compute(self):
        pass

