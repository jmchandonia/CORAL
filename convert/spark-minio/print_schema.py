# export schema to DBML

from pyspark.sql import SparkSession
from datetime import datetime
import json
import re

spark = SparkSession.builder.appName("SchemaExport").getOrCreate()
namespace = "jmc_coral"

def spark_to_dbml_type(spark_type):
    """Map Spark types to DBML types"""
    type_map = {
        'string': 'varchar', 'int': 'int', 'integer': 'int',
        'bigint': 'bigint', 'long': 'bigint', 'smallint': 'smallint',
        'tinyint': 'tinyint', 'float': 'float', 'double': 'double',
        'boolean': 'boolean', 'timestamp': 'timestamp', 'date': 'date',
        'binary': 'binary'
    }
    spark_type_lower = spark_type.lower()
    if spark_type_lower.startswith('decimal'):
        return spark_type
    if 'array' in spark_type_lower or 'map' in spark_type_lower or 'struct' in spark_type_lower:
        return 'json'
    return type_map.get(spark_type_lower, 'varchar')

def parse_comment(comment):
    """Parse comment as JSON if possible, otherwise return as plain text"""
    if not comment:
        return None, None
    
    try:
        comment_data = json.loads(comment)
        return comment_data, comment_data.get('description', comment)
    except (json.JSONDecodeError, TypeError):
        return None, comment

def get_table_info(namespace, table_name):
    """Get table schema information"""
    full_table_name = f"{namespace}.{table_name}"
    
    desc = spark.sql(f"DESCRIBE EXTENDED {full_table_name}").collect()
    
    columns = []
    partition_cols = []
    table_comment = None
    
    in_column_section = True
    for row in desc:
        col_name = row['col_name'].strip()
        data_type = row['data_type'].strip()
        
        if col_name == '':
            in_column_section = False
            continue
            
        if in_column_section and col_name not in ['# Partition Information', '# col_name']:
            comment = row['comment'] if row['comment'] else None
            columns.append((col_name, data_type, comment))
        
        if col_name == 'Comment':
            table_comment = data_type if data_type else None
        elif not in_column_section and col_name and col_name[0] != '#' and data_type:
            if col_name not in [c[0] for c in columns]:
                partition_cols.append(col_name)
    
    return columns, partition_cols, table_comment

def extract_foreign_keys(table_name, columns):
    """Extract foreign keys from column comments"""
    foreign_keys = []
    
    for col_name, data_type, comment in columns:
        comment_data, description = parse_comment(comment)
        
        if comment_data and comment_data.get('type') == 'foreign_key':
            references = comment_data.get('references')
            if references:
                # Parse references like "sys_process.sys_process_id"
                if '.' in references:
                    ref_table, ref_column = references.split('.', 1)
                    foreign_keys.append((col_name, ref_table, ref_column, description))
    
    return foreign_keys

# Get all tables
tables = spark.sql(f"SHOW TABLES IN {namespace}").collect()

# Store all table info and foreign keys
table_data = {}
all_foreign_keys = []

# Collect all table information
for table in tables:
    table_name = table['tableName']
    
    if table['isTemporary']:
        continue
    
    try:
        columns, partition_cols, table_comment = get_table_info(namespace, table_name)
        table_data[table_name] = {
            'columns': columns,
            'partition_cols': partition_cols,
            'table_comment': table_comment
        }
        
        # Extract foreign keys from column comments
        fks = extract_foreign_keys(table_name, columns)
        for col_name, ref_table, ref_column, description in fks:
            all_foreign_keys.append((table_name, col_name, ref_table, ref_column))
        
    except Exception as e:
        print(f"// Error processing {table_name}: {str(e)}")

# Print DBML header
print(f"// DBML Schema Export")
print(f"// Database: {namespace}")
print(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print(f"Project {namespace} {{")
print(f"  database_type: 'Delta Lake'")
print("}")
print()

# Print tables
for table_name, data in table_data.items():
    columns = data['columns']
    partition_cols = data['partition_cols']
    table_comment = data['table_comment']
    
    regular_cols = [c for c in columns if c[0] not in partition_cols]
    
    print(f"Table {table_name} {{")
    
    # Add columns
    for col_name, data_type, comment in regular_cols:
        dbml_type = spark_to_dbml_type(data_type)
        col_def = f"  {col_name} {dbml_type}"
        
        # Check if this column is a primary key (common convention)
        if col_name.lower() in ['id', f'{table_name}_id']:
            col_def += " [pk]"
        
        # Parse comment
        comment_data, description = parse_comment(comment)
        
        if description:
            escaped_description = description.replace('"', '\\"').replace("'", "\\'")
            if '[pk]' in col_def:
                col_def = col_def.replace('[pk]', f"[pk, note: '{escaped_description}']")
            else:
                col_def += f" [note: '{escaped_description}']"
        
        print(col_def)
    
    # Add partition columns if any
    if partition_cols:
        print()
        print("  // Partition columns")
        for partition_col in partition_cols:
            for col_name, data_type, comment in columns:
                if col_name == partition_col:
                    dbml_type = spark_to_dbml_type(data_type)
                    col_def = f"  {col_name} {dbml_type}"
                    
                    comment_data, description = parse_comment(comment)
                    if description:
                        escaped_description = description.replace('"', '\\"').replace("'", "\\'")
                        col_def += f" [note: 'Partition column - {escaped_description}']"
                    else:
                        col_def += " [note: 'Partition column']"
                    print(col_def)
                    break
    
    # Add table note/comment
    if table_comment:
        table_comment_data, table_description = parse_comment(table_comment)
        if table_description:
            print()
            escaped_comment = table_description.replace('"', '\\"').replace("'", "\\'")
            print(f"  Note: '{escaped_comment}'")
    
    print("}")
    print()

# Print foreign key relationships
if all_foreign_keys:
    print("// Foreign Key Relationships")
    for source_table, source_col, target_table, target_col in all_foreign_keys:
        print(f"Ref: {source_table}.{source_col} > {target_table}.{target_col}")
    print()
