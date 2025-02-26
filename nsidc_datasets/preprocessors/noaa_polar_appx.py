"""Preprocessor for NOAA Polar APPx"""
import re

import numpy as np

import xarray as xr
import rioxarray

from nsidc_projections.grid import AVHRR_EASEGridNorth25km

def add_spatial_coords(ds):
    """Add spatial coordinates to a dataset

    Arguments
    ---------
    ds : xarray.Dataset containing a NOAA Polar APPx granule

    Returns
    -------
    a modified xarray.DataSet

    The following modifications are made to the file to improve compliance
    with CF-Conventions and also dataset interoperability.

    1. Reset longitude and latitude coordinates to data variables
    2. Rename spatial dimensions to x and y
    3. Adds x and y coordinates in AVHRR EASE Grid 25 km
    4. Adds required attributes"""
    
    # Move longitude and latitude to data_vars
    ds = ds.reset_coords(['longitude', 'latitude'])  # remove lat and lon as coordinates

    # Rename horizontal dimensions - the original dimensions are
    # incorrectly named; columns are up-down, and rows left-right.
    # Normally x would be the column dimension and y the row dimensions.
    # The mapping used below is different from that to correct the mistake.
    ds = ds.rename({'columns': 'y', 'rows': 'x'})  # rename to x and y - these will be set as coordinates

    # Generate projected x and y coordinates
    x, y = AVHRR_EASEGridNorth25km.get_coordinates()
    x = xr.DataArray(x, coords=[x], dims=['x'], name='x', 
                     attrs={'units': 'm', 
                            'long_name': 'x coordinate of projection', 
                            'standard_name': 'projection_x_coordinate',
                            'grid_mapping': 'lambert_azimuthal_equal_area',
                            'axis': 'X'})
    y = xr.DataArray(y, coords=[y], dims=['y'], name='y', 
                     attrs={'units': 'm', 
                            'long_name': 'y coordinate of projection', 
                            'standard_name': 'projection_y_coordinate',
                            'grid_mapping': 'lambert_azimuthal_equal_area',
                            'axis': 'Y'})

    # Assign x and y coordinates
    ds = ds.assign_coords({'x': x, 'y': y})

    # Add WKT to crs definition
    ds.crs.attrs['crs_wkt'] = AVHRR_EASEGridNorth25km.crs.to_cf()['crs_wkt']

    return ds


def get_time_from_id(ds):
    """Returns hour and minute from the id global attribute"""
    p = re.compile(r"hem_(\d{2})(\d{2})_d")
    hour, minute = p.search(ds.attrs["id"]).groups()
    return int(hour), int(minute)


def fix_time_coords(ds):
    """Fixes issues with time coordinates and returns the correct datetime coordinate value
    
    1. Rename time dimensions
    2. Adjust time coordinate value for observation time and 1 day offset introduced by
       by using day of year. 

    The functions fixes to issues with the time coordinates as well as changing the name of them
    the time dimension from Time to time to match community convention.

    Stored time coordinate values are days of year number rather than following CF-Convention as
    days since.  The time units are `days since YYYY-01-01 00:00:00`.  This results in decoded
    time being one day after file name timestamp.  To fix this undecoded time coordinate
    values have 1 subtracted from them.

    In addition, time coordinates are all 00:00:00 and do not reflect the observation time.  This causes
    the 0400 observation being overwritten by the 1400 observation when a time series of observations are
    concatenated.  To fix this, the observation hour and minute (all minutes are 00) are extracted
    from id global attribute.  These are added to the time coordinate.
    """
    ds = ds.swap_dims({'Time': 'time'})  # rename Time dimension

    # Fix the time coordinate -
    hour, minute = get_time_from_id(ds)
    ds['time'] = (ds['time'] + np.timedelta64(hour, "h") +
                  np.timedelta64(minute, "m") - np.timedelta64(1, "D"))
    return xr.decode_cf(ds)


def fix_dimensions_order(ds):
    """Transposes dimensions in accordance with CF-Convention
    recommendation"""
    return ds.transpose("time", "y", "x")    


def drop_vars(ds, data_vars):
    """Drops variables not in data_vars"""
    these_vars = [var for var in datasets[0].data_vars if var not in data_vars]
    return ds.drop_vars(these_vars)


def preprocess(ds, data_vars=None):
    """Wrapper for pre-processing functions"""
    ds = add_spatial_coords(ds)
    ds = fix_time_coords(ds)
    ds = fix_dimensions_order(ds)
    if data_vars:
        ds = drop_vars(ds, data_vars)
    return ds
