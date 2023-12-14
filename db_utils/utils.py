import re
import pandas as pd
import ast
import numpy as np
import json

# TODO: I'm not sure which of these functions is deletable and which are being used in db_prep.py, so I'm leaving them all here for now
# TODO: consilidate all of the cleaning functions into one function that takes in a dataframe and returns a cleaned dataframe
# TODO: this process is going to have to be unique per dataset, so we'll need to create a new function for each dataset we bring in
# TODO: Also create a function that takes in a list of file paths and binds them together into one master dataframe
# TODO: Create a function that creates the unique_ingredients dataset

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

# Extract base URLs from list of URLs in recipeNLG dataset
def extract_base_url(url):

    extensions = ['.com', '.net', '.org', '.io', '.dev', '.ai', '.inc', 'co']

    for extension in extensions:
        # # print(f"Extracting base URLs for extension: {extension}")
        pattern = re.compile(fr'(www\..*?{re.escape(extension)})')
        # pattern = re.compile(fr'(www\..*?\{extension})')

        if pattern.search(url):
            return pattern.search(url).group(1)

    return "NA"

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
    df = df.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients', 'link':'url'})

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

    # sort by lowercased values
    def lowercase_sort(lst):
        return sorted(lst, key=lambda x: x.lower()) 
    
    # sort the ingredients in each dish
    df = df.assign(ingredients = lambda x: (x["ingredients"].apply(lowercase_sort)))

    # create a base_url column from the URL column
    df = df.assign(base_url = lambda x: (x["url"].apply(extract_base_url)))

    # create a column for the image url with a default value of "NA"
    df = df.assign(img = "NA")

    # Reorder columns in the DataFrame
    df = df[['uid', 'dish', 'ingredients', 'split_ingredients', "quantities", "directions", "url", "base_url", "img"]]
    
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

# Create proper JSON columns in NER dataset
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

def process_dataset_recipeNLG(df):
    """Process recipeNLG dataset

    Args:
        df (pandas.DataFrame): Raw recipeNLG dataset

    Returns:
        pandas.DataFrame: Cleaned recipeNLG dataset
    """
    # df = recipes.head(500000)
    # df = recipes[1200000:1250000]
    # df = recipes[1750000:2000000]
    
    # clean_raw_data(df)

    # Clean pandas dataframe and save to parquet
    df = clean_raw_data(df)

    # make list columns into sets for insertion into postgres DB
    df = list_to_json_dump(df)

    # Add a unique dish_id to act as the primary key
    df["dish_id"] = df.index

    # Save cleaned dataframe as parquet and csv files
    df = df[['dish_id', 'dish', 'ingredients', 'quantities', 'directions', 'url', 'base_url', 'img']]
    # recipes[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_parquet('data/dish_recipes.parquet')
    # recipes[['dish_id', 'dish', 'ingredients', 'quantities', 'directions']].to_csv('data/dish_recipes.csv', index=False)

    return df


def create_unique_ingredients(df):
    """Create unique ingredients dataset

    Args:
        df (pandas.DataFrame): Raw NER dataset

    Returns:
        pandas.DataFrame: Unique ingredients dataset
    """

    # df = recipes2.head(5)

    # # convert json dictionary column to dictionary and then list
    # df['ingredients'].apply(json.loads)

    # Select just ingredients column
    df = df[["ingredients"]]

    df["ingredients"] = df["ingredients"].apply(lambda row: json.loads(row)['ingredients'])

    # explode "ingredients" list column to make an individual row for each ingredients in each dish
    df = df.explode(['ingredients']).reset_index(drop=True)

    # replace whitespace with single space
    df["ingredients"] = df["ingredients"].replace(r'\s+', ' ', regex=True)

    # convert all characters in 'ingredients' to lowercase
    df['ingredients'] = df['ingredients'].str.lower()

    # CREATE FREQUENCY DATAFRAME
    # ingreds_df = df[["ingredients"]]
    freq_df = df[["ingredients"]].value_counts()

    # convert series to dataframe
    freq_df = pd.DataFrame(freq_df)

    # reset index
    freq_df = freq_df.reset_index()

    # select unique ingredients
    unique_ingreds = df[["ingredients"]].drop_duplicates(subset=['ingredients'], keep='first')

    # merge counts with unique ingredients
    unique_ingreds = pd.merge(unique_ingreds, freq_df, on='ingredients', how='left')

    # replace NaN values with 0
    unique_ingreds['count'].fillna(0, inplace=True)

    # Convert the 'float_column' to an integer
    unique_ingreds['count'] = unique_ingreds['count'].astype(int)

    # sort unique_ingreds by count in descending order
    unique_ingreds = unique_ingreds.sort_values(by='count', ascending=False)

    # add unique id for each ingredient
    unique_ingreds["ingredients_id"] = unique_ingreds.index

    # reorder columns
    unique_ingreds = unique_ingreds[["ingredients_id", "ingredients", "count"]]

    # # save unique ingredients dataframe to csv
    # unique_ingreds[["ingredients_id", "ingredients", "count"]].to_csv('data/unique_ingredients.csv', index=False)

    return unique_ingreds

# tmp = recipes[recipes["dish"] == "Broken Glass Dessert"]
# # tmp = recipes[recipes["dish_id"] == 14670]
# xx = json.loads(tmp.ingredients.values[0])
# tmp
# xx["ingredients"]
# tmp[["dish"]].drop_duplicates(subset=['dish'], keep='first')
