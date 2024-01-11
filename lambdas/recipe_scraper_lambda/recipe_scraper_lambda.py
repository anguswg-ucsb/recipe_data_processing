# Description: 
    # Python script for an AWS Lambda function that gets triggered by an S3 Event notification and 
    # consumes newly created JSON objects and retrieves additional data for the JSON from the internet.
    # The new data is added the original JSON and is uploaded with a unique ID to another S3 bucket for outputs
    # Designed to be zipped up with its dependencies and provided as a zip file to an AWS Lambda function
# Usage: python recipe_scraper_lambda.py
# Author: Angus Watters

# general utility libraries
import os
from datetime import datetime
import json
import random
import time
import uuid
import re
# import sys 

# library for making HTTPS requests
import httpx

# AWS SDK for Python (Boto3) and S3fs for S3 file system support
import boto3
# import s3fs
# import awswrangler as wr
import pandas as pd

# Import recipe_scrapers library
from recipe_scrapers import scrape_me, scrape_html

# environemnt variables
OUTPUT_S3_BUCKET = os.environ.get('OUTPUT_S3_BUCKET')
DYNAMODB_TABLE   = os.environ.get('DYNAMODB_TABLE')

# Bright Data credentials
BRIGHT_DATA_USERNAME = os.environ.get('BRIGHT_DATA_USERNAME')
BRIGHT_DATA_PASSWORD = os.environ.get('BRIGHT_DATA_PASSWORD')
BRIGHT_DATA_HOST     = os.environ.get('BRIGHT_DATA_HOST')
BRIGHT_DATA_PORT     = os.environ.get('BRIGHT_DATA_PORT')

# Scrape Ops API Key
SCRAPE_OPS_API_KEY = os.environ.get('SCRAPE_OPS_API_KEY')

# S3 client
s3 = boto3.client('s3')

# DynamoDB client
dynamodb = boto3.client('dynamodb')

# function to make a DynamoDB item and add a status code and timestamp. 
# Input JSON object just requires an "uid" key
def make_dynamodb_item(origin_json, status_code=-1):

    # set any None values to empty strings
    for key, value in origin_json.items():
        if value is None:
            origin_json[key] = ""

    # get the current time
    current_time = datetime.now()

    # convert the current datetime object to epoch time integer
    epoch_time = int(current_time.timestamp())

    # initialize an empty dictionary for ddb_item
    ddb_item = {"uid": {"S": origin_json["uid"]}}

    # iterate through keys in origin_json and add them to ddb_item
    for key, value in origin_json.items():
        ddb_item[key] = {"S": str(value)}
    
    # add additional keys like status_code and timestamp
    ddb_item['status_code'] = {'N': str(status_code)}
    ddb_item["timestamp"] = {'N': str(epoch_time)}

    return ddb_item

# Function to log failed request to DynamoDB
def log_failed_request(url, origin_json, status_code = -1):

    # Create a DynamoDB item
    ddb_item = make_dynamodb_item(origin_json, status_code)

    try:
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=ddb_item
        )
    except Exception as e:
        print(f"Error logging failed request to DynamoDB: {e}")

# Function to log request with maximum retries reached to DynamoDB
def log_max_retries_exceeded(url, origin_json, status_code = -1):
    
    # Create a DynamoDB item
    ddb_item = make_dynamodb_item(origin_json, status_code)

    try:
        dynamodb.put_item(
            TableName=DYNAMODB_TABLE,
            Item=ddb_item
        )
    except Exception as e:
        print(f"Error logging max retries exceeded to DynamoDB: {e}")

# Function to get a proxy from Bright Data
def get_proxy():

    session_id = random.random()

    # format your proxy
    proxy_url = f'https://{BRIGHT_DATA_USERNAME}-session-{session_id}:{BRIGHT_DATA_PASSWORD}@{BRIGHT_DATA_HOST}:{BRIGHT_DATA_PORT}'

    # define your proxies in dictionary
    proxies = {'http://': proxy_url, 'https://': proxy_url}   

    return proxies

