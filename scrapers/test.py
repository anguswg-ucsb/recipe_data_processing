import time
import random
import requests
import re
from bs4 import BeautifulSoup
from scrapers.averiecooks.averiecooks_utils import *
# from scrapers.runners.runners_utils import *



base_url = "https://www.averiecooks.com/category/recipes/page/2/?utm_campaign=Landing%20Page%20or%20Form%20-%205506760&utm_medium=email&utm_source=convertkit"

# def get_allrecipes_recipe_urls(base_url, 
#                                random_sleeps=True, 
#                                lower_sleep = 2, 
#                                upper_sleep = 5):

# Base URL is a URL from allrecipes.com with a list of recipes on the page
# Examples:
# "https://www.allrecipes.com/recipes/17057/everyday-cooking/more-meal-ideas/5-ingredients/main-dishes/"
# base_url  =  "https://www.allrecipes.com/recipes/1947/everyday-cooking/quick-and-easy/"
# if random_sleeps:
#     sleep_time = random.randint(lower_sleep, upper_sleep)
#     time.sleep(sleep_time)

response = requests.get(base_url)

response.content

# Fetch HTML content
html = requests.get(base_url).content
soup = list(BeautifulSoup(html, "html.parser"))

# Find all <a> tags with a not null 'href' attribute
links = [a["href"] for a in soup.find_all("a", href=True)]

# Define the pattern using a regular expression
pattern = re.compile(r'https://www\.allrecipes\.com/recipe/\d+/\w+(?:-\w+)+/')

# Use list comprehension to filter the URLs
filtered_urls = [url for url in links if pattern.match(url)]

# return filtered_urls

soup.find("a")










# When running build_averiecooks_urls, you should see the links printed for each base URL.
averiecooks_urls = build_averiecooks_urls(random_sleeps=True, start_page=2, end_page=3)
print(averiecooks_urls)