#!/bin/bash

# ========================================================= #
# Write Help
# ========================================================= #

Help()
{
    echo "Script to create JULES ancillary maps in netCDF format."
    echo
    echo "Syntax: create-app.sh [-h|o]"
    echo "options:"
    echo "-h | --help          Print this help message."
    echo "-o | --overwrite     Overwrite existing database (WARNING: could take a long time)."
    echo "--one-d              Write one-dimensional netCDF files."
    echo "--grid-dim-name      The name of the single grid dimension, if `--one-d` specified."
    echo "--x-dim-name         The name of the x dimension."
    echo "--y-dim-name         The name of the y dimension."
    echo "--time-dim-name      The name of the time dimension in files with time-varying data."
    echo "--type-dim-name      The name of the type dimension."
    echo "--tile-dim-name      The name of the tile dimension."    
    echo "--soil-dim-name      The name of the soil dimension."
    echo "--snow-dim-name      The name of the snow dimension."
    echo "--pdm                Write PDM ancillary maps."
    echo "--topmodel           Write TOPMODEL ancillary maps."
    echo "--routing            Write river routing ancillary maps."
    echo "--overbank           Write overbank ancillary maps."
    echo "--nine-pft           Write 9 PFT fraction maps."
    echo "--five-pft           Write 5 PFT fraction maps."
    echo "--write-pft-for-lai  Format netCDF so that it is compatible with ANTS LAI module"
    echo "--no-land-frac       Do not write JULES land fraction data."
    echo "--no-latlon          Do not write JULES latitude/longitude data."
    echo "--soil-cosby         Write soil maps computed with Cosby PTFs."
    echo "--soil-tomasella     Write soil maps computed with Tomasella & Hodnett PTFs."
    echo "--soil-rosetta       Write soil maps computed with Rosetta3 PTFs."
    echo "--region             Name for model domain, e.g. 'globe'."
    echo "--res                Resolution of model region, in DMS (e.g. 0:15, not 0.25)."
    echo "--ext                Extent of model region (xmin, ymin, xmax, ymax), in DMS."
    echo "--file               Name of geocoded raster file to use to specify region."
    echo "--use-file-land-frac Use file indicated by `--file` to define land frac"
    echo "-d | --destdir    Output directory."
    echo
}

# ========================================================= #
# Get options
# ========================================================= #

# Based on advice from:
# https://www.codebyamir.com/blog/parse-command-line-arguments-using-getopt
# https://stackoverflow.com/a/7948533 

# Adapted from:
# https://stackoverflow.com/a/14203146 ***

# Set defaults
ONE_D=0
GRID_DIM_NAME=land
X_DIM_NAME=x
Y_DIM_NAME=y
TIME_DIM_NAME=time
PFT_DIM_NAME=pft
TYPE_DIM_NAME=type
TILE_DIM_NAME=tile
SOIL_DIM_NAME=soil
SNOW_DIM_NAME=snow
PDM=0
TOPMODEL=0
ROUTING=0
OVERBANK=0
NINEPFT=0
FIVEPFT=0
ANTSFORMAT=0
LAND_FRAC=1
LATLON=1
COSBY=0
TOMASELLA=0
ROSETTA=0
XMIN=-180
YMIN=-90
XMAX=180
YMAX=90
XRES=0:30
YRES=0:30
FILE_LAND_FRAC=0
OUTDIR=.
POSITIONAL=()

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
	-h|--help)
	    Help
	    # HELP="$2"
	    # shift
	    # shift
	    exit
	    ;;
	-o|--overwrite)
	    OVERWRITE='--overwrite'
	    shift
	    # shift
	    ;;
	--one-d)
	    ONE_D=1
	    shift
	    ;;
	--grid-dim-name)
	    GRID_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--x-dim-name)
	    X_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--y-dim-name)
	    Y_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--time-dim-name)
	    TIME_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--pft-dim-name)
	    PFT_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--type-dim-name)
	    TYPE_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--tile-dim-name)
	    TILE_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--soil-dim-name)
	    SOIL_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--snow-dim-name)
	    SNOW_DIM_NAME="$2"
	    shift
	    shift
	    ;;
	--pdm)
	    PDM=1
	    shift
	    ;;
	--topmodel)
	    TOPMODEL=1
	    shift
	    ;;
	--routing)
	    ROUTING=1
	    shift
	    ;;
	--overbank)
	    OVERBANK=1
	    shift
	    ;;
	--nine-pft)
	    NINEPFT=1
	    shift
	    ;;
	--five-pft)
	    FIVEPFT=1
	    shift
	    ;;
	--write-pft-for-lai)
	    ANTSFORMAT=1
	    shift
	    ;;
	--no-land-frac)
	    LAND_FRAC=0
	    shift
	    ;;
	--no-latlon)
	    LATLON=0
	    shift
	    ;;
	--soil-cosby)
	    COSBY=1
	    shift
	    ;;
	--soil-tomasella)
	    TOMASELLA=1
	    shift
	    ;;
	--soil-rosetta)
	    ROSETTA=1
	    shift
	    ;;
	--region)
	    REGION="$2"
	    shift
	    shift
	    ;;	
	--res)
	    XRES="$2"
	    YRES="$3"
	    shift
	    shift
	    ;;
	--ext)
	    XMIN="$2"
	    YMIN="$3"
	    XMAX="$4"
	    YMAX="$5"
	    shift
	    shift
	    ;;
	--file)
	    FILE="$2"
	    shift
	    shift
	    ;;
	--use-file-land-frac)
	    FILE_LAND_FRAC=1
	    shift
	    ;;
	-d|--destdir)
	    OUTDIR="$2"
	    shift
	    shift
	    ;;
	*)  # unknown option
	    POSITIONAL+=("$1") # save it in an array for later
	    shift # past argument
	    ;;
    esac
