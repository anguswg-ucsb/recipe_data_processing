
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

df["ingredient_tags"] = df.apply(lambda row: generate_tags(model, row['ingredients']), axis=1)

# df["ingredient_tags"]

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


df['simple_ingredients'] = df.apply(lambda row: replacements(row['simple_ingredients'], units_of_measurement), axis=1)
ingredients = ['2/3 cup old fashioned oats', '2/3 cup milk, of choice (cow’s, almond, soy, rice…)', 
               '2 tablespoons cocoa powder', '1 tablespoon granulated sugar', '2 bananas', '2 tablespoons semisweet chocolate chunks']


input = " ... ".join(ingredients)

model_output = model.extract_foods(input)
food_tags = []

for food in model_output[0]["Ingredient"]:
    print(f"food: {food}")
    print(f"food['text']: {food['text']}")
    food['text'].lower()
    x = "Chocolate's cake"
    x.lower()

    food_tags.append(food['text'].lower())

for ingredient in ingredients:
    print(ingredient)
    model_output = model.extract_foods('some some some 5 tablespoons butter some some like')
    model.predict('some 5 tablespoons butter some people')
    model_output
    tags = []

    for food in model_output[0]["Ingredient"]:
        tags.append(food['text'])

    food_tags.append(tags)


model_output = model.extract_foods(ingredients[1])

tags = []
for food in model_output[0]["Ingredient"]:
    tags.append(food['text'])

# [0]['text']
model_output[0]["Ingredient"][0]['text']

########################################################
############---- OPENAI GPT API ----- ##################
########################################################

def clean_ingredients_list(ingredients):
    # Define a regular expression pattern to match numbers
    # pattern = re.compile(r'\d+(\.\d+)?')
    # pattern = re.compile(r'[\d.,]+|\W+')
    # pattern = re.compile(r'[\d.,]*\s*|\W+')
    
    # pattern = re.compile(r'[^\w\s]|\d')

    # pattern = re.compile(r'[^a-zA-Z0-9\s]')

    # # Iterate through each ingredient and remove numbers
    # ingredients_without_numbers = [pattern.sub('', ingredient).strip() for ingredient in ingredients]

    # pattern = re.compile(r'[^a-zA-Z0-9\s]')
    
    # # Iterate through each ingredient
    # ingredients_without_numbers = [
    #     ''.join(c if not c.isdigit() else c[0] for c in pattern.sub('', ingredient).strip())
    #     for ingredient in ingredients
    # ]

    # return ingredients_without_numbers
    pattern = re.compile(r'[^a-zA-Z0-9\s]')
    
    # Iterate through each ingredient
    ingredients_without_numbers = [
        ''.join(c if not c.isdigit() else c[0] for c in pattern.sub('', ingredient).strip())
        for ingredient in ingredients
    ]

    return ingredients_without_numbers

df["ingredients"].apply(clean_ingredients_list)

df["simple_ingredients"] = df["ingredients"].apply(clean_ingredients_list)

df["ingredients"].values[0]

units_of_measurement = [
    "Cups",  "Cup",  "cups",   "cup",
    "Tablespoon","Tablespoons",  "Tbsp.",  "Teaspoon",   "Teaspoons",  "teaspoons",  "Tsp.", "Fluid ounce","Fl. oz.",  "Pint",
    "Pts.","Quart", "Qts.", "Gallon",  "Gal.", "Milliliter",  "Milliliters", "Millilitres",   "mL","Liter", "Liters",
    "Litres","L",   "Pound",  "Pounds",  "Lb.","Ounce",  "Ounces","Oz.",   "Gram",
    "Grams",  "Kilogram","Kilograms", "Kg", "Dash","Pinch",
    "Smidgen",   "Drop", "Handful",   "Sprig",   "Clove",   "Slice",   "Piece", "Whole",  "Package",
    "Packet",   "Can",   "Jar",
    "Stick",   "Bunch",  "Head",   "Bulb", "Dash"
]

def replacements(ingredients, replace_items):

    for i, k in enumerate(ingredients):
        # print(f"i: {i}")
        # print(f"k: {k}")
        # print(f"ingredients[i]: {ingredients[i]}")
        # print(f"ingredients[i]: {type(ingredients[i])}")

        for unit in replace_items:
            # print(f"unit: {unit}")
            # print(f"k.split(): {k.split()}")
            if unit in k.split():
                # print(f"unit {unit} in k {k}")

                ingredients[i] = k.replace(unit, "")

    return ingredients

