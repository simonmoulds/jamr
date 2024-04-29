"""Console script for jamr."""
import sys
import click
import tomllib

from grass_session import Session

from jamr.regions import set_regions
from jamr.elevation import process_merit_dem


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
def preprocess(config):
    click.echo("Preprocess subcommand is working")

    # Parse config
    with open(config, "rb") as f:
        config_dict = tomllib.load(f)

    gisdb = config_dict['main']['gisdb']

    # Start GRASS session
    session = start_session(gisdb = gisdb)

    # Create regions
    set_regions()

    # Process elevation data
    process_merit_dem(config_dict)

    session.close()


@main.command()
def process(config):
    click.echo("Process subcommand is working")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
