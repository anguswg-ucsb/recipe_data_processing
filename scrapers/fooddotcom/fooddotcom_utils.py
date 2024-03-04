import requests
from bs4 import BeautifulSoup
import re
from recipe_scrapers import scrape_me 
import pandas as pd
import random 
import time


# Get recipe URLs from a "base_url" from www.food.com
def get_fooddotcom_recipe_urls(base_url):

    # Fetch HTML content
    html = requests.get(base_url).content
    
    soup = BeautifulSoup(html, "html.parser")

    # Find all <a> tags with a not null 'href' attribute
    links = [a["href"] for a in soup.find_all("a", href=True)]
    
    # Define the pattern using a regular expression
    pattern = re.compile(r'https://www\.food\.com/recipe/\w+(?:-\w+)+-\d+')

    # Use list comprehension to filter the URLs
    filtered_urls = [url for url in links if pattern.match(url)]

    return filtered_urls

# Get a list of URLs that lead to recipes from food.com. 
# There are some hardcoded base URLs that contain many recipes and then there is a process for looking through the Main navbar on the site and going through the dropdown section links.
# Returns a list of recipe URLs from food.com.
def build_fooddotcom_urls(random_sleeps=True):

    # List of base URLs to get list of URLs of recipes
    base_urls = [
        "https://www.food.com/ideas/top-breakfast-recipes-6935#c-796349",
        "https://www.food.com/ideas/quick-easy-pasta-recipes-6078",
        "https://www.food.com/ideas/fun-salad-ideas-6301?ref=nav",
        "https://www.food.com/ideas/copycat-recipes-6576?ref=nav"
        ] 

    # Get any URLs from buttons on the "base_urls" pages to find more recipes
    for url in base_urls:
        print(f"url: {url}")

        # Get URLs of "See Them All" buttons
        button_url = extract_button_urls(url, random_sleeps=random_sleeps)

        # Add newly found button URLs to base_urls list
        base_urls.extend(button_url)

    # Get URLs from the navbar of the main page
    navbar_urls = fooddotcom_navbar_urls(random_sleeps=random_sleeps)

    # Add URLs from navbar to list of base_urls
    base_urls.extend(navbar_urls)

    # Remove duplicates
    urls_set = set(base_urls)

    # Convert deduplicated set back to a list
    base_urls = list(urls_set)
    
    # Output list of recipe URLs
    recipe_list = []

    print(f"Scraping recipes from\n{base_urls}")

    for url in base_urls:

        print(f"Getting recipes from:\n - {url}")

        recipe_url = get_fooddotcom_recipe_urls(url)
    
        recipe_list.extend(recipe_url)
    
    return recipe_list

# Extract base URLs from the navbar of food.com, also any links from the navbar dropdowns
# with "See Them All" button will check these buttons and add there hrefs to the return list of base URLs 
def fooddotcom_navbar_urls(random_sleeps = True):

    navbar_url = "https://www.food.com/?ref=nav"

    # Fetch HTML content
    html = requests.get(navbar_url).content
    
    soup = BeautifulSoup(html, "html.parser")

    # Find the <nav> element with ID "main-nav"
    main_nav = soup.find("nav", {"id": "main-nav"})

    # Find all <a> tags within the <nav> element
    nav_links = main_nav.find_all("a")

    # Extract href attributes from the <a> tags
    hrefs = [link.get("href") for link in nav_links if link.get("href")]

    # Get all of the links in the dropdowns of the navbar on food.com
    nav_hrefs = ["https://www.food.com" + i for i in hrefs]

    button_list = [] 
    to_drop = []

    for i in range(len(nav_hrefs)):

        url = nav_hrefs[i]

        if random_sleeps:
            sleep_time = random.randint(3, 7)
            time.sleep(sleep_time)

        html = requests.get(url).content
    
        soup = BeautifulSoup(html, "html.parser")

        # Find the <a> tag with the text "See them all"
        see_them_all_button = soup.find_all("a", string="See Them All")

        if see_them_all_button:
            print(f"Found {len(see_them_all_button)} 'See Them All' button!")

            button_hrefs = [link.get("href") for link in see_them_all_button if link.get("href")]
            
            button_list.extend(button_hrefs)
            to_drop.append(url)

    for i in nav_hrefs:
        if i not in to_drop:
            button_list.append(i)
    
    return button_list
    

# Given a food.com URL, returns the links found in all the See Them All buttons
def extract_button_urls(url, random_sleeps = True):

    button_urls = [] 

    # If random_sleeps is True, delay the request for 2-4 seconds
    if random_sleeps:
        sleep_time = random.randint(2, 4)
        time.sleep(sleep_time)

    # Get HTML
    html = requests.get(url).content

    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Find all of the <a> tag with the text "See them all"
    see_them_all_button = soup.find_all("a", string="See Them All")

    if see_them_all_button:
        
        button_hrefs = [link.get("href") for link in see_them_all_button if link.get("href")]
        button_urls.extend(button_hrefs)
    
    return button_urls


def fooddotcom_scraper(url, limit = None):
    print(f"Scraping recipe from {url}")

    # Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # Convert recipe to json
    recipe_json = scraper.to_json()

    return recipe_json