done

# First check if file exists
if [[ -f $FILE && $FILE != '' ]]
then    
    USEFILE=1
elif [[ ! -f $FILE && $FILE != '' ]]
then    
    echo "Filename supplied, but does not exist"
    echo "Exiting..."
    exit
else
    USEFILE=0
fi

if [[ $YRES == '' ]]
then
    YRES=$XRES
fi

# Export the variables required to set GRASS region
# export WD=$HOME/projects/jules_apps
export WD=$(pwd)
export REGION=$REGION
export XMIN=$XMIN
export YMIN=$YMIN
export XMAX=$XMAX
export YMAX=$YMAX
export XRES=$XRES
export YRES=$YRES
export FILE=$FILE
export FILE_LAND_FRAC=$FILE_LAND_FRAC
export OUTDIR=$OUTDIR
export OVERWRITE=$OVERWRITE

if [ ! -d $OUTDIR ]
then
    mkdir $OUTDIR
fi

if [ ! -d $OUTDIR/geotiff ]
then
    mkdir $OUTDIR/geotiff
fi

if [ ! -d $OUTDIR/netcdf ]
then
    mkdir $OUTDIR/netcdf
fi

# ##################################### #
# Create GRASS region
# ##################################### #

# Check whether supplied region is the name of a protected region:
# TODO: could add a string to make it less likely that a similar name would be used
# e.g. globe_0.250000Deg_PROTECTED
echo "globe_0.500000Deg
globe_0.250000Deg
globe_0.125000Deg
globe_0.100000Deg
globe_0.083333Deg
globe_0.062500Deg
globe_0.050000Deg
globe_0.016667Deg
globe_0.010000Deg
globe_0.008333Deg
globe_0.004167Deg
globe_0.002083Deg
globe_0.000833Deg" > /tmp/current_regions.txt

if [ `grep -x $REGION /tmp/current_regions.txt` ]
then
    echo "The supplied region name is the name of a protected region: "
    echo "Please choose another region name"
    exit
fi

# TODO: put this somewhere logical
MAPSET=$HOME/grassdata/latlong/jules

SRCDIR=../src
DATADIR=../data

# Run GRASS script to create user-specified region
chmod u+x $SRCDIR/bash/grass_define_custom_region.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_define_custom_region.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# The above script prints the region; here we check that
# the user is happy to go ahead
while true;
do
    read -p "The specified region is summarised above. Do you wish to proceed? " yn
    case $yn in
	[Yy]* ) break;;
	[Nn]* ) exit;;
	* ) echo "Please answer yes or no.";;
    esac
done

# Export options which define which ancillary maps to write
export ONE_D=$ONE_D
export PDM=$PDM
export TOPMODEL=$TOPMODEL
export ROUTING=$ROUTING
export OVERBANK=$OVERBANK
export NINEPFT=$NINEPFT
export FIVEPFT=$FIVEPFT
export ANTSFORMAT=$ANTSFORMAT
export LAND_FRAC=$LAND_FRAC
export LATLON=$LATLON
export COSBY=$COSBY
export TOMASELLA=$TOMASELLA
export ROSETTA=$ROSETTA

# Also export options which define netCDF dimension names
export GRID_DIM_NAME=$GRID_DIM_NAME
export X_DIM_NAME=$X_DIM_NAME
export Y_DIM_NAME=$Y_DIM_NAME
export TIME_DIM_NAME=$TIME_DIM_NAME
export PFT_DIM_NAME=$PFT_DIM_NAME
export TYPE_DIM_NAME=$TYPE_DIM_NAME
export TILE_DIM_NAME=$TILE_DIM_NAME
export SOIL_DIM_NAME=$SOIL_DIM_NAME
export SNOW_DIM_NAME=$SNOW_DIM_NAME

# Deactivate Anaconda environment
CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda deactivate

# Load input filenames and variable names
set -a
. $DATADIR/maps1k/filenames.txt
set +a

set -a
. $DATADIR/maps1k/varnames.txt
set +a

# Export maps from GRASS database to geotiff image files
chmod u+x $SRCDIR/bash/grass_write_jules_ancil_maps.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_write_jules_ancil_maps.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

set -a
. $OUTDIR/geotiff/filenames.txt
set +a

# Convert geotiffs to netCDFs with Python script
conda activate jules-data
python3 $SRCDIR/python/make-jules-input.py -d $OUTDIR/netcdf
conda deactivate
