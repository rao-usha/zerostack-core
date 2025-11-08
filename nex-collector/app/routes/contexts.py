"""Context routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db import get_db
from .. import models, schemas


router = APIRouter(prefix="/v1/contexts", tags=["contexts"])


@router.post("", status_code=201, response_model=schemas.ContextDocResponse)
def create_context(
    payload: schemas.ContextDocCreate,
    db: Session = Depends(get_db)
):
    """Create a ContextDoc."""
    existing = db.query(models.ContextDoc).filter(models.ContextDoc.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="ContextDoc ID already exists")
    
    obj = models.ContextDoc(
        id=payload.id,
        title=payload.title,
        version=payload.version,
        body_text=payload.body_text,
        metadata_json=payload.metadata_json,
        nex_context_id=payload.nex_context_id,
        nex_context_version=payload.nex_context_version
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/variants", response_model=List[schemas.ContextVariantResponse])
def list_variants(
    domain: Optional[str] = None,
    persona: Optional[str] = None,
    task: Optional[str] = None,
    context_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List ContextVariants with optional filters by domain, persona, task, or context_id."""
    query = db.query(models.ContextVariant)
    
    if domain:
        query = query.filter(models.ContextVariant.domain == domain)
    if persona:
        query = query.filter(models.ContextVariant.persona == persona)
    if task:
        query = query.filter(models.ContextVariant.task == task)
    if context_id:
        query = query.filter(models.ContextVariant.context_id == context_id)
    
    variants = query.order_by(models.ContextVariant.created_at.desc()).all()
    return variants


