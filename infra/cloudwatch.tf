######################################
# Lambda Log Group (recipe scraper lambda) #
######################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "raw_recipes_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.scraper_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}
