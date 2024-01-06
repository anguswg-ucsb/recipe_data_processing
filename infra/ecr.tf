# ####################################
# AWS ECR for Lambda container image #
######################################

# ECR Repo for Extract ingredients Docker image 
data "aws_ecr_repository" "lambda_ecr_repository" {
  name = var.lambda_ecr_repository_name
}

# # Create an ECR repository for the Lambda container image
# resource "aws_ecr_repository" "lambda_ecr_repository" {
#   name = var.lambda_ecr_repository_name
#   force_delete = false
#   image_tag_mutability = "MUTABLE"
#   image_scanning_configuration {
#     scan_on_push = true
#   }
#   tags = {
#     name              = local.name_tag
#     resource_category = "ecr"
#   }
# }
