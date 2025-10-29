# --------------------------------------------------------------
# 0️⃣  Imports & Spark session
# --------------------------------------------------------------
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import ArrayType, StringType
import re

spark = (SparkSession.builder
         .appName("ProvenanceCoassemblyNormalized")
         .enableHiveSupport()
         .getOrCreate())

# Use the jmc_coral database
spark.sql("USE jmc_coral")

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

# Get set of all process IDs referenced in input/output tables
print("  Finding referenced process IDs...")
referenced_process_ids = set()
for row in input_df.select("sys_process_id").distinct().collect():
    referenced_process_ids.add(row.sys_process_id)
for row in output_df.select("sys_process_id").distinct().collect():
    referenced_process_ids.add(row.sys_process_id)

print(f"✅ Found {len(referenced_process_ids)} unique process IDs in input/output tables\n")

# --------------------------------------------------------------
# 4️⃣  Load sys_process metadata (only for referenced processes)
# --------------------------------------------------------------
print("Loading sys_process metadata...")
process_df = spark.table("sys_process").filter(
    F.col("sys_process_id").isin(list(referenced_process_ids))
)
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
# 6️⃣  Build provenance lookup from input/output tables (OPTIMIZED)
# --------------------------------------------------------------
print("Building provenance lookup...")

# --------------------------------------------------------------
# Collect all data once upfront (more efficient than repeated filtering)
# --------------------------------------------------------------
print("  Collecting output data...")
output_rows = output_df.collect()
print(f"  ✓ Collected {len(output_rows)} output rows")

print("  Collecting input data...")
input_rows = input_df.collect()
print(f"  ✓ Collected {len(input_rows)} input rows")

# --------------------------------------------------------------
# Build index: process_id -> list of input objects
# This allows O(1) lookup instead of O(n) filtering for each output
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
# Build main output lookup
# --------------------------------------------------------------
print("  Building output lookup...")
out_lookup = {}  # {token: {id, metadata, input_objs}}

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
        
        # Store in lookup
        out_lookup[token] = {
            "id": process_id,
            "process_term_name": metadata.get("process_term_name"),
            "person_term_name": metadata.get("person_term_name"),
            "protocol": metadata.get("protocol"),
            "date_end": metadata.get("date_end"),
            "input_objs": input_objs
        }

print(f"✅ Built provenance for {len(out_lookup)} distinct output objects.\n")

# --------------------------------------------------------------
# 7️⃣  Build forward map (input → outputs) - OPTIMIZED
# --------------------------------------------------------------
print("Building forward map...")

# Build index: process_id -> list of output tokens
print("  Building process -> outputs index...")
process_to_outputs = {}

for i, row in enumerate(output_rows):
    if i > 0 and i % 100000 == 0:
        print(f"    Processed {i}/{len(output_rows)} output rows...")
    
    process_id = row.sys_process_id
    output_objects = extract_objects_from_row(row)
    
    if process_id not in process_to_outputs:
        process_to_outputs[process_id] = []
    
    for table_name, obj_id in output_objects:
        output_token = f"{table_name}:{obj_id}"
        process_to_outputs[process_id].append(output_token)

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
# 9️⃣  Recursive tree printer
# --------------------------------------------------------------
def walk_provenance(output_obj: str, depth: int = 0, visited: set = None):
    """Print the provenance tree starting from `output_obj`."""
    if visited is None:
        visited = set()
    indent = "    " * depth

    if output_obj in visited:
        print(f"{indent}{output_obj} (already visited)")
        return
    visited.add(output_obj)

    proc = out_lookup.get(output_obj)
    if proc is None:
        print(f"{indent}{output_obj}  <-- (no upstream process)")
        return

    # Process line
    print(f"{indent}{proc['process_term_name']} | "
          f"{proc['person_term_name']} | "
          f"{proc['protocol']} | {proc['date_end']}")

    # Recurse over every input object
    for inp in proc.get("input_objs", []):
        print(f"{indent}    └─ Input: {resolve_name(inp)}")
        walk_provenance(inp, depth + 2, visited)

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
    walk_provenance(token, depth=1)

# --------------------------------------------------------------
# 1️⃣2️⃣  Co‑assembly detection helpers
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
    """
    visited = set()

    def dfs_up(obj: str) -> bool:
        if obj in visited:
            return False
        visited.add(obj)

        # Check if this is an assembly object
        table_name, _ = parse_token(obj)
        if table_name and 'assembly' in table_name.lower():
            proc_for_assembly = out_lookup.get(obj)
            if proc_for_assembly and _is_coassembly_process(proc_for_assembly):
                return True

        # Move upstream
        producing_proc = out_lookup.get(obj)
        if not producing_proc:
            return False

        for inp in producing_proc.get("input_objs", []) or []:
            if dfs_up(inp):
                return True
        return False

    return dfs_up(output_obj)

def has_coassembled_assembly_by_name(table_name: str, object_name: str) -> bool:
    """Check if an object has a co-assembled assembly in its provenance."""
    token = object_token_from_name(table_name, object_name)
    return has_coassembled_assembly(token)

# --------------------------------------------------------------
# 1️⃣3️⃣  Example / driver code
# --------------------------------------------------------------
# Example: look up a genome (update table name and object name as needed)
user_table = "sdt_genome"  # or "sdt_asv" if genomes are called ASVs, or "ddt_ndarray" for bricks
user_object_name = "GW821-FHT01C12.3"

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
