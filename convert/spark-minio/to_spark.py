#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
to_spark.py

Generate three artefacts from a CORAL ``typedef.json`` file:

1. **Python snippet** (default name: ``make_tables.py``) that
   contains a ``generate_cdm(spark)`` function.  Paste this file into a
   Jupyter notebook, create a SparkSession (configured for your MinIO/S3
   endpoint) and call ``generate_cdm(spark)`` – the CDM tables will be
   created.

2. **Shell script** (default name: ``copy_to_minio.sh``) that copies
   only the OBO ontology files actually referenced in the typedef and
   any existing TSV data files into a MinIO bucket using the ``mc``
   client.  The script creates the buckets with ``mc mb`` before copying.

3. **Update script** (default name:
   ``update_coral_ontologies.py``) that can be run on a PySpark
   cluster to (re)populate the ``coral_ontologies`` Delta table with
   *all* term information, **including every ``property_value`` line**.
   This script reads the OBO files directly from the S3 bucket
   (``$S3ROOT/data/ontologies/``) using the workspace helpers
   ``get_my_workspace()`` and ``get_minio_credentials()``.

Both the generated CDM snippet and the update script contain the same
light‑weight OBO parser, so no external ontology‑parsing libraries are
required.

Usage
-----
    python to_spark.py \\
        --typedef /path/to/typedef.json \\
        --obo_dir /path/to/ontologies \\
        --output make_tables.py \\
        --minio_target cdm-minio/cdm-lake/users-general-warehouse/jmc/data \\
        --shell_output copy_to_minio.sh \\
        --update_script_output update_coral_ontologies.py \\
        --tsv_dir /path/to/tsv
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import json
import os
import re
import sys
import logging
import datetime
import base64
import textwrap
import tempfile
from typing import Any, Dict, List, Tuple, Set

# ----------------------------------------------------------------------
# PySpark imports (used only for the CDM‑generation snippet)
# ----------------------------------------------------------------------
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    BooleanType,
    ArrayType,
    MapType,
    DataType,
)

# ----------------------------------------------------------------------
# Logging configuration (used by this script)
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)

# ----------------------------------------------------------------------
# 1️⃣  AUTHENTICATION HELPERS (unchanged – kept for completeness)
# ----------------------------------------------------------------------
def load_public_key(pubkey_path: str) -> Any:
    """Load the public RSA key used by the Data‑Clearinghouse."""
    if not os.path.isfile(pubkey_path):
        raise FileNotFoundError(f"Public key file not found: {pubkey_path}")

    from Crypto.PublicKey import RSA

    with open(pubkey_path, "rb") as f:
        key_data = f.read()
    return RSA.import_key(key_data)


def build_authorized_headers(public_key: Any) -> dict:
    """Create the ``Authorization`` header required by the CORAL API."""
    import jwt
    from Crypto.Cipher import PKCS1_OAEP

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    payload = {"exp": now + datetime.timedelta(minutes=120), "iat": now}

    # ------------------------------------------------------------------
    # IMPORTANT FIX: encode *before* encrypt!
    # ------------------------------------------------------------------
    timestamp_bytes = str(int(now.timestamp())).encode("utf-8")
    encryptor = PKCS1_OAEP.new(public_key)
    secret_encrypted = encryptor.encrypt(timestamp_bytes)

    b64_secret = base64.b64encode(secret_encrypted).decode("utf-8")
    token = jwt.encode(
        payload,
        "data clearinghouse",
        algorithm="HS256",
        headers={"secret": b64_secret},
    )
    return {"Authorization": f"JwToken {token}", "content-type": "application/json"}


