"""Console script for jamr."""

import os
import sys
import click
import tomllib
import logging

from grass_session import Session

from jamr.download import (download_esacci_landcover,
                           download_esacci_waterbodies,
                           download_soilgrids250m,
                           download_soilgrids1000m,
                           download_hydrography90m,
                           download_merit_dem,
                           download_merit_hydro)

from jamr.regions import set_regions
from jamr.elevation import MERITDEM
from jamr.landfraction import ESALandFraction
from jamr.landcover import TerrestrialEcoregions, C4Fraction, ESACCILC, ESACCIWB, Poulter2015PFT
# from jamr.topography import process_topographic_index
from jamr.soil import SoilGrids, CosbySoilProperties #, TomasellaHodnettSoilProperties, ZhangSchaapSoilProperties


logging.getLogger('jamr').addHandler(logging.NullHandler())


def parse_config(config):
    # Parse config
    with open(config, "rb") as f:
        config_dict = tomllib.load(f)
    return config_dict


def start_session(gisdb):
    PERMANENT = Session()
    PERMANENT.open(gisdb = gisdb, location = "jamr", create_opts='EPSG:4326')
    return PERMANENT

class InputData:
    def __init__(self, 
                 config, 
                 overwrite=False):

        # TODO check classes 
        # TODO allow user to specify dataset source (perhaps in config?)
        self.landcover = ESACCILC(config, overwrite)
        self.waterbodies = ESACCIWB(config, overwrite)
        self.soil = SoilGrids(config, overwrite)
        self.elevation = MERITDEM(config, overwrite)
        self.ecoregions = TerrestrialEcoregions(config, overwrite)
        self.c4fraction = C4Fraction(config, overwrite)

    def initial(self):
        self.landcover.initial()
        self.waterbodies.initial()
        self.soil.initial()
        self.elevation.initial()
        self.ecoregions.initial()
        self.c4fraction.initial() 


class JULESAncillaryData:
    # def __init__(self, config, inputdata, overwrite):
    def __init__(self, config, overwrite):
        self.config = config
        self.input_data = InputData(config, overwrite)
        self.input_data.initial()
        self.landfrac = ESALandFraction()
        self.frac = [] 
        self.soil_props = [] 

    def _set_land_fraction(self):
        self.landfrac = ESALandFraction() 

    def _set_frac(self):
        # class LandCoverFracFactory()
        self.frac = []
        if 'Poulter' in self.config['methods']['frac']:
            self.frac += Poulter2015PFT()

    def _set_soil_props(self):
        # class SoilPropertiesFactory()
        self.soil_props = [] 
        if 'Cosby' in self.config['methods']['soil_props']:
            self.soil_props += CosbySoilProperties()

        if 'TomasellaHodnett' in self.config['methods']['soil_props']:
            self.soil_props += TomasellaHodnettSoilProperties()

    def compute(self):
        pass

    def write(self):
        pass 


@click.group()
def main(args=None):
    """Console script for jamr."""
    pass
    # click.echo("Replace this message by putting your code into "
    #            "jamr.cli.main")
    # click.echo("See click documentation at https://click.palletsprojects.com/")
    # return 0


@main.command()
@click.option('--config', default='config.toml', help='Path to configuration file')
def download(config):
    config_dict = parse_config(config)
    download_esacci_landcover(config_dict)
    download_esacci_waterbodies(config_dict)
    download_soilgrids250m(config_dict)
    download_soilgrids1000m(config_dict)
    # download_hydrography90m(config_dict)
    download_merit_dem(config_dict)
    download_merit_hydro(config_dict)


@main.command()
@click.option('--config', default='config.toml', help='Path to configuration file')
def preprocess(config):

    config_dict = parse_config(config)

    gisdb = config_dict['main']['grass_gis_database']

    # Start GRASS session
    session = start_session(gisdb = gisdb)
    
    # Create regions
    set_regions()

    # Raw data products:
    # ==================
    input_data = InputData(config_dict, overwrite=False)
    input_data.initial()

    region='uk_0.008333Deg'

    # Derived data products:
    # ======================

    # landfrac = ESALandFraction(config_dict, input_data, region, overwrite=False)
    # landfrac.compute() 

    # frac = Poulter2015PFT(config_dict, input_data, region, overwrite=False)
    # frac.compute()

    # soilprops = CosbySoilProperties(config_dict, input_data, region, overwrite=False)
    # soilprops.compute() 

    # output_directory = config_dict['main']['output_directory']
    # os.makedirs(output_directory, exist_ok=True)

    session.close()


@main.command()
def process(config):
    click.echo("Process subcommand is working")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
