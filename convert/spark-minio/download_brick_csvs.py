#!/usr/bin/env python3
"""
download_brick_csvs.py

Download every Brick defined in the CORAL catalog as a CSV file.

Usage
-----
    python download_brick_csvs.py \
        --out_dir ./exported_bricks \
        [--host coral-enigma.lbl.gov] \
        [--port 443] \
        [--no-https] \
        [--pubkey /etc/ssl/certs/data_clearinghouse.pub]
        [--force]

Arguments
---------
--out_dir   Directory where CSV files will be written (default: ./exported_bricks).
--host      CORAL host (default: coral-enigma.lbl.gov).
--port      Port number (default: 443).
--no-https  Use HTTP instead of HTTPS.
--pubkey    Path to the public RSA key (default:
            /etc/ssl/certs/data_clearinghouse.pub).
--force     Forces re-download of all bricks
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import base64
import csv
import datetime
import json
import logging
import os
import sys
import warnings

# ----------------------------------------------------------------------
# Third‑party imports
# ----------------------------------------------------------------------
import jwt
import requests
import urllib3
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

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
# 1️⃣  AUTHENTICATION HELPERS
# ----------------------------------------------------------------------
def load_public_key(pubkey_path: str) -> RSA.RsaKey:
    """Load the RSA public key used by the CORAL Data‑Clearinghouse."""
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

    # Encode the timestamp **before** encrypting – required order.
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
# 2️⃣  FETCH LIST OF BRICKS (TSV)
# ----------------------------------------------------------------------
def fetch_brick_ids(base_url: str, headers: dict) -> list[str]:
    """
    Query ``/search`` for Brick records (TSV format) and return the list
    of ``brick_id`` values.
    """
    query = {
        "format": "TSV",
        "raw": True,
        "queryMatch": {
            "category": "DDT_",
            "dataModel": "Brick",
            "dataType": "NDArray",
            "params": [],
        },
    }

    url = f"{base_url.rstrip('/')}/search"
    logging.debug(f"POST {url} – payload: {json.dumps(query)}")
    resp = requests.post(url, headers=headers, json=query, verify=False)

    if resp.status_code != 200:
        logging.error(
            f"Failed to retrieve brick list – HTTP {resp.status_code}: {resp.text}"
        )
        sys.exit(1)

    # Parse TSV response
    tsv_text = resp.text
    reader = csv.DictReader(tsv_text.splitlines(), delimiter="\t")
    if "brick_id" not in reader.fieldnames:
        logging.error("TSV response does not contain a 'brick_id' column.")
        sys.exit(1)

    brick_ids = [row["brick_id"] for row in reader if row.get("brick_id")]
    logging.info(f"Found {len(brick_ids)} brick(s) in the catalog.")
    return brick_ids

# ----------------------------------------------------------------------
# 3️⃣  DOWNLOAD ONE BRICK AS CSV (POST)
# ----------------------------------------------------------------------
def download_brick_csv(
    brick_id: str,
    base_url: str,
    headers: dict,
    out_dir: str,
) -> None:
    """
    POST ``/brick/<brick_id>`` with ``{'format': 'CSV'}`` and write the CSV
    payload to ``<out_dir>/<brick_id>.csv``.
    """
    url = f"{base_url.rstrip('/')}/brick/{brick_id}"
    payload = {"format": "CSV"}
    logging.debug(f"POST {url} – payload: {payload}")

    resp = requests.post(url, headers=headers, json=payload, verify=False)

    if resp.status_code != 200:
        logging.error(
            f"Failed to download CSV for brick {brick_id} – "
            f"HTTP {resp.status_code}: {resp.text}"
        )
        return

    # --------------------------------------------------------------
    # The API returns JSON that contains a `"status": "success"` field
    # and the CSV text (usually under a key like 'data', 'csv', or
    # 'result').  Fall back to raw CSV if the content‑type is not JSON.
    # --------------------------------------------------------------
    content_type = resp.headers.get("Content-Type", "").lower()
    csv_text: str

    if "application/json" in content_type or resp.text.lstrip().startswith("{"):
        try:
            payload_json = resp.json()
        except json.JSONDecodeError:
            logging.error(f"Brick {brick_id}: response is not valid JSON.")
            return

        if payload_json.get("status") != "success":
            logging.error(f"Brick {brick_id}: API reported failure – {payload_json}")
            return

        # Find the CSV payload
        if "res" in payload_json:
            csv_text = payload_json["res"]
        else:
            logging.error(
                f"Brick {brick_id}: JSON response lacks CSV data (keys: {list(payload_json.keys())})"
            )
            return
    else:
        # Assume the body itself is the CSV.
        csv_text = resp.text

    # --------------------------------------------------------------
    # Write CSV to file
    # --------------------------------------------------------------
    out_path = os.path.join(out_dir, f"{brick_id}.csv")
    try:
        with open(out_path, "w", newline="") as f:
            f.write(csv_text)
        logging.info(f"Saved brick {brick_id}")
    except OSError as exc:
        logging.error(f"Could not write CSV for brick {brick_id}: {exc}")

# ----------------------------------------------------------------------
# 4️⃣  MAIN DRIVER
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download all bricks from the CORAL API as CSV files."
    )
    parser.add_argument(
        "--out_dir",
        default="./exported_bricks",
        help="Directory where CSV files will be written (default: ./exported_bricks).",
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
        "--force",
        action="store_true",
        help="Re‑download bricks even if the CSV file already exists.",
    )
    parser.add_argument(
        "--pubkey",
        default="/etc/ssl/certs/data_clearinghouse.pub",
        help="Path to the public RSA key (default: /etc/ssl/certs/data_clearinghouse.pub).",
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Prepare the output directory (this is the final destination)
    # ------------------------------------------------------------------
    os.makedirs(args.out_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Build base URL
    # ------------------------------------------------------------------
    scheme = "http" if args.no_https else "https"
    base_url = f"{scheme}://{args.host}:{args.port}/coral/"

    logging.info(f"Using CORAL endpoint: {base_url}")

    # ------------------------------------------------------------------
    # Load RSA public key and build auth header
    # ------------------------------------------------------------------
    try:
        public_key = load_public_key(args.pubkey)
    except Exception as exc:
        logging.error(f"Unable to load public key: {exc}")
        sys.exit(1)

    headers = build_authorized_headers(public_key)

    # ------------------------------------------------------------------
    # 1️⃣  Retrieve list of brick IDs
    # ------------------------------------------------------------------
    brick_ids = fetch_brick_ids(base_url, headers)

    # ------------------------------------------------------------------
    # 2️⃣  Download each brick as CSV
    # ------------------------------------------------------------------
    for brick_id in brick_ids:
        csv_path = os.path.join(args.out_dir, f"{brick_id}.csv")
        if os.path.isfile(csv_path) and not args.force:
            logging.info(f"Skipping {brick_id}: file already exists ({csv_path})")
            continue
        download_brick_csv(brick_id, base_url, headers, args.out_dir)

    logging.info("All brick CSVs have been generated.")

if __name__ == "__main__":
    main()
