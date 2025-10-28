"""make_ddt_tables.py

Load Dynamic Data Type (DDT) tables into Spark Delta Lake.

This script loads three types of tables:
1. ddt_ndarray - metadata about n-dimensional arrays
2. sys_ddt_typedef - type definitions for DDT fields
3. ddt_brick* tables - individual brick data tables with their own schemas

The script follows the same conventions as make_tables.py.

Run the script in a notebook as follows::

    spark = get_spark_session()               # <-- defined elsewhere
    db_name = "jmc_coral"
    spark.sql(f"USE {db_name}")
    generate_ddt_tables(spark, db_name)
"""

import json
import logging
import os
import re
import tempfile
import importlib.util
import sys
from typing import Any, Dict, List, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    BooleanType,
    ArrayType,
    DataType,
)

# ------------------------------------------------------------------
# Helper: parse an ``s3a://`` URI into bucket + prefix
# ------------------------------------------------------------------
def _parse_s3a_uri(s3a_uri: str) -> Tuple[str, str]:
    """
    Split an ``s3a://`` URI into its bucket component and the *remaining*
    path (prefix).  The returned prefix does **not** include a leading
    slash and always ends with a slash (unless it is empty).

    Example
    -------
    >>> _parse_s3a_uri("s3a://cdm‑lake/users-general-warehouse/jmc")
    ('cdm‑lake', 'users-general-warehouse/jmc/')
    """
    if not s3a_uri.startswith("s3a://"):
        raise ValueError(f"Unexpected S3A URI: {s3a_uri}")

    # Strip the scheme
    path = s3a_uri[len("s3a://") :]  # e.g. "cdm-lake/users-general-warehouse/jmc"

    # Split on the first slash – everything before it is the bucket name
    parts = path.split("/", 1)
    bucket = parts[0]

    # The rest (if any) is the prefix; normalise it to end with a slash
    if len(parts) == 2:
        prefix = parts[1].rstrip("/") + "/"
    else:
        prefix = ""

    return bucket, prefix


# ------------------------------------------------------------------
# Helper: create a boto3 client that works with MinIO (path‑style)
# ------------------------------------------------------------------
def _get_boto3_s3_client(credentials, endpoint: str):
    """
    Return a boto3 S3 client configured for MinIO.

    Parameters
    ----------
    credentials : object
        Must expose ``access_key`` and ``secret_key`` attributes.
    endpoint : str
        Full URL of the MinIO service, e.g. ``http://10.58.1.104:9002``.
    """
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        # MinIO expects bucket name in the *path* (not as a sub‑domain)
        config=Config(s3={"addressing_style": "path"}),
    )


# ------------------------------------------------------------------
# Helper: list objects in a bucket/prefix (boto3 version)
# ------------------------------------------------------------------
def list_objects_boto3(
    bucket: str,
    prefix: str,
    credentials,
    endpoint: str,
    region: str = "us-east-1",
) -> List[str]:
    """
    Return a flat list of object keys under ``bucket/prefix`` on a MinIO
    server using boto3.

    The function forces *path‑style* addressing (required for MinIO).
    """
    # Normalise prefix – ensure a trailing slash if non‑empty
    if prefix and not prefix.endswith("/"):
        prefix = f"{prefix}/"

    client = _get_boto3_s3_client(credentials, endpoint)

    paginator = client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    keys: List[str] = []
    for page in page_iterator:
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


# ------------------------------------------------------------------
# Helper: download a file from S3 to a temporary local file
# ------------------------------------------------------------------
def _download_to_temp(s3_client, bucket: str, key: str, suffix: str = ".py") -> str:
    """
    Download a file from MinIO to a temporary local file and
    return the temporary file path.
    """
    resp = s3_client.get_object(Bucket=bucket, Key=key)
    body = resp["Body"].read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode='wb')
    tmp.write(body)
    tmp.close()
    return tmp.name


