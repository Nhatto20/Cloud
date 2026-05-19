import os
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse

from app.s3_service import (
    delete_file_from_s3,
    generate_presigned_url,
    list_bucket_files,
    upload_file_to_s3,
)

router = APIRouter(prefix="/files", tags=["File Storage (S3)"])

# Max upload size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
}


@router.post("/upload", summary="Upload a file to S3")
async def upload_file(
    file: UploadFile = File(..., description="File to upload (max 10 MB)"),
    folder: str = Query("uploads", description="S3 folder / prefix"),
):
    """
    Upload a file to the configured S3 bucket.

    - Returns the S3 **key**, **bucket**, a public-style **url**, and file metadata.
    - Use the `/files/download` endpoint to get a presigned download URL.
    """
    # --- size guard ---
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    # --- content-type guard ---
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{content_type}'. "
            f"Allowed: {sorted(ALLOWED_CONTENT_TYPES)}",
        )

    try:
        result = upload_file_to_s3(
            file_bytes=content,
            original_filename=file.filename or "unnamed",
            content_type=content_type,
            folder=folder,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(status_code=201, content={"success": True, **result})


@router.get("/download", summary="Get a presigned download URL for an S3 object")
def download_file(
    key: str = Query(..., description="S3 object key returned from /upload"),
    expiry: int = Query(3600, description="URL validity in seconds (default 1 hour)"),
):
    """
    Generate a time-limited presigned URL so a client can download the file
    directly from S3 without exposing credentials.
    """
    try:
        url = generate_presigned_url(key=key, expiry_seconds=expiry)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"key": key, "download_url": url, "expires_in_seconds": expiry}


@router.get("/list", summary="List files stored in S3")
def list_files(
    prefix: str = Query("uploads/", description="S3 key prefix to filter by"),
):
    """List all objects in the S3 bucket under the given prefix."""
    try:
        files = list_bucket_files(prefix=prefix)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"prefix": prefix, "count": len(files), "files": files}


@router.delete("/delete", summary="Delete a file from S3")
def delete_file(
    key: str = Query(..., description="S3 object key to delete"),
):
    """Permanently delete an object from the S3 bucket."""
    try:
        delete_file_from_s3(key=key)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"success": True, "deleted_key": key}
