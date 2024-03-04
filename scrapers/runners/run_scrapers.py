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

# Import environment variables
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

# List of recipe URLs from food.com to scrape
fooddotcom_urls = build_fooddotcom_urls()

# List of recipe URLs from food.com to scrape
averiecooks_urls = build_averiecooks_urls(random_sleeps=True, start_page=2, end_page=50) # TODO: gpes through 180 but images get iffy at some point


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

# List to store JSON recipes 
output_list = []

# Scrape allrecipes.com, food.com
for url in random_urls:
    print(f"Scraping recipe from:\n - {url}")
    
    # Sleep for random amount of time between 10 and 20 seconds
    sleep_time = random.randint(1, 2)
    print(f"Sleeping for {sleep_time} seconds...")
    time.sleep(sleep_time)

    # Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # Convert recipe to json
    recipe_json = scraper.to_json()

    if "canonical_url" not in recipe_json:
        recipe_json["canonical_url"] = url
    
    if recipe_json["canonical_url"] != url:
        recipe_json["canonical_url"] = url

    output_list.append(recipe_json)

print(f"Number of recipes scraped: {len(output_list)}")


##########################################################################################################
# Step 3: 
# Convert the list of JSON recipes (output_list) to a pandas dataframe
##########################################################################################################

# Convert list of dictionaries to pandas dataframe
df = pd.DataFrame(output_list)

# fill missing values with empty string ""
df = df.fillna('')

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