# ----------------------------------------------------------------------
# 2️⃣  OBO PARSER (captures property_value lines) – **local filesystem version**
# ----------------------------------------------------------------------
def _parse_obo_file(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse an OBO file and return a mapping ``{term_id: term_dict}``.

    ``term_dict`` contains:
        * id               – CURIE (e.g. ``ME:0000277``)
        * name
        * definition
        * synonyms   – list of synonym strings
        * xrefs      – list of cross‑reference CURIEs
        * is_obsolete – bool (default ``False``)
        * property_values – dict ``{property_curie: [value, …]}``
    """
    terms: Dict[str, Dict[str, Any]] = {}
    current: Dict[str, Any] = {}
    in_term = False

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("!"):
                continue

            # New stanza
            if line == "[Term]":
                if in_term and "id" in current:
                    terms[current["id"]] = current
                current = {
                    "synonyms": [],
                    "xrefs": [],
                    "is_obsolete": False,
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
            elif key == "is_obsolete":
                current["is_obsolete"] = value.lower() == "true"
            elif key == "property_value":
                # Expected format: <property_curie> "value"
                m = re.match(r'^(\\S+)\\s+"([^"]*)"', value)
                if m:
                    prop_curie, prop_val = m.group(1), m.group(2)
                    current["property_values"].setdefault(prop_curie, []).append(prop_val)

    if in_term and "id" in current:
        terms[current["id"]] = current
    return terms


def load_ontologies(obo_dir: str, prefixes: Set[str]) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Load the OBO file that provides the *most* terms for each required
    prefix from the **local filesystem**.  Returns a mapping
    ``{prefix: {term_id: term_dict}}`` and the list of file paths that were
    actually selected (used for the copy script).
    """
    best_by_prefix: Dict[str, Tuple[int, Dict[str, Any], str]] = {}
    for fn in os.listdir(obo_dir):
        if not fn.lower().endswith(".obo"):
            continue
        path = os.path.abspath(os.path.join(obo_dir, fn))
        terms = _parse_obo_file(path)

        # Count terms per needed prefix
        prefix_counts: Dict[str, int] = {}
        for term_id in terms:
            if ":" not in term_id:
                continue
            prefix = term_id.split(":")[0]
            if prefix not in prefixes:
                continue
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        for prefix, cnt in prefix_counts.items():
            if prefix not in best_by_prefix or cnt > best_by_prefix[prefix][0]:
                best_by_prefix[prefix] = (cnt, terms, path)

    ontologies = {p: best_by_prefix[p][1] for p in best_by_prefix}
    loaded_files = [best_by_prefix[p][2] for p in best_by_prefix]
    for p in ontologies:
        logging.info(
            f"Selected ontology '{p}' from '{best_by_prefix[p][2]}' "
            f"({len(ontologies[p])} terms)"
        )
    return ontologies, loaded_files


# ----------------------------------------------------------------------
# 3️⃣  TYPEDEF → CDM SCHEMA HELPERS
# ----------------------------------------------------------------------
def map_scalar_type(scalar_type: str) -> DataType:
    """Map a CORAL ``scalar_type`` string to a Spark DataType."""
    if scalar_type.startswith("[") and scalar_type.endswith("]"):
        inner = scalar_type[1:-1].strip()
        return ArrayType(map_scalar_type(inner), containsNull=False)

    st = scalar_type.lower()
    if st in ("text", "term"):
        return StringType()
    if st == "int":
        return IntegerType()
    if st in ("float", "double"):
        return DoubleType()
    if st == "bool":
        return BooleanType()
    return StringType()


def parse_fk(fk_str: str) -> Tuple[str, bool]:
    """Parse a foreign‑key descriptor (returns table name, is_array)."""
    is_array = False
    if fk_str.startswith("[") and fk_str.endswith("]"):
        is_array = True
        fk_str = fk_str[1:-1].strip()
    return fk_str.split(".", 1)[0], is_array


def fk_column_name(table_name: str, is_array: bool) -> str:
    base = table_name.lower()
    return f"{base}_ids" if is_array else f"{base}_id"


def field_to_column_name(field: Dict[str, Any]) -> str:
    """Return the CDM column name for a field."""
    if field.get("PK", False):
        return "id"
    if field.get("UPK", False):
        return "name"
    fk = field.get("FK")
    if fk:
        ref_table, is_array = parse_fk(fk)
        return fk_column_name(ref_table, is_array)
    return field.get("name")


def get_column_names_for_type(type_def: Dict[str, Any]) -> List[str]:
    """Return the ordered CDM column names for a type definition."""
    cols = [field_to_column_name(f) for f in type_def.get("fields", [])]
    if not any(f.get("PK", False) for f in type_def.get("fields", [])):
        cols.insert(0, "id")
    if any(f.get("UPK", False) for f in type_def.get("fields", [])) and "name" not in cols:
        cols.append("name")
    return cols


def process_field(field: Dict[str, Any], type_name: str) -> Tuple[StructField, Dict[str, Any]]:
    """Convert a CORAL field definition into a Spark ``StructField`` and a metadata dict."""
    col_name = field_to_column_name(field)
    spark_type = map_scalar_type(field.get("scalar_type", "text"))
    nullable = not field.get("required", False)

    metadata: Dict[str, Any] = {
        "orig_name": field.get("name"),
        "type_term": field.get("type_term"),
        "required": field.get("required", False),
        "pk": field.get("PK", False),
        "upk": field.get("UPK", False),
    }
    if "constraint" in field:
        metadata["constraint"] = (
            json.dumps(field["constraint"])
            if isinstance(field["constraint"], (list, dict))
            else field["constraint"]
        )
    if "comment" in field:
        metadata["comment"] = field["comment"]
    if "units_term" in field:
        metadata["units_term"] = field["units_term"]
    if field.get("FK"):
        metadata["fk"] = field["FK"]
        metadata["fk_table"], metadata["fk_is_array"] = parse_fk(field["FK"])

    struct_field = StructField(col_name, spark_type, nullable=nullable, metadata=metadata)

    typedef_row = {
        "type_name": type_name,
        "field_name": field.get("name"),
        "cdm_column_name": col_name,
        "scalar_type": field.get("scalar_type", "text"),
        "required": field.get("required", False),
        "pk": field.get("PK", False),
        "upk": field.get("UPK", False),
        "fk": field.get("FK"),
        "constraint": field.get("constraint"),
        "comment": field.get("comment"),
        "units_term": field.get("units_term"),
        "type_term": field.get("type_term"),
    }
    return struct_field, typedef_row


def generate_schema(type_def: Dict[str, Any]) -> Tuple[StructType, List[Dict[str, Any]]]:
    """Build a Spark ``StructType`` for a CORAL type and collect typedef metadata."""
    struct_fields = []
    typedef_rows = []
    for f in type_def.get("fields", []):
        sf, meta = process_field(f, type_def.get("name"))
        struct_fields.append(sf)
        typedef_rows.append(meta)

    if not any(sf.name == "id" for sf in struct_fields):
        struct_fields.insert(
            0,
            StructField(
                "id",
                StringType(),
                nullable=False,
                metadata={"generated": True, "note": "added by generator"},
            ),
        )
    if any(r["upk"] for r in typedef_rows) and not any(sf.name == "name" for sf in struct_fields):
        struct_fields.append(
            StructField(
                "name",
                StringType(),
                nullable=False,
                metadata={"generated": True, "note": "UPK promoted to name"},
            )
        )
    return StructType(struct_fields), typedef_rows


def build_typedefs_dataframe(spark, typedef_rows: List[Dict[str, Any]]):
    """Create the ``coral_typedefs`` DataFrame."""
    schema = StructType(
        [
            StructField("type_name", StringType(), nullable=False),
            StructField("field_name", StringType(), nullable=False),
            StructField("cdm_column_name", StringType(), nullable=False),
            StructField("scalar_type", StringType(), nullable=True),
            StructField("required", BooleanType(), nullable=True),
            StructField("pk", BooleanType(), nullable=True),
            StructField("upk", BooleanType(), nullable=True),
            StructField("fk", StringType(), nullable=True),
            StructField("constraint", StringType(), nullable=True),
            StructField("comment", StringType(), nullable=True),
            StructField("units_term", StringType(), nullable=True),
            StructField("type_term", StringType(), nullable=True),
        ]
    )
    rows = [
        (
            r["type_name"],
            r["field_name"],
            r["cdm_column_name"],
            r["scalar_type"],
            r["required"],
            r["pk"],
            r["upk"],
            r["fk"],
            json.dumps(r["constraint"])
            if isinstance(r["constraint"], (list, dict))
            else r["constraint"],
            r["comment"],
            r["units_term"],
            r["type_term"],
        )
        for r in typedef_rows
    ]
    return spark.createDataFrame(rows, schema)


def build_ontologies_dataframe(spark, ontologies: Dict[str, Dict[str, Any]]):
    """Create the ``coral_ontologies`` DataFrame (includes property values)."""
    schema = StructType(
        [
            StructField("ontology_prefix", StringType(), nullable=False),
            StructField("term_id", StringType(), nullable=False),
            StructField("name", StringType(), nullable=True),
            StructField("definition", StringType(), nullable=True),
            StructField("synonyms", ArrayType(StringType()), nullable=True),
            StructField("xrefs", ArrayType(StringType()), nullable=True),
            StructField("is_obsolete", BooleanType(), nullable=False),
            StructField("property_values", MapType(StringType(), StringType()), nullable=True),
        ]
    )
    rows = []
    for prefix, terms in ontologies.items():
        for term_id, term in terms.items():
            prop_map = None
            if term.get("property_values"):
                prop_map = {k: ";".join(v) for k, v in term["property_values"].items()}
            rows.append(
                (
                    prefix,
                    term_id,
                    term.get("name"),
                    term.get("definition"),
                    term.get("synonyms") if term.get("synonyms") else None,
                    term.get("xrefs") if term.get("xrefs") else None,
                    term.get("is_obsolete", False),
                    prop_map,
                )
            )
    return spark.createDataFrame(rows, schema)


def create_cdm_table(
    spark,
    db_name: str,
    table_name: str,
    schema: StructType,
    base_path: str,
    fmt: str = "delta",
):
    """Create (or replace) an empty CDM table using the supplied schema."""
    full_name = f"{db_name}.{table_name}"
    location = os.path.join(base_path, table_name)

    spark.sql(f"DROP TABLE IF EXISTS {full_name}")
    empty_df = spark.createDataFrame([], schema)
    empty_df.write.format(fmt).option("path", location).saveAsTable(full_name)

    logging.info(f"Created table {full_name} at {location}")


def generate_cdm(
    spark,
    typedef_path: str,
    obo_dir: str,
    base_path: str,
    db_name: str,
    load_tsv: bool,
    tsv_dir: str,
    fmt: str = "delta",
):
    """
    Create the CDM tables in Spark.

    Conventions:
      * Table name = lower‑case CORAL type name.
      * Primary key column = ``id``.
      * User primary key (UPK) → column ``name``.
      * Foreign keys → ``<referenced_table>_id`` (or ``_ids`` for arrays).
      * Two auxiliary tables: ``coral_typedefs`` and ``coral_ontologies``.
    """
    # Load typedef definitions
    with open(typedef_path, "r", encoding="utf-8") as f:
        typedef_data = json.load(f)
    type_defs = typedef_data.get("system_types", []) + typedef_data.get("static_types", [])

    # Load ontologies from the local filesystem (all OBO files)
    ontologies = load_ontologies(obo_dir, set())[0]

    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    spark.sql(f"USE {db_name}")

    all_typedef_rows: List[Dict[str, Any]] = []

    for tdef in type_defs:
        type_name = tdef.get("name")
        if not type_name:
            continue
        table_name = type_name.lower()
        schema, typedef_rows = generate_schema(tdef)
        all_typedef_rows.extend(typedef_rows)

        create_cdm_table(spark, db_name, table_name, schema, base_path, fmt=fmt)

        if load_tsv:
            tsv_path = os.path.join(tsv_dir, f"{type_name}.tsv")
            if os.path.isfile(tsv_path):
                df = (
                    spark.read.format("csv")
                    .option("header", "true")
                    .option("sep", "\t")
                    .schema(schema)
                    .load(tsv_path)
                )
                df.write.format(fmt).mode("overwrite").saveAsTable(f"{db_name}.{table_name}")
                logging.info(f"Loaded TSV data into {db_name}.{table_name}")
            else:
                logging.warning(f"TSV file {tsv_path} not found – skipping.")

    typedefs_df = build_typedefs_dataframe(spark, all_typedef_rows)
    typedefs_df.write.format(fmt).mode("overwrite").saveAsTable(f"{db_name}.coral_typedefs")
    logging.info(f"Created auxiliary table {db_name}.coral_typedefs")

    ontologies_df = build_ontologies_dataframe(spark, ontologies)
    ontologies_df.write.format(fmt).mode("overwrite").saveAsTable(f"{db_name}.coral_ontologies")
    logging.info(f"Created auxiliary table {db_name}.coral_ontologies")

    logging.info("✅ CDM generation complete.")


# ----------------------------------------------------------------------
# 5️⃣  RENDERERS FOR THE GENERATED FILES
# ----------------------------------------------------------------------
def render_make_tables(needed_prefixes: Set[str]) -> str:
    """
    Return the source code for ``make_tables.py``.
    The placeholder ``__NEEDED_PREFIXES__`` will be replaced with the
    actual set of prefixes.
    """
    template = textwrap.dedent('''\
"""make_tables.py

This file is auto‑generated by ``to_spark.py``.  It contains a
``generate_cdm(spark)`` function that builds the CDM tables in a Spark
session (Delta Lake format).  The script follows the conventions used in
``update_coral_ontologies.py`` and adds robust handling for the
``scalar_type == "term"`` fields.

Key behaviours
--------------
* System types → tables named ``sys_<type>`` (e.g. ``sys_process``)
* Static types → tables named ``sdt_<type>`` (e.g. ``sdt_genome``)
* Primary‑key column → ``<table>_id``
* Foreign‑key column → ``<referenced_table>_id`` (or ``_ids`` for arrays)
* ``scalar_type == "term"`` fields are **expanded in place** into two
  columns:
  ``<field>_sys_oterm_id`` (FK → ``sys_oterm``) and
  ``<field>_sys_oterm_name`` (the term name)
* All column names are lower‑case snake_case (underscores only)
* The TSV loader expects a *single* combined column for each term field of
  the form ``<term name> <term id>`` – e.g. ``Assay Growth <PROCESS:0000006>``
  – and splits it back into the two generated columns.
* Missing columns in a TSV are added as ``NULL`` so that the final schema
  can always be satisfied.
* Before each table is written we log its schema and the first few rows
  (up to 5) for debugging.
* Each table is dropped first (``DROP TABLE IF EXISTS``) to guarantee a
  clean creation.

Run the script in a notebook as follows::

    spark = get_spark_session()               # <-- defined elsewhere
    db_name = "jmc_coral"
    spark.sql(f"USE {db_name}")
    generate_cdm(spark, db_name)
"""

import json
import logging
import os
import re
from typing import Any, Dict, List, Tuple

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
    """Return (bucket, prefix) from a ``s3a://`` URI."""
    if not s3a_uri.startswith("s3a://"):
        raise ValueError(f"Unexpected S3A URI: {s3a_uri}")

    path = s3a_uri[len("s3a://") :]          # e.g. "cdm‑lake/users‑general‑warehouse/jmc"
    parts = path.split("/", 1)
    bucket = parts[0]
    prefix = parts[1].rstrip("/") + "/" if len(parts) == 2 else ""
    return bucket, prefix


# ------------------------------------------------------------------
# Normalise column names (lower‑case, underscores only)
# ------------------------------------------------------------------
def _normalize_name(name: str) -> str:
    """Convert an arbitrary name to snake_case."""
    name = name.strip()
    name = re.sub(r"[ \-]+", "_", name)            # spaces / hyphens → _
    name = re.sub(r"[^0-9a-zA-Z_]", "_", name)     # everything else → _
    name = re.sub(r"_+", "_", name)                # collapse multiple _
    return name.lower().strip("_")


# ------------------------------------------------------------------
# CDM naming helpers
# ------------------------------------------------------------------
def map_scalar_type(scalar_type: str) -> DataType:
    """Map a CORAL ``scalar_type`` to a Spark DataType."""
    if scalar_type.startswith("[") and scalar_type.endswith("]"):
        inner = scalar_type[1:-1].strip()
        return ArrayType(map_scalar_type(inner), containsNull=False)

    st = scalar_type.lower()
    if st in ("text", "term"):
        return StringType()
    if st == "int":
        return IntegerType()
    if st in ("float", "double"):
        return DoubleType()
    if st == "bool":
        return BooleanType()
    return StringType()


def parse_fk(fk_str: str) -> Tuple[str, bool]:
    """Parse a foreign‑key descriptor, returning (type, is_array)."""
    is_array = False
    if fk_str.startswith("[") and fk_str.endswith("]"):
        is_array = True
        fk_str = fk_str[1:-1].strip()
    return fk_str.split(".", 1)[0], is_array


def rename_fk_column(original_name: str, ref_type: str, is_array: bool,
                    type_to_table: Dict[str, str]) -> str:
    """
    Rename a foreign‑key column according to CDM conventions and then
    normalise it to snake_case.

    * If the original column name contains the referenced type (singular or
      plural), replace that part with the CDM table name and insert ``_id``
      or ``_ids`` **before** any remaining suffix.
      Example: ``genes_changed`` → ``sdt_gene_ids_changed``.
    * If it does not contain the referenced type, append ``_<cdm_table>_id``
      (or ``_ids``) to the original name.
      Example: ``derived_from`` → ``derived_from_sdt_genome_id``.
    """
    target_table = type_to_table.get(ref_type, ref_type.lower())
    suffix = "_ids" if is_array else "_id"

    lower_orig = original_name.lower()
    ref_singular = ref_type.lower()
    ref_plural = ref_singular + "s"

    idx = -1
    match_len = 0
    if ref_plural in lower_orig:
        idx = lower_orig.find(ref_plural)
        match_len = len(ref_plural)
    elif ref_singular in lower_orig:
        idx = lower_orig.find(ref_singular)
        match_len = len(ref_singular)

    if idx != -1:
        prefix = lower_orig[:idx]
        suffix_part = lower_orig[idx + match_len :]   # keep whatever follows the match
        new_name = f"{prefix}{target_table}{suffix}{suffix_part}"
    else:
        new_name = f"{lower_orig}_{target_table}{suffix}"

    return _normalize_name(new_name)


def field_to_column_name(field: Dict[str, Any],
                         current_table: str,
                         type_to_table: Dict[str, str]) -> str:
    """
    Derive the CDM column name for a field (non‑term fields only) and
    normalise it.
    """
    if field.get("PK", False):
        return _normalize_name(f"{current_table}_id")
    if field.get("UPK", False):
        return "name"                     # will be renamed later to <table>_name
    fk = field.get("FK")
    if fk:
        ref_type, is_array = parse_fk(fk)
        return rename_fk_column(field["name"], ref_type, is_array, type_to_table)
    return _normalize_name(field["name"])


# ------------------------------------------------------------------
# Process a single field – may produce one or two CDM columns
# ------------------------------------------------------------------
def process_field(field: Dict[str, Any],
                  type_name: str,
                  current_table: str,
                  type_to_table: Dict[str, str]) -> Tuple[
                      List[StructField],
                      List[Dict[str, Any]],
                      List[Dict[str, Any]]
                  ]:
    """
    Convert a CORAL field definition into Spark ``StructField`` objects,
    rows for the ``sys_typedef`` table, and (if needed) term‑mapping
    dictionaries used later to split the combined TSV column.
    """
    def build(col_name: str,
              spark_type: DataType,
              nullable: bool,
              comment: str,
              fk: str = None) -> Tuple[StructField, Dict[str, Any]]:
        metadata = {
            "orig_name": field.get("name"),
            "type_term": field.get("type_term"),
            "required": field.get("required", False),
            "pk": field.get("PK", False),
            "upk": field.get("UPK", False),
            "comment": comment,
        }
        if "constraint" in field:
            metadata["constraint"] = (
                json.dumps(field["constraint"])
                if isinstance(field["constraint"], (list, dict))
                else field["constraint"]
            )
        if "units_term" in field:
            metadata["units_term"] = field["units_term"]
        if fk:
            metadata["fk"] = fk

        struct = StructField(col_name, spark_type, nullable=nullable, metadata=metadata)

        typedef = {
            "type_name": type_name,
            "field_name": field.get("name"),
            "cdm_column_name": col_name,
            "scalar_type": field.get("scalar_type", "text"),
            "required": field.get("required", False),
            "pk": field.get("PK", False),
            "upk": field.get("UPK", False),
            "fk": fk,
            "constraint": field.get("constraint"),
            "comment": comment,
            "units_term": field.get("units_term"),
            "type_term": field.get("type_term"),
        }
        return struct, typedef

    # ------------------------------------------------------------------
    # TERM fields – split into id + name columns (keep original order)
    # ------------------------------------------------------------------
    if field.get("scalar_type") == "term":
        base = _normalize_name(field.get("name"))
        id_col = f"{base}_sys_oterm_id"
        name_col = f"{base}_sys_oterm_name"

        id_comment = f"Foreign key to `sys_oterm` (term id for field `{field.get('name')}`)"
        name_comment = f"Term name for field `{field.get('name')}`"

        id_field, id_typedef = build(
            id_col,
            StringType(),
            not field.get("required", False),
            id_comment,
            fk="sys_oterm.id",
        )
        name_field, name_typedef = build(
            name_col,
            StringType(),
            not field.get("required", False),
            name_comment,
        )

        term_mapping = {
            "orig_name": field.get("name"),   # column name as it appears in the TSV
            "id_col": id_col,
            "name_col": name_col,
            "required": field.get("required", False),
        }
        return [id_field, name_field], [id_typedef, name_typedef], [term_mapping]

    # ------------------------------------------------------------------
    # NON‑TERM fields – regular handling
    # ------------------------------------------------------------------
    col_name = field_to_column_name(field, current_table, type_to_table)
    spark_type = map_scalar_type(field.get("scalar_type", "text"))
    nullable = not field.get("required", False)

    if field.get("PK", False):
        comment = f"Primary key for table `{current_table}`"
    elif field.get("FK"):
        ref_type, _ = parse_fk(field["FK"])
        comment = f"Foreign key to `{type_to_table.get(ref_type, ref_type.lower())}`"
    else:
        comment = field.get("comment") or f"Field `{field.get('name')}`"

    struct, typedef = build(col_name, spark_type, nullable, comment,
                           fk=field.get("FK") if field.get("FK") else None)
    return [struct], [typedef], []


# ------------------------------------------------------------------
# Build the full schema for a type, collecting term‑split info
# ------------------------------------------------------------------
def generate_schema(type_def: Dict[str, Any],
                    table_name: str,
                    type_to_table: Dict[str, str]) -> Tuple[
                        StructType,
                        List[Dict[str, Any]],
                        List[Dict[str, Any]]
                    ]:
    """
    Return (schema, typedef_rows, term_mappings) for a CORAL type.
    The schema preserves the order of fields, expanding term fields into the
    two generated columns in the same position as the original field.
    """
    struct_fields: List[StructField] = []
    typedef_rows: List[Dict[str, Any]] = []
    term_mappings: List[Dict[str, Any]] = []

    for f in type_def.get("fields", []):
        fields, rows, terms = process_field(f, type_def.get("name"), table_name, type_to_table)
        struct_fields.extend(fields)
        typedef_rows.extend(rows)
        term_mappings.extend(terms)

    # Ensure a primary‑key column exists (if not already added by a PK field)
    pk_name = f"{table_name}_id"
    if not any(sf.name == pk_name for sf in struct_fields):
        struct_fields.insert(
            0,
            StructField(
                pk_name,
                StringType(),
                nullable=False,
                metadata={"comment": f"Primary key for table `{table_name}`"},
            ),
        )

    # Add a ``name`` column for user‑primary‑key (UPK) if needed
    if any(r["upk"] for r in typedef_rows) and not any(sf.name == "name" for sf in struct_fields):
        struct_fields.append(
            StructField(
                "name",
                StringType(),
                nullable=False,
                metadata={"comment": "User‑defined primary key (UPK)"},
            )
        )

    return StructType(struct_fields), typedef_rows, term_mappings


# ------------------------------------------------------------------
# Build the auxiliary ``sys_typedef`` DataFrame
# ------------------------------------------------------------------
def build_typedefs_dataframe(spark, typedef_rows: List[Dict[str, Any]]):
    schema = StructType([
        StructField("type_name", StringType(), nullable=False),
        StructField("field_name", StringType(), nullable=False),
        StructField("cdm_column_name", StringType(), nullable=False),
        StructField("scalar_type", StringType(), nullable=True),
        StructField("required", BooleanType(), nullable=True),
        StructField("pk", BooleanType(), nullable=True),
        StructField("upk", BooleanType(), nullable=True),
        StructField("fk", StringType(), nullable=True),
        StructField("constraint", StringType(), nullable=True),
        StructField("comment", StringType(), nullable=True),
        StructField("units_term", StringType(), nullable=True),
        StructField("type_term", StringType(), nullable=True),
    ])

    rows = [
        (
            r["type_name"],
            r["field_name"],
            r["cdm_column_name"],
            r["scalar_type"],
            r["required"],
            r["pk"],
            r["upk"],
            r["fk"],
            json.dumps(r["constraint"])
            if isinstance(r["constraint"], (list, dict))
            else r["constraint"],
            r["comment"],
            r["units_term"],
            r["type_term"],
        )
        for r in typedef_rows
    ]
    return spark.createDataFrame(rows, schema)


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
# Helper: split a combined term column ``"<name> <id>"`` into two columns
# ------------------------------------------------------------------
def _split_term_column(df,
                       orig_name: str,
                       id_col: str,
                       name_col: str):
    """
    From a column that contains ``term name <term id>`` (or only one part)
    create two new columns: ``id_col`` and ``name_col`` and drop the
    original column.
    """
    term_str = F.col(orig_name).cast("string")

    # ---- extract the ID (text inside <...>) ---------------------------------
    raw_id = F.regexp_extract(term_str, r"<([^>]+)>", 1)          # empty string if no match
    id_extracted = F.when(raw_id == "", None).otherwise(raw_id)

    # ---- extract the name (everything before the angle‑bracket part) -------
    raw_name = F.regexp_extract(term_str, r"^(.*?)(?:\s*<[^>]+>)?\s*$", 1)
    name_extracted = F.when(raw_name == "", None).otherwise(F.trim(raw_name))

    # ---- handle completely empty cells --------------------------------------
    id_extracted = F.when(term_str.isNull() | (term_str == ""), None).otherwise(id_extracted)
    name_extracted = F.when(term_str.isNull() | (term_str == ""), None).otherwise(name_extracted)

    df = df.withColumn(id_col, id_extracted).withColumn(name_col, name_extracted)
    df = df.drop(orig_name)
    return df


# ------------------------------------------------------------------
# Main entry point – to be called from a notebook
# ------------------------------------------------------------------
def generate_cdm(spark,
                 db_name: str = "jmc_coral",
                 load_tsv: bool = True,
                 fmt: str = "delta"):
    """
    Build the CDM tables.

    * System types → ``sys_<type>``
    * Static types → ``sdt_<type>``
    * ``term`` fields become ``<field>_sys_oterm_id`` and
      ``<field>_sys_oterm_name`` in the same position as the original column.
    * All column names are lower‑case snake_case.
    """
    # ------------------------------------------------------------------
    # Resolve bucket & base prefix from the workspace (same as in
    # update_coral_ontologies.py)
    # ------------------------------------------------------------------
    workspace = get_my_workspace()                     # <-- defined elsewhere
    s3a_root = workspace.home_paths[0]                # e.g. "s3a://cdm‑lake/users‑general‑warehouse/jmc"
    bucket, base_prefix = _parse_s3a_uri(s3a_root)

    # TSV and typedef files live under <base_prefix>/data/data/
    data_prefix = f"{base_prefix.rstrip('/')}/data/data/"

    # ------------------------------------------------------------------
    # Load typedef.json (multiline JSON)
    # ------------------------------------------------------------------
    typedef_path = f"s3a://{bucket}/{data_prefix}typedef.json"
    typedef_df = spark.read.option("multiline", "true").json(typedef_path)

    typedef_row = typedef_df.first()
    if typedef_row is None:
        raise RuntimeError(f"Unable to load typedef.json from {typedef_path}")

    typedef_data = typedef_row.asDict(recursive=True)

    system_types = typedef_data.get("system_types", [])
    static_types = typedef_data.get("static_types", [])
    all_type_defs = system_types + static_types

    # ------------------------------------------------------------------
    # Build a mapping from CORAL type name → CDM table name
    # ------------------------------------------------------------------
    type_to_table: Dict[str, str] = {}
    for tdef in system_types:
        type_to_table[tdef["name"]] = f"sys_{tdef['name'].lower()}"
    for tdef in static_types:
        type_to_table[tdef["name"]] = f"sdt_{tdef['name'].lower()}"

    # ------------------------------------------------------------------
    # Initialise the target database
    # ------------------------------------------------------------------
    spark.sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    spark.sql(f"USE {db_name}")

    all_typedef_rows: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Process each CORAL type
    # ------------------------------------------------------------------
    for tdef in all_type_defs:
        coral_type_name = tdef.get("name")
        if not coral_type_name:
            continue

        table_name = type_to_table[coral_type_name]          # e.g. sys_process or sdt_genome
        schema, typedef_rows, term_mappings = generate_schema(tdef, table_name, type_to_table)
        all_typedef_rows.extend(typedef_rows)

        table_comment = f"CDM table for CORAL type `{coral_type_name}`"

        # ------------------------------------------------------------------
        # Load TSV data (if requested) – handle arrays and term columns
        # ------------------------------------------------------------------
        if load_tsv:
            tsv_path = f"s3a://{bucket}/{data_prefix}{coral_type_name}.tsv"
            try:
                # --------------------------------------------------------------
                # 1) Read the raw TSV **without** a schema so we keep the
                #    original column names exactly as they appear in the file.
                # --------------------------------------------------------------
                df = (
                    spark.read.format("csv")
                    .option("header", "true")
                    .option("sep", "\\t")
                    .option("inferSchema", "false")      # keep everything as string
                    .load(tsv_path)
                )

                # --------------------------------------------------------------
                # 2) Rename NON‑TERM columns to their CDM names.
                #    TERM columns are left untouched for now – they will be split
                #    later.
                # --------------------------------------------------------------
                rename_map: Dict[str, str] = {}
                for f in tdef.get("fields", []):
                    if f.get("scalar_type") == "term":
                        continue                      # keep the original name for now
                    orig = f["name"]
                    new_name = field_to_column_name(f, table_name, type_to_table)
                    rename_map[orig] = new_name

                for orig, new_name in rename_map.items():
                    if orig in df.columns:
                        df = df.withColumnRenamed(orig, new_name)

                # --------------------------------------------------------------
                # 3) Convert any ARRAY columns (now identified by their CDM names)
                #    from the string representation to a real Spark ArrayType.
                # --------------------------------------------------------------
                array_cols = [
                    f.name for f in schema.fields
                    if isinstance(f.dataType, ArrayType)
                ]
                for col in array_cols:
                    if col in df.columns:
                        df = df.withColumn(col, _convert_array_column(col))

                # --------------------------------------------------------------
                # 4) Split TERM columns (original combined column → two cols)
                # --------------------------------------------------------------
                for m in term_mappings:
                    orig = m["orig_name"]
                    if orig in df.columns:
                        df = _split_term_column(df, orig, m["id_col"], m["name_col"])

                # --------------------------------------------------------------
                # 5) Add any missing columns (they will be NULL) so that the final
                #    select can succeed even if a TSV omitted optional fields.
                # --------------------------------------------------------------
                final_order = [f.name for f in schema.fields]
                missing = set(final_order) - set(df.columns)
                for col in missing:
                    # Find the expected datatype from the schema
                    dt = next((f.dataType for f in schema.fields if f.name == col), StringType())
                    df = df.withColumn(col, F.lit(None).cast(dt))

                # --------------------------------------------------------------
                # 6) Re‑order columns to exactly match the CDM schema.
                # --------------------------------------------------------------
                df = df.select(*final_order)

            except Exception as exc:  # pragma: no cover
                logging.warning(
                    f"Could not load TSV for {coral_type_name} from {tsv_path}: {exc}"
                )
                # Fallback: create an empty DataFrame with the final schema
                df = spark.createDataFrame([], schema)
        else:
            # No TSV loading – create an empty DataFrame with the final schema
            df = spark.createDataFrame([], schema)

        # ------------------------------------------------------------------
        # Rename generic columns to be table‑specific
        # ------------------------------------------------------------------
        # ``name`` → <table>_name
        if "name" in df.columns:
            df = df.withColumnRenamed("name", f"{table_name}_name")
        # ``description`` → <table>_description
        if "description" in df.columns:
            df = df.withColumnRenamed("description", f"{table_name}_description")

        # ------------------------------------------------------------------
        # Debug: show schema and a few rows before writing
        # ------------------------------------------------------------------
        logging.info(f"--- Schema for table `{db_name}.{table_name}` ---")
        df.printSchema()
        logging.info(f"--- Sample rows for `{db_name}.{table_name}` (up to 5) ---")
        df.show(5, truncate=False)

        # ------------------------------------------------------------------
        # Drop the table if it already exists (environment‑specific handling)
        # ------------------------------------------------------------------
        spark.sql(f"DROP TABLE IF EXISTS {db_name}.{table_name}")

        # ------------------------------------------------------------------
        # Write the Delta table (no .mode("overwrite") needed)
        # ------------------------------------------------------------------
        df.write.format(fmt).option("comment", table_comment).saveAsTable(
            f"{db_name}.{table_name}"
        )
        logging.info(f"Created table {db_name}.{table_name}")

    # ------------------------------------------------------------------
    # Auxiliary table: sys_typedef
    # ------------------------------------------------------------------
    sys_typedef_df = build_typedefs_dataframe(spark, all_typedef_rows)

    logging.info(f"--- Schema for auxiliary table `{db_name}.sys_typedef` ---")
    sys_typedef_df.printSchema()
    logging.info(f"--- Sample rows for `{db_name}.sys_typedef` (up to 5) ---")
    sys_typedef_df.show(5, truncate=False)

    spark.sql(f"DROP TABLE IF EXISTS {db_name}.sys_typedef")
    sys_typedef_df.write.format(fmt).option("comment", "CORAL type definitions").saveAsTable(f"{db_name}.sys_typedef")
    logging.info(f"Created auxiliary table {db_name}.sys_typedef")

    logging.info("✅ CDM generation complete.")


# ------------------------------------------------------------------
# Execute when run inside a notebook
# ------------------------------------------------------------------
spark = get_spark_session()               # <-- defined elsewhere
db_name = "jmc_coral"
spark.sql(f"USE {db_name}")
generate_cdm(spark, db_name)
        ''')
    return template.replace("__NEEDED_PREFIXES__", repr(sorted(needed_prefixes)))


def render_copy_script(typedef: str, minio_target: str, loaded_obo_files: List[str], tsv_dir: str, type_defs: List[Dict[str, Any]]) -> str:
    """
    Return the contents of ``copy_to_minio.sh``.
    The script creates the target buckets with ``mc mb`` and then copies the
    selected OBO files and any TSV data files.
    """
    lines = [
        "#!/usr/bin/env bash",
        "# Auto‑generated script to copy required OBO and TSV files to MinIO",
        "",
        f'TARGET="{minio_target.rstrip("/")}"',
        'ONTOLOGY_TARGET="${TARGET}/ontologies"',
        'DATA_TARGET="${TARGET}/data"',
        "",
        "# Create target buckets on MinIO (if they do not already exist)",
        "mc mb \"$ONTOLOGY_TARGET\"",
        "mc mb \"$DATA_TARGET\"",
        "",
        "# --------------------------------------------------",
        "# Copy ontology files",
        "# --------------------------------------------------",
    ]
    for src_path in loaded_obo_files:
        lines.append(f'mc cp "{os.path.abspath(src_path)}" "$ONTOLOGY_TARGET/"')
    lines.append("")
    lines.append("# --------------------------------------------------")
    lines.append("# Copy Typedef file")
    lines.append("# --------------------------------------------------")
    lines.append(f'mc cp "{os.path.abspath(typedef)}" "$DATA_TARGET/"')
    lines.append("")
    lines.append("# --------------------------------------------------")
    lines.append("# Copy TSV data files (if they exist)")
    lines.append("# --------------------------------------------------")
    for tdef in type_defs:
        type_name = tdef.get("name")
        if not type_name:
            continue
        tsv_path = os.path.join(tsv_dir, f"{type_name}.tsv")
        if os.path.isfile(tsv_path):
            lines.append(f'mc cp "{os.path.abspath(tsv_path)}" "$DATA_TARGET/"')
        else:
            lines.append(f'# mc cp "{os.path.abspath(tsv_path)}" "$DATA_TARGET/"  # file not found')
    return "\n".join(lines) + "\n"


def render_update_script() -> str:
    """
    Return the source code for ``update_coral_ontologies.py``.
    This script reads OBO files from MinIO (S3) using the workspace helpers.
    """
    return textwrap.dedent('''\
"""
update_coral_ontologies.py

Load all OBO files from the MinIO S3‑A bucket defined by the workspace
and (re)populate the ``sys_oterm`` Delta table.  This script is
intended to be executed inside a Jupyter notebook – no command‑line
arguments are required.
"""

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
    s3a_root = workspace.home_paths[0]                # e.g. "s3a://cdm-lake/users-general-warehouse/jmc"
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
    endpoint = "http://10.58.1.104:9002"

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
                metadata={"comment": "Term identifier, aka CURIE (Primary key)"},
            ),
            StructField(
                "parent_sys_oterm_id",
                StringType(),
                nullable=True,
                metadata={"comment": "Parent term identifier (Foreign key to sys_oterm.sys_oterm_id)"},
            ),
            StructField(
                "sys_oterm_ontology",
                StringType(),
                nullable=False,
                metadata={"comment": "Ontology that each term is from"},
            ),
            StructField(
                "sys_oterm_name",
                StringType(),
                nullable=True,
                metadata={"comment": "Term name"},
            ),
            StructField(
                "sys_oterm_synonyms",
                ArrayType(StringType()),
                nullable=True,
                metadata={"comment": "List of synonyms for a term"},
            ),
            StructField(
                "sys_oterm_definition",
                StringType(),
                nullable=True,
                metadata={"comment": "Term definition"},
            ),
            StructField(
                "sys_oterm_links",
                ArrayType(StringType()),
                nullable=True,
                metadata={"comment": "Indicates that values are links to other tables (Ref) or ontological terms (ORef)"},
            ),
            StructField(
                "sys_oterm_properties",
                MapType(StringType(), StringType()),
                nullable=True,
                metadata={"comment": "Semicolon‑separated map of properties to values for terms that are CORAL microtypes, including scalar data_type, is_valid_data_variable, is_valid_dimension, is_valid_data_variable, is_valid_dimension_variable, is_valid_property, valid_units, and valid_units_parent"},
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
db_name = "jmc_coral"
table_name = "sys_oterm"
spark.sql(f"USE {db_name}")

ontologies = load_all_ontologies_from_minio()
df = build_ontologies_dataframe(spark, ontologies)

# Overwrite the Delta table with the freshly‑loaded data and add a table comment
df.write.format("delta").option("comment", "Ontology terms used in CORAL").saveAsTable(f"{db_name}.{table_name}")
        ''')


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# MAIN DRIVER – generate all artefacts
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate CDM code, a MinIO copy script, and an ontology‑update script from CORAL typedef.json."
    )
    parser.add_argument("--typedef", required=True, help="Path to the CORAL typedef.json file.")
    parser.add_argument(
        "--obo_dir",
        required=True,
        help="Directory containing the OBO ontology files (local filesystem).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the generated Python file (e.g., make_tables.py).",
    )
    parser.add_argument(
        "--minio_target",
        default="cdm-minio/cdm-lake/users-general-warehouse/jmc/data",
        help="Target MinIO bucket path (default: cdm-minio/cdm-lake/users-general-warehouse/jmc/data).",
    )
    parser.add_argument(
        "--shell_output",
        default="copy_to_minio.sh",
        help="Path to the generated shell script (default: copy_to_minio.sh).",
    )
    parser.add_argument(
        "--update_script_output",
        default="update_coral_ontologies.py",
        help="Path to the generated ontology‑update script (default: update_coral_ontologies.py).",
    )
    parser.add_argument(
        "--tsv_dir",
        default=".",
        help="Directory containing TSV files (used for generating copy commands).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Load typedef and discover needed ontology prefixes
    # ------------------------------------------------------------------
    logging.info(f"Reading typedef definitions from {args.typedef}")
    with open(args.typedef, "r", encoding="utf-8") as f:
        typedef_data = json.load(f)

    type_defs = typedef_data.get("system_types", []) + typedef_data.get("static_types", [])

    def extract_ontology_prefixes(type_defs: List[Dict[str, Any]]) -> Set[str]:
        prefixes: Set[str] = set()
        for tdef in type_defs:
            term = tdef.get("term")
            if term:
                prefixes.add(term.split(":")[0])

            for pt in tdef.get("process_types", []):
                prefixes.add(pt.split(":")[0])

            for fld in tdef.get("fields", []):
                for key in ("type_term", "units_term"):
                    term = fld.get(key)
                    if term:
                        prefixes.add(term.split(":")[0])

                constraint = fld.get("constraint")
                if isinstance(constraint, str) and re.match(r"^[A-Z]+:\d+$", constraint):
                    prefixes.add(constraint.split(":")[0])

        prefixes.discard("")
        return prefixes

    needed_prefixes = extract_ontology_prefixes(type_defs)
    logging.info(f"Ontology prefixes referenced in typedef.json: {sorted(needed_prefixes)}")

    # ------------------------------------------------------------------
    # Load ontologies from the local filesystem (select the best file per prefix)
    # ------------------------------------------------------------------
    ontologies, loaded_obo_files = load_ontologies(args.obo_dir, needed_prefixes)

    # ------------------------------------------------------------------
    # 1️⃣  Generate the CDM Python snippet (still expects a local OBO dir)
    # ------------------------------------------------------------------
    make_tables = render_make_tables(needed_prefixes)
    with open(args.output, "w", encoding="utf-8") as out_f:
        out_f.write(make_tables)
    logging.info(f"Generated CDM code to make tables written to {args.output}")

    # ------------------------------------------------------------------
    # 2️⃣  Generate the copy‑to‑MinIO shell script (uses mc mb)
    # ------------------------------------------------------------------
    copy_script = render_copy_script(args.typedef, args.minio_target, loaded_obo_files, args.tsv_dir, type_defs)
    with open(args.shell_output, "w", encoding="utf-8") as sh_f:
        sh_f.write(copy_script)
    try:
        os.chmod(args.shell_output, 0o755)
    except Exception as exc:
        logging.warning(f"Could not set executable flag on {args.shell_output}: {exc}")
    logging.info(f"Generated copy script written to {args.shell_output}")

    # ------------------------------------------------------------------
    # 3️⃣  Generate the ontology‑update script (reads OBO files from MinIO)
    # ------------------------------------------------------------------
    update_script = render_update_script()
    with open(args.update_script_output, "w", encoding="utf-8") as upd_f:
        upd_f.write(update_script)
    try:
        os.chmod(args.update_script_output, 0o755)
    except Exception as exc:
        logging.warning(f"Could not set executable flag on {args.update_script_output}: {exc}")
    logging.info(f"Generated ontology‑update script written to {args.update_script_output}")

    # ------------------------------------------------------------------
    # Final instructions
    # ------------------------------------------------------------------
    logging.info(
        "\nAll artefacts generated successfully.\n"
        f"• Run the shell script to create buckets and copy files to MinIO:\n"
        f"    bash {args.shell_output}\n"
        f"• Paste the generated CDM code ({args.output}) into a notebook and execute it.\n"
        f"• When you need to refresh the ontology table, run:\n"
        f"    spark-submit {args.update_script_output} --db_name cdm --table_name coral_ontologies"
    )


if __name__ == "__main__":
    main()
