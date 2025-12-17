"""
update_coral_ontologies.py

Load all OBO files from the MinIO S3‑A bucket defined by the workspace
and (re)populate the ``sys_oterm`` Delta table.  This script is
intended to be executed inside a Jupyter notebook – no command‑line
arguments are required.
"""

import json
import logging
import os
import re
import tempfile
from typing import Dict, Any, List

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    BooleanType,
    ArrayType,
    MapType,
)

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, NoCredentialsError

# ------------------------------------------------------------------
# Helper: parse an ``s3a://`` URI into bucket + prefix
# ------------------------------------------------------------------
def _parse_s3a_uri(s3a_uri: str) -> (str, str):
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
# OBO parser (identical to the one used locally)
# ------------------------------------------------------------------
def _parse_obo_file(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse an OBO file and return a mapping ``{term_id: term_dict}``.
    """
    terms = {}
    current = {}
    in_term = False

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("!"):
                continue

            if line == "[Term]":
                if in_term and "id" in current:
                    terms[current["id"]] = current
                current = {
                    "synonyms": [],
                    "xrefs": [],
                    "property_values": {},
                }
                in_term = True
                continue
            elif line.startswith("["):
                if in_term and "id" in current:
                    terms[current["id"]] = current
                in_term = False
                continue

            if not in_term:
                continue

            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key == "id":
                current["id"] = value
            elif key == "name":
                current["name"] = value
            elif key == "def":
                m = re.match(r'^"(.*)"(?:\s+\[.*\])?$', value)
                current["definition"] = m.group(1) if m else value
            elif key == "synonym":
                m = re.match(r'^"(.*)"\s+.*$', value)
                synonym = m.group(1) if m else value
                current["synonyms"].append(synonym)
            elif key == "xref":
                xref_curie = value.split(" ", 1)[0]
                current["xrefs"].append(xref_curie)
            elif key == "is_a":
                current["parent"] = value.split(" ", 1)[0]
            elif key == "property_value":
                m = re.match(r'^(\S+)\s+"([^"]*)"', value)
                if m:
                    prop_curie, prop_val = m.group(1), m.group(2)
                    current["property_values"].setdefault(prop_curie, []).append(prop_val)

    if in_term and "id" in current:
        terms[current["id"]] = current
    return terms


# ------------------------------------------------------------------
# Helper: download a single OBO object to a temporary local file
# ------------------------------------------------------------------
def _download_obo_to_temp(s3_client, bucket: str, key: str) -> str:
    """
    Download an OBO object from MinIO to a temporary local file and
    return the temporary file path.
    """
    resp = s3_client.get_object(Bucket=bucket, Key=key)
    body = resp["Body"].read()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".obo")
    tmp.write(body)
    tmp.close()
    return tmp.name


# ------------------------------------------------------------------
# Main loader – now uses the helper functions above
# ------------------------------------------------------------------
def load_all_ontologies_from_minio() -> Dict[str, Dict[str, Any]]:
    """
    Load **all** OBO files from the MinIO S3‑A bucket defined by the
    workspace. Returns a mapping ``{prefix: {term_id: term_dict}}`` where
    ``prefix`` is the filename without the ``.obo`` extension.
    """
    # ------------------------------------------------------------------
    # Resolve bucket & base prefix from the workspace
    # ------------------------------------------------------------------
    workspace = get_my_workspace()                     # <-- defined elsewhere
    s3a_root = workspace.home_paths[0]                # e.g. "s3a://cdm-lake/users-general-warehouse/jmc/coral"
    bucket, base_prefix = _parse_s3a_uri(s3a_root)

    # The ontologies live under <base_prefix>/data/ontologies/
    prefix = f"{base_prefix.rstrip('/')}/data/ontologies/"

    # ------------------------------------------------------------------
    # MinIO credentials (object with .access_key, .secret_key, .username)
    # ------------------------------------------------------------------
    cred = get_minio_credentials()                    # <-- defined elsewhere

    # ------------------------------------------------------------------
    # Hard‑coded endpoint for the local MinIO server
    # ------------------------------------------------------------------
    endpoint = "https://minio.minio.berdl.kbase.us"

    # ------------------------------------------------------------------
    # 1️⃣  List all OBO objects under the computed prefix
    # ------------------------------------------------------------------
    try:
        obo_keys = list_objects_boto3(
            bucket=bucket,
            prefix=prefix,
            credentials=cred,
            endpoint=endpoint,
        )
    except (ClientError, NoCredentialsError) as e:
        logging.error(f"Failed to list objects in bucket {bucket}: {e}")
        raise

    # ------------------------------------------------------------------
    # 2️⃣  Download each OBO file, parse it, and collect the terms
    # ------------------------------------------------------------------
    s3_client = _get_boto3_s3_client(cred, endpoint)
    ontologies: Dict[str, Dict[str, Any]] = {}

    for key in obo_keys:
        if not key.lower().endswith(".obo"):
            continue

        tmp_path = _download_obo_to_temp(s3_client, bucket, key)
        terms = _parse_obo_file(tmp_path)

        # The ontology prefix is the filename without the .obo extension
        ont_prefix = os.path.basename(key).split(".")[0]
        ontologies[ont_prefix] = terms

        logging.info(
            f"Loaded ontology '{ont_prefix}' from '{key}' "
            f"({len(terms)} terms)"
        )

    return ontologies


# ------------------------------------------------------------------
# Build a Spark DataFrame that matches the ``coral_ontologies`` schema
# ------------------------------------------------------------------
def build_ontologies_dataframe(spark: SparkSession, ontologies):
    """Create a DataFrame matching the ``coral_ontologies`` schema."""
    schema = StructType(
        [
            StructField(
                "sys_oterm_id",
                StringType(),
                nullable=False,
                metadata={
                    "comment": json.dumps({
                        "description": "Term identifier, aka CURIE (Primary key)",
                        "type": "primary_key"
                    })
                },
            ),
            StructField(
                "parent_sys_oterm_id",
                StringType(),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "Parent term identifier",
                        "type": "foreign_key",
                        "references": "sys_oterm.sys_oterm_id"
                    })
                },
            ),
            StructField(
                "sys_oterm_ontology",
                StringType(),
                nullable=False,
                metadata={
                    "comment": json.dumps({
                        "description": "Ontology that each term is from"
                    })
                },
            ),
            StructField(
                "sys_oterm_name",
                StringType(),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "Term name"
                    })
                },
            ),
            StructField(
                "sys_oterm_synonyms",
                ArrayType(StringType()),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "List of synonyms for a term"
                    })
                },
            ),
            StructField(
                "sys_oterm_definition",
                StringType(),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "Term definition"
                    })
                },
            ),
            StructField(
                "sys_oterm_links",
                ArrayType(StringType()),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "Indicates that values are links to other tables (Ref) or ontological terms (ORef)"
                    })
                },
            ),
            StructField(
                "sys_oterm_properties",
                MapType(StringType(), StringType()),
                nullable=True,
                metadata={
                    "comment": json.dumps({
                        "description": "Semicolon-separated map of properties to values for terms that are CORAL microtypes, including scalar data_type, is_valid_data_variable, is_valid_dimension, is_valid_data_variable, is_valid_dimension_variable, is_valid_property, valid_units, and valid_units_parent"
                    })
                },
            ),
        ]
    )

    rows = []
    for prefix, terms in ontologies.items():
        for term_id, term in terms.items():
            prop_map = None
            if term.get("property_values"):
                # Collapse list‑of‑values into a semicolon‑separated string
                prop_map = {k: ";".join(v) for k, v in term["property_values"].items()}
            rows.append(
                (
                    term_id,
                    term.get("parent") if term.get("parent") else None,
                    prefix,
                    term.get("name"),
                    term.get("synonyms"),
                    term.get("definition"),
                    term.get("xrefs") if term.get("xrefs") else None,
                    prop_map
                )
            )
    return spark.createDataFrame(rows, schema)


# ------------------------------------------------------------------
# Execution (intended for a Jupyter notebook)
# ------------------------------------------------------------------
spark = get_spark_session()               # <-- defined elsewhere
db_name = "u_jmc__coral"
table_name = "sys_oterm"
spark.sql(f"USE {db_name}")

ontologies = load_all_ontologies_from_minio()
df = build_ontologies_dataframe(spark, ontologies)

# Drop the table if it already exists
spark.sql(f"DROP TABLE IF EXISTS {db_name}.{table_name}")

# Write the Delta table with the freshly‑loaded data and add a table comment
df.write.format("delta").option("comment", "Ontology terms used in CORAL").saveAsTable(f"{db_name}.{table_name}")

logging.info(f"✅ Successfully created/updated table {db_name}.{table_name}")
