import boto3
import csv
import sys
import logging
import os
import psycopg2
from psycopg2 import sql

# RDS environemnt variables
endpoint = os.environ.get('ENDPOINT')
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_pw = os.environ.get('DB_PW')

# Use the environment variables
print(f'Value of endpoint: {endpoint}')
print(f'Value of db_name: {db_name}')
print(f'Value of db_user: {db_user}')

# table = dynamodb.Table("dish_recipes_db")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn_string = "host=%s user=%s  password=%s dbname=%s" % \
                    (endpoint, db_user, db_pw, db_name)
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()
except:
    logger.error("ERROR: Could not connect to Postgres instance.")
    sys.exit()

logger.info("SUCCESS: Connection to RDS Postgres instance succeeded")

# initialize s3 client
s3_client = boto3.client("s3")

# # # # Establish table name to be created
# table_name = 'dish_table'

# create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB         
#     )""").format(sql.Identifier(table_name))

# cur.execute(create_table_query)
# conn.commit()

# print(f'Created {table_name} table')

# # # Establish table name to be created
# dish_table_name = 'dish_table'

# dish_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB        
#     )""").format(sql.Identifier(dish_table_name))

# cur.execute(dish_table_query)
# conn.commit()
# print(f'Created {dish_table_name} table')

# # # Establish table name to be created
# details_table_name = 'details_table'

# details_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         quantities JSONB,
#         directions JSONB,
#         split_ingredients JSONB,
#         FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)        
#     )""").format(sql.Identifier(details_table_name))
# cur.execute(details_table_query)
# conn.commit()
# print(f'Created {details_table_name} table')

def s3_to_aurora(event, context):
    
    # Use the environment variables
    print(f'-> Value of endpoint: {endpoint}')
    print(f'-> Value of db_name: {db_name}')
    print(f'-> Value of db_user: {db_user}')

    # print(f"event: {event}")
    #bucket_name = event['Records'][0]['s3']['bucket']['name']
    #s3_file_name = event['Records'][0]['s3']['object']['key']
    
    bucket_name = "dish-recipes-bucket"
    s3_file_name = "dish_recipes.csv"
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

    print(f"Maybe dropping 'aws_s3' extension in DB")
    
    cur.execute("DROP EXTENSION IF EXISTS aws_s3;")
    conn.commit()

    print(f"Adding AWS lambda extension")
    cur.execute("CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;")
    conn.commit()

    print(f"creating 'aws_s3' extension in DB")
    cur.execute("CREATE EXTENSION aws_s3 CASCADE;")
    conn.commit()

    print(f"Adding AWS Commons S3 URI")
    cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes.csv','us-west-1' ) AS s3_uri")
    #cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes2.csv','us-west-1' ) AS s3_uri gset")
    conn.commit()
    
    s3_uri = cur.fetchone()[0]  # Fetch the S3 URI from the result
    print("S3 URI:", s3_uri) 

    import_data_query = sql.SQL("""
        SELECT aws_s3.table_import_from_s3(
        'dish_table', 
        'dish_id,uid,dish,ingredients,split_ingredients,quantities,directions', 
        '(FORMAT CSV, DELIMITER '','', HEADER true)', 
        'dish-recipes-bucket', 
        'dish_recipes.csv', 
        'us-west-1'
        )""").format(sql.Identifier(table_name))    
        
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

    # split_table_query = sql.SQL("""
    #     BEGIN;

    #     -- Create details_table
    #     CREATE TABLE details_table (
    #         dish_id INT PRIMARY KEY,
    #         uid TEXT,
    #         split_ingredients JSONB,
    #         quantities JSONB,
    #         directions JSONB,
    #         FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)
    #     );

    #     -- Copy data to details_table
    #     INSERT INTO details_table (dish_id, uid, split_ingredients, quantities, directions)
    #     SELECT dish_id, uid, split_ingredients, quantities, directions
    #     FROM dish_table;

    #     -- Remove unnecessary columns from dish_table
    #     ALTER TABLE dish_table
    #     DROP COLUMN IF EXISTS split_ingredients,
    #     DROP COLUMN IF EXISTS quantities,
    #     DROP COLUMN IF EXISTS directions;
                                
    #     COMMIT;
    # """).format(sql.Identifier(table_name))

    # print(f"Creating new 'details_table' from 'dish_table'")

    # cur.execute(split_table_query)
    # conn.commit()

    print(f"ALL TRANSACTIONS COMPLETED")


# import boto3
# import csv
# import sys
# import logging
# import os
# import psycopg2
# from psycopg2 import sql

# # RDS environemnt variables
# endpoint = os.environ.get('ENDPOINT')
# db_name = os.environ.get('DB_NAME')
# db_user = os.environ.get('DB_USER')
# db_pw = os.environ.get('DB_PW')

# # Use the environment variables
# print(f'Value of endpoint: {endpoint}')
# print(f'Value of db_name: {db_name}')
# print(f'Value of db_user: {db_user}')

