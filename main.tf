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

#################
# Local variables
#################

locals {
  csv_file_path = "data/dish_recipes2.csv"
  unique_ingred_file_path = "data/unique_ingredients.csv"
  process_csv_lambda_path = "lambda/process_csv_lambda.zip"
  s3_to_db_lambda_path = "lambda/s3_to_db.zip"
  create_user_lambda_path = "lambda/create_user.zip"
  psychopg2_zip_path ="lambda/psycopg2-py38.zip"
}

####################
# VPC and Subnet IDs
####################

data "aws_vpc" "main_vpc" {
  id = var.vpc_id
  # id = "vpc-06a9576a46a4e4979"
}

# Default VPC subnet 1 data block
data "aws_subnet" "default_subnet1" {
  id = var.subnet_id1
}

# Default VPC subnet 1 data block
data "aws_subnet" "default_subnet2" {
  id = var.subnet_id2
}

# # ##############################
# # # SECRETS MANAGERS RDS PROXY #
# # ##############################

resource "aws_secretsmanager_secret" "ec2_db_secret" {
  name_prefix = var.ec2_secret_prefix
  recovery_window_in_days = 0
  description = "Secret for EC2 DB instance"
}

# # aws_rds_cluster.aurora_dish_recipes_cluster.iam_database_authentication_enabled
# # aws_rds_cluster_instance.aurora_dish_recipes_instance
resource "aws_secretsmanager_secret_version" "ec2_secret_version" {
  secret_id     = aws_secretsmanager_secret.ec2_db_secret.id
  secret_string = jsonencode({
    "username"             = var.db_username
    "password"             = var.db_password
    "db_name"              = var.db_name
    "engine"               = "postgres"
    "port"                 = 5432
  })
}

# ###############################
# EC2 instance to run PostgresSQL
# ###############################

resource "aws_instance" "ec2_db_instance" {
  ami           = var.ec2_t2_micro_ami_id
  instance_type = "t2.micro"
  iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name
  key_name      = aws_key_pair.ssh_key.key_name
  
  user_data_base64  = base64encode("${templatefile("${var.path_to_setup_db_script}", {
      DB_USERNAME   = jsondecode(aws_secretsmanager_secret_version.ec2_secret_version.secret_string)["username"],
      DB_PASSWORD   = jsondecode(aws_secretsmanager_secret_version.ec2_secret_version.secret_string)["password"],
      DB_NAME       = jsondecode(aws_secretsmanager_secret_version.ec2_secret_version.secret_string)["db_name"],
      S3_BUCKET     = var.s3_bucket_name,
      S3_FILE       = var.s3_csv_file_name,
      S3_UNIQUE_INGREDS_FILE = var.s3_unique_ingred_file_name,
      AWS_REGION    = var.region,
  })}")

  # user_data     = file("path/to/your/user-data-script.sh")
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  subnet_id         = data.aws_subnet.default_subnet1.id
  
  associate_public_ip_address = true

  depends_on = [
    aws_s3_bucket.dish_recipes_bucket,
    aws_s3_object.dish_recipes_bucket_object,
    aws_s3_object.uingredients_bucket_object,
    aws_secretsmanager_secret_version.ec2_secret_version,
    aws_secretsmanager_secret.ec2_db_secret,
    aws_security_group.ec2_sg,
  ]

  tags = {
    Name = "EC2 Database Instance"
  }
}

##############
# EC2 IAM ROLE
##############

resource "aws_iam_role" "ec2_role" {
  name = "EC2-IAM-ReadOnly"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "ec2_role_policy_attachment" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
  name = "ec2-instance-profile"

  role = aws_iam_role.ec2_role.id
}
# # ##############
# # EC2 Key Pair #
# # ##############

# Public key to use to login to the EC2 instance
resource "aws_key_pair" "ssh_key" {
  key_name   = "ec2_db_key"
  public_key = file(var.ec2_public_key_path)
}

#################
# SECURITY GROUPS
#################

# Security group for the EC2 instance
resource "aws_security_group" "ec2_sg" {
  name        = "ec2_sg"
  description = "Security group for the EC2 Postgres DB instance"
  vpc_id      = data.aws_vpc.main_vpc.id

  # Rule to allow SSH (port 22) access from your personal IP
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["${var.env_ip}/32"]
  }

  # Rule to allow PostgreSQL (port 5432) access from your personal IP
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["${var.env_ip}/32"]
  }

  # # Rule to allow traffic from the Lambda security group
  ingress {
    from_port         = 5432
    to_port           = 5432
    protocol          = "tcp"
    security_groups   = [data.aws_security_group.lambda_sg.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ec2_sg"
  }
}

