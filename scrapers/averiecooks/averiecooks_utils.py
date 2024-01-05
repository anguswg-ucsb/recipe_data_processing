import random
import time
import httpx
from bs4 import BeautifulSoup
import re
from recipe_scrapers import scrape_me 


# Get recipe URLs from a "base_url" from www.food.com
def get_averiecooks_recipe_urls(base_url, random_sleeps=True, lower_sleep=2, upper_sleep=5):
    
    if random_sleeps:
        sleep_time = random.randint(lower_sleep, upper_sleep)
        time.sleep(sleep_time)

    # Fetch HTML content
    html = httpx.get(base_url).content

    # Print the HTML content for troubleshooting
    print(f"2.1 HTML content for {base_url}:\n --> {html}")

    soup = BeautifulSoup(html, "html.parser")

    # Find all <a> tags with a not null 'href' attribute
    links = [a["href"] for a in soup.find_all("a", href=True)]
    
    # Define the pattern using a regular expression
    pattern = re.compile(r'https://www\.averiecooks\.com/([a-zA-Z]+-){2,}[a-zA-Z]+/')

    # Print the links found for troubleshooting
    print(f"2.2 Links found on {base_url}:\n --> {links}")

    # Filter out unwanted url patterns
    unwanted_patterns = [
                "/interview-with-averie/", 
                "/work-with-me/"
            ]

    # Use list comprehension to filter the URLs
    filtered_urls = [url for url in links if pattern.match(url) and not any(re.search(pattern, url) for pattern in unwanted_patterns)]

    return filtered_urls

def build_averiecooks_urls(random_sleeps=True, start_page=2, end_page=3):
    # Base URL is a URL from www.averiecooks.com with a list of recipes on the page
    base_url_template = "https://www.averiecooks.com/category/recipes/page/{}/?utm_campaign=Landing%20Page%20or%20Form%20-%205506760&utm_medium=email&utm_source=convertkit"
    
    # List of base URLs to get list of URLs of recipes
    base_urls = [base_url_template.format(page) for page in range(start_page, end_page + 1)]
    
    # Output list of recipe URLs
    recipe_list = []

    # Print a message indicating that recipe scraping is starting from the specified base URLs
    print(f"1.1 Staring to scrape recipes from:\n --> {base_urls}")

    # Iterate through each base URL
    for url in base_urls:
        # Print a message indicating the current base URL being processed
        print(f"1.2 Getting recipes from:\n --> {url}")

        # Call the function to get Averiecooks recipe URLs from the current base URL
        recipe_url = get_averiecooks_recipe_urls(url, random_sleeps=True, lower_sleep=2, upper_sleep=5)

        # Extend the recipe_list with the URLs obtained from the current base URL
        recipe_list.extend(recipe_url)

    return recipe_list


def averiecooks_scraper(url, limit = None):

    # Print a message indicating that recipe scraping is starting from the specified URLs
    print(f"Scraping recipe from {url}")

    # Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # Convert recipe to json
    recipe_json = scraper.to_json()

    return recipe_json