"""
Parse sys_process table and create 1NF tables: sys_process_input and sys_process_output.

This script converts the array-valued input_objects and output_objects columns
into normalized tables with one row per (process, object) combination.
"""

import json
import logging
from typing import Dict, List, Set, Tuple
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType

# Assume spark session and database are already set up
# spark = get_spark_session()
# spark.sql("USE jmc_coral")

def parse_object_reference(obj_ref: str) -> Tuple[str, str, str]:
    """
    Parse an object reference from input_objects or output_objects.
    
    Returns (object_type, table_name, object_id)
    - For "Strain:Strain0000673" -> ("Strain", "sdt_strain", "Strain0000673")
    - For "Brick-1:Brick0000003" -> ("Brick", "ddt_ndarray", "Brick0000003")
    
    Returns (None, None, None) if parsing fails.
    """
    if not obj_ref or ":" not in obj_ref:
        return None, None, None
    
    parts = obj_ref.split(":", 1)
    if len(parts) != 2:
        return None, None, None
    
    type_part, id_part = parts
    
    # Handle Brick references (ddt types)
    if type_part.startswith("Brick-") or type_part == "Brick":
        return "Brick", "ddt_ndarray", id_part
    
    # Handle sdt types - will be mapped later
    return type_part, None, id_part


def build_type_mapping(spark) -> Dict[str, Tuple[str, str]]:
    """
    Build mapping from CORAL type name to (CDM table name, primary key column).
    
    Returns dict like:
    {
        "Strain": ("sdt_strain", "sdt_strain_id"),
        "Genome": ("sdt_genome", "sdt_genome_id"),
        ...
    }
    """
    typedef_df = spark.sql("""
        SELECT type_name, cdm_column_name 
        FROM sys_typedef 
        WHERE is_pk = true
    """)
    
    type_mapping = {}
    for row in typedef_df.collect():
        type_name = row.type_name
        pk_column = row.cdm_column_name
        
        # Derive table name from primary key (remove "_id" suffix)
        if pk_column.endswith("_id"):
            table_name = pk_column[:-3]  # Remove "_id"
            type_mapping[type_name] = (table_name, pk_column)
        else:
            logging.warning(f"Unexpected primary key format: {pk_column}")
    
    logging.info(f"Built type mapping for {len(type_mapping)} types")
    return type_mapping


def validate_foreign_keys(spark, type_mapping: Dict[str, Tuple[str, str]]) -> Dict[str, Set[str]]:
    """
    Load all valid IDs for each table to validate foreign keys.
    
    Returns dict like:
    {
        "sdt_strain": {"Strain0000001", "Strain0000002", ...},
        "ddt_ndarray": {"Brick0000001", "Brick0000002", ...},
        ...
    }
    """
    valid_ids = {}
    
    # Get all unique table names
    tables = set()
    for table_name, _ in type_mapping.values():
        tables.add(table_name)
    tables.add("ddt_ndarray")  # Always include ddt_ndarray
    
    for table_name in tables:
        try:
            # Determine the ID column name
            if table_name == "ddt_ndarray":
                id_col = "ddt_ndarray_id"
            else:
                id_col = f"{table_name}_id"
            
            # Load all IDs from the table
            df = spark.table(table_name).select(id_col)
            ids = {row[id_col] for row in df.collect() if row[id_col]}
            valid_ids[table_name] = ids
            logging.info(f"Loaded {len(ids)} valid IDs from {table_name}")
        except Exception as e:
            logging.warning(f"Could not load IDs from {table_name}: {e}")
            valid_ids[table_name] = set()
    
    return valid_ids


