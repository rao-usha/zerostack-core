"""
Distillation Workbench API router.

Provides endpoints for:
- Domain/topic/tag management
- Task library (CRUD + execution)
- Interactive chat with multi-model support
- Response bank and curation
- Model comparisons and voting
- Dataset building
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlmodel import Session

from .db_models import DistillationRun, DistillationResponse
from .models import (
    # Domain/Topic/Tag
    DomainCreate, DomainUpdate, DomainResponse, DomainListResponse,
    TopicCreate, TopicUpdate, TopicResponse, TopicListResponse,
    TagCreate, TagResponse,
    # Tasks
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    # Runs
    RunCreate, RunResponse, RunListResponse, TriggerType, RunStatus,
    # Responses
    ResponseResponse, ResponseUpdate, ResponseListResponse,
    # Banking
    BankCreate, BankedResponse, BankedUpdate, BankedListResponse, BankedStatus,
    # Comparisons
    ComparisonCreate, ComparisonResponse, VoteCreate, VoteResponse,
    # Interactive
    InteractiveChatRequest, InteractiveChatResponse,
    # Datasets
    DatasetCreate, DatasetResponse, DatasetListResponse, DatasetItemAdd,
    # Structured (Phase 5)
    StructuredCreate, StructuredUpdate, StructuredResponse,
    # Expert Review (Phase 6)
    ReviewQueueCreate, ReviewQueueUpdate, ReviewQueueResponse,
    ReviewItemCreate, ReviewItemUpdate, ReviewItemResponse,
    ReviewAction, ReviewExportResponse, ReviewImportRequest
)
from .service import DistillationService
from db_session import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/distillation", tags=["distillation"])


# ============================================
# Helper Functions
# ============================================

def _serialize_response(r, tags=None) -> dict:
    """Serialize a DistillationResponse to dict with tags."""
    return {
        "id": str(r.id),
        "run_id": str(r.run_id),
        "provider": r.provider,
        "model": r.model,
        "prompt_sent": r.prompt_sent,
        "system_prompt_used": r.system_prompt_used,
        "response_text": r.response_text,
        "tokens_input": r.tokens_input,
        "tokens_output": r.tokens_output,
        "latency_ms": r.latency_ms,
        "domain_id": str(r.domain_id) if r.domain_id else None,
        "topic_id": str(r.topic_id) if r.topic_id else None,
        "quality_rating": r.quality_rating,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "tags": tags or []
    }


# ============================================
# Domain Management
# ============================================

@router.post("/domains", response_model=DomainResponse, status_code=201)
async def create_domain(
    data: DomainCreate,
    session: Session = Depends(get_session)
):
    """Create a new knowledge domain."""
    try:
        domain = DistillationService.create_domain(session, data)
        return DomainResponse(**domain.model_dump(), topic_count=0)
    except Exception as e:
        logger.error(f"Failed to create domain: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/domains", response_model=DomainListResponse)
async def list_domains(session: Session = Depends(get_session)):
    """List all domains."""
    domains = DistillationService.list_domains(session)
    return DomainListResponse(
        domains=[DomainResponse(**d.model_dump(), topic_count=len(d.topics) if d.topics else 0) for d in domains],
        total=len(domains)
    )


@router.get("/domains/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: UUID, session: Session = Depends(get_session)):
    """Get a domain by ID."""
    domain = DistillationService.get_domain(session, domain_id)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return DomainResponse(**domain.model_dump(), topic_count=len(domain.topics) if domain.topics else 0)


@router.patch("/domains/{domain_id}", response_model=DomainResponse)
async def update_domain(
    domain_id: UUID,
    data: DomainUpdate,
    session: Session = Depends(get_session)
):
    """Update a domain."""
    domain = DistillationService.update_domain(session, domain_id, data)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return DomainResponse(**domain.model_dump(), topic_count=len(domain.topics) if domain.topics else 0)


@router.delete("/domains/{domain_id}", status_code=204)
async def delete_domain(domain_id: UUID, session: Session = Depends(get_session)):
    """Delete a domain."""
    if not DistillationService.delete_domain(session, domain_id):
        raise HTTPException(status_code=404, detail="Domain not found")


# ============================================
# Topic Management
# ============================================

@router.post("/topics", response_model=TopicResponse, status_code=201)
async def create_topic(
    data: TopicCreate,
    session: Session = Depends(get_session)
):
    """Create a new topic within a domain."""
    try:
        topic = DistillationService.create_topic(session, data)
        return TopicResponse(**topic.model_dump())
    except Exception as e:
        logger.error(f"Failed to create topic: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/domains/{domain_id}/topics", response_model=TopicListResponse)
async def list_topics_for_domain(domain_id: UUID, session: Session = Depends(get_session)):
    """List all topics for a domain."""
    topics = DistillationService.get_topics_for_domain(session, domain_id)
    return TopicListResponse(
        topics=[TopicResponse(**t.model_dump()) for t in topics],
        total=len(topics)
    )


@router.patch("/topics/{topic_id}", response_model=TopicResponse)
async def update_topic(
    topic_id: UUID,
    data: TopicUpdate,
    session: Session = Depends(get_session)
):
    """Update a topic."""
    topic = DistillationService.update_topic(session, topic_id, data)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return TopicResponse(**topic.model_dump())


@router.delete("/topics/{topic_id}", status_code=204)
async def delete_topic(topic_id: UUID, session: Session = Depends(get_session)):
    """Delete a topic."""
    if not DistillationService.delete_topic(session, topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")


# ============================================
# Tag Management
# ============================================

@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(
    data: TagCreate,
    session: Session = Depends(get_session)
):
    """Create a new tag."""
    try:
        tag = DistillationService.create_tag(session, data)
        return TagResponse(**tag.model_dump())
    except Exception as e:
        logger.error(f"Failed to create tag: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(session: Session = Depends(get_session)):
    """List all tags."""
    tags = DistillationService.list_tags(session)
    return [TagResponse(**t.model_dump()) for t in tags]


# ============================================
# Task Library
# ============================================

@router.post("/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    data: TaskCreate,
    session: Session = Depends(get_session)
):
    """Create a new task template."""
    try:
        task = DistillationService.create_task(session, data)
        return TaskResponse(**task.model_dump())
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    domain_id: Optional[UUID] = Query(default=None),
    topic_id: Optional[UUID] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List tasks with optional filters."""
    tasks = DistillationService.list_tasks(
        session, domain_id=domain_id, topic_id=topic_id,
        is_active=is_active, skip=skip, limit=limit
    )
    return TaskListResponse(
        tasks=[TaskResponse(**t.model_dump()) for t in tasks],
        total=len(tasks)
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, session: Session = Depends(get_session)):
    """Get a task by ID."""
    task = DistillationService.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.model_dump())


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    session: Session = Depends(get_session)
):
    """Update a task."""
    task = DistillationService.update_task(session, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task.model_dump())


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: UUID, session: Session = Depends(get_session)):
    """Delete a task."""
    if not DistillationService.delete_task(session, task_id):
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/tasks/{task_id}/run", response_model=RunResponse)
async def run_task(
    task_id: UUID,
    variables: dict = {},
    background_tasks: BackgroundTasks = None,
    session: Session = Depends(get_session)
):
    """Execute a task immediately."""
    task = DistillationService.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create run
    run_data = RunCreate(
        task_id=task_id,
        variables=variables,
        domain_id=task.domain_id,
        topic_id=task.topic_id
    )
    run = DistillationService.create_run(session, run_data, trigger_type=TriggerType.MANUAL)
    
    # Execute in background or synchronously
    try:
        import asyncio
        run = asyncio.get_event_loop().run_until_complete(
            DistillationService.execute_run(session, run)
        )
    except RuntimeError:
        # Already in async context
        run = await DistillationService.execute_run(session, run)
    
    response_count = len(DistillationService.get_responses_for_run(session, run.id))
    return RunResponse(**run.model_dump(), response_count=response_count)


