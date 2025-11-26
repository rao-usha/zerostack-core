"""Ontology API router."""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from services.ontology.manager import OntologyManager

router = APIRouter(prefix="/ontology", tags=["ontology"])
mgr = OntologyManager()


@router.post("/", status_code=201)
async def create_ontology(req: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new ontology."""
    try:
        return mgr.create(
            req.get("org_id", "demo"),
            req["name"],
            req.get("description"),
            req.get("actor", "user")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ontology_id}/terms", status_code=200)
async def add_terms(ontology_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
    """Add or update terms in an ontology."""
    try:
        return mgr.add_terms(ontology_id, req["items"], req.get("actor", "user"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ontology_id}/relations", status_code=200)
async def add_relations(ontology_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
    """Add relations between terms."""
    try:
        return mgr.add_relations(ontology_id, req["items"], req.get("actor", "user"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_ontologies(org_id: str = "demo") -> Dict[str, Any]:
    """List all ontologies for an organization."""
    try:
        # This is a stub - you'll need to implement in OntologyManager
        return {"ontologies": []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ontology_id}")
async def get_ontology(ontology_id: str) -> Dict[str, Any]:
    """Get all terms and relations in an ontology."""
    try:
        return mgr.list(ontology_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ontology_id}/publish", status_code=200)
async def publish_version(ontology_id: str, req: Dict[str, Any]) -> Dict[str, Any]:
    """Publish a new version of the ontology."""
    try:
        from services.ontology.schema import PublishSummary
        summary = PublishSummary(change_summary=req.get("change_summary"))
        return mgr.publish_version(ontology_id, summary, req.get("actor", "user"))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ontology_id}/diff")
async def diff_head(ontology_id: str) -> Dict[str, Any]:
    """Compare working set vs last published version."""
    try:
        return mgr.diff_head(ontology_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


