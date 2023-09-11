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