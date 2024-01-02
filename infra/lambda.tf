###################################################################
#  Lambda function (Triggered by JSON ObjectCreated in S3 bucket) #
###################################################################

# lambda function triggered when a JSON file is uploaded to the raw S3 bucket (ObjectCreated)
# Function loads the JSON data and gets more data from the URL in the JSON and
# adds to new found data to the original JSON, then uploads this to the staging bucket
resource "aws_lambda_function" "recipe_scraper_lambda_function" {
  s3_bucket        = aws_s3_bucket.lambda_s3_bucket.bucket
  s3_key           = var.scraper_lambda_function_zip_file
  s3_object_version = aws_s3_object.recipe_scraper_lambda_code_object.version_id
  source_code_hash = var.scraper_lambda_function_zip_file
  # source_code_hash = filebase64sha256(local.recipe_scraper_lambda_zip)
  # source_code_hash = aws_s3_object.recipe_scraper_lambda_code_object.etag

  function_name    = var.scraper_lambda_function_name
  handler          = "recipe_scraper_lambda.recipe_scraper_lambda.recipe_scraper_lambda"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.11"
  architectures    = ["x86_64"]
  # architectures    = ["arm64"]

  # timeout in seconds
  timeout         = 500

  # Only allow for a maximum of 8 Lambdas to be run concurrently
  reserved_concurrent_executions = 8
  
  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
        CW_LOG_GROUP         = aws_cloudwatch_log_group.raw_recipes_lambda_log_group.name,
        S3_BUCKET            = aws_s3_bucket.raw_s3_bucket.bucket,
        OUTPUT_S3_BUCKET     = aws_s3_bucket.stage_s3_bucket.bucket,
        SCRAPE_OPS_API_KEY   = var.scrape_ops_api_key,
        DYNAMODB_TABLE       = aws_dynamodb_table.recipe_scraper_table.name,
        BRIGHT_DATA_USERNAME = var.bright_data_username,
        BRIGHT_DATA_PASSWORD = var.bright_data_password,
        BRIGHT_DATA_HOST     = var.bright_data_host,
        BRIGHT_DATA_PORT     = var.bright_data_port,
    }
  }

  depends_on = [
    aws_s3_bucket.lambda_s3_bucket,
    aws_s3_object.recipe_scraper_lambda_code_object,
    # aws_s3_bucket_notification.raw_s3_bucket_notification,
    aws_iam_role_policy_attachment.lambda_logs_policy_attachment,
    aws_cloudwatch_log_group.raw_recipes_lambda_log_group,
    aws_s3_bucket.stage_s3_bucket,
  ]
  
  tags = {
    name              = local.name_tag
    resource_category = "lambda"
  }
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
  principal = "s3.amazonaws.com"
  source_arn = "${aws_s3_bucket.raw_s3_bucket.arn}"
}


################################################
# Lambda (sqs_consumer) SQS Event Source Mapping
################################################

# Lambda SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "sqs_consumer_lambda_event_source_mapping" {
  event_source_arn = aws_sqs_queue.sqs_to_scrape_queue.arn
  function_name    = aws_lambda_function.recipe_scraper_lambda_function.function_name
  batch_size       = 2
  function_response_types = ["ReportBatchItemFailures"]
  depends_on = [
    aws_lambda_function.recipe_scraper_lambda_function,
    aws_sqs_queue.sqs_to_scrape_queue,
  ]
}

# Allow S3 to invoke the Lambda function
resource "aws_lambda_permission" "allow_sqs_invoke" {
  statement_id  = "AllowSQSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
  principal = "sqs.amazonaws.com"
  source_arn = "${aws_sqs_queue.sqs_to_scrape_queue.arn}"
}