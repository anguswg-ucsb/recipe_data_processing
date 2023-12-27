# Taking the processed dataset from db_utils/processing_raw.py and converting each row to an individual JSON file to be uploaded to S3

from config import Config
import re
import pandas as pd
import os
from db_utils.utils import *


# -----------------------------------------------
# ---- Declare source and output files/paths ----
# -----------------------------------------------

# Access configuration attributes
base_dir = Config.BASE_DIR
json_dir = Config.JSON_DIR

csv_path = os.path.join(base_dir, 'raw', 'recipes.csv')

raw_dir = Config.RAW_DIR
processed_dir = Config.PROCESSED_DIR
output_dir = Config.OUTPUT_DIR
reprocess_flag = Config.REPROCESS_FLAG

# -----------------------------------------------
# ---- Compile list of files to be processed ----
# -----------------------------------------------
# Assuming raw datasets are named 'raw_dataset_<dataset_specification>.csv' and located within raw_dir

# Get a list of all files and directories in the specified folder
all_files = os.listdir(raw_dir)

# Filter out only the files from the list
csv_paths = [os.path.join(raw_dir, file) for file in all_files if os.path.isfile(os.path.join(raw_dir, file))]

# list to stores pandas dataframes
dataset_list = []

# Read in all csv files
for path in csv_paths:
    df = pd.read_csv(path)
    dataset_list.append(df)

# Concatenate all datasets into one
recipes = pd.concat(dataset_list)

# process recipes data
processed_recipes = process_dataset_recipeNLG(recipes)
processed_recipes.source.value_counts()

# remove recipes from www.cookbooks.com 
recipes_subset = processed_recipes[processed_recipes["source"] != "www.cookbooks.com"]
# tmp = processed_recipes[processed_recipes["source"] != "www.cookbooks.com"]
# tmp = tmp[tmp['url'].str.contains('www.epicurious.com/recipes/member', case=False)]

# remove recipes from www.epicurious.com/recipes/member
recipes_subset = recipes_subset[-recipes_subset['url'].str.contains('www.epicurious.com/recipes/member', case=False)]
recipes_subset = recipes_subset[-recipes_subset['url'].str.contains('recipes-plus', case=False)]
# tmp_df = recipes_subset.head(100000)

# Create a new column representing the order within each group
recipes_subset['source_order'] = recipes_subset.groupby('source').cumcount()

# Sort the DataFrame based on the new column and 'group_col'
recipes_subset = recipes_subset.sort_values(by=['source_order', 'source']).drop('source_order', axis=1)
# recipes_subset = recipes_subset.sort_values(by=['source_order', 'source'])

# Iterate over rows, convert each row to a dictionary, and save as JSON
for index, row in recipes_subset.iterrows():
    # print(f"Processing row {index}...")

    # Convert the row to a dictionary
    row_dict = row.to_dict()
    
    dish_id = row_dict["dish_id"]
    source_str = row_dict["source"]

    # Define a regular expression pattern to match special characters
    pattern = re.compile('[^a-zA-Z0-9_]')
    
    # Replace special characters with underscores
    source_str = re.sub(pattern, '_', source_str)


    # json filename
    json_filename = f"{dish_id}_{source_str}.json"
    json_filepath = os.path.join(json_dir, json_filename)

    # Save the dictionary as a JSON file
    with open(json_filepath, 'w') as json_file:
        json.dump(row_dict, json_file)

# -----------------------------------------------

# recipes_subset.source.value_counts()
# recipes_subset[recipes_subset["source"] == "Recipes1M"].url.value_counts()

# from recipe_scrapers import scrape_me
# scrap = scrape_me("www.tastykitchen.com/recipes/sidedishes/cranberry-pear-rosemary-chutney/")
# scrap.instructions()