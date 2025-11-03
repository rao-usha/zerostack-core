"""Object storage interface for datasets."""
from typing import Protocol, BinaryIO
from pathlib import Path
import os
import hashlib
import io


class ObjectStore(Protocol):
    """Protocol for object storage backends."""
    
    def put(self, key: str, fp: BinaryIO, content_type: str) -> str:
        """Store a file and return its storage path/URL."""
        ...
    
    def get(self, key: str) -> BinaryIO:
        """Retrieve a file by key."""
        ...
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...


class LocalStore:
    """Write files under ./var/objects; replace with S3 later."""
    
    def __init__(self, root: str = "var/objects"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
    
    def put(self, key: str, fp: BinaryIO, content_type: str) -> str:
        """
        Store a file and return its storage path.
        
        TODO: Implement file streaming to disk, compute sha256.
        """
        # Stub: create the file path
        file_path = self.root / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # TODO: Stream fp to file_path, compute sha256
        with open(file_path, 'wb') as f:
            content = fp.read()
            f.write(content)
        
        return str(file_path)
    
    def get(self, key: str) -> BinaryIO:
        """
        Retrieve a file by key.
        
        TODO: Implement file retrieval.
        """
        file_path = self.root / key
        if not file_path.exists():
            raise FileNotFoundError(f"Key not found: {key}")
        
        with open(file_path, 'rb') as f:
            return io.BytesIO(f.read())
    
    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        file_path = self.root / key
        return file_path.exists()

