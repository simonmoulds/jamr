"""Console script for jamr."""

import sys
import click
import tomllib

from grass_session import Session

from grass.pygrass.modules.shortcuts import raster as r

from jamr.utils.setup_logging import setup_logging
from jamr.utils.regions import set_regions
from jamr.input.input import InputData
from jamr.process.process import ProcessData


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


# @main.command()
# @click.option('--config', default='config.toml', help='Path to configuration file')
# def download(config):
#     config_dict = parse_config(config)
#     download_esacci_landcover(config_dict)
#     download_esacci_waterbodies(config_dict)
#     download_soilgrids250m(config_dict)
#     download_soilgrids1000m(config_dict)
#     # download_hydrography90m(config_dict)
#     download_merit_dem(config_dict)
#     download_merit_hydro(config_dict)


@main.command()
@click.option('--config', default='config.toml', help='Path to configuration file')
def preprocess(config):
    
    setup_logging("output.log")

    config_dict = parse_config(config)

    gisdb = config_dict['main']['grass_gis_database']

    # Start GRASS session

    session = start_session(gisdb = gisdb)

    # FIXME This may not be necessary 
    # Create regions
    set_regions()

    # Make sure we're not using external
    r.external_out(flags='r')

    # Raw data products:
    # ==================

    inputdata = InputData(config_dict, overwrite=False)
    inputdata.initial()
    inputdata.compute()

    outputdata = ProcessData(config_dict, inputdata, overwrite=True)
    outputdata.initial()
    outputdata.compute()
    outputdata.write()

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


# From old file:
# # Make sure PYTHONPATH and GISBASE are set, e.g.
# # GISBASE=/usr/lib/grass78
# # PYTHONPATH=$GISBASE/etc/python
# import grass.script as gscript

# # # Settings
# # env = gscript.gisenv()
# # overwrite = True
# # env['GRASS_OVERWRITE'] = overwrite
# # env['GRASS_VERBOSE'] = False
# # env['GRASS_MESSAGE_FORMAT'] = 'standard'
# # gisdbase = env['GISDBASE']
# # location = env['LOCATION_NAME']
# # mapset = env['MAPSET']

# from jamr.download import (download_esacci_landcover,
#                            download_esacci_waterbodies,
#                            download_soilgrids250m,
#                            download_soilgrids1000m,
#                         #    download_hydrography90m,
#                            download_merit_dem,
#                            download_merit_hydro)
