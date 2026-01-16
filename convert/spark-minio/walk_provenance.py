# --------------------------------------------------------------
# 0️⃣  Imports & Spark session
# --------------------------------------------------------------
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import ArrayType, StringType
import re

spark = get_spark_session();

# Use the enigma_coral database
spark.sql("USE enigma_coral")

# --------------------------------------------------------------
# 1️⃣  Auto-discover all sdt_*, ddt_ndarray, and sys_* tables
# --------------------------------------------------------------
def discover_tables():
    """
    Return a list of table names in the current database that match
    sdt_*, ddt_ndarray, or sys_* patterns.
    Excludes ddt_brick* tables (they contain data, not metadata).
    """
    tables_df = spark.sql("SHOW TABLES")
    all_tables = [row.tableName for row in tables_df.collect()]
    
    matching_tables = []
    for t in all_tables:
        # Include sdt_* tables
        if t.startswith('sdt_'):
            matching_tables.append(t)
        # Include sys_* tables
        elif t.startswith('sys_'):
            matching_tables.append(t)
        # Include ddt_ndarray but NOT ddt_brick* tables
        elif t == 'ddt_ndarray':
            matching_tables.append(t)
    
    return matching_tables

# --------------------------------------------------------------
# 2️⃣  Load reference tables dynamically
# --------------------------------------------------------------
def load_lookup(table_name: str):
    """
    Return two dicts: {id → name} and {name → id}.
    Assumes columns are <table>_id and <table>_name.
    Returns ({}, {}) if the table can't be read or doesn't have those columns.
    """
    try:
        df = spark.table(table_name)
        columns = df.columns
        
        # Expected column names based on table name
        id_col = f"{table_name}_id"
        name_col = f"{table_name}_name"
        
        # Check if both columns exist
        if id_col not in columns or name_col not in columns:
            print(f"⚠️  Table '{table_name}' missing {id_col} or {name_col}, skipping")
            return {}, {}
        
        # Collect the mappings
        rows = df.select(id_col, name_col).collect()
        id_to_name = {row[id_col]: row[name_col] for row in rows}
        name_to_id = {row[name_col]: row[id_col] for row in rows}
        
        print(f"✅ Loaded {len(id_to_name)} entries from '{table_name}'")
        return id_to_name, name_to_id
    
    except Exception as e:
        print(f"⚠️  Could not load lookup for '{table_name}': {e}")
        return {}, {}

# Build registries for all discovered tables
print("\n--- Discovering and loading tables ---")
discovered_tables = discover_tables()
print(f"Found {len(discovered_tables)} matching tables")

ID_TO_NAME_REGISTRY = {}   # {table_name: {id → name}}
NAME_TO_ID_REGISTRY = {}   # {table_name: {name → id}}

for table in discovered_tables:
    id_to_name, name_to_id = load_lookup(table)
    if id_to_name:  # Only store if we got data
        ID_TO_NAME_REGISTRY[table] = id_to_name
        NAME_TO_ID_REGISTRY[table] = name_to_id

print(f"\n✅ Loaded {len(ID_TO_NAME_REGISTRY)} reference tables into registries\n")

# --------------------------------------------------------------
# 3️⃣  Load sys_process_input and sys_process_output
# --------------------------------------------------------------
print("Loading sys_process_input and sys_process_output...")

input_df = spark.table("sys_process_input")
output_df = spark.table("sys_process_output")

print(f"✅ Loaded input and output tables\n")

# --------------------------------------------------------------
# 4️⃣  Load ALL sys_process metadata (CHANGE 1: no filtering)
# --------------------------------------------------------------
print("Loading ALL sys_process metadata...")
process_df = spark.table("sys_process")
process_columns = process_df.columns

