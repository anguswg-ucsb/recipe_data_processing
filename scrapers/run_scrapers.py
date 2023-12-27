
##########################################################################################################
# Step 0: 

# Import scraper <website>_utils.py files. Each _utils.py file contains helper functions to scrape a website.

# The <website>_utils.py files will typically have some sort of functionality for getting a list of recipe URLs from either base URLs or
#  depending on the website, a base_url can just be provided to the main scraper function to get the recipe data.
# Each _utils.py file WILL HAVE A "build_<site_name>_urls()" function that will return a list of recipe URLs from the website.

# TO ADD MORE RECIPE URLS:
    #  the easiest thing to do is to go into the <website>_utils.py file for the website 
    # and within the "build_<site_name>_urls()" function, add/remove to the list of "base_urls" within the function.

# TODO: 1. Find more eligible "base_urls" and add these to the "base_urls" list in each <website>_utils.py file
# TODO: 2. Add more <website>_utils.py files for other websites
# TODO: 3. Add more "build_<site_name>_urls()" functions to each _utils.py file
# TODO: 4. Consider providing "base_urls" as a parameter to the "build_<site_name>_urls()" function... 
# TODO: (Continue 4) right now i felt it was cleaner to store the list of "base_urls" within each "build_<site_name>_urls()" function
##########################################################################################################

# import helper utility functions from each <website>_utils.py in the scrapers folder
from scrapers.allrecipes.allrecipes_utils import *
from scrapers.fooddotcom.fooddotcom_utils import *

import pandas as pd
import numpy as np
from recipe_scrapers import scrape_me 

import openai
from openai import OpenAI

import ast
import time
import random 
import json

# import environment variables
from config import Config


##########################################################################################################
# Step 1: 
# Get list of recipe URLs from our websites of interest
##########################################################################################################

# List of recipe URLs from allrecipes.com to scrape
allrecipes_urls = build_allrecipes_urls(random_sleeps = True, lower_sleep=1, upper_sleep=2)
# allrecipes_urls = recipe_list
# len(allrecipes_urls)

# List of recipe URLs from food.com to scrape
fooddotcom_urls = build_fooddotcom_urls()

# len(fooddotcom_urls)

##########################################################################################################
# Step 2: 
# Go through our list of recipe URLs and scrape recipe from the page and store the returned JSON in a list
##########################################################################################################

random_urls = allrecipes_urls

random_urls.extend(fooddotcom_urls)

# Randomly shuffle URLs to make sure not to scrape from the same website over and over again
random.shuffle(random_urls)

len(random_urls)

# list to store JSON recipes 
output_list = []

# Scrape allrecipes.com
# for url in random_urls:
for url in random_urls[0:7]:
    print(f"Scraping recipe from:\n - {url}")
    
    # sleep for random amount of time between 10 and 20 seconds
    sleep_time = random.randint(1, 2)

    print(f"Sleeping for {sleep_time} seconds...")
    
    time.sleep(sleep_time)

    #  Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # convert recipe to json
    recipe_json = scraper.to_json()

    if "canonical_url" not in recipe_json:
        recipe_json["canonical_url"] = url
    
    if recipe_json["canonical_url"] != url:
        recipe_json["canonical_url"] = url

    # recipe_json['canonical_url'] 
    # recipe_json = allrecipes_scraper(url)

    output_list.append(recipe_json)

print(f"Number of recipes scraped: {len(output_list)}")

# # Scrape allrecipes.com
# for url in allrecipes_urls[0:3]:
# # for url in allrecipes_urls:
#     print(f"Scraping recipe from:\n - {url}")
    
#     #  Use recipe_scrapers to scrape recipe information
#     scraper = scrape_me(url)

#     # convert recipe to json
#     recipe_json = scraper.to_json()
#     # recipe_json = allrecipes_scraper(url)

#     output_list.append(recipe_json)

# print(f"Number of recipes scraped: {len(output_list)}")

# # Scrape food.com
# for url in fooddotcom_urls[0:3]:
# # for url in fooddotcom_urls:
#     print(f"Scraping recipe from:\n - {url}")

#     # Use recipe_scrapers to scrape recipe information
#     scraper = scrape_me(url)
    
#     random.randint(10, 20)

#     # convert recipe to json
#     recipe_json = scraper.to_json()
#     # recipe_json = fooddotcom_scraper(url)

#     output_list.append(recipe_json)

# print(f"Number of recipes scraped: {len(output_list)}")

# # check the number of keys in each recipe
# [len(i.keys()) for i in output_list]

##########################################################################################################
# Step 3: 
# Convert the list of JSON recipes (output_list) to a pandas dataframe
##########################################################################################################

# Extract foods from this list: ['23 cup old fashioned oats', '23 cup milk, of choice (cows, almond, soy, rice)', '2 tablespoons cocoa powder', '1 tablespoon granulated sugar', '2 bananas', '2 tablespoons semisweet chocolate chunks']
# Convert list of dictionaries to pandas dataframe
df = pd.DataFrame(output_list)

# fill missing values with empty string ""
df = df.fillna('')
# df.columns

# # fill missing values with empty string ""
# df = df.fillna('')

df.head()
df.columns

# [len(i) for i in df["ingredient_groups"].values]

###########################################################
############---- FoodModel GPT API ----- ##################
###########################################################

# Credit: https://github.com/chambliss/foodbert.git
# Thank you for the model and heurtistics for extracting food ingredients from a list of ingredients! 

# GitHub Repository: https://github.com/chambliss/foodbert/tree/master

# To install via pip:
# pip3 install git+https://github.com/chambliss/foodbert.git

from food_extractor.food_model import FoodModel

# Load the model from HuggingFace
model = FoodModel("chambliss/distilbert-for-food-extraction")

# function to extract food ingredients from a list of ingredients using the FoodModel
def generate_tags(model, ingredient_list):

    food_tags = []

    input = " ... ".join(ingredient_list)

    model_output = model.extract_foods(input)

    for food in model_output[0]["Ingredient"]:
        food_tags.append(food['text'].lower())

    # for ingredient in ingredient_list:
    #     # prefix_str = "some people like "
    #     prefix_str = "... "
    #     input = prefix_str + ingredient if len(ingredient.split()) < 3 else ingredient
    #     model_output = model.extract_foods(input)
    #     tags = []
    #     for food in model_output[0]["Ingredient"]:
    #         tags.append(food['text'])
    #     food_tags.append(tags)
        
    return food_tags

# Add a column to the dataframe with the food tags from the FoodModel
df["ingredient_tags"] = df.apply(lambda row: generate_tags(model, row['ingredients']), axis=1)

final_scraped = clean_scraped_data(df)

final_scraped.dtypes == recipes.dtypes

recipes.base_url.value_counts()
recipes[recipes["base_url"] == "www.foodrepublic.com"].head(1).values[0]
recipes[(recipes["base_url"] != "www.cookbooks.com") & (recipes["source"] != "cookbooks")]
recipes[recipes["base_url"] == "www.food.com"].head(1).values[0]

pd.concat([final_scraped, recipes], axis=1)
# df.columns

def clean_scraped_data(df):

    # df.columns
    # df2 = df

    # # fill missing values with empty string ""
    # df2 = df2.fillna('')

    # rename "title" column to "dish" 
    df = df.rename(columns={
        "title": "dish", 
        "canonical_url": "url",
        "instructions_list": "directions", 
        "ingredients": "quantities", 
        "ingredient_tags": "ingredients",
        "image" : "img", 
        "site_name": "source",
        "host": "base_url"
        },
        inplace=False)
    
    # # Call clean_text function to clean and preprocess 'ingredients' column
    # # convert the stringified list into a list for the ingredients, NER, and directions columns
    # df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    # df['quantities'] = df['quantities'].apply(ast.literal_eval)
    # df['directions'] = df['directions'].apply(ast.literal_eval)

    # remove any non alpha numerics and strip away any trailing/leading whitespaces
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[^A-Za-z ]', '', s).strip() for s in x])

    # split up the words in the list of ingredients
    # # # Call split_text function to split cleaned 'ingredients' column, creating a new 'split_ingredients' column
    # df['split_ingredients'] = df['ingredients'].apply(lambda x: " ".join(x).split())

    # df['split_ingredients'] = df['tmp_ingredients'].apply(split_text)

    # # Reorder columns in the DataFrame
    # df = df[['dish', 'ingredients', 'split_ingredients', "quantities", "directions"]]
    # df = df[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'id']]

    # any dishes with missing values, replace with the word "missing"
    df['dish'] = df['dish'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')

    # any category/cuisine with missing values, replace with the word "missing"
    df['category'] = df['category'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')
    df['cuisine'] = df['cuisine'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')
    
    # split the category column into a list of strings
    df['category'] = df['category'].str.split(',')
    df['cuisine'] = df['cuisine'].str.split(',')

    # santize list columns by removing unicode values
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    # df['split_ingredients']  = df['split_ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['quantities']  = df['quantities'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['directions']  = df['directions'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['category']    = df['category'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['cuisine']     = df['cuisine'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])

    # coerce all time values to Int64 and replace missing/NaN values with 0
    df['cook_time']  = pd.to_numeric(df['cook_time'], errors='coerce').astype('Int64').fillna(0)
    df['prep_time']  = pd.to_numeric(df['prep_time'], errors='coerce').astype('Int64').fillna(0)
    df['total_time'] = pd.to_numeric(df['total_time'], errors='coerce').astype('Int64').fillna(0)

    # coerce all ratings values to float64 and replace missing/NaN values with 0
    df['ratings'] = pd.to_numeric(df['ratings'], errors='coerce').astype('float64').fillna(0)

    # # List of column names that SHOULD contain list values
    # list_columns = ['ingredients', 'quantities', 'directions']
    # for column_name in list_columns:
    #     is_list_column = df[column_name].apply(lambda x: isinstance(x, list)).all()
    #     if not is_list_column:
    #         # Coerce non-list values to lists
    #         df[column_name] = df[column_name].apply(lambda x: [x] if not isinstance(x, list) else x)
    #         # df[column_name] = df[column_name].apply(ast.literal_eval)

    # add a row number column
    df['n'] = np.arange(len(df))

    # df['uid'] = df['dish'].apply(lambda x: "".join([re.sub('[^A-Za-z0-9]+', '', s).strip().lower() for s in x]))

    df['uid']  = df['dish'].str.lower()
    df['uid'] = df['uid'].str.replace('\W', '', regex=True)
    df['uid'] = df['uid'] + "_" + df['n'].astype(str)
 
    # sort by lowercased values
    def lowercase_sort(lst):
        return sorted(lst, key=lambda x: x.lower()) 
    
    # sort the ingredients in each dish
    df = df.assign(ingredients = lambda x: (x["ingredients"].apply(lowercase_sort)))

    # df = df[['uid', 'dish', 'ingredients',
    #            'split_ingredients',
    #             'quantities', 'directions', 'description', 
    #     'prep_time', 'cook_time', 'total_time', 
    #     'yields', 
    #     # 'nutrients', 
    #     'category', 'cuisine','ratings',
    #     'url', 'base_url', 'img', 'source']]
    
    # convert a dictionary column to json  function:
    def dict2json(dictionary):
        return json.dumps(dictionary, ensure_ascii=False)
    
    # convert list columns into dictonary columns
    df["ingredients"] = df.apply(lambda row: {"ingredients":row['ingredients']}, axis=1)
    # df["split_ingredients"] = df.apply(lambda row: {"split_ingredients":row['split_ingredients']}, axis=1)
    df["quantities"] = df.apply(lambda row: {"quantities":row['quantities']}, axis=1)
    df["directions"] = df.apply(lambda row: {"directions":row['directions']}, axis=1)
    df["category"] = df.apply(lambda row: {"category":row['category']}, axis=1)
    df["cuisine"] = df.apply(lambda row: {"category":row['cuisine']}, axis=1)

    # convert dictionary columns to json columns
    df["ingredients"] = df.ingredients.map(dict2json)
    # df["split_ingredients"] = df.split_ingredients.map(dict2json)
    df["quantities"] = df.quantities.map(dict2json)
    df["directions"] = df.directions.map(dict2json)
    df["category"] = df.category.map(dict2json)
    df["cuisine"] = df.cuisine.map(dict2json)

    # Add a unique dish_id to act as the primary key
    df["dish_id"] = df.index
    
    # # Reorder columns in the DataFrame
    # df = df[['uid', 'dish', 'ingredients', 'split_ingredients', "quantities", "directions", "url", "base_url", "img"]]

    # Reorder and select columns in the DataFrame
    df = df[['dish_id', 'uid', 'dish', 'ingredients', 
            #  'split_ingredients', 
             'quantities', 'directions', 'description',
            'prep_time', 'cook_time', 'total_time', 'yields',  # 'nutrients', 
            'category', 'cuisine','ratings', 'url', 'base_url', 'img', 'source']]
    
    return df


# len(df["ingredient_groups"].values[0])

########################################################
########################################################

########################################################
########################################################

import os
import subprocess
import random
import time 

# Base directory for test JSONs
test_base_dir = "/Users/anguswatters/Desktop/recipes_json/"
# test_base_dir = "/Users/anguswatters/Desktop/test_jsons/"

# S3 bucket URI to upload raw JSONs to
s3_uri = "s3://recipes-raw-bucket/"

# # list the files in the directory
filenames = os.listdir(test_base_dir)

file_paths = [os.path.join(test_base_dir, file) for file in filenames if os.path.isfile(os.path.join(test_base_dir, file)) and file != ".DS_Store"]
len(file_paths)

len(file_paths)

final_list = []

for file in file_paths:
    if file not in to_drop:
        final_list.append(file)
len(final_list)

# file_paths = [file_paths[2], file_paths[5]]
random.shuffle(file_paths)

# file = file_paths[-1]
# file_paths = file_paths[:len(file_paths)-1]

for file in file_paths:
    print(f"file: {file}")

    sleep_time = random.randint(2, 5)

    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    subprocess.run(f"aws s3 cp {file} {s3_uri}", shell=True)
    # subprocess.process.call(f"aws s3 cp {test_base_dir}{file} s3://recipe-scrapers-jsons/", shell=True)

    print(f"===" * 10)

########################################################
########################################################
import httpx

def get_headers_list(api_key):
        response = httpx.get(f"https://headers.scrapeops.io/v1/browser-headers?api_key={api_key}")

        json_response = response.json()

        return json_response.get('result', [])
    
def get_random_header(header_list):
    random_index = random.randint(0, len(header_list) - 1)
    return header_list[random_index]


# get a list of viable headers from scrapeops.io header API
header_list = get_headers_list(api_key = SCRAPE_OPS_API_KEY)
header_list

# get a random header from the list of headers from scrapeops.io header API
header = get_random_header(header_list)
test_url = "https://www.seriouseats.com/recipes/2019/10/cajun-gumbo-with-chicken-and-andouille-recipe.html"

response = httpx.get(url=test_url, headers=header, follow_redirects=True)
response.status_code

response.content