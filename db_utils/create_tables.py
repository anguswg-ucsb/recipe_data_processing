import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine

from psycopg2 import sql
import numpy as np
import json

from db_utils.utils import *
from db_utils.query_utils import *
from db_utils.config import *

# from dotenv import load_dotenv

# # load .env file
# load_dotenv()

# # get databse URL from config.py
db_url = Config.DATABASE_URL
db_host = Config.DATABASE_HOST
db_name = Config.DATABASE_NAME
db_user = Config.DATABASE_USER
db_pw = Config.DATABASE_PW
db_port = Config.DATABASE_PORT

dish_table_df = pd.read_csv('data/dish_table.csv')
details_table_df = pd.read_csv('data/details_table.csv')

# # SQL query to create table if it doesn't exist
dish_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        dish_id SERIAL PRIMARY KEY,
        uid TEXT,
        dish TEXT,
        ingredients JSONB,
        split_ingredients JSONB,
        quantities JSONB,
        directions JSONB         
    )""")

create_db_table(db_host, db_port, db_name, db_user, db_pw, 'dish_table', dish_table_query)

# # SQL query to create table if it doesn't exist
details_table_query = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
        dish_id SERIAL PRIMARY KEY,
        uid TEXT,
        quantities JSONB,
        directions JSONB,
        split_ingredients JSONB,
        FOREIGN KEY (dish_id) REFERENCES dish_table(dish_id)        
    )""")

create_db_table(db_host, db_port, db_name, db_user, db_pw, 'details_table', details_table_query)