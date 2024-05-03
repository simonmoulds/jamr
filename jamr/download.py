#!/usr/bin/env python3

import os
import requests
import urllib.request
import cdsapi
import zipfile

from urllib.error import HTTPError
from urllib.parse import urlparse

from osgeo import gdal, gdalconst

from jamr.constants import (ESA_CCI_LC_YEARS,
                            SOILGRIDS_VARIABLES,
                            SOILGRIDS_HORIZONS)


def download_http_file(url, username, password, local_filename):
    try:
        # # Parse the URL to extract the hostname and path
        # parsed_url = urlparse(url)
        # hostname = parsed_url.hostname
        # path = parsed_url.path

        # # Create a password manager
        # password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        # password_mgr.add_password(None, hostname, username, password)

        # # Create an HTTP Basic Authentication handler
        # auth_handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

        # # Create an opener with the authentication handler
        # opener = urllib.request.build_opener(auth_handler)

        # # Install the opener
        # urllib.request.install_opener(opener)

        # # # Download the file from the URL and save it to the local file
        # # urllib.request.urlretrieve(url, local_filename)

        # # Open the URL and read the content
        # with opener.open(url) as response:
        #     content = response.read()

        # # Write the content to the local file
        # with open(local_filename, 'wb') as file:
        #     file.write(content)

        # Send an HTTP GET request with authentication
        response = requests.get(url, auth=(username, password))

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Write the response content to the local file
            with open(local_filename, 'wb') as file:
                file.write(response.content)

        print(f"File downloaded successfully to '{local_filename}'.")
    except HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    return 0


def download_ftp_file(hostname, remote_filename, local_filename):
    try:
        # Build FTP URL
        ftp_url = f"ftp://{hostname}/{remote_filename}"

        # Download the file
        urllib.request.urlretrieve(ftp_url, local_filename)

        print(f"File '{remote_filename}' downloaded successfully.")
    except Exception as e:
        print(f"Error: {e}")


def unpack_zip(zip_filename, extract_to):
    try:
        # Open the zip file for reading
        with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
            # Extract all contents of the zip file to the specified directory
            zip_ref.extractall(extract_to)

        print(f"Zip file '{zip_filename}' unpacked successfully to '{extract_to}'.")
    except Exception as e:
        print(f"Error: {e}")


def zip_contents(zip_filename):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        # Extract all contents of the zip file to the specified directory
        contents = zip_ref.namelist()
    return contents


def _download_esacci_landcover_ftp(year, dest, overwrite):
    hostname = 'geo10.elie.ucl.ac.be'
    filename = f'ESACCI-LC-L4-LCCS-Map-300m-P1Y-{year}-v2.0.7.tif'
    remote_filename = os.path.join('CCI/LandCover/byYear', filename)
    local_filename = os.path.join(dest, filename)
    if not os.path.exists(local_filename) or overwrite:
        download_ftp_file(hostname, remote_filename, local_filename)

    return 0


def _download_esacci_landcover_cds(year, dest, overwrite):

    if year <= 2015:
        vn = 'v2.0.7'
        basename = f'ESACCI-LC-L4-LCCS-Map-300m-P1Y-{year}-{vn}'
    else:
        vn = 'v2.1.1'
        basename = f'C3S-LC-L4-LCCS-Map-300m-P1Y-{year}-{vn}'

    local_nc_filename = os.path.join(dest, basename + '.nc')
    local_gtiff_filename = os.path.join(dest, basename + '.tif')

    if not os.path.exists(local_nc_filename) or overwrite:
        # For some reason 'cds' is appended to v2.0.7 in CDS
        if vn == 'v2.0.7':
            vn = vn + 'cds'

        tmpdir = os.environ.get('TMPDIR', '/tmp')
        outfile = os.path.join(tmpdir, 'download.zip')
        c = cdsapi.Client()
        c.retrieve(
            'satellite-land-cover',
            {
                'variable': 'all',
                'format': 'zip',
                'year': str(year),
                'version': vn,
            },
            outfile)

        # contents = zip_contents(outfile)
        out = unpack_zip(outfile, dest)
        # local_nc_filename = os.path.join(dest, contents[0])

    if not os.path.exists(local_gtiff_filename) or overwrite:
        opts = gdal.WarpOptions(
            format='GTiff', creationOptions=['COMPRESS=LZW', 'TILED=YES'],
            outputType=gdalconst.GDT_Byte, outputBounds=[-180, -90, 180, 90],
            xRes=0.002777777777778, yRes=0.002777777777778, dstSRS='EPSG:4326'
        )
        gdal.Warp(local_gtiff_filename, 'NETCDF:' + local_nc_filename + ':lccs_class', options=opts)

    return 0


def download_esacci_landcover(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'ESACCI_LC')
    os.makedirs(dest, exist_ok=True)
    for year in ESA_CCI_LC_YEARS:
        if year <= 2015:
            _download_esacci_landcover_ftp(year, dest, overwrite)
        else:
            _download_esacci_landcover_cds(year, dest, overwrite)
    return 0