# ------------------------------------------------------------------
# Helper: Create a nullable version of a schema
# ------------------------------------------------------------------
def _make_schema_nullable(schema: StructType) -> StructType:
    """
    Create a copy of the schema with all fields marked as nullable.
    This is used when loading TSV data to handle missing or incomplete data.
    """
    nullable_fields = []
    for field in schema.fields:
        nullable_fields.append(
            StructField(field.name, field.dataType, nullable=True, metadata=field.metadata)
        )
    return StructType(nullable_fields)


# ------------------------------------------------------------------
# Helper: Cast DataFrame columns to match schema types
# ------------------------------------------------------------------
def _cast_columns_to_schema(df, schema: StructType):
    """
    Cast DataFrame columns to match the types defined in the schema.
    This is needed because TSV files are read with all string columns.
    """
    for field in schema.fields:
        if field.name in df.columns:
            df = df.withColumn(field.name, F.col(field.name).cast(field.dataType))
    return df


# ------------------------------------------------------------------
# Helper: Apply schema with metadata to a DataFrame
# ------------------------------------------------------------------
def _apply_schema_with_metadata(spark, df, schema: StructType, make_nullable: bool = False):
    """
    Apply a schema with metadata (including comments) to a DataFrame.
    This ensures that column comments are preserved when writing to Delta tables.
    """
    target_schema = _make_schema_nullable(schema) if make_nullable else schema
    
    if df.rdd.isEmpty():
        return spark.createDataFrame([], target_schema)
    
    df = _cast_columns_to_schema(df, target_schema)
    return spark.createDataFrame(df.rdd, target_schema)


# ------------------------------------------------------------------
# Helper: convert a stringified array back to an actual ArrayType column
# ------------------------------------------------------------------
def _convert_array_column(col_name: str) -> Any:
    """
    Turn a TSV string like ``[a,b,c]`` into an ``ArrayType(String)``.
    Empty or null values become an empty array.
    """
    cleaned = F.regexp_replace(F.col(col_name), r"^\[|\]$", "")
    splitted = F.split(cleaned, r",\s*")
    without_empty = F.array_remove(splitted, "")
    return F.when(F.col(col_name).isNull() | (F.col(col_name) == ""), F.array()).otherwise(without_empty)


# ------------------------------------------------------------------
# Build schema for ddt_ndarray table
# ------------------------------------------------------------------
def build_ddt_ndarray_schema() -> StructType:
    """Build the schema for the ddt_ndarray table."""
    return StructType([
        StructField(
            "ddt_ndarray_id",
            StringType(),
            nullable=False,
            metadata={"comment": json.dumps({
                "description": "Primary key for DDT N-dimensional array",
                "type": "primary_key"
            })}
        ),
        StructField(
            "ddt_ndarray_name",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Name of the DDT N-dimensional array",
                "type": "unique_key"
            })}
        ),
        StructField(
            "ddt_ndarray_description",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Description of the DDT N-dimensional array"
            })}
        ),
        StructField(
            "ddt_ndarray_metadata",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Metadata for the DDT N-dimensional array"
            })}
        ),
        StructField(
            "ddt_ndarray_type_sys_oterm_id",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Array type ontology term CURIE",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "ddt_ndarray_type_sys_oterm_name",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Array type ontology term name"
            })}
        ),
        StructField(
            "ddt_ndarray_shape",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Shape of the N-dimensional array"
            })}
        ),
        StructField(
            "ddt_ndarray_dimension_types_sys_oterm_id",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension types ontology term CURIEs",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "ddt_ndarray_dimension_types_sys_oterm_name",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension types ontology term names"
            })}
        ),
        StructField(
            "ddt_ndarray_dimension_variable_types_sys_oterm_id",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension variable types ontology term CURIEs",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "ddt_ndarray_dimension_variable_types_sys_oterm_name",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension variable types ontology term names"
            })}
        ),
        StructField(
            "ddt_ndarray_variable_types_sys_oterm_id",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Variable types ontology term CURIEs",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "ddt_ndarray_variable_types_sys_oterm_name",
            ArrayType(StringType()),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Variable types ontology term names"
            })}
        ),
        StructField(
            "withdrawn_date",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Date when this DDT was withdrawn"
            })}
        ),
        StructField(
            "superceded_by_ddt_ndarray_id",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "DDT that supercedes this one",
                "type": "foreign_key",
                "references": "ddt_ndarray.ddt_ndarray_id"
            })}
        ),
    ])


