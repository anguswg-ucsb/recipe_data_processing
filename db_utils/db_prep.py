import pandas as pd
import psycopg2 as pg
from psycopg2 import sql
from sqlalchemy import create_engine
from db_utils.utils import *
import io 



# ------------------------------
# Create/Clean Pandas DataFrame:
# ------------------------------

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data
recipes = pd.read_csv(file_path)

recipes = clean_raw_recipes(recipes, 'data/dish_recipes.parquet')

# -----------------------------------
# Create table and insert data into Postgres
# -----------------------------------

# connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'anguswatters', 
    password = '1224')

# make cursor for DB connection
cursor = conn.cursor()

# name table
table_name = "dish_db"

# SQL query to create table if it doesn't exist
create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        dish TEXT,
        ingredients TEXT[],
        split_ingredients TEXT[],
        quantities TEXT[],
        directions TEXT[],
        link CHAR(255),
        ID INTEGER
    )
""").format(sql.Identifier(table_name))

# excute create table command
cursor.execute(create_table_query)

# commit create table querry to DB
conn.commit()

# database engine
engine = create_engine("postgresql://anguswatters:1224@localhost:5432/postgres")

# Write recipes data to DB by appending to already created DB above
recipes.head().to_sql(table_name, engine, if_exists='append', index=False)

# close cursor and connection
cursor.close()
conn.close()

# ------------------------------
# Create/Clean Pandas DataFrame:
# ------------------------------

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data
read_recipes = pd.read_csv(file_path)

# Drop unnecessary columns and rename
recipes = read_recipes.drop(columns=['Unnamed: 0', 'source'], axis=1)
recipes = recipes.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients'})

# Add a unique 'ID' column to the DataFrame
recipes['ID'] = pd.RangeIndex(start=1, stop=len(recipes) + 1)

# Call clean_text function to clean and preprocess 'ingredients' column
recipes['ingredients'] = recipes['ingredients'].apply(clean_text)

# Call split_text function to split cleaned 'ingredients' column, creating a new 'split_ingredients' column
recipes['split_ingredients'] = recipes['ingredients'].apply(split_text)

# Reorder columns in the DataFrame
recipes = recipes[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'ID']]

# Create DataFrame for image links, retaining only relevent columns
links = recipes.copy()
links = links.drop(columns=['ingredients', 'split_ingredients', 'quantities', 'directions'], axis=1)

# Save cleaned recipes DataFrame to a Parquet file
recipes.to_parquet('data/dish_recipes.parquet')

# Save image links DataFrame to a Parquet file
links.to_parquet('data/image_links.parquet')

# -------------------------------------------
# Load Pandas DataFrame to Postgres Database:
# -------------------------------------------

# Connect to the PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224')

# Create cursor object to interact with the database
cur = conn.cursor()

# Create table 'dish_db' if it doesn't already exist
cur.execute("""CREATE TABLE IF NOT EXISTS dish_db (
    ingredients TEXT, 
    split_ingredients TEXT, 
    quantities TEXT, 
    directions TEXT, 
    link CHAR(255)
    id INTEGER)""")

# Create table 'link_db' if it doesn't already exist
cur.execute("""CREATE TABLE IF NOT EXISTS link_db (
    dish CHAR(255), 
    link CHAR(255)
    id INTEGER)""")

# Commit changes to the database
conn.commit()

# Close cursor and connection
cur.close()
conn.close()

# Create engine to connect to the PostgreSQL database
engine = create_engine("postgresql://postgres:1224@localhost:5432/postgres")

# Load 'recipes' & 'links' DFs into the database, replacing if they already exist
recipes.head().to_sql('dish_db', engine, if_exists='replace')
links.head().to_sql('link_db', engine, if_exists='replace')


# -------------------------------
# SQL Queries to Access database:
# -------------------------------