df['simple_ingredients'] = df.apply(lambda row: replacements(row['simple_ingredients'], units_of_measurement), axis=1)



# set openai api key
# openai.api_key = Config.OPENAI_API_KEY

client = OpenAI(
    # This is the default and can be omitted
    # api_key=os.environ.get("OPENAI_API_KEY"),
    # api_key=Config.OPENAI_API_KEY,
    api_key=OPENAI_API_KEY,
)

"Can you extract the food ingredients from the rest of the extra text in this list of ingredients and return a comma-separated Python list? [' old fashioned oats', ' milk of choice cows almond soy rice', 'tablespoons cocoa powder', 'tablespoon granulated sugar', 'bananas', 'tablespoons semisweet chocolate chunks']"
gpt_list = []

for i in range(len(df.simple_ingredients.tolist())):
    print(f"i: {i}")
    row = df.simple_ingredients.tolist()[i]

    # Query question
    # prompt = f"Can you extract the food ingredients from the rest of the extra text in this list of ingredients and return a comma separated python list? {row}"
    prompt = f"Extract foods from this list ignoring all descriptive text and return a comma separated python list?: {row}"

    msg = make_message(prompt, model="gpt-3.5-turbo")

    chat_completion = client.chat.completions.create(
        messages = msg,
        model    = "gpt-3.5-turbo"
    )
    time.sleep(20)
    gpt_response = ast.literal_eval(chat_completion.choices[0].message.content)

    print(f"gpt_response: {gpt_response}")

    gpt_list.append(gpt_response)

    print(f"=========================")
# Query question
prompt = f"Can you extract the food ingredients from the rest of the extra text in this list of ingredients and return a comma separated python list? {df.simple_ingredients.values[0]}"
df.simple_ingredients.values[0]
response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "user", "content": "You are a helpful assistant."}
  ]
)

msg = make_message(prompt, model="gpt-3.5-turbo")

chat_completion = client.chat.completions.create(
    messages = msg,
    model    = "gpt-3.5-turbo"
)

import ast

gpt_response = ast.literal_eval(chat_completion.choices[0].message.content)

# Query question
prompt = f"What are the ingredients in this list? {df.ingredients.values[0]}"

def make_message(prompt, model="gpt-3.5-turbo"):

    # messages = [{"role": "user", "content": prompt}]
    messages = [{"role": "user", "content": prompt}]
    
    # response = openai.ChatCompletion.create(
    #     model=model,
    #     messages=messages,
    #     temperature=0,
    # )

    # return response.choices[0].message["content"]
    return messages

prompt = "<YOUR QUERY>"
response = get_completion(prompt)
print(response)

df.ingredient_groups.values[0]


# df.isna().sum()

# df.site_name
# df.image
# df.author
# df.title
# df.canonical_url

# ########################################################
# ##################### FoodBaseBERT #####################
# ########################################################

# from transformers import AutoTokenizer, AutoModelForTokenClassification
# from transformers import pipeline

# model_path = "Dizex/FoodBaseBERT"
# # model_path = "Shengtao/simcse_recipe_ingredients"
# # model_path = "gsliwoski/bart-food-summarizer"

# tokenizer = AutoTokenizer.from_pretrained(model_path)
# # tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2", trust_remote_code=True)

# model = AutoModelForTokenClassification.from_pretrained(model_path)
# # model = AutoModelForTokenClassification.from_pretrained(model_path)

# # model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2", torch_dtype=torch.float32, device_map="cpu", trust_remote_code=True)

# pipe = pipeline("ner", model=model, tokenizer=tokenizer)

# example = "Today's meal: Fresh olive poké bowl topped with chia seeds. Very delicious!"
# examples = """3 tablespoons (21 grams) blanched almond flour
# ... ¾ teaspoon pumpkin spice blend
# ... ⅛ teaspoon baking soda
# ... ⅛ teaspoon Diamond Crystal kosher salt
# ... 1½ tablespoons maple syrup or 1 tablespoon honey
# ... 1 tablespoon (15 grams) canned pumpkin puree
# ... 1 teaspoon avocado oil or melted coconut oil
# ... ⅛ teaspoon vanilla extract
# ... 1 large egg""".split("\n")

# ner_entity = pipe(examples)


# example = ['2/3 cup old fashioned oats',
#             '2/3 cup milk, of choice (cow’s, almond, soy, rice…)',
#               '2 tablespoons cocoa powder', 
#               '1 tablespoon granulated sugar', 
#               '2 bananas', '2 tablespoons semisweet chocolate chunks']

