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
  # airtable_lambda_zip = "../deploy/lambda_function.zip"
    airtable_to_sqs_zip = "../deploy/airtable_to_sqs.zip"
    stage_s3_to_prod_s3_zip = "../deploy/stage_s3_to_prod_s3.zip"
    name_tag = "mros"
}

###############################
# S3 bucket for airtable data #
###############################

# s3 bucket for raw data
resource "aws_s3_bucket" "raw_s3_bucket" {
  bucket = var.raw_s3_bucket_name
}

#######################################
# S3 bucket permissions airtable data #
#######################################

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

###############################
# S3 bucket for lambda function code #
###############################

# s3 bucket for lambda code
resource "aws_s3_bucket" "lambda_s3_bucket" {
  bucket = var.lambda_s3_bucket_name
}

###############################
#  Lambda function #
###############################

# lambda function to react to s3 event and augment data
resource "aws_lambda_function" "airtable_to_sqs_lambda" {
  filename      = local.airtable_to_sqs_zip
  function_name = "airtable_to_sqs_lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  memory_size   = 128
  timeout       = 300
  source_code_hash = filebase64sha256(local.airtable_to_sqs_zip)
  depends_on = [
    aws_s3_bucket_notification.raw_s3_bucket_notification,
    aws_s3_bucket.lambda_s3_bucket,
  ]
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
# Lambda Log Group (airtable_to_sqs) #
######################################

# Cloudwatch log group for 'airtable_to_sqs' Python lambda function
resource "aws_cloudwatch_log_group" "raw_recipes_lambda_log_group" {
  # name              = "/aws/lambda/${var.airtable_to_sqs_lambda_function_name}"
  name_prefix              = "/aws/lambda/${var.raw_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}


###############################################################
# Lambda Logging Policy (mros-airtable-processor-logging-policy) 
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

####################################
# Lambda Function (Airtable to S3) #
####################################

# lambda function to process csv file
resource "aws_lambda_function" "s3_recipe_scraper_lambda_function" {
  s3_bucket        = aws_s3_bucket.lambda_bucket.bucket
  s3_key           = var.raw_lambda_function_zip_file
  function_name    = var.raw_lambda_function_name
  handler          = "s3_recipe_scraper.s3_recipe_scraper.s3_recipe_scraper"
  # handler          = "function.name/handler.process_csv_lambda"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.11"
  architectures    = ["x86_64"]
  # architectures    = ["arm64"]

  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
        CW_LOG_GROUP = aws_cloudwatch_log_group.raw_recipes_lambda_log_group.name,
        S3_BUCKET = "s3://${aws_s3_bucket.raw_s3_bucket.bucket}",
    }
  }

  # timeout in seconds
  timeout         = 300
  
  depends_on = [
    aws_s3_bucket.lambda_bucket,
    aws_s3_object.airtable_lambda_code_object,
    aws_iam_role_policy_attachment.lambda_logs_policy_attachment,
    aws_cloudwatch_log_group.raw_recipes_lambda_log_group,
  ]
  
  tags = {
    name              = local.name_tag
    resource_category = "lambda"
  }
}