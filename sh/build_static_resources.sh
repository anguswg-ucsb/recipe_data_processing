# S3 bucket and ECR repo names
BUCKET_NAME="recipes-output-bucket"
ECR_REPO_NAME="extract-ingredients-lambda-repository"

# regions to create/check resources
AWS_REGION="us-west-1"
LOCATION_CONSTRAINT="us-west-1"

export TF_VAR_output_s3_bucket_name="$BUCKET_NAME"
export TF_VAR_lambda_ecr_repository_name="$ECR_REPO_NAME"

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