# ------------------------------------------------------------------
# Build schema for sys_ddt_typedef table
# ------------------------------------------------------------------
def build_sys_ddt_typedef_schema() -> StructType:
    """Build the schema for the sys_ddt_typedef table."""
    return StructType([
        StructField(
            "ddt_ndarray_id",
            StringType(),
            nullable=False,
            metadata={"comment": json.dumps({
                "description": "Foreign key to ddt_ndarray",
                "type": "foreign_key",
                "references": "ddt_ndarray.ddt_ndarray_id"
            })}
        ),
        StructField(
            "cdm_column_name",
            StringType(),
            nullable=False,
            metadata={"comment": json.dumps({
                "description": "CDM column name"
            })}
        ),
        StructField(
            "cdm_column_data_type",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "CDM column data type"
            })}
        ),
        StructField(
            "scalar_type",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Scalar type"
            })}
        ),
        StructField(
            "fk",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Foreign key reference"
            })}
        ),
        StructField(
            "comment",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Column comment"
            })}
        ),
        StructField(
            "unit_sys_oterm_id",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Unit ontology term CURIE",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "unit_sys_oterm_name",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Unit ontology term name"
            })}
        ),
        StructField(
            "dimension_number",
            IntegerType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension number"
            })}
        ),
        StructField(
            "dimension_oterm_id",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension ontology term CURIE",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "dimension_oterm_name",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Dimension ontology term name"
            })}
        ),
        StructField(
            "variable_number",
            IntegerType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Variable number"
            })}
        ),
        StructField(
            "variable_oterm_id",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Variable ontology term CURIE",
                "type": "foreign_key",
                "references": "sys_oterm.sys_oterm_id"
            })}
        ),
        StructField(
            "variable_oterm_name",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Variable ontology term name"
            })}
        ),
        StructField(
            "original_csv_string",
            StringType(),
            nullable=True,
            metadata={"comment": json.dumps({
                "description": "Original CSV string representation"
            })}
        ),
    ])


# ------------------------------------------------------------------
# Load a schema from a Python file
# ------------------------------------------------------------------
def load_schema_from_file(schema_file_path: str) -> StructType:
    """
    Dynamically load a schema from a Python file.
    The file should define a variable named 'schema' that is a StructType.
    The first line (imports) should already be stripped.
    """
    spec = importlib.util.spec_from_file_location("schema_module", schema_file_path)
    schema_module = importlib.util.module_from_spec(spec)
    
    # Inject PySpark types into the module's namespace
    # so the schema definition can use them without importing
    schema_module.__dict__['StructType'] = StructType
    schema_module.__dict__['StructField'] = StructField
    schema_module.__dict__['StringType'] = StringType
    schema_module.__dict__['IntegerType'] = IntegerType
    schema_module.__dict__['DoubleType'] = DoubleType
    schema_module.__dict__['BooleanType'] = BooleanType
    schema_module.__dict__['ArrayType'] = ArrayType
    schema_module.__dict__['DataType'] = DataType
    
    # Now execute the module
    spec.loader.exec_module(schema_module)
    
    if not hasattr(schema_module, 'schema'):
        raise ValueError(f"Schema file {schema_file_path} does not define 'schema' variable")
    
    return schema_module.schema

