import json
import re
import ast
import time
import random
import pandas as pd
import numpy as np

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



# from io import StringIO

# import boto3
# import pandas as pd


# # Create a DataFrame
# data = {'uid': [1, 2, 3],
#         'url': ['https://example1.com', 'https://example2.com', 'https://example3.com']}

# df = pd.DataFrame(data)

# # Save the DataFrame to a CSV file
# file_path = '/Users/anguswatters/Desktop/test_split_df.csv'
# df.to_csv(file_path, index=False)

# print(f"DataFrame saved to: {file_path}")

# json_buffer = StringIO()
            
# df2 = pd.read_csv(file_path)

# df2.to_json(json_buffer, orient='index')

# json.loads(json_buffer.getvalue())