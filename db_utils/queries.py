import psycopg2 as pg
from psycopg2 import sql

# ------------------------------------
# Query Ingrediient(s) to Fetch Row(s)
# ------------------------------------

# Connect to PostgreSQL server
conn = pg.connect(
    host     = 'localhost', 
    port     = '5432', 
    dbname   = 'postgres', 
    user     = 'postgres', 
    password = '1224')

# Create cursor object to interact with the database
cur = conn.cursor()

# Define the SQL query to search for recipes containing (a) specific ingredient(s)
query = sql.SQL("""
    SELECT * 
    FROM public.dish_db 
    WHERE EXISTS (
        SELECT 1 
        FROM unnest(ingredients) as ingredient 
        WHERE ingredient LIKE %s
    )""")

# Specify ingredient to search
ingredient_to_search = '%chick%'

# Execute the query with the specified ingredient
cur.execute(query, (ingredient_to_search,))

# Commit changes to the databas
conn.commit()

# Fetch all the rows that match the query
row = cur.fetchall() 

# close cursor and connection
cur.close()
conn.close()