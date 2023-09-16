import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine
from db_utils.utils import *
from psycopg2 import sql

# ------------------------------
# Create/Clean Pandas DataFrame:
# ------------------------------

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data into pandas dataframe
read_recipes = pd.read_csv(file_path)

# Clean pandas dataframe and save to parquet
recipes = clean_raw_data(read_recipes.head(), 'data/dish_recipes.parquet')

# ------------------------------------------
# Create Table and Insert Data into Postgres
# ------------------------------------------

# Connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224'
    )

# Create cursor object to interact with the database
cur = conn.cursor()

# Establish table name to be created
table_name = 'dish_db'

# SQL query to create table if it doesn't exist
create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        dish TEXT,
        ingredients TEXT[],
        split_ingredients TEXT[],
        quantities TEXT[],
        directions TEXT[]                 
    )""").format(sql.Identifier(table_name))

# Excute create table command
cur.execute(create_table_query)

# Commit changes to the database
conn.commit()

# Close cursor and connection
cur.close()
conn.close()

# Connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224'
    )

# Establish DB engine
engine = create_engine("postgresql://postgres:1224@localhost:5432/postgres")

# Write recipes data to DB by appending to already created DB above
recipes.to_sql(
    name      = table_name, 
    con       = engine, 
    if_exists = 'append', 
    index     = False
    )

# Close cursor and connection
cur.close()
conn.close()