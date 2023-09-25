from flask import Flask, request
from flask_restful import reqparse, abort, Api, Resource
import os
import psycopg2
import api_utils 
import config

# import rest_api.api_utils
# from rest_api.config import Config
# from dotenv import load_dotenv

# load_dotenv()

# instantiate Flask app
app = Flask(__name__)
api = Api(app)

# get databse URL from config.py
url = config.Config.DATABASE_URL

# connect to database through URL
connection = psycopg2.connect(url)

# placeholder for home resource
class DishDatabase(Resource):

    def get(self):
        print(f"Making get request to w/ Chicken and bacon")
        res = api_utils.getDishes2(
            conn = connection,
            table_name = "dish_db",
            ingredients = ['chicken', 'bacon'],
            limit = 5
            )
        
        return res
    
# look up dishes by ingredients resource
class FindDishes(Resource):
    def get(self):

        ingredients = request.args.getlist("ingredients")

        print(f"Making get request to w/ {ingredients}")
        print(f"type(ingredients): {type(ingredients)}")

        res = api_utils.getDishes2(
            conn = connection,
            table_name = "dish_db",
            ingredients = ingredients,
            limit = 2
            )
        return res

# add resources to api
api.add_resource(DishDatabase, '/')
api.add_resource(FindDishes, '/dishes')

# run app
if __name__ == '__main__':
    app.run(debug=True)
