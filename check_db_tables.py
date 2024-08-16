import sqlite3

def print_table_schemas():
    # Connect to your database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # List of tables in your models
    model_tables = ['game_character', 'game_zone', 'game_subzone']

    # Print the schema for each table in your models
    for table_name in model_tables:
        print(f"Schema of '{table_name}' table:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema_info = cursor.fetchall()
        for column_info in schema_info:
            print(f"- {column_info[1]} ({column_info[2]})")
        print()  # Add a blank line for readability

    # Close connection
    conn.close()

if __name__ == "__main__":
    print_table_schemas()
