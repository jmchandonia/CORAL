#!/usr/bin/env python3
"""
convert_bricks.py

Convert a CORAL NDArray CSV into a TSV file.  The TSV header and the data
rows are derived from an OBO ontology.

Key points
----------
* The CSV sections may appear in any order:
    1. one or more ``values`` lines (often before the ``size`` line)
    2. a ``size`` line (dimension lengths)
    3. any number of ``dmeta`` blocks – a ``dmeta`` line followed by L
       value lines, where L is the length of the referenced dimension
    4. a ``data`` line – everything after this line are ND‑Array rows
* Column names follow the rules you supplied, including the column(s)
  derived from a ``values`` line (e.g. ``relative_abundance_fraction``).
* The columns created from the ``values`` line(s) are always placed **last**
  in the TSV.
* For each data row the script looks up the correct value for every
  dimension‑variable column (using the indices supplied in the row) and
  writes the measurement(s) from the ``values`` line(s) into the trailing
  column(s).  For ORef data types the generated columns are
  ``…_sys_oterm_id`` and ``…_sys_oterm_name``; the script now places the
  OBO identifier in the ``_id`` column and the term name in the
  ``_name`` column (the previous version had them swapped).
* Missing entries are written as ``n/a``.
* No authentication code – it has been removed because it is not needed.
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import csv
import logging
import os
import re
import sys
import warnings
from typing import Dict, List, Tuple, Union

# ----------------------------------------------------------------------
# Suppress noisy warnings (mirrors the original code)
# ----------------------------------------------------------------------
warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", DeprecationWarning)

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)

# ----------------------------------------------------------------------
# 1️⃣  OBO parsing (names, data types, parent relationships)
# ----------------------------------------------------------------------
def _parse_xref(xref: str) -> Union[str, Tuple[str, str], None]:
    """Derive a data‑type from an OBO ``xref`` line.

    * ``Ref:``   → ``sdt_<type>_<column>``
    * ``ORef:``  → ``("sys_oterm_id","sys_oterm_name")``
    """
    if xref.startswith("Ref:"):
        # Example: Ref:DA:0000063.OTU.Name → sdt_otu_name
        parts = xref.split(".")
        if len(parts) >= 2:
            typ = parts[-2].lower()
            col = parts[-1].lower()
            return f"sdt_{typ}_{col}"
    elif xref.startswith("ORef:"):
        return ("sys_oterm_id", "sys_oterm_name")
    return None


def load_obo(
    obo_path: str,
) -> Tuple[
    Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    Dict[str, List[str]],
]:
    """
    Parse an OBO file.

    Returns
    -------
    term_map   : term_id → {"name": str, "data_type": str|tuple|None}
    parent_map : term_id → list[parent_term_id]   (is_a hierarchy)
    """
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]] = {}
    parent_map: Dict[str, List[str]] = {}

    cur_id = cur_name = ""
    cur_data_type: Union[str, Tuple[str, str], None] = None

    with open(obo_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:                     # blank line → finish current term
                if cur_id:
                    term_map[cur_id] = {"name": cur_name, "data_type": cur_data_type}
                    parent_map.setdefault(cur_id, [])
                    cur_id = cur_name = ""
                    cur_data_type = None
                continue

            if line == "[Term]":
                continue
            if line.startswith("id:"):
                cur_id = line.split("id:", 1)[1].strip()
            elif line.startswith("name:"):
                cur_name = line.split("name:", 1)[1].strip()
            elif line.startswith("xref:"):
                cur_data_type = _parse_xref(line.split("xref:", 1)[1].strip())
            elif line.startswith("is_a:"):
                parent_part = line.split("is_a:", 1)[1].strip()
                parent_id = parent_part.split("!", 1)[0].strip().split()[0]
                parent_map.setdefault(cur_id, []).append(parent_id)

    # final term (in case file does not end with a blank line)
    if cur_id:
        term_map[cur_id] = {"name": cur_name, "data_type": cur_data_type}
        parent_map.setdefault(cur_id, [])

    return term_map, parent_map


def is_descendant(
    child_id: str,
    ancestor_id: str,
    parent_map: Dict[str, List[str]],
) -> bool:
    """Return True if *ancestor_id* appears anywhere in the ancestry of *child_id*."""
    if child_id == ancestor_id:
        return True
    visited = set()
    stack = list(parent_map.get(child_id, []))
    while stack:
        cur = stack.pop()
        if cur == ancestor_id:
            return True
        if cur in visited:
            continue
        visited.add(cur)
        stack.extend(parent_map.get(cur, []))
    return False


# ----------------------------------------------------------------------
# 2️⃣  Helper utilities for term handling
# ----------------------------------------------------------------------
_TERM_RE = re.compile(r"""^\s*(?P<name>.+?)\s*<(?P<id>[^>]+)>\s*$""")


def _split_term(term_str: str) -> Tuple[str, str]:
    """Parse ``term name <term_id>`` → (name, id)."""
    m = _TERM_RE.match(term_str)
    if not m:
        return term_str.strip(), ""
    return m.group("name").strip(), m.group("id").strip()


def _normalize(txt: str) -> str:
    """Lower‑case and replace whitespace with '_'."""
    return re.sub(r"\s+", "_", txt.strip().lower())


def _resolve_name(
    csv_name: str,
    term_id: str,
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
) -> str:
    """
    Return the OBO name if the term id exists, otherwise the CSV name.
    Emit a warning when they differ.
    """
    if term_id and term_id in term_map:
        obo_name = term_map[term_id]["name"]
        if csv_name != obo_name:
            logging.warning(
                f"Term ID {term_id}: remapping name from CSV '{csv_name}' "
                f"to OBO '{obo_name}'"
            )
        return obo_name
    return csv_name


# ----------------------------------------------------------------------
# 3️⃣  Column‑name generation (dmeta & values)
# ----------------------------------------------------------------------
def column_names_for_var(
    var: Dict[str, Union[str, List[Dict[str, str]]]],
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    parent_map: Dict[str, List[str]],
    dim_lengths: Dict[int, int],
    is_value_line: bool = False,
) -> Tuple[List[str], Union[str, Tuple[str, str], None]]:
    """
    Produce column name(s) for a variable and return its data type.

    Parameters
    ----------
    var
        dict with keys ``dim_name``, ``dim_id``, ``var_name``, ``var_id``,
        optional ``extra`` (list of ``{'name':…, 'id':…}``).
    is_value_line
        ``True`` when the variable originates from a ``values`` line.
    dim_lengths
        Mapping dimension index → its length (used only for validation).
    """
    # Resolve human‑readable names (prefer OBO name when available)
    dim_name = var.get("dim_name")
    dim_id = var.get("dim_id")
    var_name = var["var_name"]
    var_id = var["var_id"]
    extra = var.get("extra", [])

    if not is_value_line and dim_name is not None:
        dim_name = _resolve_name(dim_name, dim_id, term_map)
    var_name = _resolve_name(var_name, var_id, term_map)

    dim_norm = _normalize(dim_name) if dim_name else ""
    var_norm = _normalize(var_name)

    # Data‑type comes from the *variable* term
    entry = term_map.get(var_id)
    data_type = entry["data_type"] if entry else None

    # --------------------------------------------------------------
    # Should we drop the dimension prefix?
    # --------------------------------------------------------------
    omit_dim = False
    if not is_value_line and data_type is not None and dim_id:
        if is_descendant(var_id, dim_id, parent_map):
            omit_dim = True

    # --------------------------------------------------------------
    # 1️⃣  NULL data type – concatenate all term names on the line
    # --------------------------------------------------------------
    if data_type is None:
        parts: List[str] = []
        if not is_value_line and dim_norm != var_norm:
            parts.append(dim_name)
        parts.append(var_name)
        for extra_term in extra:
            extra_name = _resolve_name(extra_term["name"], extra_term["id"], term_map)
            parts.append(extra_name)
        col_name = "_".join(_normalize(p) for p in parts)
        return [col_name], data_type

    # --------------------------------------------------------------
    # 2️⃣  Tuple data type (ORef) – two columns
    # --------------------------------------------------------------
    if isinstance(data_type, tuple):
        if is_value_line:
            prefix = var_norm
        else:
            if omit_dim or dim_norm == var_norm:
                prefix = var_norm
            else:
                prefix = f"{dim_norm}_{var_norm}"
        return [f"{prefix}_{data_type[0]}", f"{prefix}_{data_type[1]}"], data_type

    # --------------------------------------------------------------
    # 3️⃣  Reference (Ref) – single column
    # --------------------------------------------------------------
    if is_value_line:
        col = data_type
    else:
        if omit_dim or dim_norm == var_norm:
            col = data_type
        else:
            col = f"{dim_norm}_{data_type}"
    return [col], data_type


# ----------------------------------------------------------------------
# 4️⃣  Transform a raw CSV value into the list that fits the column(s)
# ----------------------------------------------------------------------
def extract_values(
    value_str: str,
    data_type: Union[str, Tuple[str, str], None],
) -> List[str]:
    """
    Convert a CSV value into the list of values that should be written to
    the TSV columns.

    * Ref  – keep only the name part (text before ``<``).
    * ORef – return ``[id, name]`` (id first, then name) to match the
      ``*_sys_oterm_id`` and ``*_sys_oterm_name`` column order.
    * null – return the original string unchanged.
    """
    if isinstance(data_type, tuple):
        # ORef → id + name (swap order compared to previous version)
        name, term_id = _split_term(value_str)
        return [term_id, name]

    if data_type is None:
        return [value_str]

    # Ref – keep the name part only
    name, _ = _split_term(value_str)
    return [name]


# ----------------------------------------------------------------------
# 5️⃣  Main conversion routine (single‑pass over the CSV)
# ----------------------------------------------------------------------
def convert(
    csv_path: str,
    out_path: str,
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    parent_map: Dict[str, List[str]],
) -> None:
    """
    Parse the CSV, build the header and write a TSV that contains **all**
    rows after the ``data`` line.

    The processing is done in a single pass:
        * ``values``   → measurement columns (may appear before ``size``)
        * ``size``     → dimension lengths
        * ``dmeta``    → dimension variables + per‑index value block
        * ``data``     → actual ND‑Array rows
    """
    # ------------------------------------------------------------------
    # Containers for the different parts of the header
    # ------------------------------------------------------------------
    dmeta_header: List[str] = []          # columns coming from dmeta blocks
    dmeta_vars: List[Dict] = []           # info needed to fill those columns

    values_header: List[str] = []          # columns coming from values line(s)
    values_vars: List[Dict] = []           # info needed to fill those columns

    dim_lengths: Dict[int, int] = {}      # dimension index → length

    # ------------------------------------------------------------------
    # PASS 1 – read metadata (values, size, dmeta) and build the header
    # ------------------------------------------------------------------
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        for row in reader:
            if not row:
                continue
            token = row[0].strip()

            # --------------------------------------------------------------
            # values line – defines measurement column(s)
            # --------------------------------------------------------------
            if token == "values":
                if len(row) < 2:
                    logging.warning("Malformed values line – skipping")
                    continue
                var_type_raw = row[1].strip()
                var_name, var_id = _split_term(var_type_raw)

                extra_terms: List[Dict[str, str]] = []
                for extra_raw in row[2:]:
                    e_name, e_id = _split_term(extra_raw.strip())
                    extra_terms.append({"name": e_name, "id": e_id})

                var = {
                    "dim_name": None,
                    "dim_id": None,
                    "var_name": var_name,
                    "var_id": var_id,
                    "extra": extra_terms,
                }

                col_names, data_type = column_names_for_var(
                    var, term_map, parent_map, dim_lengths, is_value_line=True
                )
                # keep the column names for later – they will be appended after dmeta columns
                values_header.extend(col_names)

                values_vars.append(
                    {
                        "col_names": col_names,
                        "data_type": data_type,
                    }
                )
                continue

            # --------------------------------------------------------------
            # size line – gives the length of each dimension
            # --------------------------------------------------------------
            if token == "size":
                for idx, val in enumerate(row[1:], start=1):
                    try:
                        dim_lengths[idx] = int(val.strip())
                    except ValueError:
                        logging.error(f"Invalid size value '{val}' for dimension {idx}")
                continue

            # --------------------------------------------------------------
            # dmeta block – dimension variable + its per‑index values
            # --------------------------------------------------------------
            if token == "dmeta":
                if len(row) < 4:
                    logging.warning("Malformed dmeta line – skipping")
                    continue

                dim_idx = int(row[1].strip())
                dim_type_raw = row[2].strip()
                var_type_raw = row[3].strip()

                dim_name, dim_id = _split_term(dim_type_raw)
                var_name, var_id = _split_term(var_type_raw)

                extra_terms: List[Dict[str, str]] = []
                for extra_raw in row[4:]:
                    e_name, e_id = _split_term(extra_raw.strip())
                    extra_terms.append({"name": e_name, "id": e_id})

                var = {
                    "dim_name": dim_name,
                    "dim_id": dim_id,
                    "var_name": var_name,
                    "var_id": var_id,
                    "extra": extra_terms,
                }

                col_names, data_type = column_names_for_var(
                    var, term_map, parent_map, dim_lengths, is_value_line=False
                )
                col_start = len(dmeta_header)
                dmeta_header.extend(col_names)

                # ---- read the value block that follows this dmeta line ----
                block_len = dim_lengths.get(dim_idx, 0)
                values_by_index: List[List[str]] = [None] * block_len

                for i in range(block_len):
                    try:
                        val_row = next(reader)
                    except StopIteration:
                        logging.error(
                            f"Unexpected EOF while reading values for dimension {dim_idx}"
                        )
                        break
                    if not val_row:
                        continue
                    # Expected format: index,value (ignore the index)
                    value_str = val_row[1].strip() if len(val_row) > 1 else ""
                    extracted = extract_values(value_str, data_type)

                    # Pad in case the variable produces fewer columns than expected
                    while len(extracted) < len(col_names):
                        extracted.append("")
                    values_by_index[i] = extracted

                dmeta_vars.append(
                    {
                        "dim_idx": dim_idx,
                        "col_start": col_start,
                        "col_count": len(col_names),
                        "values_by_index": values_by_index,
                        "data_type": data_type,
                    }
                )
                continue

            # --------------------------------------------------------------
            # data marker – end of metadata, start of actual ND‑Array rows
            # --------------------------------------------------------------
            if token == "data":
                # Header is complete; the reader is now positioned at the first
                # data row (the line containing only "data" has been consumed).
                break

            # --------------------------------------------------------------
            # any other line is ignored for header construction
            # --------------------------------------------------------------

        # ------------------------------------------------------------------
        # Assemble the final header: dmeta columns first, values columns last
        # ------------------------------------------------------------------
        header = dmeta_header + values_header

        # Assign column offsets for the values variables (they come after dmeta columns)
        values_start = len(dmeta_header)
        for vv in values_vars:
            vv["col_start"] = values_start
            vv["col_count"] = len(vv["col_names"])
            values_start += vv["col_count"]

        # Number of dimension‑index columns = number of dimensions
        num_dims = len(dim_lengths)

        # ------------------------------------------------------------------
        # Write the TSV (header + all data rows)
        # ------------------------------------------------------------------
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as out_f:
            out_writer = csv.writer(out_f, delimiter="\t")
            out_writer.writerow(header)

            for data_row in reader:
                if not data_row:
                    continue
                if len(data_row) < num_dims + 1:
                    logging.warning(
                        f"Data row has fewer columns than expected (need {num_dims + 1}) – skipping"
                    )
                    continue

                # -------------------- indices --------------------------------
                try:
                    indices = [int(v.strip()) for v in data_row[:num_dims]]
                except ValueError:
                    logging.warning(
                        f"Non‑integer index in row {data_row} – skipping"
                    )
                    continue

                # -------------------- measurement values ----------------------
                measurement_vals = data_row[num_dims:]  # may be more than one

                # start with a row full of “n/a”
                out_row = ["n/a"] * len(header)

                # -------------------- dmeta variables -------------------------
                for dv in dmeta_vars:
                    dim_idx = dv["dim_idx"]
                    idx_val = indices[dim_idx - 1]               # CSV uses 1‑based indices
                    if idx_val < 1 or idx_val > len(dv["values_by_index"]):
                        logging.warning(
                            f"Index {idx_val} out of range for dimension {dim_idx}"
                        )
                        continue
                    vals = dv["values_by_index"][idx_val - 1]    # list of column values
                    if vals is None:
                        continue
                    for offset, v in enumerate(vals):
                        out_row[dv["col_start"] + offset] = v if v != "" else "n/a"

                # -------------------- values line(s) --------------------------
                for vi, vv in enumerate(values_vars):
                    raw_val = (
                        measurement_vals[vi].strip()
                        if vi < len(measurement_vals)
                        else ""
                    )
                    extracted = extract_values(raw_val, vv["data_type"])
                    # Pad for tuple case (two columns)
                    while len(extracted) < vv["col_count"]:
                        extracted.append("")
                    for offset, v in enumerate(extracted):
                        out_row[vv["col_start"] + offset] = v if v != "" else "n/a"

                out_writer.writerow(out_row)

    logging.info(f"TSV written to {out_path}")


# ----------------------------------------------------------------------
# 6️⃣  CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a CORAL NDArray CSV into a TSV file whose header "
            "and data are derived from an OBO ontology."
        )
    )
    parser.add_argument("--obo", required=True, help="Path to the OBO ontology file.")
    parser.add_argument("--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "--out", required=True, help="Path to the TSV file that will be created."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
    )
    args = parser.parse_args()

    if os.path.exists(args.out) and not args.force:
        logging.error(
            f"Output file {args.out} already exists – use --force to overwrite."
        )
        sys.exit(1)

    logging.info("Parsing OBO file …")
    term_map, parent_map = load_obo(args.obo)

    logging.info("Converting CSV to TSV …")
    convert(args.csv, args.out, term_map, parent_map)


if __name__ == "__main__":
    main()