# Find metadata columns
process_term_name_col = next((c for c in process_columns if 'process' in c.lower() and 'sys_oterm_name' in c.lower()), None)
person_term_name_col = next((c for c in process_columns if 'person' in c.lower() and 'sys_oterm_name' in c.lower()), None)
protocol_col = next((c for c in process_columns if 'protocol' in c.lower()), None)
date_end_col = next((c for c in process_columns if 'date_end' in c.lower()), None)

# Build process metadata lookup
process_metadata = {}
for row in process_df.collect():
    process_metadata[row.sys_process_id] = {
        "process_term_name": getattr(row, process_term_name_col) if process_term_name_col else None,
        "person_term_name": getattr(row, person_term_name_col) if person_term_name_col else None,
        "protocol": getattr(row, protocol_col) if protocol_col else None,
        "date_end": getattr(row, date_end_col) if date_end_col else None,
    }

print(f"✅ Loaded metadata for {len(process_metadata)} processes\n")

# --------------------------------------------------------------
# 5️⃣  Helper function to extract object tokens from a row
# --------------------------------------------------------------
def extract_objects_from_row(row, exclude_cols={'sys_process_id'}):
    """
    Extract all non-null object references from a row.
    Returns list of (table_name, object_id) tuples.
    
    For example, if row has sdt_strain_id='Strain0000001' and ddt_ndarray_id=None,
    returns [('sdt_strain', 'Strain0000001')]
    """
    objects = []
    row_dict = row.asDict()
    
    for col_name, value in row_dict.items():
        if col_name in exclude_cols or value is None:
            continue
        
        # Column name is like "sdt_strain_id" or "ddt_ndarray_id"
        # Extract table name by removing "_id" suffix
        if col_name.endswith("_id"):
            table_name = col_name[:-3]  # Remove "_id"
            objects.append((table_name, value))
    
    return objects

# --------------------------------------------------------------
# 6️⃣  Build provenance lookup (CHANGE 2: support multiple processes per output)
# --------------------------------------------------------------
print("Building provenance lookup...")

# --------------------------------------------------------------
# Collect all data once upfront
# --------------------------------------------------------------
print("  Collecting output data...")
output_rows = output_df.collect()
print(f"  ✓ Collected {len(output_rows)} output rows")

print("  Collecting input data...")
input_rows = input_df.collect()
print(f"  ✓ Collected {len(input_rows)} input rows")

# --------------------------------------------------------------
# Build index: process_id -> list of input objects
# --------------------------------------------------------------
print("  Building process -> inputs index...")
process_to_inputs = {}  # {process_id: [list of input tokens]}

for i, row in enumerate(input_rows):
    if i > 0 and i % 100000 == 0:
        print(f"    Processed {i}/{len(input_rows)} input rows...")
    
    process_id = row.sys_process_id
    input_objects = extract_objects_from_row(row)
    
    if process_id not in process_to_inputs:
        process_to_inputs[process_id] = []
    
    for table_name, obj_id in input_objects:
        input_token = f"{table_name}:{obj_id}"
        process_to_inputs[process_id].append(input_token)

print(f"  ✓ Built index for {len(process_to_inputs)} processes")

# --------------------------------------------------------------
# Build main output lookup (NOW STORES LISTS OF PROCESSES)
# --------------------------------------------------------------
print("  Building output lookup...")
out_lookup = {}  # {token: [list of {id, metadata, input_objs}]}
# Debug: Track (token, process_id) pairs to detect if we're missing any
seen_pairs = set()  # {(token, process_id)}
token_to_process_ids = {}  # {token: set of process_ids} for debugging

