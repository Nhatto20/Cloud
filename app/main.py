from fastapi import FastAPI

from app.db import check_db_connection
from app.routers.upload import router as upload_router

app = FastAPI(
    title="FastAPI Cloud – RDS + S3",
    version="1.0.0",
    description="FastAPI application with Amazon RDS (PostgreSQL) and Amazon S3 integration.",
)

app.include_router(upload_router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "FastAPI Cloud (RDS + S3) is running"}


@app.get("/health", tags=["Health"])
def health_check():
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected",
    }
