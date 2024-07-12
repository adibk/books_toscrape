import pandas as pd

import mysql.connector
from mysql.connector import Error

import subprocess

import scrape

def connect_to_database(database, host='localhost', user='root', password='password', v=True):
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            db_info = connection.get_server_info()
            if v:
                print("Connected to MySQL Server version", db_info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            if v:
                print("You're connected to database:", record)
            return connection, cursor

    except Error as e:
        if v: 
            print("Error while connecting to MySQL", e)
    return None

def close_connection(connection, cursor):
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()
        print("MySQL connection is closed")

def show_databases(connection):
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Databases:")
        for database in databases:
            print(database[0])  
    except Error as e:
        print("Error executing SHOW DATABASES command", e)

def execute_query(connection, cursor, query, params=None):
    try:
        cursor.execute(query, params)
        if query.strip().lower().startswith('select') or query.strip().lower().startswith('show'):
            result = cursor.fetchall()
            return result
        else:
            connection.commit()
            return cursor.rowcount
    except Error as e:
        print("Error executing query:", e)
        return None

def put_res(results, query_type="SELECT"):
    if not results:
        print("No results found.")
        return

    if query_type.lower() in ["select", "show"]:
        for row in results:
            print(row)
    else:
        print(f"Affected rows: {results}")


def create_database(connection, db_name):
    cursor = None
    try:
        cursor = connection.cursor()
        query = f"SHOW DATABASES LIKE '{db_name}'"
        result = execute_query(connection, cursor, query)
        if result:
            print(f"Database '{db_name}' already exists.")
        else:
            query = f"CREATE DATABASE {db_name}"
            result = execute_query(connection, cursor, query)
            print(f"Database '{db_name}' created successfully.")
            show_databases(connection)
    finally:
        if cursor:
            cursor.close()

def map_dtype_to_mysql(dtype, smallint=False):
    if pd.api.types.is_integer_dtype(dtype):
        if smallint:
            return "SMALLINT"
        return "INT"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "DATETIME"
    else:
        return "VARCHAR(255)"
    
def create_table_from_dataframe(connection, table_name, dataframe, column_types=None, foreign_keys=None, smallint=False):
    cursor = None
    try:
        cursor = connection.cursor()
        columns = dataframe.columns
        types = dataframe.dtypes

        column_definitions = []
        for col in columns:
            if column_types and col in column_types:
                col_type = column_types[col]
            else:
                col_type = map_dtype_to_mysql(types[col],  smallint=smallint)
            column_definitions.append(f"{col} {col_type}")

        if foreign_keys:
            for col, ref in foreign_keys.items():
                column_definitions.append(f"FOREIGN KEY ({col}) REFERENCES {ref}")

        query = f"CREATE TABLE {table_name} ({', '.join(column_definitions)})"
        result = execute_query(connection, cursor, query)
        print(f"Table '{table_name}' created successfully.")
    finally:
        if cursor:
            cursor.close()

def insert_dataframe_to_table(connection, table_name, dataframe):
    cursor = None
    try:
        cursor = connection.cursor()
        for _, row in dataframe.iterrows():
            columns = ", ".join(row.index)
            values = ", ".join(["%s"] * len(row))
            # row_values = [None if pd.isna(value) else value for value in row] 
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
            cursor.execute(query, tuple(row))
            # cursor.execute(query, tuple(row_values))
        connection.commit()
        print(f"Data inserted successfully into '{table_name}' table.")
    except Error as e:
        print("Error inserting data:", e)
    finally:
        if cursor:
            cursor.close()


def exec_sh(file_name, path='sh'):
    bash_script_path = f"{path}/{file_name}.sh"

    try:
        # Run the bash script
        result = subprocess.run([bash_script_path], check=True, text=True, capture_output=True)
        
        # Print the output of the script
        if result.stdout:
            print("Script output:")
            print(result.stdout)
        
        # Print the error output of the script if any
        if result.stderr:
            print("Script error output:")
            print(result.stderr)
        
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the script: {e}")



db_name = 'create_db'
exec_sh(db_name)
con, cur = connect_to_database(db_name) 

