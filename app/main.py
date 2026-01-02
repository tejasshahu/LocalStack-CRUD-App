import json
import boto3
import os
import base64
import uuid
from datetime import datetime
from botocore.exceptions import ClientError

# --- Configuration ---
# In a real app, these are environment variables
S3_BUCKET = os.environ.get("BUCKET_NAME", "my-image-bucket")
DYNAMO_TABLE = os.environ.get("TABLE_NAME", "ImagesTable")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# Initialize AWS Clients
# endpoint_url is required to point to LocalStack inside the docker network
s3 = boto3.client('s3', region_name=REGION,
                  endpoint_url=f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')}:4566")
dynamodb = boto3.resource('dynamodb', region_name=REGION,
                          endpoint_url=f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')}:4566")
table = dynamodb.Table(DYNAMO_TABLE)


def lambda_handler(event, context):
    """
    Main entry point for API Gateway.
    Routes requests based on HTTP Method and Resource Path.
    """
    print("Received event:", json.dumps(event))

    method = event.get('httpMethod')
    path = event.get('path')

    try:
        if method == 'POST' and path == '/images':
            return upload_image(event)
        elif method == 'GET' and path.startswith('/images/'):
            image_id = path.split('/')[-1]
            return get_image(image_id)
        elif method == 'GET' and path == '/images':
            return list_images(event)
        elif method == 'DELETE' and path.startswith('/images/'):
            image_id = path.split('/')[-1]
            return delete_image(image_id)
        else:
            return response(404, {"error": "Route not found"})
    except Exception as e:
        print(e)
        return response(500, {"error": str(e)})


def response(status_code, body):
    """Helper to format API Gateway response"""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }


def upload_image(event):
    """
    Task 1.1: Upload image with metadata
    Expected Body: {"data": "base64string", "filename": "x.png", "owner": "y", "category": "z"}
    """
    body = json.loads(event.get('body', '{}'))

    # Validation
    if 'data' not in body or 'filename' not in body:
        return response(400, {"error": "Missing data or filename"})

    image_id = str(uuid.uuid4())
    image_data = base64.b64decode(body['data'])
    filename = body['filename']

    # 1. Upload to S3
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=image_id,
        Body=image_data,
        ContentType='image/jpeg'  # Simplification
    )

    # 2. Save Metadata to DynamoDB
    metadata = {
        'image_id': image_id,
        'filename': filename,
        'owner': body.get('owner', 'unknown'),
        'category': body.get('category', 'general'),
        'upload_date': datetime.now().isoformat()
    }
    table.put_item(Item=metadata)

    return response(201, {"message": "Image uploaded", "id": image_id, "metadata": metadata})


def list_images(event):
    """
    Task 1.2: List images with filters
    Supports filtering by 'owner' and 'category' via query parameters
    """
    params = event.get('queryStringParameters') or {}

    # Build DynamoDB Scan Filter
    scan_kwargs = {}
    filter_expression = None
    expression_values = {}
    expression_names = {}  # To handle reserved words if any

    filters = []

    if 'owner' in params:
        filters.append("#o = :o")
        expression_values[':o'] = params['owner']
        expression_names['#o'] = 'owner'

    if 'category' in params:
        filters.append("#c = :c")
        expression_values[':c'] = params['category']
        expression_names['#c'] = 'category'

    if filters:
        scan_kwargs['FilterExpression'] = " AND ".join(filters)
        scan_kwargs['ExpressionAttributeValues'] = expression_values
        scan_kwargs['ExpressionAttributeNames'] = expression_names

    # Perform Scan
    result = table.scan(**scan_kwargs)
    return response(200, {"count": result['Count'], "items": result['Items']})


def get_image(image_id):
    """
    Task 1.3: View/Download image
    Returns a Presigned URL for temporary access
    """
    # Check if exists in DB first
    db_item = table.get_item(Key={'image_id': image_id})
    if 'Item' not in db_item:
        return response(404, {"error": "Image not found"})

    # Generate Presigned URL
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET, 'Key': image_id},
        ExpiresIn=3600
    )

    return response(200, {"image_id": image_id, "download_url": url, "metadata": db_item['Item']})


def delete_image(image_id):
    """
    Task 1.4: Delete image
    """
    # 1. Delete from S3
    s3.delete_object(Bucket=S3_BUCKET, Key=image_id)

    # 2. Delete from DynamoDB
    table.delete_item(Key={'image_id': image_id})

    return response(200, {"message": f"Image {image_id} deleted successfully"})