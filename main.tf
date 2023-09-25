terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# cloud provider
provider "aws" {
  region = var.region
  profile = var.profile
}

locals {
  csv_file_path = "data/dish_recipes.csv"
  process_csv_lambda_path = "lambda/process_csv_lambda.zip"
}

# s3 bucket to store csv file
resource "aws_s3_bucket" "dish_recipes_bucket" {
  bucket = "dish-recipes-bucket"
}

# s3 bucket policy data document to allow public access
data "aws_iam_policy_document" "s3_bucket_policy_document" {
  statement {
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.dish_recipes_bucket.arn,
      "${aws_s3_bucket.dish_recipes_bucket.arn}/*",
    ]
  }
}

# s3 bucket policy to allow public access
resource "aws_s3_bucket_policy" "dish_recipes_bucket_policy" {
  bucket = aws_s3_bucket.dish_recipes_bucket.id
  policy = data.aws_iam_policy_document.s3_bucket_policy_document.json
}

# resource "aws_s3_bucket_policy" "dish_recipes_bucket_policy" {
#   bucket = aws_s3_bucket.dish_recipes_bucket.id

#   policy = <<EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Sid": "AllowS3ReadWrite",
#       "Effect": "Allow",
#       "Principal": {
#         "AWS": ["*"]  
#       },
#       "Action": [
#         "s3:GetObject",
#         "s3:PutObject"
#       ],
#       "Resource": "arn:aws:s3:::${aws_s3_bucket.dish_recipes_bucket.bucket}/*"
#     }
#   ]
# }
# EOF
# }

resource "aws_s3_object" "dish_recipes_bucket_object" {
  bucket = aws_s3_bucket.dish_recipes_bucket.bucket
  key    = "dish_recipes.csv"
  source = local.csv_file_path
}

resource "aws_s3_bucket" "process_csv_lambda_code_bucket" {
  bucket = "process-csv-lambda-bucket" 
}

resource "aws_s3_object" "process_csv_lambda_code" {
  bucket = aws_s3_bucket.process_csv_lambda_code_bucket.bucket
  key    = "lambda_function.zip"
  source = local.process_csv_lambda_path
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_policy" "lambda_policy" {
  name = "lambda_policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "dynamodb:PutItem",
      "Resource": "arn:aws:dynamodb:*:*:table/dish_recipes_db"
    },
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::dish-recipes-bucket/*"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_lambda_function" "process_csv_lambda" {
  s3_bucket        = aws_s3_bucket.process_csv_lambda_code_bucket.bucket
  s3_key           = "lambda_function.zip"
  function_name    = "process_csv_lambda"
  handler          = "lambda_handler"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.8"
}

# resource "aws_lambda_event_source_mapping" "s3_event_mapping" {
#   event_source_arn  = aws_s3_bucket.dish_recipes_bucket.arn
#   function_name     = aws_lambda_function.process_csv_lambda.function_name
#   starting_position = "LATEST"
#   batch_size        = 10
# }

resource "aws_s3_bucket_notification" "s3_bucket_notification" {
    bucket = aws_s3_bucket.dish_recipes_bucket.id

    lambda_function {
        lambda_function_arn = aws_lambda_function.process_csv_lambda.arn
        events              = ["s3:ObjectCreated:*"]
        # filter_prefix       = "AWSLogs/"
        filter_suffix       = ".csv"
    }
}

# lambda permissions to allow s3 to invoke lambda
resource "aws_lambda_permission" "lambda_s3_permission" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_csv_lambda.arn
  principal = "s3.amazonaws.com"
  # source_arn = "arn:aws:s3:::dish_recipes_bucket"
  source_arn = aws_s3_bucket.dish_recipes_bucket.arn
}


resource "aws_dynamodb_table" "dish_recipes_ddb_table" {
  name           = "dish_recipes_db"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_lambda_permission" "s3_invoke_lambda_permission" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.process_csv_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.dish_recipes_bucket.arn
}

# resource "aws_lambda_function" "process_csv" {
#   function_name = "process_csv"
#   handler       = "index.handler"
#   runtime       = "nodejs14.x"
#   filename      = "path/to/your/lambda_function.zip"  # Update with the path to your Lambda function code

#   environment {
#     variables = {
#       DYNAMODB_TABLE_NAME = aws_dynamodb_table.example_table.name
#     }
#   }
# }

# resource "aws_dynamodb_table" "example_table" {
#   name           = "example_table"
#   billing_mode   = "PAY_PER_REQUEST"
#   hash_key       = "id"
#   attribute {
#     name = "id"
#     type = "S"
#   }
# }

# resource "aws_lambda_event_source_mapping" "example_trigger" {
#   event_source_arn  = aws_s3_bucket.example_bucket.arn
#   function_name     = aws_lambda_function.process_csv.function_name
#   starting_position = "LATEST"
# }