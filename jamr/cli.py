"""Console script for jamr."""
import sys
import click
import tomllib

from grass_session import Session

from jamr.download import (download_esacci_landcover,
                           download_esacci_waterbodies,
                           download_soilgrids250m,
                           download_soilgrids1000m,
                           download_hydrography90m,
                           download_merit_dem,
                           download_merit_hydro)

from jamr.regions import set_regions
from jamr.elevation import process_merit_dem


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
    # download_esacci_landcover(config_dict)
    # download_esacci_waterbodies(config_dict)
    # download_soilgrids250m(config_dict)
    # download_soilgrids1000m(config_dict)
    # download_hydrography90m(config_dict)
    # download_merit_dem(config_dict)
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

    # Process elevation data
    process_merit_dem(config_dict)

    # # Process land fraction data
    # process_land_frac(config_dict)

    # Process topography data

    # Process land cover fraction

    # Process soil

    # Leave out for now: routing, overbank flow, LAI etc.

    session.close()


@main.command()
def process(config):
    click.echo("Process subcommand is working")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
