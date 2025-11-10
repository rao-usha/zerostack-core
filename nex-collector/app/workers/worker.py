"""Background workers for processing jobs."""
import json
import uuid
from sqlalchemy.orm import Session
from ..db import SessionLocal
from ..models import TeacherRun, ContextDoc, ContextVariant
from ..providers.registry import registry
from ..ingest.generator import ContextGenerator
from ..ingest.chunking import Chunker
from ..ingest.embed import Embedder
from ..ingest.features import FeatureExtractor


def process_teacher_run(run_id: str):
    """Process a teacher run: call LLM and save output."""
    db: Session = SessionLocal()
    
    try:
        # Get run
        run = db.query(TeacherRun).filter(TeacherRun.id == run_id).first()
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        # Get provider
        provider = registry.get_provider(run.provider)
        if not provider:
            raise ValueError(f"Provider {run.provider} not available")
        
        # Get example
        example = run.example
        input_data = example.input_json
        
        # Build messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": json.dumps(input_data, separators=(",", ":"), ensure_ascii=False)}
        ]
        
        # Call provider (sync for RQ)
        import asyncio
        
        async def call_provider():
            return await provider.chat(run.model, messages, run.params_json)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(call_provider())
        
        # Save output
        run.output_json = {
            "text": result["text"],
            "logprobs": result.get("logprobs")
        }
        run.usage_json = result["usage"]
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def process_aggregate_job(job_id: str, payload: dict):
    """Process an aggregation job: generate/mutate context."""
    db: Session = SessionLocal()
    
    try:
        context_id = payload.get("context_id")
        variant_id = payload.get("variant_id")
        provider = payload.get("provider", "openai")
        model = payload.get("model", "gpt-4o-mini")
        prompt = payload.get("prompt", "")
        seed = payload.get("seed")
        domain = payload.get("domain")
        persona = payload.get("persona")
        task = payload.get("task")
        
        # Generate context
        generator = ContextGenerator()
        
        if variant_id:
            # Mutate existing variant
            variant = db.query(ContextVariant).filter(ContextVariant.id == variant_id).first()
            if not variant:
                raise ValueError(f"Variant {variant_id} not found")
            
            body_text = generator.mutate(variant.body_text, prompt, provider, model, seed=seed)
            new_variant_id = f"var-{uuid.uuid4().hex[:12]}"
            
            new_variant = ContextVariant(
                id=new_variant_id,
                context_id=variant.context_id,
                domain=domain or variant.domain,
                persona=persona or variant.persona,
                task=task or variant.task,
                style=variant.style,
                constraints_json=variant.constraints_json,
                body_text=body_text,
                parent_variant_id=variant_id
            )
            db.add(new_variant)
            
        elif context_id:
            # Generate new variant for existing context
            context = db.query(ContextDoc).filter(ContextDoc.id == context_id).first()
            if not context:
                raise ValueError(f"Context {context_id} not found")
            
            # Format prompt with domain/persona/task
            formatted_prompt = prompt.format(domain=domain or "general", persona=persona or "general", task=task or "general")
            body_text = generator.generate(formatted_prompt, provider, model, seed=seed)
            
            new_variant_id = f"var-{uuid.uuid4().hex[:12]}"
            new_variant = ContextVariant(
                id=new_variant_id,
                context_id=context_id,
                domain=domain,
                persona=persona,
                task=task,
                body_text=body_text,
                constraints_json={}
            )
            db.add(new_variant)
            
        else:
            # Create new context and variant
            formatted_prompt = prompt.format(domain=domain or "general", persona=persona or "general", task=task or "general")
            body_text = generator.generate(formatted_prompt, provider, model, seed=seed)
            
            new_context_id = f"ctx-{uuid.uuid4().hex[:12]}"
            context = ContextDoc(
                id=new_context_id,
                title=f"Generated Context ({domain or 'general'})",
                version="1.0.0",
                body_text=body_text,
                metadata_json={"generated": True, "provider": provider, "model": model}
            )
            db.add(context)
            
            new_variant_id = f"var-{uuid.uuid4().hex[:12]}"
            new_variant = ContextVariant(
                id=new_variant_id,
                context_id=new_context_id,
                domain=domain,
                persona=persona,
                task=task,
                body_text=body_text,
                constraints_json={}
            )
            db.add(new_variant)
        
        # Extract features, chunk, embed
        extractor = FeatureExtractor()
        features = extractor.extract(new_variant.body_text, domain, persona, task)
        
        from ..models import FeatureVector
        feature_vector = FeatureVector(
            id=f"fv-{new_variant_id}",
            variant_id=new_variant_id,
            features_json=features
        )
        db.add(feature_vector)
        
        chunker = Chunker()
        chunks = chunker.chunk(new_variant.body_text)
        
        embedder = Embedder()
        embeddings = embedder.embed(chunks)
        
        from ..models import Chunk
        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = Chunk(
                id=f"chunk-{new_variant_id}-{i}",
                variant_id=new_variant_id,
                order=i,
                text=chunk_text,
                embedding=embedding
            )
            db.add(chunk)
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
