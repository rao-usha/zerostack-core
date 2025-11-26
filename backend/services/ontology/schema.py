"""Pydantic schemas for ontology service."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class Term(BaseModel):
    """A term in an ontology."""
    term: str
    definition: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Relation(BaseModel):
    """A relationship between terms in an ontology."""
    src_term: str
    rel_type: str  # "is_a" | "synonym_of" | "part_of" | "related_to"
    dst_term: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PublishSummary(BaseModel):
    """Summary for a published ontology version."""
    change_summary: Optional[str] = None


class OntologySnapshot(BaseModel):
    """A snapshot of an ontology state."""
    terms: List[Term] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)


