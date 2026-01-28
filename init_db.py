import sqlite3
import os

# Define the path to the database file (it will be created here)
DB_PATH = 'stockedup.db'
# Define the path to your SQL schema file (should be in the same folder)
SCHEMA_PATH = 'create.sql'

print(f"Looking for database at: {os.path.abspath(DB_PATH)}")
print(f"Looking for schema at: {os.path.abspath(SCHEMA_PATH)}")

# Delete the database file if it already exists (to ensure a fresh start)
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")
    except OSError as e:
        print(f"Error removing existing database {DB_PATH}: {e}. Check file permissions.")
        exit() # Stop if we can't remove the old one

try:
    # Check if schema file exists before connecting
    if not os.path.exists(SCHEMA_PATH):
         raise FileNotFoundError(f"Error: Could not find the schema file at {SCHEMA_PATH}")

    # Connect to the database (this creates the file if it doesn't exist)
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    print(f"Database file created/connected: {DB_PATH}")

    # Read the SQL commands from the create.sql file
    with open(SCHEMA_PATH, 'r') as f:
        sql_script = f.read()
        print(f"Read schema from: {SCHEMA_PATH}")

    # Execute the SQL script to create tables
    # Using executescript for potentially multiple SQL statements in the file
    cursor.executescript(sql_script)
    print("Executed SQL script to create tables.")

    # Commit the changes (important!)
    connection.commit()
    print("Database changes committed.")

except sqlite3.Error as e:
    print(f"An SQLite error occurred: {e}")
    # Attempt to clean up potentially incomplete DB file on error
    if 'connection' in locals() and connection:
        connection.close()
    if os.path.exists(DB_PATH):
        # Be cautious about deleting if connection failed initially
        # os.remove(DB_PATH)
        pass # Decide if cleanup is desired

except FileNotFoundError as e:
    print(e) # Already formatted error message

except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    # Always ensure the connection is closed if it was opened
    if 'connection' in locals() and connection:
        connection.close()
        print("Database connection closed.")

# Final check if DB file exists
if os.path.exists(DB_PATH):
    print("Database initialization process finished. Database file exists.")
else:
    print("Database initialization process finished. Database file was NOT created (check errors).")