# Function to make a request with retries and delay
def make_request_with_retry(url, header, origin_json, max_retries=3, initial_sleep=5, max_sleep=15, status_code = -1):

    for attempt in range(max_retries):
        
        # get a random proxy from Bright Data
        proxy        = get_proxy()

        try:
            # Make a request to the URL
            print(f"Getting recipe data from: {url}")
            response = httpx.get(url=url, headers=header, follow_redirects=True, proxies=proxy)
            # response = httpx.get(url=url, follow_redirects=True)

            response.raise_for_status()  # Raise HTTPError for bad responses

            # Get the HTML content from the response
            html = response.content

            # Use recipe_scrapers to scrape the recipe from the HTML content
            scraped_data = scrape_html(html=html, org_url=url)
            scraped_json = scraped_data.to_json()

            return scraped_json

        except httpx.HTTPError as exc:
            # print(f"HTTP error with url: {url}, status code: {response.status_code}")
            print(f"HTTP Exception for {exc.request.url} - {exc}")

            # get status code
            status_code = exc.response.status_code if hasattr(exc, 'response') else -1
            # status_code = exc.response.status_code

            print(f"HTTP request failed with status code: {status_code}")

        except Exception as esc:
            print(f"Error with url: {url}, {exc}")

        print(f"Retrying... (Attempt {attempt + 1})")
        backoff_time = random.randint(initial_sleep, min(max_sleep, initial_sleep * 2**attempt))
        print(f"Sleeping for {backoff_time} seconds...")

        time.sleep(backoff_time)

    print(f"Max retries reached for url: {url}")

    # Log the request with status code if status code is NOT the default value and put the log into DynamoDB table
    if status_code != -1:
        log_failed_request(url, origin_json, status_code)

    # Log the request with maximum retries reached to DynamoDB
    log_max_retries_exceeded(url, origin_json, status_code)

    return None


def truncate_filename(filename, max_bytes=1024):
    # Calculate the maximum allowed length for the filename (including ".json")
    max_length = max_bytes - len(".json")
    
    # Truncate the filename while preserving the ".json" extension
    truncated_name = filename[:max_length] + ".json"
    
    return truncated_name

# santitize_json function to complete
def sanitize_json(json_obj):
    # create a function that ensures each output json (python dictionary) has the same keys, 
    # if any keys are missing, then insert an appropriate missing value)

    # create a list of all the keys that should be in each json object
    keys_to_keep = [
        "host", "title", "category", "total_time", "cook_time", "prep_time",
        "yields", "image", "ingredients", "instructions", "ratings",
        "author", "cuisine", "description", 
        "uid", "url", "ingredient_tags" # keys that are added and do NOT come from the recipe scraper
        ]
    
    # create a dictionary of the keys and their data types
    keys_to_type_map = {
        "host": str,
        "title": str,
        "category": list,
        "total_time": int,
        "cook_time": int,
        "prep_time": int,
        "yields": str,
        "image": str,
        "ingredients": list,
        "instructions": list,
        "ratings": int,
        "author": str,
        "cuisine": list,
        "description": str,
        "uid": str,
        "url": str,
        "ingredient_tags": list
        }
    
    # iterate over each key and add it with an appropriate empty value if missing
    for key in keys_to_keep:
        # print(f"key: {key}")
        # check if key is in json object
        if key not in json_obj or json_obj[key] is None:
            print(f"==== '{key}' not in json_obj or is None ====")
            print(f"---> Adding key: {key} to json_obj")

            # add key with an empty value based on the data type
            default_value = (
                0 if keys_to_type_map[key] == int else
                [] if keys_to_type_map[key] == list else
                ""  # assuming all other cases are strings
            )
            json_obj[key] = default_value
        else:
            # coerce the value to the expected type if needed
            expected_type = keys_to_type_map[key]
            current_type = type(json_obj[key])

            if current_type != expected_type:
                try:
                    # try to coerce the value to the expected type
                    if expected_type == list:
                        # if expected type is list and value is a string, put it in a list
                        json_obj[key] = [json_obj[key]]
                    else:
                        json_obj[key] = expected_type(json_obj[key])
                except ValueError:
                    # handle the case where coercion is not possible, set to default value
                    json_obj[key] = (
                        0 if expected_type == int else
                        [] if expected_type == list else
                        ""  # assuming all other cases are strings
                    )
    # Remove keys that are not in keys_to_keep
    json_obj = {key: json_obj[key] for key in keys_to_keep if key in json_obj}

    return json_obj

