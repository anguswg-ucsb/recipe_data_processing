
# import helper utility functions from scraper_utils.py
from scrapers.allrecipes.allrecipes_utils import *
# from scrapers.scraper_utils import get_AZ_base_urls, scrape_recipes, get_recipe_urls

###########################################################
# Compile list of "base_urls" to extract recipe URLs from #
###########################################################

# Note: A "base URL" would be a URL that contains links to recipes on the page

# TODO: Add to this list, try and get as many of these base URLs as possible

# List of base URLs to get list of URLs of recipes
base_urls = [
    "https://www.allrecipes.com/recipes/17057/everyday-cooking/more-meal-ideas/5-ingredients/main-dishes/", 
    "https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/", 
    "https://www.allrecipes.com/recipes/17485/everyday-cooking/quick-and-easy/breakfast-and-brunch/",
    "https://www.allrecipes.com/recipes/455/everyday-cooking/more-meal-ideas/30-minute-meals/",
    "https://www.allrecipes.com/recipes/17561/lunch/"
    ] 

##############################################################################
# Get more base URLs from scraping page with recipes by ingredients from A-Z #
##############################################################################

# AZ base URLs of sections of foods to add to base_url list
az_pages = ["https://www.allrecipes.com/ingredients-a-z-6740416"]

# loop through list of AZ pages, and get base URLs from each page, and add to list of base URLs
for az_page in az_pages:

    print(f"Scraping recipes from {az_page}")

    # Get list of AZ base URLs
    az_urls = get_allrecipes_AZ_base_urls(az_page)

    # Add A-Z base URLs to 'base_url' list 
    base_urls.extend(az_urls)

len(base_url)

#########################################################
# Get Recipe data from each base URLs in base_urls list #
#########################################################

# Number of results to return from each base URL (None returns all results), limiting this number to not overload allrecipes.com with requests
limit = 1

# Scrape recipes and get the list of dictionaries
# This recipes data can be converted to a pandas dataframe, and saved to a CSV file and added to our dataset (still needs to be cleaned to match the rest of the data)
recipes_data = scrape_recipes(base_urls, limit)

recipes_data[0]
len(recipes_data)

# recipe_url = get_recipe_urls(base_urls[1])

# #  USER recipe_scrapers library to scrape recipe data from a URL
# scraper = scrape_me(recipe_url[0])

# # save this information to a dictionary and append to a list
# scraper.title()
# scraper.total_time()
# scraper.ingredients()
# scraper.instructions()
# scraper.image()