# ============================================
# Runs
# ============================================

@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    task_id: Optional[UUID] = Query(default=None),
    status: Optional[RunStatus] = Query(default=None),
    trigger_type: Optional[TriggerType] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List runs with optional filters."""
    runs = DistillationService.list_runs(
        session, task_id=task_id, status=status,
        trigger_type=trigger_type, skip=skip, limit=limit
    )
    return RunListResponse(
        runs=[RunResponse(**r.model_dump(), response_count=len(r.responses) if r.responses else 0) for r in runs],
        total=len(runs)
    )


@router.get("/runs/{run_id}", response_model=RunResponse)
async def get_run(run_id: UUID, session: Session = Depends(get_session)):
    """Get a run by ID."""
    run = DistillationService.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    response_count = len(DistillationService.get_responses_for_run(session, run.id))
    return RunResponse(**run.model_dump(), response_count=response_count)


@router.get("/runs/{run_id}/responses", response_model=List[ResponseResponse])
async def get_run_responses(run_id: UUID, session: Session = Depends(get_session)):
    """Get all responses for a run."""
    responses = DistillationService.get_responses_for_run(session, run_id)
    return [_serialize_response(r) for r in responses]


# ============================================
# Interactive Chat
# ============================================

@router.post("/chat")
async def interactive_chat(
    data: InteractiveChatRequest,
    session: Session = Depends(get_session)
):
    """
    Interactive chat with SOTA models (non-streaming).
    
    Send a message to one or more models and get responses.
    Optionally create a comparison for multi-model runs.
    """
    try:
        logger.info(f"Starting interactive chat with models: {data.models}")
        result = await DistillationService.interactive_chat(session, data)
        
        # Get the run to check for errors
        run = DistillationService.get_run(session, result["run_id"])
        
        # Build response list
        response_list = []
        for r in result["responses"]:
            try:
                response_list.append(_serialize_response(r))
            except Exception as e:
                logger.error(f"Failed to serialize response {r.id if hasattr(r, 'id') else 'unknown'}: {e}")
        
        return {
            "run_id": str(result["run_id"]),
            "responses": response_list,
            "comparison_id": str(result["comparison_id"]) if result.get("comparison_id") else None,
            "status": run.status if run else "unknown",
            "error": run.error_message if run else None
        }
    except Exception as e:
        logger.error(f"Interactive chat failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def interactive_chat_stream(
    data: InteractiveChatRequest,
    session: Session = Depends(get_session)
):
    """
    Interactive chat with SOTA models (streaming) - CONCURRENT execution.
    
    All selected models run simultaneously, streaming their outputs as they generate.
    
    Returns Server-Sent Events with:
    - status: Stage updates (starting, model_start, model_streaming, model_complete, etc.)
    - delta: Streaming text chunks per model
    - complete: Final response with all data
    - error: Error messages
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def generate_stream():
        try:
            # Send initial status
            yield "event: status\n"
            yield f"data: {json.dumps({'stage': 'starting', 'message': 'Initializing...'})}\n\n"
            await asyncio.sleep(0)
            
            # Create run record
            run = DistillationRun(
                ad_hoc_prompt=data.message,
                ad_hoc_system_prompt=data.system_prompt,
                ad_hoc_models=data.models,
                variables_used={},
                trigger_type=TriggerType.INTERACTIVE.value,
                domain_id=data.domain_id,
                topic_id=data.topic_id,
                status=RunStatus.RUNNING.value,
                started_at=datetime.utcnow()
            )
            session.add(run)
            session.commit()
            session.refresh(run)
            
            yield "event: status\n"
            yield f"data: {json.dumps({'stage': 'run_created', 'run_id': str(run.id)})}\n\n"
            await asyncio.sleep(0)
            
            # Queue for collecting events from all concurrent model streams
            event_queue = asyncio.Queue()
            
            # Track results per model
            model_results = {}  # model_spec -> {content: [], error: None, latency: 0, response: None}
            
            async def stream_model(model_spec: str, index: int):
                """Stream a single model and put events into the queue."""
                # Parse provider:model
                if ":" in model_spec:
                    provider_name, model_name = model_spec.split(":", 1)
                elif model_spec.startswith("claude"):
                    provider_name, model_name = "anthropic", model_spec
                elif model_spec.startswith("gemini"):
                    provider_name, model_name = "google", model_spec
                elif model_spec.startswith("grok"):
                    provider_name, model_name = "xai", model_spec
                else:
                    provider_name, model_name = "openai", model_spec
                
                model_results[model_spec] = {"content": [], "error": None, "latency": 0, "response": None}
                
                await event_queue.put({
                    "event": "status",
                    "data": {"stage": "model_start", "model": model_spec, "provider": provider_name, "index": index}
                })
                
                try:
                    from llm.providers import get_provider
                    provider = get_provider(provider_name, model_name)
                    
                    messages = []
                    if data.system_prompt:
                        messages.append({"role": "system", "content": data.system_prompt})
                    messages.append({"role": "user", "content": data.message})
                    
                    start_time = datetime.utcnow()
                    
                    # Stream the response
                    async for event in provider.stream_chat(messages=messages):
                        event_type = event.get("type")
                        if event_type == "delta":
                            content = event.get("content", "")
                            model_results[model_spec]["content"].append(content)
                            await event_queue.put({
                                "event": "delta",
                                "data": {"model": model_spec, "content": content, "index": index}
                            })
                        elif event_type == "error":
                            error_msg = event.get("error", "Unknown error")
                            model_results[model_spec]["error"] = error_msg
                            await event_queue.put({
                                "event": "error",
                                "data": {"model": model_spec, "error": error_msg}
                            })
                            return
                    
                    end_time = datetime.utcnow()
                    latency = int((end_time - start_time).total_seconds() * 1000)
                    response_text = "".join(model_results[model_spec]["content"])
                    model_results[model_spec]["latency"] = latency
                    
                    logger.info(f"Model {model_spec} completed: {len(model_results[model_spec]['content'])} chunks, {len(response_text)} chars, {latency}ms")
                    
                    # Save response to database
                    response = DistillationResponse(
                        run_id=run.id,
                        provider=provider_name,
                        model=model_name,
                        prompt_sent=data.message,
                        system_prompt_used=data.system_prompt,
                        response_text=response_text,
                        latency_ms=latency,
                        domain_id=data.domain_id,
                        topic_id=data.topic_id
                    )
                    session.add(response)
                    session.commit()
                    session.refresh(response)
                    model_results[model_spec]["response"] = response
                    
                    await event_queue.put({
                        "event": "status",
                        "data": {"stage": "model_complete", "model": model_spec, "latency_ms": latency, "response_id": str(response.id)}
                    })
                    
                except Exception as e:
                    error_msg = f"{provider_name}/{model_name}: {str(e)}"
                    model_results[model_spec]["error"] = error_msg
                    await event_queue.put({
                        "event": "error", 
                        "data": {"model": model_spec, "error": str(e)}
                    })
                    logger.error(f"Model {model_spec} failed: {e}")
            
            # Start all model streams concurrently
            tasks = [
                asyncio.create_task(stream_model(model_spec, i))
                for i, model_spec in enumerate(data.models)
            ]
            
            # Consumer: yield events from queue while tasks are running
            completed_count = 0
            total_models = len(data.models)
            
            while completed_count < total_models:
                # Check if all tasks are done
                done_tasks = [t for t in tasks if t.done()]
                
                # Try to get events from queue with timeout
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield f"event: {event['event']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                    
                    # Track completions
                    if event['event'] == 'status' and event['data'].get('stage') == 'model_complete':
                        completed_count += 1
                    elif event['event'] == 'error' and 'model' in event['data']:
                        # Check if this model hasn't already been counted
                        model = event['data']['model']
                        if model_results.get(model, {}).get("error"):
                            completed_count += 1
                            
                except asyncio.TimeoutError:
                    # No events available, check if tasks completed with errors
                    for task in done_tasks:
                        if task not in [t for t in tasks if t.done()]:
                            continue
                    
                    # Count models that are done (either completed or errored)
                    done_models = sum(1 for m, r in model_results.items() 
                                     if r.get("response") is not None or r.get("error") is not None)
                    if done_models >= total_models:
                        break
                    
                    await asyncio.sleep(0)
            
            # Wait for all tasks to fully complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Drain any remaining events from queue
            while not event_queue.empty():
                try:
                    event = event_queue.get_nowait()
                    yield f"event: {event['event']}\n"
                    yield f"data: {json.dumps(event['data'])}\n\n"
                except asyncio.QueueEmpty:
                    break
            
            # Collect results
            responses = [r["response"] for r in model_results.values() if r.get("response")]
            errors = [r["error"] for r in model_results.values() if r.get("error")]
            
            # Update run status
            if len(responses) == 0:
                run.status = RunStatus.FAILED.value
                run.error_message = "All models failed: " + "; ".join(errors)
            elif len(errors) > 0:
                run.status = RunStatus.COMPLETED.value
                run.error_message = "Some models failed: " + "; ".join(errors)
            else:
                run.status = RunStatus.COMPLETED.value
            run.completed_at = datetime.utcnow()
            session.add(run)
            session.commit()
            
            # Create comparison if requested
            comparison_id = None
            if data.create_comparison and len(responses) > 1:
                comparison_data = ComparisonCreate(
                    response_ids=[r.id for r in responses],
                    comparison_type="side_by_side",
                    prompt_used=data.message
                )
                comparison = DistillationService.create_comparison(session, comparison_data, run_id=run.id)
                comparison_id = comparison.id
            
            # Send complete event with all responses
            response_list = [_serialize_response(r) for r in responses]
            yield "event: complete\n"
            yield f"data: {json.dumps({'run_id': str(run.id), 'responses': response_list, 'comparison_id': str(comparison_id) if comparison_id else None, 'status': run.status, 'error': run.error_message})}\n\n"
            
        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield "event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================
