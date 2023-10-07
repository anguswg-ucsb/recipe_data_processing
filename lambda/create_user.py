import boto3
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

new_user = os.environ.get('NEW_USER')
new_pw = os.environ.get('NEW_PW')

# Use the environment variables
print(f'Value of endpoint: {endpoint}')
print(f'Value of db_name: {db_name}')
print(f'Value of db_user: {db_user}')
print(f'Value of new_user: {new_user}')

# table = dynamodb.Table("dish_recipes_db")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn_string = "host=%s user=%s password=%s dbname=%s" % \
                    (endpoint, db_user, db_pw, db_name)
    conn = psycopg2.connect(conn_string)
    # cur = conn.cursor()
except:
    logger.error("ERROR: Could not connect to Postgres instance.")
    sys.exit()

def create_user(event, context):

    # SQL command to create a new user
    create_user_sql = sql.SQL("""
    CREATE USER {} WITH PASSWORD '{}';
    GRANT ALL PRIVILEGES ON DATABASE {} TO {};
    """).format(sql.Identifier(new_user), sql.Identifier(new_pw), 
                sql.Identifier(db_name), sql.Identifier(new_user))

    # privledges_sql = sql.SQL("""
    # ALTER USER {} WITH SUPERUSER;
    # """).format(sql.Identifier(new_user))

    # # SQL command to create a new user
    # create_user_sql = "CREATE USER new_username WITH PASSWORD 'new_password';"
    try:
        # Create a cursor object
        cursor = conn.cursor()
        
        # Execute the SQL command to create a new user
        cursor.execute(create_user_sql)
        
        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': 'New user created successfully'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }