import re
import pandas as pd
import ast
import numpy as np
import json
import os 
import urllib.parse


def clean_text(text):
    """
    Clean and preprocess text.

    Args:
        text (str): Input text to be cleaned.

    Returns:
        list: A list of cleaned and lowercase text elements.
    """
    
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

    extensions = ['.com', '.net', '.org', '.io', '.dev', '.ai', '.inc', '.co']

    for extension in extensions:
        # Construct regex pattern
        pattern = re.compile(fr'(www\..*?{re.escape(extension)})')

        # Get matches
        matches = pattern.findall(url)

        # If matches are found, return the first one
        if matches:
            return matches[0]

    return "NA"


# Extract base URLs from list of URLs in recipeNLG dataset
def extract_site_source(url):

    pattern = r"https://(?:www\.)?(.*?).com|.net|.io|.org|.dev|.ai|.inc|.co"

    regex_pattern = re.compile(pattern)

    if regex_pattern.search(url):
        return regex_pattern.search(url).group(1)

    return "NA"


# Extract base URLs from list of URLs in recipeNLG dataset
def extract_base_url2(url):
    base_url = os.path.dirname(url)

    if base_url:
        return base_url
    
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
    df = df.drop(columns=['Unnamed: 0'], axis=1)
    df = df.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients', 'link':'url'})

    # Call clean_text function to clean and preprocess 'ingredients' column
    # Convert the stringified list into a list for the ingredients, NER, and directions columns
    df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    df['quantities'] = df['quantities'].apply(ast.literal_eval)
    df['directions'] = df['directions'].apply(ast.literal_eval)

    # Apply the function to each row in the list_column
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[^A-Za-z ]', '', s).strip() for s in x])

    # Any dishes with missing values, replace with the word "missing"
    df['dish'] = df['dish'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')
    
    # Santize list columns by removing unicode values
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['quantities'] = df['quantities'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['directions'] = df['directions'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])

    df['n'] = np.arange(len(df))

    df['uid']  = df['dish'].str.lower()
    df['uid'] = df['uid'].str.replace('\W', '', regex=True)
    df['uid'] = df['uid'] + "_" + df['n'].astype(str)

    # Sort by lowercased values
    def lowercase_sort(lst):
        return sorted(lst, key=lambda x: x.lower()) 
    
    # Sort the ingredients in each dish
    df = df.assign(ingredients = lambda x: (x["ingredients"].apply(lowercase_sort)))
    
    # Add "https://" to the beginning of each URL if it doesn't already start with it
    df['url'] = df['url'].apply(lambda x: "https://" + x if not x.startswith("https://") else x)

    # Create a base_url column from the URL column
    df = df.assign(base_url = lambda x: (x["url"].apply(extract_base_url2)))

    # Create a column for the image url with a default value of "NA"
    df = df.assign(img = "NA")
    
    # Add columns with missing values of the specified types
    df['description'] = ""  # Int64 with missing values
    df['prep_time']  = 0    # int64 with missing values
    df['cook_time']  = 0    # int64 with missing values
    df['total_time'] = 0    # int64 with missing values
    df['ratings']    = 0.0  # float64 with missing values

    # Coerce all time values to Int64 and replace missing/NaN values with 0
    df['cook_time']  = pd.to_numeric(df['cook_time'], errors='coerce').astype('Int64').fillna(0)
    df['prep_time']  = pd.to_numeric(df['prep_time'], errors='coerce').astype('Int64').fillna(0)
    df['total_time'] = pd.to_numeric(df['total_time'], errors='coerce').astype('Int64').fillna(0)

    # Coerce all ratings values to float64 and replace missing/NaN values with 0
    df['ratings'] = pd.to_numeric(df['ratings'], errors='coerce').astype('float64').fillna(0) 
    df['yields']    = ""  # String with missing values
    df['category']  = [None] * len(df)  # List of strings with missing values
    df['cuisine']   = [None] * len(df)  # List of strings with missing values

    # Extract the text between the two periods
    df["source2"] =df["base_url"].astype(str).apply(lambda x: urllib.parse.urlparse(x).hostname)

    # Conditionally assign values to 'source2' based on 'source'
    df['source'] = np.where(df['source'] == 'Gathered', df['source2'], df['source'])

    # Drop the 'source2' column
    df.drop(columns=['source2'], inplace=True)

    # Reorder and select columns in dataFrame
    df = df[['uid', 'dish', 'ingredients', 
            'quantities', 'directions', 'description',
            'prep_time', 'cook_time', 'total_time', 'yields',
            'category', 'cuisine','ratings', 'url', 
            'base_url',
            'img', 'source']]
    
    return df


def fix_list_cols(df):
    df['ingredients'] = df['ingredients'].apply(set)
    df['directions'] = df['directions'].apply(set)
    df['quantities'] = df['quantities'].apply(set)

    return df


def json_dump_list_cols(df):
    df['ingredients'] = df['ingredients'].apply(json.dumps)
    df['directions'] = df['directions'].apply(json.dumps)
    df['quantities'] = df['quantities'].apply(json.dumps)

    return df


# Create proper JSON columns in NER dataset
def list_to_json_dump(df):

    # Conversion function:
    def dict2json(dictionary):
        return json.dumps(dictionary, ensure_ascii=False)

    df["ingredients"] = df.apply(lambda row: {"ingredients":row['ingredients']}, axis=1)
    df["quantities"] = df.apply(lambda row: {"quantities":row['quantities']}, axis=1)
    df["directions"] = df.apply(lambda row: {"directions":row['directions']}, axis=1)


    df["ingredients"] = df.ingredients.map(dict2json)
    df["quantities"] = df.quantities.map(dict2json)
    df["directions"] = df.directions.map(dict2json)

    return df


def process_dataset_recipeNLG(df):
    """Process recipeNLG dataset

    Args:
        df (pandas.DataFrame): Raw recipeNLG dataset

    Returns:
        pandas.DataFrame: Cleaned recipeNLG dataset
    """

    # Clean pandas dataframe and save to parquet
    df = clean_raw_data(df)

    # Make list columns into sets for insertion into postgres DB
    df = list_to_json_dump(df)

    # Add a unique dish_id to act as the primary key
    df["dish_id"] = df.index
    
    # Save cleaned dataframe as parquet and csv files
    df = df[['dish_id', 'uid', 'dish', 'ingredients',
            'quantities', 'directions', 'description',
            'prep_time', 'cook_time', 'total_time', 'yields', 
            'category', 'cuisine','ratings', 'url', 
            'img', 'source']]

    return df


def create_unique_ingredients(df):
    """Create unique ingredients dataset

    Args:
        df (pandas.DataFrame): Raw NER dataset

    Returns:
        pandas.DataFrame: Unique ingredients dataset
    """

    # Select just ingredients column
    df = df[["ingredients"]]
    df["ingredients"] = df["ingredients"].apply(lambda row: json.loads(row)['ingredients'])

    # Explode "ingredients" list column to make an individual row for each ingredients in each dish
    df = df.explode(['ingredients']).reset_index(drop=True)

    # Replace whitespace with single space
    df["ingredients"] = df["ingredients"].replace(r'\s+', ' ', regex=True)

    # Convert all characters in 'ingredients' to lowercase
    df['ingredients'] = df['ingredients'].str.lower()

    # Create frequency dataframe
    freq_df = df[["ingredients"]].value_counts()

    # Convert series to dataframe
    freq_df = pd.DataFrame(freq_df)

    # Reset index
    freq_df = freq_df.reset_index()

    # Select unique ingredients
    unique_ingreds = df[["ingredients"]].drop_duplicates(subset=['ingredients'], keep='first')

    # Merge counts with unique ingredients
    unique_ingreds = pd.merge(unique_ingreds, freq_df, on='ingredients', how='left')

    # Replace NaN values with 0
    unique_ingreds['count'].fillna(0, inplace=True)

    # Convert the 'float_column' to an integer
    unique_ingreds['count'] = unique_ingreds['count'].astype(int)

    # Sort unique_ingreds by count in descending order
    unique_ingreds = unique_ingreds.sort_values(by='count', ascending=False)

    # Add unique id for each ingredient
    unique_ingreds["ingredients_id"] = unique_ingreds.index

    # Reorder columns
    unique_ingreds = unique_ingreds[["ingredients_id", "ingredients", "count"]]

    return unique_ingreds