data "aws_security_group" "lambda_sg" {
  id = var.lambda_sg_id
}


# # Security group for the Lambda function
# resource "aws_security_group" "lambda_sg" {
#   name        = "lambda_sg"
#   description = "Security group for the Lambda function"
#   vpc_id      = data.aws_vpc.main_vpc.id

#   # lambda function egress
#   egress {
#     from_port        = 0
#     to_port          = 0
#     protocol         = "-1"
#     cidr_blocks      = ["0.0.0.0/0"]
#   }

#   tags = {
#     Name = "lambda_sg"
#   }
# }

# resource "aws_security_group" "lambda_sg" {
#     name = "lambda-sg"
#     vpc_id      = data.aws_vpc.main_vpc.id

#     ingress {
#         from_port = 80
#         to_port = 80
#         protocol = "tcp"
#         cidr_blocks = ["0.0.0.0/0"]
#     }

#     egress {
#         from_port = 0
#         to_port = 0
#         protocol = "-1"
#         cidr_blocks = ["0.0.0.0/0"]
#     }


# }

# resource "aws_security_group" "aurora_sg" {
#     name = "aurora-sg"
#     vpc_id      = data.aws_vpc.main_vpc.id

#     ingress {
#         from_port = 5432
#         to_port = 5432
#         protocol = "tcp"
#         security_groups = [aws_security_group.lambda_sg.id]
#     }

#     ingress {
#       from_port = 5432
#       to_port = 5432
#       protocol = "tcp"
#       cidr_blocks = ["${var.env_ip}/32"]
#     }

#     ingress {
#       from_port = 443
#       to_port = 443
#       protocol = "tcp"
#       cidr_blocks = ["${var.env_ip}/32"]
#     }

#     ingress {
#       from_port = 22
#       to_port = 22
#       protocol = "tcp"
#       cidr_blocks = ["${var.env_ip}/32"]
#     }

#     egress {
#         from_port = 0
#         to_port = 0
#         protocol = "-1"
#         cidr_blocks = ["0.0.0.0/0"]
#     }

# }

# resource "aws_security_group" "sg_lambda" {
#   name = "lambda-sg-proxy"
#   vpc_id      = data.aws_vpc.main_vpc.id

  # egress {
  #   from_port        = 0
  #   to_port          = 0
  #   protocol         = "-1"
  #   cidr_blocks      = ["0.0.0.0/0"]
  # }
# }

# resource "aws_security_group" "sg_rds_proxy" {
#   name = "rds-proxy-sg"
#   vpc_id      = data.aws_vpc.main_vpc.id

#   ingress {
#     description      = "POSTGRES TLS from sg_lambda"
#     from_port        = 5432
#     to_port          = 5432
#     protocol         = "tcp"
#     security_groups  = [aws_security_group.sg_lambda.id]
#   }

#   egress {
#     from_port        = 0
#     to_port          = 0
#     protocol         = "-1"
#     cidr_blocks      = ["0.0.0.0/0"]
#   }
# }

# resource "aws_security_group" "sg_rds" {
#   name = "rds-sg"
#   vpc_id      = data.aws_vpc.main_vpc.id

#   ingress {
#     description      = "POSTGRES TLS from sg_rds_proxy"
#     from_port        = 5432
#     to_port          = 5432
#     protocol         = "tcp"
#     security_groups  = [aws_security_group.sg_rds_proxy.id]
#   }

#   egress {
#     from_port        = 0
#     to_port          = 0
#     protocol         = "-1"
#     cidr_blocks      = ["0.0.0.0/0"]
#   }
# }


# #######################################
# # AWS S3 bucket (dish-recipes-bucket) #
# #######################################

# s3 bucket to store csv file
resource "aws_s3_bucket" "dish_recipes_bucket" {
  bucket = "dish-recipes-bucket"
  #   depends_on = [
  #   aws_lambda_function.s3_to_db_lambda,
  #   aws_instance.ec2_db_instance,
  # ]
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
      aws_s3_bucket.dish_recipes_bucket.arn,
      "${aws_s3_bucket.dish_recipes_bucket.arn}/*"
    ]

    condition {
      test = "StringEquals"
      variable = "aws:PrincipalAccount"
      values = [var.account_number]
    }
  }
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
# ###############################
# # AWS S3 Object (CSV file) #
# ###############################

