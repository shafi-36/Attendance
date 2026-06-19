"""MinIO object storage service."""
import io
import logging

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

logger = logging.getLogger(__name__)
_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        settings = get_settings()
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        _ensure_bucket(_client, settings.minio_bucket)
    return _client


def _ensure_bucket(client: Minio, bucket: str) -> None:
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info("Created MinIO bucket: %s", bucket)
    except S3Error as exc:
        logger.error("MinIO bucket error: %s", exc)
        raise


def upload_image(roll_no: str, image_bytes: bytes, filename: str = "profile.jpg") -> str:
    """Upload student face image and return the object path (key)."""
    settings = get_settings()
    client = get_minio_client()
    object_name = f"students/{roll_no}/{filename}"
    client.put_object(
        settings.minio_bucket,
        object_name,
        io.BytesIO(image_bytes),
        length=len(image_bytes),
        content_type="image/jpeg",
    )
    logger.info("Uploaded image to MinIO: %s", object_name)
    return object_name


def get_presigned_url(object_name: str, expires_seconds: int = 3600) -> str:
    """Return a presigned URL for temporary access."""
    from datetime import timedelta

    settings = get_settings()
    client = get_minio_client()
    try:
        url = client.presigned_get_object(
            settings.minio_bucket,
            object_name,
            expires=timedelta(seconds=expires_seconds),
        )
        return url
    except S3Error as exc:
        logger.error("Failed to get presigned URL: %s", exc)
        return ""


def delete_image(object_name: str) -> None:
    """Delete an object from MinIO."""
    settings = get_settings()
    client = get_minio_client()
    try:
        client.remove_object(settings.minio_bucket, object_name)
        logger.info("Deleted MinIO object: %s", object_name)
    except S3Error as exc:
        logger.warning("Could not delete MinIO object %s: %s", object_name, exc)