for i, row in enumerate(output_rows):
    if i > 0 and i % 100000 == 0:
        print(f"    Processed {i}/{len(output_rows)} output rows...")
    
    process_id = row.sys_process_id
    output_objects = extract_objects_from_row(row)
    
    # Get process metadata (O(1) lookup)
    metadata = process_metadata.get(process_id, {})
    
    # Get inputs for this process (O(1) lookup instead of Spark filter)
    input_objs = process_to_inputs.get(process_id, [])
    
    for table_name, obj_id in output_objects:
        # Create token in format "table_name:obj_id"
        token = f"{table_name}:{obj_id}"
        
        # Initialize list if this is the first time we see this token
        if token not in out_lookup:
            out_lookup[token] = []
            token_to_process_ids[token] = set()
        
        # Track this (token, process_id) pair
        pair_key = (token, process_id)
        
        # Only add if we haven't seen this exact (token, process_id) pair before
        # This prevents duplicates from the same row having the same object in multiple columns
        # BUT allows the same object to appear in different rows with different process_ids
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            token_to_process_ids[token].add(process_id)
            # Append this process to the list (don't overwrite)
            out_lookup[token].append({
                "id": process_id,
                "process_term_name": metadata.get("process_term_name"),
                "person_term_name": metadata.get("person_term_name"),
                "protocol": metadata.get("protocol"),
                "date_end": metadata.get("date_end"),
                "input_objs": input_objs
            })

total_output_objects = len(out_lookup)
total_process_links = sum(len(procs) for procs in out_lookup.values())

# Debug: Find objects with multiple processes
objects_with_multiple_procs = {token: len(procs) for token, procs in out_lookup.items() if len(procs) > 1}
if objects_with_multiple_procs:
    print(f"  [DEBUG] Found {len(objects_with_multiple_procs)} objects with multiple processes:")
    # Show top 10 examples with their process_ids
    sorted_multi = sorted(objects_with_multiple_procs.items(), key=lambda x: x[1], reverse=True)[:10]
    for token, count in sorted_multi:
        proc_ids = sorted([p['id'] for p in out_lookup[token]])
        print(f"    {token}: {count} processes with IDs: {proc_ids}")
    if len(objects_with_multiple_procs) > 10:
        print(f"    ... and {len(objects_with_multiple_procs) - 10} more")

# Debug: Verify we processed all rows correctly
print(f"  [DEBUG] Processed {len(output_rows)} total output rows")
print(f"  [DEBUG] Created {len(seen_pairs)} unique (token, process_id) pairs")
print(f"  [DEBUG] Total tokens: {total_output_objects}, Total process links: {total_process_links}")

print(f"✅ Built provenance for {total_output_objects} distinct output objects with {total_process_links} total process links.\n")

# --------------------------------------------------------------
# 6️⃣.5️⃣  REBUILD lookup from sys_process directly (FIX for missing processes)
# --------------------------------------------------------------
# NOTE: sys_process_output only keeps the highest process_id per output object
# (see parse_process.py lines 201-214). We need to rebuild from sys_process directly.
print("Rebuilding output lookup from sys_process directly (to get ALL processes)...")

def parse_object_ref_to_token(obj_ref: str) -> str:
    """
    Parse an object reference like "Brick-0000005:Brick0000010" or "Sample:Sample0002241"
    and convert to token format "table_name:obj_id"
    """
    if not obj_ref or ":" not in obj_ref:
        return None
    
    parts = obj_ref.split(":", 1)
    if len(parts) != 2:
        return None
    
    type_part, id_part = parts
    
    # Handle Brick references (ddt_ndarray)
    if type_part.startswith("Brick-") or type_part == "Brick":
        return f"ddt_ndarray:{id_part}"
    
    # For other types, try to find the table name in discovered_tables
    # The type_part might be like "Strain", "Sample", etc.
    # We need to map it to table names like "sdt_strain", "sdt_sample", etc.
    for table in discovered_tables:
        # Check if the table name contains the type (case-insensitive)
        if type_part.lower() in table.lower() or table.lower().replace("sdt_", "").replace("ddt_", "") == type_part.lower():
            return f"{table}:{id_part}"
    
    # If we can't find a match, try common patterns
    type_lower = type_part.lower()
    if type_lower in ["strain", "sample", "genome", "asv", "assembly", "reads"]:
        return f"sdt_{type_lower}:{id_part}"
    
    return None