# s3 object to store csv file
resource "aws_s3_object" "dish_recipes_bucket_object" {
  bucket = aws_s3_bucket.dish_recipes_bucket.bucket
  key    = var.s3_csv_file_name
  source = local.csv_file_path
  # depends_on = [
  #   aws_s3_bucket_notification.s3_bucket_notification,
  #   aws_lambda_function.s3_to_db_lambda,
  #   aws_instance.ec2_db_instance,
  # ]
}

# s3 object to store csv file
resource "aws_s3_object" "uingredients_bucket_object" {
  bucket = aws_s3_bucket.dish_recipes_bucket.bucket
  key    = var.s3_unique_ingred_file_name
  source = local.unique_ingred_file_path
  # depends_on = [
  #   aws_s3_bucket_notification.s3_bucket_notification,
  #   aws_lambda_function.s3_to_db_lambda,
  #   aws_instance.ec2_db_instance,
  # ]
}

# # S3 bucket notification to invoke lambda when csv file is uploaded
# resource "aws_s3_bucket_notification" "s3_bucket_notification" {
#     bucket = aws_s3_bucket.dish_recipes_bucket.id


#     lambda_function {
#         lambda_function_arn = aws_lambda_function.s3_to_db_lambda.arn
#         events              = ["s3:ObjectCreated:*"]
#         # filter_prefix       = "AWSLogs/"
#         filter_suffix       = ".csv"
#     }

#     depends_on = [
#       aws_lambda_permission.lambda_s3_permission,
#       aws_lambda_function.s3_to_db_lambda,
#       aws_instance.ec2_db_instance,
#       ]
# }

# # # lambda permissions to allow s3 to invoke lambda
# resource "aws_lambda_permission" "lambda_s3_permission" {
#   statement_id  = "AllowExecutionFromS3Bucket"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.s3_to_db_lambda.arn
#   principal = "s3.amazonaws.com"
#   # source_arn = "arn:aws:s3:::dish_recipes_bucket"
#   source_arn = aws_s3_bucket.dish_recipes_bucket.arn
# }

# # # lambda permissions to allow RDS to invoke lambda
# resource "aws_lambda_permission" "lambda_rds_permission" {
#   statement_id  = "AllowExecutionFromAuroraRDSCluster"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.s3_to_db_lambda.arn
#   principal =  "rds.amazonaws.com"
#   # source_arn = "arn:aws:s3:::dish_recipes_bucket"
#   source_arn = aws_rds_cluster.aurora_dish_recipes_cluster.arn
# }

# ####################################################
# # AWS S3 logging bucket (dish-recipes-bucket logs) #
# ####################################################

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


# ##############################
# # AWS S3 pyscopg2 Lambda layer 
# ##############################

# # Create an S3 bucket
# resource "aws_s3_bucket" "lambda_layer_bucket" {
#   bucket = var.input_s3_bucket_name
# }

# # Upload the zip file to the S3 bucket
# resource "aws_s3_object" "lambda_layer_zip" {
#   bucket = aws_s3_bucket.lambda_layer_bucket.bucket
#   key    = var.input_s3_obj_key 
#   source = local.psychopg2_zip_path
# }

# resource "aws_lambda_layer_version" "psychopg2_layer" {
#   layer_name          = var.input_layer_name
#   description         = var.input_desc
#   s3_bucket           = var.input_s3_bucket_name
#   s3_key              = var.input_s3_obj_key
#   compatible_runtimes = var.input_runtime
#   depends_on = [
#     aws_s3_bucket.lambda_layer_bucket,
#     aws_s3_object.lambda_layer_zip,
#   ] 
# }


# ######################################
# # S3 to EC2 Database Lambda Function #
# ######################################

# # lambda function to process csv file
# resource "aws_lambda_function" "s3_to_db_lambda" {
#   s3_bucket        = aws_s3_bucket.s3_to_db_lambda_bucket.bucket
#   s3_key           = "lambda_function.zip"
#   function_name    = "s3_to_db"
#   handler          = "s3_to_db.s3_to_db"
#   # handler          = "function.name/handler.process_csv_lambda"
#   role             = aws_iam_role.lambda_role.arn
#   runtime          = "python3.8"

