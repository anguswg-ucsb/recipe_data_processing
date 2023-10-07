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
  csv_file_path = "data/dish_recipes2.csv"
  process_csv_lambda_path = "lambda/process_csv_lambda.zip"
  s3_to_aurora_lambda_path = "lambda/s3_to_aurora.zip"
  create_user_lambda_path = "lambda/create_user.zip"
  psychopg2_zip_path ="lambda/psycopg2-py38.zip"
}

data "aws_vpc" "main_vpc" {
  id = var.vpc_id
  # id = "vpc-06a9576a46a4e4979"
}
#################
# SECURITY GROUPS
#################

resource "aws_security_group" "lambda_sg" {
    name = "lambda-sg"
    vpc_id      = data.aws_vpc.main_vpc.id

    ingress {
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }


}

# data "http" "env_ip" {
#   url = "https://ipv4.icanhazip.com"
# }
# data "http" "my_public_ip" {
#   url = "https://ifconfig.co/json"
#   request_headers = {
#     Accept = "application/json"
#   }
# }

resource "aws_security_group" "aurora_sg" {
    name = "aurora-sg"
    vpc_id      = data.aws_vpc.main_vpc.id

    ingress {
        from_port = 5432
        to_port = 5432
        protocol = "tcp"
        security_groups = [aws_security_group.lambda_sg.id]
    }

    ingress {
      from_port = 5432
      to_port = 5432
      protocol = "tcp"
      cidr_blocks = ["${var.env_ip}/32"]
    }

    ingress {
      from_port = 443
      to_port = 443
      protocol = "tcp"
      cidr_blocks = ["${var.env_ip}/32"]
    }

    ingress {
      from_port = 22
      to_port = 22
      protocol = "tcp"
      cidr_blocks = ["${var.env_ip}/32"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

}

resource "aws_security_group" "sg_lambda" {
  name = "sg-lambda"
  vpc_id      = data.aws_vpc.main_vpc.id

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "sg_rds_proxy" {
  vpc_id      = data.aws_vpc.main_vpc.id

  ingress {
    description      = "POSTGRES TLS from sg_lambda"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.sg_lambda.id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "sg_rds" {
  vpc_id      = data.aws_vpc.main_vpc.id

  ingress {
    description      = "POSTGRES TLS from sg_rds_proxy"
    from_port        = 5432
    to_port          = 5432
    protocol         = "tcp"
    security_groups  = [aws_security_group.sg_rds_proxy.id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

###############################
# AWS SECRETS MANAGERS CONFIG #
###############################


resource "aws_secretsmanager_secret" "database_credentials" {
  name = var.secrets_manager_credentials_name
}

resource "aws_secretsmanager_secret_version" "database_credentials_version" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = var.db_username,
    password = var.db_password
  })
}

resource "aws_iam_policy" "secrets_manager_policy" {
  name        = "secrets-manager-policy"
  path        = "/"
  description = "Allows access to the Secrets Manager"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Action    = [
          "secretsmanager:GetSecretValue",
        ],
        Resource = aws_secretsmanager_secret.database_credentials.arn,
      },
    ],
  })
}

resource "aws_iam_role" "secrets_manager_role" {
  name               = "secrets-manager-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Principal = { Service = "lambda.amazonaws.com" },
        Action    = "sts:AssumeRole",
      },
    ],
  })

  # policy = aws_iam_policy.secrets_manager_policy.policy
}

resource "aws_iam_role_policy_attachment" "secrets_manager_role_policy_attachment" {
  role       = aws_iam_role.secrets_manager_role.name
  policy_arn = aws_iam_policy.secrets_manager_policy.arn
}

###############################
# AWS Aurora cluster #
###############################

