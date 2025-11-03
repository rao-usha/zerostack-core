"""Content-addressed versioning utilities."""
import json
import hashlib
from typing import Dict, Any


class Snapshotter:
    """
    Create digest = sha256(json.dumps({
        "dataset_version_ids": [...],
        "layers": [each layer's kind/name/spec/enabled],
        "metadata": {...}
    }, sort_keys=True))
    """
    
    def create(self, obj: dict) -> dict:
        """
        Create a content-addressed snapshot of an object.
        
        Args:
            obj: Dictionary containing dataset_version_ids, layers, metadata
            
        Returns:
            Dictionary with digest and snapshot data
            
        TODO: Implement proper digest computation with deterministic JSON serialization.
        """
        # Stub: compute digest from the object
        # TODO: Use json.dumps with sort_keys=True for deterministic serialization
        serialized = json.dumps(obj, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
        
        return {
            "digest": digest,
            "snapshot": obj,
            "serialized": serialized
        }
    
    def compute_context_digest(
        self,
        dataset_version_ids: list[str],
        layers: list[dict],
        metadata: dict[str, Any] = None
    ) -> str:
        """
        Compute digest for a context specification.
        
        Args:
            dataset_version_ids: List of dataset version IDs
            layers: List of layer dictionaries (with kind, name, spec, enabled)
            metadata: Optional metadata dictionary
            
        Returns:
            SHA256 digest string
        """
        metadata = metadata or {}
        
        # Normalize layers to include only relevant fields
        normalized_layers = [
            {
                "kind": layer.get("kind"),
                "name": layer.get("name"),
                "spec": layer.get("spec", {}),
                "enabled": layer.get("enabled", True)
            }
            for layer in layers
        ]
        
        obj = {
            "dataset_version_ids": sorted(dataset_version_ids),
            "layers": normalized_layers,
            "metadata": metadata
        }
        
        result = self.create(obj)
        return result["digest"]

