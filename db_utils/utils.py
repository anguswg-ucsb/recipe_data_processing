import re
import pandas as pd
import ast
import numpy as np
import json

def clean_text(text):
    """
    Clean and preprocess text.

    Args:
        text (str): Input text to be cleaned.

    Returns:
        list: A list of cleaned and lowercase text elements.
    """
    
    # # Split text using double quotation marks as separators
    # clean_text = re.split('"', text)
    
    # Iterate through split text, removing non-alphanumeric characters
    for idx, val in enumerate(text):
        text[idx] = re.sub('[^A-Za-z0-9 ]+', '', val)
    
    # Create new_text list to store cleaned and lowercase text
    new_text = []

    # Iterate through cleaned text, appending to new_text if not empty
    for i in text:
        if i.strip():
            new_text.append(i.lower())
    
    return new_text
    

def split_text(text):
    """
    Split strings containing multiple words into individual strings.

    Args:
        text (list): List of text elements.

    Returns:
        list: A list of words extracted from the input text.
    """
    # Join list of text into a single string, then split into words
    text = ' '.join(text).split()
    return text


def clean_raw_data(df):
    """
    Clean up raw dataset and save to a folder as parquet.

    Args:
        df (pandas.DataFrame): Raw data to be cleaned.

    Returns:
        pandas.DataFrame
    """
    
    # Drop unnecessary columns and rename
    df = df.drop(columns=['Unnamed: 0', 'source'], axis=1)
    df = df.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients'})

    # # Add a unique 'ID' column to the DataFrame
    # df['id'] = pd.RangeIndex(start=1, stop=len(df) + 1)

    # Call clean_text function to clean and preprocess 'ingredients' column
    # convert the stringified list into a list for the ingredients, NER, and directions columns
    df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    df['quantities'] = df['quantities'].apply(ast.literal_eval)
    df['directions'] = df['directions'].apply(ast.literal_eval)

    # Apply the function to each row in the list_column
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[^A-Za-z ]', '', s).strip() for s in x])

    # split up the words in the list of ingredients
    # Call split_text function to split cleaned 'ingredients' column, creating a new 'split_ingredients' column
    df['split_ingredients'] = df['ingredients'].apply(lambda x: " ".join(x).split())
    # df['split_ingredients'] = df['tmp_ingredients'].apply(split_text)

    # # Reorder columns in the DataFrame
    # df = df[['dish', 'ingredients', 'split_ingredients', "quantities", "directions"]]
    # df = df[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'id']]

    # any dishes with missing values, replace with the word "missing"
    df['dish'] = df['dish'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')

    # santize list columns by removing unicode values
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['quantities'] = df['quantities'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['directions'] = df['directions'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])

    df['n'] = np.arange(len(df))

    # df['uid'] = df['dish'].apply(lambda x: "".join([re.sub('[^A-Za-z0-9]+', '', s).strip().lower() for s in x]))

    df['uid']  = df['dish'].str.lower()
    df['uid'] = df['uid'].str.replace('\W', '', regex=True)
    df['uid'] = df['uid'] + "_" + df['n'].astype(str)

    # Reorder columns in the DataFrame
    df = df[['uid', 'dish', 'ingredients', 'split_ingredients', "quantities", "directions"]]
    
    return df

def fix_list_cols(df):
    df['ingredients'] = df['ingredients'].apply(set)
    df['directions'] = df['directions'].apply(set)
    df['quantities'] = df['quantities'].apply(set)
    df['split_ingredients'] = df['split_ingredients'].apply(set)

    return df

def json_dump_list_cols(df):
    df['ingredients'] = df['ingredients'].apply(json.dumps)
    df['directions'] = df['directions'].apply(json.dumps)
    df['quantities'] = df['quantities'].apply(json.dumps)
    df['split_ingredients'] = df['split_ingredients'].apply(json.dumps)

    return df

def list_to_json_dump(df):

    # conversion function:
    def dict2json(dictionary):
        return json.dumps(dictionary, ensure_ascii=False)

    # df["ingredients_json"] = df.apply(lambda row: {"ingredients":row['ingredients']}, axis=1)
    # df["split_ingredients_json"] = df.apply(lambda row: {"split_ingredients":row['split_ingredients']}, axis=1)
    # df["quantities_json"] = df.apply(lambda row: {"quantities":row['quantities']}, axis=1)
    # df["directions_json"] = df.apply(lambda row: {"directions":row['directions']}, axis=1)


    # df["ingredients_json"] = df.ingredients_json.map(dict2json)
    # df["split_ingredients_json"] = df.split_ingredients_json.map(dict2json)
    # df["quantities_json"] = df.quantities_json.map(dict2json)
    # df["directions_json"] = df.directions_json.map(dict2json)
    df["ingredients"] = df.apply(lambda row: {"ingredients":row['ingredients']}, axis=1)
    df["split_ingredients"] = df.apply(lambda row: {"split_ingredients":row['split_ingredients']}, axis=1)
    df["quantities"] = df.apply(lambda row: {"quantities":row['quantities']}, axis=1)
    df["directions"] = df.apply(lambda row: {"directions":row['directions']}, axis=1)


    df["ingredients"] = df.ingredients.map(dict2json)
    df["split_ingredients"] = df.split_ingredients.map(dict2json)
    df["quantities"] = df.quantities.map(dict2json)
    df["directions"] = df.directions.map(dict2json)

    # df['ingredients'] = df['ingredients'].apply(lambda x: "{" + ", ".join(x) + "}")
    # df['ingredients'] = df['ingredients'].apply(lambda x: json.dumps(x))
    # df['split_ingredients'] = df['split_ingredients'].apply(lambda x: json.dumps(x))
    # df['quantities'] = df['quantities'].apply(lambda x: json.dumps(x))
    # df['directions'] = df['directions'].apply(lambda x: json.dumps(x))

    return df