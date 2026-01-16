import os
import csv
import json
import re
from pathlib import Path

def pyspark_to_sql_type(pyspark_type):
    """Convert PySpark type to SQL type string."""
    type_mapping = {
        'StringType': 'STRING',
        'IntegerType': 'INT',
        'DoubleType': 'DOUBLE',
        'FloatType': 'FLOAT',
        'BooleanType': 'BOOLEAN',
        'LongType': 'BIGINT',
        'DateType': 'DATE',
        'TimestampType': 'TIMESTAMP',
    }
    return type_mapping.get(pyspark_type, 'STRING')

def parse_schema_file(schema_path):
    """Parse a PySpark schema file to extract column definitions."""
    with open(schema_path, 'r') as f:
        content = f.read()
    
    # Extract StructField definitions
    pattern = r'StructField\("([^"]+)",\s*(\w+)\(\)'
    matches = re.findall(pattern, content)
    
    columns = []
    for col_name, pyspark_type in matches:
        sql_type = pyspark_to_sql_type(pyspark_type)
        columns.append(f"{col_name} {sql_type}")
    
    return ", ".join(columns)

def parse_schema_with_comments(schema_path):
    """Parse a PySpark schema file to extract column names, types, and comments."""
    with open(schema_path, 'r') as f:
        content = f.read()
    
    # Pattern to match StructField with metadata
    # Updated pattern to handle escaped quotes in the comment value
    # (?:[^"\\]|\\.)* matches either: non-quote/non-backslash chars, OR backslash followed by any char
    pattern = r'StructField\("([^"]+)",\s*(\w+)\(\).*?metadata=\{"comment":\s*"((?:[^"\\]|\\.)*)"\}'
    matches = re.findall(pattern, content, re.DOTALL)
    
    columns_with_comments = []
    for col_name, pyspark_type, comment in matches:
        sql_type = pyspark_to_sql_type(pyspark_type)
        # Unescape the JSON string in the comment
        comment_unescaped = comment.replace('\\"', '"')
        
        columns_with_comments.append({
            'name': col_name,
            'type': sql_type,
            'comment': comment_unescaped
        })
    
    return columns_with_comments