resource "aws_rds_cluster" "aurora_dish_recipes_cluster" {
  cluster_identifier      = "aurora-cluster-dish-recipes"
  engine                  = "aurora-postgresql"  
  engine_mode             = "provisioned"  
  engine_version          = "15.3"
  database_name           = var.db_name  
  # master_username         = var.db_username
  # master_password         = var.db_password
  master_username         = jsondecode(aws_secretsmanager_secret_version.database_credentials_version.secret_string)["username"]
  master_password         = jsondecode(aws_secretsmanager_secret_version.database_credentials_version.secret_string)["password"]

  serverlessv2_scaling_configuration {
    # auto_pause   = true
    max_capacity = 1.0
    min_capacity = 0.5
  }
  skip_final_snapshot     = true

  # iam_database_authentication_enabled = true
  # iam_roles = [aws_iam_role.aurora_rds_role.arn]
  vpc_security_group_ids = [aws_security_group.aurora_sg.id]
}

resource "aws_rds_cluster_role_association" "aurora_dish_recipes_role_association" {
  db_cluster_identifier = aws_rds_cluster.aurora_dish_recipes_cluster.id
  feature_name          = "s3Import"
  role_arn              = aws_iam_role.aurora_rds_role.arn  
}

resource "aws_rds_cluster_instance" "aurora_dish_recipes_instance" {
  cluster_identifier = aws_rds_cluster.aurora_dish_recipes_cluster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora_dish_recipes_cluster.engine
  engine_version     = aws_rds_cluster.aurora_dish_recipes_cluster.engine_version
  apply_immediately  = true
  publicly_accessible     = true
}

#####################
# Aurora Cluster Role
#####################

resource "aws_iam_role" "aurora_rds_role" {
  name               = "aurora-rds-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow"
        Sid = ""
        Principal = { 
          Service = "rds.amazonaws.com" 
          }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceArn": aws_rds_cluster.aurora_dish_recipes_cluster.arn,
          }
      },
      },
    ],
  })
}

resource "aws_iam_policy" "aurora_rds_policy" {
  name        = "aurora-rds-policy"
  description = "Allows RDS to invoke lambda"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect    = "Allow",
        Action    = [
          "lambda:InvokeFunction",
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "s3:GetBucketACL",
          "s3:GetBucketLocation",
          "s3:ListMultipartUploadParts",
          "s3:AbortMultipartUpload",
          "s3:ListAllMyBuckets",
          "rds:DescribeDBClusters",
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusterEndpoints",
          "rds:DescribeDBClusterParameterGroups",
          "rds:DescribeDBClusterParameters",
          "rds:DescribeDBClusterSnapshots",
          "rds:DescribeDBSubnetGroups",
          "rds:DescribeEventSubscriptions",
          "rds:DescribeEvents",
          "rds:DescribeOrderableDBInstanceOptions",
          "rds:DescribePendingMaintenanceActions",
          "rds:DescribeReservedDBInstances",
          "rds:DescribeReservedDBInstancesOfferings",
          "rds:ListTagsForResource",
          "rds:ViewBilling",
        ],
        Resource = "*",
      },
    ],
  })
}

resource "aws_iam_role_policy_attachment" "aurora_rds_role_policy_attachment" {
  role       = aws_iam_role.aurora_rds_role.name
  policy_arn = aws_iam_policy.aurora_rds_policy.arn
}

###############################
# AWS Lambda #
###############################

# s3 bucket for lambda code
resource "aws_s3_bucket" "s3_to_aurora_lambda_bucket" {
  bucket = "s3-to-aurora-lambda-bucket" 
}

# s3 object for lambda code
resource "aws_s3_object" "s3_to_aurora_lambda_code" {
  bucket = aws_s3_bucket.s3_to_aurora_lambda_bucket.bucket
  key    = "lambda_function.zip"
  source = local.s3_to_aurora_lambda_path
}

# lambda role to assume
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
  name               = "lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Create an IAM policy for the lambda to access S3 and DynamoDB
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
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
        ],
      "Resource": "*"
    }
  ]
}
EOF
}

