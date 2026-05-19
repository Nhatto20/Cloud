import os
import uuid
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


def _get_s3_client():
    """Return a boto3 S3 client using credentials from environment."""
    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def upload_file_to_s3(
    file_bytes: bytes,
    original_filename: str,
    content_type: str,
    folder: str = "uploads",
) -> dict:
    """
    Upload raw bytes to S3.

    Returns a dict with:
        - key          : the S3 object key
        - bucket       : bucket name
        - url          : public-style URL (bucket may be private; use presigned URL for access)
        - filename     : the original filename
        - size         : bytes uploaded
    """
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")

    # Build a unique key so same-named files don't overwrite each other
    unique_prefix = uuid.uuid4().hex[:8]
    safe_name = original_filename.replace(" ", "_")
    key = f"{folder}/{unique_prefix}_{safe_name}"

    s3 = _get_s3_client()
    try:
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 upload failed: {exc}") from exc

    return {
        "key": key,
        "bucket": S3_BUCKET_NAME,
        "url": f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}",
        "filename": original_filename,
        "size": len(file_bytes),
    }


def generate_presigned_url(key: str, expiry_seconds: int = 3600) -> str:
    """Return a time-limited presigned URL for downloading an S3 object."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")

    s3 = _get_s3_client()
    try:
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expiry_seconds,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Could not generate presigned URL: {exc}") from exc

    return url


def list_bucket_files(prefix: str = "uploads/") -> list[dict]:
    """List objects in the bucket under *prefix*."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")

    s3 = _get_s3_client()
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=prefix)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"Could not list bucket: {exc}") from exc

    contents = response.get("Contents", [])
    return [
        {
            "key": obj["Key"],
            "size": obj["Size"],
            "last_modified": obj["LastModified"].isoformat(),
        }
        for obj in contents
    ]


def delete_file_from_s3(key: str) -> bool:
    """Delete an object from S3. Returns True on success."""
    if not S3_BUCKET_NAME:
        raise ValueError("S3_BUCKET_NAME environment variable is not set")

    s3 = _get_s3_client()
    try:
        s3.delete_object(Bucket=S3_BUCKET_NAME, Key=key)
        return True
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"S3 delete failed: {exc}") from exc