# Rebuild out_lookup from sys_process
out_lookup_from_sys_process = {}  # {token: [list of {id, metadata, input_objs}]}
seen_pairs_sys_process = set()

print("  Processing sys_process rows...")
process_rows_list = process_df.collect()
for i, row in enumerate(process_rows_list):
    if i > 0 and i % 10000 == 0:
        print(f"    Processed {i}/{len(process_rows_list)} process rows...")
    
    process_id = row.sys_process_id
    output_objects = row.output_objects if hasattr(row, 'output_objects') and row.output_objects else []
    input_objects = row.input_objects if hasattr(row, 'input_objects') and row.input_objects else []
    
    # Get process metadata
    metadata = process_metadata.get(process_id, {})
    
    # Parse input objects to tokens
    input_tokens = []
    for inp_ref in input_objects:
        token = parse_object_ref_to_token(inp_ref)
        if token:
            input_tokens.append(token)
    
    # Parse output objects and add to lookup
    for out_ref in output_objects:
        token = parse_object_ref_to_token(out_ref)
        if not token:
            continue
        
        pair_key = (token, process_id)
        if pair_key in seen_pairs_sys_process:
            continue
        
        seen_pairs_sys_process.add(pair_key)
        
        if token not in out_lookup_from_sys_process:
            out_lookup_from_sys_process[token] = []
        
        out_lookup_from_sys_process[token].append({
            "id": process_id,
            "process_term_name": metadata.get("process_term_name"),
            "person_term_name": metadata.get("person_term_name"),
            "protocol": metadata.get("protocol"),
            "date_end": metadata.get("date_end"),
            "input_objs": input_tokens
        })

# Replace the old lookup with the new one
out_lookup = out_lookup_from_sys_process
total_output_objects = len(out_lookup)
total_process_links = sum(len(procs) for procs in out_lookup.values())

print(f"✅ Rebuilt provenance from sys_process: {total_output_objects} distinct output objects with {total_process_links} total process links.\n")

# Debug: Show comparison
objects_with_multiple_procs_new = {token: len(procs) for token, procs in out_lookup.items() if len(procs) > 1}
if objects_with_multiple_procs_new:
    print(f"  [DEBUG] After rebuild: Found {len(objects_with_multiple_procs_new)} objects with multiple processes")
    sorted_multi = sorted(objects_with_multiple_procs_new.items(), key=lambda x: x[1], reverse=True)[:5]
    for token, count in sorted_multi:
        proc_ids = sorted([p['id'] for p in out_lookup[token]])
        print(f"    {token}: {count} processes with IDs: {proc_ids[:10]}...")  # Show first 10

# --------------------------------------------------------------
# 7️⃣  Build forward map (input → outputs) - OPTIMIZED
# --------------------------------------------------------------
print("Building forward map...")

# Build index: process_id -> list of output tokens (from sys_process)
print("  Building process -> outputs index from sys_process...")
process_to_outputs = {}

for token, proc_list in out_lookup.items():
    for proc in proc_list:
        process_id = proc['id']
        if process_id not in process_to_outputs:
            process_to_outputs[process_id] = []
        if token not in process_to_outputs[process_id]:
            process_to_outputs[process_id].append(token)

print(f"  ✓ Built index for {len(process_to_outputs)} processes")

# Build the forward map using the indexes
print("  Building forward map from indexes...")
forward_map = {}

for i, row in enumerate(input_rows):
    if i > 0 and i % 100000 == 0:
        print(f"    Processed {i}/{len(input_rows)} input rows...")
    
    process_id = row.sys_process_id
    input_objects = extract_objects_from_row(row)
    
    for table_name, obj_id in input_objects:
        input_token = f"{table_name}:{obj_id}"
        
        if input_token not in forward_map:
            forward_map[input_token] = []
        
        # Get all outputs for this process (O(1) lookup)
        outputs = process_to_outputs.get(process_id, [])
        for output_token in outputs:
            if output_token not in forward_map[input_token]:
                forward_map[input_token].append(output_token)

