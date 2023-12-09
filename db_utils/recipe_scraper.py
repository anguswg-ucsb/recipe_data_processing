import requests
from bs4 import BeautifulSoup
from recipe_scrapers import scrape_me
import re 

def get_AZ_base_urls(url):
    # url = "https://www.allrecipes.com/ingredients-a-z-6740416"

    html = requests.get(url).content
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('[id^="alphabetical-list"] a[href]')
    urls = [link['href'] for link in links]

    return urls

def get_recipe_urls(base_url):

    # Base URL is a URL from allrecipes.com with a list of recipes on the page
    # Examples:
        # "https://www.allrecipes.com/recipes/17057/everyday-cooking/more-meal-ideas/5-ingredients/main-dishes/"
        # "https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/"

    # Fetch HTML content
    html = requests.get(base_url).content
    soup = BeautifulSoup(html, "html.parser")

    # Find all <a> tags with a not null 'href' attribute
    links = [a["href"] for a in soup.find_all("a", href=True)]

    # Define the pattern using a regular expression
    pattern = re.compile(r'https://www\.allrecipes\.com/recipe/\d+/\w+(?:-\w+)+/')

    # Use list comprehension to filter the URLs
    filtered_urls = [url for url in links if pattern.match(url)]


    return filtered_urls

def scrape_recipes(base_urls):
    recipe_list = []

    for base_url in base_urls:
        print(f"Scraping recipes from {base_url}")

        # Get list of recipe URLs
        recipe_urls = get_recipe_urls(base_url)
        
        # only get first 5 recipes to not overload the server
        for i in range(0, 5):
        # for recipe_url in recipe_urls:
            recipe_url = recipe_urls[i]
            print(f"Scraping recipe from {recipe_url}")
            # Use recipe_scrapers to scrape recipe information
            scraper = scrape_me(recipe_url)

            # Save recipe information to a dictionary
            recipe_info = {
                "title": scraper.title(),
                "total_time": scraper.total_time(),
                "ingredients": scraper.ingredients(),
                "instructions": scraper.instructions(),
                "image": scraper.image(),
            }

            # Append the dictionary to the list
            recipe_list.append(recipe_info)

    return recipe_list

# List of base URLs to get list of URLs of recipes
base_urls = ["https://www.allrecipes.com/recipes/17057/everyday-cooking/more-meal-ideas/5-ingredients/main-dishes/", 
"https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/", 
"https://www.allrecipes.com/recipes/17485/everyday-cooking/quick-and-easy/breakfast-and-brunch/",
"https://www.allrecipes.com/recipes/455/everyday-cooking/more-meal-ideas/30-minute-meals/"] 

# AZ base URLs of sections of foods to add to base_url list
az_page = ["https://www.allrecipes.com/ingredients-a-z-6740416"]
az_urls = get_AZ_base_urls(az_page[0])

# Extend base_urls list with AZ base URLs
base_urls.extend(az_urls)

base_urls = base_urls[0:1]

# Scrape recipes and get the list of dictionaries
recipes_data = scrape_recipes(base_urls)
recipes_data[0]

# recipe_url = get_recipe_urls(base_urls[1])

# #  USER recipe_scrapers library to scrape recipe data from a URL
# scraper = scrape_me(recipe_url[0])

# # save this information to a dictionary and append to a list
# scraper.title()
# scraper.total_time()
# scraper.ingredients()
# scraper.instructions()
# scraper.image()
