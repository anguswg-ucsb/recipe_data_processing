# ------------------------
# Create Pandas DataFrame:
# ------------------------

import pandas as pd
import re

def clean_text(text):
    """
    Clean and preprocess text.

    Args:
        text (str): Input text to be cleaned.

    Returns:
        list: A list of cleaned and lowercase text elements.
    """
    # Split text using double quotation marks as separators
    clean_text = re.split('"', text)
    
    # Iterate through split text, removing non-alphanumeric characters
    for idx, val in enumerate(clean_text):
        clean_text[idx] = re.sub('[^A-Za-z0-9 ]+', '', val)
    
    # Create new_text list to store cleaned and lowercase text
    new_text = []

    # Iterate through cleaned text, appending to new_text if not empty
    for i in clean_text:
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



# Read CSV file containing recipe data
read_recipes = pd.read_csv('/Users/mkayeterry/Desktop/dataset/full_dataset.csv')

# Drop unnecessary columns and rename
recipes = read_recipes.drop(columns=['Unnamed: 0', 'source'], axis=1)
recipes = recipes.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients'})

# Add a unique 'ID' column to the DataFrame
recipes['ID'] = pd.RangeIndex(start=1, stop=len(recipes) + 1)

# Call clean_text function to clean and preprocess 'ingredients' column
recipes['ingredients'] = recipes['ingredients'].apply(clean_text)

# Call split_text function to split cleaned 'ingredients' column, creating a new 'split_ingredients' column
recipes['split_ingredients'] = recipes['ingredients'].apply(split_text)

# Reorder columns in the DataFrame
recipes = recipes[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'ID']]

# Create a DataFrame for image links, retaining only relevent columns
links = recipes.copy()
links = links.drop(columns=['quantities', 'directions', 'ingredients'], axis=1)

# Save cleaned recipes DataFrame to a Parquet file
recipes.to_parquet('data/dish_recipes.parquet')

# Save image links DataFrame to a Parquet file
links.to_parquet('data/image_links.parquet')

# ---------------------------
# Create a Postgres Database:
# ---------------------------

import psycopg2 as pg

conn = pg.connect(
    host='localhost', 
    port='5432', 
    dbname='postgres', 
    user='postgres', 
    password='1224')

cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS dish_db (
    id SERIAL PRIMARY KEY, dish CHAR(255), 
    ingredients TEXT, 
    split_ingredients TEXT, 
    quantities TEXT, 
    directions TEXT, 
    link CHAR(255))""")

cur.execute("""CREATE TABLE IF NOT EXISTS link_db (
    id SERIAL PRIMARY KEY, 
    dish CHAR(255), 
    link CHAR(255))""")


conn.commit()

cur.close()
conn.close()


