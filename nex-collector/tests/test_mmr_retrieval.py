#!/usr/bin/env python3
"""Simple test script for MMR & query-aware selection (no pytest required)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, Chunk, SyntheticExample, ExampleType
)
from app.distill.mmr import mmr_retrieval, simple_retrieval, cosine_similarity


def test_mmr_and_retrieval_context_ids():
    """Test MMR retrieval and retrieval_context_ids field."""
    print("🧪 Testing MMR & Query-Aware Selection")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-mmr",
            title="Test Context for MMR",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-mmr",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Create chunks with embeddings for MMR
        print("\n3️⃣ Creating chunks with embeddings...")
        # Simple embeddings (3D vectors for testing)
        chunks_data = [
            {"id": "chunk-mmr-1", "text": "Chunk about risk assessment", "embedding": [0.8, 0.6, 0.0]},
            {"id": "chunk-mmr-2", "text": "Chunk about risk assessment", "embedding": [0.7, 0.7, 0.0]},  # Similar to 1
            {"id": "chunk-mmr-3", "text": "Chunk about policy terms", "embedding": [0.0, 0.0, 0.9]},  # Different
            {"id": "chunk-mmr-4", "text": "Chunk about claims processing", "embedding": [0.0, 0.0, 0.8]},  # Different
            {"id": "chunk-mmr-5", "text": "Chunk about risk assessment", "embedding": [0.75, 0.65, 0.0]},  # Similar to 1,2
        ]
        
        for i, chunk_data in enumerate(chunks_data):
            chunk = Chunk(
                id=chunk_data["id"],
                variant_id=variant.id,
                order=i,
                text=chunk_data["text"],
                embedding=chunk_data["embedding"]
            )
            db.add(chunk)
        db.commit()
        print(f"   ✅ Created {len(chunks_data)} chunks with embeddings")
        
        # Test MMR retrieval
        print("\n4️⃣ Testing MMR retrieval...")
        query_embedding = [0.8, 0.6, 0.0]  # Similar to risk assessment chunks
        
        candidate_chunks = [
            {"id": c.id, "embedding": c.embedding}
            for c in db.query(Chunk).filter_by(variant_id=variant.id).all()
        ]
        
        # MMR with lambda=0.5 (balanced)
        mmr_ids = mmr_retrieval(query_embedding, candidate_chunks, lambda_param=0.5, top_k=3)
        assert len(mmr_ids) == 3
        assert "chunk-mmr-1" in mmr_ids  # High relevance
        # Should include diverse chunks (not all similar ones)
        print(f"   ✅ MMR retrieval selected: {mmr_ids}")
        
        # MMR with lambda=0.0 (pure relevance)
        relevance_ids = mmr_retrieval(query_embedding, candidate_chunks, lambda_param=0.0, top_k=3)
        assert len(relevance_ids) == 3
        print(f"   ✅ Pure relevance retrieval: {relevance_ids}")
        
        # MMR with lambda=1.0 (pure diversity)
        diversity_ids = mmr_retrieval(query_embedding, candidate_chunks, lambda_param=1.0, top_k=3)
        assert len(diversity_ids) == 3
        print(f"   ✅ Pure diversity retrieval: {diversity_ids}")
        
        # Test simple retrieval
        print("\n5️⃣ Testing simple retrieval...")
        simple_ids = simple_retrieval(query_embedding, candidate_chunks, top_k=3)
        assert len(simple_ids) == 3
        assert simple_ids[0] == "chunk-mmr-1"  # Highest similarity
        print(f"   ✅ Simple retrieval: {simple_ids}")
        
        # Test SyntheticExample with retrieval_context_ids
        print("\n6️⃣ Testing SyntheticExample with retrieval_context_ids...")
        example = SyntheticExample(
            id="test-ex-mmr",
            variant_id=variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "What about risk assessment?"},
            constraints_json={},
            tags=[],
            retrieval_context_ids=mmr_ids  # Store MMR-selected chunk IDs
        )
        db.add(example)
        db.commit()
        
        retrieved = db.query(SyntheticExample).filter_by(id="test-ex-mmr").first()
        assert retrieved.retrieval_context_ids == mmr_ids
        assert len(retrieved.retrieval_context_ids) == 3
        assert "chunk-mmr-1" in retrieved.retrieval_context_ids
        print(f"   ✅ retrieval_context_ids stored correctly: {retrieved.retrieval_context_ids}")
        
        # Test querying examples by retrieval context
        print("\n7️⃣ Testing querying by retrieval_context_ids...")
        # Find examples that used a specific chunk
        examples_using_chunk1 = db.query(SyntheticExample).filter(
            SyntheticExample.retrieval_context_ids.contains(["chunk-mmr-1"])
        ).all()
        assert len(examples_using_chunk1) == 1
        assert examples_using_chunk1[0].id == "test-ex-mmr"
        print("   ✅ Querying by retrieval_context_ids works correctly")
        
        # Test optional field
        print("\n8️⃣ Testing optional retrieval_context_ids...")
        example2 = SyntheticExample(
            id="test-ex-no-retrieval",
            variant_id=variant.id,
            example_type=ExampleType.TASK,
            input_json={"task": "test"},
            constraints_json={},
            tags=[]
        )
        db.add(example2)
        db.commit()
        
        retrieved2 = db.query(SyntheticExample).filter_by(id="test-ex-no-retrieval").first()
        assert retrieved2.retrieval_context_ids is None
        print("   ✅ Optional retrieval_context_ids works correctly")
        
        # Test cosine similarity function
        print("\n9️⃣ Testing cosine similarity...")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001  # Should be 1.0 (identical)
        
        vec3 = [0.0, 1.0, 0.0]
        similarity2 = cosine_similarity(vec1, vec3)
        assert abs(similarity2 - 0.0) < 0.001  # Should be 0.0 (orthogonal)
        print("   ✅ Cosine similarity works correctly")
        
        print("\n" + "=" * 60)
        print("✅ All MMR & query-aware selection tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)
    
    return True


if __name__ == "__main__":
    success = test_mmr_and_retrieval_context_ids()
    sys.exit(0 if success else 1)

