def preprocess(
        ds: xr.Dataset,
        keep_vars: List[str]=None,
        rename: Dict={"cdr_seaice_conc": "sic"},
        ) -> xr.Dataset:
    """Preprocessor for NOAA/NSIDC CDR of Passive Microwave
    Sea Ice Concentration (G02202).  Returns a preprocessed
    xarray.Dataset to include in an Analysis Ready Dataset.

    Arguments
    ---------
    ds : xarray.Dataset containing a single CDR granule
    keep_vars : list of strings containing data variables to keep
        NotImplemented
    rename : dict of old_name: new_name key-values pairs.  By default
        cdr_seaice_conc is renamed to sic
        NotImplemented

    Returns
    -------
    An Analysis Ready xarray.Dataset with sea ice concentration and mask variables

    1. Rename time, x and y dimensions to conform to CF-Conventions
    2. Extract mask flags to separate DataArray
    3. Remove mask flag values from SIC variable
    4. Drop unrequired data variables: only data variables listed in data_vars are
       retained.  By default this is just cdr_seaice_conc
    """

    data_vars = list(ds.data_vars.keys())
    
    icecon_var = "cdr_seaice_conc"
    
    # Rename dimensions to fit CF-Conventions best practices
    ds = ds.rename_vars({"xgrid": "x", "ygrid": "y"})
    ds = ds.swap_dims({"tdim": "time"})

    ds["mask"] = extract_mask(ds[icecon_var])
    ds["sic"] = update_nsidc0051_sic(ds[icecon_var])

    # Drop data variables unless listed in data_vars
    ds = ds.drop_vars(data_vars)

    return ds
