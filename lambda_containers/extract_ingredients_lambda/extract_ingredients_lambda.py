# import random 
# import json

# from food_extractor.food_model import FoodModel

# # Credit: https://github.com/chambliss/foodbert.git
# # Thank you for the model and heurtistics for extracting food ingredients from a list of ingredients! 

# # GitHub Repository: https://github.com/chambliss/foodbert/tree/master

# # To install via pip:
# # pip3 install git+https://github.com/chambliss/foodbert.git

# # from food_extractor.food_model import FoodModel

# # # Download the model from HuggingFace
# # from transformers import (
# #     DistilBertForTokenClassification,
# #     DistilBertTokenizerFast,
# # )
# # # HuggingFace path to model
# # HF_MODEL_PATH = "chambliss/distilbert-for-food-extraction"

# # # Download the model from HuggingFace
# # model = DistilBertForTokenClassification.from_pretrained(HF_MODEL_PATH)

# # # Specify the directory where you want to save the model
# # # save_directory = '/model/chambliss-distilbert-for-food-extraction'
# # save_directory = './lambda_images/model/chambliss-distilbert-for-food-extraction'

# # # Save the model and its configuration to the specified directory
# # model.save_pretrained(save_directory)

import random 
import json

# import model interface from Hugging Face model 
from food_extractor.food_model import FoodModel

# Credit: https://github.com/chambliss/foodbert.git
# Thank you for the model and heurtistics for extracting food ingredients from a list of ingredients! 

# # GitHub Repository: https://github.com/chambliss/foodbert/tree/master

# path to saved distilbert FoodModel from Hugging Face
model_path = './model/chambliss-distilbert-for-food-extraction'

# Load the model from HuggingFace
model = FoodModel(model_path)
# model = FoodModel("chambliss/distilbert-for-food-extraction")

# # function to extract food ingredients from a list of ingredients using the FoodModel
def generate_tags(model, ingredient_list):

    food_tags = []

    input = " ... ".join(ingredient_list)

    model_output = model.extract_foods(input)

    for food in model_output[0]["Ingredient"]:
        food_tags.append(food['text'].lower())
        
    return food_tags

def extract_ingredients_lambda(event, context):
    example_json = {
        'uid': 'spanishsquash_906928', 
        'url': 'https://www.allrecipes.com/recipe/73794/spanish-squash/',
        'scraped_ingredients': ['1 pound ground beef', '1 tablespoon vegetable oil', '3 medium yellow squash, sliced', '1 small yellow onion, sliced', '1 (14.5 ounce) can diced tomatoes, drained', '0.5 cup water', '1 teaspoon chili powder', '0.25 teaspoon cumin', '1 dash garlic powder', 'salt and pepper to taste'] 
        }
    batch_events = [example_json for i in range(4)]
    # batch_ingredients = [example_json["scraped_ingredients"] for i in range(5)]

    # print(f"model: {model}")
    print(f"event: {event}")
    print(f"context: {context}")
    output_tags = []

    for single_event in batch_events:
        food_tags = generate_tags(model, single_event["scraped_ingredients"])
        output_tags.append(food_tags)

        print(f"food_tags: {food_tags}")
        print(f"=========================")


    # food_tags = generate_tags(model, event["scraped_ingredients"])
    print(f"output_tags: {output_tags}")

    return output_tags