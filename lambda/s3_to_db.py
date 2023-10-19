import boto3
import csv
import sys
import logging
import os
import psycopg2
from psycopg2 import sql

# DB environemnt variables
s3_file_name = os.environ.get('S3_FILE_NAME')
endpoint = os.environ.get('ENDPOINT')
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_pw = os.environ.get('DB_PW')

# Use the environment variables
print(f'Value of s3_file_name: {s3_file_name}')
print(f'Value of endpoint: {endpoint}')
print(f'Value of db_name: {db_name}')
print(f'Value of db_user: {db_user}')

# table = dynamodb.Table("dish_recipes_db")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn_string = "host=%s user=%s password=%s dbname=%s" % \
                    (endpoint, db_user, db_pw, db_name)
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
except:
    logger.error("ERROR: Could not connect to Postgres instance.")
    sys.exit()

logger.info("SUCCESS: Connection to RDS Postgres instance succeeded")

# initialize s3 client
s3_client = boto3.client("s3")

def s3_to_db(event, context):
    
    # Use the environment variables
    print(f'-> Value of endpoint: {endpoint}')
    print(f'-> Value of db_name: {db_name}')
    print(f'-> Value of db_user: {db_user}')
    
    print(f"=====================")
    print(f'---->\n Value of event: {event}')
    print(f"=====================")
    
    #bucket_name = event['Records'][0]['s3']['bucket']['name']
    #s3_file_name = event['Records'][0]['s3']['object']['key']
    
    bucket_name = "dish-recipes-bucket"

    # dish_table_file_name = "dish_table.csv"
    # details_table_file_name = "details_table.csv"

    print(f"bucket_name: {bucket_name}")
    print(f"s3_file_name: {s3_file_name}")
    
    table_name = "dish_table"
    details_table_name = "details_table"

    # Drop the table if it exists
    drop_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(sql.Identifier(table_name))
    cur.execute(drop_table_query)
    conn.commit()

    print(f'Attempting to drop {table_name} table')

    # Drop the table if it exists
    drop_details_table_query = sql.SQL("DROP TABLE IF EXISTS {} CASCADE;").format(sql.Identifier(details_table_name))
    cur.execute(drop_details_table_query)
    conn.commit()

    print(f'Attempting to drop {details_table_name} table')

    # Create the table
    create_table_query = sql.SQL("""
        CREATE TABLE {} (
            dish_id SERIAL PRIMARY KEY,
            uid TEXT,
            dish TEXT,
            ingredients JSONB,
            split_ingredients JSONB,
            quantities JSONB,
            directions JSONB
        )
    """).format(sql.Identifier(table_name))

    cur.execute(create_table_query)
    conn.commit()

    print(f'Created {table_name} table')

    # print(f"Maybe dropping 'aws_s3' extension in DB")
    
    # drop_s3ext_query = sql.SQL("DROP EXTENSION IF EXISTS aws_s3;")
    # cur.execute(drop_s3ext_query)
    # # cur.execute("DROP EXTENSION IF EXISTS aws_s3;")

    # conn.commit()

    # print(f"Adding AWS lambda extension")
    # lambda_ext_query = sql.SQL("CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;")
    # cur.execute(lambda_ext_query)
    # conn.commit()

    # print(f"creating 'aws_s3' extension in DB")
    # s3_ext_query = sql.SQL("CREATE EXTENSION aws_s3 CASCADE;")
    # cur.execute(s3_ext_query)
    # # cur.execute("CREATE EXTENSION aws_s3 CASCADE;")
    # conn.commit()

    print(f"Adding AWS Commons S3 URI")
    s3_uri_query = sql.SQL("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', '{}', 'us-west-1') AS s3_uri").format(sql.Identifier(s3_file_name))
    # s3_uri_query = "SELECT aws_commons.create_s3_uri('dish-recipes-bucket', '%s', 'us-west-1') AS s3_uri"

    print(f"s3_uri_query: {s3_uri_query}")
    cur.execute(s3_uri_query)

    # cur.execute(s3_uri_query, (s3_file_name,))

    #cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes.csv','us-west-1' ) AS s3_uri")
    #cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes2.csv','us-west-1' ) AS s3_uri gset")
    conn.commit()
    
    s3_uri = cur.fetchone()[0]  # Fetch the S3 URI from the result
    print("S3 URI:", s3_uri) 

    # import_data_query = sql.SQL("""
    #     SELECT aws_s3.table_import_from_s3(
    #     'dish_table', 
    #     'dish_id,uid,dish,ingredients,split_ingredients,quantities,directions', 
    #     '(FORMAT CSV, DELIMITER '','', HEADER true)', 
    #     'dish-recipes-bucket', 
    #     'dish_recipes.csv', 
    #     'us-west-1'
    #     )""").format(sql.Identifier(table_name))    
    
    import_data_query = sql.SQL("""
        SELECT aws_s3.table_import_from_s3(
        'dish_table', 
        'dish_id,uid,dish,ingredients,split_ingredients,quantities,directions', 
        '(FORMAT CSV, DELIMITER '','', HEADER true)', 
        'dish-recipes-bucket', 
        '{}', 
        'us-west-1'
        )""").format(sql.Identifier(s3_file_name)) 

    print(f"Executing S3 CSV copy command")
    cur.execute(import_data_query)
    conn.commit()

    print(f"Finished creating main dish_table from file: {s3_file_name}")

    # 1. Create the details_table
    create_details_table_query = sql.SQL("""
        CREATE TABLE details_table (
            dish_id SERIAL PRIMARY KEY,
            uid TEXT,
            split_ingredients JSONB,
            quantities JSONB,
            directions JSONB,
            FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
        )""")

    cur.execute(create_details_table_query)
    conn.commit()   

    print(f"Created 'details_table'")

    # insert data to details_table from dish_table
    insert_data_query = sql.SQL("""
        INSERT INTO details_table (dish_id, uid, split_ingredients, quantities, directions)
        SELECT dish_id, uid, split_ingredients, quantities, directions
        FROM dish_table;
    """)

    cur.execute(insert_data_query)
    conn.commit()

    print(f"Copied data from 'dish_table' to 'details_table'")

    # Remove unnecessary columns from dish_table
    rm_cols_query = sql.SQL("""
        ALTER TABLE dish_table
        DROP COLUMN IF EXISTS split_ingredients,
        DROP COLUMN IF EXISTS quantities,
        DROP COLUMN IF EXISTS directions;
    """)

    cur.execute(rm_cols_query)
    conn.commit()

    print(f"Removed unnecessary columns from 'dish_table'")


    print(f"ALL TRANSACTIONS COMPLETED")