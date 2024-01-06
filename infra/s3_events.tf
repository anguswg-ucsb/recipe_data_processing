# # Create S3 event notification to send messages to SQS queue when a JSON file is uploaded to the raw S3 bucket
# resource "aws_s3_bucket_notification" "raw_s3_bucket_notification" {
#   bucket = aws_s3_bucket.raw_s3_bucket.id

#   queue {
#     queue_arn     = aws_sqs_queue.sqs_to_scrape_queue.arn
#     events        = ["s3:ObjectCreated:*"]
#     filter_suffix = ".csv"
#   }
# }

# S3 event notification for raw data bucket to trigger lambda function
resource "aws_s3_bucket_notification" "raw_s3_bucket_notification" {
  bucket = aws_s3_bucket.raw_s3_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.chunk_csv_lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = "raw/"
    filter_suffix       = ".csv"
  }
}

# # Create S3 event notification to send messages to SQS queue when a JSON file is uploaded to the raw S3 bucket
# resource "aws_s3_bucket_notification" "raw_s3_bucket_notification" {
#   bucket = aws_s3_bucket.raw_s3_bucket.id

#   queue {
#     queue_arn     = aws_sqs_queue.sqs_to_scrape_queue.arn
#     events        = ["s3:ObjectCreated:*"]
#     filter_suffix = ".json"
#   }
# }

# Create S3 event notification to send messages to SQS queue 
# when a JSON file is uploaded to the STAGE S3 bucket (scraped data)
resource "aws_s3_bucket_notification" "stage_s3_bucket_notification" {
  bucket = aws_s3_bucket.stage_s3_bucket.id

  queue {
    queue_arn     = aws_sqs_queue.sqs_process_staged_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_suffix = ".json"
  }
}