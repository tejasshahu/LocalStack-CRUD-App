# Problem Statement
You are developing the service layer of an application like Instagram. 
You are working on a module which is responsible for supporting image upload 
and storage in the Cloud. Along with the image, its metadata must be persisted
in a NoSQL storage. Multiple users are going to use this service at the same 
time. For this reason, the service should be scalable.
The team currently uses API Gateway, Lambda Functions, S3 and DynamoDB services.

Language: Python3.7+

Tasks:
1. Create APIs for:
   1. Uploading image with metadata
   2. List all images, support at least two filters to search
   3. View/download image
   4. Delete an image
2. Write unit tests to cover all scenarios.
3. API documentation and usage instructions.

### Prerequisites
- LocalStack CLI,
- LocalStack Web Application account & Auth Token
- Docker
- Python 3.9.6+ & pip
- AWS CLI & awslocal wrapper
- `curl` (for testing)

## Serverless Image Service (LocalStack)
A Dockerized Python application using API Gateway, Lambda, S3, and DynamoDB.

## Setup and Run
1. Start the application:
   ```bash
   docker-compose up --build
2. To Run Test cases:
   ```
   python3 -m unittest tests/test_handler.py
   ```