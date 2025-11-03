"""Context engineering service."""
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy import create_engine, select, update, delete, func as sql_func
from sqlalchemy.engine import Engine

from core.config import settings
from db.models import contexts, context_layers, context_versions, context_dictionaries, context_documents, orgs
from domains.context.models import ContextLayer, ContextSpec, ContextVersion, ContextDictionary
from services.versioning.snapshot import Snapshotter
from services.datasets.storage import LocalStore
from services.documents.processor import compute_sha256, extract_text_from_file, get_file_size
from services.documents.summarization import DocumentSummarizer
from fastapi import UploadFile
from pathlib import Path
import io


class ContextService:
    """Service for managing contexts, layers, dictionaries, and versions."""
    
    def __init__(self):
        self.engine: Engine = create_engine(settings.database_url)
        self.snapshotter = Snapshotter()
        self.storage = LocalStore(root="var/objects")
        self.summarizer = DocumentSummarizer()
    
    def _get_org_id(self, org_name: str) -> UUID:
        """Look up org ID by name, or create if it doesn't exist."""
        with self.engine.connect() as conn:
            result = conn.execute(
                select(orgs).where(orgs.c.name == org_name)
            ).fetchone()
            
            if result:
                return result.id
            
            # Create org if it doesn't exist (for demo purposes)
            org_id = uuid.uuid4()
            with self.engine.begin() as conn:
                conn.execute(
                    orgs.insert().values(
                        id=org_id,
                        name=org_name
                    )
                )
            return org_id
    
    def create_context(
        self,
        name: str,
        org_id: str,
        description: Optional[str] = None,
        dataset_version_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new context."""
        context_id = uuid.uuid4()
        metadata = metadata or {}
        
        # Look up or create org
        org_uuid = self._get_org_id(org_id) if isinstance(org_id, str) else org_id
        
        with self.engine.begin() as conn:
            conn.execute(
                contexts.insert().values(
                    id=context_id,
                    org_id=org_uuid,
                    name=name,
                    description=description,
                    metadata=metadata
                )
            )
        
        return {
            "context_id": str(context_id),
            "name": name,
            "description": description,
            "status": "created"
        }
    
    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Get a context by ID."""
        with self.engine.connect() as conn:
            result = conn.execute(
                select(contexts).where(contexts.c.id == UUID(context_id))
            ).fetchone()
            
            if not result:
                return None
            
            return dict(result._mapping)
    
    def list_contexts(self, org_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all contexts, optionally filtered by org_id."""
        with self.engine.connect() as conn:
            query = select(contexts)
            if org_id:
                org_uuid = self._get_org_id(org_id)
                query = query.where(contexts.c.org_id == org_uuid)
            query = query.order_by(contexts.c.created_at.desc())
            
            results = conn.execute(query).fetchall()
            return [dict(row._mapping) for row in results]
    
    def add_layer(
        self,
        context_id: str,
        kind: str,
        name: str,
        spec: Dict[str, Any],
        enabled: bool = True
    ) -> Dict[str, Any]:
        """Add a layer to a context."""
        # Validate context exists
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        
        # Get next order value
        with self.engine.connect() as conn:
            max_order = conn.execute(
                select(sql_func.max(context_layers.c.order))
                .where(context_layers.c.context_id == UUID(context_id))
            ).scalar() or -1
        
        layer_id = uuid.uuid4()
        
        with self.engine.begin() as conn:
            conn.execute(
                context_layers.insert().values(
                    id=layer_id,
                    context_id=UUID(context_id),
                    kind=kind,
                    name=name,
                    spec=spec,
                    enabled=enabled,
                    order=max_order + 1
                )
            )
        
        return {
            "layer_id": str(layer_id),
            "context_id": context_id,
            "kind": kind,
            "name": name,
            "spec": spec,
            "enabled": enabled
        }
    
    def get_layers(self, context_id: str) -> List[Dict[str, Any]]:
        """Get all layers for a context."""
        with self.engine.connect() as conn:
            results = conn.execute(
                select(context_layers)
                .where(context_layers.c.context_id == UUID(context_id))
                .order_by(context_layers.c.order.asc())
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def update_layer(
        self,
        layer_id: str,
        enabled: Optional[bool] = None,
        spec: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update a layer."""
        updates = {}
        if enabled is not None:
            updates["enabled"] = enabled
        if spec is not None:
            updates["spec"] = spec
        
        if not updates:
            raise ValueError("No updates provided")
        
        with self.engine.begin() as conn:
            conn.execute(
                update(context_layers)
                .where(context_layers.c.id == UUID(layer_id))
                .values(**updates)
            )
        
        # Fetch updated layer
        with self.engine.connect() as conn:
            result = conn.execute(
                select(context_layers).where(context_layers.c.id == UUID(layer_id))
            ).fetchone()
            
            return dict(result._mapping) if result else None
    
    def delete_layer(self, layer_id: str) -> bool:
        """Delete a layer."""
        with self.engine.begin() as conn:
            result = conn.execute(
                delete(context_layers).where(context_layers.c.id == UUID(layer_id))
            )
            return result.rowcount > 0
    
    def upsert_dictionary(
        self,
        context_id: str,
        name: str,
        entries: Dict[str, str]
    ) -> Dict[str, Any]:
        """Upsert a dictionary for a context."""
        # Validate context exists
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        
        # Check if dictionary exists
        with self.engine.connect() as conn:
            existing = conn.execute(
                select(context_dictionaries)
                .where(
                    context_dictionaries.c.context_id == UUID(context_id),
                    context_dictionaries.c.name == name
                )
            ).fetchone()
        
        if existing:
            # Update existing
            with self.engine.begin() as conn:
                conn.execute(
                    update(context_dictionaries)
                    .where(
                        context_dictionaries.c.context_id == UUID(context_id),
                        context_dictionaries.c.name == name
                    )
                    .values(entries=entries, updated_at=datetime.now())
                )
        else:
            # Create new
            dict_id = uuid.uuid4()
            with self.engine.begin() as conn:
                conn.execute(
                    context_dictionaries.insert().values(
                        id=dict_id,
                        context_id=UUID(context_id),
                        name=name,
                        entries=entries
                    )
                )
        
        return {
            "context_id": context_id,
            "name": name,
            "entries": entries
        }
    
    def get_dictionaries(self, context_id: str) -> List[Dict[str, Any]]:
        """Get all dictionaries for a context."""
        with self.engine.connect() as conn:
            results = conn.execute(
                select(context_dictionaries)
                .where(context_dictionaries.c.context_id == UUID(context_id))
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def create_version(
        self,
        context_id: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a versioned snapshot of the context."""
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        
        # Get all layers
        layers = self.get_layers(context_id)
        # Get all dictionaries
        dictionaries = self.get_dictionaries(context_id)
        
        # Get dataset version IDs from context metadata or layers
        dataset_version_ids = context.get("metadata", {}).get("dataset_version_ids", [])
        
        # Build layer data for digest
        layer_data = [
            {
                "kind": layer["kind"],
                "name": layer["name"],
                "spec": layer["spec"],
                "enabled": layer["enabled"]
            }
            for layer in layers if layer.get("enabled", True)
        ]
        
        # Compute digest
        digest = self.snapshotter.compute_context_digest(
            dataset_version_ids=dataset_version_ids,
            layers=layer_data,
            metadata=context.get("metadata", {})
        )
        
        # Get next version number
        with self.engine.connect() as conn:
            version_count = conn.execute(
                select(sql_func.count(context_versions.c.id))
                .where(context_versions.c.context_id == UUID(context_id))
            ).scalar() or 0
        
        version_str = f"{version_count + 1}"
        
        # Build data_refs (dataset versions, personas, MCP tools from layers)
        data_refs = dataset_version_ids.copy()
        for layer in layers:
            if layer["kind"] == "persona" and "persona_id" in layer.get("spec", {}):
                data_refs.append(f"persona:{layer['spec']['persona_id']}")
            elif layer["kind"] == "mcp" and "tool_name" in layer.get("spec", {}):
                data_refs.append(f"mcp:{layer['spec']['tool_name']}")
        
        version_id = uuid.uuid4()
        
        with self.engine.begin() as conn:
            conn.execute(
                context_versions.insert().values(
                    id=version_id,
                    context_id=UUID(context_id),
                    version=version_str,
                    digest=digest,
                    data_refs=data_refs,
                    layers=layer_data,
                    diff_summary=message
                )
            )
        
        return {
            "context_id": context_id,
            "version_id": str(version_id),
            "version": version_str,
            "digest": digest,
            "message": message
        }
    
    def get_versions(self, context_id: str) -> List[Dict[str, Any]]:
        """Get all versions for a context."""
        with self.engine.connect() as conn:
            results = conn.execute(
                select(context_versions)
                .where(context_versions.c.context_id == UUID(context_id))
                .order_by(context_versions.c.created_at.desc())
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def get_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific version."""
        with self.engine.connect() as conn:
            result = conn.execute(
                select(context_versions).where(context_versions.c.id == UUID(version_id))
            ).fetchone()
            
            return dict(result._mapping) if result else None
    
    def export_context_pack(
        self,
        context_id: str,
        version_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export a context pack as JSON."""
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        
        layers = self.get_layers(context_id)
        dictionaries = self.get_dictionaries(context_id)
        
        version_data = None
        if version_id:
            version_data = self.get_version(version_id)
        else:
            # Get latest version
            versions = self.get_versions(context_id)
            if versions:
                version_data = versions[0]
        
        pack = {
            "context": {
                "id": str(context["id"]),
                "name": context["name"],
                "description": context.get("description"),
                "metadata": context.get("metadata", {})
            },
            "layers": [
                {
                    "kind": layer["kind"],
                    "name": layer["name"],
                    "spec": layer["spec"],
                    "enabled": layer.get("enabled", True)
                }
                for layer in layers
            ],
            "dictionaries": [
                {
                    "name": dict_data["name"],
                    "entries": dict_data["entries"]
                }
                for dict_data in dictionaries
            ],
            "version": {
                "id": str(version_data["id"]) if version_data else None,
                "version": version_data["version"] if version_data else None,
                "digest": version_data["digest"] if version_data else None,
                "created_at": version_data["created_at"].isoformat() if version_data and version_data.get("created_at") else None
            } if version_data else None
        }
        
        return pack
    
    async def upload_document(
        self,
        context_id: str,
        file: UploadFile,
        name: Optional[str] = None,
        auto_summarize: bool = True
    ) -> Dict[str, Any]:
        """Upload a document to a context."""
        import logging
        logger = logging.getLogger(__name__)
        
        context = self.get_context(context_id)
        if not context:
            raise ValueError(f"Context not found: {context_id}")
        
        # Validate filename
        filename = file.filename or "unnamed_file"
        if not filename or filename.strip() == "":
            filename = "unnamed_file"
        
        # Read file content
        content = await file.read()
        
        if not content:
            raise ValueError("Uploaded file is empty")
        
        # Compute hash
        sha256_hash = compute_sha256(io.BytesIO(content))
        
        # Sanitize filename for storage
        safe_filename = filename.replace("/", "_").replace("\\", "_").replace("..", "_")
        if len(safe_filename) > 255:
            safe_filename = safe_filename[:255]
        
        # Generate storage key
        storage_key = f"contexts/{context_id}/{sha256_hash[:16]}_{safe_filename}"
        
        # Store file
        file_io = io.BytesIO(content)
        storage_path = self.storage.put(storage_key, file_io, file.content_type or "application/octet-stream")
        
        # Extract text content
        text_content = extract_text_from_file(safe_filename, content, file.content_type or "")
        
        # Generate summary if requested
        summary = None
        if auto_summarize and text_content:
            try:
                summary = self.summarizer.summarize(text_content, style="concise")
            except Exception as e:
                logger.warning(f"Failed to generate summary: {e}")
                summary = None
        
        # Create document record
        doc_id = uuid.uuid4()
        doc_name = name or filename
        
        with self.engine.begin() as conn:
            conn.execute(
                context_documents.insert().values(
                    id=doc_id,
                    context_id=UUID(context_id),
                    name=doc_name,
                    filename=filename,
                    storage_path=storage_path,
                    content_type=file.content_type or "application/octet-stream",
                    file_size=len(content),
                    sha256=sha256_hash,
                    summary=summary,
                    text_content=text_content[:10000] if text_content else None,  # Store first 10k chars
                    metadata={}
                )
            )
        
        return {
            "document_id": str(doc_id),
            "context_id": context_id,
            "name": doc_name,
            "filename": filename,
            "file_size": len(content),
            "summary": summary,
            "sha256": sha256_hash
        }
    
    def get_documents(self, context_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a context."""
        with self.engine.connect() as conn:
            results = conn.execute(
                select(context_documents)
                .where(context_documents.c.context_id == UUID(context_id))
                .order_by(context_documents.c.created_at.desc())
            ).fetchall()
            
            return [dict(row._mapping) for row in results]
    
    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document."""
        with self.engine.connect() as conn:
            result = conn.execute(
                select(context_documents).where(context_documents.c.id == UUID(document_id))
            ).fetchone()
            
            return dict(result._mapping) if result else None
    
    def summarize_document(self, document_id: str, style: str = "concise") -> Optional[str]:
        """Generate or regenerate summary for a document."""
        import logging
        logger = logging.getLogger(__name__)
        
        document = self.get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        logger.info(f"Summarizing document {document_id}, filename: {document.get('filename')}")
        
        text = document.get("text_content")
        if not text:
            # Try to read from storage
            logger.debug(f"No text_content in DB, reading from storage: {document.get('storage_path')}")
            try:
                file_io = self.storage.get(document["storage_path"])
                content = file_io.read()
                text = extract_text_from_file(document["filename"], content, document.get("content_type", ""))
                logger.debug(f"Extracted {len(text) if text else 0} characters from storage")
            except Exception as e:
                logger.warning(f"Failed to read from storage: {e}")
                pass
        
        if not text:
            logger.warning(f"No extractable text found for document {document_id}")
            return None
        
        if len(text.strip()) < 50:
            logger.warning(f"Text too short ({len(text)} chars) for summarization")
            return None
        
        try:
            summary = self.summarizer.summarize(text, style=style)
            
            if summary:
                # Update document with new summary
                with self.engine.begin() as conn:
                    conn.execute(
                        update(context_documents)
                        .where(context_documents.c.id == UUID(document_id))
                        .values(summary=summary)
                    )
                logger.info(f"Summary generated and saved for document {document_id}")
                return summary
            else:
                logger.warning(f"Summarizer returned None for document {document_id}")
                return None
        except Exception as e:
            logger.error(f"Error during summarization: {e}", exc_info=True)
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        document = self.get_document(document_id)
        if not document:
            return False
        
        # Delete from storage
        try:
            storage_path = Path(document["storage_path"])
            if storage_path.exists():
                storage_path.unlink()
        except:
            pass  # Continue even if file delete fails
        
        # Delete from database
        with self.engine.begin() as conn:
            result = conn.execute(
                delete(context_documents).where(context_documents.c.id == UUID(document_id))
            )
            return result.rowcount > 0

