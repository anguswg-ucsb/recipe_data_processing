# TODO: probably can delete all of this
import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine
from db_utils.utils import *
from psycopg2 import sql
import numpy as np
import json

def create_db_table(host, port, dbname, user, password, table_name, create_table_query):
    try:
        # Connect to PostgreSQL server
        conn = pg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )

        # Create cursor object to interact with the database
        cur = conn.cursor()

        # SQL query to create table if it doesn't exist
        create_table_query = sql.SQL(create_table_query).format(sql.Identifier(table_name))

        # Execute create table command
        cur.execute(create_table_query)

        # Commit changes to the database
        conn.commit()

        # Close cursor and connection
        cur.close()
        conn.close()

        print("Success - Table '{}' created.".format(table_name))

    except Exception as e:
        print("error occurred: {}".format(str(e)))


def pd_to_sql_table(host, port, dbname, user, password, table_name, df):
    try:
        # Connect to PostgreSQL server
        conn = pg.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )

        # Create cursor object to interact with the database
        cur = conn.cursor()

        # SQL query to create table if it doesn't exist
        create_table_query = sql.SQL(create_table_query).format(sql.Identifier(table_name))

        # Write recipes data to DB by appending to already created DB above
        df.to_sql(
            name      = table_name, 
            con       = conn, 
            if_exists = 'append', 
            index     = False
            )
        
        cur.close()
        conn.close()

        print("Success - Inserted data into table '{}'".format(table_name))

    except Exception as e:
        print("error occurred: {}".format(str(e)))