terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  profile = var.aws_profile
}

#################
# Local variables
#################

# paths to Lambda zip files and tag variables

locals {
    s3_recipe_scraper_lambda_zip = "../deploy/s3_recipe_scraper.zip"
    name_tag = "recipe-scraper"
}

#######################################
# S3 bucket for raw recipes JSON data #
#######################################

# s3 bucket for raw data
resource "aws_s3_bucket" "raw_s3_bucket" {
  bucket = var.raw_s3_bucket_name
}

###############################
# S3 bucket permissions (RAW) #
###############################

# Enable object versioning on RAW S3 bucket
resource "aws_s3_bucket_versioning" "raw_s3_bucket_versioning" {
  bucket = aws_s3_bucket.raw_s3_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# s3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "raw_s3_bucket_ownership_controls" {
  bucket = aws_s3_bucket.raw_s3_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# s3 bucket public access block
resource "aws_s3_bucket_public_access_block" "raw_s3_public_access_block" {
  bucket = aws_s3_bucket.raw_s3_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

}

resource "aws_s3_bucket_acl" "raw_s3_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.raw_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.raw_s3_public_access_block,
  ]

  bucket = aws_s3_bucket.raw_s3_bucket.id
  acl    = "private"
}

data "aws_iam_policy_document" "s3_bucket_policy_document" {
  statement {
    sid = "AllowCurrentAccount"
    effect = "Allow"

    principals {
      type = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.raw_s3_bucket.arn,
      "${aws_s3_bucket.raw_s3_bucket.arn}/*"
    ]

    condition {
      test = "StringEquals"
      variable = "aws:PrincipalAccount"
      values = [var.aws_account_number]
    }
  }
}

# s3 bucket policy to allow public access
resource "aws_s3_bucket_policy" "raw_bucket_policy" {
  bucket = aws_s3_bucket.raw_s3_bucket.id
  policy = data.aws_iam_policy_document.s3_bucket_policy_document.json
  depends_on = [
    aws_s3_bucket_acl.raw_s3_bucket_acl,
    aws_s3_bucket_ownership_controls.raw_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.raw_s3_public_access_block,
  ]
}


# S3 event notification for raw data bucket to trigger lambda function
resource "aws_s3_bucket_notification" "raw_s3_bucket_notification" {
  bucket = aws_s3_bucket.raw_s3_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.s3_recipe_scraper_lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    # filter_prefix       = "raw/"
    filter_suffix       = ".json"
  }
}

#####################
# S3 bucket (STAGE) #
#####################

# s3 bucket for raw data
resource "aws_s3_bucket" "stage_s3_bucket" {
  bucket = var.stage_s3_bucket_name
}

#################################
# S3 bucket permissions (STAGE) #
#################################

# Enable object versioning on STAGE S3 bucket
resource "aws_s3_bucket_versioning" "stage_s3_bucket_versioning" {
  bucket = aws_s3_bucket.stage_s3_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# s3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "stage_s3_bucket_ownership_controls" {
  bucket = aws_s3_bucket.stage_s3_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# s3 bucket public access block
resource "aws_s3_bucket_public_access_block" "stage_s3_public_access_block" {
  bucket = aws_s3_bucket.stage_s3_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_acl" "stage_s3_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.stage_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.stage_s3_public_access_block,
  ]

  bucket = aws_s3_bucket.stage_s3_bucket.id
  acl    = "private"
}

data "aws_iam_policy_document" "stage_s3_bucket_policy_document" {
  statement {
    sid = "AllowCurrentAccount"
    effect = "Allow"

    principals {
      type = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.stage_s3_bucket.arn,
      "${aws_s3_bucket.stage_s3_bucket.arn}/*"
    ]

    condition {
      test = "StringEquals"
      variable = "aws:PrincipalAccount"
      values = [var.aws_account_number]
    }
  }
}

# s3 bucket policy to allow public access
resource "aws_s3_bucket_policy" "stage_bucket_policy" {
  bucket = aws_s3_bucket.stage_s3_bucket.id
  policy = data.aws_iam_policy_document.stage_s3_bucket_policy_document.json
  depends_on = [
    aws_s3_bucket_acl.stage_s3_bucket_acl,
    aws_s3_bucket_ownership_controls.stage_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.stage_s3_public_access_block,
  ]
}

###############################
# S3 bucket for lambda function code #
###############################

# s3 bucket for lambda code
resource "aws_s3_bucket" "lambda_s3_bucket" {
  bucket = var.lambda_s3_bucket_name
}

# s3 object for lambda code process_staging function
resource "aws_s3_object" "recipe_scraper_lambda_code_object" {
  bucket = aws_s3_bucket.lambda_s3_bucket.bucket
  key    = var.s3_recipe_scraper_lambda_zip_filename
  source = local.s3_recipe_scraper_lambda_zip
  etag   = filemd5(local.s3_recipe_scraper_lambda_zip)
}

##################################
# Lambda Role (mros_lambda_role) #
##################################

