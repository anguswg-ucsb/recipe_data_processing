import re

# https://cookbooks.com/Recipe-Details.aspx?id=44874
# scraper = scrape_me("https://www.food.com/recipe/cherry-almond-crisp-290252")
# scraper = scrape_me("https://cookbooks.com/Recipe-Details.aspx?id=44874")
# scraper = scrape_me("")

# # Q: What if the recipe site I want to extract information from is not listed below?
# # A: You can give it a try with the wild_mode option! If there is Schema/Recipe available it will work just fine.
# scraper = scrape_me('https://www.feastingathome.com/tomato-risotto/', wild_mode=True)

# scraper.host()
# scraper.title()
# scraper.image()

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

def clean_raw_recipes(df, save_path = None):

    """Clean up raw recipes dataset and save to a folder as parquet

    df (pandas.DataFrame)
    save_path (str) path to save folder (must be .parquet file)

    Returns:
        pandas.DataFrame
    """

    # Drop unnecessary columns and rename
    df = df.drop(columns=['Unnamed: 0', 'source'], axis=1)
    df = df.rename(columns={'title': 'dish', 'ingredients': 'quantities', 'NER': 'ingredients'})

    # Add a unique 'ID' column to the DataFrame
    df['ID'] = pd.RangeIndex(start=1, stop=len(df) + 1)

    # Call clean_text function to clean and preprocess 'ingredients' column
    df['ingredients'] = df['ingredients'].apply(clean_text)

    # Call split_text function to split cleaned 'ingredients' column, creating a new 'split_ingredients' column
    df['split_ingredients'] = df['ingredients'].apply(split_text)

    # Reorder columns in the DataFrame
    df = df[['dish', 'ingredients', 'split_ingredients', 'quantities', 'directions', 'link', 'ID']]

    if save_path:
        df.to_parquet(save_path)

    return df

# def execute_sql(connection, query):
#     """
#     Connect to PostgreSQL server annd execute given queries.

#     Args:
#         connections (dict): Connection variables to connect to PostgreSQL Database.

#         commands (lst): Queries to be executed.
#     """
#     # Connect to the server
#     conn = pg.connect(
#         host     = connection['host'], 
#         port     = connection['port'], 
#         dbname   = connection['dbname'], 
#         user     = connection['user'], 
#         password = connection['password'])

#     # Create cursor object to interact with the database
#     cur = conn.cursor()

#     cur.execute(query)

#     # Commit changes to the database
#     conn.commit()

#     # Close cursor and connection
#     cur.close()
#     conn.close()