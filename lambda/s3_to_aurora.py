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

# # Establish table name to be created
table_name = 'dish_table'

# # SQL query to create table if it doesn't exist
create_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        uid TEXT,
        dish TEXT,
        ingredients JSONB,
        split_ingredients JSONB,
        quantities JSONB,
        directions JSONB         
    )""").format(sql.Identifier(table_name))

# # SQL query to create table if it doesn't exist
# create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         uid TEXT,
#         dish TEXT,
#         ingredients TEXT[]     
#     )""").format(sql.Identifier(table_name))

# # SQL query to create table if it doesn't exist
# create_table_query = sql.SQL("""
#     CREATE TABLE IF NOT EXISTS {} (
#         uid TEXT,
#         dish TEXT,
#         ingredients TEXT[],
#         split_ingredients TEXT[],
#         quantities TEXT[],
#         directions TEXT[]         
#     )""").format(sql.Identifier(table_name))

cur.execute(create_table_query)
conn.commit()

#cur.close()
#conn.close()

print(f'Created {table_name} table')

def s3_to_aurora(event, context):
    
    # Use the environment variables
    print(f'-> Value of endpoint: {endpoint}')
    print(f'-> Value of db_name: {db_name}')
    print(f'-> Value of db_user: {db_user}')

    # print(f"event: {event}")
    #bucket_name = event['Records'][0]['s3']['bucket']['name']
    #s3_file_name = event['Records'][0]['s3']['object']['key']
    
    bucket_name = "dish-recipes-bucket"
    s3_file_name = "dish_recipes2.csv"
    
    print(f"bucket_name: {bucket_name}")
    print(f"s3_file_name: {s3_file_name}")
    
    table_name = "dish_table"
    
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
        'uid,dish,ingredients,split_ingredients,quantities,directions', 
        '(FORMAT CSV, DELIMITER '','', HEADER true)', 
        'dish-recipes-bucket', 
        'dish_recipes.csv', 
        'us-west-1'
        )""").format(sql.Identifier(table_name))    
        
    print(f"Executing S3 CSV copy command")
    cur.execute(import_data_query)
    conn.commit()
    
    ## get object from s3 bucket
    #resp = s3_client.get_object(Bucket=bucket_name,Key=s3_file_name)
    #resp = resp['Body'].read().decode('utf-8').splitlines()
    #lines = csv.reader(resp)
    # print(lines)
    #print(f"type(lines): {type(lines)}")
    
    #headers = next(lines)
    #print('headers: %s' %(headers))
    
    #for dish in lines:
    #    #print complete line
    #    print("dish: ", dish)
    #    print("len(dish): ", len(dish))
    #    print("type(dish): ", type(dish))
    #    cur.execute(
    #        "INSERT INTO dish_table VALUES (%s, %s, %s,  %s, %s, %s)",
    #        dish
    #        )
    #conn.commit()
    #cur.close()
    #conn.close()
    
    print(f"Finished processing file: {s3_file_name}")

    #     print(f"type(dish): {type(dish)}")
        
    #     try:
    #         table.put_item(
    #             Item = {
    #                 "id" : dish[0],
    #                 "uid": dish[1],
    #                 "dish"        : dish[2],
    #                 "ingredients"       : dish[3],
    #                 "split_ingredients" : dish[4],
    #                 "quantities"   : dish[5],
    #                 "directions"   : dish[6]
    #             }
    #         )
    #     except Exception as e:
    #         print("Finished processing file")