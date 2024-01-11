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
SQS_QUEUE_URL = os.environ.get('SQS_QUEUE_URL')

# S3 client
s3 = boto3.client('s3')

# SQS client
sqs = boto3.client('sqs')

# lambda handler function
def chunk_csv_lambda(event, context):

    print(f"=====================")
    print(f'---->\n Value of event: {event}')
    print(f"=====================")

    # # Extract the S3 bucket and the filename from the S3 event notification JSON object
    S3_BUCKET    = event['Records'][0]['s3']['bucket']['name']
    S3_FILE_NAME = event['Records'][0]['s3']['object']['key']

    print(f"- S3_BUCKET: {S3_BUCKET}")
    print(f"- S3_FILE_NAME: {S3_FILE_NAME}")

    # s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)
    # url_s3_df = pd.read_csv(s3_obj['Body'])

    s3_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)

    # Read CSV in chunks of 2 rows
    chunk_size = 4

    # Chunk iterator
    chunks     = pd.read_csv(s3_obj['Body'], chunksize=chunk_size)

    # Iterate through chunks and send messages to SQS
    for i, chunk in enumerate(chunks):

        print(f"Chunk {i + 1}")

        # start of chunk index
        start_index = (i * chunk_size) + 1
        # start_index = 1 if i == 0 else i * chunk_size
        # stop_index = start_index + chunk_size - 1 if i < len(chunk) - 1 else chunk.index[-1]
        # test_nrows = chunk_size if i < len(chunk) - 1 else chunk.index[-1] - start_index + 1

        # Create a message with start and stop indices
        message = {
            "start_index": start_index,
            "nrows": chunk_size,
            "s3_bucket": S3_BUCKET,
            "s3_file_path": S3_FILE_NAME
        }

        # s3_chunk_obj = s3.get_object(Bucket=S3_BUCKET, Key=S3_FILE_NAME)
        # chunk_csv = pd.read_csv(s3_chunk_obj['Body'], skiprows=start_index, nrows=chunk_size, header = None, names = ["uid", "url"])
        # chunked_list.append(chunk_csv)

        # print(f"message: {message}")
        print(f"json.dumps(message): {json.dumps(message)}")

        # # Send the message to SQS
        response = sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message)
        )

        print(f"message sent to SQS: {response}")
        print(f"SQS message MessageId: {response['MessageId']}")

        # print(f"=====" * 5)
    
    return "Successfully sent CSV chunk message to SQS queue!"


# chunked_list
# [len(i) for i in chunked_list]

# chunked_list[0]
# chunked_list[1]
# chunked_list[2]
# chunked_list[3]

# url_s3_df


# flatten_df = pd.concat(chunked_list)
# flatten_df
# flatten_df.duplicated()
# flatten_df.columns
# len(flatten_df)

