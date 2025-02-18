"""Code to preprocess NSIDC passive microwave datasets"""
from typing import Union, List, Dict

import xarray as xr
import numpy as np

def get_icecon_variable_name(ds: xr.Dataset) -> str:
    """Returns name of ICECON variable

    Parameters
    ----------
    ds : xarray dataset

    Returns
    -------
    name f ice concentration variable.  Raises KeyError is no match or more than one match
    """
    icecon_var = [v for v in ds.data_vars if "ICECON" in v]
    nvars = len(icecon_var)
    if nvars == 1:
        return icecon_var[0]
    elif nvars > 1:
        raise KeyError(f"More than one ICECON variable found: {icecon_var}")
    else:
        raise KeyError("No ICECON variable found")


def get_actual_valid_range(da: xr.DataArray):
    """Returns valid range in scaled units
    
    Parameters
    ----------
    da : xarray.DataArray
    
    Returns
    -------
    valid range in scaled units as tuple
    """
    if 'valid_range' not in da.attrs:
        raise KeyError(f"No `valid_range` attribute for {da.name}")
    valid_range = da.attrs['valid_range']

    scale_factor = da.encoding.get("scale_factor", 1.)
    add_offset = da.encoding.get("add_offset", 0.)
    valid_range = valid_range * scale_factor + add_offset
    
    return valid_range


def extract_mask(da: xr.Dataset):
    """Extracts mask values from a data variable and returns a mask
    DataArray.

    Arguments
    ---------
    da : data variable with mask flags embedded

    Returns
    -------
    mask variable
    """

    valid_min, valid_max = get_actual_valid_range(da)

    scale_factor = da.encoding.get("scale_factor", 1.)
    add_offset = da.encoding.get("add_offset", 0.)
    
    mask = da.where((da < valid_min) | (da > valid_max), 0)
    mask = (mask - add_offset) / scale_factor
    mask = mask.astype(int)
    
    # Add attributes to mask
    mask.attrs = {
        "long_name": "mask",
        "standard_name": "mask",
        "units": None,
        "flag_values": np.insert(da.attrs.get('flag_values', []), 0, [0]),
        "flag_meanings": " ".join(["valid", da.attrs.get('flag_meanings', '')]),
        }

    mask.encoding = da.encoding
    
    return mask.squeeze()


def update_sic(sic: xr.DataArray, new_name: str="sic") -> xr.DataArray:
    """Extract and recodes sic field

    Arguments
    ---------
    sic : xr.DataArray containing sea ice concentration
    new_name : new name for sic DataArray.  Default is sic

    Returns
    -------
    Returns a new DataArray with only sea ice concentration values

    Steps:
    1. SIC values outside of valid_min and valid_max are set to
       _FillValue
    2. legacy_binary_header, flag_values, flag_meanings and comment
       attributes are deleted.
    3. valid_range attribute is set to actual valid range
    4. DataArray is renamed to new_name.  Default is "sic"
    """
    valid_min, valid_max = get_actual_valid_range(sic)
    encoding = sic.encoding
    
    sic = sic.where((sic >= valid_min) & (sic <= valid_max))

    for attname in ["legacy_binary_header", "flag_values", 
                    "flag_meanings", "comment"]:
        try:
            del sic.attrs[attname]
        except Exception as err:
            print(f"Cound not find {attname}, skipping deletion")
    sic.attrs["valid_range"] = [valid_min, valid_max]
    
    sic = sic.rename(new_name)

    sic.encoding = encoding
    
    return sic


def create_sensor(da):
    """Returns a DataArray object containing sensor id"""
    sensor_id = da.name
    return sensor_id

    
def preprocess(ds: xr.Dataset):
    """Preprocess NSIDC-0051 for building larger dataset

    Arguments
    ---------
    ds : xarray dataset

    Return
    ------
    Returns a preprocessed xarray.Dataset

    Preprocessing steps to make dataset analysis ready

    1. Extracts mask values from a data variable and returns
       a mask dataset with attributes.  
    2. Remove mask flags and update data variables
    3. Updates name of sea ice concentration variable
    4. Updates and copies encoding
    """

    icecon_var = get_icecon_variable_name(ds)
    sensor_id = icecon_var.split('_')[0]  # Get the sensor name from the variable

    icecon_encoding = ds[icecon_var].encoding

    ds["mask"] = extract_mask(ds[icecon_var])
    ds["sic"] = update_sic(ds[icecon_var])
    ds["sensor"] = create_sensor(ds[icecon_var])
    
    # Drop original *_ICECON variable
    ds.drop_var(icecon_var)
    
    return ds


