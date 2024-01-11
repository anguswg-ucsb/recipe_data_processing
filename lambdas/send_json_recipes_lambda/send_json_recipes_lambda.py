# Description: 
    # Python script for an AWS Lambda function that gets triggered by an S3 Event notification when 
    # a CSV file is uploaded to an S3 bucket. Row numbers for splitting the CSV into smaller groupings are 
    # then found and a reference to the original CSV and an offset row number are sent to an SQS queue.
# Usage: python chunk_csv_lambda.py
# Author: Angus Watters

# general utility libraries
import os
import json
# from datetime import datetime
# import random
# import time
# import uuid
# from decimal import Decimal

# AWS SDK for Python (Boto3) and S3fs for S3 file system support
import boto3
import pandas as pd
import s3fs

# Environment variables

# SQS queue URL to send messages to
CHUNK_SQS_QUEUE_URL = os.environ.get('CHUNK_SQS_QUEUE_URL')

OUTPUT_SQS_QUEUE_URL = os.environ.get('OUTPUT_SQS_QUEUE_URL')

# S3 client
s3 = boto3.client('s3')

# SQS client
sqs = boto3.client('sqs')

def process_csv_chunk_message(message):

    print(f"=====================")
    print(f"---->\n Value of message: {message}")
    print(f"=====================")
    print(f"value of type(message): {type(message)}")

        # Get the SQS event message ID
    message_id   = message["messageId"]

    # Get the SQS event message body
    message_body = message["body"]

    print(f'---->\n Value of message_id: {message_id}')
    print(f'---->\n Value of message_body: {message_body}')
    print(f'---->\n Value of type(message_body): {type(message_body)}')

    print(f"Converting message_body to python dict via json.loads()...")

    message_body = json.loads(message_body)

    print(f'---->\n Value of message_body: {message_body}')
    print(f'---->\n Value of type(message_body): {type(message_body)}')

    # Extract the S3 bucket and the filename from the SQS message
    S3_BUCKET    = message_body["s3_bucket"]
    S3_FILE_NAME = message_body["s3_file_path"]

    print(f"- S3_BUCKET: {S3_BUCKET}")
    print(f"- S3_FILE_NAME: {S3_FILE_NAME}")

    # get the object from S3
    s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)

    chunk_csv = pd.read_csv(s3_obj['Body'], skiprows=message_body["start_index"], nrows=message_body["nrows"], header = None, names = ["uid", "url"])
    # chunked_list.append(chunk_csv)

    # Iterate over rows, convert each row to a dictionary, and save as JSON
    for index, row in chunk_csv.iterrows():
        print(f"Processing row {index}...")

        # Convert the row to a dictionary
        row_dict = row.to_dict()

        unique_id = row_dict["uid"]
        url = row_dict["url"]

        print(f"unique_id: {unique_id}")
        print(f"url: {url}")

        json_message = json.dumps(row_dict)

        print(f"json_message: {json_message}")

        # Send message to SQS queue
        sqs_response = sqs.send_message(
            QueueUrl=OUTPUT_SQS_QUEUE_URL,
            MessageBody=json_message
        )

        print(f"SQS response: {sqs_response}")
        # print(f"===" * 5)
    
    # # # Extract the S3 bucket and the filename from the S3 event notification JSON object
    # S3_BUCKET    = event['Records'][0]['s3']['bucket']['name']
    # S3_FILE_NAME = event['Records'][0]['s3']['object']['key']
    return {'status': 'True',
            'statusCode': 200,
            'body': 'Successfully sent JSON recipes to SQS queue!'}


# lambda handler function
def send_json_recipes_lambda(event, context):

    print(f"=====================")
    print(f'---->\n Value of event: {event}')
    print(f"=====================")

    message_count = 0
    
    batch_item_failures = []
    sqs_batch_response = {}

    for message in event['Records']:

        message_count += 1
        print(f"PROCESSING MESSAGE: {message_count}")
        # print(f"PROCESSING MESSAGE: {message_count} / {len(event['Records'])}")
        try:
            process_csv_chunk_message(message)
        except Exception as e:
            print(f"Exception raised from messageId {message['messageId']}\n: {e}")
            batch_item_failures.append({"itemIdentifier": message['messageId']})
        
    sqs_batch_response["batchItemFailures"] = batch_item_failures

    print(f"sqs_batch_response: {sqs_batch_response}")

    return sqs_batch_response

# # lambda handler function
# def send_json_recipes_lambda(event, context):

#     # Get the SQS message from the event 
#     message = event['Records'][0]["body"]

#     print(f"=====================")
#     print(f'---->\n Value of event: {event}')
#     print(f"=====================")

#     print(f"=====================")
#     print(f'---->\n Value of message: {message}')
#     print(f"=====================")

#     # Extract the S3 bucket and the filename from the SQS message
#     S3_BUCKET = message["s3_bucket"]
#     S3_FILE_NAME = message["s3_file_path"]


#     print(f"- S3_BUCKET: {S3_BUCKET}")
#     print(f"- S3_FILE_NAME: {S3_FILE_NAME}")
    
#     # get the object from S3
#     s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)

#     chunk_csv = pd.read_csv(s3_obj['Body'], skiprows=message["start_index"], nrows=message["nrows"], header = None, names = ["uid", "url"])
#     # chunked_list.append(chunk_csv)

#     # Iterate over rows, convert each row to a dictionary, and save as JSON
#     for index, row in chunk_csv.iterrows():
#         print(f"Processing row {index}...")

#         # Convert the row to a dictionary
#         row_dict = row.to_dict()

#         unique_id = row_dict["uid"]
#         url = row_dict["url"]

#         print(f"unique_id: {unique_id}")
#         print(f"url: {url}")
#         json_message = json.dumps(row_dict)

#         print(f"json_message: {json_message}")
#         # Send message to SQS queue
#         sqs_response = sqs.send_message(
#             QueueUrl=OUTPUT_SQS_QUEUE_URL,
#             MessageBody=json_message
#         )

#         print(f"SQS response: {sqs_response}")
#         # print(f"===" * 5)
    
#     # # # Extract the S3 bucket and the filename from the S3 event notification JSON object
#     # S3_BUCKET    = event['Records'][0]['s3']['bucket']['name']
#     # S3_FILE_NAME = event['Records'][0]['s3']['object']['key']
#     return {'status': 'True',
#             'statusCode': 200,
#             'body': 'Successfully sent JSON recipes to SQS queue!'}