print(f"✅ Built forward map for {len(forward_map)} input objects.\n")

# --------------------------------------------------------------
# 8️⃣  Name resolution function
# --------------------------------------------------------------
def parse_token(token: str):
    """
    Parse a token like "sdt_genome:genome_id_123" or "ddt_ndarray:brick_id_456"
    into (table_name, obj_id).
    Returns (None, None) if format is invalid.
    """
    if not token or ":" not in token:
        return None, None
    parts = token.split(":", 1)
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]

def resolve_name(token: str) -> str:
    """
    Turn a token like "sdt_genome:ASV123" into
    "sdt_genome:ASV123 (Candidatus …)" if a name exists.
    Also works for ddt_ndarray tokens.
    """
    table_name, obj_id = parse_token(token)
    if not table_name or not obj_id:
        return token
    
    lookup = ID_TO_NAME_REGISTRY.get(table_name)
    if not lookup:
        return token
    
    name = lookup.get(obj_id)
    return f"{token}  ({name})" if name else token

# --------------------------------------------------------------
# 9️⃣  Recursive tree printer (UPDATED to handle multiple processes)
# --------------------------------------------------------------
def walk_provenance(output_obj: str, depth: int = 0, visited: set = None):
    """
    Print the provenance tree starting from `output_obj`.
    
    Tracks visited (object, process_id) pairs to ensure all processes
    that produce the same output are traversed, while preventing cycles.
    """
    if visited is None:
        visited = set()
    indent = "    " * depth

    proc_list = out_lookup.get(output_obj)
    if proc_list is None:
        print(f"{indent}{output_obj}  <-- (no upstream process)")
        return

    # Debug: Show total number of processes for this object (only at top level or when multiple)
    if depth == 0 or len(proc_list) > 1:
        print(f"{indent}[DEBUG] Object {output_obj} has {len(proc_list)} producing process(es)")

    # Handle multiple processes that produce this output
    processes_traversed = 0
    for proc_idx, proc in enumerate(proc_list):
        # Create a unique key for this (object, process) pair
        process_key = (output_obj, proc['id'])
        
        # Check if we've already traversed this specific process for this object
        if process_key in visited:
            if len(proc_list) > 1:
                print(f"{indent}[Process {proc_idx + 1} of {len(proc_list)}] (already traversed)")
            else:
                print(f"{indent}{output_obj} (already traversed via this process)")
            continue
        
        # Mark this (object, process) pair as visited
        visited.add(process_key)
        processes_traversed += 1
        
        # If there are multiple processes, indicate which one
        if len(proc_list) > 1:
            print(f"{indent}━━━ Process {proc_idx + 1} of {len(proc_list)} ━━━")
        
        # Process line
        print(f"{indent}Process: {proc['process_term_name']} | "
              f"Person: {proc['person_term_name']} | "
              f"Protocol: {proc['protocol']} | "
              f"Date: {proc['date_end']} | "
              f"ID: {proc['id']}")

        # Recurse over every input object
        input_objs = proc.get("input_objs", [])
        if input_objs:
            print(f"{indent}  Inputs ({len(input_objs)}):")
            for inp in input_objs:
                print(f"{indent}    └─ {resolve_name(inp)}")
                walk_provenance(inp, depth + 2, visited)
        else:
            print(f"{indent}  (no inputs)")
    
    # Debug: Confirm how many processes were actually traversed
    if len(proc_list) > 1 and processes_traversed < len(proc_list):
        print(f"{indent}[DEBUG] WARNING: Only {processes_traversed} of {len(proc_list)} processes were traversed!")