@router.get("/variants/{variant_id}", response_model=schemas.ContextVariantResponse)
def get_variant(
    variant_id: str,
    db: Session = Depends(get_db)
):
    """Get a ContextVariant by ID."""
    obj = db.query(models.ContextVariant).filter(models.ContextVariant.id == variant_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Variant not found")
    return obj


@router.get("/{context_id}", response_model=schemas.ContextDocResponse)
def get_context(
    context_id: str,
    db: Session = Depends(get_db)
):
    """Get a ContextDoc by ID."""
    obj = db.query(models.ContextDoc).filter(models.ContextDoc.id == context_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="ContextDoc not found")
    return obj


@router.post("/{context_id}/variants", status_code=201, response_model=schemas.ContextVariantResponse)
def create_variant(
    context_id: str,
    payload: schemas.ContextVariantCreate,
    db: Session = Depends(get_db)
):
    """Create a ContextVariant."""
    context = db.query(models.ContextDoc).filter(models.ContextDoc.id == context_id).first()
    if not context:
        raise HTTPException(status_code=404, detail="ContextDoc not found")
    
    existing = db.query(models.ContextVariant).filter(models.ContextVariant.id == payload.id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Variant ID already exists")
    
    obj = models.ContextVariant(
        id=payload.id,
        context_id=context_id,
        domain=payload.domain,
        persona=payload.persona,
        task=payload.task,
        style=payload.style,
        constraints_json=payload.constraints_json,
        body_text=payload.body_text,
        parent_variant_id=payload.parent_variant_id
    )
    db.add(obj)
    
    # Extract features
    from ..ingest.features import FeatureExtractor
    extractor = FeatureExtractor()
    features = extractor.extract(
        payload.body_text,
        payload.domain,
        payload.persona,
        payload.task,
        payload.style
    )
    
    feature_vector = models.FeatureVector(
        id=f"fv-{payload.id}",
        variant_id=payload.id,
        features_json=features
    )
    db.add(feature_vector)
    
    # Chunk and embed if enabled
    from ..ingest.chunking import Chunker
    from ..ingest.embed import Embedder
    from ..config import settings
    
    chunker = Chunker()
    chunks = chunker.chunk(payload.body_text)
    
    embedder = Embedder()
    embeddings = embedder.embed(chunks)
    
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = models.Chunk(
            id=f"chunk-{payload.id}-{i}",
            variant_id=payload.id,
            order=i,
            text=chunk_text,
            embedding=embedding
        )
        db.add(chunk)
    
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/variants", response_model=List[schemas.ContextVariantResponse])
def list_variants(
    domain: Optional[str] = None,
    persona: Optional[str] = None,
    task: Optional[str] = None,
    context_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List ContextVariants with optional filters by domain, persona, task, or context_id."""
    query = db.query(models.ContextVariant)
    
    if domain:
        query = query.filter(models.ContextVariant.domain == domain)
    if persona:
        query = query.filter(models.ContextVariant.persona == persona)
    if task:
        query = query.filter(models.ContextVariant.task == task)
    if context_id:
        query = query.filter(models.ContextVariant.context_id == context_id)
    
    variants = query.order_by(models.ContextVariant.created_at.desc()).all()
    return variants


@router.get("/variants/{variant_id}", response_model=schemas.ContextVariantResponse)
def get_variant(
    variant_id: str,
    db: Session = Depends(get_db)
):
    """Get a ContextVariant by ID."""
    obj = db.query(models.ContextVariant).filter(models.ContextVariant.id == variant_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Variant not found")
    return obj


@router.post("/variants/compose", status_code=201, response_model=schemas.ContextVariantResponse)
def compose_variant(
    payload: schemas.VariantComposeRequest,
    db: Session = Depends(get_db)
):
    """Compose a new variant by mixing facets from existing variants."""
    # Get source variants
    source_variants = db.query(models.ContextVariant).filter(
        models.ContextVariant.id.in_(payload.source_variant_ids)
    ).all()
    
    if len(source_variants) != len(payload.source_variant_ids):
        raise HTTPException(status_code=404, detail="Some source variants not found")
    
    # Determine target context
    target_context_id = payload.target_context_id or source_variants[0].context_id
    
    # Compose body text (concatenate or use first)
    if payload.composition_strategy == "concatenate":
        body_text = "\n\n".join([v.body_text for v in source_variants])
    elif payload.composition_strategy == "merge":
        # Merge sections intelligently
        sections = {}
        for variant in source_variants:
            # Simple merge: combine constraints and text
            if variant.constraints_json:
                sections.setdefault("constraints", []).append(variant.constraints_json)
            sections.setdefault("content", []).append(variant.body_text)
        
        constraints_merged = {}
        for c in sections.get("constraints", []):
            constraints_merged.update(c)
        
        body_text = "\n\n---\n\n".join(sections.get("content", []))
    else:  # first
        body_text = source_variants[0].body_text
    
    # Use provided facets or inherit from sources
    domain = payload.domain or source_variants[0].domain
    persona = payload.persona or source_variants[0].persona
    task = payload.task or source_variants[0].task
    style = payload.style or source_variants[0].style
    
    # Merge constraints
    constraints = payload.constraints_json or {}
    for variant in source_variants:
        if variant.constraints_json:
            constraints.update(variant.constraints_json)
    
    # Create composed variant
    import uuid
    variant_id = payload.variant_id or f"var-composed-{uuid.uuid4().hex[:12]}"
    
    obj = models.ContextVariant(
        id=variant_id,
        context_id=target_context_id,
        domain=domain,
        persona=persona,
        task=task,
        style=style,
        constraints_json=constraints,
        body_text=body_text,
        parent_variant_id=source_variants[0].id if source_variants else None
    )
    db.add(obj)
    
    # Extract features
    from ..ingest.features import FeatureExtractor
    extractor = FeatureExtractor()
    features = extractor.extract(body_text, domain, persona, task, style)
    
    feature_vector = models.FeatureVector(
        id=f"fv-{variant_id}",
        variant_id=variant_id,
        features_json=features
    )
    db.add(feature_vector)
    
    # Chunk and embed
    from ..ingest.chunking import Chunker
    from ..ingest.embed import Embedder
    
    chunker = Chunker()
    chunks = chunker.chunk(body_text)
    
    embedder = Embedder()
    embeddings = embedder.embed(chunks)
    
    for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        chunk = models.Chunk(
            id=f"chunk-{variant_id}-{i}",
            variant_id=variant_id,
            order=i,
            text=chunk_text,
            embedding=embedding
        )
        db.add(chunk)
    
    db.commit()
    db.refresh(obj)
    return obj
