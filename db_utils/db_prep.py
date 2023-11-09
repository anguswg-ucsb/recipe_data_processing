from sqlalchemy import create_engine

import psycopg2 
from psycopg2 import sql

import numpy as np
import pandas as pd

import json
import os

from db_utils.config import *
from db_utils.utils import *

# TODO: Recreate the steps outlined below to create a unique processing script for each dataset we find
# # Steps to take for each new dataset:
# 1. Specify location of dataset
# 2. Specify a location to save out the cleaned dataset
# 3. Read in Dataset
# 4. Clean + process dataset (create unique functions for each unique dataset we bring in to get them into the final output schema)
# 5. save out cleaned dataset

# TODO: Create a file that loads in all of our processed datasets, binds them together into one master dataset 
# TODO: and saves this master dataset to a specified location
# TODO: In this script (or in a separate one, whichever makes more sense), use the master dataset to generate the "unique_ingredients" dataset 

# -------------------
# Process NER dataset
# -------------------

# TODO: I'm picturing we have a folder, for example, on your Desktop named ~/Desktop/recipe_data/
# Subfolders: 
# ~/Desktop/recipe_data/
# - ~/Desktop/recipe_data/raw
#    - ~/Desktop/recipe_data/processed/raw_dataset1.csv
#    - ~/Desktop/recipe_data/processed/raw_dataset2.csv
#    - ~/Desktop/recipe_data/processed/raw_dataset3.csv
# - ~/Desktop/recipe_data/processed
#    - ~/Desktop/recipe_data/processed/cleaned_dataset1.csv
#    - ~/Desktop/recipe_data/processed/cleaned_dataset2.csv
#    - ~/Desktop/recipe_data/processed/cleaned_dataset3.csv
# - ~/Desktop/recipe_data/output
#    - ~/Desktop/recipe_data/output/dish_recipes.csv
#    - ~/Desktop/recipe_data/output/unique_ingredients.csv

source_path = "path/to/some/source/dataset"
out_path = "path/to/save/output/dataset.csv"

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

# save smaller version of dataset
recipes.head(500000)[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_csv('data/dish_recipes2.csv', index=False)

# # Split dataset into two tables, one for dish details and one for dish ingredients, with dish_id as the primary key
# recipes[["dish_id", "dish", "ingredients"]].to_csv('data/dish_table.csv', index=False)
# recipes[["dish_id", "dish", "directions"]].to_csv('data/directions_table.csv', index=False)
# recipes[["dish_id", "dish", "quantities"]].to_csv('data/quantities_table.csv', index=False)

# TODO: Process to generate unique ingredients dataset
# -----------------------------------
# Generate unique ingredients dataset
# -----------------------------------

# Drop duplicates in data
# Explode ingredients list into long format

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

# Add a unique ingredients_id to act as the primary key
unique_ingreds["ingredients_id"] = unique_ingreds.index

# reorder columns and save unique ingredients dataset 
unique_ingreds[["ingredients_id", "ingredients"]].to_csv('data/unique_ingredients.csv', index=False)

# -----------------------------------------
# -----------------------------------------