# --------------------------------------------------------------
# 🔟  Helper to translate a name → token for any table
# --------------------------------------------------------------
def object_token_from_name(table_name: str, object_name: str) -> str:
    """
    Convert a human‑readable object name to the token format
    "table_name:object_id". Raises ValueError if the name is unknown.
    """
    name_to_id = NAME_TO_ID_REGISTRY.get(table_name)
    if name_to_id is None:
        raise ValueError(f"Table '{table_name}' not found in registry.")
    
    object_id = name_to_id.get(object_name)
    if object_id is None:
        raise ValueError(f"Object name '{object_name}' not found in table '{table_name}'.")
    
    return f"{table_name}:{object_id}"

# --------------------------------------------------------------
# 1️⃣1️⃣  Wrapper that prints the tree starting from an object name
# --------------------------------------------------------------
def walk_provenance_by_name(table_name: str, object_name: str):
    """Print the whole provenance tree for an object given its table and name."""
    token = object_token_from_name(table_name, object_name)
    print(f"{object_name}  ({token})")
    
    # Debug: Show how many processes produce this object
    proc_list = out_lookup.get(token)
    if proc_list:
        print(f"  [DEBUG] Found {len(proc_list)} process(es) that produce this object:")
        for idx, proc in enumerate(proc_list):
            print(f"    Process {idx + 1}: ID={proc['id']}, "
                  f"Name={proc.get('process_term_name', 'N/A')}, "
                  f"Protocol={proc.get('protocol', 'N/A')}")
    else:
        print(f"  [DEBUG] No processes found for this object")
    
    walk_provenance(token, depth=1)

# --------------------------------------------------------------
# 1️⃣2️⃣  Co‑assembly detection helpers (UPDATED to handle multiple processes)
# --------------------------------------------------------------
def _is_coassembly_process(proc_info: dict) -> bool:
    """
    True if the process used multiple Reads/reads inputs
    (ignoring any non-reads inputs).
    """
    inputs = proc_info.get("input_objs") or []
    # Look for any table ending in 'reads'
    reads_inputs = [inp for inp in inputs if isinstance(inp, str) and 
                    any(inp.startswith(f"{table}:") for table in discovered_tables if 'reads' in table.lower())]
    return len(reads_inputs) > 1

def has_coassembled_assembly(output_obj: str) -> bool:
    """
    Walk **upstream** from `output_obj` and return True if we encounter
    any Assembly whose producing process is a co-assembly.
    
    Tracks visited (object, process_id) pairs to ensure all processes
    that produce the same output are traversed.
    """
    visited = set()  # Tracks (object, process_id) pairs

    def dfs_up(obj: str) -> bool:
        # Check if this is an assembly object
        table_name, _ = parse_token(obj)
        if table_name and 'assembly' in table_name.lower():
            proc_list_for_assembly = out_lookup.get(obj)
            if proc_list_for_assembly:
                # Check ALL processes that produced this assembly
                for proc in proc_list_for_assembly:
                    if _is_coassembly_process(proc):
                        return True

        # Move upstream through ALL producing processes
        producing_procs = out_lookup.get(obj)
        if not producing_procs:
            return False

        for proc in producing_procs:
            # Create a unique key for this (object, process) pair
            process_key = (obj, proc['id'])
            
            # Skip if we've already traversed this specific process for this object
            if process_key in visited:
                continue
            
            # Mark this (object, process) pair as visited
            visited.add(process_key)
            
            # Recurse on all inputs of this process
            for inp in proc.get("input_objs", []) or []:
                if dfs_up(inp):
                    return True
        return False

    return dfs_up(output_obj)

def has_coassembled_assembly_by_name(table_name: str, object_name: str) -> bool:
    """Check if an object has a co-assembled assembly in its provenance."""
    token = object_token_from_name(table_name, object_name)
    return has_coassembled_assembly(token)

