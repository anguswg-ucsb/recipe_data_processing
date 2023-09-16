import re
import pandas as pd
import ast

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


def clean_raw_data(df, save_path = None):
    """
    Clean up raw dataset and save to a folder as parquet.

    Args:
        df (pandas.DataFrame): Raw data to be cleaned.
        save_path (str): Path to save folder (must be .parquet file).

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

    # Reorder columns in the DataFrame
    df = df[['dish', 'ingredients', 'split_ingredients', "quantities", "directions"]]
    # df = df[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'id']]

    # any dishes with missing values, replace with the word "missing"
    df['dish'] = df['dish'].str.replace(r'[\x00-\x19]', '').replace('', 'missing')

    # santize list columns by removing unicode values
    df['ingredients'] = df['ingredients'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['quantities'] = df['quantities'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])
    df['directions'] = df['directions'].apply(lambda x: [re.sub('[\x00-\x19]', '', s) for s in x])

    if save_path:
        df.to_parquet(save_path)

    return df
