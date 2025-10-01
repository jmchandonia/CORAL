This directory exports data from a CORAL instance to a data lakehouse
running minio and spark.

Requires uv to install packages.

To download TSVs of all static data types, do:
```
mkdir exported_tsvs
uv run download_typedef_tsvs.py --typedef [MY_TYPEDEF.JSON] --out_dir exported_tsvs
```