# --------------------------------------------------------------
# 1️⃣2️⃣.5️⃣  Debug utility: List all processes for an object
# --------------------------------------------------------------
def query_raw_output_rows_for_object(table_name: str, object_name: str):
    """
    Debug utility: Query the database directly to show ALL raw rows
    from sys_process_output that contain this object.
    This helps verify what's actually in the database vs what we collected.
    """
    token = object_token_from_name(table_name, object_name)
    parsed_table, obj_id = parse_token(token)
    if not parsed_table or not obj_id:
        print("  Invalid object name")
        return
    
    # Build the column name (e.g., "sdt_genome_id")
    id_col = f"{parsed_table}_id"
    
    print(f"\n=== Raw database rows for {object_name} ({parsed_table}:{obj_id}) ===")
    print(f"  Querying sys_process_output for rows where {id_col} = '{obj_id}'")
    
    try:
        # Query directly from the dataframe
        matching_rows = output_df.filter(F.col(id_col) == obj_id)
        row_count = matching_rows.count()
        print(f"  Found {row_count} row(s) in sys_process_output\n")
        
        if row_count > 0:
            # Show all columns and values for each row
            for idx, row in enumerate(matching_rows.collect(), 1):
                print(f"  Row {idx}:")
                print(f"    sys_process_id: {row.sys_process_id}")
                row_dict = row.asDict()
                # Show all non-null _id columns
                for col_name, value in sorted(row_dict.items()):
                    if col_name.endswith("_id") and value is not None and col_name != "sys_process_id":
                        print(f"    {col_name}: {value}")
                print()
        else:
            print("  No rows found in database!")
    except Exception as e:
        print(f"  Error querying database: {e}")

def query_sys_process_directly(table_name: str, object_name: str):
    """
    Debug utility: Query sys_process table directly and parse output_objects arrays.
    This shows what's actually in the source table before normalization.
    """
    token = object_token_from_name(table_name, object_name)
    parsed_table, obj_id = parse_token(token)
    if not parsed_table or not obj_id:
        print("  Invalid object name")
        return
    
    print(f"\n=== Querying sys_process directly for {object_name} ({parsed_table}:{obj_id}) ===")
    
    try:
        # Query sys_process where output_objects array contains the object ID
        # The format in the array is like "Brick-0000005:Brick0000010" or "Sample:Sample0002241"
        # We need to check if any element in the array ends with :obj_id
        
        # For ddt_ndarray (Brick), the format is "Brick-XXXXX:Brick0000010"
        # For other types, it's "TypeName:ObjectID"
        if parsed_table == "ddt_ndarray":
            # Match patterns like "Brick-*:Brick0000010" or "Brick:Brick0000010"
            pattern = f"%:{obj_id}"
        else:
            # Match patterns like "TypeName:ObjectID"
            pattern = f"%:{obj_id}"
        
        # Use array_contains or array operations to find matching rows
        # Since we can't easily do pattern matching in arrays, we'll convert to string and search
        matching_rows = process_df.filter(
            F.array_join(F.col("output_objects"), ",").contains(obj_id)
        )
        row_count = matching_rows.count()
        print(f"  Found {row_count} row(s) in sys_process\n")
        
        if row_count > 0:
            process_ids_found = []
            for idx, row in enumerate(matching_rows.collect(), 1):
                process_id = row.sys_process_id
                process_ids_found.append(process_id)
                output_objs = row.output_objects if hasattr(row, 'output_objects') else []
                
                # Check if this row actually contains our object
                contains_our_object = False
                for obj_ref in output_objs:
                    if obj_ref and obj_id in obj_ref:
                        # Verify it's actually this object (ends with :obj_id)
                        if obj_ref.endswith(f":{obj_id}"):
                            contains_our_object = True
                            break
                
                if contains_our_object:
                    print(f"  Row {idx} (CONTAINS OBJECT):")
                    print(f"    sys_process_id: {process_id}")
                    print(f"    process_term_name: {getattr(row, 'process_sys_oterm_name', 'N/A')}")
                    print(f"    person_term_name: {getattr(row, 'person_sys_oterm_name', 'N/A')}")
                    print(f"    protocol: {getattr(row, 'sdt_protocol_name', 'N/A')}")
                    print(f"    date_end: {getattr(row, 'date_end', 'N/A')}")
                    print(f"    output_objects: {output_objs}")
                    print()
            
            print(f"  Total process IDs found: {len(process_ids_found)}")
            print(f"  Process IDs: {sorted(set(process_ids_found))[:20]}")  # Show first 20
            if len(set(process_ids_found)) > 20:
                print(f"    ... and {len(set(process_ids_found)) - 20} more")
        else:
            print("  No rows found in sys_process!")
    except Exception as e:
        print(f"  Error querying sys_process: {e}")
        import traceback
        traceback.print_exc()

