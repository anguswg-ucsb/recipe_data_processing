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
# from decimal import Decimal

# library for making HTTPS requests
import httpx

# AWS SDK for Python (Boto3) and S3fs for S3 file system support
import boto3
import s3fs

# Import recipe_scrapers library
from recipe_scrapers import scrape_me, scrape_html


# # import the environment variables from the config.py file
# # import lambdas.stage_s3_to_prod_s3.config
# from config import Config

# environemnt variables
S3_BUCKET        = os.environ.get('S3_BUCKET')
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

    # # format each item as a dictionary with the correct data type
    # ddb_item = {
    #     "uid": {"S": origin_json["uid"]},
    #     "id": {"S": origin_json["uid"]},
    #     "dish": {"S": origin_json["dish"]},
    #     "ingredients": {"S": origin_json["ingredients"]},
    #     "quantities": {"S": origin_json["quantities"]},
    #     "directions": {"S": origin_json["directions"]},
    #     "description": {"S": origin_json["description"]},
    #     "prep_time": {"S": str(origin_json["prep_time"])},
    #     "cook_time": {"S": str(origin_json["cook_time"])},
    #     "total_time": {"S": str(origin_json["total_time"])},
    #     "yields": {"S": str(origin_json["yields"])},
    #     "category": {"S": origin_json["category"]},
    #     "cuisine": {"S": origin_json["cuisine"]},
    #     "ratings": {"S": str(origin_json["ratings"])},
    #     "url": {"S": origin_json["url"]},
    #     "img": {"S": origin_json["img"]},
    #     "source": {"S": origin_json["source"]},
    #     'status_code': {'N': str(status_code)},
    #     "timestamp": {'N': str(epoch_time)}
    # }

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
    
    # # Send a GET request to the website
    # url = "http://checkip.amazonaws.com/"
    # response = requests.get(url, proxies=proxies)
    # response.content

    return proxies

