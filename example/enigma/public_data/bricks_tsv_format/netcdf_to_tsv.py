#!/usr/bin/python3

import xarray as xr
import pandas as pd
import sys

def netcdf_to_tsv(netcdf_file, attrs_file, data_file):
    # Open the NetCDF file
    ds = xr.open_dataset(netcdf_file)

    # Convert the data to a pandas DataFrame
    data_df = ds.to_dataframe()

    # Convert the attributes to a pandas DataFrame
    attrs_df = pd.DataFrame(ds.attrs, index=[0])

    # Add variable attributes to the attrs_df
    for var_name in ds.data_vars:
        var = ds[var_name]
        var_attrs = pd.DataFrame(var.attrs, index=[0])
        var_attrs.columns = [f'{var_name}_{col}' for col in var_attrs.columns]
        attrs_df = pd.concat([attrs_df, var_attrs], axis=1)

    # Write the DataFrames to TSV files
    attrs_df.to_csv(attrs_file, sep='\t', index=False)
    data_df.to_csv(data_file, sep='\t', index=False)

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: netcdf_to_tsv.py <netcdf_file> <attrs_file> <data_file>")
        sys.exit(1)

    netcdf_file = sys.argv[1]
    attrs_file = sys.argv[2]
    data_file = sys.argv[3]

    netcdf_to_tsv(netcdf_file, attrs_file, data_file)
