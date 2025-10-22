#!/usr/bin/env python3
"""
Convert a CORAL NDArray CSV into a TSV file.

Features
--------
* Handles optional typedef.json – if a static type has a ``preferred_name``
  the CDM table and every foreign‑key column that contains that name are
  renamed.
* Supports CSV files **with** and **without** a ``values`` line.
  • When there is no ``values`` line the first‑dimension variables are
    treated as measurement columns and rows that share the same indices
    for dimensions 2…N are merged.
* Allows missing values in a ``dmeta`` block: only rows whose first field
  is numeric are parsed; the block ends when a non‑numeric first field is
  encountered.  Missing indices are left empty (not "n/a").
* For **Ref** and **ORef** variables the column name includes any
  extra fields (columns 5 + on the ``dmeta`` line) when present – the same
  as for null‑type variables.  When no extra fields are present the column
  name is simply the data‑type (e.g. ``sdt_taxon_name``) for Ref or the
  variable name with data type suffix for ORef (e.g.
  ``sequence_type_sys_oterm_id``/``sequence_type_sys_oterm_name``).
* Emits a warning when a variable has a null data type but the value looks
  like ``term name <term id>``.
* Supports multiple OBO files – terms from all files are merged.
"""

# ----------------------------------------------------------------------
# Standard‑library imports
# ----------------------------------------------------------------------
import argparse
import csv
import json
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
    """Parse an OBO file."""
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


