"""Storage abstraction for file uploads (local and Cloudflare R2)."""

import os
from abc import ABC, abstractmethod
from flask import current_app
import boto3
from botocore.config import Config


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def upload(self, file_data: bytes, key: str, content_type: str) -> str:
        """Upload a file and return its public URL."""
        pass

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Get the public URL for a stored file."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a file. Returns True if successful."""
        pass

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Download a file's contents."""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage for development."""

    def __init__(self, base_path: str, base_url: str):
        self.base_path = base_path
        self.base_url = base_url
        os.makedirs(base_path, exist_ok=True)

    def upload(self, file_data: bytes, key: str, content_type: str) -> str:
        """Save file to local filesystem."""
        file_path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            f.write(file_data)

        return self.get_url(key)

    def get_url(self, key: str) -> str:
        """Get URL for locally stored file."""
        return f"{self.base_url}/uploads/{key}"

    def delete(self, key: str) -> bool:
        """Delete file from local filesystem."""
        file_path = os.path.join(self.base_path, key)
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False

    def download(self, key: str) -> bytes:
        """Read file from local filesystem."""
        file_path = os.path.join(self.base_path, key)
        with open(file_path, 'rb') as f:
            return f.read()


class R2Storage(StorageBackend):
    """Cloudflare R2 storage for production."""

    def __init__(self, account_id: str, access_key: str, secret_key: str,
                 bucket_name: str, public_url: str):
        self.bucket_name = bucket_name
        self.public_url = public_url.rstrip('/')

        # R2 endpoint URL
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        # Create S3 client for R2
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version='s3v4',
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
        )

    def upload(self, file_data: bytes, key: str, content_type: str) -> str:
        """Upload file to R2."""
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=file_data,
            ContentType=content_type
        )
        return self.get_url(key)

    def get_url(self, key: str) -> str:
        """Get public URL for R2 object."""
        return f"{self.public_url}/{key}"

    def delete(self, key: str) -> bool:
        """Delete object from R2."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception:
            return False

    def download(self, key: str) -> bytes:
        """Download object from R2."""
        response = self.client.get_object(
            Bucket=self.bucket_name,
            Key=key
        )
        return response['Body'].read()


def get_storage() -> StorageBackend:
    """Get the configured storage backend."""
    backend = current_app.config.get('STORAGE_BACKEND', 'local')

    if backend == 'local':
        base_path = current_app.config.get('LOCAL_STORAGE_PATH', 'uploads')
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        return LocalStorage(base_path, base_url)

    elif backend == 'r2':
        return R2Storage(
            account_id=current_app.config['R2_ACCOUNT_ID'],
            access_key=current_app.config['R2_ACCESS_KEY_ID'],
            secret_key=current_app.config['R2_SECRET_ACCESS_KEY'],
            bucket_name=current_app.config['R2_BUCKET_NAME'],
            public_url=current_app.config['R2_PUBLIC_URL']
        )

    raise ValueError(f"Unknown storage backend: {backend}")