# Attach necessary policies to the IAM role
resource "aws_iam_role_policy_attachment" "lambda_role_attachment" {
  role      = aws_iam_role.lambda_role.name
  # policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  policy_arn = aws_iam_policy.lambda_policy.arn
  # policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}
# arn:aws:iam::aws:policy/AWSLambda_FullAccess
# arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# lambda log group
resource "aws_cloudwatch_log_group" "s3_to_aurora_log_group" {
  name              = "/aws/lambda/${var.s3_to_aurora_lambda_function_name}"
  # name              = "/aws/lambda/${aws_lambda_function.process_csv_lambda.function_name}"
  # name              = "/aws/lambda/process_csv_lambda"
  retention_in_days = 14
}

resource "aws_iam_policy" "s3_to_aurora_logging_policy" {
  name   = "s3-to-aurora-logging-policy"
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

# Attach the lambda logging IAM policy to the lambda role
resource "aws_iam_role_policy_attachment" "s3_to_aurora_lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.s3_to_aurora_logging_policy.arn
}

# Default VPC subnet 1 data block
data "aws_subnet" "default_subnet1" {
  id = var.subnet_id1
}

# Default VPC subnet 1 data block
data "aws_subnet" "default_subnet2" {
  id = var.subnet_id2
}


####################
# AWS Pyscopg Lambda layer 
####################

# Create an S3 bucket
resource "aws_s3_bucket" "lambda_layer_bucket" {
  bucket = var.input_s3_bucket_name
}

# Upload the zip file to the S3 bucket
resource "aws_s3_object" "lambda_layer_zip" {
  bucket = aws_s3_bucket.lambda_layer_bucket.bucket
  key    = var.input_s3_obj_key 
  source = local.psychopg2_zip_path
}

resource "aws_lambda_layer_version" "psychopg2_layer" {
  layer_name          = var.input_layer_name
  description         = var.input_desc
  s3_bucket           = var.input_s3_bucket_name
  s3_key              = var.input_s3_obj_key
  compatible_runtimes = var.input_runtime
}


################################
# S3 to Aurora Lambda Function #
################################

# lambda function to process csv file
resource "aws_lambda_function" "s3_to_aurora_lambda" {
  s3_bucket        = aws_s3_bucket.s3_to_aurora_lambda_bucket.bucket
  s3_key           = "lambda_function.zip"
  function_name    = "s3_to_aurora"
  handler          = "s3_to_aurora.s3_to_aurora"
  # handler          = "function.name/handler.process_csv_lambda"
  role             = aws_iam_role.lambda_role.arn
  runtime          = "python3.8"

  layers = [aws_lambda_layer_version.psychopg2_layer.arn]

  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
      CW_LOG_GROUP = aws_cloudwatch_log_group.s3_to_aurora_log_group.name,
      DB_NAME = aws_rds_cluster.aurora_dish_recipes_cluster.database_name,
      ENDPOINT = aws_rds_cluster.aurora_dish_recipes_cluster.endpoint,
      DB_USER = aws_rds_cluster.aurora_dish_recipes_cluster.master_username,
      DB_PW = aws_rds_cluster.aurora_dish_recipes_cluster.master_password,
    }
  }

  # configure VPC settings so Lambda can connect with Aurora DB in same VPC
  vpc_config {
    subnet_ids         = [data.aws_subnet.default_subnet1.id, data.aws_subnet.default_subnet2.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  # timeout in seconds
  timeout         = 900
  
  depends_on = [
    aws_s3_object.lambda_layer_zip,
    aws_iam_role_policy_attachment.s3_to_aurora_lambda_logs,
    aws_cloudwatch_log_group.s3_to_aurora_log_group,
  ]

}

##################################
# AWS create user Lambda Resources
##################################

# S3 bucket for Lambda code
resource "aws_s3_bucket" "create_user_lambda_bucket" {
  bucket = "create-user-lambda-bucket"
}

# S3 object for Lambda code
resource "aws_s3_object" "create_user_lambda_code" {
  bucket = aws_s3_bucket.create_user_lambda_bucket.bucket
  key    = "lambda_function.zip"
  source = local.create_user_lambda_path
}

# Create an IAM role for the Lambda to assume role
resource "aws_iam_role" "create_user_lambda_role" {
  name               = "create_user_lambda_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Create an IAM policy for the Lambda to access Aurora PostgreSQL
resource "aws_iam_policy" "create_user_lambda_policy" {
  name = "create_user_lambda_policy"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds-db:connect",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:AssignPrivateIpAddresses",
        "ec2:UnassignPrivateIpAddresses"
        ],
      "Resource": "*"
    }
  ]
}
EOF
}

# Attach necessary policies to the IAM role
resource "aws_iam_role_policy_attachment" "create_user_lambda_role_attachment" {
  role       = aws_iam_role.create_user_lambda_role.name
  policy_arn = aws_iam_policy.create_user_lambda_policy.arn
}

# Lambda log group
resource "aws_cloudwatch_log_group" "create_user_lambda_log_group" {
  name              = "/aws/lambda/create_user_lambda"
  retention_in_days = 14
}

# IAM policy for Lambda logging
resource "aws_iam_policy" "create_user_lambda_logging_policy" {
  name   = "create_user_lambda_logging_policy"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Action": [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Effect": "Allow",
        "Resource": "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Attach the Lambda logging IAM policy to the Lambda role
resource "aws_iam_role_policy_attachment" "create_user_lambda_logs" {
  role       = aws_iam_role.create_user_lambda_role.name
  policy_arn = aws_iam_policy.create_user_lambda_logging_policy.arn
}

############################################
# AWS Create Postgres user Lambda Function #
############################################

resource "aws_lambda_function" "create_user_lambda" {
  s3_bucket        = aws_s3_bucket.create_user_lambda_bucket.bucket
  s3_key           = "lambda_function.zip"
  function_name    = "create_user"
  handler          = "create_user.create_user"
  role             = aws_iam_role.create_user_lambda_role.arn
  runtime          = "python3.8"
  
  layers = [aws_lambda_layer_version.psychopg2_layer.arn]

  # Attach the Lambda function to the CloudWatch Logs group
  environment {
    variables = {
      CW_LOG_GROUP = aws_cloudwatch_log_group.create_user_lambda_log_group.name,
      DB_NAME = aws_rds_cluster.aurora_dish_recipes_cluster.database_name,
      ENDPOINT = aws_rds_cluster.aurora_dish_recipes_cluster.endpoint,
      DB_USER = aws_rds_cluster.aurora_dish_recipes_cluster.master_username,
      DB_PW = aws_rds_cluster.aurora_dish_recipes_cluster.master_password,
      NEW_USER = var.new_username,
      NEW_PW = var.new_password,
    }
  }
  
  # configure VPC settings so Lambda can connect with Aurora DB in same VPC
  vpc_config {
    subnet_ids         = [data.aws_subnet.default_subnet1.id, data.aws_subnet.default_subnet2.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
  
  # timeout in seconds
  timeout         = 900

  depends_on = [
    aws_s3_object.lambda_layer_zip,
    aws_s3_object.create_user_lambda_code,
    aws_iam_role_policy_attachment.create_user_lambda_logs,
    aws_cloudwatch_log_group.create_user_lambda_log_group,
  ]
}

###############################
# AWS S3 bucket #
###############################

# s3 bucket to store csv file
resource "aws_s3_bucket" "dish_recipes_bucket" {
  bucket = "dish-recipes-bucket"
    depends_on = [
    aws_lambda_function.s3_to_aurora_lambda,
    aws_rds_cluster.aurora_dish_recipes_cluster,
  ]
}

# s3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "dish_s3_bucket_ownership_controls" {
  bucket = aws_s3_bucket.dish_recipes_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# s3 bucket public access block
resource "aws_s3_bucket_public_access_block" "dish_s3_public_access_block" {
  bucket = aws_s3_bucket.dish_recipes_bucket.id

  # block_public_acls       = false
  # block_public_policy     = false
  # ignore_public_acls      = false
  # restrict_public_buckets = false
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

}

resource "aws_s3_bucket_acl" "dish_s3_bucket_acl" {
  depends_on = [
    aws_s3_bucket_ownership_controls.dish_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.dish_s3_public_access_block,
  ]

  bucket = aws_s3_bucket.dish_recipes_bucket.id
  acl    = "private"
  # acl    = "public-read"
  # grant {
  #   id          = aws_iam_role.lambda_role.arn
  #   type        = "CanonicalUser"
  #   permissions = ["FULL_CONTROL"]
  # }
}

# # s3 bucket policy data document to allow public access
# data "aws_iam_policy_document" "s3_bucket_policy_document" {
#   statement {
#     principals {
#       type        = "AWS"
#       identifiers = ["*"]
#     }

#     actions = [
#       "s3:GetObject",
#       "s3:PutObject",
#       "s3:ListBucket",
#     ]

#     resources = [
#       aws_s3_bucket.dish_recipes_bucket.arn,
#       "${aws_s3_bucket.dish_recipes_bucket.arn}/*",
#     ]
#   }
# }

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
      aws_s3_bucket.dish_recipes_bucket.arn,
      "${aws_s3_bucket.dish_recipes_bucket.arn}/*"
    ]

    condition {
      test = "StringEquals"
      variable = "aws:PrincipalAccount"
      values = [var.account_number]
    }
  }

  # statement {
  #   sid = "AllowLambdaFunction"
  #   effect = "Allow"

  #   principals {
  #     type = "Service"
  #     identifiers = ["arn:aws:iam::*:role/*"]
  #   }

  #   actions = [
  #     "s3:GetObject",
  #     "s3:PutObject",
  #     "s3:ListBucket"
  #   ]

  #   resources = [
  #     aws_s3_bucket.dish_recipes_bucket.arn,
  #     "${aws_s3_bucket.dish_recipes_bucket.arn}/*"
  #   ]
  # }

  # statement {
  #   sid = "AllowRDSInstance"
  #   effect = "Allow"

  #   principals {
  #     type = "Service"
  #     identifiers = ["arn:aws:rds:*:*:db:*"]
  #   }

  #   actions = [
  #     "s3:GetObject",
  #     "s3:PutObject",
  #     "s3:ListBucket"
  #   ]

  #   resources = [
  #     aws_s3_bucket.dish_recipes_bucket.arn,
  #     "${aws_s3_bucket.dish_recipes_bucket.arn}/*"
  #   ]
  # }
}