def load_multiple_obos(
    obo_paths: List[str],
) -> Tuple[
    Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    Dict[str, List[str]],
]:
    """Parse multiple OBO files and merge their term and parent maps."""
    merged_term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]] = {}
    merged_parent_map: Dict[str, List[str]] = {}

    for obo_path in obo_paths:
        logging.info(f"Parsing OBO file: {obo_path}")
        term_map, parent_map = load_obo(obo_path)
        
        # Merge term_map
        for term_id, term_data in term_map.items():
            if term_id in merged_term_map:
                # Check for conflicts
                existing = merged_term_map[term_id]
                if existing["name"] != term_data["name"]:
                    logging.warning(
                        f"Term ID {term_id} has conflicting names: "
                        f"'{existing['name']}' vs '{term_data['name']}'. "
                        f"Keeping first occurrence."
                    )
                if existing["data_type"] != term_data["data_type"]:
                    logging.warning(
                        f"Term ID {term_id} has conflicting data types. "
                        f"Keeping first occurrence."
                    )
            else:
                merged_term_map[term_id] = term_data
        
        # Merge parent_map
        for term_id, parents in parent_map.items():
            if term_id in merged_parent_map:
                # Merge parent lists, avoiding duplicates
                existing_parents = set(merged_parent_map[term_id])
                new_parents = set(parents)
                merged_parent_map[term_id] = list(existing_parents | new_parents)
            else:
                merged_parent_map[term_id] = parents
    
    logging.info(
        f"Loaded {len(merged_term_map)} terms from {len(obo_paths)} OBO file(s)"
    )
    return merged_term_map, merged_parent_map


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
    """Return the OBO name if the term id exists, otherwise the CSV name."""
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
# 3️⃣  Typedef handling (preferred names)
# ----------------------------------------------------------------------
def load_typedef(typedef_path: str) -> Dict[str, str]:
    """Load typedef.json and return a mapping ``old_name → preferred_name``."""
    try:
        with open(typedef_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read typedef file '{typedef_path}': {e}")
        return {}

    mapping: Dict[str, str] = {}
    for st in data.get("static_types", []):
        name = st.get("name", "").lower()
        pref = st.get("preferred_name")
        if pref:
            mapping[name] = pref.lower()
        else:
            mapping[name] = name
    return mapping


def apply_type_mapping(col_names: List[str], type_map: Dict[str, str]) -> List[str]:
    """Replace any token in a column name that matches a static‑type name."""
    if not type_map:
        return col_names
    new_cols: List[str] = []
    for col in col_names:
        parts = col.split("_")
        parts = [type_map.get(p, p) for p in parts]
        new_cols.append("_".join(parts))
    return new_cols


# ----------------------------------------------------------------------
# 4️⃣  Column‑name generation (dmeta & values)
# ----------------------------------------------------------------------
def column_names_for_var(
    var: Dict[str, Union[str, List[Dict[str, str]]]],
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    parent_map: Dict[str, List[str]],
    dim_lengths: Dict[int, int],
    is_value_line: bool = False,
    type_map: Dict[str, str] = None,
) -> Tuple[List[str], Union[str, Tuple[str, str], None]]:
    """
    Produce column name(s) for a variable and return its data type.

    ``type_map`` is the optional preferred‑name mapping from ``typedef.json``.
    """
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

    entry = term_map.get(var_id)
    data_type = entry["data_type"] if entry else None

    # --------------------------------------------------------------
    # Should we drop the dimension prefix?
    # --------------------------------------------------------------
    omit_dim = False
    if not is_value_line and data_type is not None and dim_id:
        # Omit the dimension prefix only when the variable is the same
        # or a descendant of the dimension term.
        if is_descendant(var_id, dim_id, parent_map) or var_id == dim_id:
            omit_dim = True

    # --------------------------------------------------------------
    # Helper that builds the prefix used for Ref/ORef column names
    # --------------------------------------------------------------
    def _build_prefix() -> str:
        parts: List[str] = []
        if not is_value_line:
            if not omit_dim and dim_norm:
                parts.append(dim_norm)
            if var_norm and (dim_norm != var_norm):
                parts.append(var_norm)
        for extra_term in extra:
            extra_name = _resolve_name(extra_term["name"], extra_term["id"], term_map)
            parts.append(_normalize(extra_name))
        return "_".join(parts)

    # ------------------------------------------------------------------
    # 1️⃣  NULL data type – concatenate all term names on the line
    # ------------------------------------------------------------------
    if data_type is None:
        parts: List[str] = []
        if not is_value_line and dim_norm != var_norm:
            parts.append(dim_name)
        parts.append(var_name)
        for extra_term in extra:
            extra_name = _resolve_name(extra_term["name"], extra_term["id"], term_map)
            parts.append(extra_name)
        col_name = "_".join(_normalize(p) for p in parts)
        col_names = [col_name]
        col_names = apply_type_mapping(col_names, type_map or {})
        return col_names, data_type

    # ------------------------------------------------------------------
    # 2️⃣  Tuple data type (ORef) – two columns
    # ------------------------------------------------------------------
    if isinstance(data_type, tuple):
        if is_value_line:
            prefix = var_norm
        else:
            # Only include extra fields if they exist
            if extra:
                prefix = _build_prefix()
            else:
                # No extra fields: just use variable name (and dimension if applicable)
                parts: List[str] = []
                if not omit_dim and dim_norm:
                    parts.append(dim_norm)
                if var_norm and (dim_norm != var_norm):
                    parts.append(var_norm)
                prefix = "_".join(parts) if parts else var_norm
        
        col_names = [f"{prefix}_{data_type[0]}", f"{prefix}_{data_type[1]}"]
        col_names = apply_type_mapping(col_names, type_map or {})
        return col_names, data_type

    # ------------------------------------------------------------------
    # 3️⃣  Reference (Ref) – single column
    # ------------------------------------------------------------------
    if is_value_line:
        col_name = data_type
    else:
        # Only include extra fields if they exist
        if extra:
            prefix = _build_prefix()
            col_name = f"{prefix}_{data_type}"
        else:
            # No extra fields: just use the data type
            col_name = data_type
    
    col_names = [col_name]
    col_names = apply_type_mapping(col_names, type_map or {})
    return col_names, data_type


# ----------------------------------------------------------------------
# 5️⃣  Transform a raw CSV value into the list that fits the column(s)
# ----------------------------------------------------------------------
def extract_values(
    value_str: str,
    data_type: Union[str, Tuple[str, str], None],
) -> List[str]:
    """
    Convert a CSV value into the list of values that should be written to
    the TSV columns.

    * Ref  – keep only the name part (text before ``<``).
    * ORef – return ``[id, name]`` (identifier first, then term name).
    * null – return the original string unchanged **but** emit a warning
      if the value looks like ``term name <term id>``.
    """
    if isinstance(data_type, tuple):
        name, term_id = _split_term(value_str)
        return [term_id, name]          # id first, then name

    if data_type is None:
        if value_str and _TERM_RE.match(value_str):
            logging.warning(
                f"Value '{value_str}' appears to be a term '<name> <id>' "
                f"but the variable has a null data type."
            )
        return [value_str]

    # Ref – keep the name part only
    name, _ = _split_term(value_str)
    return [name]


# ----------------------------------------------------------------------
# 6️⃣  Main conversion routine (single‑pass over the CSV)
# ----------------------------------------------------------------------
def convert(
    csv_path: str,
    out_path: str,
    term_map: Dict[str, Dict[str, Union[str, Tuple[str, str], None]]],
    parent_map: Dict[str, List[str]],
    type_map: Dict[str, str],
) -> None:
    """
    Parse the CSV, build the header and write a TSV that contains **all**
    rows after the ``data`` line.

    The processing is done in a single pass:
        * ``values``   – measurement columns (may appear before ``size``)
        * ``size``     – dimension lengths
        * ``dmeta``    – dimension variables + per‑index value block
        * ``data``     – actual ND‑Array rows (merged when no ``values`` line)
    """
    # ------------------------------------------------------------------
    # Containers for the different parts of the header
    # ------------------------------------------------------------------
    dmeta_header: List[str] = []          # columns from dmeta blocks (dim > 1)
    dmeta_vars: List[Dict] = []           # info needed to fill those columns

    values_header: List[str] = []          # columns that come from ``values`` lines
    values_vars: List[Dict] = []           # info for real ``values`` lines

    first_dim_vars: Dict[int, Dict] = {}   # first‑dimension variable → column info
    dim_lengths: Dict[int, int] = {}       # dimension index → length

    has_values_line = False                # true if a ``values`` line was seen

    # ------------------------------------------------------------------
    # Helper: read the next row (or None) from the CSV iterator
    # ------------------------------------------------------------------
    def _next_row(it):
        try:
            return next(it)
        except StopIteration:
            return None

    # ------------------------------------------------------------------
    # PASS 1 – read metadata (values, size, dmeta) and build the header
    # ------------------------------------------------------------------
    with open(csv_path, newline="", encoding="utf-8") as f:
        it = csv.reader(f)
        row = _next_row(it)

        while row is not None:
            token = row[0].strip()

            # --------------------------------------------------------------
            # values line – defines measurement column(s)
            # --------------------------------------------------------------
            if token == "values":
                if len(row) < 2:
                    logging.warning("Malformed values line – skipping")
                    row = _next_row(it)
                    continue
                has_values_line = True

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
                    var, term_map, parent_map, dim_lengths,
                    is_value_line=True, type_map=type_map
                )
                col_start = len(values_header)
                values_header.extend(col_names)

                values_vars.append(
                    {
                        "col_start": col_start,
                        "col_count": len(col_names),
                        "data_type": data_type,
                        "col_names": col_names,
                    }
                )
                row = _next_row(it)
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
                row = _next_row(it)
                continue

            # --------------------------------------------------------------
            # dmeta block – dimension variable + its per‑index values
            # --------------------------------------------------------------
            if token == "dmeta":
                if len(row) < 4:
                    logging.warning("Malformed dmeta line – skipping")
                    row = _next_row(it)
                    continue

                dim_idx = int(row[1].strip())
                dim_type_raw = row[2].strip()
                var_type_raw = row[3].strip()

                # ----------------------------------------------------------
                # Special case: first dimension & no explicit values line
                # ----------------------------------------------------------
                if dim_idx == 1 and not has_values_line:
                    # Following lines define measurement columns.
                    while True:
                        next_row = _next_row(it)
                        if next_row is None:
                            row = None
                            break
                        if not next_row:
                            continue
                        first_field = next_row[0].strip()
                        if first_field.isdigit():
                            dim1_index = int(first_field)
                            var_type_raw = next_row[1].strip() if len(next_row) > 1 else ""
                            var_name, var_id = _split_term(var_type_raw)

                            extra_terms: List[Dict[str, str]] = []
                            for extra_raw in next_row[2:]:
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
                                var, term_map, parent_map, dim_lengths,
                                is_value_line=True, type_map=type_map
                            )
                            col_start = len(values_header)
                            values_header.extend(col_names)

                            first_dim_vars[dim1_index] = {
                                "col_start": col_start,
                                "col_count": len(col_names),
                                "data_type": data_type,
                            }
                            continue
                        else:
                            # start of next section
                            row = next_row
                            break
                    # skip normal dmeta handling for dim 1
                    continue

                # ----------------------------------------------------------
                # Normal dmeta handling (dimensions >1 or when values line exists)
                # ----------------------------------------------------------
                dim_name, dim_id = _split_term(dim_type_raw)
                var_name, var_id = _split_term(var_type_raw)

                # Extract extra terms from column 5 onwards (index 4+)
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
                    var, term_map, parent_map, dim_lengths,
                    is_value_line=False, type_map=type_map
                )
                col_start = len(dmeta_header)
                dmeta_header.extend(col_names)

                # ---- read the value block that follows this dmeta line ----
                block_len = dim_lengths.get(dim_idx, 0)
                values_by_index: List[List[str]] = [None] * block_len

                # read block – stop when first field is not numeric
                while True:
                    next_row = _next_row(it)
                    if next_row is None:
                        break
                    if not next_row:
                        continue
                    first_field = next_row[0].strip()
                    if first_field.isdigit():
                        idx = int(first_field)
                        if 1 <= idx <= block_len:
                            value_str = (
                                next_row[1].strip()
                                if len(next_row) > 1
                                else ""
                            )
                            extracted = extract_values(value_str, data_type)
                            while len(extracted) < len(col_names):
                                extracted.append("")
                            values_by_index[idx - 1] = extracted
                        else:
                            logging.warning(
                                f"Index {idx} out of range for dimension {dim_idx}"
                            )
                        continue
                    else:
                        # start of a new section
                        row = next_row
                        break

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
                # Header is complete; iterator now points to first data row.
                break

            # --------------------------------------------------------------
            # any other line is ignored for header construction
            # --------------------------------------------------------------
            row = _next_row(it)

        # ------------------------------------------------------------------
        # Assemble final header
        # ------------------------------------------------------------------
        header = dmeta_header + values_header

        # Adjust column offsets for the values segment
        values_offset_base = len(dmeta_header)
        for vv in values_vars:
            vv["col_start"] = values_offset_base + vv["col_start"]
            vv["col_count"] = len(vv["col_names"])

        for fd in first_dim_vars.values():
            fd["col_start"] = values_offset_base + fd["col_start"]
            # col_count already correct

        num_dims = len(dim_lengths)   # number of index columns

        # ------------------------------------------------------------------
        # Write the TSV (header + data rows)
        # ------------------------------------------------------------------
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as out_f:
            out_writer = csv.writer(out_f, delimiter="\t")
            out_writer.writerow(header)

            # --------------------------------------------------------------
            # CASE A – no explicit ``values`` line → merge rows on dimensions 2..N
            # --------------------------------------------------------------
            if not has_values_line:
                merged_rows: Dict[Tuple[int, ...], List[str]] = {}

                for data_row in it:
                    if not data_row:
                        continue
                    if len(data_row) < num_dims + 1:
                        logging.warning(
                            f"Data row has fewer columns than expected (need {num_dims + 1}) – skipping"
                        )
                        continue

                    try:
                        indices = [int(v.strip()) for v in data_row[:num_dims]]
                    except ValueError:
                        logging.warning(
                            f"Non‑integer index in row {data_row} – skipping"
                        )
                        continue

                    key = tuple(indices[1:])   # dimensions 2..N

                    if key not in merged_rows:
                        out_row = [""] * len(header)

                        # Fill dmeta columns (same for all rows with this key)
                        for dv in dmeta_vars:
                            dim_idx = dv["dim_idx"]
                            idx_val = indices[dim_idx - 1]
                            if idx_val < 1 or idx_val > len(dv["values_by_index"]):
                                logging.warning(
                                    f"Index {idx_val} out of range for dimension {dim_idx}"
                                )
                                continue
                            vals = dv["values_by_index"][idx_val - 1]
                            if vals is None:
                                continue
                            for off, v in enumerate(vals):
                                out_row[dv["col_start"] + off] = v
                        merged_rows[key] = out_row
                    else:
                        out_row = merged_rows[key]

                    first_idx = indices[0]
                    fd = first_dim_vars.get(first_idx)
                    if fd:
                        measurement_val = (
                            data_row[num_dims].strip()
                            if len(data_row) > num_dims
                            else ""
                        )
                        extracted = extract_values(measurement_val, fd["data_type"])
                        while len(extracted) < fd["col_count"]:
                            extracted.append("")
                        for off, v in enumerate(extracted):
                            out_row[fd["col_start"] + off] = v

                for out_row in merged_rows.values():
                    out_writer.writerow(out_row)

            # --------------------------------------------------------------
            # CASE B – normal case (explicit ``values`` line present)
            # --------------------------------------------------------------
            else:
                for data_row in it:
                    if not data_row:
                        continue
                    if len(data_row) < num_dims + 1:
                        logging.warning(
                            f"Data row has fewer columns than expected (need {num_dims + 1}) – skipping"
                        )
                        continue

                    try:
                        indices = [int(v.strip()) for v in data_row[:num_dims]]
                    except ValueError:
                        logging.warning(
                            f"Non‑integer index in row {data_row} – skipping"
                        )
                        continue

                    measurement_vals = data_row[num_dims:]   # may be more than one

                    out_row = [""] * len(header)

                    # dmeta columns
                    for dv in dmeta_vars:
                        dim_idx = dv["dim_idx"]
                        idx_val = indices[dim_idx - 1]
                        if idx_val < 1 or idx_val > len(dv["values_by_index"]):
                            logging.warning(
                                f"Index {idx_val} out of range for dimension {dim_idx}"
                            )
                            continue
                        vals = dv["values_by_index"][idx_val - 1]
                        if vals is None:
                            continue
                        for off, v in enumerate(vals):
                            out_row[dv["col_start"] + off] = v

                    # values columns (explicit)
                    for vi, vv in enumerate(values_vars):
                        raw_val = (
                            measurement_vals[vi].strip()
                            if vi < len(measurement_vals)
                            else ""
                        )
                        extracted = extract_values(raw_val, vv["data_type"])
                        while len(extracted) < vv["col_count"]:
                            extracted.append("")
                        for off, v in enumerate(extracted):
                            out_row[vv["col_start"] + off] = v

                    out_writer.writerow(out_row)

    logging.info(f"TSV written to {out_path}")


