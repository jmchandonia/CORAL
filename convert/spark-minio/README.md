This directory exports data from a CORAL instance to a data lakehouse
running minio and spark.

Requires uv to install packages.

To download TSVs of all static data types, do:
```
mkdir exported_tsvs
uv run download_typedef_tsvs.py --typedef [MY_TYPEDEF.JSON] --out_dir exported_tsvs
```

To make code to transfer data to the lakehouse and make tables,, do:
```
uv run to_spark.py --typedef ~/src/CORAL/example/enigma/setup/typedef.json --obo_dir /home/coral/prod/data_import/ontologies/ --tsv_dir exported_tsvs --output make_tables.py --shell_output copy_data.sh
```

To copy the data to the lakehouse using the minio client mc (aka mcli), you can now run:
```
sh copy_data.sh
```

Then in a Jupyter notebook on the data lakehouse, paste in and run the
contents of these files to generate all the necessary tables:
```
update_coral_ontologies.py
make_tables.py
```