#   layers = [aws_lambda_layer_version.psychopg2_layer.arn]

#   # Attach the Lambda function to the CloudWatch Logs group
#   environment {
#     variables = {
#       CW_LOG_GROUP = aws_cloudwatch_log_group.s3_to_db_log_group.name,
#       S3_FILE_NAME = var.s3_csv_file_name,
#       DB_NAME = var.db_name,
#       # ENDPOINT = aws_rds_cluster.aurora_dish_recipes_cluster.endpoint,
#       ENDPOINT = aws_instance.ec2_db_instance.public_dns,
#       DB_USER = var.db_username,
#       DB_PW = var.db_password,
#     }
#   }

#   # configure VPC settings so Lambda can connect with EC2 postgres DB in same VPC
#   vpc_config {
#     subnet_ids         = [data.aws_subnet.default_subnet1.id, data.aws_subnet.default_subnet2.id]
#     security_group_ids = [aws_security_group.lambda_sg.id]
#   }
  
#   # timeout in seconds
#   timeout         = 900
  
#   depends_on = [
#     aws_instance.ec2_db_instance,
#     aws_security_group.ec2_sg,
#     aws_s3_object.lambda_layer_zip,
#     aws_iam_role_policy_attachment.s3_to_db_lambda_logs,
#     aws_cloudwatch_log_group.s3_to_db_log_group,
#   ]

# }


# ##########################################
# # RDS PROXY SECRETS IAM ROLE/PERMISSIONS #
# ##########################################

# data "aws_iam_policy_document" "assume_role" {

#   statement {
#     effect  = "Allow"
#     actions = ["sts:AssumeRole"]

#     principals {
#       type        = "Service"
#       identifiers = ["rds.amazonaws.com"]
#     }
#   }
# }

# data "aws_iam_policy_document" "rds_proxy_policy_document" {

#   statement {
#     sid = "AllowProxyToGetDbCredsFromSecretsManager"

#     actions = [
#       "secretsmanager:GetSecretValue"
#     ]

#     resources = [
#       aws_secretsmanager_secret.rds_secret.arn
#     ]
#   }

#   statement {
#     sid = "AllowProxyToDecryptDbCredsFromSecretsManager"

#     actions = [
#       "kms:Decrypt"
#     ]

#     resources = [
#       "*"
#     ]

#     condition {
#       test     = "StringEquals"
#       values   = ["secretsmanager.${var.region}.amazonaws.com"]
#       variable = "kms:ViaService"
#     }
#   }
# }

# # Create an IAM policy with the necessary permissions for the RDS Proxy to access Secrets Manager
# resource "aws_iam_policy" "rds_proxy_iam_policy" {
#   name   = "rds-proxy-policy"
#   policy = data.aws_iam_policy_document.rds_proxy_policy_document.json
# }

# # Attach above IAM policy to the IAM role for RDS Proxy
# resource "aws_iam_role_policy_attachment" "rds_proxy_iam_attach" {
#   policy_arn = aws_iam_policy.rds_proxy_iam_policy.arn
#   role       = aws_iam_role.rds_proxy_iam_role.name
# }

# # Create an IAM role for the RDS Proxy to assume
# resource "aws_iam_role" "rds_proxy_iam_role" {
#   name               = "rds-proxy-role"
#   assume_role_policy = data.aws_iam_policy_document.assume_role.json
# }

# ###############################
# # DB SECRETS MANAGERS SECRETS #
# ###############################

# resource "aws_secretsmanager_secret" "database_credentials" {
#   name = var.secrets_manager_credentials_name
#   recovery_window_in_days = 0
# }

# resource "aws_secretsmanager_secret_version" "database_credentials_version" {
#   secret_id = aws_secretsmanager_secret.database_credentials.id
#   secret_string = jsonencode({
#     username = var.db_username,
#     password = var.db_password
#   })
# }

# resource "aws_iam_policy" "secrets_manager_policy" {
#   name        = "secrets-manager-policy"
#   path        = "/"
#   description = "Allows access to the Secrets Manager"
#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect    = "Allow",
#         Action    = [
#           "secretsmanager:GetSecretValue",
#         ],
#         Resource = aws_secretsmanager_secret.database_credentials.arn,
#       },
#     ],
#   })
# }

