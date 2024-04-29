#!/bin/bash

# ========================================================= #
# Write Help
# ========================================================= #

Help()
{
    # Display help
    echo "Main script to create JULES input data."
    echo
    echo "Syntax: populate-grass-db.sh [-h|o]"
    echo "options:"
    echo "-h | --help       Print this help message."
    echo "-o | --overwrite  Overwrite existing database (WARNING: could take a long time)."
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

POSITIONAL=()
while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
	-h|--help)
	    Help
	    shift
	    ;;
	-o|--overwrite)
	    OVERWRITE='--overwrite'
	    shift
	    ;;
	*)  # unknown option
	    POSITIONAL+=("$1") # save it in an array for later
	    shift # past argument
	    ;;
    esac
done

# ========================================================= #
# Declare global variables
# ========================================================= #

export WD=$(pwd)
export SRCDIR=$(pwd)/../src
export AUXDIR=$(pwd)/../data/aux
export TMPDIR=/tmp
export OUTDIR=$(pwd)/../data/
export DATADIR=$(pwd)/../data/
export HYDRODIR=/mnt/scratch/scratch/data/HydroSHEDS
export MERITDIR=/mnt/scratch/scratch/data/MERIT/dem
export GWBMDIR=/mnt/scratch/scratch/data/MERIT/g1wbm
export OSMDIR=/mnt/scratch/scratch/data/MERIT/OSM_water_tif
export GSWODIR=/mnt/scratch/scratch/data/MERIT/GSWO
export CAMADIR=/mnt/scratch/scratch/data/MERIT/ToECMWF
export ESACCIDIR=/mnt/scratch/scratch/data/ESA_CCI_LC
export GEOMORPHDIR=/mnt/scratch/scratch/data/geomorpho90m
export MARTHEWDIR=/mnt/scratch/scratch/data/marthews_topographic_index/
RES=1km
export SOILGRIDDIR=/mnt/scratch/scratch/data/SoilGrids${RES}
export HWSDDIR=/mnt/scratch/scratch/data/hwsd
export OVERWRITE=$OVERWRITE

# ========================================================= #
# Make output directories
# ========================================================= #

if [ ! -d $AUXDIR ]
then
    mkdir $AUXDIR
fi

for DIR in hydro dem soil land_frac frac 
do
    if [ ! -d $AUXDIR/$DIR ]
    then
	mkdir $AUXDIR/$DIR
    fi
done

# ========================================================= #
# Set-up GRASS
# ========================================================= #

# Create location if it doesn't exist
# N.B. this assumes that GISDBASE is in $HOME/grassdata
LOCATION=$HOME/grassdata/latlong
if [ ! -d $LOCATION ]
then
    grass -c EPSG:4326 -e $LOCATION
fi

MAPSET=$HOME/grassdata/latlong/jules
if [ ! -d $MAPSET ]
then    
   grass -c -e $MAPSET
fi

# Deactivate Anaconda environment (this can mess up GRASS)
# See - https://github.com/conda/conda/issues/7980#issuecomment-441358406
# https://stackoverflow.com/a/45817972
conda --version > /dev/null 2>&1
if [ $? == 0 ]
then
    ANACONDA_INSTALLED=1
else
    ANACONDA_INSTALLED=0
fi

if [ $ANACONDA_INSTALLED == 1 ]
then    
    CONDA_BASE=$(conda info --base)
    source $CONDA_BASE/etc/profile.d/conda.sh
    conda deactivate
    # conda activate base
fi

# ========================================================= #
# Run GRASS scripts to populate GRASS DB and write aux maps
# ==========================================================#

# Define some global regions which are used during data processing
chmod u+x $SRCDIR/bash/grass_define_regions.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_define_regions.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# This script merges MERIT DEM files into a single global
# elevation file at 0.008333 and 0.004167 degree resolution.
# This is used to estimate the surface height of cover fractions,
# and calculate slope for the PDM ancillary file.
chmod u+x $SRCDIR/bash/grass_make_elevation.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_elevation.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# JULES_RIVERS_PROPS : area, direction
# TODO: need to handle the case where river props do not
# have the same grid as model
chmod u+x $SRCDIR/bash/grass_make_jules_routing_props.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_routing_props.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# JULES_LAND_FRAC
chmod u+x $SRCDIR/bash/grass_make_jules_land_frac.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_land_frac.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# JULES_TOP, JULES_PDM
chmod u+x $SRCDIR/bash/grass_make_jules_topography_props.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_topography_props.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# JULES_FRAC
chmod u+x $SRCDIR/bash/grass_make_jules_frac.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_frac.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# JULES_SOIL_PROPS
chmod u+x $SRCDIR/bash/grass_make_jules_soil_props.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_soil_props.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# # JULES_OVERBANK_PROPS
# # N.B. input maps to this script are computed in
# # data-raw/bin/make-merit-con-dem.sh
# chmod u+x $SRCDIR/bash/grass_make_jules_overbank_props.sh
# export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_jules_overbank_props.sh
# grass76 $MAPSET
# unset GRASS_BATCH_JOB
