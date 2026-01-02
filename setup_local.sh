#!/bin/bash

# Configuration
URL="http://localstack:4566"
BUCKET_NAME="my-image-bucket"
TABLE_NAME="ImagesTable"
LAMBDA_NAME="ImageServiceLambda"
ROLE_ARN="arn:aws:iam::000000000000:role/lambda-role"

# --- 1. INSTALL PRE-REQUISITES ---
echo "Installing zip utility..."
# The amazon/aws-cli image is based on Amazon Linux, so we use yum
yum install -y zip > /dev/null 2>&1

echo "Waiting for LocalStack to be ready..."
until aws --endpoint-url=$URL s3 ls > /dev/null 2>&1; do
  printf '.'
  sleep 2
done
echo "LocalStack is ready!"

echo "--- STARTING INFRASTRUCTURE SETUP ---"

# --- 2. CREATE ZIP FILE ---
echo "Zipping Lambda code..."
# Ensure we are in the right directory
if [ -d "app" ]; then
    cd app
    # Zip main.py into function.zip located in the parent folder
    zip -r ../function.zip main.py
    cd ..
else
    echo "ERROR: 'app' directory not found!"
    ls -la
    exit 1
fi

# DEBUG: Verify zip content
echo "Verifying zip content:"
unzip -l function.zip

# --- 3. CREATE RESOURCES ---

echo "Creating S3 Bucket..."
aws --endpoint-url=$URL s3 mb s3://$BUCKET_NAME

echo "Creating DynamoDB Table..."
aws --endpoint-url=$URL dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions AttributeName=image_id,AttributeType=S \
    --key-schema AttributeName=image_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

echo "Creating Lambda Function..."
aws --endpoint-url=$URL lambda create-function \
    --function-name $LAMBDA_NAME \
    --runtime python3.9 \
    --handler main.lambda_handler \
    --role $ROLE_ARN \
    --zip-file fileb://function.zip \
    --environment Variables="{BUCKET_NAME=$BUCKET_NAME,TABLE_NAME=$TABLE_NAME,LOCALSTACK_HOSTNAME=localstack}"

echo "Creating API Gateway..."
API_ID=$(aws --endpoint-url=$URL apigateway create-rest-api --name "ImageAPI" --query 'id' --output text)
PARENT_ID=$(aws --endpoint-url=$URL apigateway get-resources --rest-api-id $API_ID --query 'items[0].id' --output text)

RESOURCE_ID=$(aws --endpoint-url=$URL apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $PARENT_ID \
    --path-part "{proxy+}" \
    --query 'id' --output text)

aws --endpoint-url=$URL apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --authorization-type "NONE"

aws --endpoint-url=$URL apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method ANY \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:000000000000:function:$LAMBDA_NAME/invocations

aws --endpoint-url=$URL apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name dev

echo "--- SETUP COMPLETE ---"
echo "API ID: $API_ID"