# s3 bucket policy to allow public access
resource "aws_s3_bucket_policy" "dish_recipes_bucket_policy" {
  bucket = aws_s3_bucket.dish_recipes_bucket.id
  policy = data.aws_iam_policy_document.s3_bucket_policy_document.json
  depends_on = [
    aws_s3_bucket_acl.dish_s3_bucket_acl,
    aws_s3_bucket_ownership_controls.dish_s3_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.dish_s3_public_access_block,
  ]
}

# s3 object to store csv file
resource "aws_s3_object" "dish_recipes_bucket_object" {
  bucket = aws_s3_bucket.dish_recipes_bucket.bucket
  key    = "dish_recipes.csv"
  source = local.csv_file_path
  depends_on = [
    aws_s3_bucket_notification.s3_bucket_notification,
    aws_lambda_function.s3_to_aurora_lambda,
    aws_rds_cluster.aurora_dish_recipes_cluster,
  ]
}

# S3 bucket notification to invoke lambda when csv file is uploaded
resource "aws_s3_bucket_notification" "s3_bucket_notification" {
    bucket = aws_s3_bucket.dish_recipes_bucket.id


    lambda_function {
        lambda_function_arn = aws_lambda_function.s3_to_aurora_lambda.arn
        events              = ["s3:ObjectCreated:*"]
        # filter_prefix       = "AWSLogs/"
        filter_suffix       = ".csv"
    }

    depends_on = [
      aws_lambda_permission.lambda_s3_permission,
      aws_lambda_function.s3_to_aurora_lambda,
      aws_rds_cluster.aurora_dish_recipes_cluster,
      ]
}