# Response Bank
# ============================================

@router.get("/responses", response_model=ResponseListResponse)
async def list_responses(
    domain_id: Optional[UUID] = Query(default=None),
    topic_id: Optional[UUID] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List responses with optional filters."""
    responses = DistillationService.list_responses(
        session, domain_id=domain_id, topic_id=topic_id,
        provider=provider, model=model, skip=skip, limit=limit
    )
    return {
        "responses": [_serialize_response(r) for r in responses],
        "total": len(responses)
    }


@router.get("/responses/{response_id}")
async def get_response(response_id: UUID, session: Session = Depends(get_session)):
    """Get a response by ID."""
    response = DistillationService.get_response(session, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return _serialize_response(response)


@router.patch("/responses/{response_id}")
async def update_response(
    response_id: UUID,
    data: ResponseUpdate,
    session: Session = Depends(get_session)
):
    """Update a response (domain, topic, tags, rating)."""
    response = DistillationService.update_response(session, response_id, data)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    return _serialize_response(response)


@router.delete("/responses/{response_id}", status_code=204)
async def delete_response(
    response_id: UUID,
    session: Session = Depends(get_session)
):
    """Delete a response."""
    success = DistillationService.delete_response(session, response_id)
    if not success:
        raise HTTPException(status_code=404, detail="Response not found")
    return None


@router.post("/responses/{response_id}/bank", response_model=BankedResponse)
async def bank_response(
    response_id: UUID,
    quality_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    notes: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Bank a response for curation."""
    response = DistillationService.get_response(session, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    data = BankCreate(
        response_id=response_id,
        domain_id=response.domain_id,
        topic_id=response.topic_id,
        quality_score=quality_score,
        notes=notes
    )
    banked = DistillationService.bank_response(session, data)
    return BankedResponse(**banked.model_dump())


# ============================================
# Banked Responses
# ============================================

@router.get("/banked", response_model=BankedListResponse)
async def list_banked(
    domain_id: Optional[UUID] = Query(default=None),
    topic_id: Optional[UUID] = Query(default=None),
    status: Optional[BankedStatus] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List banked responses with optional filters."""
    banked = DistillationService.list_banked(
        session, domain_id=domain_id, topic_id=topic_id,
        status=status, skip=skip, limit=limit
    )
    return BankedListResponse(
        banked=[BankedResponse(**b.model_dump()) for b in banked],
        total=len(banked)
    )


@router.get("/banked/{banked_id}", response_model=BankedResponse)
async def get_banked(banked_id: UUID, session: Session = Depends(get_session)):
    """Get a banked response by ID."""
    banked = DistillationService.get_banked(session, banked_id)
    if not banked:
        raise HTTPException(status_code=404, detail="Banked response not found")
    
    # Include the original response
    response = DistillationService.get_response(session, banked.response_id)
    result = banked.model_dump()
    result["response"] = _serialize_response(response) if response else None
    return result


@router.patch("/banked/{banked_id}", response_model=BankedResponse)
async def update_banked(
    banked_id: UUID,
    data: BankedUpdate,
    session: Session = Depends(get_session)
):
    """Update a banked response."""
    banked = DistillationService.update_banked(session, banked_id, data)
    if not banked:
        raise HTTPException(status_code=404, detail="Banked response not found")
    return BankedResponse(**banked.model_dump())


# ============================================
# Comparisons
# ============================================

@router.post("/comparisons", response_model=ComparisonResponse, status_code=201)
async def create_comparison(
    data: ComparisonCreate,
    session: Session = Depends(get_session)
):
    """Create a new comparison between responses."""
    try:
        comparison = DistillationService.create_comparison(session, data)
        return ComparisonResponse(**comparison.model_dump(), responses=[], votes=[])
    except Exception as e:
        logger.error(f"Failed to create comparison: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comparisons/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(comparison_id: UUID, session: Session = Depends(get_session)):
    """Get a comparison by ID with responses and votes."""
    comparison = DistillationService.get_comparison(session, comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    # TODO: Load responses and votes
    return ComparisonResponse(**comparison.model_dump(), responses=[], votes=[])


@router.post("/comparisons/{comparison_id}/vote", response_model=VoteResponse, status_code=201)
async def submit_vote(
    comparison_id: UUID,
    data: VoteCreate,
    session: Session = Depends(get_session)
):
    """Submit a vote on a comparison."""
    comparison = DistillationService.get_comparison(session, comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    data.comparison_id = comparison_id
    vote = DistillationService.submit_vote(session, data)
    return VoteResponse(**vote.model_dump())


# ============================================
# Datasets
# ============================================

@router.post("/datasets", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    data: DatasetCreate,
    session: Session = Depends(get_session)
):
    """Create a new dataset."""
    try:
        dataset = DistillationService.create_dataset(session, data)
        return DatasetResponse(**dataset.model_dump())
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets", response_model=DatasetListResponse)
async def list_datasets(
    domain_id: Optional[UUID] = Query(default=None),
    dataset_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List datasets with optional filters."""
    datasets = DistillationService.list_datasets(
        session, domain_id=domain_id, dataset_type=dataset_type,
        status=status, skip=skip, limit=limit
    )
    return DatasetListResponse(
        datasets=[DatasetResponse(**d.model_dump()) for d in datasets],
        total=len(datasets)
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: UUID, session: Session = Depends(get_session)):
    """Get a dataset by ID."""
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse(**dataset.model_dump())


@router.post("/datasets/{dataset_id}/items")
async def add_items_to_dataset(
    dataset_id: UUID,
    data: DatasetItemAdd,
    session: Session = Depends(get_session)
):
    """Add items to a dataset."""
    count = DistillationService.add_items_to_dataset(
        session, dataset_id,
        banked_ids=data.banked_ids,
        structured_ids=data.structured_ids,
        split=data.split
    )
    return {"items_added": count}


# ============================================
# Phase 3: Enhanced Response Bank
# ============================================

@router.post("/responses/search")
async def search_responses(
    query: Optional[str] = Query(default=None, description="Text search in response and prompt"),
    domain_id: Optional[UUID] = Query(default=None),
    topic_id: Optional[UUID] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    model: Optional[str] = Query(default=None),
    tag_ids: Optional[str] = Query(default=None, description="Comma-separated tag UUIDs"),
    is_banked: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """
    Advanced search for responses with text search and filters.
    
    - query: Search text in response_text and prompt_sent
    - tag_ids: Comma-separated list of tag UUIDs to filter by
    - is_banked: Filter for banked (True) or not banked (False) responses
    """
    # Parse tag_ids from comma-separated string
    parsed_tag_ids = None
    if tag_ids:
        try:
            parsed_tag_ids = [UUID(t.strip()) for t in tag_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tag_ids format")
    
    result = DistillationService.search_responses(
        session,
        query=query,
        domain_id=domain_id,
        topic_id=topic_id,
        provider=provider,
        model=model,
        tag_ids=parsed_tag_ids,
        is_banked=is_banked,
        skip=skip,
        limit=limit
    )
    
    # Get tags for each response
    responses_with_tags = []
    for r in result["responses"]:
        tags = DistillationService.get_response_tags(session, r.id)
        tag_list = [{"id": str(t.id), "name": t.name, "color": t.color} for t in tags]
        responses_with_tags.append(_serialize_response(r, tags=tag_list))
    
    return {
        "responses": responses_with_tags,
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"]
    }


@router.get("/responses/{response_id}/tags", response_model=List[TagResponse])
async def get_response_tags(response_id: UUID, session: Session = Depends(get_session)):
    """Get all tags for a response."""
    response = DistillationService.get_response(session, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    tags = DistillationService.get_response_tags(session, response_id)
    return [TagResponse(**t.model_dump()) for t in tags]


@router.post("/responses/{response_id}/tags", response_model=List[TagResponse])
async def add_tags_to_response(
    response_id: UUID,
    tag_names: List[str],
    session: Session = Depends(get_session)
):
    """Add tags to a response by name. Creates tags if they don't exist."""
    response = DistillationService.get_response(session, response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")
    
    tags = DistillationService.add_tags_to_response(session, response_id, tag_names)
    return [TagResponse(**t.model_dump()) for t in tags]


@router.delete("/responses/{response_id}/tags/{tag_id}", status_code=204)
async def remove_tag_from_response(
    response_id: UUID,
    tag_id: UUID,
    session: Session = Depends(get_session)
):
    """Remove a tag from a response."""
    if not DistillationService.remove_tag_from_response(session, response_id, tag_id):
        raise HTTPException(status_code=404, detail="Tag link not found")


@router.get("/statistics")
async def get_statistics(session: Session = Depends(get_session)):
    """Get overall distillation statistics."""
    return DistillationService.get_response_statistics(session)


# ============================================
# Phase 4: Enhanced Comparisons & Voting
# ============================================

@router.get("/comparisons")
async def list_comparisons(
    status: Optional[str] = Query(default=None, description="Filter by status: pending, completed"),
    comparison_type: Optional[str] = Query(default=None, description="Filter by type: side_by_side, blind, ab_preference"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List all comparisons with optional filters."""
    comparisons = DistillationService.list_comparisons(
        session, status=status, comparison_type=comparison_type, skip=skip, limit=limit
    )
    return {
        "comparisons": [ComparisonResponse(**c.model_dump(), responses=[], votes=[]) for c in comparisons],
        "total": len(comparisons)
    }


@router.get("/comparisons/{comparison_id}/details")
async def get_comparison_details(comparison_id: UUID, session: Session = Depends(get_session)):
    """Get a comparison with full details including responses and votes."""
    result = DistillationService.get_comparison_with_details(session, comparison_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    comparison = result["comparison"]
    
    # Format responses with display info
    formatted_responses = []
    for item in result["responses"]:
        resp = item["response"]
        tags = DistillationService.get_response_tags(session, resp.id)
        tag_list = [{"id": str(t.id), "name": t.name, "color": t.color} for t in tags]
        formatted_responses.append({
            "response": _serialize_response(resp, tags=tag_list),
            "display_order": item["display_order"],
            "display_label": item["display_label"]
        })
    
    # Format votes
    formatted_votes = [VoteResponse(**v.model_dump()) for v in result["votes"]]
    
    return {
        "comparison": ComparisonResponse(**comparison.model_dump(), responses=[], votes=[]),
        "responses": formatted_responses,
        "votes": formatted_votes,
        "vote_count": result["vote_count"]
    }


@router.get("/comparisons/{comparison_id}/votes", response_model=List[VoteResponse])
async def get_comparison_votes(comparison_id: UUID, session: Session = Depends(get_session)):
    """Get all votes for a comparison."""
    comparison = DistillationService.get_comparison(session, comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    votes = DistillationService.get_comparison_votes(session, comparison_id)
    return [VoteResponse(**v.model_dump()) for v in votes]


@router.get("/comparisons/{comparison_id}/statistics")
async def get_comparison_statistics(comparison_id: UUID, session: Session = Depends(get_session)):
    """Get vote statistics for a specific comparison."""
    comparison = DistillationService.get_comparison(session, comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparison not found")
    
    return DistillationService.get_vote_statistics(session, comparison_id)


@router.post("/comparisons/blind", status_code=201)
async def create_blind_comparison(
    response_ids: List[UUID],
    prompt_used: str,
    session: Session = Depends(get_session)
):
    """Create a blind comparison where response order is randomized and labeled A, B, C..."""
    if len(response_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 responses required for comparison")
    
    # Verify all responses exist
    for response_id in response_ids:
        if not DistillationService.get_response(session, response_id):
            raise HTTPException(status_code=404, detail=f"Response {response_id} not found")
    
    comparison = DistillationService.create_blind_comparison(
        session, response_ids, prompt_used
    )
    
    return ComparisonResponse(**comparison.model_dump(), responses=[], votes=[])


@router.get("/model-preferences")
async def get_model_preferences(session: Session = Depends(get_session)):
    """Get overall model preference statistics from all comparisons."""
    return DistillationService.get_model_preference_stats(session)


# ============================================
# Phase 5: Structuring
# ============================================

@router.get("/schemas")
async def get_schema_definitions():
    """Get all available schema definitions for structuring."""
    schemas = DistillationService.get_schema_definitions()
    return {
        "schemas": [
            {"key": key, **value}
            for key, value in schemas.items()
        ]
    }


@router.post("/structured", status_code=201)
async def create_structured(
    data: StructuredCreate,
    session: Session = Depends(get_session)
):
    """Create a structured extraction from a banked response."""
    # Verify banked exists
    banked = DistillationService.get_banked(session, data.banked_id)
    if not banked:
        raise HTTPException(status_code=404, detail="Banked response not found")
    
    # Verify schema is valid
    schemas = DistillationService.get_schema_definitions()
    if data.schema_name not in schemas:
        raise HTTPException(status_code=400, detail=f"Invalid schema: {data.schema_name}")
    
    structured = DistillationService.create_structured(
        session,
        banked_id=data.banked_id,
        schema_name=data.schema_name,
        structured_data=data.structured_data,
        extraction_method=data.extraction_method
    )
    return StructuredResponse(**structured.model_dump())


@router.get("/structured")
async def list_structured(
    schema_name: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List structured extractions with optional filters."""
    items = DistillationService.list_structured(session, schema_name=schema_name, skip=skip, limit=limit)
    return {
        "structured": [StructuredResponse(**s.model_dump()) for s in items],
        "total": len(items)
    }


@router.get("/structured/{structured_id}")
async def get_structured(structured_id: UUID, session: Session = Depends(get_session)):
    """Get a structured extraction by ID."""
    structured = DistillationService.get_structured(session, structured_id)
    if not structured:
        raise HTTPException(status_code=404, detail="Structured extraction not found")
    return StructuredResponse(**structured.model_dump())


@router.patch("/structured/{structured_id}")
async def update_structured(
    structured_id: UUID,
    data: StructuredUpdate,
    session: Session = Depends(get_session)
):
    """Update structured data."""
    structured = DistillationService.update_structured(session, structured_id, data.structured_data)
    if not structured:
        raise HTTPException(status_code=404, detail="Structured extraction not found")
    return StructuredResponse(**structured.model_dump())


@router.delete("/structured/{structured_id}", status_code=204)
async def delete_structured(structured_id: UUID, session: Session = Depends(get_session)):
    """Delete a structured extraction."""
    if not DistillationService.delete_structured(session, structured_id):
        raise HTTPException(status_code=404, detail="Structured extraction not found")


@router.get("/banked/{banked_id}/structured")
async def get_structured_for_banked(banked_id: UUID, session: Session = Depends(get_session)):
    """Get all structured extractions for a banked response."""
    banked = DistillationService.get_banked(session, banked_id)
    if not banked:
        raise HTTPException(status_code=404, detail="Banked response not found")
    
    items = DistillationService.get_structured_for_banked(session, banked_id)
    return {
        "structured": [StructuredResponse(**s.model_dump()) for s in items],
        "total": len(items)
    }


@router.post("/banked/{banked_id}/extract")
async def llm_extract_structured(
    banked_id: UUID,
    schema_name: str = Query(..., description="Schema to extract into"),
    session: Session = Depends(get_session)
):
    """Use LLM to automatically extract structured data from a banked response."""
    banked = DistillationService.get_banked(session, banked_id)
    if not banked:
        raise HTTPException(status_code=404, detail="Banked response not found")
    
    schemas = DistillationService.get_schema_definitions()
    if schema_name not in schemas:
        raise HTTPException(status_code=400, detail=f"Invalid schema: {schema_name}")
    
    try:
        structured = await DistillationService.llm_assisted_extraction(
            session, banked_id, schema_name
        )
        if not structured:
            raise HTTPException(status_code=500, detail="Extraction failed")
        return StructuredResponse(**structured.model_dump())
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Phase 7: Dataset Export
# ============================================

@router.get("/datasets/{dataset_id}/items")
async def get_dataset_items(
    dataset_id: UUID,
    split: Optional[str] = Query(default=None, description="Filter by split: train, validation, test"),
    session: Session = Depends(get_session)
):
    """Get all items in a dataset with full data."""
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    items = DistillationService.get_dataset_items(session, dataset_id, split)
    return {
        "items": items,
        "total": len(items)
    }


@router.get("/datasets/{dataset_id}/statistics")
async def get_dataset_statistics(dataset_id: UUID, session: Session = Depends(get_session)):
    """Get statistics for a dataset."""
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return DistillationService.get_dataset_statistics(session, dataset_id)


@router.post("/datasets/{dataset_id}/export/jsonl")
async def export_dataset_jsonl(
    dataset_id: UUID,
    split: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Export dataset to JSONL format."""
    from fastapi.responses import Response
    
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    content = DistillationService.export_dataset_jsonl(session, dataset_id, split)
    
    # Update dataset status
    DistillationService.update_dataset_status(session, dataset_id, "exported", "jsonl")
    
    filename = f"{dataset.name}_{dataset.version}"
    if split:
        filename += f"_{split}"
    filename += ".jsonl"
    
    return Response(
        content=content,
        media_type="application/jsonl",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/datasets/{dataset_id}/export/csv")
async def export_dataset_csv(
    dataset_id: UUID,
    split: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Export dataset to CSV format."""
    from fastapi.responses import Response
    
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    content = DistillationService.export_dataset_csv(session, dataset_id, split)
    
    # Update dataset status
    DistillationService.update_dataset_status(session, dataset_id, "exported", "csv")
    
    filename = f"{dataset.name}_{dataset.version}"
    if split:
        filename += f"_{split}"
    filename += ".csv"
    
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/datasets/{dataset_id}/export/alpaca")
async def export_dataset_alpaca(
    dataset_id: UUID,
    split: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Export dataset to Alpaca format (JSON array)."""
    from fastapi.responses import Response
    
    dataset = DistillationService.get_dataset(session, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    content = DistillationService.export_dataset_alpaca(session, dataset_id, split)
    
    # Update dataset status
    DistillationService.update_dataset_status(session, dataset_id, "exported", "alpaca")
    
    filename = f"{dataset.name}_{dataset.version}_alpaca"
    if split:
        filename += f"_{split}"
    filename += ".json"
    
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.delete("/datasets/{dataset_id}/items/{item_id}", status_code=204)
async def remove_dataset_item(
    dataset_id: UUID,
    item_id: UUID,
    session: Session = Depends(get_session)
):
    """Remove an item from a dataset."""
    if not DistillationService.remove_item_from_dataset(session, dataset_id, item_id):
        raise HTTPException(status_code=404, detail="Item not found in dataset")


@router.patch("/datasets/{dataset_id}/items/{item_id}/split")
async def update_item_split(
    dataset_id: UUID,
    item_id: UUID,
    split: str = Query(..., description="New split: train, validation, or test"),
    session: Session = Depends(get_session)
):
    """Update the split for a dataset item."""
    if split not in ["train", "validation", "test"]:
        raise HTTPException(status_code=400, detail="Split must be train, validation, or test")
    
    item = DistillationService.update_item_split(session, item_id, split)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"id": str(item.id), "split": item.split}


# ============================================
# Phase 6: Expert Review
# ============================================

@router.post("/review-queues", response_model=ReviewQueueResponse, status_code=201)
async def create_review_queue(
    data: ReviewQueueCreate,
    session: Session = Depends(get_session)
):
    """Create a new review queue for expert evaluation."""
    try:
        queue = DistillationService.create_review_queue(session, data)
        stats = DistillationService.get_queue_statistics(session, queue.id)
        return ReviewQueueResponse(
            **queue.model_dump(),
            pending_count=stats["pending_count"],
            completed_count=stats["completed_count"]
        )
    except Exception as e:
        logger.error(f"Failed to create review queue: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/review-queues")
async def list_review_queues(
    is_active: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List all review queues."""
    queues = DistillationService.list_review_queues(session, is_active=is_active, skip=skip, limit=limit)
    
    result = []
    for queue in queues:
        stats = DistillationService.get_queue_statistics(session, queue.id)
        result.append(ReviewQueueResponse(
            **queue.model_dump(),
            pending_count=stats["pending_count"],
            completed_count=stats["completed_count"]
        ))
    
    return {"queues": result, "total": len(result)}


@router.get("/review-queues/{queue_id}", response_model=ReviewQueueResponse)
async def get_review_queue(queue_id: UUID, session: Session = Depends(get_session)):
    """Get a review queue by ID."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    stats = DistillationService.get_queue_statistics(session, queue.id)
    return ReviewQueueResponse(
        **queue.model_dump(),
        pending_count=stats["pending_count"],
        completed_count=stats["completed_count"]
    )


@router.patch("/review-queues/{queue_id}", response_model=ReviewQueueResponse)
async def update_review_queue(
    queue_id: UUID,
    data: ReviewQueueUpdate,
    session: Session = Depends(get_session)
):
    """Update a review queue."""
    queue = DistillationService.update_review_queue(session, queue_id, data)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    stats = DistillationService.get_queue_statistics(session, queue.id)
    return ReviewQueueResponse(
        **queue.model_dump(),
        pending_count=stats["pending_count"],
        completed_count=stats["completed_count"]
    )


@router.delete("/review-queues/{queue_id}", status_code=204)
async def delete_review_queue(queue_id: UUID, session: Session = Depends(get_session)):
    """Delete a review queue."""
    if not DistillationService.delete_review_queue(session, queue_id):
        raise HTTPException(status_code=404, detail="Review queue not found")


@router.get("/review-queues/{queue_id}/statistics")
async def get_queue_statistics(queue_id: UUID, session: Session = Depends(get_session)):
    """Get statistics for a review queue."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    return DistillationService.get_queue_statistics(session, queue_id)


@router.post("/review-queues/{queue_id}/items")
async def add_items_to_queue(
    queue_id: UUID,
    data: ReviewItemCreate,
    session: Session = Depends(get_session)
):
    """Add banked items to a review queue."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    count = DistillationService.add_items_to_queue(session, queue_id, data)
    return {"items_added": count}


@router.post("/review-queues/{queue_id}/auto-populate")
async def auto_populate_queue(
    queue_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session)
):
    """Auto-populate a review queue based on its criteria."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    count = DistillationService.auto_populate_queue(session, queue_id, limit)
    return {"items_added": count}


@router.get("/review-queues/{queue_id}/items")
async def list_review_items(
    queue_id: UUID,
    status: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List review items in a queue."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    items = DistillationService.list_review_items(
        session, queue_id, status=status, assigned_to=assigned_to, skip=skip, limit=limit
    )
    
    # Include banked details
    result = []
    for item in items:
        banked = DistillationService.get_banked(session, item.banked_id)
        result.append(ReviewItemResponse(
            **item.model_dump(),
            banked=BankedResponse(**banked.model_dump()) if banked else None
        ))
    
    return {"items": result, "total": len(result)}


@router.get("/review-queues/{queue_id}/next")
async def get_next_review_item(
    queue_id: UUID,
    reviewer: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Get the next item to review (claims it for the reviewer)."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    item = DistillationService.get_next_review_item(session, queue_id, reviewer)
    if not item:
        return {"item": None, "message": "No pending items to review"}
    
    # Get full banked response with original response
    banked = DistillationService.get_banked(session, item.banked_id)
    response_data = None
    if banked:
        response = DistillationService.get_response(session, banked.response_id)
        if response:
            response_data = _serialize_response(response)
    
    return {
        "item": ReviewItemResponse(
            **item.model_dump(),
            banked=BankedResponse(**banked.model_dump()) if banked else None
        ),
        "response": response_data
    }


@router.get("/review-items/{item_id}", response_model=ReviewItemResponse)
async def get_review_item(item_id: UUID, session: Session = Depends(get_session)):
    """Get a review item by ID."""
    item = DistillationService.get_review_item(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    banked = DistillationService.get_banked(session, item.banked_id)
    return ReviewItemResponse(
        **item.model_dump(),
        banked=BankedResponse(**banked.model_dump()) if banked else None
    )


@router.post("/review-items/{item_id}/review", response_model=ReviewItemResponse)
async def submit_review(
    item_id: UUID,
    action: ReviewAction,
    reviewer: Optional[str] = Query(default=None),
    session: Session = Depends(get_session)
):
    """Submit a review decision on an item."""
    item = DistillationService.submit_review(session, item_id, action, reviewer)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    banked = DistillationService.get_banked(session, item.banked_id)
    return ReviewItemResponse(
        **item.model_dump(),
        banked=BankedResponse(**banked.model_dump()) if banked else None
    )


@router.patch("/review-items/{item_id}", response_model=ReviewItemResponse)
async def update_review_item(
    item_id: UUID,
    data: ReviewItemUpdate,
    session: Session = Depends(get_session)
):
    """Update a review item."""
    item = DistillationService.update_review_item(session, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    banked = DistillationService.get_banked(session, item.banked_id)
    return ReviewItemResponse(
        **item.model_dump(),
        banked=BankedResponse(**banked.model_dump()) if banked else None
    )


@router.delete("/review-items/{item_id}", status_code=204)
async def remove_review_item(item_id: UUID, session: Session = Depends(get_session)):
    """Remove an item from a review queue."""
    if not DistillationService.remove_review_item(session, item_id):
        raise HTTPException(status_code=404, detail="Review item not found")


@router.post("/review-queues/{queue_id}/export")
async def export_review_queue(
    queue_id: UUID,
    export_format: str = Query(default="csv", pattern="^(csv|json)$"),
    session: Session = Depends(get_session)
):
    """Export review queue items for offline review."""
    from fastapi.responses import Response
    
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    result = DistillationService.export_review_queue(session, queue_id, export_format)
    
    media_type = "text/csv" if export_format == "csv" else "application/json"
    filename = f"review_queue_{queue.name}.{export_format}"
    
    return Response(
        content=result["content"],
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/review-queues/{queue_id}/import")
async def import_review_ratings(
    queue_id: UUID,
    data: ReviewImportRequest,
    session: Session = Depends(get_session)
):
    """Import review ratings from external review."""
    queue = DistillationService.get_review_queue(session, queue_id)
    if not queue:
        raise HTTPException(status_code=404, detail="Review queue not found")
    
    updated_count = DistillationService.import_review_ratings(session, queue_id, data.items)
    return {"items_updated": updated_count}
