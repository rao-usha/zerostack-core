"""Ontology manager for CRUD operations."""
import uuid
import json
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, insert, select, update, delete
from core.config import settings
from .schema import Term, Relation, PublishSummary, OntologySnapshot


class OntologyManager:
    """
    Postgres-backed operations for ontology management.
    Handles creation, modification, versioning, and auditing of ontologies.
    """
    
    def __init__(self):
        """Initialize the manager with database connection."""
        self.engine = create_engine(settings.database_url)
    
    def _audit(self, conn, ontology_id: str, actor: str, action: str, payload: Dict[str, Any]):
        """Record an audit entry."""
        conn.execute(
            text("""
                INSERT INTO ontology_audit (id, ontology_id, actor, action, payload)
                VALUES (:id, :ontology_id, :actor, :action, :payload::jsonb)
            """),
            {
                "id": str(uuid.uuid4()),
                "ontology_id": ontology_id,
                "actor": actor,
                "action": action,
                "payload": json.dumps(payload)
            }
        )
    
    def create(self, org_id: str, name: str, description: Optional[str], actor: str) -> Dict[str, Any]:
        """Create a new ontology."""
        ontology_id = str(uuid.uuid4())
        
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO ontologies (id, org_id, name, description)
                    VALUES (:id, :org_id, :name, :description)
                """),
                {
                    "id": ontology_id,
                    "org_id": org_id,
                    "name": name,
                    "description": description
                }
            )
            
            self._audit(conn, ontology_id, actor, "create", {
                "name": name,
                "description": description
            })
        
        return {"ontology_id": ontology_id}
    
    def add_terms(self, ontology_id: str, items: List[Dict[str, Any]], actor: str) -> Dict[str, Any]:
        """Add or update terms in an ontology."""
        with self.engine.begin() as conn:
            # Verify ontology exists
            result = conn.execute(
                text("SELECT id FROM ontologies WHERE id = :id"),
                {"id": ontology_id}
            )
            if not result.fetchone():
                raise ValueError(f"Ontology {ontology_id} not found")
            
            # Upsert terms
            for item in items:
                term = item.get("term")
                definition = item.get("definition")
                metadata = item.get("metadata", {})
                
                # Check if term exists
                existing = conn.execute(
                    text("""
                        SELECT id FROM ontology_terms 
                        WHERE ontology_id = :ontology_id AND term = :term
                    """),
                    {"ontology_id": ontology_id, "term": term}
                ).fetchone()
                
                if existing:
                    # Update existing term
                    conn.execute(
                        text("""
                            UPDATE ontology_terms 
                            SET definition = :definition, metadata = :metadata::jsonb
                            WHERE ontology_id = :ontology_id AND term = :term
                        """),
                        {
                            "ontology_id": ontology_id,
                            "term": term,
                            "definition": definition,
                            "metadata": json.dumps(metadata)
                        }
                    )
                else:
                    # Insert new term
                    conn.execute(
                        text("""
                            INSERT INTO ontology_terms (id, ontology_id, term, definition, metadata)
                            VALUES (:id, :ontology_id, :term, :definition, :metadata::jsonb)
                        """),
                        {
                            "id": str(uuid.uuid4()),
                            "ontology_id": ontology_id,
                            "term": term,
                            "definition": definition,
                            "metadata": json.dumps(metadata)
                        }
                    )
            
            self._audit(conn, ontology_id, actor, "add_terms", {"count": len(items)})
        
        return {"added": len(items)}
    
    def add_relations(self, ontology_id: str, items: List[Dict[str, Any]], actor: str) -> Dict[str, Any]:
        """Add relations between terms in an ontology."""
        with self.engine.begin() as conn:
            # Verify ontology exists
            result = conn.execute(
                text("SELECT id FROM ontologies WHERE id = :id"),
                {"id": ontology_id}
            )
            if not result.fetchone():
                raise ValueError(f"Ontology {ontology_id} not found")
            
            # Insert relations
            for item in items:
                conn.execute(
                    text("""
                        INSERT INTO ontology_relations 
                        (id, ontology_id, src_term, rel_type, dst_term, metadata)
                        VALUES (:id, :ontology_id, :src_term, :rel_type, :dst_term, :metadata::jsonb)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "ontology_id": ontology_id,
                        "src_term": item.get("src_term"),
                        "rel_type": item.get("rel_type"),
                        "dst_term": item.get("dst_term"),
                        "metadata": json.dumps(item.get("metadata", {}))
                    }
                )
            
            self._audit(conn, ontology_id, actor, "add_relations", {"count": len(items)})
        
        return {"added": len(items)}
    
    def list(self, ontology_id: str) -> Dict[str, Any]:
        """List all terms and relations in an ontology."""
        with self.engine.begin() as conn:
            # Get terms
            terms_result = conn.execute(
                text("""
                    SELECT term, definition, metadata 
                    FROM ontology_terms 
                    WHERE ontology_id = :ontology_id
                """),
                {"ontology_id": ontology_id}
            )
            terms = [
                {
                    "term": row[0],
                    "definition": row[1],
                    "metadata": row[2] if row[2] else {}
                }
                for row in terms_result
            ]
            
            # Get relations
            relations_result = conn.execute(
                text("""
                    SELECT src_term, rel_type, dst_term, metadata 
                    FROM ontology_relations 
                    WHERE ontology_id = :ontology_id
                """),
                {"ontology_id": ontology_id}
            )
            relations = [
                {
                    "src_term": row[0],
                    "rel_type": row[1],
                    "dst_term": row[2],
                    "metadata": row[3] if row[3] else {}
                }
                for row in relations_result
            ]
        
        return {"terms": terms, "relations": relations}
    
    def publish_version(self, ontology_id: str, summary: PublishSummary, actor: str) -> Dict[str, Any]:
        """Publish a new version of the ontology."""
        with self.engine.begin() as conn:
            # Get current state
            current = self.list(ontology_id)
            snapshot = {
                "terms": current["terms"],
                "relations": current["relations"]
            }
            
            # Compute digest
            content_str = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
            digest = hashlib.sha256(content_str.encode()).hexdigest()
            
            # Get version number (increment from last version)
            last_version = conn.execute(
                text("""
                    SELECT version FROM ontology_versions 
                    WHERE ontology_id = :ontology_id 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """),
                {"ontology_id": ontology_id}
            ).fetchone()
            
            if last_version:
                # Parse version like "v0.1" -> "v0.2"
                try:
                    version_num = float(last_version[0].replace("v", ""))
                    new_version = f"v{version_num + 0.1:.1f}"
                except:
                    new_version = "v1.0"
            else:
                new_version = "v0.1"
            
            # Create version record
            version_id = str(uuid.uuid4())
            conn.execute(
                text("""
                    INSERT INTO ontology_versions 
                    (id, ontology_id, version, digest, change_summary, created_by)
                    VALUES (:id, :ontology_id, :version, :digest, :change_summary, :created_by)
                """),
                {
                    "id": version_id,
                    "ontology_id": ontology_id,
                    "version": new_version,
                    "digest": digest,
                    "change_summary": summary.change_summary,
                    "created_by": actor
                }
            )
            
            # Store version content
            conn.execute(
                text("""
                    INSERT INTO ontology_version_content 
                    (id, ontology_version_id, terms, relations)
                    VALUES (:id, :version_id, :terms::jsonb, :relations::jsonb)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "version_id": version_id,
                    "terms": json.dumps(snapshot["terms"]),
                    "relations": json.dumps(snapshot["relations"])
                }
            )
            
            self._audit(conn, ontology_id, actor, "publish_version", {
                "version": new_version,
                "digest": digest
            })
        
        return {"version_id": new_version, "digest": digest}
    
    def diff_head(self, ontology_id: str) -> Dict[str, Any]:
        """Compare working set vs last published version."""
        with self.engine.begin() as conn:
            # Get current working state
            current = self.list(ontology_id)
            
            # Get last published version
            last_version = conn.execute(
                text("""
                    SELECT ovc.terms, ovc.relations 
                    FROM ontology_versions ov
                    JOIN ontology_version_content ovc ON ovc.ontology_version_id = ov.id
                    WHERE ov.ontology_id = :ontology_id
                    ORDER BY ov.created_at DESC
                    LIMIT 1
                """),
                {"ontology_id": ontology_id}
            ).fetchone()
            
            if not last_version:
                # No previous version, everything is new
                return {
                    "added_terms": current["terms"],
                    "changed_terms": [],
                    "deleted_terms": [],
                    "added_relations": current["relations"]
                }
            
            # Compare terms
            prev_terms = {t["term"]: t for t in last_version[0]}
            curr_terms = {t["term"]: t for t in current["terms"]}
            
            added_terms = [t for term, t in curr_terms.items() if term not in prev_terms]
            changed_terms = [
                t for term, t in curr_terms.items() 
                if term in prev_terms and t != prev_terms[term]
            ]
            deleted_terms = [t for term, t in prev_terms.items() if term not in curr_terms]
            
            # Compare relations
            prev_rels = set(
                (r["src_term"], r["rel_type"], r["dst_term"]) 
                for r in last_version[1]
            )
            curr_rels = set(
                (r["src_term"], r["rel_type"], r["dst_term"]) 
                for r in current["relations"]
            )
            
            added_relations = [
                r for r in current["relations"]
                if (r["src_term"], r["rel_type"], r["dst_term"]) not in prev_rels
            ]
        
        return {
            "added_terms": added_terms,
            "changed_terms": changed_terms,
            "deleted_terms": deleted_terms,
            "added_relations": added_relations
        }


