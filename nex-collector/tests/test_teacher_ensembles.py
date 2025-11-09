#!/usr/bin/env python3
"""Simple test script for Teacher Ensembles & Self-Consistency (no pytest required)."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal, Base, engine
from app.models import (
    ContextDoc, ContextVariant, SyntheticExample, TeacherRun, ExampleType
)
from app.distill.ensemble import (
    majority_vote, borda_count, pairwise_preference, aggregate_ensemble
)


def test_teacher_ensembles():
    """Test teacher ensemble aggregation and reproducibility fields."""
    print("🧪 Testing Teacher Ensembles & Self-Consistency")
    print("=" * 60)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        # Create test context doc
        print("\n1️⃣ Creating test context document...")
        ctx = ContextDoc(
            id="test-ctx-ensemble",
            title="Test Context for Ensembles",
            version="1.0.0",
            body_text="Test context body text."
        )
        db.add(ctx)
        db.commit()
        print("   ✅ ContextDoc created")
        
        # Create test variant
        print("\n2️⃣ Creating test variant...")
        variant = ContextVariant(
            id="test-var-ensemble",
            context_id=ctx.id,
            domain="test",
            persona="tester",
            task="testing",
            body_text="Test variant body text."
        )
        db.add(variant)
        db.commit()
        print("   ✅ ContextVariant created")
        
        # Create test example
        print("\n3️⃣ Creating test example...")
        example = SyntheticExample(
            id="test-ex-ensemble",
            variant_id=variant.id,
            example_type=ExampleType.QA,
            input_json={"question": "What is the answer?"},
            constraints_json={},
            tags=[]
        )
        db.add(example)
        db.commit()
        print("   ✅ SyntheticExample created")
        
        # Create multiple teacher runs with different parameters
        print("\n4️⃣ Creating teacher runs with reproducibility fields...")
        runs_data = [
            {
                "id": "tr-ensemble-1",
                "output": "Answer A",
                "rand_seed": 42,
                "temperature": 0.7,
                "decoding_params": {"top_p": 0.9, "top_k": 50},
                "confidence": 0.9
            },
            {
                "id": "tr-ensemble-2",
                "output": "Answer A",
                "rand_seed": 43,
                "temperature": 0.7,
                "decoding_params": {"top_p": 0.9, "top_k": 50},
                "confidence": 0.85
            },
            {
                "id": "tr-ensemble-3",
                "output": "Answer B",
                "rand_seed": 44,
                "temperature": 0.8,
                "decoding_params": {"top_p": 0.95, "top_k": 40},
                "confidence": 0.75
            },
            {
                "id": "tr-ensemble-4",
                "output": "Answer A",
                "rand_seed": 45,
                "temperature": 0.7,
                "decoding_params": {"top_p": 0.9, "top_k": 50},
                "confidence": 0.88
            },
        ]
        
        teacher_runs = []
        for run_data in runs_data:
            run = TeacherRun(
                id=run_data["id"],
                example_id=example.id,
                provider="openai",
                model="gpt-4o-mini",
                params_json={"temperature": run_data["temperature"]},
                output_json={"text": run_data["output"]},
                rand_seed=run_data["rand_seed"],
                temperature=run_data["temperature"],
                decoding_params=run_data["decoding_params"],
                confidence=run_data["confidence"]
            )
            db.add(run)
            teacher_runs.append(run)
        db.commit()
        print(f"   ✅ Created {len(teacher_runs)} teacher runs with reproducibility fields")
        
        # Test reproducibility fields
        print("\n5️⃣ Testing reproducibility fields...")
        retrieved_run = db.query(TeacherRun).filter_by(id="tr-ensemble-1").first()
        assert retrieved_run.rand_seed == 42
        assert retrieved_run.temperature == 0.7
        assert retrieved_run.decoding_params == {"top_p": 0.9, "top_k": 50}
        print("   ✅ Reproducibility fields stored correctly")
        
        # Test majority vote
        print("\n6️⃣ Testing majority vote aggregation...")
        runs_dicts = [
            {"id": r.id, "output_json": r.output_json, "confidence": r.confidence}
            for r in teacher_runs
        ]
        majority_result = majority_vote(runs_dicts)
        assert majority_result == "Answer A"  # 3 out of 4 votes
        print(f"   ✅ Majority vote: {majority_result}")
        
        # Test Borda count
        print("\n7️⃣ Testing Borda count aggregation...")
        # Sort by confidence (descending)
        sorted_runs = sorted(runs_dicts, key=lambda x: x["confidence"], reverse=True)
        borda_result = borda_count(sorted_runs)
        assert borda_result == "Answer A"  # Should win due to higher confidence
        print(f"   ✅ Borda count: {borda_result}")
        
        # Test pairwise preference
        print("\n8️⃣ Testing pairwise preference aggregation...")
        pairwise_result = pairwise_preference(runs_dicts)
        assert pairwise_result == "Answer A"  # Should win pairwise comparisons
        print(f"   ✅ Pairwise preference: {pairwise_result}")
        
        # Test aggregate_ensemble function
        print("\n9️⃣ Testing aggregate_ensemble function...")
        aggregated_mv, metadata_mv = aggregate_ensemble(teacher_runs, method="majority_vote")
        assert aggregated_mv == "Answer A"
        assert metadata_mv["method"] == "majority_vote"
        assert metadata_mv["num_runs"] == 4
        assert len(metadata_mv["run_details"]) == 4
        print(f"   ✅ aggregate_ensemble (majority_vote): {aggregated_mv}")
        print(f"      Metadata: {len(metadata_mv['run_details'])} runs")
        
        aggregated_bc, metadata_bc = aggregate_ensemble(teacher_runs, method="borda_count")
        assert aggregated_bc == "Answer A"
        print(f"   ✅ aggregate_ensemble (borda_count): {aggregated_bc}")
        
        aggregated_pp, metadata_pp = aggregate_ensemble(teacher_runs, method="pairwise_preference")
        assert aggregated_pp == "Answer A"
        print(f"   ✅ aggregate_ensemble (pairwise_preference): {aggregated_pp}")
        
        # Test with different outputs (tie scenario)
        print("\n🔟 Testing tie scenario...")
        tie_runs = [
            {"id": "tie-1", "output_json": {"text": "Answer X"}, "confidence": 0.9},
            {"id": "tie-2", "output_json": {"text": "Answer Y"}, "confidence": 0.9},
            {"id": "tie-3", "output_json": {"text": "Answer X"}, "confidence": 0.8},
        ]
        tie_result = majority_vote(tie_runs)
        assert tie_result == "Answer X"  # 2 out of 3 votes
        print(f"   ✅ Tie scenario handled: {tie_result}")
        
        # Test optional fields
        print("\n1️⃣1️⃣ Testing optional reproducibility fields...")
        run_no_params = TeacherRun(
            id="tr-no-params",
            example_id=example.id,
            provider="openai",
            model="gpt-4o-mini",
            params_json={},
            output_json={"text": "Answer"}
        )
        db.add(run_no_params)
        db.commit()
        
        retrieved_no_params = db.query(TeacherRun).filter_by(id="tr-no-params").first()
        assert retrieved_no_params.rand_seed is None
        assert retrieved_no_params.temperature is None
        assert retrieved_no_params.decoding_params is None
        print("   ✅ Optional reproducibility fields work correctly")
        
        print("\n" + "=" * 60)
        print("✅ All Teacher Ensemble & Self-Consistency tests passed!")
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
    success = test_teacher_ensembles()
    sys.exit(0 if success else 1)

