import psycopg2 as pg
from psycopg2 import sql

# -----------------------------------
# Query Ingredient(s) to Fetch Row(s)
# -----------------------------------

# Connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224')

# Create cursor object to interact with the database
cur = conn.cursor()

# table name of long formatted ingredients data
wide_table_name = 'dish_db'

# make a SQL query to search for all rows in the ingredients column (which contains a list of ingredients) that includes all of the ingredients in ["apple", "banana"]"
query = sql.SQL("""
    SELECT *
    FROM {}
    WHERE ingredients @> %s
    """).format(sql.Identifier(wide_table_name))

# # Define the SQL query to search for recipes containing (a) specific ingredient(s)
# query = sql.SQL("""
#     SELECT * 
#     FROM {}
#     WHERE EXISTS (
#         SELECT 1 
#         FROM unnest(ingredients) as ingredient 
#         WHERE ingredient LIKE %s
#     )""").format(sql.Identifier(wide_table_name))

# Specify ingredient to search
search_ingredient = ['apple', 'bacon']

# ingredient_to_search = '%chicken%'

# Execute the query with the specified ingredient
cur.execute(query, (search_ingredient,))

# Commit changes to the databas
conn.commit()

# Fetch all the rows that match the query
row = cur.fetchall() 

# len(row)
# row[0][0]
# row[0][1]

# close cursor and connection
cur.close()
conn.close()

# # Define the SQL query to search for recipes containing (a) specific ingredient(s)
# query = sql.SQL("""
#     SELECT * 
#     FROM {}
#     WHERE EXISTS (
#         SELECT 1 
#         FROM unnest(ingredients) as ingredient 
#         WHERE ingredient LIKE %s
#     )""").format(sql.Identifier(wide_table_name))

# # Specify ingredient to search
# ingredient_to_search = '%chicken%'

# # Execute the query with the specified ingredient
# cur.execute(query, (ingredient_to_search,))

# # Commit changes to the databas
# conn.commit()

# # Fetch all the rows that match the query
# row = cur.fetchall() 

# # close cursor and connection
# cur.close()
# conn.close()

# -------------------------
# Long formatted DB queries
# -------------------------

# Connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224')

# Create cursor object to interact with the database
cur = conn.cursor()

# table name of long formatted ingredients data
table_name = 'single_ingredients_db'

search_ingredient = 'apple'

query = sql.SQL("""
    SELECT id, dish, ingredients
    FROM {}
    WHERE ingredients LIKE {}
    """).format(sql.Identifier(table_name), sql.Literal('%' + search_ingredient + '%'))

search_ingredients = ['apple', 'banana']

# Construct the SQL query using IN operator
query = sql.SQL("""
    SELECT id, dish, ingredients
    FROM {}
    WHERE ingredients IN ({})
    """).format(
        sql.Identifier(table_name),
        sql.SQL(', ').join(map(sql.Literal, search_ingredients))
    )

# define SQL query to find all rows in the dish column that contain the specified ingredient
# the database is long formatted so each dish may have multiple rows for each ingredient in the dish 
query = sql.SQL("""
    SELECT id, dish, ingredients
    FROM {}
    WHERE ingredients LIKE {}
    """).format(sql.Identifier(table_name), sql.Literal('%' + search_ingredient + '%'))
ingredients_list = ['apple', 'walnuts']
['%' + i + '%' for i in ingredients_list]

query = sql.SQL("""
    SELECT id, dish, ingredients
    FROM {}
    WHERE ingredients LIKE {}
    """).format(sql.Identifier(table_name), ['%' + i + '%' for i in ingredients_list])


# define the SQL query to search a specific ingredient in the ingredients column
# query = sql.SQL("""
#     SELECT * 
#     FROM {}
#     WHERE ingredients LIKE %s
#     """).format(sql.Identifier(table_name))
# define the SQL query to search a specific ingredient in the ingredients column
query = sql.SQL("""
    SELECT * 
    FROM {}
    WHERE ingredients LIKE %s
    """).format(sql.Identifier(table_name))

# Option 1 (single quotes around %apple%)
query = sql.SQL("""
    SELECT * 
    FROM single_ingredients_db
    WHERE ingredients LIKE '%apple%'
    """)

# Option 2 (no single quotes around %apple%)
query = sql.SQL("""
    SELECT * 
    FROM single_ingredients_db
    WHERE ingredients LIKE %apple%
    """)

# # Define the SQL query to search for recipes containing (a) specific ingredient(s)
# query = sql.SQL("""
#     SELECT * 
#     FROM {}
#     WHERE EXISTS (
#         SELECT 1 
#         FROM unnest(ingredients) as ingredient 
#         WHERE ingredient LIKE %s
#     )""").format(sql.Identifier(table_name))


# sql.SQL("""
    

# """)

# Specify ingredient to search
ingredient_to_search = '%chicken%'

# Execute the query with the specified ingredient
cur.execute(query)
cur.execute(query, (ingredient_to_search,))

# Commit changes to the databas
conn.commit()

# Fetch all the rows that match the query
row = cur.fetchall() 
len(row)
row[0:2]
# close cursor and connection
cur.close()
conn.close()