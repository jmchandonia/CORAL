# TSV files:

The files in this directory were made from the NetCDF4 files using the
"netcdf_to_tsv.py" code.  Each Brick got split into two TSV files: one
containing the data, and one containing the metadata.  This is because
for large datasets, putting all the metadata about each variable into
the rows and columns is very redundant, and creates a huge TSV file.
