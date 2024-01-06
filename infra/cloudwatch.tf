
######################################
# Lambda Log Group (chunk_csv_lambda) #
######################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "chunk_csv_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.chunk_csv_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}

######################################
# Lambda Log Group (send JSON lambda) #
######################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "send_json_recipes_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.send_json_recipes_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}


######################################
# Lambda Log Group (recipe scraper lambda) #
######################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "raw_recipes_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.scraper_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}

#################################################
# Lambda Log Group (extract ingredients lambda) #
#################################################

# Cloudwatch log group for 'raw_recipes_lambda_log_group' Python lambda function
resource "aws_cloudwatch_log_group" "extract_ingredients_lambda_log_group" {
  name_prefix              = "/aws/lambda/${var.extract_ingredients_lambda_function_name}"
  retention_in_days = 14
  skip_destroy = true
}

