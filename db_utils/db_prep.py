from sqlalchemy import create_engine

import psycopg2 
from psycopg2 import sql

import numpy as np
import pandas as pd

import json
import os

from db_utils.config import *
from db_utils.utils import *

# ------------------------------
# Create/Clean Pandas DataFrame:
# ------------------------------

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data into pandas dataframe
read_recipes = pd.read_csv(file_path)

# Clean pandas dataframe and save to parquet
recipes = clean_raw_data(read_recipes)

# make list columns into sets for insertion into postgres DB
recipes = list_to_json_dump(recipes)

# Add a unique dish_id to act as the primary key
recipes["dish_id"] = recipes.index

# Save cleaned dataframe as parquet and csv files
recipes[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_parquet('data/dish_recipes.parquet')
recipes[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_csv('data/dish_recipes.csv', index=False)

# test dataset
recipes.head(500000)[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_csv('data/dish_recipes2.csv', index=False)

# Split dataset into two tables, one for dish details and one for dish ingredients, with dish_id as the primary key
recipes[["dish_id", "dish", "ingredients"]].to_csv('data/dish_table.csv', index=False)
recipes[["dish_id", "dish", "directions"]].to_csv('data/directions_table.csv', index=False)
recipes[["dish_id", "dish", "quantities"]].to_csv('data/quantities_table.csv', index=False)

# -----------------------------------------
# Explode ingredients list into long format
# -----------------------------------------

recipes_dedup = recipes.drop_duplicates(subset=['dish'], keep='first')
# duplicate = recipes[recipes.duplicated("dish")]

# Create variable for csv file path to recipe dataset
file_path = '/Users/anguswatters/Desktop/recipes/data/raw/full_dataset.csv'

# Read CSV file containing data into pandas dataframe
read_recipes = pd.read_csv(file_path)

# Clean pandas dataframe and save to parquet
recipes = clean_raw_data(read_recipes)

# explode "ingredients" list column to make an individual row for each ingredients in each dish
df_exp = recipes.explode(['ingredients']).reset_index(drop=True)

# # select dish, ingredients, and quantities columns
# ingreds_df = df_exp[["ingredients"]]

unique_ingreds = df_exp[["ingredients"]].drop_duplicates(subset=['ingredients'], keep='first')
unique_ingreds.ingredients = unique_ingreds.ingredients.replace(r'\s+', ' ', regex=True)

unique_ingreds["ingredients_id"] = unique_ingreds.index

unique_ingreds[["ingredients_id", "ingredients"]].to_csv('data/unique_ingredients.csv', index=False)

# -----------------------------------------
# -----------------------------------------

# Connect to PostgreSQL server
conn = psycopg2.connect(
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
conn = psycopg2.connect(
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

# ------------------------------------------
# Create Table and Insert Data into Postgres
# ------------------------------------------

# Connect to PostgreSQL server
conn = psycopg2.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224'
    )

# conn = pg.connect(url)

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
conn = psycopg2.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224'
    )

# Establish DB engine
# engine = create_engine("postgresql://postgres:1224@localhost:5432/postgres")

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