# # table = dynamodb.Table("dish_recipes_db")
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# try:
#     conn_string = "host=%s user=%s password=%s dbname=%s" % \
#                     (endpoint, db_user, db_pw, db_name)
#     conn = psycopg2.connect(conn_string)
#     cur = conn.cursor()
# except:
#     logger.error("ERROR: Could not connect to Postgres instance.")
#     sys.exit()

# logger.info("SUCCESS: Connection to RDS Postgres instance succeeded")

# # initialize s3 client
# s3_client = boto3.client("s3")

# # # Establish table name to be created
# table_name = 'dish_table'

# # # SQL query to create table if it doesn't exist
# create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB         
#     )""").format(sql.Identifier(table_name))

# # # SQL query to create table if it doesn't exist
# create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB,
#         split_ingredients JSONB,
#         quantities JSONB,
#         directions JSONB         
#     )""").format(sql.Identifier(table_name))

# # # Establish table name to be created
# dish_table_name = 'dish_table'

# dish_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         dish TEXT,
#         ingredients JSONB        
#     )""").format(sql.Identifier(dish_table_name))

# # # Establish table name to be created
# details_table_name = 'details_table'

# details_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         dish_id SERIAL PRIMARY KEY,
#         uid TEXT,
#         quantities JSONB,
#         directions JSONB,
#         split_ingredients JSONB,
#         FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)        
#     )""").format(sql.Identifier(details_table_name))
# # # SQL query to create table if it doesn't exist
# # create_table_query = sql.SQL("""
# #     CREATE TABLE IF NOT EXISTS {} (
# #         uid TEXT,
# #         dish TEXT,
# #         ingredients TEXT[]     
# #     )""").format(sql.Identifier(table_name))

# # # SQL query to create table if it doesn't exist
# # create_table_query = sql.SQL("""
# #     CREATE TABLE IF NOT EXISTS {} (
# #         uid TEXT,
# #         dish TEXT,
# #         ingredients TEXT[],
# #         split_ingredients TEXT[],
# #         quantities TEXT[],
# #         directions TEXT[]         
# #     )""").format(sql.Identifier(table_name))

# cur.execute(create_table_query)
# conn.commit()

# #cur.close()
# #conn.close()

# print(f'Created {table_name} table')

# def s3_to_aurora(event, context):
    
#     # Use the environment variables
#     print(f'-> Value of endpoint: {endpoint}')
#     print(f'-> Value of db_name: {db_name}')
#     print(f'-> Value of db_user: {db_user}')

#     # print(f"event: {event}")
#     #bucket_name = event['Records'][0]['s3']['bucket']['name']
#     #s3_file_name = event['Records'][0]['s3']['object']['key']
    
#     bucket_name = "dish-recipes-bucket"
#     s3_file_name = "dish_recipes2.csv"
    
#     print(f"bucket_name: {bucket_name}")
#     print(f"s3_file_name: {s3_file_name}")
    
#     table_name = "dish_table"
    
#     print(f"Maybe dropping 'aws_s3' extension in DB")
    
#     cur.execute("DROP EXTENSION IF EXISTS aws_s3;")
#     conn.commit()

#     print(f"Adding AWS lambda extension")
#     cur.execute("CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;")
#     conn.commit()

#     print(f"creating 'aws_s3' extension in DB")
#     cur.execute("CREATE EXTENSION aws_s3 CASCADE;")
#     conn.commit()

#     print(f"Adding AWS Commons S3 URI")
#     cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes.csv','us-west-1' ) AS s3_uri")
#     #cur.execute("SELECT aws_commons.create_s3_uri('dish-recipes-bucket', 'dish_recipes2.csv','us-west-1' ) AS s3_uri gset")
#     conn.commit()
    
#     s3_uri = cur.fetchone()[0]  # Fetch the S3 URI from the result
#     print("S3 URI:", s3_uri) 

#     import_data_query = sql.SQL("""
#         SELECT aws_s3.table_import_from_s3(
#         'dish_table', 
#         'uid,dish,ingredients,split_ingredients,quantities,directions', 
#         '(FORMAT CSV, DELIMITER '','', HEADER true)', 
#         'dish-recipes-bucket', 
#         'dish_recipes.csv', 
#         'us-west-1'
#         )""").format(sql.Identifier(table_name))    
        
#     print(f"Executing S3 CSV copy command")
#     cur.execute(import_data_query)
#     conn.commit()
    
#     print(f"Finished processing file: {s3_file_name}")

#     #     print(f"type(dish): {type(dish)}")
        
#     #     try:
#     #         table.put_item(
#     #             Item = {
#     #                 "id" : dish[0],
#     #                 "uid": dish[1],
#     #                 "dish"        : dish[2],
#     #                 "ingredients"       : dish[3],
#     #                 "split_ingredients" : dish[4],
#     #                 "quantities"   : dish[5],
#     #                 "directions"   : dish[6]
#     #             }
#     #         )
#     #     except Exception as e:
#     #         print("Finished processing file")