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

    landcover = ESACCILC(config_dict, overwrite=False) 
    landcover.initial()
    
    # # TODO eventually make this into a separate class 
    # # Load raw data objects
    # elevation = MERITDEM(config_dict, overwrite=False)
    # ecoregions = TerrestrialEcoregions(config_dict, overwrite=False)
    # c4fraction = C4Fraction(config_dict, overwrite=False)
    # waterbodies = ESACCIWB(config_dict, overwrite=False)
    # landcover = ESACCILC(config_dict, overwrite=False) 
    # soil = SoilGrids(config_dict, overwrite=False) 

    # elevation.initial()
    # ecoregions.initial() 
    # c4fraction.initial()
    # waterbodies.initial()
    # landcover.initial()
    # soil.initial() 

    # region='uk_0.008333Deg'

    # # Now create derived data products 
    # landfrac = ESALandFraction(config_dict, waterbodies, landcover, region, overwrite=False)
    # frac = Poulter2015PFT(config_dict, landcover, region, overwrite=False)
    # soilprops = CosbySoilProperties(config_dict, soil, region, overwrite=False)

    # landfrac.compute() 
    # # frac.compute() 
    # soilprops.compute() 

    # output_directory = config_dict['main']['output_directory']
    # os.makedirs(output_directory, exist_ok=True)
    # frac.write() 

    session.close()


@main.command()
def process(config):
    click.echo("Process subcommand is working")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
