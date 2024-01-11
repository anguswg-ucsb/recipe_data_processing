#####################################
# Lambda Role (primary lambda role) #
#####################################

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

##########################################################################################
# Lambda Role (lambda_role) Attach AWSLambdaBasicExecutionRole Policy (AWS managed role) #
##########################################################################################

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
data "aws_iam_policy_document" "lambda_s3_and_sqs_policy_doc" {
  statement {
    sid = "RecipesS3AndSQSPermissionsForLambda"
    
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

    statement {
    sid = "SQSReadDeletePermissions"
    
    effect = "Allow"

    actions = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
    ]

    resources = [
      aws_sqs_queue.sqs_to_scrape_queue.arn,
      aws_sqs_queue.sqs_csv_chunk_queue.arn,
      aws_sqs_queue.sqs_process_staged_queue.arn,
      ]
  }

}

# Make an IAM policy from the IAM policy document for S3/SQS permissions for sqs_consumer lambda
resource "aws_iam_policy" "lambda_s3_policy" {
  name_prefix = "recipe-lambdas-s3-and-sqs-policy"
  description = "IAM Policy for Recipes Lambda to interact with S3 and SQS"
  policy      = data.aws_iam_policy_document.lambda_s3_and_sqs_policy_doc.json
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

###############################################################
# Lambda Logging Policy 
# - Allow Lambda to send logs to CloudWatch Logs #
###############################################################

resource "aws_iam_policy" "logging_policy" {
  name_prefix   = "recipe-lambdas-logging-policy"
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

##############################
# DynamoDB Table permissions #
##############################

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

# ###################################################
# # Lambda (sqs_consumer) IAM Policy for S3/SQS queue
# ###################################################

# data "aws_iam_policy_document" "sqs_consumer_lambda_policy_doc" {

#   statement {
#     sid = "SQSReadDeletePermissions"
    
#     effect = "Allow"

#     actions = [
#           "sqs:ReceiveMessage",
#           "sqs:DeleteMessage",
#           "sqs:GetQueueAttributes",
#     ]

#     resources = [
#       aws_sqs_queue.sqs_to_scrape_queue.arn
#       ]
#   }
# }

# # Make an IAM policy from the IAM policy document for S3/SQS permissions for sqs_consumer lambda
# resource "aws_iam_policy" "sqs_consumer_lambda_policy" {
#   name        = "recipe-sqs-consumer-lambda-policy"
#   description = "Recipe scraper policy for sqs consumer Lambda to interact with S3 and SQS queue"
#   policy      = data.aws_iam_policy_document.sqs_consumer_lambda_policy_doc.json
#   tags = {
#     name              = local.name_tag
#     resource_category = "iam"
#   }
# }

# # Attach the lambda to SQS IAM policy to the lambda role
# resource "aws_iam_role_policy_attachment" "sqs_consumer_lambda_policy_attachment" {
#   role       = aws_iam_role.lambda_role.name
#   policy_arn = aws_iam_policy.sqs_consumer_lambda_policy.arn
#   # policy_arn = data.aws_iam_policy_document.sqs_consumer_lambda_policy.json
# }

# ######################################################################
# # Lambda (AWSLambdaBasicExecutionRole - AWS managed role) IAM Policy #
# ######################################################################

# # Attach necessary policies to the IAM role
# resource "aws_iam_role_policy_attachment" "lambda_basic_exec_policy_attachment" {
#   role       = aws_iam_role.lambda_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
# }