# IAM policy document allowing Lambda to AssumeRole
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Create an IAM role for the lambda to assume role
resource "aws_iam_role" "lambda_role" {
  name_prefix         = "recipes_lambda_role"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_role.json
  tags = {
    name              = local.name_tag
    resource_category = "iam"
  }
}

############################################################################
# Lambda Role (mros_lambda_role) Attach AWSLambdaBasicExecutionRole Policy #
############################################################################

# Attach necessary policies to the IAM role
resource "aws_iam_role_policy_attachment" "lambda_role_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  # policy_arn = aws_iam_policy.lambda_policy.arn
}

###############################################################
# Lambda Role (mros_lambda_role) Attach S3 permissions Policy #
###############################################################

# Inline policy for S3 permissions using jsonencode
data "aws_iam_policy_document" "lambda_s3_policy_doc" {
  statement {
    sid = "RecipesS3PermissionsForLambda"
    
    effect = "Allow"

    actions = [
          "s3:GetObject", 
          "s3:PutObject",
          "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.raw_s3_bucket.arn,
      "${aws_s3_bucket.raw_s3_bucket.arn}/*",
      aws_s3_bucket.stage_s3_bucket.arn,
      "${aws_s3_bucket.stage_s3_bucket.arn}/*",
    ]
  }


}

# Make an IAM policy from the IAM policy document for S3/SQS permissions for sqs_consumer lambda
resource "aws_iam_policy" "lambda_s3_policy" {
  name_prefix = "recipes-lambda-s3-policy"
  description = "IAM Policy for Recipes Lambda to interact with S3"
  policy      = data.aws_iam_policy_document.lambda_s3_policy_doc.json
  tags = {
    name              = local.name_tag
    resource_category = "iam"
  }
}

# Attach the inline S3 policy to the IAM role
resource "aws_iam_role_policy_attachment" "lambda_s3_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

######################################
# Lambda Log Group (recipe scraper lambda) #
######################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "raw_recipes_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.raw_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}


###############################################################
# Lambda Logging Policy 
# - Allow Lambda to send logs to CloudWatch Logs #
###############################################################

resource "aws_iam_policy" "logging_policy" {
  name_prefix   = "s3-recipe-scraper-logging-policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        Action : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect : "Allow",
        Resource : "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach the lambda logging IAM policy to the Python lambda roles
resource "aws_iam_role_policy_attachment" "lambda_logs_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.logging_policy.arn
}

###################################################################
#  Lambda function (Triggered by JSON ObjectCreated in S3 bucket) #
###################################################################

# lambda function triggered when a JSON file is uploaded to the raw S3 bucket (ObjectCreated)
# Function loads the JSON data and gets more data from the URL in the JSON and
# adds to new found data to the original JSON, then uploads this to the staging bucket
resource "aws_lambda_function" "s3_recipe_scraper_lambda_function" {
  s3_bucket        = aws_s3_bucket.lambda_s3_bucket.bucket
  s3_key           = var.raw_lambda_function_zip_file
  s3_object_version = aws_s3_object.recipe_scraper_lambda_code_object.version_id
  source_code_hash = var.raw_lambda_function_zip_file
  # source_code_hash = filebase64sha256(local.s3_recipe_scraper_lambda_zip)
  # source_code_hash = aws_s3_object.recipe_scraper_lambda_code_object.etag

  function_name    = var.raw_lambda_function_name
  handler          = "s3_recipe_scraper.s3_recipe_scraper.s3_recipe_scraper"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.11"
  architectures    = ["x86_64"]
  # architectures    = ["arm64"]

  # timeout in seconds
  timeout         = 450

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
  function_name = "${aws_lambda_function.s3_recipe_scraper_lambda_function.arn}"
  principal = "s3.amazonaws.com"
  source_arn = "${aws_s3_bucket.raw_s3_bucket.arn}"
}

#################################################################
# DynamoDB Table for logging/redriving failed lambda executions #
#################################################################

# Add DynamoDB table for logging failed lambda executions
resource "aws_dynamodb_table" "recipe_scraper_table" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "uid"
  range_key      = "timestamp"

  attribute {
    name = "uid"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  tags = {
    name              = local.name_tag
    resource_category = "dynamodb"
  }
}

# Policy docuemnet for DynamoDB permissions 
data "aws_iam_policy_document" "lambda_dynamodb_policy_doc" {
  statement {
    sid = "LambdaDynamoDBPermissions"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]

    resources = [
      aws_dynamodb_table.recipe_scraper_table.arn,
      "${aws_dynamodb_table.recipe_scraper_table.arn}/*"
    ]
  }
}

# Make an IAM policy from the IAM policy document for DynamoDB permissions
resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name_prefix = "recipes-lambda-dynamodb-policy"
  description = "IAM Policy for Recipes Lambda to interact with DynamoDB"
  policy      = data.aws_iam_policy_document.lambda_dynamodb_policy_doc.json
  tags = {
    name              = local.name_tag
    resource_category = "iam"
  }
}

# Attach the inline DynamoDB policy to the IAM role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}
