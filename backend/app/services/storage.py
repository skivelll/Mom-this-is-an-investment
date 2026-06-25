from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.core.config import Settings

ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


@dataclass(frozen=True, slots=True)
class PresignedUpload:
    object_key: str
    upload_url: str
    public_url: str
    headers: dict[str, str]
    expires_in: int


class S3Storage:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def public_url(self, object_key: str) -> str:
        base_url = self._settings.s3_public_base_url.rstrip("/")
        if base_url:
            return f"{base_url}/{object_key}"
        endpoint = self._settings.s3_endpoint_url.rstrip("/")
        return f"{endpoint}/{self._settings.s3_bucket}/{object_key}"

    def create_presigned_upload(
        self,
        *,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
    ) -> PresignedUpload:
        if mime_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise ValueError("Unsupported media type.")
        if size_bytes > self._settings.media_max_upload_size_bytes:
            raise ValueError("File is too large.")

        object_key = self._object_key(original_filename=original_filename)
        client = self._client()
        upload_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self._settings.s3_bucket,
                "Key": object_key,
                "ContentType": mime_type,
            },
            ExpiresIn=self._settings.media_presigned_url_ttl_seconds,
        )
        return PresignedUpload(
            object_key=object_key,
            upload_url=str(upload_url),
            public_url=self.public_url(object_key),
            headers={"Content-Type": mime_type},
            expires_in=self._settings.media_presigned_url_ttl_seconds,
        )

    def _client(self) -> Any:
        import boto3  # type: ignore[import-not-found]

        return boto3.client(
            "s3",
            endpoint_url=self._settings.s3_endpoint_url or None,
            aws_access_key_id=self._settings.s3_access_key or None,
            aws_secret_access_key=self._settings.s3_secret_key or None,
            region_name=self._settings.s3_region,
            use_ssl=self._settings.s3_use_ssl,
        )

    def _object_key(self, *, original_filename: str) -> str:
        suffix = _safe_suffix(original_filename)
        return f"catalog/{uuid4().hex}{suffix}"


def _safe_suffix(filename: str) -> str:
    lowered = filename.lower()
    for suffix in (".jpg", ".jpeg", ".png", ".webp"):
        if lowered.endswith(suffix):
            return suffix
    return ""
