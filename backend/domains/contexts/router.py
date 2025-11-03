"""Context engineering API router."""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from domains.context.models import ContextLayer, ContextSpec, ContextVersion, ContextDictionary
from domains.contexts.service import ContextService

router = APIRouter(prefix="/contexts", tags=["contexts"])
context_service = ContextService()


class CreateContextReq(BaseModel):
    """Request to create a context."""
    name: str
    description: str | None = None
    dataset_version_ids: List[str] = []
    metadata: Dict[str, Any] = {}


@router.post("/")
def create_context(
    payload: CreateContextReq,
    x_org_id: str = Header(default="demo", alias="X-Org-ID")
):
    """Create a new context workspace."""
    try:
        metadata = payload.metadata.copy()
        if payload.dataset_version_ids:
            metadata["dataset_version_ids"] = payload.dataset_version_ids
        
        result = context_service.create_context(
            name=payload.name,
            org_id=x_org_id,
            description=payload.description,
            dataset_version_ids=payload.dataset_version_ids,
            metadata=metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def list_contexts(x_org_id: str = Header(default="demo", alias="X-Org-ID")):
    """List all contexts for an organization."""
    try:
        contexts_list = context_service.list_contexts(org_id=x_org_id)
        
        # Convert UUIDs to strings for JSON serialization
        result = []
        for ctx in contexts_list:
            ctx_dict = {
                "id": str(ctx["id"]),
                "name": ctx["name"],
                "description": ctx.get("description"),
                "metadata": ctx.get("metadata", {}),
                "created_at": ctx["created_at"].isoformat() if ctx.get("created_at") else None
            }
            result.append(ctx_dict)
        
        return {"contexts": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}")
def get_context(context_id: str):
    """Get a context by ID."""
    try:
        context = context_service.get_context(context_id)
        if not context:
            raise HTTPException(status_code=404, detail="Context not found")
        
        return {
            "id": str(context["id"]),
            "name": context["name"],
            "description": context.get("description"),
            "metadata": context.get("metadata", {}),
            "created_at": context["created_at"].isoformat() if context.get("created_at") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class AddLayerReq(BaseModel):
    """Request to add a layer to a context."""
    kind: str
    name: str
    spec: Dict[str, Any] = {}
    enabled: bool = True


@router.post("/{context_id}/layers")
def add_layer(context_id: str, layer: AddLayerReq):
    """Add a layer to a context."""
    try:
        result = context_service.add_layer(
            context_id=context_id,
            kind=layer.kind,
            name=layer.name,
            spec=layer.spec,
            enabled=layer.enabled
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}/layers")
def get_layers(context_id: str):
    """Get all layers for a context."""
    try:
        layers = context_service.get_layers(context_id)
        result = []
        for layer in layers:
            layer_dict = {
                "id": str(layer["id"]),
                "kind": layer["kind"],
                "name": layer["name"],
                "spec": layer["spec"],
                "enabled": layer.get("enabled", True),
                "order": layer.get("order", 0),
                "created_at": layer["created_at"].isoformat() if layer.get("created_at") else None
            }
            result.append(layer_dict)
        return {"layers": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateLayerReq(BaseModel):
    """Request to update a layer."""
    enabled: bool | None = None
    spec: Dict[str, Any] | None = None


@router.put("/layers/{layer_id}")
def update_layer(layer_id: str, req: UpdateLayerReq):
    """Update a layer."""
    try:
        result = context_service.update_layer(
            layer_id,
            enabled=req.enabled,
            spec=req.spec
        )
        if not result:
            raise HTTPException(status_code=404, detail="Layer not found")
        
        return {
            "id": str(result["id"]),
            "kind": result["kind"],
            "name": result["name"],
            "spec": result["spec"],
            "enabled": result.get("enabled", True)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/layers/{layer_id}")
def delete_layer(layer_id: str):
    """Delete a layer."""
    try:
        success = context_service.delete_layer(layer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Layer not found")
        return {"status": "deleted", "layer_id": layer_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateVersionReq(BaseModel):
    """Request to create a version."""
    message: str | None = None


@router.post("/{context_id}/version")
def create_version(context_id: str, req: CreateVersionReq | None = None):
    """Create a versioned snapshot of the context."""
    try:
        message = req.message if req else None
        result = context_service.create_version(context_id, message=message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}/versions")
def list_versions(context_id: str):
    """List all versions for a context."""
    try:
        versions = context_service.get_versions(context_id)
        result = []
        for version in versions:
            version_dict = {
                "id": str(version["id"]),
                "version": version["version"],
                "digest": version["digest"],
                "diff_summary": version.get("diff_summary"),
                "data_refs": version.get("data_refs", []),
                "layers": version.get("layers", []),
                "created_at": version["created_at"].isoformat() if version.get("created_at") else None
            }
            result.append(version_dict)
        return {"versions": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{version_id}")
def get_version(version_id: str):
    """Get a specific version."""
    try:
        version = context_service.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return {
            "id": str(version["id"]),
            "context_id": str(version["context_id"]),
            "version": version["version"],
            "digest": version["digest"],
            "diff_summary": version.get("diff_summary"),
            "data_refs": version.get("data_refs", []),
            "layers": version.get("layers", []),
            "created_at": version["created_at"].isoformat() if version.get("created_at") else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DictionaryReq(BaseModel):
    """Request to upsert a dictionary."""
    name: str
    entries: Dict[str, str] = {}  # term -> definition or mapping


@router.post("/{context_id}/dictionary")
def upsert_dictionary(context_id: str, body: DictionaryReq):
    """Upsert a dictionary for a context."""
    try:
        result = context_service.upsert_dictionary(
            context_id=context_id,
            name=body.name,
            entries=body.entries
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}/dictionaries")
def get_dictionaries(context_id: str):
    """Get all dictionaries for a context."""
    try:
        dictionaries = context_service.get_dictionaries(context_id)
        result = []
        for dict_data in dictionaries:
            dict_dict = {
                "id": str(dict_data["id"]),
                "name": dict_data["name"],
                "entries": dict_data["entries"],
                "created_at": dict_data["created_at"].isoformat() if dict_data.get("created_at") else None,
                "updated_at": dict_data.get("updated_at").isoformat() if dict_data.get("updated_at") else None
            }
            result.append(dict_dict)
        return {"dictionaries": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}/export")
def export_context_pack(context_id: str, version_id: str | None = None):
    """Export a context pack (JSON bundle with datasets, layers, dictionaries)."""
    try:
        pack = context_service.export_context_pack(context_id, version_id)
        return pack
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{context_id}/attach/persona/{persona_id}")
def attach_persona_layer(context_id: str, persona_id: str):
    """Attach a persona as a layer to a context."""
    try:
        result = context_service.add_layer(
            context_id=context_id,
            kind="persona",
            name=f"Persona: {persona_id}",
            spec={"persona_id": persona_id},
            enabled=True
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MCPLayerReq(BaseModel):
    """Request to attach an MCP tool layer."""
    params: Dict[str, Any] = {}


@router.post("/{context_id}/attach/mcp/{tool_name}")
def attach_mcp_layer(context_id: str, tool_name: str, req: MCPLayerReq | None = None):
    """Attach an MCP tool as a layer to a context."""
    try:
        params = req.params if req else {}
        result = context_service.add_layer(
            context_id=context_id,
            kind="mcp",
            name=f"MCP: {tool_name}",
            spec={"tool_name": tool_name, "params": params},
            enabled=True
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document endpoints

@router.post("/{context_id}/documents")
async def upload_document(
    context_id: str,
    file: UploadFile = File(...),
    name: str | None = Form(None),
    auto_summarize: bool = Form(True)
):
    """Upload a document to a context with optional auto-summarization."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Uploading document to context {context_id}, filename: {file.filename}, auto_summarize: {auto_summarize}")
        result = await context_service.upload_document(
            context_id=context_id,
            file=file,
            name=name,
            auto_summarize=auto_summarize
        )
        logger.info(f"Document uploaded successfully: {result.get('document_id')}")
        return result
    except ValueError as e:
        logger.error(f"ValueError in upload_document: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Exception in upload_document: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{context_id}/documents")
def get_documents(context_id: str):
    """Get all documents for a context."""
    try:
        documents = context_service.get_documents(context_id)
        result = []
        for doc in documents:
            doc_dict = {
                "id": str(doc["id"]),
                "name": doc["name"],
                "filename": doc["filename"],
                "file_size": doc.get("file_size", 0),
                "content_type": doc.get("content_type"),
                "summary": doc.get("summary"),
                "sha256": doc.get("sha256"),
                "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None
            }
            result.append(doc_dict)
        return {"documents": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/summarize")
def summarize_document(
    document_id: str, 
    style: str = Query("concise", description="Summary style: concise, detailed, or bullet_points")
):
    """Generate or regenerate summary for a document."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Summarizing document {document_id} with style: {style}")
        summary = context_service.summarize_document(document_id, style=style)
        if summary is None:
            logger.warning(f"Could not generate summary for document {document_id}")
            raise HTTPException(
                status_code=400, 
                detail="Could not generate summary. Document may not contain extractable text or OpenAI API key may not be configured."
            )
        logger.info(f"Successfully generated summary for document {document_id}")
        return {"document_id": document_id, "summary": summary}
    except ValueError as e:
        logger.error(f"ValueError in summarize_document: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Exception in summarize_document: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
def delete_document(document_id: str):
    """Delete a document."""
    try:
        success = context_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"status": "deleted", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

