from config import Config
import re
import pandas as pd
import os
from db_utils.utils import *

# TODO: Create a file that loads in all of our processed datasets, binds them together into one master dataset 
# TODO: and saves this master dataset to oupt_dir
# TODO: In this script (or in a separate one, whichever makes more sense), use the master dataset to generate the "unique_ingredients" dataset 

# -----------------------------------------------
# ---- Declare source and output files/paths ----
# -----------------------------------------------

# Access configuration attributes
base_dir = Config.BASE_DIR
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
file_list = [file for file in all_files if os.path.isfile(os.path.join(raw_dir, file))]

# Initialize a set to store dataset specifications
dataset_specifications = set()

# Define the regex pattern
pattern = r'raw_dataset_(.+)\.csv'

# Loop through the list of file names
for file_name in file_list:
    match = re.match(pattern, file_name)
    
    # If there is a match, add the dataset specification to the set
    if match:
        dataset_specifications.add(match.group(1))

# Generate filenames to process if reprocess_flag is True OR if file does not exist in processed directory
filenames_to_process = {}
for dataset_specification in dataset_specifications:
    file_needs_processing = reprocess_flag or not os.path.isfile(os.path.join(processed_dir, f"processed_dataset_{dataset_specification}.csv"))
    if file_needs_processing:
        filenames_to_process[dataset_specification] = f"raw_dataset_{dataset_specification}.csv"

# Generate processed filenames for files in filenames_to_process
processed_filenames = {}
for dataset_specification in filenames_to_process:
    processed_filenames[dataset_specification] = f"processed_dataset_{dataset_specification}.csv"

# Print the list of files to process
print("Files to Process:", filenames_to_process)

# Create paths to retrieve raw datasets
retrieve_raw_paths = {spec: os.path.join(raw_dir, filename) for spec, filename in filenames_to_process.items()}

# Create output paths to save processed data to
processed_paths = {spec: os.path.join(processed_dir, processed_filename) for spec, processed_filename in processed_filenames.items()}

# -----------------------------------------------
# ------------- Process datasets ----------------
# -----------------------------------------------

# Process datasets by iterating through the key-value pairs in retrieve_raw_paths
for dataset_specification, path in retrieve_raw_paths.items():

    # Read CSV file containing data into pandas dataframe
    recipes = pd.read_csv(path)

    # Generate the function name based on the dataset specification
    function_name = f'process_dataset_{dataset_specification}'

    # Dynamic function call based on the dataset specification
    try:
        process_function = globals()[function_name]
        recipes = process_function(recipes)
    except KeyError:
        print(f"No matching function found for name: {function_name}")

    # Save processed datasets as CSV to the output directory
    recipes.to_csv(f"{output_dir}dish_recipes.csv", index=False)
    recipes.head(500000).to_csv(f"{output_dir}dish_recipes_small.csv", index=False)

# -----------------------------------------------
# ----- Generate unique ingredients dataset -----
# -----------------------------------------------

# Read in new data if necessary
recipes = pd.read_csv(f"{output_dir}dish_recipes.csv")

unique_ingredients = create_unique_ingredients(recipes)
unique_ingredients_small = create_unique_ingredients(recipes.head(500000))

# reorder columns and save unique ingredients dataset 
unique_ingredients.to_csv(f"{output_dir}unique_ingredients.csv", index=False)
unique_ingredients_small.to_csv(f"{output_dir}unique_ingredients_small.csv", index=False)