def download_esacci_waterbodies(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'ESACCI_WB')
    os.makedirs(dest, exist_ok=True)
    hostname = 'geo10.elie.ucl.ac.be'
    filename = 'ESACCI-LC-L4-WB-Ocean-Land-Map-150m-P13Y-2000-v4.0.tif'
    remote_filename = os.path.join('CCI/WaterBodies', filename)
    local_filename = os.path.join(dest, filename)
    download_ftp_file(hostname, remote_filename, local_filename)
    return 0


def download_soilgrids250m(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'SoilGrids_250m')
    os.makedirs(dest, exist_ok=True)
    kwargs = {'format': 'GTiff', 'creationOptions': ["TILED=YES", "COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"]}
    for var in SOILGRIDS_VARIABLES:
        for horizon in SOILGRIDS_HORIZONS:
            remote_filename = f'/vsicurl?max_retry=3&retry_delay=1&list_dir=no&url=https://files.isric.org/soilgrids/latest/data/{var}/{var}_{horizon}_mean.vrt'
            local_filename = os.path.join(dest, f'{var}_{horizon}_mean.tif')
            ds = gdal.Translate(
                local_filename,
                remote_filename,
                callback=gdal.TermProgress_nocb,
                **kwargs
            )

    return 0


def download_soilgrids1000m(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'SoilGrids_1000m')
    os.makedirs(dest, exist_ok=True)
    kwargs = {'format': 'GTiff', 'creationOptions': ["TILED=YES", "COMPRESS=DEFLATE", "PREDICTOR=2", "BIGTIFF=YES"]}
    for var in SOILGRIDS_VARIABLES:
        for horizon in SOILGRIDS_HORIZONS:
            filename = f'{var}_{horizon}_mean_1000.tif'
            http_url = f'https://files.isric.org/soilgrids/latest/data_aggregated/1000m/{var}/{filename}'
            local_filename = os.path.join(dest, filename)
            urllib.request.urlretrieve(http_url, local_filename)


def download_hydrography90m(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'Hydrography90m')
    os.makedirs(dest, exist_ok=True)

    # Get the tile list, which we will use to download the dataset
    tmpdir = os.environ.get('TMPDIR', '/tmp')
    urllib.request.urlretrieve(
        "https://gitlab.com/selvaje74/hydrography.org/-/raw/main/images/hydrography90m/tiles20d/tile_list.txt",
        os.path.join(tmpdir, "tile_list.txt")
    )
    with open(os.path.join(tmpdir, "tile_list.txt"), "r") as f:
        for tile in f:
            tile = tile.strip()
            filename = f'cti_{tile}.tif'
            http_url = f'https://public.igb-berlin.de/index.php/s/agciopgzXjWswF4/download?path=%2Fflow.index%2Fcti_tiles20d&files={filename}'
            local_filename = os.path.join(dest, filename)
            urllib.request.urlretrieve(http_url, local_filename)


MERIT_DEM_USERNAME = 'globaldem'
MERIT_DEM_PASSWORD = 'preciseelevation'
MERIT_HYDRO_USERNAME = 'hydrography'
MERIT_HYDRO_PASSWORD = 'rivernetwork'
MERIT_HYDRO_VARS = ['dir', 'elv', 'upa', 'upg', 'wth']
MERIT_LATITUDES = ['n' + str(n).zfill(2) for n in range(60, -1, -30)] + ['s' + str(s).zfill(2) for s in range(30, 90, 30)]
MERIT_LONGITUDES = ['w' + str(w).zfill(3) for w in range(180, 0, -30)] + ['e' + str(e).zfill(3) for e in range(0, 180, 30)]
def download_merit_dem(config, overwrite=False):
    dest = os.path.join(config['main']['data_directory'], 'MERIT', 'dem')
    os.makedirs(dest, exist_ok=True)
    for lat in MERIT_LATITUDES:
        for lon in MERIT_LONGITUDES:
            filename = f'dem_tif_{lat}{lon}.tar'
            http_url = f'http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_DEM/distribute/v1.0.2/{filename}'
            local_filename = os.path.join(dest, filename)
            download_http_file(http_url, MERIT_DEM_USERNAME, MERIT_DEM_PASSWORD, local_filename)


def download_merit_hydro(config, overwrite=False):
    dest_root = os.path.join(config['main']['data_directory'], 'MERIT', 'hydro')
    for var in MERIT_HYDRO_VARS:
        for lat in MERIT_LATITUDES:
            for lon in MERIT_LONGITUDES:
                dest = os.path.join(dest_root, var)
                os.makedirs(dest, exist_ok=True)
                filename = f'{var}_{lat}{lon}.tar'
                http_url = f'http://hydro.iis.u-tokyo.ac.jp/~yamadai/MERIT_Hydro/distribute/v1.0/{filename}'
                local_filename = os.path.join(dest, filename)
                download_http_file(http_url, MERIT_HYDRO_USERNAME, MERIT_HYDRO_PASSWORD, local_filename)

