import requests
from bs4 import BeautifulSoup
import re 
from recipe_scrapers import scrape_me
import pandas as pd
import time
import random

def get_allrecipes_AZ_base_urls(
        url, 
        random_sleeps = True, 
        lower_sleep   = 1, 
        upper_sleep   = 3
        ):

    if random_sleeps:
        sleep_time = random.randint(lower_sleep, upper_sleep)
        time.sleep(sleep_time)

    html = requests.get(url).content
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select('[id^="alphabetical-list"] a[href]')
    urls = [link['href'] for link in links]
    
    return urls


def get_allrecipes_recipe_urls(base_url, 
                               random_sleeps=True, 
                               lower_sleep = 2, 
                               upper_sleep = 5):

    if random_sleeps:
        sleep_time = random.randint(lower_sleep, upper_sleep)
        time.sleep(sleep_time)

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


def build_allrecipes_urls(
        random_sleeps = True, 
        lower_sleep   = 2, 
        upper_sleep   = 5
        ):

    # List of base URLs to get list of URLs of recipes
    base_urls = [
        "https://www.allrecipes.com/recipes/17057/everyday-cooking/more-meal-ideas/5-ingredients/main-dishes/",
        "https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/",
        "https://www.allrecipes.com/recipes/17485/everyday-cooking/quick-and-easy/breakfast-and-brunch/",
        "https://www.allrecipes.com/recipes/455/everyday-cooking/more-meal-ideas/30-minute-meals/",
        "https://www.allrecipes.com/recipes/17561/lunch/",
        "https://www.allrecipes.com/recipes/841/holidays-and-events/christmas/desserts/christmas-cookies/"
        ] 

    # Get more base URLs from scraping page with recipes by ingredients from A-Z 
    # AZ base URLs of sections of foods to add to base_url list
    az_pages = ["https://www.allrecipes.com/ingredients-a-z-6740416", "https://www.allrecipes.com/recipes-a-z-6735880"]
    
    recipe_list = []

    if az_pages:
        
        print(f"Scraping recipes from\n{az_pages}")
        
        # loop through list of AZ pages, and get base URLs from each page, and add to list of base URLs
        for az_page in az_pages:
            # az_page = az_pages[0]
            print(f"Getting A-Z recipes from:\n - {az_page}")

            # Get list of AZ base URLs
            az_urls = get_allrecipes_AZ_base_urls(url = az_page, random_sleeps = random_sleeps)

            # Get list of recipe URLs from each AZ base URL
            for az_url in az_urls:
                print(f"Extracting A-Z recipes from:\n - {az_url}")
                
                recipe_urls = get_allrecipes_recipe_urls(
                                    base_url      = az_url,      
                                    random_sleeps = random_sleeps, 
                                    lower_sleep   = lower_sleep, 
                                    upper_sleep   = upper_sleep
                                    )

                recipe_list.extend(recipe_urls)
            
    print(f"Scraping recipes from\n{base_urls}")

    for url in base_urls:
        print(f"Getting recipes from:\n - {url}")

        recipe_url = get_allrecipes_recipe_urls(
                                base_url      = url, 
                                random_sleeps = random_sleeps, 
                                lower_sleep   = lower_sleep, 
                                upper_sleep   = upper_sleep
                                )

        recipe_list.extend(recipe_url)

    return recipe_list


def allrecipes_scraper(url, limit = None):
    print(f"Scraping recipe from {url}")

    # Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # Convert recipe to json
    recipe_json = scraper.to_json()

    return recipe_json


def scrape_recipes(base_urls, limit = None):

    recipe_list = []

    print(f"Number of base_urls: {len(base_urls)}")

    for base_url in base_urls:
        print(f"Scraping recipes from {base_url}")

        # Get list of recipe URLs
        recipe_urls = get_allrecipes_recipe_urls(base_url)

        # If limit IS GIVEN, and the number of recipes is less than the limit, set limit to the number of recipes
        if limit:
            limit = len(recipe_urls) if len(recipe_urls) < limit else limit
            
        # Otherwise, if limit IS NOT GIVEN, set limit to the number of recipes
        else:
            limit = len(recipe_urls)

        print(f"Retrieving {limit} recipes from base URL:\n - {base_url}...")

        # Get all recipes up to the limit
        for i in range(0, limit):
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