# ----------------------------------------------------------------------
# 7️⃣  CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a CORAL NDArray CSV into a TSV file whose header and data "
            "are derived from an OBO ontology."
        )
    )
    parser.add_argument(
        "--obo",
        required=True,
        nargs='+',
        help="Path(s) to one or more OBO ontology files."
    )
    parser.add_argument("--csv", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "--out", required=True, help="Path to the TSV file that will be created."
    )
    parser.add_argument(
        "--typedef",
        required=False,
        help="Path to typedef.json file containing preferred static type names.",
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

    logging.info("Parsing OBO file(s) …")
    term_map, parent_map = load_multiple_obos(args.obo)

    # ------------------------------------------------------------------
    # Load typedef.json (if supplied) and create a preferred‑name map
    # ------------------------------------------------------------------
    type_map: Dict[str, str] = {}
    if args.typedef:
        logging.info(f"Loading typedef file '{args.typedef}' …")
        type_map = load_typedef(args.typedef)
        if type_map:
            logging.info(f"Preferred‑name mapping loaded for {len(type_map)} static types.")
        else:
            logging.warning("Typedef file loaded but no preferred_name mappings found.")

    logging.info("Converting CSV to TSV …")
    convert(args.csv, args.out, term_map, parent_map, type_map)


if __name__ == "__main__":
    main()
