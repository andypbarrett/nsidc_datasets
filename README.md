# nsidc-datasets

This repo contains tools for working with datasets from NSIDC, including NSIDC-DAAC and NOAA@NSIDC.

Some NSIDC datasets do not lend themselves to modern workflows using the current suite of Python tools, such as `xarray`, `pandas`, `geopandas`, etc.  This repo contains preprocessors for this data to make datasets more analysis ready, along with ancilliary data, and plotting routines.

The motivation for the routines contained here is to facilitate efficient modern geospatial analysis workflows with a minimum of intervention by a human.  For example, we should be able to do something like this...

```
import earthaccess
import xarray as xr


auth = earthaccess.login()

# Get NSIDC Passive Microwave Sea Ice Concentration for
# the northern hemisphere
result = earthaccess.search_data(
    short_name = "NSIDC-0051",
    temporal = (start_date, end_date),
    bounding_box = (-180., 60., 180., 90.),
    cloud_hosted=True,
)

# Download files
files = earthaccess.download(result, local_path="../data")

# Load a time series of daily data as a dataset 
ds = xr.open_mfdataset(files, decode_coords="all", chunks={}, 
                       parallel=True, 
                       data_vars="minimal", coords="minimal",
                       compat="override", engine="h5netcdf")

# Calculate dailt northern hemisphere sea ice extent
sic_extent = (ds.sic * ds.cell_area).sum(dims=["x",y"])
```

However, this is not possible because sea ice concentration is stored in different variables in different files, depending on the sensor used to produce the data; cell_area is not included in the data files, it is an ancilliary file that has to be downloaded; and data variables contain a mix of measuremet values (sea ice concentration) and flag values to indicate land, coastline and missing values at the pole (the pole-hole).

Each of these idiosynchrases needs to be identified by a user and then handled with some ad-hoc code.


## Preprocessors

Preprocessor functions are intended to be passed to `xarray.open_mfdataset` via the `preprocessor` keyword argument.  These modify individual files so they can be loaded as `xarray.Dataset` objects as more Analysis Ready Data.

Currently preprocessors are available for the following datasets:

- NSIDC-0051
- [NOAA@NSIDC G02202 NOAA/NSIDC Climate Data Record of Passive Microwave Sea Ice Concentration, Version 4](https://nsidc.org/data/g02202/versions/4)

## Ancilliary Files

PS25 km cell-area

