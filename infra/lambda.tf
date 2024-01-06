###################################################################
#  Lambda function (Triggered by CSV ObjectCreated in S3 bucket) #
###################################################################

resource "aws_lambda_function" "chunk_csv_lambda_function" {
    s3_bucket        = aws_s3_bucket.lambda_s3_bucket.bucket
    s3_key           = var.chunk_csv_lambda_function_zip_file
    s3_object_version = aws_s3_object.chunk_csv_lambda_code_object.version_id
    source_code_hash = var.chunk_csv_lambda_function_zip_file
    function_name    = var.chunk_csv_lambda_function_name
    handler          = "chunk_csv_lambda.chunk_csv_lambda.chunk_csv_lambda"
    role             = aws_iam_role.lambda_role.arn
    runtime          = "python3.11"
    architectures    = ["x86_64"]
    # architectures    = ["arm64"]

    # timeout in seconds
    timeout         = 900

    # Only allow a maximum of 5 Lambdas to be run concurrently
    reserved_concurrent_executions = 5

    # Attach the Lambda function to the CloudWatch Logs group
    environment {
        variables = {
            CW_LOG_GROUP         = aws_cloudwatch_log_group.chunk_csv_lambda_log_group.name,
            SQS_QUEUE_URL        = aws_sqs_queue.sqs_csv_chunk_queue.url
        }
    }
}

##################################################################################################################
# Lambda SQS Event Source Mapping (map CSV chunk lambda to S3 event notification for when a new CSV is uploaded) #
##################################################################################################################

# Allow S3 Event notifications to invoke the Chunk CSV Lambda function
resource "aws_lambda_permission" "allow_s3_invoke" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.chunk_csv_lambda_function.arn}"
  principal = "s3.amazonaws.com"
  source_arn = "${aws_s3_bucket.raw_s3_bucket.arn}"
}

########################################################
# Lambda function (Send JSON recipes to SQS to scrape) #
########################################################

# lambda function consumes chunked CSV SQS queue and iterates over chunk of CSV in S3 and sends each row as a JSON message to the SQS "to scrape" queue
resource "aws_lambda_function" "send_json_lambda_function" {
  s3_bucket        = aws_s3_bucket.lambda_s3_bucket.bucket
  s3_key           = var.send_json_recipes_lambda_function_zip_file
  s3_object_version = aws_s3_object.recipe_scraper_lambda_code_object.version_id
  source_code_hash = var.send_json_recipes_lambda_function_zip_file
  # source_code_hash = filebase64sha256(local.recipe_scraper_lambda_zip)
  # source_code_hash = aws_s3_object.recipe_scraper_lambda_code_object.etag

  function_name    = var.send_json_recipes_lambda_function_name
  handler          = "send_json_recipes_lambda.send_json_recipes_lambda.send_json_recipes_lambda"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.11"
  architectures    = ["x86_64"]
  # architectures    = ["arm64"]

  # timeout in seconds
  timeout         = 900

  # Only allow for a maximum of 8 Lambdas to be run concurrently
  reserved_concurrent_executions = 5
  
  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
        CW_LOG_GROUP         = aws_cloudwatch_log_group.send_json_recipes_lambda_log_group.name,
        CHUNK_SQS_QUEUE_URL     = aws_sqs_queue.sqs_csv_chunk_queue.url,
        OUTPUT_SQS_QUEUE_URL     = aws_sqs_queue.sqs_to_scrape_queue.url,
    }
  }

  depends_on = [
    aws_s3_bucket.lambda_s3_bucket,
    aws_s3_object.send_json_lambda_code_object,
    # aws_s3_bucket_notification.raw_s3_bucket_notification,
    aws_iam_role_policy_attachment.lambda_logs_policy_attachment,
    aws_cloudwatch_log_group.send_json_recipes_lambda_log_group
  ]
  
  tags = {
    name              = local.name_tag
    resource_category = "lambda"
  }
}

#####################################################################################################
# Lambda SQS Event Source Mapping (Allows Chunk CSV SQS Queue to trigger send JSON lambda function) #
#####################################################################################################

# Lambda SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "send_json_lambda_sqs_event_source_mapping" {
  event_source_arn = aws_sqs_queue.sqs_csv_chunk_queue.arn
  function_name    = aws_lambda_function.send_json_lambda_function.function_name
  batch_size       = 1
  depends_on = [
    aws_lambda_function.send_json_lambda_function,
    aws_sqs_queue.sqs_csv_chunk_queue,
  ]
}

