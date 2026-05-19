import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# Upload a simple test file
s3.put_object(
    Bucket=S3_BUCKET_NAME,
    Key="uploads/test-upload.txt",
    Body=b"Hello from FastAPI S3 Task 3!",
    ContentType="text/plain",
)

print(f"Upload successful!")
print(f"Bucket : {S3_BUCKET_NAME}")
print(f"Key    : uploads/test-upload.txt")
print(f"URL    : https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/uploads/test-upload.txt")