def create_process_tables(spark, db_name: str = "jmc_coral"):
    """
    Create sys_process_input and sys_process_output tables.
    """
    # --------------------------------------------------------------
    # 1. Build type mapping from sys_typedef
    # --------------------------------------------------------------
    type_mapping = build_type_mapping(spark)
    
    # --------------------------------------------------------------
    # 2. Validate foreign keys
    # --------------------------------------------------------------
    valid_ids = validate_foreign_keys(spark, type_mapping)
    
    # --------------------------------------------------------------
    # 3. Load and parse sys_process table
    # --------------------------------------------------------------
    process_df = spark.table("sys_process")
    
    # Helper function to parse objects (run on driver)
    def parse_objects(objects_list, type_mapping, valid_ids):
        """
        Parse a list of object references and return valid ones grouped by table.
        
        Returns dict like:
        {
            "sdt_strain": ["Strain0000001", "Strain0000002"],
            "ddt_ndarray": ["Brick0000001"],
            ...
        }
        """
        if not objects_list:
            return {}
        
        result = {}
        for obj_ref in objects_list:
            if not obj_ref:
                continue
            
            coral_type, table_name, obj_id = parse_object_reference(obj_ref)
            
            if not coral_type or not obj_id:
                continue
            
            # Map CORAL type to CDM table if needed
            if table_name is None and coral_type in type_mapping:
                table_name, _ = type_mapping[coral_type]
            
            if not table_name:
                continue
            
            # Validate foreign key
            if table_name in valid_ids and obj_id in valid_ids[table_name]:
                if table_name not in result:
                    result[table_name] = []
                result[table_name].append(obj_id)
        
        return result
    
    # --------------------------------------------------------------
    # 4. Collect and parse process data
    # --------------------------------------------------------------
    processes = []
    
    for row in process_df.collect():
        process_id = row.sys_process_id
        input_objects = row.input_objects if row.input_objects else []
        output_objects = row.output_objects if row.output_objects else []
        
        # Parse inputs and outputs
        inputs = parse_objects(input_objects, type_mapping, valid_ids)
        outputs = parse_objects(output_objects, type_mapping, valid_ids)
        
        # Only include if at least one valid reference exists
        if inputs or outputs:
            processes.append({
                "process_id": process_id,
                "inputs": inputs,
                "outputs": outputs
            })
    
    logging.info(f"Parsed {len(processes)} valid process records")
    
    # --------------------------------------------------------------
    # 5. Keep only highest ID process for each output
    # --------------------------------------------------------------
    # Build mapping: output -> highest process ID
    output_to_max_process = {}
    
    for proc in processes:
        for table_name, obj_ids in proc["outputs"].items():
            for obj_id in obj_ids:
                key = (table_name, obj_id)
                current_max = output_to_max_process.get(key)
                if current_max is None or proc["process_id"] > current_max:
                    output_to_max_process[key] = proc["process_id"]
    
    # Filter processes to keep only those with highest ID for their outputs
    filtered_processes = []
    for proc in processes:
        # Check if this process has the highest ID for any of its outputs
        is_highest = False
        for table_name, obj_ids in proc["outputs"].items():
            for obj_id in obj_ids:
                key = (table_name, obj_id)
                if output_to_max_process.get(key) == proc["process_id"]:
                    is_highest = True
                    break
            if is_highest:
                break
        
        # If no outputs, keep the process (it might have inputs)
        if not proc["outputs"] or is_highest:
            filtered_processes.append(proc)
    
    logging.info(f"Kept {len(filtered_processes)} processes after filtering by highest ID")
    
    # --------------------------------------------------------------
    # 6. Determine which table columns are actually used
    # --------------------------------------------------------------
    input_tables = set()
    output_tables = set()
    
    for proc in filtered_processes:
        for table_name in proc["inputs"].keys():
            input_tables.add(table_name)
        for table_name in proc["outputs"].keys():
            output_tables.add(table_name)
    
    logging.info(f"Input tables used: {sorted(input_tables)}")
    logging.info(f"Output tables used: {sorted(output_tables)}")
    
    # --------------------------------------------------------------
    # 7. Build sys_process_input rows
    # --------------------------------------------------------------
    input_rows = []
    
    for proc in filtered_processes:
        for table_name, obj_ids in proc["inputs"].items():
            for obj_id in obj_ids:
                row_dict = {"sys_process_id": proc["process_id"]}
                # Set the appropriate column to the object ID
                if table_name == "ddt_ndarray":
                    row_dict["ddt_ndarray_id"] = obj_id
                else:
                    # Use the primary key column name
                    pk_col = f"{table_name}_id"
                    row_dict[pk_col] = obj_id
                input_rows.append(row_dict)
    
    # --------------------------------------------------------------
    # 8. Build sys_process_output rows
    # --------------------------------------------------------------
    output_rows = []
    
    for proc in filtered_processes:
        for table_name, obj_ids in proc["outputs"].items():
            for obj_id in obj_ids:
                row_dict = {"sys_process_id": proc["process_id"]}
                # Set the appropriate column to the object ID
                if table_name == "ddt_ndarray":
                    row_dict["ddt_ndarray_id"] = obj_id
                else:
                    # Use the primary key column name
                    pk_col = f"{table_name}_id"
                    row_dict[pk_col] = obj_id
                output_rows.append(row_dict)
    
    logging.info(f"Created {len(input_rows)} input rows and {len(output_rows)} output rows")
    
    # --------------------------------------------------------------
    # 9. Build schemas for input and output tables
    # --------------------------------------------------------------
    def build_schema(tables_used: Set[str], direction: str) -> StructType:
        """Build schema with JSON comments for each field."""
        fields = []
        
        # sys_process_id column (always first)
        fields.append(StructField(
            "sys_process_id",
            StringType(),
            nullable=False,
            metadata={"comment": json.dumps({
                "description": f"Foreign key to sys_process",
                "type": "foreign_key",
                "references": "sys_process.sys_process_id"
            })}
        ))
        
        # Add columns for each table type used, in sorted order
        for table_name in sorted(tables_used):
            if table_name == "ddt_ndarray":
                col_name = "ddt_ndarray_id"
                ref_table = "ddt_ndarray"
            else:
                col_name = f"{table_name}_id"
                ref_table = table_name
            
            fields.append(StructField(
                col_name,
                StringType(),
                nullable=True,
                metadata={"comment": json.dumps({
                    "description": f"{direction.capitalize()} object from {ref_table}",
                    "type": "foreign_key",
                    "references": f"{ref_table}.{col_name}"
                })}
            ))
        
        return StructType(fields)
    
    input_schema = build_schema(input_tables, "input")
    output_schema = build_schema(output_tables, "output")
    
    # --------------------------------------------------------------
    # 10. Create DataFrames and ensure all columns exist
    # --------------------------------------------------------------
    def create_df(rows: List[Dict], schema: StructType):
        """Create DataFrame ensuring all schema columns are present."""
        if not rows:
            return spark.createDataFrame([], schema)
        
        # Ensure all rows have all columns (fill missing with None)
        complete_rows = []
        for row_dict in rows:
            complete_row = {}
            for field in schema.fields:
                complete_row[field.name] = row_dict.get(field.name)
            complete_rows.append(complete_row)
        
        # Convert to list of tuples in schema order
        rows_tuples = [
            tuple(row[field.name] for field in schema.fields)
            for row in complete_rows
        ]
        
        return spark.createDataFrame(rows_tuples, schema)
    
    input_df = create_df(input_rows, input_schema)
    output_df = create_df(output_rows, output_schema)
    
    # --------------------------------------------------------------
    # 11. Show schemas and sample data
    # --------------------------------------------------------------
    logging.info("--- Schema for sys_process_input ---")
    input_df.printSchema()
    logging.info("--- Sample rows for sys_process_input (up to 5) ---")
    input_df.show(5, truncate=False)
    
    logging.info("--- Schema for sys_process_output ---")
    output_df.printSchema()
    logging.info("--- Sample rows for sys_process_output (up to 5) ---")
    output_df.show(5, truncate=False)
    
    # --------------------------------------------------------------
    # 12. Write tables
    # --------------------------------------------------------------
    spark.sql(f"DROP TABLE IF EXISTS {db_name}.sys_process_input")
    input_df.write.format("delta").option(
        "comment", "Process Inputs"
    ).saveAsTable(f"{db_name}.sys_process_input")
    logging.info(f"Created table {db_name}.sys_process_input")
    
    spark.sql(f"DROP TABLE IF EXISTS {db_name}.sys_process_output")
    output_df.write.format("delta").option(
        "comment", "Process Outputs"
    ).saveAsTable(f"{db_name}.sys_process_output")
    logging.info(f"Created table {db_name}.sys_process_output")
    
    logging.info("✅ Process table creation complete.")


# --------------------------------------------------------------
# Execute
# --------------------------------------------------------------
spark = get_spark_session()  # <-- defined elsewhere
db_name = "enigma_coral"
spark.sql(f"USE {db_name}")
create_process_tables(spark, db_name)
