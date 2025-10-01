#!/usr/bin/env python3
"""
download_typedef_tsvs.py

Parse a CORAL ``typedef.json`` file, discover every data‑type name that
appears, download a **JSON** representation of each type from the CORAL
Data‑Clearinghouse API (with ``raw: "True"`` so the server returns the extra
``*_term_name`` / ``*_term_id`` fields for Term‑typed columns), convert the
JSON to a TSV file, and write the TSV to a user‑specified directory.

For every field whose ``scalar_type`` is ``Term`` the TSV column contains the
concatenation of the term name and term id in the form:

    term name <term id>

If only one of the two pieces is present the column contains that piece
alone; if neither is present the cell is left empty.

Requirements
------------
pip install requests pyjwt pycryptodome

Usage
-----
    python download_typedef_tsvs.py \
        --typedef /path/to/typedef.json \
        --out_dir ./tsv_downloads \
        [--host coral-enigma.lbl.gov] \
        [--port 443] \
        [--no-https] \
        [--category SDT_] \
        [--pubkey /etc/ssl/certs/data_clearinghouse.pub]

Arguments
---------
--typedef   Path to the CORAL typedef.json file (required).
--out_dir   Directory where TSV files will be written (default: ./tsv).
--host      CORAL host (default: coral-enigma.lbl.gov).
--port      Port number (default: 443).
--no-https  Use HTTP instead of HTTPS.
--category  Category to request from the API (default: SDT_).
--pubkey    Path to the public RSA key (default:
            /etc/ssl/certs/data_clearinghouse.pub).
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import json
import os
import sys
import warnings
import datetime
import base64
import logging
import csv
from typing import Any, Dict, List, Tuple, Set

# ----------------------------------------------------------------------
# Third‑party imports
# ----------------------------------------------------------------------
import requests
import urllib3
import jwt
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# ----------------------------------------------------------------------
# Suppress noisy warnings (mirrors the original unittest)
# ----------------------------------------------------------------------
warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", DeprecationWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 1️⃣  AUTHENTICATION HELPERS
# ----------------------------------------------------------------------
def load_public_key(pubkey_path: str) -> RSA.RsaKey:
    """Load the public RSA key used by the Data‑Clearinghouse."""
    if not os.path.isfile(pubkey_path):
        raise FileNotFoundError(f"Public key file not found: {pubkey_path}")

    with open(pubkey_path, "rb") as f:
        key_data = f.read()
    return RSA.import_key(key_data)


def build_authorized_headers(public_key: RSA.RsaKey) -> dict:
    """Create the ``Authorization`` header required by the CORAL API."""
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    payload = {
        "exp": now + datetime.timedelta(minutes=120),
        "iat": now,
    }

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

    return {
        "Authorization": f"JwToken {token}",
        "content-type": "application/json",
    }


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 2️⃣  TYPEDEF PARSING & CDM‑SCHEMA HELPERS
# ----------------------------------------------------------------------
def extract_type_definitions(typedef_path: str) -> Dict[str, Dict[str, Any]]:
    """Load ``typedef.json`` and return a mapping ``{type_name: type_definition}``."""
    if not os.path.isfile(typedef_path):
        raise FileNotFoundError(f"typedef.json not found: {typedef_path}")

    with open(typedef_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    type_defs: Dict[str, Dict[str, Any]] = {}
    for entry in data.get("system_types", []):
        name = entry.get("name")
        if name:
            type_defs[name] = entry
    for entry in data.get("static_types", []):
        name = entry.get("name")
        if name:
            type_defs[name] = entry

    logging.info(f"Found {len(type_defs)} distinct data‑type(s) in typedef.json.")
    return type_defs


def parse_fk(fk_str: str) -> Tuple[str, bool]:
    """Parse a foreign‑key descriptor. Returns (referenced_table, is_array)."""
    is_array = False
    if fk_str.startswith("[") and fk_str.endswith("]"):
        is_array = True
        fk_str = fk_str[1:-1].strip()
    table_name = fk_str.split(".", 1)[0]
    return table_name, is_array


def fk_column_name(table_name: str, is_array: bool) -> str:
    """Return the CDM column name for a foreign key."""
    base = table_name.lower()
    return f"{base}_ids" if is_array else f"{base}_id"


def field_to_column_name(field: Dict[str, Any]) -> str:
    """Convert a CORAL field definition to the column name used by the CDM."""
    orig_name = field.get("name")
    if field.get("PK", False):
        return "id"
    if field.get("UPK", False):
        return "name"
    fk_str = field.get("FK")
    if fk_str:
        ref_table, is_array = parse_fk(fk_str)
        return fk_column_name(ref_table, is_array)
    return orig_name


def get_column_names_for_type(type_def: Dict[str, Any]) -> List[str]:
    """
    Compute the ordered list of column names that the CORAL API will emit for
    ``type_def`` (CDM ordering: PK → fields → name if UPK).
    """
    fields = type_def.get("fields", [])
    column_names: List[str] = []

    has_pk = False
    has_upk = False

    for fld in fields:
        col_name = field_to_column_name(fld)
        column_names.append(col_name)

        if fld.get("PK", False):
            has_pk = True
        if fld.get("UPK", False):
            has_upk = True

    if not has_pk:
        column_names.insert(0, "id")
    if has_upk and "name" not in column_names:
        column_names.append("name")

    return column_names


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 3️⃣  VALUE FORMATTING (arrays / objects without quotes)
# ----------------------------------------------------------------------
def format_value(val: Any) -> str:
    """Render a JSON value for TSV output (no quoting of strings)."""
    if val is None:
        return ""

    if isinstance(val, list):
        inner = ", ".join(format_value(item) for item in val)
        return f"[{inner}]"

    if isinstance(val, dict):
        inner = ", ".join(f"{k}: {format_value(v)}" for k, v in val.items())
        return f"{{{inner}}}"

    return str(val)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 4️⃣  DOWNLOAD JSON → CONVERT → WRITE TSV (Term handling)
# ----------------------------------------------------------------------
def download_json_and_write_tsv(
    datatype: str,
    type_def: Dict[str, Any],
    base_url: str,
    headers: dict,
    out_dir: str,
    category: str = "SDT_",
) -> None:
    """
    Download the JSON representation of ``datatype`` from the CORAL API,
    convert it to a TSV file that contains **all** columns defined in the
    typedef (missing values become empty strings), and write the TSV to
    ``out_dir/<datatype>.tsv``.

    For fields whose ``scalar_type`` is ``Term`` the server (when called
    with ``raw: "True"``) returns two extra keys:
        * ``<field>_term_name``
        * ``<field>_term_id``

    In the TSV these two pieces of information are merged into a single
    column formatted as ``term name <term id>``.
    """
    # ------------------------------------------------------------------
    # 1️⃣  Build the request payload (JSON format, raw="True")
    # ------------------------------------------------------------------
    query = {
        "format": "JSON",
        "raw": True,
        "queryMatch": {
            "category": category,
            "dataModel": datatype,
            "dataType": datatype,
            "params": [],
        },
    }

    url = f"{base_url.rstrip('/')}/search"
    logging.debug(f"POST {url} – payload: {json.dumps(query)}")
    response = requests.post(url, headers=headers, json=query, verify=False)

    if response.status_code != 200:
        logging.error(
            f"Failed to download JSON for '{datatype}'. "
            f"HTTP {response.status_code}: {response.text}"
        )
        return

    # ------------------------------------------------------------------
    # 2️⃣  Parse the JSON payload
    # ------------------------------------------------------------------
    try:
        payload = json.loads(response.text)
    except json.JSONDecodeError as exc:
        logging.error(f"Invalid JSON returned for '{datatype}': {exc}")
        return

    # The API sometimes wraps the list of records inside a dict.
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            records = payload["data"]
        elif isinstance(payload.get("results"), list):
            records = payload["results"]
        else:
            records = [payload]          # treat as a single record
    elif isinstance(payload, list):
        records = payload
    else:
        logging.error(f"Unexpected JSON structure for '{datatype}'.")
        return

    # ------------------------------------------------------------------
    # 3️⃣  Determine column order and which columns are Term‑typed
    # ------------------------------------------------------------------
    column_names = get_column_names_for_type(type_def)

    # Mapping: CDM column name -> original field name (only for Term fields)
    term_columns: Dict[str, str] = {}
    for fld in type_def.get("fields", []):
        if fld.get("scalar_type") == "term":
            col_name = field_to_column_name(fld)
            term_columns[col_name] = fld.get("name")   # original field name

    # ------------------------------------------------------------------
    # 4️⃣  Write TSV
    # ------------------------------------------------------------------
    out_path = os.path.join(out_dir, f"{datatype}.tsv")
    with open(out_path, "w", newline="", encoding="utf-8") as tsv_file:
        writer = csv.writer(tsv_file, delimiter="\t", quoting=csv.QUOTE_MINIMAL)

        # Header row
        writer.writerow(column_names)

        # Data rows
        for rec in records:
            row: List[str] = []
            for col in column_names:
                # ----- Term‑type handling -----
                if col in term_columns:
                    orig = term_columns[col]               # e.g. "material"
                    term_name = rec.get(f"{orig}_term_name", "")
                    term_id   = rec.get(f"{orig}_term_id", "")

                    if term_name and term_id:
                        combined = f"{term_name} <{term_id}>"
                    elif term_name:
                        combined = term_name
                    elif term_id:
                        combined = f"<{term_id}>"
                    else:
                        combined = ""

                    row.append(combined)
                else:
                    # Regular scalar / list / dict handling (no quotes)
                    raw_val = rec.get(col, "")
                    row.append(format_value(raw_val))
            writer.writerow(row)

    logging.info(f"Saved TSV for '{datatype}' → {out_path}")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# 5️⃣  MAIN DRIVER
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description=(
            "Parse typedef.json, download JSON (raw=\"True\") for each data type "
            "from the CORAL API, convert to TSV (Term fields merged) and write "
            "to disk."
        )
    )
    parser.add_argument(
        "--typedef",
        required=True,
        help="Path to the CORAL typedef.json file.",
    )
    parser.add_argument(
        "--out_dir",
        default="./tsv",
        help="Directory where TSV files will be written (default: ./tsv).",
    )
    parser.add_argument(
        "--host",
        default="coral-enigma.lbl.gov",
        help="CORAL host (default: coral-enigma.lbl.gov).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=443,
        help="Port number (default: 443).",
    )
    parser.add_argument(
        "--no-https",
        action="store_true",
        help="Use HTTP instead of HTTPS.",
    )
    parser.add_argument(
        "--category",
        default="SDT_",
        help="Category to request from the API (default: SDT_).",
    )
    parser.add_argument(
        "--pubkey",
        default="/etc/ssl/certs/data_clearinghouse.pub",
        help="Path to the public RSA key (default: /etc/ssl/certs/data_clearinghouse.pub).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Prepare output directory
    # ------------------------------------------------------------------
    os.makedirs(args.out_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Build the base URL (mirrors the unittest setUpClass logic)
    # ------------------------------------------------------------------
    scheme = "http" if args.no_https else "https"
    base_url = f"{scheme}://{args.host}:{args.port}/coral/"

    logging.info(f"Using CORAL endpoint: {base_url}")

    # ------------------------------------------------------------------
    # Load the public RSA key and build the auth header
    # ------------------------------------------------------------------
    try:
        public_key = load_public_key(args.pubkey)
    except Exception as exc:
        logging.error(f"Unable to load public key: {exc}")
        sys.exit(1)

    headers = build_authorized_headers(public_key)

    # ------------------------------------------------------------------
    # Parse typedef.json and build a map {type_name: type_definition}
    # ------------------------------------------------------------------
    try:
        type_defs = extract_type_definitions(args.typedef)
    except Exception as exc:
        logging.error(f"Failed to read typedef.json: {exc}")
        sys.exit(1)

    if not type_defs:
        logging.warning("No data‑type definitions found – exiting.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Download JSON for each type, convert to TSV, and write the file
    # ------------------------------------------------------------------
    for datatype, type_def in sorted(type_defs.items()):
        logging.info(f"Processing data type: {datatype}")
        download_json_and_write_tsv(
            datatype=datatype,
            type_def=type_def,
            base_url=base_url,
            headers=headers,
            out_dir=args.out_dir,
            category=args.category,
        )

    logging.info("All TSV files have been generated.")


if __name__ == "__main__":
    main()
