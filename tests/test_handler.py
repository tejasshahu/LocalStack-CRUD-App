import unittest
import json
import os
from unittest.mock import MagicMock, patch

# Set env vars before importing main
os.environ['BUCKET_NAME'] = 'test-bucket'
os.environ['TABLE_NAME'] = 'test-table'
os.environ['AWS_REGION'] = 'us-east-1'

# Import application code
from app import main


class TestImageService(unittest.TestCase):

    def setUp(self):
        # Mock S3 Client
        self.mock_s3 = MagicMock()
        main.s3 = self.mock_s3

        # Mock DynamoDB Table
        self.mock_table = MagicMock()
        main.table = self.mock_table

    def test_upload_image_success(self):
        event = {
            'httpMethod': 'POST',
            'path': '/images',
            'body': json.dumps({
                "filename": "BeKind.jpeg",
                "data": "VGhpcyBpcyBhIHRlc3Q=",  # Base64 for "This is a test"
                "owner": "user1",
                "category": "nature"
            })
        }

        response = main.lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 201)
        self.mock_s3.put_object.assert_called_once()
        self.mock_table.put_item.assert_called_once()

    def test_list_images_with_filters(self):
        event = {
            'httpMethod': 'GET',
            'path': '/images',
            'queryStringParameters': {'owner': 'user1', 'category': 'nature'}
        }

        # Mock DynamoDB Scan return
        self.mock_table.scan.return_value = {'Count': 1, 'Items': [{'id': '123'}]}

        response = main.lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        # Verify filters were passed
        call_args = self.mock_table.scan.call_args[1]
        self.assertIn('FilterExpression', call_args)

    def test_get_image_not_found(self):
        event = {
            'httpMethod': 'GET',
            'path': '/images/999'
        }

        # Mock Item not found
        self.mock_table.get_item.return_value = {}

        response = main.lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 404)

    def test_delete_image(self):
        event = {
            'httpMethod': 'DELETE',
            'path': '/images/123'
        }

        response = main.lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        self.mock_s3.delete_object.assert_called_with(Bucket='test-bucket', Key='123')
        self.mock_table.delete_item.assert_called_with(Key={'image_id': '123'})


if __name__ == '__main__':
    unittest.main()