"""S3-compatible object storage client."""
import json
import logging
from typing import Optional, BinaryIO, Union
from io import BytesIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from core.config import settings

logger = logging.getLogger(__name__)


class ObjectStoreClient:
    """S3-compatible object storage client for MinIO/S3."""
    
    _instance: Optional["ObjectStoreClient"] = None
    
    def __init__(self):
        """Initialize S3 client with settings."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1',  # Required but ignored for MinIO
            use_ssl=settings.s3_use_ssl
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket()
    
    @classmethod
    def get_instance(cls) -> "ObjectStoreClient":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _ensure_bucket(self):
        """Ensure the bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code in ('404', 'NoSuchBucket'):
                logger.info(f"Creating bucket: {self.bucket}")
                self.client.create_bucket(Bucket=self.bucket)
            else:
                logger.warning(f"Could not check bucket: {e}")
    
    def put_json(self, key: str, data: dict) -> str:
        """
        Write JSON object and return full S3 URI.
        
        Args:
            key: Object key (path within bucket)
            data: Dictionary to serialize as JSON
            
        Returns:
            Full S3 URI (s3://bucket/key)
        """
        body = json.dumps(data, indent=2, default=str)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=body.encode('utf-8'),
            ContentType='application/json'
        )
        logger.debug(f"Wrote JSON to s3://{self.bucket}/{key}")
        return f"s3://{self.bucket}/{key}"
    
    def get_json(self, key: str) -> dict:
        """
        Read JSON object from storage.
        
        Args:
            key: Object key (can be full URI or just key)
            
        Returns:
            Parsed JSON as dictionary
        """
        key = self._normalize_key(key)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    
    def put_text(self, key: str, text: str) -> str:
        """
        Write text file and return full S3 URI.
        
        Args:
            key: Object key
            text: Text content
            
        Returns:
            Full S3 URI
        """
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=text.encode('utf-8'),
            ContentType='text/plain'
        )
        logger.debug(f"Wrote text to s3://{self.bucket}/{key}")
        return f"s3://{self.bucket}/{key}"
    
    def get_text(self, key: str) -> str:
        """
        Read text file from storage.
        
        Args:
            key: Object key (can be full URI or just key)
            
        Returns:
            Text content
        """
        key = self._normalize_key(key)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read().decode('utf-8')
    
    def put_bytes(self, key: str, data: bytes, content_type: str = 'application/octet-stream') -> str:
        """
        Write binary data and return full S3 URI.
        
        Args:
            key: Object key
            data: Binary data
            content_type: MIME type
            
        Returns:
            Full S3 URI
        """
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        logger.debug(f"Wrote bytes to s3://{self.bucket}/{key}")
        return f"s3://{self.bucket}/{key}"
    
    def get_bytes(self, key: str) -> bytes:
        """
        Read binary data from storage.
        
        Args:
            key: Object key
            
        Returns:
            Binary content
        """
        key = self._normalize_key(key)
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
    
    def upload_file(self, key: str, file_obj: BinaryIO, content_type: str = 'application/octet-stream') -> str:
        """
        Upload a file object.
        
        Args:
            key: Object key
            file_obj: File-like object
            content_type: MIME type
            
        Returns:
            Full S3 URI
        """
        self.client.upload_fileobj(
            file_obj, 
            self.bucket, 
            key,
            ExtraArgs={'ContentType': content_type}
        )
        logger.debug(f"Uploaded file to s3://{self.bucket}/{key}")
        return f"s3://{self.bucket}/{key}"
    
    def download_file(self, key: str, file_obj: BinaryIO) -> None:
        """
        Download to a file object.
        
        Args:
            key: Object key
            file_obj: File-like object to write to
        """
        key = self._normalize_key(key)
        self.client.download_fileobj(self.bucket, key, file_obj)
    
    def exists(self, key: str) -> bool:
        """
        Check if object exists.
        
        Args:
            key: Object key
            
        Returns:
            True if object exists
        """
        key = self._normalize_key(key)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete an object.
        
        Args:
            key: Object key
            
        Returns:
            True if deleted successfully
        """
        key = self._normalize_key(key)
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {key}: {e}")
            return False
    
    def list_objects(self, prefix: str, max_keys: int = 1000) -> list[dict]:
        """
        List objects with given prefix.
        
        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return
            
        Returns:
            List of object metadata dicts with 'Key', 'Size', 'LastModified'
        """
        prefix = self._normalize_key(prefix)
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=prefix,
            MaxKeys=max_keys
        )
        return response.get('Contents', [])
    
    def generate_presigned_url(self, key: str, expires_in: int = 3600, method: str = 'get_object') -> str:
        """
        Generate a presigned URL for temporary access.
        
        Args:
            key: Object key
            expires_in: URL validity in seconds (default 1 hour)
            method: 'get_object' for download, 'put_object' for upload
            
        Returns:
            Presigned URL string
        """
        key = self._normalize_key(key)
        return self.client.generate_presigned_url(
            method,
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )
    
    def copy_object(self, source_key: str, dest_key: str) -> str:
        """
        Copy an object within the bucket.
        
        Args:
            source_key: Source object key
            dest_key: Destination object key
            
        Returns:
            Full S3 URI of destination
        """
        source_key = self._normalize_key(source_key)
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource={'Bucket': self.bucket, 'Key': source_key},
            Key=dest_key
        )
        return f"s3://{self.bucket}/{dest_key}"
    
    def get_uri(self, key: str) -> str:
        """
        Get full S3 URI for a key.
        
        Args:
            key: Object key
            
        Returns:
            Full S3 URI
        """
        return f"s3://{self.bucket}/{key}"
    
    def _normalize_key(self, key: str) -> str:
        """
        Normalize key by stripping S3 URI prefix if present.
        
        Args:
            key: Object key or full S3 URI
            
        Returns:
            Just the key part
        """
        if key.startswith('s3://'):
            # s3://bucket/key -> key
            parts = key[5:].split('/', 1)
            if len(parts) > 1:
                return parts[1]
        return key


# Convenience function
def get_object_store() -> ObjectStoreClient:
    """Get the object store client singleton."""
    return ObjectStoreClient.get_instance()
