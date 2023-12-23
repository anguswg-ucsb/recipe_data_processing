# Description: This script will pull data from Airtable and save it to S3 as a parquet file
# Usage: python airtable_to_sqs.py
# Author: Angus Watters

# general utility libraries
import os
from datetime import datetime
# import requests
import httpx
import random

import json
import random
import time

# AWS SDK for Python (Boto3) and S3fs for S3 file system support
import boto3
import s3fs
# import logging

# Import recipe_scrapers library
from recipe_scrapers import scrape_me, scrape_html


# import the environment variables from the config.py file
# import lambdas.stage_s3_to_prod_s3.config
from .config import Config

# environemnt variables
S3_BUCKET = os.environ.get('S3_BUCKET')
SCRAPE_OPS_API_KEY = os.environ.get('SCRAPE_OPS_API_KEY')
OUTPUT_S3_BUCKET = os.environ.get('OUTPUT_S3_BUCKET')

# S3 client
s3 = boto3.client('s3')

# # # test event
# event = {"Records": [
#     {
#       "eventVersion": "2.1",
#       "eventSource": "aws:s3",
#       "awsRegion": "us-east-1",
#       "eventTime": "2022-01-01T00:00:00.000Z",
#       "eventName": "ObjectCreated:Put",
#       "userIdentity": {
#         "principalId": "AWS:EXAMPLE"
#       },
#       "requestParameters": {
#         "sourceIPAddress": "127.0.0.1"
#       },
#       "responseElements": {
#         "x-amz-request-id": "EXAMPLE123456789",
#         "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
#       },
#       "s3": {
#         "s3SchemaVersion": "1.0",
#         "configurationId": "testConfigRule",
#         "bucket": {
#           "name": "example-bucket",
#           "ownerIdentity": {
#             "principalId": "EXAMPLE"
#           },
#           "arn": "arn:aws:s3:::example-bucket"
#         },
#         "object": {
#           "key": "example.json",
#           "size": 1024,
#           "eTag": "0123456789abcdef0123456789abcdef",
#           "versionId": "1",
#           "sequencer": "0A1B2C3D4E5F678901"
#         }
#       }
#     }
#   ]
# }

# event['Records'][0]['s3']['bucket']['name']
# event['Records'][0]['s3']['object']['key']

# # read in a JSON file from '/Users/anguswatters/Desktop/recipes_json/1643107_Recipes1M.json'
# path = '/Users/anguswatters/Desktop/recipes_json/1643107_Recipes1M.json'
# # Read the JSON file into a dictionary
# with open(path, 'r') as json_file:
#     data_dict = json.load(json_file)

# Function to make a request with retries and delay
def make_request_with_retry(url, header, max_retries=3, initial_sleep=5, max_sleep=15):
    for attempt in range(max_retries):
        try:
            # Make a request to the URL
            print(f"Getting recipe data from: {url}")
            response = httpx.get(url, headers=header)
            response.raise_for_status()  # Raise HTTPError for bad responses

            # Get the HTML content from the response
            html = response.content

            # Use recipe_scrapers to scrape the recipe from the HTML content
            scraped_data = scrape_html(html=html, org_url=url)
            scraped_json = scraped_data.to_json()

            return scraped_json

        except httpx.HTTPError as e:
            print(f"HTTP error with url: {url}, status code: {response.status_code}")
        except Exception as e:
            print(f"Error with url: {url}, {e}")

        print(f"Retrying... (Attempt {attempt + 1})")
        backoff_time = random.randint(initial_sleep, min(max_sleep, initial_sleep * 2**attempt))
        print(f"Sleeping for {backoff_time} seconds...")

        time.sleep(backoff_time)

    print(f"Max retries reached for url: {url}")

    return None

# lambda handler function
def s3_recipe_scraper(event, context):

    def get_headers_list():
        response = httpx.get(f"https://headers.scrapeops.io/v1/browser-headers?api_key={SCRAPE_OPS_API_KEY}")

        json_response = response.json()

        return json_response.get('result', [])
    
    def get_random_header(header_list):
        random_index = random.randint(0, len(header_list) - 1)
        return header_list[random_index]

    S3_BUCKET = event['Records'][0]['s3']['bucket']['name']
    S3_FILE_NAME = event['Records'][0]['s3']['object']['key']

    print(f"- S3_BUCKET: {S3_BUCKET}")
    print(f"- S3_FILE_NAME: {S3_FILE_NAME}")
    # print(f"- S3_STAGING_BUCKET: {S3_STAGING_BUCKET}")
    # print(f"- S3_PROD_BUCKET: {S3_PROD_BUCKET}")

    print(f"=====================")
    print(f'---->\n Value of event: {event}')
    print(f"=====================")

    # get the object from S3
    s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)

    # read the JSON file into a dictionary
    s3_json = json.load(s3_obj["Body"])
    # s3_json = response_obj.get('Body').read().decode('utf-8')

    # s3_json = row_dict
    print(f"s3_json: {s3_json}")

    # s3_json['url']
    print(f"s3_json['url']: {s3_json['url']}")

    # get a random sleep time between 1 and 5 seconds
    random_sleep_time = random.randint(1, 5)
    
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
    scraped_json = make_request_with_retry(url = s3_json["url"], header = header, max_retries=3, initial_sleep=5, max_sleep=15)

    # scraped_json.keys()

    # create a mapping to rename scraped json keys to add back to original json
    key_mapping = {key : "scraped_" + key for key in scraped_json.keys()}

    # Create a new dictionary with the renamed keys
    updated_scraped_json = {key_mapping.get(old_key, old_key): value for old_key, value in scraped_json.items()}

    # add the scraped data to the original json
    s3_json.update(updated_scraped_json)
    
    # name of the output json file
    OUTPUT_S3_OBJECT_NAME = f"stage_{S3_FILE_NAME}"

    print(f"OUTPUT_S3_OBJECT_NAME: {OUTPUT_S3_OBJECT_NAME}")

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