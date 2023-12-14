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

def scrape_recipes(base_urls, limit = None):

    recipe_list = []

    print(f"Number of base_urls: {len(base_urls)}")

    for base_url in base_urls:
        # print(f"Scraping recipes from {base_url}")

        # Get list of recipe URLs
        recipe_urls = get_recipe_urls(base_url)

        # if limit IS GIVEN, and the number of recipes is less than the limit, set limit to the number of recipes
        if limit:
            limit = len(recipe_urls) if len(recipe_urls) < limit else limit
        # Otherwise, if limit IS NOT GIVEN, set limit to the number of recipes
        else:
            limit = len(recipe_urls)

        print(f"Retrieving {limit} recipes from base URL:\n - {base_url}...")

        # get all recipes up to the limit
        for i in range(0, limit):
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