# code to process one of the batch of messages in SQS queue
def process_message(message):

    def get_headers_list():
        response = httpx.get(f"https://headers.scrapeops.io/v1/browser-headers?api_key={SCRAPE_OPS_API_KEY}")

        json_response = response.json()

        return json_response.get('result', [])
    
    def get_random_header(header_list):

        random_index = random.randint(0, len(header_list) - 1)

        return header_list[random_index]
    
    print(f"=====================")
    print(f'---->\n Value of message: {message}')
    print(f"=====================")

    # Get the SQS event message ID
    message_id   = message["messageId"]

    # Get the SQS event message body
    message_body = json.loads(message["body"])

    # # test message body
    # output_list = []
    # message_body = {"uid": "test_uid", "url": "https://www.food.com/recipe/lenten-lentils-oaxacan-style-85328"}

    print(f"- message_id: {message_id}")
    print(f"- message_body: {message_body}")
    
    print(f"message_body['url']: {message_body['url']}")

    # get a random sleep time between 1 and 5 seconds
    random_sleep_time = random.randint(1, 2)
    
    print(f"Sleeping for {random_sleep_time} seconds...")
    
    # sleep for a random amount of time
    time.sleep(random_sleep_time)

    # get a list of viable headers from scrapeops.io header API
    header_list = get_headers_list()

    # get a random header from the list of headers from scrapeops.io header API
    header = get_random_header(header_list)
    
    # get the scraped data from the URL with exponential backoff retries
    scraped_json = make_request_with_retry(
        url           = message_body["url"], 
        header        = header,
        origin_json   = message_body,
        max_retries   = 1, 
        initial_sleep = 3, 
        max_sleep     = 9,
        status_code   = -1
        )

    # if None is returned from the request, raise an error
    if scraped_json is None:
        error_message = f"Error retrieving scraped data from url: {message_body['url']}"
        print(error_message)
        raise Exception(error_message)
    
    # # create a mapping to rename scraped json keys to add back to original json
    # key_mapping = {key : "scraped_" + key for key in scraped_json.keys()}
    # # Create a new dictionary with the renamed keys
    # updated_scraped_json = {key_mapping.get(old_key, old_key): value for old_key, value in scraped_json.items()}

    # add the scraped data to the original json
    message_body.update(scraped_json)

    try:
        message_body = sanitize_json(message_body)
    except Exception as e:
        print(f"Error sanitizing json: {e}")
        print(f"Returning message_body without sanitization")
        return message_body
    
    return message_body
    
    # # generate a random UUID to add to the OUTPUT_S3_OBJECT_NAME
    # unique_id = f"{uuid.uuid4().hex}"

    # # # extract the base file name and the extension from the file_name
    # # BASE_NAME, extension = os.path.splitext(message_body["url"])
    # # os.path.basename(message_body["url"])

    # # use URL to generate unique filename
    # url_filename = message_body["url"]

    # # remove http:// or https:// from the URL
    # url_filename = re.sub("http://|https://", "", url_filename)

    # # regex pattern to match all special characters and whitespaces
    # pattern = re.compile(r'[^a-zA-Z0-9]+')

    # # replace special character/whitespaces with underscores
    # url_filename = re.sub(pattern, '_', url_filename)

    # # get the midpoint of the filename
    # midpoint = len(url_filename)//2

    # # truncate the filename to half its size if the length of the filename is greater than 700 characters
    # # (S3 object key just needs to be under 1024 bytes, this wont ever really be an issue probably)
    # url_filename = url_filename if len(url_filename) < 700 else url_filename[:midpoint]

    # print(f"url_filename: '{url_filename}'")

    # # name of the output json file
    # OUTPUT_S3_OBJECT_NAME = f"stage_{url_filename}_{unique_id}.json"

    # print(f"OUTPUT_S3_OBJECT_NAME: '{OUTPUT_S3_OBJECT_NAME}'")

    # # save the output JSON to local lambda /tmp/ folder to upload to output S3 bucket
    # LAMBDA_JSON_FILEPATH = f"/tmp/{OUTPUT_S3_OBJECT_NAME}"
    # print(f"LAMBDA_JSON_FILEPATH: {LAMBDA_JSON_FILEPATH}")
    # # # Save the dictionary as a JSON file
    # # with open(LAMBDA_JSON_FILEPATH, 'w') as json_file:
    # #     json.dump(message_body, json_file)
    # # print(f"Uploading '{LAMBDA_JSON_FILEPATH}' to:\n - OUTPUT_S3_BUCKET: '{OUTPUT_S3_BUCKET}'\n - OUTPUT_S3_OBJECT_NAME: '{OUTPUT_S3_OBJECT_NAME}'")
    # # # Upload file to S3 Bucket
    # # try:
    # #     # Upload the file
    # #     response = s3.upload_file(LAMBDA_JSON_FILEPATH, OUTPUT_S3_BUCKET, OUTPUT_S3_OBJECT_NAME)
    # # except Exception as e:
    # #     print(f"Error uploading file to S3: {e}")
    # #     return False

    # return message_body