# Allow the "CSV chunk" SQS queue to invoke the Send JSON Lambda function
resource "aws_lambda_permission" "allow_sqs_invoke_send_json_lambda" {
  statement_id  = "AllowSQSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.send_json_lambda_function.arn}"
  principal = "sqs.amazonaws.com"
  source_arn = "${aws_sqs_queue.sqs_csv_chunk_queue.arn}"
}

####################################################################################
# Lambda function (Recipe Scraper - Triggered by new recipe messages in SQS queue) #
####################################################################################

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

# # Allow S3 to invoke the Lambda function
# resource "aws_lambda_permission" "allow_s3_invoke" {
#   statement_id  = "AllowS3Invoke"
#   action        = "lambda:InvokeFunction"
#   function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
#   principal = "s3.amazonaws.com"
#   source_arn = "${aws_s3_bucket.raw_s3_bucket.arn}"
# }


######################################################################################
# Lambda SQS Event Source Mapping (map recipe scraper lambda to to_scrape SQS queue) #
######################################################################################

# Lambda SQS Event Source Mapping
resource "aws_lambda_event_source_mapping" "recipe_scraper_lambda_sqs_event_source_mapping" {
  event_source_arn = aws_sqs_queue.sqs_to_scrape_queue.arn
  function_name    = aws_lambda_function.recipe_scraper_lambda_function.function_name
  batch_size       = 2
  function_response_types = ["ReportBatchItemFailures"]
  depends_on = [
    aws_lambda_function.recipe_scraper_lambda_function,
    aws_sqs_queue.sqs_to_scrape_queue,
  ]
}

# Allow the "to scrape" SQS queue to invoke the Recipe Scraper Lambda function
resource "aws_lambda_permission" "allow_sqs_invoke_recipe_scraper_lambda" {
  statement_id  = "AllowSQSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
  principal = "sqs.amazonaws.com"
  source_arn = "${aws_sqs_queue.sqs_to_scrape_queue.arn}"
}

###################################################################
# Lambda function (Extract ingredients Triggered by new scraped messages in SQS queue) #
###################################################################

# lambda function triggered when a JSON file is uploaded to the raw S3 bucket (ObjectCreated)
# Function loads the JSON data and gets more data from the URL in the JSON and
# adds to new found data to the original JSON, then uploads this to the staging bucket
resource "aws_lambda_function" "extract_ingredients_lambda_function" {
  function_name    = var.extract_ingredients_lambda_function_name
  image_uri        = "${data.aws_ecr_repository.lambda_ecr_repository.repository_url}:latest"
  # image_uri        = data.aws_ecr_repository.lambda_ecr_repository.repository_url
  package_type     = "Image"
  architectures    = ["x86_64"]
  # architectures    = ["arm64"]
  # handler          = "extract_ingredients_lambda.extract_ingredients_lambda.extract_ingredients_lambda"

  # timeout in seconds
  timeout         = 300

  # Only allow for a maximum of 50 Lambdas to be run concurrently
  reserved_concurrent_executions = 50
  
  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
        CW_LOG_GROUP         = aws_cloudwatch_log_group.extract_ingredients_lambda_log_group.name,
        OUTPUT_S3_BUCKET     = aws_s3_bucket.output_s3_bucket.bucket,
    }
  }

  depends_on = [
    aws_ecr_repository.lambda_ecr_repository,
    # aws_iam_role_policy_attachment.lambda_logs_policy_attachment,
    aws_cloudwatch_log_group.extract_ingredients_lambda_log_group,
    aws_s3_bucket.output_s3_bucket,
  ]
  
  tags = {
    name              = local.name_tag
    resource_category = "lambda"
  }
}

# # Allow S3 to invoke the Lambda function
# resource "aws_lambda_permission" "allow_s3_invoke" {
#   statement_id  = "AllowS3Invoke"
#   action        = "lambda:InvokeFunction"
#   function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
#   principal = "s3.amazonaws.com"
#   source_arn = "${aws_s3_bucket.raw_s3_bucket.arn}"
# }


######################################################################################
# Lambda SQS Event Source Mapping (map recipe scraper lambda to to_scrape SQS queue) #
######################################################################################

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

# Allow the "to scrape" SQS queue to invoke the Recipe Scraper Lambda function
resource "aws_lambda_permission" "allow_sqs_invoke_recipe_scraper_lambda" {
  statement_id  = "AllowSQSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.recipe_scraper_lambda_function.arn}"
  principal = "sqs.amazonaws.com"
  source_arn = "${aws_sqs_queue.sqs_to_scrape_queue.arn}"
}