# Function to make a request with retries and delay
def make_request_with_retry(url, header, origin_json, max_retries=3, initial_sleep=5, max_sleep=15, status_code = -1):
    
    # url           = s3_json["url"]
    # header        = header
    # origin_json   = s3_json
    # max_retries   = 3
    # initial_sleep = 7
    # max_sleep     = 15
    # status_code   = -1
    # proxy        = get_proxy()

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

            # # Log the failed request to DynamoDB
            # log_failed_request(url, origin_json, status_code)
            # # log_failed_request(url, exc.request.status_code, origin_json)

        except Exception as esc:
            print(f"Error with url: {url}, {exc}")

        print(f"Retrying... (Attempt {attempt + 1})")
        backoff_time = random.randint(initial_sleep, min(max_sleep, initial_sleep * 2**attempt))
        print(f"Sleeping for {backoff_time} seconds...")

        time.sleep(backoff_time)

    print(f"Max retries reached for url: {url}")

    # # Log the request with maximum retries reached to DynamoDB
    # log_failed_request(url, origin_json, status_code) if status_code != -1 else log_max_retries_exceeded(url, origin_json, status_code)

    # Log the request with status code if status code is NOT the default value and put the log into DynamoDB table
    if status_code != -1:
        log_failed_request(url, origin_json, status_code)

    # Log the request with maximum retries reached to DynamoDB
    log_max_retries_exceeded(url, origin_json, status_code)

    return None

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
    message_id = message["messageId"]
    
    print(f"message_id: {message_id}")

    # Get the S3 event notification JSON object from the message body
    s3_event = json.loads(message["body"])
    # s3_event = event["Records"][0]["body"]

    # Extract the S3 bucket and the filename from the S3 event notification JSON object
    S3_BUCKET    = s3_event['Records'][0]['s3']['bucket']['name']
    S3_FILE_NAME = s3_event['Records'][0]['s3']['object']['key']

    print(f"=====================")
    print(f'---->\n Value of s3_event: {s3_event}')
    print(f"=====================")

    print(f"- S3_BUCKET: {S3_BUCKET}")
    print(f"- S3_FILE_NAME: {S3_FILE_NAME}")
    
    # get the object from S3
    s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)

    # json_path = "/Users/anguswatters/Desktop/recipes_json_chunks/subdirectory_3/906928_www_allrecipes_com.json"

    # # Open the JSON file for reading
    # with open(json_path, 'r') as file:
    #     # Load the JSON data from the file
    #     s3_json = json.load(file)

    # # Now, 'data' contains a Python dictionary with the content of the JSON file
    # print(s3_json)
    # keys_to_keep = ["uid", "url"]

    # # # Create a new dictionary with only the keys we want to keep
    # s3_json = {key: s3_json[key] for key in keys_to_keep}

    # read the JSON file into a dictionary
    s3_json = json.load(s3_obj["Body"])
    
    # s3_json = response_obj.get('Body').read().decode('utf-8')

    # s3_json = row_dict
    print(f"s3_json: {s3_json}")

    # s3_json['url']
    print(f"s3_json['url']: {s3_json['url']}")

    # get a random sleep time between 1 and 5 seconds
    random_sleep_time = random.randint(4, 6)
    
    print(f"Sleeping for {random_sleep_time} seconds...")
    
    # sleep for a random amount of time
    time.sleep(random_sleep_time)

    # get a list of viable headers from scrapeops.io header API
    header_list = get_headers_list()

    # get a random header from the list of headers from scrapeops.io header API
    header = get_random_header(header_list)
    # s3_json["url"]

    # # Make a request to URL from the S3 JSON file
    # response = httpx.get(s3_json["url"], headers=header)

    # # get the HTML content from the response
    # html = response.content
    
    # # Use recipe_scrapers to scrape the recipe from the HTML content
    # scraped_data = scrape_html(html = html, org_url = s3_json["url"])
    # scraped_data.to_json()
    
    # get the scraped data from the URL with exponential backoff retries
    scraped_json = make_request_with_retry(
        url           = s3_json["url"], 
        header        = header,
        origin_json   = s3_json,
        max_retries   = 3, 
        initial_sleep = 7, 
        max_sleep     = 15,
        status_code   = -1
        )

    # if None is returned from the request, return False
    if not scraped_json:
        print(f"Error retrieving scraped data from url: {s3_json['url']}")
        return False

    # create a mapping to rename scraped json keys to add back to original json
    key_mapping = {key : "scraped_" + key for key in scraped_json.keys()}

    # Create a new dictionary with the renamed keys
    updated_scraped_json = {key_mapping.get(old_key, old_key): value for old_key, value in scraped_json.items()}

    # add the scraped data to the original json
    s3_json.update(updated_scraped_json)

    # generate a random UUID to add to the OUTPUT_S3_OBJECT_NAME
    unique_id = f"{uuid.uuid4().hex}"

    # extract the base file name and the extension from the file_name
    BASE_NAME, extension = os.path.splitext(S3_FILE_NAME)

    print(f"BASE_NAME: '{BASE_NAME}'")
    print(f"extension: '{extension}'")

    # name of the output json file
    OUTPUT_S3_OBJECT_NAME = f"stage_{BASE_NAME}_{unique_id}.json"

    print(f"OUTPUT_S3_OBJECT_NAME: '{OUTPUT_S3_OBJECT_NAME}'")

    # save the output JSON to local lambda /tmp/ folder to upload to output S3 bucket
    LAMBDA_JSON_FILEPATH = f"/tmp/{OUTPUT_S3_OBJECT_NAME}"

    print(f"LAMBDA_JSON_FILEPATH: {LAMBDA_JSON_FILEPATH}")

    # Save the dictionary as a JSON file
    with open(LAMBDA_JSON_FILEPATH, 'w') as json_file:
        json.dump(s3_json, json_file)

    print(f"Uploading '{LAMBDA_JSON_FILEPATH}' to:\n - OUTPUT_S3_BUCKET: '{OUTPUT_S3_BUCKET}'\n - OUTPUT_S3_OBJECT_NAME: '{OUTPUT_S3_OBJECT_NAME}'")

    # Upload file to S3 Bucket
    try:
        # Upload the file
        response = s3.upload_file(LAMBDA_JSON_FILEPATH, OUTPUT_S3_BUCKET, OUTPUT_S3_OBJECT_NAME)

    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return False

    return {'status': 'True',
            'statusCode': 200,
            'body': 'JSON Uploaded'}

# lambda handler function
def recipe_scraper_lambda(event, context):
    message_count = 0
    
    batch_item_failures = []
    sqs_batch_response = {}

    for message in event['Records']:

        message_count += 1
        print(f"PROCESSING MESSAGE: {message_count}")
        try:
            process_message(message)
        except Exception as e:
            batch_item_failures.append({"itemIdentifier": message['messageId']})
        
    sqs_batch_response["batchItemFailures"] = batch_item_failures

    print(f"sqs_batch_response: {sqs_batch_response}")

    return sqs_batch_response

    