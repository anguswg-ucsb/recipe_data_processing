import pandas as pd
import psycopg2 as pg
from sqlalchemy import create_engine

from psycopg2 import sql
import numpy as np
import json

from db_utils.utils import *
from db_utils.query_utils import *

# import db_utils.config
import db_utils.config
# from dotenv import load_dotenv

# # load .env file
# load_dotenv()

# # get databse URL from config.py
db_url = Config.DATABASE_URL
db_host = config.Config.DATABASE_HOST
db_name = config.Config.DATABASE_NAME
db_user = config.Config.DATABASE_USER
db_pw = config.Config.DATABASE_PW
db_port = config.Config.DATABASE_PORT