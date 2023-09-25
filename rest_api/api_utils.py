
import psycopg2 as pg
from psycopg2 import sql

def getDishes2(conn, table_name, ingredients, limit = 20):

    """
    Get dishes from the database that contain the specified ingredients.

    Args:
        conn (psycopg2.extensions.connection): Connection to the database.
        table_name (str): Name of the table to query.
        ingredients (str or list): Ingredients to search for.
        limit (int): Maximum number of results to return.

    Returns:
        dict: A dictionary of dishes and their ingredients.
    """

    # limit the highest number of results to return
    if limit and limit > 100:
        limit = 100


    # Create cursor object to interact with the database
    cur = conn.cursor()

    # if a limit was specified, use it, otherwise return all results
    if limit:
        query = sql.SQL("""
                    SELECT dish, ingredients
                    FROM {}
                    WHERE ingredients @> %s
                    LIMIT {}
                    """).format(sql.Identifier(table_name), sql.Literal(limit))
    else:
        query = sql.SQL("""
                    SELECT dish, ingredients
                    FROM {}
                    WHERE ingredients @> %s
                    """).format(sql.Identifier(table_name))

    # Create cursor object to interact with the database
    cur = conn.cursor()

    # if ingredients is a string, convert it to a list of length 1
    if isinstance(ingredients, str):
        ingredients = [ingredients]

    # Execute the query with the specified ingredient
    cur.execute(query, (ingredients, ))

    # Commit changes to the database
    conn.commit()

    # Fetch all the rows that match the query
    db_rows = cur.fetchall() 
    
    # convert the returned dishes to a key-value pair (dish: ingredients)
    dishes = {db_rows[i][0]: db_rows[i][1] for i in range(0, len(db_rows))}

    return dishes

def getDishes(host, port, dbname, user, password, table_name, ingredients, limit = 20):

    
    # limit the highest number of results to return
    if limit and limit > 100:
        limit = 100

    # # Connect to PostgreSQL server
    conn = pg.connect(
        host     = host, 
        port     = port, 
        dbname   = dbname, 
        user     = user, 
        password = password)

    # Create cursor object to interact with the database
    cur = conn.cursor()

    # if a limit was specified, use it, otherwise return all results
    if limit:
        query = sql.SQL("""
                    SELECT dish, ingredients
                    FROM {}
                    WHERE ingredients @> %s
                    LIMIT {}
                    """).format(sql.Identifier(table_name), sql.Literal(limit))
    else:
        query = sql.SQL("""
                    SELECT dish, ingredients
                    FROM {}
                    WHERE ingredients @> %s
                    """).format(sql.Identifier(table_name))

    # Create cursor object to interact with the database
    cur = conn.cursor()

    # if ingredients is a string, convert it to a list of length 1
    if isinstance(ingredients, str):
        ingredients = [ingredients]

    # Execute the query with the specified ingredient
    cur.execute(query, (ingredients, ))

    # Commit changes to the database
    conn.commit()

    # Fetch all the rows that match the query
    db_rows = cur.fetchall() 
    
    # convert the returned dishes to a key-value pair (dish: ingredients)
    dishes = {db_rows[i][0]: db_rows[i][1] for i in range(0, len(db_rows))}

    # # close cursor and connection
    # cur.close()
    # conn.close()

    return dishes


###################
### OLD QUERIES ###
###################

### Eventually we will use this query but for testing we'll just get the dish and ingredients columns
# # if a limit was specified, use it, otherwise return all results
# if limit:
#     query = sql.SQL("""
#                 SELECT *
#                 FROM {}
#                 WHERE ingredients @> %s
#                 LIMIT {}
#                 """).format(sql.Identifier(table_name), sql.Literal(limit))
# else:
#     query = sql.SQL("""
#                 SELECT *
#                 FROM {}
#                 WHERE ingredients @> %s
#                 """).format(sql.Identifier(table_name))
        
# # # Define the SQL query to search for recipes containing (a) specific ingredient(s)
# query = sql.SQL("""
#     SELECT * 
#     FROM public.dish_db 
#     WHERE EXISTS (
#         SELECT 1 
#         FROM unnest(ingredients) as ingredient 
#         WHERE ingredient LIKE %s
#     )""")

# make a SQL query to search for all rows in the ingredients column (which contains a list of ingredients) that includes all of the ingredients in ["apple", "banana"]"
# query = sql.SQL("""
#     SELECT *
#     FROM {}
#     WHERE ingredients @> %s
#     """).format(sql.Identifier(table_name))

# # handle if ingredients is a single string
# if isinstance(ingredients, str):
#     if ingredients[0] != "%" and ingredients[-1] != "%":
#         ingredients = "%" + ingredients + "%"

# # handle if ingredients is a list
# if isinstance(ingredients, list):
#     if len(ingredients) == 1:
#         ingredients = ingredients[0].strip()
#         if ingredients[0] != "%" and ingredients[-1] != "%":
#             ingredients = "%" + ingredients + "%"
#     else:
#         ingredients = ["%" + i + "%" for i in ingredients]