# ------------------------------------------------------------------
# Load a TSV file with a given schema
# ------------------------------------------------------------------
def load_tsv_with_schema(spark, tsv_path: str, schema: StructType) -> Any:
    """
    Load a TSV file and apply the given schema with metadata.
    """
    # Read raw TSV
    df = (
        spark.read.format("csv")
        .option("header", "true")
        .option("sep", "\t")
        .option("inferSchema", "false")
        .option("multiLine", "true")
        .option("quote", "\"")
        .option("escape", "\"")
        .load(tsv_path)
    )
    
    # Handle array columns (convert from string representation)
    for field in schema.fields:
        if isinstance(field.dataType, ArrayType) and field.name in df.columns:
            df = df.withColumn(field.name, _convert_array_column(field.name))
    
    # Apply schema with metadata
    df = _apply_schema_with_metadata(spark, df, schema, make_nullable=True)
    
    return df


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------
def generate_ddt_tables(spark,
                        db_name: str = "jmc_coral",
                        fmt: str = "delta"):
    """
    Build the DDT tables:
    1. ddt_ndarray - metadata table
    2. sys_ddt_typedef - typedef table
    3. ddt_brick* tables - individual brick data tables
    """
    # ------------------------------------------------------------------
    # Resolve bucket & base prefix from the workspace
    # ------------------------------------------------------------------
    workspace = get_my_workspace()
    s3a_root = workspace.home_paths[0]
    bucket, base_prefix = _parse_s3a_uri(s3a_root)
    
    # DDT files live under <base_prefix>/data/data/
    data_prefix = f"{base_prefix.rstrip('/')}/data/data/"
    
    # ------------------------------------------------------------------
    # Get MinIO credentials and endpoint
    # ------------------------------------------------------------------
    cred = get_minio_credentials()  # <-- defined elsewhere
    endpoint = "http://10.58.1.104:9002"
    
    # ------------------------------------------------------------------
    # Initialize the target database
    # ------------------------------------------------------------------
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    spark.sql(f"USE {db_name}")
    
    # ------------------------------------------------------------------
    # 1. Load ddt_ndarray table
    # ------------------------------------------------------------------
    logging.info("Loading ddt_ndarray table...")
    ndarray_tsv_path = f"s3a://{bucket}/{data_prefix}ddt_ndarray.tsv"
    ndarray_schema = build_ddt_ndarray_schema()
    
    try:
        ndarray_df = load_tsv_with_schema(spark, ndarray_tsv_path, ndarray_schema)
        
        logging.info(f"--- Schema for table `{db_name}.ddt_ndarray` ---")
        ndarray_df.printSchema()
        logging.info(f"--- Sample rows for `{db_name}.ddt_ndarray` (up to 5) ---")
        ndarray_df.show(5, truncate=False)
        
        spark.sql(f"DROP TABLE IF EXISTS {db_name}.ddt_ndarray")
        ndarray_df.write.format(fmt).option(
            "comment", "Dynamic Data Types (N-Dimensional Arrays)"
        ).saveAsTable(f"{db_name}.ddt_ndarray")
        logging.info(f"Created table {db_name}.ddt_ndarray")
    except Exception as exc:
        logging.error(f"Failed to load ddt_ndarray: {exc}")
        raise
    
    # ------------------------------------------------------------------
    # 2. Load sys_ddt_typedef table
    # ------------------------------------------------------------------
    logging.info("Loading sys_ddt_typedef table...")
    typedef_tsv_path = f"s3a://{bucket}/{data_prefix}sys_ddt_typedef.tsv"
    typedef_schema = build_sys_ddt_typedef_schema()
    
    try:
        typedef_df = load_tsv_with_schema(spark, typedef_tsv_path, typedef_schema)
        
        # Rename brick_id to ddt_ndarray_id if needed
        if "brick_id" in typedef_df.columns:
            typedef_df = typedef_df.withColumnRenamed("brick_id", "ddt_ndarray_id")
            # Reapply schema to preserve metadata
            typedef_df = _apply_schema_with_metadata(spark, typedef_df, typedef_schema, make_nullable=True)
        
        logging.info(f"--- Schema for table `{db_name}.sys_ddt_typedef` ---")
        typedef_df.printSchema()
        logging.info(f"--- Sample rows for `{db_name}.sys_ddt_typedef` (up to 5) ---")
        typedef_df.show(5, truncate=False)
        
        spark.sql(f"DROP TABLE IF EXISTS {db_name}.sys_ddt_typedef")
        typedef_df.write.format(fmt).option(
            "comment", "Typedefs for Dynamic Data Types (N-Dimensional Arrays)"
        ).saveAsTable(f"{db_name}.sys_ddt_typedef")
        logging.info(f"Created table {db_name}.sys_ddt_typedef")
    except Exception as exc:
        logging.error(f"Failed to load sys_ddt_typedef: {exc}")
        raise
    
    # ------------------------------------------------------------------
    # 3. Load all Brick* tables
    # ------------------------------------------------------------------
    logging.info("Loading Brick* tables...")
    
    try:
        # List all objects in the data directory using boto3
        all_keys = list_objects_boto3(
            bucket=bucket,
            prefix=data_prefix,
            credentials=cred,
            endpoint=endpoint,
        )
        
        # Filter for Brick*.tsv files
        brick_tsv_files = []
        for key in all_keys:
            filename = os.path.basename(key)
            if filename.startswith("Brick") and filename.endswith(".tsv"):
                brick_tsv_files.append(key)
        
        logging.info(f"Found {len(brick_tsv_files)} Brick TSV files")
        
        # Create S3 client for downloading schema files
        s3_client = _get_boto3_s3_client(cred, endpoint)
        
        for brick_tsv_key in brick_tsv_files:
            # Extract brick name (e.g., "Brick00123" from path ending in "Brick00123.tsv")
            brick_filename = os.path.basename(brick_tsv_key)
            brick_name = brick_filename.replace(".tsv", "")
            
            # Construct paths
            brick_tsv_path = f"s3a://{bucket}/{brick_tsv_key}"
            
            # Schema file is in the same directory as the TSV
            brick_schema_filename = f"{brick_name}_schema.py"
            brick_schema_key = os.path.join(os.path.dirname(brick_tsv_key), brick_schema_filename)
            
            logging.info(f"Processing brick: {brick_name}")
            
            # Download schema file to local temp location
            tmp_schema_path = None
            try:
                tmp_schema_path = _download_to_temp(s3_client, bucket, brick_schema_key, suffix='.py')
                
                # Load schema
                brick_schema = load_schema_from_file(tmp_schema_path)
                
                # Load TSV data
                brick_df = load_tsv_with_schema(spark, brick_tsv_path, brick_schema)
                
                # Table name is ddt_ + brick name in lowercase (e.g., ddt_brick00123)
                table_name = f"ddt_{brick_name.lower()}"
                
                logging.info(f"--- Schema for table `{db_name}.{table_name}` ---")
                brick_df.printSchema()
                logging.info(f"--- Sample rows for `{db_name}.{table_name}` (up to 5) ---")
                brick_df.show(5, truncate=False)
                
                spark.sql(f"DROP TABLE IF EXISTS {db_name}.{table_name}")
                brick_df.write.format(fmt).option(
                    "comment", f"DDT Brick table: {brick_name}"
                ).saveAsTable(f"{db_name}.{table_name}")
                logging.info(f"Created table {db_name}.{table_name}")
                
            except ClientError as e:
                logging.warning(f"Schema file not found for {brick_name}, skipping... ({e})")
                continue
            except Exception as exc:
                logging.error(f"Failed to load brick {brick_name}: {exc}")
                continue
            finally:
                # Clean up temp file
                if tmp_schema_path and os.path.exists(tmp_schema_path):
                    os.remove(tmp_schema_path)
    
    except Exception as exc:
        logging.error(f"Failed to list Brick files: {exc}")
        raise
    
    logging.info("✅ DDT table generation complete.")


# ------------------------------------------------------------------
# Execute when run inside a notebook
# ------------------------------------------------------------------
spark = get_spark_session()               # <-- defined elsewhere
db_name = "jmc_coral"
spark.sql(f"USE {db_name}")
generate_ddt_tables(spark, db_name)