def tsv_to_csv(tsv_path, csv_path):
    """Convert a TSV file to CSV."""
    with open(tsv_path, 'r', encoding='utf-8') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        with open(csv_path, 'w', encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for row in reader:
                writer.writerow(row)

def append_tsv_to_csv(tsv_path, csv_path, skip_header=False):
    """Append TSV content to a CSV file."""
    mode = 'a' if os.path.exists(csv_path) else 'w'
    
    with open(tsv_path, 'r', encoding='utf-8') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        with open(csv_path, mode, encoding='utf-8', newline='') as csv_file:
            writer = csv.writer(csv_file)
            
            for i, row in enumerate(reader):
                if i == 0 and skip_header:
                    continue
                writer.writerow(row)

def generate_comment_update_script(output_dir, table_comments):
    """Generate a Python script to update table comments using Spark SQL."""
    script_path = output_dir / "update_brick_comments.py"
    database_name = "enigma_coral"
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write("""# Auto-generated script to update table column comments
# This script uses Spark SQL ALTER TABLE commands to add comments to columns

from spark_utils import get_spark_session

def update_comments(spark):
    \"\"\"Update column comments for all tables.\"\"\"
    
    # Database name
    database = "enigma_coral"
    
""")
        
        for table_name, columns in table_comments.items():
            f.write(f"    # Update comments for table: {table_name}\n")
            f.write(f"    print(f\"Updating comments for table: {table_name}\")\n")
            
            for col in columns:
                col_name = col['name']
                col_type = col['type']
                comment = col['comment'].replace("'", "\\'")  # Escape single quotes for SQL
                
                # Use the database_name variable defined in this function
                alter_stmt = f"ALTER TABLE {database_name}.{table_name} CHANGE COLUMN {col_name} {col_name} {col_type} COMMENT '{comment}'"
                
                f.write(f"    \n")
                f.write(f"    spark.sql(\"\"\"\n")
                f.write(f"        {alter_stmt}\n")
                f.write(f"    \"\"\")\n")
            
            f.write(f"    print(f\"  Updated {len(columns)} columns for {table_name}\")\n")
            f.write(f"    \n")
        
        f.write("""
if __name__ == "__main__":
    # Create Spark session
    spark = get_spark_session()
    
    try:
        update_comments(spark)
        print("\\nSuccessfully updated all column comments!")
    except Exception as e:
        print(f"Error updating comments: {e}")
        raise
    finally:
        spark.stop()
""")
    
    print(f"Generated comment update script: {script_path}")

def main():
    input_dir = Path("bricks_in_cdm")
    output_dir = Path("bricks_in_berdl")
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Initialize aggregated files
    ddt_ndarray_csv = output_dir / "ddt_ndarray.csv"
    sys_ddt_typedef_csv = output_dir / "sys_ddt_typedef.csv"
    
    # Remove existing aggregated files
    if ddt_ndarray_csv.exists():
        ddt_ndarray_csv.unlink()
    if sys_ddt_typedef_csv.exists():
        sys_ddt_typedef_csv.unlink()
    
    # Track which files we've processed
    first_ddt_ndarray = True
    first_sys_ddt_typedef = True
    
    # Find all Brick TSV files (excluding the metadata files)
    all_files = sorted(input_dir.glob("Brick*.tsv"))
    brick_files = [f for f in all_files if not any(x in f.name for x in ['_ddt_ndarray', '_sys_ddt_typedef'])]
    
    tables = []
    table_comments = {}  # Store table comments for script generation
    
    for brick_tsv in brick_files:
        brick_id = brick_tsv.stem # e.g., "Brick0000010"
        brick_name = "ddt_"+brick_id.lower() # e.g., "ddt_brick0000010"
        
        # Convert main TSV to CSV
        output_csv = output_dir / f"{brick_name}.csv"
        tsv_to_csv(brick_tsv, output_csv)
        print(f"Converted {brick_id}.tsv to CSV")
        
        # Parse schema file
        schema_file = input_dir / f"{brick_id}_schema.py"
        if schema_file.exists():
            schema_sql = parse_schema_file(schema_file)
            # Also parse comments for the update script
            columns_with_comments = parse_schema_with_comments(schema_file)
            if columns_with_comments:
                table_comments[brick_name] = columns_with_comments
        else:
            print(f"Warning: Schema file not found for {brick_id}")
            continue
        
        # Append ddt_ndarray data
        ddt_ndarray_tsv = input_dir / f"{brick_id}_ddt_ndarray.tsv"
        if ddt_ndarray_tsv.exists():
            append_tsv_to_csv(ddt_ndarray_tsv, ddt_ndarray_csv, skip_header=not first_ddt_ndarray)
            first_ddt_ndarray = False
        
        # Append sys_ddt_typedef data
        sys_ddt_typedef_tsv = input_dir / f"{brick_id}_sys_ddt_typedef.tsv"
        if sys_ddt_typedef_tsv.exists():
            append_tsv_to_csv(sys_ddt_typedef_tsv, sys_ddt_typedef_csv, skip_header=not first_sys_ddt_typedef)
            first_sys_ddt_typedef = False
        
        # Add table definition
        table_def = {
            "name": brick_name,
            "enabled": True,
            "partition_by": None,
            "drop_extra_columns": True,
            "schema_sql": schema_sql,
            "bronze_path": f"s3a://cdm-lake/tenant-general-warehouse/enigma/datasets/coral-source/bronze/{brick_name}.csv"
        }
        tables.append(table_def)
    
    # Add ddt_ndarray table definition
    ddt_ndarray_schema = "ddt_ndarray_id STRING, ddt_ndarray_name STRING, ddt_ndarray_description STRING, ddt_ndarray_metadata STRING, ddt_ndarray_type_sys_oterm_id STRING, ddt_ndarray_type_sys_oterm_name STRING, ddt_ndarray_shape STRING, ddt_ndarray_dimension_types_sys_oterm_id STRING, ddt_ndarray_dimension_types_sys_oterm_name STRING, ddt_ndarray_dimension_variable_types_sys_oterm_id STRING, ddt_ndarray_dimension_variable_types_sys_oterm_name STRING, ddt_ndarray_variable_types_sys_oterm_id STRING, ddt_ndarray_variable_types_sys_oterm_name STRING, withdrawn_date STRING, superceded_by_ddt_ndarray_id STRING"
    
    tables.append({
        "name": "ddt_ndarray",
        "enabled": True,
        "partition_by": None,
        "drop_extra_columns": True,
        "schema_sql": ddt_ndarray_schema,
        "bronze_path": "s3a://cdm-lake/tenant-general-warehouse/enigma/datasets/coral-source/bronze/ddt_ndarray.csv"
    })
    
    # Add ddt_ndarray comments
    table_comments["ddt_ndarray"] = [
        {"name": "ddt_ndarray_id", "type": "STRING", "comment": '{"description": "Primary key for dynamic data type (N-dimensional array)", "type": "primary_key"}'},
        {"name": "ddt_ndarray_name", "type": "STRING", "comment": '{"description": "Name of the data brick (N-dimensional array)", "type": "unique_key"}'},
        {"name": "ddt_ndarray_description", "type": "STRING", "comment": '{"description": "Description of the data brick (N-dimensional array)"}'},
        {"name": "ddt_ndarray_metadata", "type": "STRING", "comment": '{"description": "Metadata for the data brick (N-dimensional array)"}'},
        {"name": "ddt_ndarray_type_sys_oterm_id", "type": "STRING", "comment": '{"description": "Data type for this data brick, ontology term CURIE", "type": "foreign_key", "references": "sys_oterm.sys_oterm_id"}'},
        {"name": "ddt_ndarray_type_sys_oterm_name", "type": "STRING", "comment": '{"description": "Data type for this data brick"}'},
        {"name": "ddt_ndarray_shape", "type": "STRING", "comment": '{"description": "Shape of the N-dimensional array, array with one integer per dimension", "example": "[10,10]"}'},
        {"name": "ddt_ndarray_dimension_types_sys_oterm_id", "type": "STRING", "comment": '{"description": "Array of dimension data types, ontology term CURIEs", "type": "foreign_key", "references": "[sys_oterm.sys_oterm_id]"}'},
        {"name": "ddt_ndarray_dimension_types_sys_oterm_name", "type": "STRING", "comment": '{"description": "Array of dimension data types"}'},
        {"name": "ddt_ndarray_dimension_variable_types_sys_oterm_id", "type": "STRING", "comment": '{"description": "Array of dimension variable types, ontology term CURIEs", "type": "foreign_key", "references": "[sys_oterm.sys_oterm_id]"}'},
        {"name": "ddt_ndarray_dimension_variable_types_sys_oterm_name", "type": "STRING", "comment": '{"description": "Array of dimension variable types"}'},
        {"name": "ddt_ndarray_variable_types_sys_oterm_id", "type": "STRING", "comment": '{"description": "Array of variable types, ontology term CURIEs", "type": "foreign_key", "references": "[sys_oterm.sys_oterm_id]"}'},
        {"name": "ddt_ndarray_variable_types_sys_oterm_name", "type": "STRING", "comment": '{"description": "Array of variable types"}'},
        {"name": "withdrawn_date", "type": "STRING", "comment": '{"description": "Date when this dataset was withdrawn, or null if the dataset is currently valid"}'},
        {"name": "superceded_by_ddt_ndarray_id", "type": "STRING", "comment": '{"description": "Dataset that supercedes this one, if the dataset was withdrawn and replaced, or null if the dataset is currently valid", "type": "foreign_key", "references": "ddt_ndarray.ddt_ndarray_id"}'},
    ]
    
    # Add sys_ddt_typedef table definition
    sys_ddt_typedef_schema = "ddt_ndarray_id STRING, berdl_column_name STRING, berdl_column_data_type STRING, scalar_type STRING, foreign_key STRING, comment STRING, unit_sys_oterm_id STRING, unit_sys_oterm_name STRING, dimension_number INT, dimension_oterm_id STRING, dimension_oterm_name STRING, variable_number INT, variable_oterm_id STRING, variable_oterm_name STRING, original_csv_string STRING"
    
    tables.append({
        "name": "sys_ddt_typedef",
        "enabled": True,
        "partition_by": None,
        "drop_extra_columns": True,
        "schema_sql": sys_ddt_typedef_schema,
        "bronze_path": "s3a://cdm-lake/tenant-general-warehouse/enigma/datasets/coral-source/bronze/sys_ddt_typedef.csv"
    })
    
    # Add sys_ddt_typedef comments
    table_comments["sys_ddt_typedef"] = [
        {"name": "ddt_ndarray_id", "type": "STRING", "comment": '{"description": "Key for dynamic data type (N-dimensional array)", "type": "foreign_key", "references": "ddt_ndarray.ddt_ndarray_id"}'},
        {"name": "berdl_column_name", "type": "STRING", "comment": '{"description": "BERDL column name"}'},
        {"name": "berdl_column_data_type", "type": "STRING", "comment": '{"description": "BERDL column data type, variable or dimension_variable"}'},
        {"name": "scalar_type", "type": "STRING", "comment": '{"description": "Scalar type"}'},
        {"name": "foreign_key", "type": "STRING", "comment": '{"description": "Foreign key reference"}'},
        {"name": "comment", "type": "STRING", "comment": '{"description": "Column comment"}'},
        {"name": "unit_sys_oterm_id", "type": "STRING", "comment": '{"description": "Unit, ontology term CURIE", "type": "foreign_key", "references": "sys_oterm.sys_oterm_id"}'},
        {"name": "unit_sys_oterm_name", "type": "STRING", "comment": '{"description": "Unit"}'},
        {"name": "dimension_number", "type": "INT", "comment": '{"description": "Dimension number, starting at 1, for dimension variables"}'},
        {"name": "dimension_oterm_id", "type": "STRING", "comment": '{"description": "Dimension data type, ontology term CURIE", "type": "foreign_key", "references": "sys_oterm.sys_oterm_id"}'},
        {"name": "dimension_oterm_name", "type": "STRING", "comment": '{"description": "Dimension data type"}'},
        {"name": "variable_number", "type": "INT", "comment": '{"description": "Variable number within a dimension, numbered starting at 1"}'},
        {"name": "variable_oterm_id", "type": "STRING", "comment": '{"description": "Dimension variable data type, ontology term CURIE", "type": "foreign_key", "references": "sys_oterm.sys_oterm_id"}'},
        {"name": "variable_oterm_name", "type": "STRING", "comment": '{"description": "Dimension variable data type"}'},
        {"name": "original_csv_string", "type": "STRING", "comment": '{"description": "Original representation of this variable in the CORAL data dump CSV"}'},
    ]
    
    # Create JSON structure
    enigma_json = {
        "tenant": "enigma",
        "dataset": "coral",
        "is_tenant": True,
        "paths": {
            "data_plane": "s3a://cdm-lake/tenant-general-warehouse/enigma/",
            "bronze_base": "s3a://cdm-lake/tenant-general-warehouse/enigma/datasets/coral-source/bronze",
            "silver_base": "s3a://cdm-lake/tenant-sql-warehouse/enigma/enigma_coral.db"
        },
        "defaults": {
            "csv": {
                "header": True,
                "delimiter": ",",
                "inferSchema": False
            }
        },
        "tables": tables
    }
    
    # Write JSON file
    json_path = output_dir / "coral.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(enigma_json, f, indent=2)
    
    # Generate comment update script
    if table_comments:
        generate_comment_update_script(output_dir, table_comments)
    
    print(f"\nProcessed {len(brick_files)} Brick files")
    print(f"Created {len(tables)} table definitions in coral.json")
    print(f"Output written to: {output_dir}")

if __name__ == "__main__":
    main()