def list_all_processes_for_object(table_name: str, object_name: str):
    """
    Debug utility: List ALL processes that produce the given object.
    Useful for verifying that multiple processes are correctly stored.
    """
    token = object_token_from_name(table_name, object_name)
    proc_list = out_lookup.get(token)
    
    print(f"\n=== All processes for {object_name} ({token}) ===")
    if not proc_list:
        print("  No processes found in lookup.")
        return
    
    print(f"  Total processes in lookup: {len(proc_list)}\n")
    for idx, proc in enumerate(proc_list, 1):
        print(f"  Process {idx}:")
        print(f"    ID: {proc['id']}")
        print(f"    Process Term: {proc.get('process_term_name', 'N/A')}")
        print(f"    Person: {proc.get('person_term_name', 'N/A')}")
        print(f"    Protocol: {proc.get('protocol', 'N/A')}")
        print(f"    Date End: {proc.get('date_end', 'N/A')}")
        input_objs = proc.get("input_objs", [])
        print(f"    Inputs ({len(input_objs)}):")
        for inp in input_objs[:5]:  # Show first 5 inputs
            print(f"      - {inp}")
        if len(input_objs) > 5:
            print(f"      ... and {len(input_objs) - 5} more")
        print()

# --------------------------------------------------------------
# 1️⃣3️⃣  Example / driver code
# --------------------------------------------------------------
# Example: look up a genome (update table name and object name as needed)
user_table = "sdt_genome"  # or "sdt_asv" if genomes are called ASVs, or "ddt_ndarray" for bricks
user_object_name = "GW821-FHT01C12.3"

print("\n--- Debug: Query sys_process directly -------------------")
try:
    query_sys_process_directly(user_table, user_object_name)
except ValueError as e:
    print(e)

print("\n--- Debug: Query raw database rows from sys_process_output -------------------")
try:
    query_raw_output_rows_for_object(user_table, user_object_name)
except ValueError as e:
    print(e)

print("\n--- Debug: List all processes for object -------------------")
try:
    list_all_processes_for_object(user_table, user_object_name)
except ValueError as e:
    print(e)

print("\n--- Provenance tree (starting from object name) -------------------")
try:
    walk_provenance_by_name(user_table, user_object_name)
except ValueError as e:
    print(e)

print("\n--- Co‑assembly check -------------------------------------------")
try:
    if has_coassembled_assembly_by_name(user_table, user_object_name):
        print(f"The {user_table} \"{user_object_name}\" **has** a co‑assembled assembly in its provenance tree.")
    else:
        print(f"The {user_table} \"{user_object_name}\" **does NOT have** a co‑assembled assembly.")
except ValueError as e:
    print(e)

# --------------------------------------------------------------
# 1️⃣4️⃣  Utility: List all available tables and sample objects
# --------------------------------------------------------------
def show_available_tables():
    """Show all tables with their sample object names."""
    print("\n--- Available Tables ---")
    for table in sorted(ID_TO_NAME_REGISTRY.keys()):
        count = len(ID_TO_NAME_REGISTRY[table])
        sample_names = list(ID_TO_NAME_REGISTRY[table].values())[:3]
        print(f"  {table}: {count} objects")
        if sample_names:
            print(f"    Example names: {', '.join(sample_names)}")

# Uncomment to see available tables and sample data
show_available_tables()
