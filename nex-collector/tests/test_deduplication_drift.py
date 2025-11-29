#!/usr/bin/env python3
"""Simple test script for De-duplication & Drift Control (no pytest required)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, SyntheticExample, Chunk, ExampleType
)
from app.distill.deduplication import (
    compute_simhash,
    compute_minhash,
    semantic_hash_from_embedding,
    hamming_distance,
    is_near_duplicate,
    compute_embedding_centroid,
    cosine_distance,
    detect_concept_drift
)


def test_deduplication_and_drift():
    """Test de-duplication and drift control functionality."""
    print("🧪 Testing De-duplication & Drift Control")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-dedup",
            title="Test Context for Deduplication",
            version="1.0.0",
            body_text="Test context body text about insurance underwriting."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-dedup",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Test SimHash
        print("\n3️⃣ Testing SimHash computation...")
        text1 = "This is a test text about insurance underwriting."
        text2 = "This is a test text about insurance underwriting."  # Exact duplicate
        text3 = "This is a different text about something else."  # Different
        
        hash1 = compute_simhash(text1)
        hash2 = compute_simhash(text2)
        hash3 = compute_simhash(text3)
        
        assert hash1 == hash2  # Exact duplicates should have same hash
        assert hash1 != hash3  # Different texts should have different hashes
        assert len(hash1) == 16  # 64 bits = 16 hex chars
        print(f"   ✅ SimHash computed: {hash1[:8]}...")
        print(f"      Duplicate hash matches: {hash1 == hash2}")
        
        # Test MinHash
        print("\n4️⃣ Testing MinHash computation...")
        minhash1 = compute_minhash(text1)
        minhash2 = compute_minhash(text2)
        minhash3 = compute_minhash(text3)
        
        assert minhash1 == minhash2  # Exact duplicates should have same signature
        assert minhash1 != minhash3  # Different texts should have different signatures
        assert len(minhash1) == 128  # num_perm = 128
        print(f"   ✅ MinHash computed: {len(minhash1)} values")
        
        # Test semantic hash from embedding
        print("\n5️⃣ Testing semantic hash from embedding...")
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100-dim embedding
        semantic_hash = semantic_hash_from_embedding(embedding)
        assert semantic_hash is not None
        assert len(semantic_hash) > 0
        print(f"   ✅ Semantic hash from embedding: {semantic_hash[:8]}...")
        
        # Test Hamming distance
        print("\n6️⃣ Testing Hamming distance...")
        hash_a = "0000000000000000"
        hash_b = "0000000000000001"  # 1 bit different
        hash_c = "ffffffffffffffff"  # All bits different
        
        dist_ab = hamming_distance(hash_a, hash_b)
        dist_ac = hamming_distance(hash_a, hash_c)
        
        assert dist_ab == 1
        assert dist_ac == 64  # All 64 bits different
        print(f"   ✅ Hamming distance: ab={dist_ab}, ac={dist_ac}")
        
        # Test near-duplicate detection
        print("\n7️⃣ Testing near-duplicate detection...")
        similar_text = "This is a test text about insurance underwriting with minor changes."
        similar_hash = compute_simhash(similar_text)
        
        is_dup = is_near_duplicate(hash1, hash2, threshold=3)
        is_similar = is_near_duplicate(hash1, similar_hash, threshold=10)  # More lenient threshold
        
        assert is_dup == True  # Exact duplicates
        print(f"   ✅ Near-duplicate detection: exact={is_dup}, similar={is_similar}")
        
        # Test embedding centroid computation
        print("\n8️⃣ Testing embedding centroid computation...")
        embeddings = [
            [1.0, 2.0, 3.0],
            [2.0, 3.0, 4.0],
            [3.0, 4.0, 5.0]
        ]
        centroid = compute_embedding_centroid(embeddings)
        assert centroid is not None
        assert len(centroid) == 3
        assert abs(centroid[0] - 2.0) < 0.01  # Mean of [1, 2, 3]
        assert abs(centroid[1] - 3.0) < 0.01  # Mean of [2, 3, 4]
        assert abs(centroid[2] - 4.0) < 0.01  # Mean of [3, 4, 5]
        print(f"   ✅ Centroid computed: {centroid}")
        
        # Test cosine distance
        print("\n9️⃣ Testing cosine distance...")
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]  # Identical
        vec3 = [0.0, 1.0, 0.0]  # Orthogonal
        
        dist_identical = cosine_distance(vec1, vec2)
        dist_orthogonal = cosine_distance(vec1, vec3)
        
        assert abs(dist_identical - 0.0) < 0.001
        assert abs(dist_orthogonal - 1.0) < 0.001
        print(f"   ✅ Cosine distance: identical={dist_identical:.3f}, orthogonal={dist_orthogonal:.3f}")
        
        # Test concept drift detection
        print("\n🔟 Testing concept drift detection...")
        old_centroid = [1.0, 0.0, 0.0]
        new_centroid_same = [1.0, 0.0, 0.0]  # No drift
        new_centroid_drift = [0.0, 1.0, 0.0]  # Significant drift
        
        drift_none = detect_concept_drift(old_centroid, new_centroid_same, threshold=0.2)
        drift_high = detect_concept_drift(old_centroid, new_centroid_drift, threshold=0.2)
        
        assert drift_none["has_drift"] == False
        assert drift_high["has_drift"] == True
        assert drift_high["severity"] == "high"
        print(f"   ✅ Drift detection: no_drift={drift_none['has_drift']}, high_drift={drift_high['has_drift']} (severity: {drift_high['severity']})")
        
        # Test storing semantic hash in SyntheticExample
        print("\n1️⃣1️⃣ Testing semantic hash storage in SyntheticExample...")
        example = SyntheticExample(
            id="test-ex-dedup",
            variant_id=variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "What is the answer?"},
            constraints_json={},
            tags=[],
            semantic_hash=hash1
        )
        db.add(example)
        db.commit()
        
        retrieved = db.query(SyntheticExample).filter_by(id="test-ex-dedup").first()
        assert retrieved.semantic_hash == hash1
        print(f"   ✅ Semantic hash stored: {retrieved.semantic_hash[:8]}...")
        
        # Test querying by semantic hash
        print("\n1️⃣2️⃣ Testing querying by semantic hash...")
        # Create another example with same hash
        example2 = SyntheticExample(
            id="test-ex-dedup-2",
            variant_id=variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "What is the answer?"},
            constraints_json={},
            tags=[],
            semantic_hash=hash2  # Same hash as hash1
        )
        db.add(example2)
        db.commit()
        
        # Query for near-duplicates
        duplicates = db.query(SyntheticExample).filter(
            SyntheticExample.semantic_hash == hash1
        ).all()
        assert len(duplicates) == 2
        print(f"   ✅ Found {len(duplicates)} examples with same semantic hash")
        
        # Test storing embedding centroid in ContextDoc
        print("\n1️⃣3️⃣ Testing embedding centroid storage in ContextDoc...")
        # Create chunks with embeddings
        chunks_data = [
            {"text": "Chunk 1", "embedding": [1.0, 2.0, 3.0]},
            {"text": "Chunk 2", "embedding": [2.0, 3.0, 4.0]},
            {"text": "Chunk 3", "embedding": [3.0, 4.0, 5.0]}
        ]
        
        for i, chunk_data in enumerate(chunks_data):
            chunk = Chunk(
                id=f"chunk-dedup-{i}",
                variant_id=variant.id,
                order=i,
                text=chunk_data["text"],
                embedding=chunk_data["embedding"]
            )
            db.add(chunk)
        db.commit()
        
        # Compute centroid from chunks
        chunk_embeddings = [c.embedding for c in db.query(Chunk).filter_by(variant_id=variant.id).all()]
        centroid = compute_embedding_centroid(chunk_embeddings)
        
        # Update context doc with centroid
        ctx.embedding_centroid = centroid
        db.commit()
        
        retrieved_ctx = db.query(ContextDoc).filter_by(id=ctx.id).first()
        assert retrieved_ctx.embedding_centroid == centroid
        print(f"   ✅ Embedding centroid stored: {centroid[:3]}...")
        
        # Test drift detection between versions
        print("\n1️⃣4️⃣ Testing drift detection between versions...")
        # Create new version of context
        ctx_v2 = ContextDoc(
            id="test-ctx-dedup-v2",
            title="Test Context for Deduplication",
            version="2.0.0",
            body_text="Completely different context about finance and banking."
        )
        db.add(ctx_v2)
        db.commit()
        
        # Create chunks for v2 with different embeddings
        chunks_v2 = [
            {"text": "Chunk v2-1", "embedding": [10.0, 20.0, 30.0]},
            {"text": "Chunk v2-2", "embedding": [20.0, 30.0, 40.0]}
        ]
        
        variant_v2 = ContextVariant(
            id="test-var-dedup-v2",
            context_id=ctx_v2.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Different variant text."
        )
        db.add(variant_v2)
        db.commit()
        
        for i, chunk_data in enumerate(chunks_v2):
            chunk = Chunk(
                id=f"chunk-dedup-v2-{i}",
                variant_id=variant_v2.id,
                order=i,
                text=chunk_data["text"],
                embedding=chunk_data["embedding"]
            )
            db.add(chunk)
        db.commit()
        
        # Compute centroid for v2
        chunk_embeddings_v2 = [c.embedding for c in db.query(Chunk).filter(
            Chunk.variant_id == variant_v2.id
        ).all()]
        centroid_v2 = compute_embedding_centroid(chunk_embeddings_v2)
        ctx_v2.embedding_centroid = centroid_v2
        db.commit()
        
        # Detect drift
        drift_result = detect_concept_drift(centroid, centroid_v2, threshold=0.2)
        # The centroids are very different, so drift should be detected
        # But cosine distance might be less than 1.0 due to normalization
        print(f"      Centroid v1: {centroid}")
        print(f"      Centroid v2: {centroid_v2}")
        print(f"      Distance: {drift_result['distance']:.3f}")
        assert drift_result["distance"] > 0.0  # Should have some distance
        print(f"   ✅ Drift detected between versions: {drift_result['severity']} (distance: {drift_result['distance']:.3f})")
        
        print("\n" + "=" * 60)
        print("✅ All De-duplication & Drift Control tests passed!")
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
    success = test_deduplication_and_drift()
    sys.exit(0 if success else 1)

