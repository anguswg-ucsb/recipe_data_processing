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

# save URL dataframe 
url_df = processed_recipes[["uid", "url"]]

# save URL dataframe to csv
url_path = '/Users/anguswatters/Desktop/recipe_urls/url_dataset_recipeNLG.csv'

# save URL dataframe to csv
url_path = '/Users/anguswatters/Desktop/recipe_urls/url_dataset_recipeNLG.csv'

# save to csv
url_df.to_csv(url_path, index=False)

# save URL dataframe to csv
test_url_path = '/Users/anguswatters/Desktop/recipe_urls/url_test_dataset_recipeNLG.csv'

# save to csv
url_df.head(42)
url_df.head(42).to_csv(test_url_path, index=False)
processed_recipes.columns

test_model_df = recipes[["title", "ingredients"]].head(1000)
test_model_df['ingredients'] = test_model_df['ingredients'].apply(ast.literal_eval)

# import model interface from Hugging Face model 
from food_extractor.food_model import FoodModel

# path to saved distilbert FoodModel from Hugging Face
model_path = './model/chambliss-distilbert-for-food-extraction'
# model_path = './extract_ingredients_lambda/model/chambliss-distilbert-for-food-extraction'

# Load the model from HuggingFace
# model = FoodModel(model_path)
model = FoodModel("chambliss/distilbert-for-food-extraction")

# # function to extract food ingredients from a list of ingredients using the FoodModel
def generate_tags(model, ingredient_list):

    food_tags = []

    input = " ... ".join(ingredient_list)

    model_output = model.extract_foods(input)

    for food in model_output[0]["Ingredient"]:
        food_tags.append(food['text'].lower())
        
    return food_tags

import time
# time_result = {"nrows": [], "time": []}
# row_ranges = range(1, 1100, 100)
row_ranges = range(1, 900, 100)
time_result = {i : 0 for i in row_ranges}

for i in row_ranges:
    print(f"i: {i}")
    print(f"Testing first {i} rows...")
    
    test_model_df = recipes[["title", "ingredients"]].head(i)
    test_model_df['ingredients'] = test_model_df['ingredients'].apply(ast.literal_eval)

    # Record the start time
    start_time = time.time()

    # Your code to be timed
    test_model_df["food_tags"] = test_model_df["ingredients"].apply(lambda x: generate_tags(model, x))

    # Record the end time
    end_time = time.time()

    # Calculate the elapsed time
    elapsed_time = end_time - start_time

    elapsed_time = round(elapsed_time, 2)

    print(f"Elapsed time: {elapsed_time} seconds")
    
    time_result[i] = elapsed_time
    print(f"time_result: {time_result}")
    print(f"===" * 5)

import matplotlib.pyplot as plt

# Extract keys and values from the dictionary
keys = list(time_result.keys())
values = list(time_result.values())

# Create a scatter plot
plt.scatter(keys, values)

# Add labels and title
plt.xlabel('Keys')
plt.ylabel('Values')
plt.title('Scatter Plot of Dictionary Values')

# Show the plot
plt.show()

print(f"Elapsed time: {elapsed_time} seconds")

test_model_df["food_tags"] = test_model_df["ingredients"].apply(lambda x: generate_tags(model, x))
test_model_df
test_model_df["food_tags"]
test_model_df["ingredients"].values.tolist()[0]
1000000/1000

test_model_df
test_model_df["food_tags"] = test_model_df["ingredients"].apply(lambda x: generate_tags(model, x))

# Iterate over rows, convert each row to a dictionary, and save as JSON
for index, row in processed_recipes.iterrows():
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
        
import os
import shutil

# os.path.exists(source_dir)

def create_subdirectories(source_dir, dest_dir, files_per_directory):

    # Ensure the destination directory exists
    os.makedirs(dest_dir, mode=0o777, exist_ok=True)

    # Get a list of all JSON files in the source directory
    json_files = [f for f in os.listdir(source_dir) if f.endswith('.json')]
 
    # Create subdirectories and move files
    for i in range(0, len(json_files), files_per_directory):
    # for i in range(0, 40, files_per_directory):

        print(f"i: {i}")
        print(f"i + files_per_directory: {i + files_per_directory}")

        subdirectory_name = f'subdirectory_{i // files_per_directory + 1}'
        subdirectory_path = os.path.join(dest_dir, subdirectory_name)

        print(f"subdirectory_path: {subdirectory_path}")
        print(f"subdirectory_name: {subdirectory_name}")

        os.makedirs(subdirectory_path, exist_ok=True)

        # Move files to the subdirectory
        for file_name in json_files[i:i + files_per_directory]:
            source_path = os.path.join(source_dir, file_name)
      
            dest_path = os.path.join(subdirectory_path, file_name)
            print(f"source_path: {source_path}")
            print(f"dest_path: {dest_path}")
            shutil.move(source_path, dest_path)
            print(f"--" * 5)
        print(f"=========" * 4)