# # lambda permissions to allow s3 to invoke lambda
resource "aws_lambda_permission" "lambda_s3_permission" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_to_aurora_lambda.arn
  principal = "s3.amazonaws.com"
  # source_arn = "arn:aws:s3:::dish_recipes_bucket"
  source_arn = aws_s3_bucket.dish_recipes_bucket.arn
}

# # lambda permissions to allow RDS to invoke lambda
resource "aws_lambda_permission" "lambda_rds_permission" {
  statement_id  = "AllowExecutionFromAuroraRDSCluster"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_to_aurora_lambda.arn
  principal =  "rds.amazonaws.com"
  # source_arn = "arn:aws:s3:::dish_recipes_bucket"
  source_arn = aws_rds_cluster.aurora_dish_recipes_cluster.arn
}

# create s3 bucket for storing logs for dish recipes bucket
resource "aws_s3_bucket" "dish_recipes_log_bucket" {
  bucket = "dish-recipes-log-bucket"
}

# s3 bucket ownership controls
resource "aws_s3_bucket_ownership_controls" "dish_logs_bucket_ownership_controls" {
  bucket = aws_s3_bucket.dish_recipes_log_bucket.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}
# s3 bucket public access block
resource "aws_s3_bucket_public_access_block" "dish_logs_public_access_block" {
  bucket = aws_s3_bucket.dish_recipes_log_bucket.id

  # block_public_acls       = false
  # block_public_policy     = false
  # ignore_public_acls      = false
  # restrict_public_buckets = false

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# add logging bucket acl
resource "aws_s3_bucket_acl" "dish_recipes_log_bucket_acl" {

  depends_on = [
    aws_s3_bucket_ownership_controls.dish_logs_bucket_ownership_controls,
    aws_s3_bucket_public_access_block.dish_logs_public_access_block,
  ]

  bucket = aws_s3_bucket.dish_recipes_log_bucket.id
  acl    = "log-delivery-write"
}

# add logging bucket policy to log from dish recipes bucket to dish_recipes_log_bucket 
resource "aws_s3_bucket_logging" "dish_recipes_logging" {
  bucket = aws_s3_bucket.dish_recipes_bucket.id
  target_bucket = aws_s3_bucket.dish_recipes_log_bucket.id
  target_prefix = "log/"
}

# # Grant s3 permission to invoke lambda
# resource "aws_lambda_permission" "s3_invoke_lambda_permission" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.s3_to_aurora_lambda.function_name
#   principal     = "s3.amazonaws.com"
#   source_arn    = aws_s3_bucket.dish_recipes_bucket.arn
# }


# # resource "aws_lambda_function" "process_csv" {
# #   function_name = "process_csv"
# #   handler       = "index.handler"
# #   runtime       = "nodejs14.x"
# #   filename      = "path/to/your/lambda_function.zip"  # Update with the path to your Lambda function code

# #   environment {
# #     variables = {
# #       DYNAMODB_TABLE_NAME = aws_dynamodb_table.example_table.name
# #     }
# #   }
# # }

# # resource "aws_dynamodb_table" "example_table" {
# #   name           = "example_table"
# #   billing_mode   = "PAY_PER_REQUEST"
# #   hash_key       = "id"
# #   attribute {
# #     name = "id"
# #     type = "S"
# #   }
# # }

# # resource "aws_lambda_event_source_mapping" "example_trigger" {
# #   event_source_arn  = aws_s3_bucket.example_bucket.arn
# #   function_name     = aws_lambda_function.process_csv.function_name
# #   starting_position = "LATEST"
# # }