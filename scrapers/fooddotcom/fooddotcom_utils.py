import requests
from bs4 import BeautifulSoup
import re
from recipe_scrapers import scrape_me 
import pandas as pd
import random 
import time


# get recipe URLs from a "base_url" from www.food.com
def get_fooddotcom_recipe_urls(base_url):

    # Base URL is a URL from www.food.com with a list of recipes on the page
    # Examples:
    # base_url = "https://www.food.com/ideas/top-breakfast-recipes-6935#c-796349"

    # Fetch HTML content
    html = requests.get(base_url).content
    
    soup = BeautifulSoup(html, "html.parser")

    # Find all <a> tags with a not null 'href' attribute
    links = [a["href"] for a in soup.find_all("a", href=True)]
    
#    food_links = [ 'https://www.food.com/recipe/gourmet-huevos-rancheros-129203', 
#     'https://www.food.com/recipe/award-winning-chili-105865', 
#     'https://www.food.com/recipe/jo-mamas-world-famous-spaghetti-22782' ]
    
    # Define the pattern using a regular expression
    pattern = re.compile(r'https://www\.food\.com/recipe/\w+(?:-\w+)+-\d+')

    # Use list comprehension to filter the URLs
    filtered_urls = [url for url in links if pattern.match(url)]

    return filtered_urls

# Get a list of URLs that lead to recipes from food.com. There are some hardcoded base URLs that contain many recipes and then 
# there is a process for looking through the Main navbar on the site and going through the dropdown section links.
# Returns a list of recipe URLs from food.com
# random_sleeps is a boolean stating whether to randomly pause the search to slow down and not overload anyones servers 
def build_fooddotcom_urls(random_sleeps=True):

    # List of base URLs to get list of URLs of recipes
    base_urls = [
        "https://www.food.com/ideas/top-breakfast-recipes-6935#c-796349",
        "https://www.food.com/ideas/quick-easy-pasta-recipes-6078",
        "https://www.food.com/ideas/fun-salad-ideas-6301?ref=nav",
        "https://www.food.com/ideas/copycat-recipes-6576?ref=nav"
        ] 

    # get any URLs from buttons on the "base_urls" pages to find more recipes
    for url in base_urls:
        print(f"url: {url}")

        # get URLs of "See Them All" buttons
        button_url = extract_button_urls(url, random_sleeps=random_sleeps)

        # add newly found button URLs to base_urls list
        base_urls.extend(button_url)

    # get URLs from the navbar of the main page
    navbar_urls = fooddotcom_navbar_urls(random_sleeps=random_sleeps)

    # Add URLs from navbar to list of base_urls
    base_urls.extend(navbar_urls)
    # len(base_urls)

    # remove duplicates
    urls_set = set(base_urls)
    # len(urls_set)

    # convert deduplicated set back to a list
    base_urls = list(urls_set)
    # len(base_urls)
    
    # output list of recipe URLs
    recipe_list = []

    print(f"Scraping recipes from\n{base_urls}")

    for url in base_urls:

        print(f"Getting recipes from:\n - {url}")

        recipe_url = get_fooddotcom_recipe_urls(url)
        # get_fooddotcom_recipe_urls("https://www.food.com/ideas/valentines-day-6499?ref=nav")
    
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

    # get all of the links in the dropdowns of the navbar on food.com
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

            # button_href = see_them_all_button.get("href")
            button_hrefs = [link.get("href") for link in see_them_all_button if link.get("href")]
            # print(f"Replacing:\n - {url}\nwith:\n - {button_href}")
            
            button_list.extend(button_hrefs)
            to_drop.append(url)

    for i in nav_hrefs:
        if i not in to_drop:
            button_list.append(i)
    
    return button_list
    
# from a food.com URL, get the URLs from the "See Them All" buttons that typically have an href to another page that contains many recipes
# Given a food.com URL, returns the links found in all the See Them All buttons
def extract_button_urls(url, random_sleeps = True):

    button_urls = [] 

    # if random_sleeps is True, delay the request for 2-4 seconds
    if random_sleeps:
        sleep_time = random.randint(2, 4)
        time.sleep(sleep_time)

    # get HTML
    html = requests.get(url).content

    # parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Find all of the <a> tag with the text "See them all"
    see_them_all_button = soup.find_all("a", string="See Them All")

    if see_them_all_button:
        # print(f"Found {len(see_them_all_button)} 'See Them All' button!")
        
        button_hrefs = [link.get("href") for link in see_them_all_button if link.get("href")]
        # print(f"Replacing:\n - {url}\nwith:\n - {button_href}")
        
        button_urls.extend(button_hrefs)
    
    return button_urls


def fooddotcom_scraper(url, limit = None):
    # url = filtered_urls[0]

    print(f"Scraping recipe from {url}")

    # Use recipe_scrapers to scrape recipe information
    scraper = scrape_me(url)

    # convert recipe to json
    recipe_json = scraper.to_json()

    # # convert json to pandas dataframe
    # recipe_row = pd.DataFrame.from_dict(recipe_json, orient='index').transpose()

    # # fill missing values with empty string ""
    # recipe_row = recipe_row.fillna('')

    # # Save recipe information to a dictionary
    # recipe_info = {
    #     "title": scraper.title(),
    #     "total_time": scraper.total_time(),
    #     "ingredients": scraper.ingredients(),
    #     "instructions": scraper.instructions(),
    #     "image": scraper.image(),
    # }

    # # Append the dictionary to the list
    # recipe_list.append(recipe_info)

    return recipe_json