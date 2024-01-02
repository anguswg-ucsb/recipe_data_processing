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