# example = "['2/3 cup old fashioned oats', '2/3 cup milk, of choice (cow’s, almond, soy, rice…)', '2 tablespoons cocoa powder', '1 tablespoon granulated sugar', '2 bananas', '2 tablespoons semisweet chocolate chunks']"
# ingredients = ['2/3 cup old fashioned oats', '2/3 cup milk, of choice (cow’s, almond, soy, rice…)', 
#                '2 tablespoons cocoa powder', '1 tablespoon granulated sugar', '2 bananas', '2 tablespoons semisweet chocolate chunks']

# foods = []

# for ingredient in ingredients:
#     # "a".isnumeric()

#     input_string = "".join([i for i in ingredient if not i.isnumeric()])

#     ner_entity = pipe(input_string)

#     print(f"ingredient: {ingredient}")
#     print(f"input_string: {input_string}")
#     print(f"ner_entity: {ner_entity}")

#     foods.append(ner_entity)

#     print("=" * 20)

# len(foods[0])
# foods[0]
# foods[1][4]['word']
# foods[1][4]['start']
# foods[1][4]['end']

# foods[1][5]['word']
# foods[1][5]['start']
# foods[1][5]['end']

# foods[0][1]

# ner_entity_results = pipe(example)
# print(ner_entity_results)
# ner_entity_results[0]

# ###############################################################################
# ##################### flax-community/t5-recipe-generation #####################
# ###############################################################################

# from transformers import FlaxAutoModelForSeq2SeqLM
# from transformers import AutoTokenizer
# import jax
# import torch

# MODEL_NAME_OR_PATH = "flax-community/t5-recipe-generation"
# tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME_OR_PATH, use_fast=True)
# model = FlaxAutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME_OR_PATH)

# prefix = "items: "
# # generation_kwargs = {
# #     "max_length": 512,
# #     "min_length": 64,
# #     "no_repeat_ngram_size": 3,
# #     "early_stopping": True,
# #     "num_beams": 5,
# #     "length_penalty": 1.5,
# # }

# generation_kwargs = {
#     "max_length": 512,
#     "min_length": 64,
#     "no_repeat_ngram_size": 3,
#     "do_sample": True,
#     "top_k": 60,
#     "top_p": 0.95
# }


# special_tokens = tokenizer.all_special_tokens
# tokens_map = {
#     "<sep>": "--",
#     "<section>": "\n"
# }

# def skip_special_tokens(text, special_tokens):
#     for token in special_tokens:
#         text = text.replace(token, "")

#     return text

# def target_postprocessing(texts, special_tokens):
#     if not isinstance(texts, list):
#         texts = [texts]
    
#     new_texts = []
#     for text in texts:
#         text = skip_special_tokens(text, special_tokens)

#         for k, v in tokens_map.items():
#             text = text.replace(k, v)

#         new_texts.append(text)

#     return new_texts

# def generation_function(texts):
#     _inputs = texts if isinstance(texts, list) else [texts]
#     inputs = [prefix + inp for inp in _inputs]
#     inputs = tokenizer(
#         inputs, 
#         max_length=256, 
#         padding="max_length", 
#         truncation=True, 
#         return_tensors="jax"
#     )

#     input_ids = inputs.input_ids
#     attention_mask = inputs.attention_mask

#     output_ids = model.generate(
#         input_ids=input_ids, 
#         attention_mask=attention_mask,
#         **generation_kwargs
#     )
#     generated = output_ids.sequences
#     generated_recipe = target_postprocessing(
#         tokenizer.batch_decode(generated, skip_special_tokens=False),
#         special_tokens
#     )
#     return generated_recipe

# items = [
#     "macaroni, butter, salt, bacon, milk, flour, pepper, cream corn",
#     "provolone cheese, bacon, bread, ginger"
# ]

# generated = generation_function(items)

# for text in generated:
#     sections = text.split("\n")
#     for section in sections:
#         section = section.strip()
#         if section.startswith("title:"):
#             section = section.replace("title:", "")
#             headline = "TITLE"
#         elif section.startswith("ingredients:"):
#             section = section.replace("ingredients:", "")
#             headline = "INGREDIENTS"
#         elif section.startswith("directions:"):
#             section = section.replace("directions:", "")
#             headline = "DIRECTIONS"
        
#         if headline == "TITLE":
#             print(f"[{headline}]: {section.strip().capitalize()}")
#         else:
#             section_info = [f"  - {i+1}: {info.strip().capitalize()}" for i, info in enumerate(section.split("--"))]
#             print(f"[{headline}]:")
#             print("\n".join(section_info))

#     print("-" * 130)