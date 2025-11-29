"""Seed script for end-to-end demo."""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import ContextDoc, ContextVariant, SyntheticExample, TeacherRun, DatasetManifest
from app.ingest.generator import ContextGenerator
from app.ingest.features import FeatureExtractor
from app.ingest.chunking import Chunker
from app.ingest.embed import Embedder
from app.distill.sampler import ExampleSampler
from app.distill.builder import build_dataset
from app.providers.registry import registry
from app.config import settings
import uuid


def seed_demo():
    """Run end-to-end demo flow."""
    db: Session = SessionLocal()
    
    try:
        print("🌱 Starting seed script...")
        
        # Step 1: Generate a context using OTS LLM
        print("\n1️⃣ Generating context from OTS LLM...")
        generator = ContextGenerator()
        
        prompt = """Generate a comprehensive context document for finance domain.
        Include:
        - Clear instructions for financial analysis
        - Key concepts and terminology
        - Example scenarios
        - Constraints and best practices"""
        
        body_text = generator.generate(
            prompt,
            provider="openai",
            model="gpt-4o-mini",
            seed=42
        )
        
        print(f"   ✓ Generated {len(body_text)} characters")
        
        # Step 2: Create ContextDoc
        print("\n2️⃣ Creating ContextDoc...")
        context_id = f"ctx-seed-{uuid.uuid4().hex[:8]}"
        context = ContextDoc(
            id=context_id,
            title="Finance Analysis Context (Seed)",
            version="1.0.0",
            body_text=body_text,
            metadata_json={"seed": True, "domain": "finance"}
        )
        db.add(context)
        db.commit()
        print(f"   ✓ Created ContextDoc: {context_id}")
        
        # Step 3: Create ContextVariant with facets
        print("\n3️⃣ Creating ContextVariant with facets...")
        variant_id = f"var-seed-{uuid.uuid4().hex[:8]}"
        variant = ContextVariant(
            id=variant_id,
            context_id=context_id,
            domain="finance",
            persona="CFO",
            task="analyze",
            style="formal",
            constraints_json={"max_length": 500, "require_citations": True},
            body_text=body_text
        )
        db.add(variant)
        
        # Extract features
        extractor = FeatureExtractor()
        features = extractor.extract(body_text, "finance", "CFO", "analyze", "formal")
        
        from app.models import FeatureVector
        feature_vector = FeatureVector(
            id=f"fv-{variant_id}",
            variant_id=variant_id,
            features_json=features
        )
        db.add(feature_vector)
        
        # Chunk and embed
        chunker = Chunker()
        chunks = chunker.chunk(body_text)
        
        embedder = Embedder()
        embeddings = embedder.embed(chunks)
        
        from app.models import Chunk
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(
                id=f"chunk-{variant_id}-{i}",
                variant_id=variant_id,
                order=i,
                text=chunk_text,
                embedding=embedding
            )
            db.add(chunk)
        
        db.commit()
        print(f"   ✓ Created ContextVariant: {variant_id}")
        print(f"   ✓ Extracted features: {features}")
        print(f"   ✓ Created {len(chunks)} chunks")
        
        # Step 4: Generate examples
        print("\n4️⃣ Generating synthetic examples...")
        sampler = ExampleSampler()
        from app.models import ExampleType
        
        example_ids = sampler.sample(
            db,
            [variant_id],
            ExampleType.INSTRUCTION,
            quota_per_variant=5,
            rules={}
        )
        print(f"   ✓ Generated {len(example_ids)} examples")
        
        # Step 5: Collect teacher outputs
        print("\n5️⃣ Collecting teacher outputs...")
        provider = registry.get_provider("openai")
        if not provider:
            print("   ⚠️ OpenAI provider not available, skipping teacher runs")
        else:
            examples = db.query(SyntheticExample).filter(
                SyntheticExample.id.in_(example_ids[:3])  # Just 3 for demo
            ).all()
            
            import asyncio
            import json
            
            async def collect_outputs():
                for example in examples:
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": json.dumps(example.input_json)}
                    ]
                    
                    result = await provider.chat("gpt-4o-mini", messages, {
                        "temperature": 0.7,
                        "max_tokens": 200
                    })
                    
                    teacher_run = TeacherRun(
                        id=f"tr-{uuid.uuid4().hex[:8]}",
                        example_id=example.id,
                        provider="openai",
                        model="gpt-4o-mini",
                        params_json={"temperature": 0.7, "max_tokens": 200},
                        output_json={"text": result["text"]},
                        usage_json=result["usage"]
                    )
                    db.add(teacher_run)
                    print(f"   ✓ Collected output for example {example.id[:12]}...")
                
                db.commit()
            
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(collect_outputs())
        
        # Step 6: Build fine-tune pack
        print("\n6️⃣ Building fine-tune pack...")
        dataset_id = f"ds-seed-{uuid.uuid4().hex[:8]}"
        
        from app.models import DatasetKind
        
        manifest = build_dataset(
            db,
            dataset_id,
            "finance-analysis-seed",
            "1.0.0",
            DatasetKind.FINETUNE_PACK,
            [variant_id],
            {"has_teacher_output": True}
        )
        
        dataset_manifest = DatasetManifest(
            id=dataset_id,
            name="finance-analysis-seed",
            version="1.0.0",
            kind=DatasetKind.FINETUNE_PACK,
            context_id=context_id,
            variant_ids=[variant_id],
            file_uris=[f["path"] for f in manifest.get("files", [])],
            filters_json={"has_teacher_output": True}
        )
        db.add(dataset_manifest)
        db.commit()
        
        print(f"   ✓ Built fine-tune pack: {dataset_id}")
        print(f"   ✓ Files: {[f['name'] for f in manifest.get('files', [])]}")
        print(f"   ✓ Examples: {manifest.get('num_examples', 0)}")
        
        print("\n✅ Seed script completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   - ContextDoc: {context_id}")
        print(f"   - ContextVariant: {variant_id}")
        print(f"   - Examples: {len(example_ids)}")
        print(f"   - Dataset: {dataset_id}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()

