"""Database models for context aggregator."""
from sqlalchemy import Column, String, DateTime, Boolean, JSON, ForeignKey, Integer, Enum as SQLEnum, Text, Float
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .db import Base
from sqlalchemy.sql import func


class ExampleType(PyEnum):
    """Synthetic example type."""
    INSTRUCTION = "instruction"
    QA = "qa"
    TASK = "task"


class DatasetKind(PyEnum):
    """Dataset kind."""
    TRAIN = "train"
    EVAL = "eval"
    SYNTHETIC = "synthetic"
    FINETUNE_PACK = "finetune_pack"


class ContextDoc(Base):
    """Context document (body of text with metadata)."""
    __tablename__ = "context_docs"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    version = Column(String, nullable=False)
    body_text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default={})
    nex_context_id = Column(String, nullable=True, index=True)  # Optional link to NEX
    nex_context_version = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variants = relationship("ContextVariant", back_populates="context_doc")
    datasets = relationship("DatasetManifest", back_populates="context_doc")


class ContextVariant(Base):
    """Context variant with facets (mix & match)."""
    __tablename__ = "context_variants"
    
    id = Column(String, primary_key=True)
    context_id = Column(String, ForeignKey("context_docs.id"), nullable=False, index=True)
    domain = Column(String, nullable=True, index=True)  # e.g., "insurance", "finance", "healthcare"
    persona = Column(String, nullable=True, index=True)  # e.g., "underwriter", "CFO", "doctor"
    task = Column(String, nullable=True, index=True)  # e.g., "risk_assessment", "explain", "classify"
    style = Column(String, nullable=True)  # e.g., "formal", "conversational"
    constraints_json = Column(JSON, nullable=False, default={})
    body_text = Column(Text, nullable=False)
    parent_variant_id = Column(String, ForeignKey("context_variants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    context_doc = relationship("ContextDoc", back_populates="variants")
    parent_variant = relationship("ContextVariant", remote_side=[id])
    chunks = relationship("Chunk", back_populates="variant")
    feature_vector = relationship("FeatureVector", back_populates="variant", uselist=False)
    examples = relationship("SyntheticExample", back_populates="variant")


class Chunk(Base):
    """Text chunk for retrieval/embeddings."""
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True)
    variant_id = Column(String, ForeignKey("context_variants.id"), nullable=False)
    order = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Vector as JSON array
    # Provenance & traceability
    source_uri = Column(String, nullable=True)  # URI of source document
    source_span = Column(JSON, nullable=True)  # Character offsets: {start: int, end: int}
    citation_ids = Column(ARRAY(String), nullable=True)  # Array of citation IDs
    text_hash = Column(String, nullable=True, index=True)  # Hash(text) for de-duplication
    license = Column(String, nullable=True)  # License information
    usage_rights = Column(String, nullable=True)  # Usage rights information
    # Quality signals
    quality_scores_json = Column(JSON, nullable=True)  # Quality scores: {coherence, faithfulness, toxicity, pii_flags, ...}
    confidence = Column(Float, nullable=True)  # Overall confidence score (0.0-1.0)
    # Smarter chunking for retrieval
    neighbors = Column(ARRAY(String), nullable=True)  # Bidirectional links to neighboring chunk IDs
    section_hierarchy = Column(JSON, nullable=True)  # Document structure: {level: int, section: str, subsection: str, ...}
    chunk_type = Column(String, nullable=True)  # Structural type: "heading", "bullet", "paragraph", "code", etc.
    overlap_start = Column(Integer, nullable=True)  # Start character offset for overlap window
    overlap_end = Column(Integer, nullable=True)  # End character offset for overlap window
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variant = relationship("ContextVariant", back_populates="chunks")


class FeatureVector(Base):
    """Extracted structured features."""
    __tablename__ = "feature_vectors"
    
    id = Column(String, primary_key=True)
    variant_id = Column(String, ForeignKey("context_variants.id"), nullable=False, unique=True)
    features_json = Column(JSON, nullable=False)  # domain, persona, task, style, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variant = relationship("ContextVariant", back_populates="feature_vector")


class SyntheticExample(Base):
    """Synthetic example built from variants."""
    __tablename__ = "synthetic_examples"
    
    id = Column(String, primary_key=True)
    variant_id = Column(String, ForeignKey("context_variants.id"), nullable=False)
    example_type = Column(SQLEnum(ExampleType), nullable=False)
    input_json = Column(JSON, nullable=False)
    constraints_json = Column(JSON, nullable=False, default={})
    tags = Column(ARRAY(String), nullable=False, default=[])
    # Provenance & traceability
    source_uri = Column(String, nullable=True)  # URI of source document
    source_span = Column(JSON, nullable=True)  # Character offsets: {start: int, end: int}
    citation_ids = Column(ARRAY(String), nullable=True)  # Array of citation IDs
    text_hash = Column(String, nullable=True, index=True)  # Hash(input_json) for de-duplication
    license = Column(String, nullable=True)  # License information
    usage_rights = Column(String, nullable=True)  # Usage rights information
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    variant = relationship("ContextVariant", back_populates="examples")
    teacher_runs = relationship("TeacherRun", back_populates="example")
    targets = relationship("Targets", back_populates="example")


class TeacherRun(Base):
    """OTS model output for labeling examples."""
    __tablename__ = "teacher_runs"
    
    id = Column(String, primary_key=True)
    example_id = Column(String, ForeignKey("synthetic_examples.id"), nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    params_json = Column(JSON, nullable=False)
    output_json = Column(JSON, nullable=True)  # {text, usage, logprobs?}
    usage_json = Column(JSON, nullable=True)
    # Quality signals
    quality_scores_json = Column(JSON, nullable=True)  # Quality scores: {coherence, faithfulness, toxicity, pii_flags, ...}
    confidence = Column(Float, nullable=True)  # Overall confidence score (0.0-1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    example = relationship("SyntheticExample", back_populates="teacher_runs")


class Targets(Base):
    """Distilled labels/soft-labels."""
    __tablename__ = "targets"
    
    id = Column(String, primary_key=True)
    example_id = Column(String, ForeignKey("synthetic_examples.id"), nullable=False, unique=True)
    y_text = Column(Text, nullable=False)
    y_probs_json = Column(JSON, nullable=True)  # Soft labels
    y_scores_json = Column(JSON, nullable=True)  # Quality scores
    # Provenance & traceability
    source_uri = Column(String, nullable=True)  # URI of source document
    source_span = Column(JSON, nullable=True)  # Character offsets: {start: int, end: int}
    citation_ids = Column(ARRAY(String), nullable=True)  # Array of citation IDs
    # Quality signals
    quality_scores_json = Column(JSON, nullable=True)  # Quality scores: {coherence, faithfulness, toxicity, pii_flags, ...}
    confidence = Column(Float, nullable=True)  # Overall confidence score (0.0-1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    example = relationship("SyntheticExample", back_populates="targets")


class DatasetManifest(Base):
    """Dataset manifest."""
    __tablename__ = "dataset_manifests"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    kind = Column(SQLEnum(DatasetKind), nullable=False)
    context_id = Column(String, ForeignKey("context_docs.id"), nullable=True)
    variant_ids = Column(ARRAY(String), nullable=False, default=[])
    file_uris = Column(ARRAY(String), nullable=False, default=[])
    filters_json = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    context_doc = relationship("ContextDoc", back_populates="datasets")
