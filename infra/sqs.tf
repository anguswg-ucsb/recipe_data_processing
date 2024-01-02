# ########################################################################################################
# # SQS Queue for receiving Lambda messages containing a reference to a CSV in S3 and a row offset value #
# ########################################################################################################

# SQS queue for S3 event notifications
resource "aws_sqs_queue" "sqs_csv_chunk_queue" {
  name                       = var.chunked_csv_sqs_queue_name
  delay_seconds              = 10
  max_message_size           = 2048
  message_retention_seconds  = 518400 # 6 day retention period
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 3200   # 6 times the Lambda function timeout (600 seconds) to allow for retries (source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
  # policy = data.aws_iam_policy_document.sqs_queue_policy_doc.json

}

# SQS queue policy to allow lambda to write to queue
resource "aws_sqs_queue_policy" "sqs_csv_chunk_queue_policy" {
  queue_url = aws_sqs_queue.sqs_csv_chunk_queue.id
  policy    = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = "*",
        Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.sqs_csv_chunk_queue.arn,
        Condition = {
          ArnEquals = {
            # "aws:SourceArn" = aws_s3_bucket.raw_s3_bucket.arn
            "aws:SourceArn" = aws_lambda_function.chunk_csv_lambda.arn
          }
        }
      }
    ]
  })
}

# ##############################################
# # SQS Queue for S3 event notifications (RAW) #
# ##############################################

# SQS queue for S3 event notifications
resource "aws_sqs_queue" "sqs_to_scrape_queue" {
  name                       = var.to_scrape_sqs_queue_name
  delay_seconds              = 10
  max_message_size           = 2048
  message_retention_seconds  = 518400 # 6 day retention period
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 3200   # 6 times the Lambda function timeout (600 seconds) to allow for retries (source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
  # policy = data.aws_iam_policy_document.sqs_queue_policy_doc.json

}

# SQS queue policy to allow lambda to write to queue
resource "aws_sqs_queue_policy" "sqs_to_scrape_queue_policy" {
  queue_url = aws_sqs_queue.sqs_to_scrape_queue.id
  policy    = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = "*",
        Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.sqs_to_scrape_queue.arn,
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.raw_s3_bucket.arn,
            "aws:SourceArn" = aws_lambda_function.send_json_recipes_lambda.arn
          }
        }
      }
    ]
  })
}

# ################################################
# # SQS Queue for S3 event notifications (STAGE) #
# ################################################

# sqs_process_staged_queue
# sqs_s3_event_queue_stage

# SQS queue for S3 event notifications
resource "aws_sqs_queue" "sqs_process_staged_queue" {
  name                       = var.process_staged_sqs_queue_name
  delay_seconds              = 10
  max_message_size           = 2048
  message_retention_seconds  = 518400 # 6 day retention period
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 3200   # 6 times the Lambda function timeout (600 seconds) to allow for retries (source: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)
  # policy = data.aws_iam_policy_document.sqs_queue_policy_doc.json

}

# SQS queue policy to allow lambda to write to queue
resource "aws_sqs_queue_policy" "sqs_process_staged_queue_policy" {
  queue_url = aws_sqs_queue.sqs_process_staged_queue.id
  policy    = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = "*",
        Action = "sqs:SendMessage",
        Resource = aws_sqs_queue.sqs_process_staged_queue.arn,
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.stage_s3_bucket.arn
          }
        }
      }
    ]
  })
}
