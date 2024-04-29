#!/bin/bash

# ========================================================= #
# Write Help
# ========================================================= #

Help()
{
    echo "Script to create JULES ancillary maps @ 1km resolution in Geotiff format."
    echo
    echo "Syntax: create-app.sh [-h|o|d]"
    echo "options:"
    echo "-h | --help       Print this help message."
    echo "-o | --overwrite  Overwrite existing database (WARNING: could take a long time)."
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

# Set default
DESTDIR=$(pwd)/../../data/maps1k
OVERWRITE=

while [[ $# -gt 0 ]]
do
    key="$1"
    case $key in
	-h|--help)
	    Help
	    exit
	    ;;
	-o|--overwrite)
	    OVERWRITE='--overwrite'
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

export WD=$(pwd)
export SRCDIR=$(pwd)/../src
export AUXDIR=$(pwd)/../data/aux
export OVERWRITE=$OVERWRITE
export OUTDIR=$DESTDIR
export REGION=globe_0.008333Deg

# TODO: make region an option

if [[ ! -d $OUTDIR ]]
then
    mkdir $OUTDIR
fi

for SUBDIR in jules_frac jules_land_frac jules_soil_props jules_top jules_pdm jules_rivers_props jules_overbank_props
do
    if [[ ! -d $OUTDIR/$SUBDIR ]]
    then
	mkdir $OUTDIR/$SUBDIR
    fi
done

# Deactivate Anaconda environment
CONDA_BASE=$(conda info --base)
source $CONDA_BASE/etc/profile.d/conda.sh
conda deactivate

# Define filenames or base names for output

# Naming convention is as follows:
# jamr_[DATA SOURCE]_[VARIABLE NAME]_[EXTENT]_[RESOLUTION].tif

echo "SLOPE_VARNM=merit_dem_slope
FEXP_VARNM=merit_dem_fexp
MERIT_TI_MEAN_VARNM=merit_dem_ti_mean
HYDRO_TI_MEAN_VARNM=hydrosheds_ti_mean
MERIT_TI_SIG_VARNM=merit_dem_ti_sig
HYDRO_TI_SIG_VARNM=hydrosheds_ti_sig
MERIT_DIRECTION_VARNM=camaflood_direction
MERIT_AREA_VARNM=camaflood_area
HYDRO_DIRECTION_VARNM=hydrosheds_direction
HYDRO_AREA_VARNM=hydrosheds_area
MERIT_LAND_FRAC_VARNM=camaflood_land_frac
HYDRO_LAND_FRAC_VARNM=hydrosheds_land_frac
ESA_LAND_FRAC_VARNM=esa_cci_lc_land_frac
FRAC_VARNM=esa_cci_lc_frac
SURF_HGT_VARNM=merit_dem_surf_hgt
WEIGHTED_ELEV_VARNM=esa_cci_lc_weighted_elev
SOIL_VARNM=soilgrids
ALBSOIL_VARNM=houldcroft_albsoil
LOGN_VARNM=merit_dem_logn
LOGN_MEAN_VARNM=merit_dem_logn_mean
LOGN_STDEV_VARNM=merit_dem_logn_stdev" > ${WD}/varnames.txt

cp ${WD}/varnames.txt ${DESTDIR}

set -a
. ${WD}/varnames.txt
set +a

echo "SLOPE_FN=${OUTDIR}/jules_pdm/jamr_${SLOPE_VARNM}_${REGION}.tif
FEXP_FN=${OUTDIR}/jules_top/jamr_${FEXP_VARNM}_globe_0.004167Deg.tif
MERIT_TI_MEAN_FN=${OUTDIR}/jules_top/jamr_${MERIT_TI_MEAN_VARNM}_globe_0.002083Deg.tif
HYDRO_TI_MEAN_FN=${OUTDIR}/jules_top/jamr_${HYDRO_TI_MEAN_VARNM}_globe_0.004167Deg.tif
MERIT_DIRECTION_BASENM=${OUTDIR}/jules_rivers_props/jamr_${MERIT_DIRECTION_VARNM}
MERIT_AREA_BASENM=${OUTDIR}/jules_rivers_props/jamr_${MERIT_AREA_VARNM}
HYDRO_DIRECTION_BASENM=${OUTDIR}/jules_rivers_props/jamr_${HYDRO_DIRECTION_VARNM}
HYDRO_AREA_BASENM=${OUTDIR}/jules_rivers_props/jamr_${HYDRO_AREA_VARNM}
MERIT_LAND_FRAC_BASENM=${OUTDIR}/jules_land_frac/jamr_${MERIT_LAND_FRAC_VARNM}
HYDRO_LAND_FRAC_FN=${OUTDIR}/jules_land_frac/jamr_${HYDRO_LAND_FRAC_VARNM}_globe_0.008333.tif
ESA_LAND_FRAC_FN=${OUTDIR}/jules_land_frac/jamr_${ESA_LAND_FRAC_VARNM}_${REGION}.tif
FRAC_BASENM=${OUTDIR}/jules_frac/jamr_${FRAC_VARNM}
SURF_HGT_FN=${OUTDIR}/jules_frac/jamr_${SURF_HGT_VARNM}_${REGION}.tif
WEIGHTED_ELEV_BASENM=${OUTDIR}/jules_frac/jamr_${WEIGHTED_ELEV_VARNM}
SOIL_BASENM=${OUTDIR}/jules_soil_props/jamr_${SOIL_VARNM}
ALBSOIL_FN=${OUTDIR}/jules_soil_props/jamr_${ALBSOIL_VARNM}_${REGION}.tif
LOGN_DIR=${OUTDIR}/jules_overbank_props" > ${WD}/filenames.txt

cp ${WD}/filenames.txt ${DESTDIR}

set -a
. ${WD}/filenames.txt
set +a

MAPSET=$HOME/grassdata/latlong/jules

# Restate grass regions
chmod u+x $SRCDIR/bash/grass_define_regions.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_define_regions.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

# Export maps from GRASS database to geotiff image files
chmod u+x $SRCDIR/bash/grass_write_jules_1km_ancil_maps.sh
export GRASS_BATCH_JOB=$SRCDIR/bash/grass_write_jules_1km_ancil_maps.sh
grass76 $MAPSET
unset GRASS_BATCH_JOB

