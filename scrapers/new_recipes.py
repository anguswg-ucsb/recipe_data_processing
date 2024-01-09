import httpx
from bs4 import BeautifulSoup
import re
import random
import time

def get_new_urls(random_sleeps=True, lower_sleep=2, upper_sleep=5):
    headers = {
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'sec-ch-ua': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'Windows',
        'sec-fetch-site': 'none',
        'sec-fetch-mod': '',
        'sec-fetch-user': '?1',
        'accept-encoding': 'gzip',
        'accept-language': 'en-US,en;q=0.9,de;q=0.5'
    }

    # Base URLs with a list of recipes on the page
    base_urls = [
        "https://www.allrecipes.com/recipes/22908/everyday-cooking/special-collections/new/", # Not updated often
        "https://food52.com/recipes/newest", # Updated daily
        "https://cooking.nytimes.com/68861692-nyt-cooking/32998034-our-newest-recipes", # Updated every 2-3 days
        "https://www.hellofresh.com/recipes/most-recent-recipes", # Updated weekly?
        "http://www.afghankitchenrecipes.com/recent-recipes/", # Not updated often
        "https://www.baking-sense.com/all-blog-posts/", # New posts 2-3 times per month
        "https://www.bbc.co.uk/food/seasons/" # List of recipes by month
    ]

    if random_sleeps:
        sleep_time = random.uniform(lower_sleep, upper_sleep)
        time.sleep(sleep_time)

    filtered_urls = []

    # Define the patterns using regular expressions
    allrecipes_pattern = re.compile(r'https://www\.allrecipes\.com/recipe/\d+/\w+(?:-\w+)+/')
    food52_pattern = re.compile(r'/recipes/([^/]+)')
    nytimes_pattern = re.compile(r'/recipes/\d+-[a-z-]+')
    hellofresh_pattern = re.compile(r'https://www\.hellofresh\.com/recipes/[\d\w-]+-\w{24}')
    afghankitchen_pattern = re.compile(r'http://www\.afghankitchenrecipes\.com/recipe/[\w-]+/')
    bakingsense_pattern = re.compile(r'https://www\.baking-sense\.com/\d+/\d+/\d+/[\w-]+/')

    for base_url in base_urls:
        html = httpx.get(url=base_url, headers=headers).content
        soup = BeautifulSoup(html, "html.parser")

        # Find all <a> tags with a 'href' attribute
        links = [a["href"] for a in soup.find_all("a", href=True)]

        if "allrecipes" in base_url:
            # Filter out non-recipe links for All Recipes
            recipe_links = [url for url in links if allrecipes_pattern.match(url)]
        elif "food52" in base_url:
            # Filter out non-recipe links for Food 52 and concatenate the string
            recipe_links = [f"https://www.food52.com{url}" for url in links if food52_pattern.match(url)]
        elif "nytimes" in base_url:
            # Filter out non-recipe links for NY Times and concatenate the string
            recipe_links = [f"https://cooking.nytimes.com{url}" for url in links if nytimes_pattern.match(url)]
        elif "hellofresh" in base_url:
            # Filter out non-recipe links for Hello Fresh
            recipe_links = [url for url in links if hellofresh_pattern.match(url)]
        elif "afghankitchenrecipes" in base_url:
            # Filter out non-recipe links for Afghan Kitchen Recipes
            recipe_links = [url for url in links if afghankitchen_pattern.match(url)]
        elif "baking-sense" in base_url:
            # Filter out non-recipe links for All Recipes
            recipe_links = [url for url in links if bakingsense_pattern.match(url)]

        # Add the filtered links to the result
        filtered_urls.extend(recipe_links)

    random.shuffle(filtered_urls)

    return filtered_urls

# Example usage
new_urls = get_new_urls()
print(len(new_urls))
print(new_urls)