# lambda handler function
def recipe_scraper_lambda(event, context):
    message_count = 0
    
    batch_item_failures = []
    sqs_batch_response = {}

    json_list       = []

    for message in event['Records']:

        message_count += 1
        print(f"PROCESSING MESSAGE: {message_count}")
        try:
            # process_message(message)
            scraped_data = process_message(message)
            json_list.append(scraped_data)
        except Exception as e:
            print(f"Exception raised from messageId {message['messageId']}\n: {e}")
            batch_item_failures.append({"itemIdentifier": message['messageId']})
    
    print(f"Creating dataframe from {len(json_list)} json objects...")

    df = pd.DataFrame(json_list)
    print(f"df.shape: {df.shape}")
    print(f"df.columns: {df.columns}")

    # generate a random UUID to add to the OUTPUT_S3_OBJECT_NAME
    unique_id = f"{uuid.uuid4().hex}"

    # Use uuid.uuid4() and current timestamp to create a unique filename
    csv_key = f"{unique_id}_{int(time.time())}.csv"

    # # create the S3 filename
    # OUTPUT_S3_FILENAME = f"s3://{OUTPUT_S3_BUCKET}/{csv_key}"
    
    LAMBDA_FILENAME = f"/tmp/{csv_key}"

    print(f"Saving dataframe to local lambda:\n - LAMBDA_FILENAME: '{LAMBDA_FILENAME}'")

    df.to_csv(LAMBDA_FILENAME, index=False)

    # print(f"Saving dataframe to S3:\n - OUTPUT_S3_FILENAME: '{OUTPUT_S3_FILENAME}'")

    # # save the dataframe to S3
    # # wr.s3.to_csv(df, OUTPUT_S3_FILENAME, index=False)
    # df.to_csv(OUTPUT_S3_FILENAME, index=False)

    # s3.upload_file(LAMBDA_FILENAME, OUTPUT_S3_BUCKET, csv_key)
    print(f"Uploading '{LAMBDA_FILENAME}' to:\n - OUTPUT_S3_BUCKET: '{OUTPUT_S3_BUCKET}'\n - csv_key: '{csv_key}'")
    # Upload file to S3 Bucket
    try:
        # Upload the file
        response = s3.upload_file(LAMBDA_FILENAME, OUTPUT_S3_BUCKET, csv_key)
        print(f"response: {response}")
        print(f"S3 upload successful!")

    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        # return False

    sqs_batch_response["batchItemFailures"] = batch_item_failures

    print(f"sqs_batch_response: {sqs_batch_response}")

    return sqs_batch_response
