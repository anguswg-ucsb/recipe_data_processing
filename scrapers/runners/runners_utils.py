import json
import re
import ast
import time
import random
import pandas as pd
import numpy as np

# Function to extract food ingredients from a list of ingredients using the FoodModel
def generate_tags(model, ingredient_list):

    food_tags = []

    input = " ... ".join(ingredient_list)

    model_output = model.extract_foods(input)

    for food in model_output[0]["Ingredient"]:
        food_tags.append(food['text'].lower())
        
    return food_tags


def clean_scraped_data(df):

    # Rename "title" column to "dish" 
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

    # Remove any non alpha numerics and strip away any trailing/leading whitespaces
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[^A-Za-z ]', '', s).strip() for s in x])

    # Any dishes with missing values, replace with the word "missing"
    df['dish'] = df['dish'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')

    # Any category/cuisine with missing values, replace with the word "missing"
    df['category'] = df['category'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')
    df['cuisine'] = df['cuisine'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')
    
    #Ssplit the category column into a list of strings
    df['category'] = df['category'].str.split(',')
    df['cuisine'] = df['cuisine'].str.split(',')

    # Santize list columns by removing unicode values
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['quantities']  = df['quantities'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['directions']  = df['directions'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['category']    = df['category'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['cuisine']     = df['cuisine'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])

    # Coerce all time values to Int64 and replace missing/NaN values with 0
    df['cook_time']  = pd.to_numeric(df['cook_time'], errors='coerce').astype('Int64').fillna(0)
    df['prep_time']  = pd.to_numeric(df['prep_time'], errors='coerce').astype('Int64').fillna(0)
    df['total_time'] = pd.to_numeric(df['total_time'], errors='coerce').astype('Int64').fillna(0)

    # Coerce all ratings values to float64 and replace missing/NaN values with 0
    df['ratings'] = pd.to_numeric(df['ratings'], errors='coerce').astype('float64').fillna(0)

    # Add a row number column
    df['n'] = np.arange(len(df))
    df['uid']  = df['dish'].str.lower()
    df['uid'] = df['uid'].str.replace('\W', '', regex=True)
    df['uid'] = df['uid'] + "_" + df['n'].astype(str)
 
    # Sort by lowercased values
    def lowercase_sort(lst):
        return sorted(lst, key=lambda x: x.lower()) 
    
    # Sort the ingredients in each dish
    df = df.assign(ingredients = lambda x: (x["ingredients"].apply(lowercase_sort)))
    
    # Convert a dictionary column to json  function:
    def dict2json(dictionary):
        return json.dumps(dictionary, ensure_ascii=False)
    
    # Convert list columns into dictonary columns
    df["ingredients"] = df.apply(lambda row: {"ingredients":row['ingredients']}, axis=1)
    df["quantities"] = df.apply(lambda row: {"quantities":row['quantities']}, axis=1)
    df["directions"] = df.apply(lambda row: {"directions":row['directions']}, axis=1)
    df["category"] = df.apply(lambda row: {"category":row['category']}, axis=1)
    df["cuisine"] = df.apply(lambda row: {"category":row['cuisine']}, axis=1)

    # Convert dictionary columns to json columns
    df["ingredients"] = df.ingredients.map(dict2json)
    df["quantities"] = df.quantities.map(dict2json)
    df["directions"] = df.directions.map(dict2json)
    df["category"] = df.category.map(dict2json)
    df["cuisine"] = df.cuisine.map(dict2json)

    # Add a unique dish_id to act as the primary key
    df["dish_id"] = df.index

    # Reorder and select columns in the DataFrame
    df = df[['dish_id', 'uid', 'dish', 'ingredients', 
             'quantities', 'directions', 'description',
            'prep_time', 'cook_time', 'total_time', 'yields',
            'category', 'cuisine','ratings', 'url', 'base_url', 'img', 'source']]
    
    return df
