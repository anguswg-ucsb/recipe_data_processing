import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine
from db_utils.utils import *
from psycopg2 import sql
import numpy as np
import json

# ------------------------------
# Create/Clean Pandas DataFrame:
# ------------------------------

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data into pandas dataframe
read_recipes = pd.read_csv(file_path)

# recipes2 = clean_raw_data(read_recipes.head(10))
# recipes2 = list_to_json_dump(recipes2)
# list_to_json_dump(recipes2).columns

# Clean pandas dataframe and save to parquet
recipes = clean_raw_data(read_recipes)

# make list columns into sets for insertion into postgres DB
recipes = list_to_json_dump(recipes)
# recipes = fix_list_cols(recipes)
# recipes.ingredients.values[0]

recipes.to_parquet('data/dish_recipes.parquet')
recipes.to_csv('data/dish_recipes.csv', index=False)

df = recipes.head(10000)
df.to_csv('data/dish_recipes2.csv', index=False)

# df
# df.replace({'"': "'"}, regex=True)
# Explode out dataset into long format

recipes_exp = recipes[["uid", "dish", "ingredients"]].explode(['ingredients']).reset_index(drop=True)
recipes_exp.to_csv('data/dish_recipes_long.csv', index=False)

df_exp = df[["uid", "dish", "ingredients"]].explode(['ingredients']).reset_index(drop=True)
df_exp.to_csv('data/dish_recipes_long2.csv', index=False)
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

conn = pg.connect("postgres://lhachoxe:0gulr1ciEm1VoUY77wARNm9--O50pR6_@mahmud.db.elephantsql.com/lhachoxe")

# conn = pg.connect(
#     "postgres://yawswscp:vZLk0MlwMcMjVo178bYyhOjYtOUcwiyL@mahmud.db.elephantsql.com/yawswscp"
#     )

# Create cursor object to interact with the database
cur = conn.cursor()

# Establish table name to be created
table_name = 'dish_db'

# SQL query to create table if it doesn't exist
create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        dish TEXT,
        ingredients TEXT[]                
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
# engine = create_engine("postgresql://postgres:1224@localhost:5432/postgres")
engine = create_engine("postgresql://lhachoxe:0gulr1ciEm1VoUY77wARNm9--O50pR6_@mahmud.db.elephantsql.com/lhachoxe")

df = recipes.head(100000)
df = df[["dish", "ingredients"]]
# df.to_csv("data/first_1000.csv")


# Write recipes data to DB by appending to already created DB above
recipes.to_sql(
    name      = table_name, 
    con       = engine, 
    if_exists = 'append', 
    index     = False
    )

df.to_sql(
    name      = table_name, 
    con       = engine, 
    if_exists = 'append', 
    index     = False
    )

# Close cursor and connection
cur.close()
conn.close()

# -----------------------------------------
# Explode ingredients list into long format
# -----------------------------------------
# explode "ingredients" list column to make an individual row for each ingredients in each dish
df_exp = recipes.explode(['ingredients']).reset_index(drop=True)

# select dish, ingredients, and quantities columns
df_exp = df_exp[["dish", "ingredients", "quantities"]]

# tmp = df_exp[df_exp["dish"] == "Creamy Corn"]
# df_exp.columns
# tmp.ingredients

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
table_name = 'single_ingredients_db'

# SQL query to create table if it doesn't exist
create_long_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        id SERIAL PRIMARY KEY,
        dish TEXT,
        ingredients TEXT,
        quantities TEXT[]     
    )""").format(sql.Identifier(table_name))

# Excute create table command
cur.execute(create_long_table_query)

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
df_exp.to_sql(
    name      = table_name, 
    con       = engine, 
    if_exists = 'append', 
    index     = False
    )

# Close cursor and connection
cur.close()
conn.close()
