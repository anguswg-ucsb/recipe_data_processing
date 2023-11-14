import pandas as pd
import os
from db_utils.utils import *
# from db_utils.config import *

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
#    - ~/Desktop/recipe_data/processed/raw_dataset_author1.csv
#    - ~/Desktop/recipe_data/processed/raw_dataset_author2.csv
#    - ~/Desktop/recipe_data/processed/raw_dataset_author3.csv
# - ~/Desktop/recipe_data/processed
#    - ~/Desktop/recipe_data/processed/processed_dataset_author1.csv
#    - ~/Desktop/recipe_data/processed/processed_dataset_author2.csv
#    - ~/Desktop/recipe_data/processed/processed_dataset_author3.csv
# - ~/Desktop/recipe_data/output
#    - ~/Desktop/recipe_data/output/dish_recipes.csv
#    - ~/Desktop/recipe_data/output/unique_ingredients.csv

# -----------------------------------------------
# ---- Declare source and output files/paths ----
# -----------------------------------------------
# TODO: move to config
user = "mkayeterry"

# Create path to base directory
base_dir = os.path.join("/Users", user, "Desktop", "recipe_data")

# -------------------------------------------------------------------------

# TODO: auto rip from file, dont move to config
dataset_specification = "glorf"
filename = f"raw_dataset_{dataset_specification}.csv"

# -------------------------------------------------------------------------
# TODO: move to config

# Define subdirectory paths
raw_dir = os.path.join(base_dir, "raw")
processed_dir = os.path.join(base_dir, "processed")
output_dir = os.path.join(base_dir, "output")

# Create base directory and subdirectories if they do not exist
directories = [base_dir, raw_dir, processed_dir, output_dir]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory created: {directory}")

# -------------------------------------------------------------------------

# TODO: dont move to cofig 
# Create path to retrieve raw data
retrieve_raw_path = os.path.join(raw_dir, filename)

# Create a name for processed dataset following pattern: "processed_<original_file_name_and_extension>"
processed_filename = f"processed_{filename[4:]}"

# Create output path to save processed data to
processed_path = os.path.join(processed_dir, processed_filename)

# -------------------------
# ---- Process dataset ----
# -------------------------

# Read CSV file containing data into pandas dataframe
recipes = pd.read_csv(retrieve_raw_path)

function_name = f'process_dataset_{dataset_specification}'

# Dynamic function call based on the dataset specification
try:
    process_function = globals()[function_name]
    recipes = process_function(recipes)
except KeyError:
    print(f"No matching function found for name: {function_name}")

# Save processed datasets as CSV to output directory
recipes.to_csv(f"{output_dir}dish_recipes.csv", index = False)
recipes.head(500000).to_csv(f"{output_dir}dish_recipes_small.csv", index = False)


# -----------------------------------
# Generate unique ingredients dataset
# -----------------------------------

# Read in new data if necessary
recipes = pd.read_csv(f"{output_dir}dish_recipes.csv")

unique_ingredients = create_unique_ingredients(recipes)
unique_ingredients_small = create_unique_ingredients(recipes.head(500000))

# reorder columns and save unique ingredients dataset 
unique_ingredients.to_csv(f"{output_dir}unique_ingredients.csv", index=False)
unique_ingredients_small.to_csv(f"{output_dir}unique_ingredients_small.csv", index=False)

