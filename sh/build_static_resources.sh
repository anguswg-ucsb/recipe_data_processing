#!/bin/bash

# # Check if AWS_ACCOUNT_NUMBER is provided as an argument
# if [ -z "$1" ]; then
#     echo "Error: AWS_ACCOUNT_NUMBER is required. Please provide it as an argument."
#     exit 1
# fi

# AWS Account Number
AWS_ACCOUNT_NUMBER=$1

BUCKET_NAME=$2

# S3 bucket and ECR repo names
BUCKET_NAME=$2
BUCKET_NAME="recipes-output-bucket"

ECR_REPO_NAME="extract-ingredients-lambda-repository"

# regions to create/check resources
AWS_REGION="us-west-1"
LOCATION_CONSTRAINT="us-west-1"

export TF_VAR_output_s3_bucket_name="$BUCKET_NAME"
export TF_VAR_lambda_ecr_repository_name="$ECR_REPO_NAME"

# export TF_VAR_output_s3_bucket_name="recipes-output-bucket"
# export TF_VAR_lambda_ecr_repository_name="extract-ingredients-lambda-repository"

# check if the output bucket ALREADY EXISTS
if ! aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    # Create the output bucket if it DOESN'T exist
    aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$AWS_REGION" --create-bucket-configuration LocationConstraint="$LOCATION_CONSTRAINT"
else
    echo "Bucket $BUCKET_NAME already exists."
fi

# check if the ECR repository ALREADY EXISTS
if ! aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" 2>/dev/null; then
    # create the ECR repository if it DOESN'T exist
    aws ecr create-repository --repository-name "$ECR_REPO_NAME" --region "$AWS_REGION"
    echo "ECR repository $ECR_REPO_NAME created."
else
    echo "ECR repository $ECR_REPO_NAME already exists."
fi

# Export ECR repository URL
ECR_REPO_URL=$(aws ecr describe-repositories --repository-names "$ECR_REPO_NAME" --region "$AWS_REGION" --query 'repositories[0].repositoryUri' --output text)
export TF_VAR_lambda_ecr_repository_url="$ECR_REPO_URL"
echo "ECR repository URL: $ECR_REPO_URL"

# AWS CLI and Docker commands to login, build, tag, and push Docker image
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin $AWS_ACCOUNT_NUMBER.dkr.ecr.$AWS_REGION.amazonaws.com

# AWS_LOGIN_CMD=$(aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$AWS_ACCOUNT_NUMBER.dkr.ecr.$AWS_REGION.amazonaws.com")
# eval $AWS_LOGIN_CMD

# build Docker image
docker build -t extract-ingredients-lambda-repository lambda_containers/extract_ingredients_lambda/

# tag Docker image
docker tag extract-ingredients-lambda-repository:latest "$AWS_ACCOUNT_NUMBER.dkr.ecr.$AWS_REGION.amazonaws.com/extract-ingredients-lambda-repository:latest"

# push Docker image to ECR repository
docker push "$AWS_ACCOUNT_NUMBER.dkr.ecr.$AWS_REGION.amazonaws.com/extract-ingredients-lambda-repository:latest"