# resource "aws_iam_role" "secrets_manager_role" {
#   name               = "secrets-manager-role"
#   assume_role_policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect    = "Allow",
#         Principal = { Service = "lambda.amazonaws.com" },
#         Action    = "sts:AssumeRole",
#       },
#     ],
#   })

#   # policy = aws_iam_policy.secrets_manager_policy.policy
# }

# resource "aws_iam_role_policy_attachment" "secrets_manager_role_policy_attachment" {
#   role       = aws_iam_role.secrets_manager_role.name
#   policy_arn = aws_iam_policy.secrets_manager_policy.arn
# }

# ################
# # ECR Repository
# ################

# # ECR Repository
# resource "aws_ecr_repository" "ecr_postgres_repo" {
#   name = var.ecr_repo_name
# }

# ###############################################
# # GitHub Actions IAM Role & Policies Repository
# ###############################################

# # IAM User for Github Actions to upload new Docker image to ECR 
# resource "aws_iam_user" "github_user" {
#   name = "github-actions-user"   
# }

# # extra IAM permissions the github-user needs that are NOT covered by AWS managed policy ("arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess")
# data "aws_iam_policy_document" "github_user_iam_policy_doc" {

#   statement {
#     effect = "Allow"
#     actions = [
#       "ecs:UpdateService",
#       "ecs:DescribeServices",
#       "ecs:RegisterTaskDefinition",
#       "ecs:DescribeTaskDefinition",
#       "ecs:RegisterTaskDefinition",
#       "ecs:DeregisterTaskDefinition",
#       "ecs:DescribeTasks",
#       "ecs:RunTask",
#       "iam:PassRole",
#     ]
#     resources = ["*"]
#   }
# }

# # create
# resource "aws_iam_policy" "github_user_iam_policy" {
#   name        = "github-user-iam-policy"
#   description = "IAM Policy to attach to the GitHub Actions User (github-user) that allows for permissions to ECS"
#   policy      = data.aws_iam_policy_document.github_user_iam_policy_doc.json
# }

# # attach github-user with AWS managed policy ("arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess")
# resource "aws_iam_user_policy_attachment" "github_user_attach1" {
#   user       = aws_iam_user.github_user.name
#   policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
# }

# # attach github-user extra needed IAM permissions ("github_user_extra_iam_policy" block above)
# resource "aws_iam_user_policy_attachment" "github_user_attach2" {
#   user       = aws_iam_user.github_user.name
#   policy_arn = aws_iam_policy.github_user_iam_policy.arn
# }

###############################
# AWS Lambda #
###############################

# # s3 bucket for lambda code
# resource "aws_s3_bucket" "s3_to_db_lambda_bucket" {
#   bucket = "s3-to-db-lambda-bucket" 
# }

# # s3 object for lambda code
# resource "aws_s3_object" "s3_to_db_lambda_code" {
#   bucket = aws_s3_bucket.s3_to_db_lambda_bucket.bucket
#   key    = "lambda_function.zip"
#   source = local.s3_to_db_lambda_path
# }

# # lambda role to assume
# data "aws_iam_policy_document" "lambda_assume_role" {
#   statement {
#     effect = "Allow"

#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }

#     actions = ["sts:AssumeRole"]
#   }
# }

# # Create an IAM role for the lambda to assume role
# resource "aws_iam_role" "lambda_role" {
#   name               = "lambda_role"
#   assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
# }

# # Create an IAM policy for the lambda to access S3 and DynamoDB
# resource "aws_iam_policy" "lambda_policy" {
#   name = "lambda_policy"

#   policy = <<EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": "s3:GetObject",
#       "Resource": "arn:aws:s3:::dish-recipes-bucket/*"
#     },
#     {
#       "Effect": "Allow",
#       "Action": [
#         "logs:CreateLogGroup",
#         "logs:CreateLogStream",
#         "logs:PutLogEvents",
#         "ec2:CreateNetworkInterface",
#         "ec2:DescribeNetworkInterfaces",
#         "ec2:DeleteNetworkInterface",
#         "ec2:AssignPrivateIpAddresses",
#         "ec2:UnassignPrivateIpAddresses",
#         "rds-db:*"
#         ],
#       "Resource": "*"
#     }
#   ]
# }
# EOF
# }

# # Attach necessary policies to the IAM role
# resource "aws_iam_role_policy_attachment" "lambda_role_attachment" {
#   role      = aws_iam_role.lambda_role.name
#   # policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
#   policy_arn = aws_iam_policy.lambda_policy.arn
#   # policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
# }
# # arn:aws:iam::aws:policy/AWSLambda_FullAccess
# # arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole

# # lambda log group
# resource "aws_cloudwatch_log_group" "s3_to_db_log_group" {
#   name              = "/aws/lambda/${var.s3_to_db_lambda_function_name}"
#   # name              = "/aws/lambda/${aws_lambda_function.process_csv_lambda.function_name}"
#   # name              = "/aws/lambda/process_csv_lambda"
#   retention_in_days = 14
# }

# resource "aws_iam_policy" "s3_to_db_logging_policy" {
#   name   = "s3-to-db-logging-policy"
#   policy = jsonencode({
#     "Version" : "2012-10-17",
#     "Statement" : [
#       {
#         Action : [
#           "logs:CreateLogGroup",
#           "logs:CreateLogStream",
#           "logs:PutLogEvents"
#         ],
#         Effect : "Allow",
#         Resource : "arn:aws:logs:*:*:*"
#       }
#     ]
#   })
# }

# # Attach the lambda logging IAM policy to the lambda role
# resource "aws_iam_role_policy_attachment" "s3_to_db_lambda_logs" {
#   role       = aws_iam_role.lambda_role.name
#   policy_arn = aws_iam_policy.s3_to_db_logging_policy.arn
# }

# ##############################
# # AWS S3 pyscopg2 Lambda layer 
# ##############################

# # Create an S3 bucket
# resource "aws_s3_bucket" "lambda_layer_bucket" {
#   bucket = var.input_s3_bucket_name
# }

# # Upload the zip file to the S3 bucket
# resource "aws_s3_object" "lambda_layer_zip" {
#   bucket = aws_s3_bucket.lambda_layer_bucket.bucket
#   key    = var.input_s3_obj_key 
#   source = local.psychopg2_zip_path
# }

# resource "aws_lambda_layer_version" "psychopg2_layer" {
#   layer_name          = var.input_layer_name
#   description         = var.input_desc
#   s3_bucket           = var.input_s3_bucket_name
#   s3_key              = var.input_s3_obj_key
#   compatible_runtimes = var.input_runtime
#   depends_on = [
#     aws_s3_bucket.lambda_layer_bucket,
#     aws_s3_object.lambda_layer_zip,
#   ] 
# }


# ######################################
# # S3 to EC2 Database Lambda Function #
# ######################################

# # lambda function to process csv file
# resource "aws_lambda_function" "s3_to_db_lambda" {
#   s3_bucket        = aws_s3_bucket.s3_to_db_lambda_bucket.bucket
#   s3_key           = "lambda_function.zip"
#   function_name    = "s3_to_db"
#   handler          = "s3_to_db.s3_to_db"
#   # handler          = "function.name/handler.process_csv_lambda"
#   role             = aws_iam_role.lambda_role.arn
#   runtime          = "python3.8"

#   layers = [aws_lambda_layer_version.psychopg2_layer.arn]

#   # Attach the Lambda function to the CloudWatch Logs group
#   environment {
#     variables = {
#       CW_LOG_GROUP = aws_cloudwatch_log_group.s3_to_db_log_group.name,
#       S3_FILE_NAME = var.s3_csv_file_name,
#       DB_NAME = var.db_name,
#       # ENDPOINT = aws_rds_cluster.aurora_dish_recipes_cluster.endpoint,
#       ENDPOINT = aws_instance.ec2_db_instance.public_dns,
#       DB_USER = var.db_username,
#       DB_PW = var.db_password,
#     }
#   }

#   # configure VPC settings so Lambda can connect with EC2 postgres DB in same VPC
#   vpc_config {
#     subnet_ids         = [data.aws_subnet.default_subnet1.id, data.aws_subnet.default_subnet2.id]
#     security_group_ids = [aws_security_group.lambda_sg.id]
#   }
  
#   # timeout in seconds
#   timeout         = 900
  
#   depends_on = [
#     aws_instance.ec2_db_instance,
#     aws_security_group.ec2_sg,
#     aws_s3_object.lambda_layer_zip,
#     aws_iam_role_policy_attachment.s3_to_db_lambda_logs,
#     aws_cloudwatch_log_group.s3_to_db_log_group,
#   ]

# }