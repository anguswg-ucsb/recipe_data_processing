
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


# # S3 event notification for raw data bucket to trigger lambda function
# resource "aws_s3_bucket_notification" "raw_s3_bucket_notification" {
#   bucket = aws_s3_bucket.raw_s3_bucket.id

#   lambda_function {
#     lambda_function_arn = aws_lambda_function.recipe_scraper_lambda_function.arn
#     events              = ["s3:ObjectCreated:*"]
#     # filter_prefix       = "raw/"
#     filter_suffix       = ".json"
#   }
# }

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
  key    = var.recipe_scraper_lambda_zip_filename
  source = local.recipe_scraper_lambda_zip
  etag   = filemd5(local.recipe_scraper_lambda_zip)
}