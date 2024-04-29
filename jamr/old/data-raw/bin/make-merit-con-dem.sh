#!/bin/bash

# ========================================================= #
# Write Help
# ========================================================= #

Help()
{
    # Display help
    echo "Main script to create conditioned DEM."
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
export MERITDIR=$HOME/data/MERIT/dem
export GWBMDIR=$HOME/data/MERIT/g1wbm
export OSMDIR=$HOME/data/MERIT/OSM_water_tif
export GSWODIR=$HOME/data/MERIT/GSWO
export OVERWRITE=$OVERWRITE

# ========================================================= #
# Make output directories
# ========================================================= #

if [ ! -d $AUXDIR ]
then
    mkdir $AUXDIR
fi

if [ ! -d $AUXDIR/dem ]
then
    mkdir $AUXDIR/dem
fi

# ========================================================= #
# Set-up GRASS
# ========================================================= #

# Create separate mapset to allow concurrent use
MAPSET=$HOME/grassdata/latlong/dem
if [ ! -d $MAPSET ]
then    
   grass -e -c $MAPSET
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
fi

# This script is used to construct a water likelihood
# surface in order to build a conditioned DEM which 
# takes account of river bathmetry.
# WARNING 1: this is experimental
# WARNING 2: this takes ages to run (> 5 days)
chmod u+x $SRCDIR/bash/grass_make_water_likelihood_surface.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_make_water_likelihood_surface.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB
