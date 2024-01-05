
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
from scrapers.averiecooks.averiecooks_utils import *
from scrapers.runners.runners_utils import *

import ast
import time
import random 
import json

import pandas as pd
import numpy as np
from recipe_scrapers import scrape_me 

# import environment variables
from config import Config

# Credit: https://github.com/chambliss/foodbert.git
# Thank you for the model and heurtistics for extracting food ingredients from a list of ingredients! 

# GitHub Repository: https://github.com/chambliss/foodbert/tree/master

# To install via pip:
# pip3 install git+https://github.com/chambliss/foodbert.git

from food_extractor.food_model import FoodModel

##########################################################################################################
# Step 1: 
# Get list of recipe URLs from our websites of interest
##########################################################################################################

# List of recipe URLs from allrecipes.com to scrape
allrecipes_urls = build_allrecipes_urls(random_sleeps = True, lower_sleep=2, upper_sleep=3)
# allrecipes_urls = build_allrecipes_urls(random_sleeps = False)

# len(allrecipes_urls)

# List of recipe URLs from food.com to scrape
fooddotcom_urls = build_fooddotcom_urls()

# len(fooddotcom_urls)

# List of recipe URLs from food.com to scrape
averiecooks_urls = build_averiecooks_urls(random_sleeps=True, start_page=2, end_page=50) # TODO: gpes through 180 but images get iffy at some point

# len(averiecooks_urls)

##########################################################################################################
# Step 2: 
# Go through our list of recipe URLs and scrape recipe from the page and store the returned JSON in a list
##########################################################################################################

random_urls = []

random_urls.extend(allrecipes_urls)

random_urls.extend(fooddotcom_urls)

random_urls.extend(averiecooks_urls)

# Randomly shuffle URLs to make sure not to scrape from the same website over and over again
random.shuffle(random_urls)

# list to store JSON recipes 
output_list = []

# Scrape allrecipes.com, food.com
for url in random_urls:
# for url in random_urls[0:7]:
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

# df.head()
# df.columns

# [len(i) for i in df["ingredient_groups"].values]

###########################################################
############ ---- FoodModel GPT API ----- #################
###########################################################

# Load the model from HuggingFace
model = FoodModel("chambliss/distilbert-for-food-extraction")

# Add a column to the dataframe with the food tags from the FoodModel
df["ingredient_tags"] = df.apply(lambda row: generate_tags(model, row['ingredients']), axis=1)

###########################################################
########### ---- FINAL CLEANING OF DATA GPT API ----- #####
###########################################################

# Final cleaning step for data
final_scraped = clean_scraped_data(df)

########################################################
########################################################