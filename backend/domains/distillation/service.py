"""
Distillation Workbench service layer.

Handles business logic for knowledge distillation from SOTA models.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncIterator
from uuid import UUID
from sqlmodel import Session, select, desc, func

from .db_models import (
    DistillationDomain, DistillationTopic, DistillationTag,
    DistillationTask, DistillationRun, DistillationResponse,
    DistillationResponseTag, DistillationBanked, DistillationComparison,
    DistillationComparisonResponse, DistillationVote, DistillationDataset,
    DistillationDatasetItem, DistillationStructured,
    DistillationReviewQueue, DistillationReviewItem, DistillationReviewExport
)
from .models import (
    DomainCreate, DomainUpdate, TopicCreate, TopicUpdate, TagCreate,
    TaskCreate, TaskUpdate, RunCreate, ResponseUpdate, BankCreate,
    BankedUpdate, ComparisonCreate, VoteCreate, DatasetCreate,
    InteractiveChatRequest, TriggerType, RunStatus, BankedStatus,
    ReviewQueueCreate, ReviewQueueUpdate, ReviewItemCreate, ReviewItemUpdate,
    ReviewAction, ReviewStatus
)
from llm.providers import get_provider

logger = logging.getLogger(__name__)


class DistillationService:
    """Service for distillation workbench operations."""
    
    # ============================================
    # Domain Management
    # ============================================
    
    @staticmethod
    def create_domain(session: Session, data: DomainCreate) -> DistillationDomain:
        """Create a new domain."""
        domain = DistillationDomain(**data.model_dump())
        session.add(domain)
        session.commit()
        session.refresh(domain)
        return domain
    
    @staticmethod
    def get_domain(session: Session, domain_id: UUID) -> Optional[DistillationDomain]:
        """Get a domain by ID."""
        return session.get(DistillationDomain, domain_id)
    
    @staticmethod
    def list_domains(session: Session) -> List[DistillationDomain]:
        """List all domains with topic counts."""
        return session.exec(
            select(DistillationDomain).order_by(DistillationDomain.name)
        ).all()
    
    @staticmethod
    def update_domain(session: Session, domain_id: UUID, data: DomainUpdate) -> Optional[DistillationDomain]:
        """Update a domain."""
        domain = session.get(DistillationDomain, domain_id)
        if not domain:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(domain, key, value)
        
        domain.updated_at = datetime.utcnow()
        session.add(domain)
        session.commit()
        session.refresh(domain)
        return domain
    
    @staticmethod
    def delete_domain(session: Session, domain_id: UUID) -> bool:
        """Delete a domain."""
        domain = session.get(DistillationDomain, domain_id)
        if not domain:
            return False
        session.delete(domain)
        session.commit()
        return True
    
    # ============================================
    # Topic Management
    # ============================================
    
    @staticmethod
    def create_topic(session: Session, data: TopicCreate) -> DistillationTopic:
        """Create a new topic."""
        topic = DistillationTopic(**data.model_dump())
        session.add(topic)
        session.commit()
        session.refresh(topic)
        return topic
    
    @staticmethod
    def get_topics_for_domain(session: Session, domain_id: UUID) -> List[DistillationTopic]:
        """Get all topics for a domain."""
        return session.exec(
            select(DistillationTopic)
            .where(DistillationTopic.domain_id == domain_id)
            .order_by(DistillationTopic.name)
        ).all()
    
    @staticmethod
    def update_topic(session: Session, topic_id: UUID, data: TopicUpdate) -> Optional[DistillationTopic]:
        """Update a topic."""
        topic = session.get(DistillationTopic, topic_id)
        if not topic:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(topic, key, value)
        
        session.add(topic)
        session.commit()
        session.refresh(topic)
        return topic
    
    @staticmethod
    def delete_topic(session: Session, topic_id: UUID) -> bool:
        """Delete a topic."""
        topic = session.get(DistillationTopic, topic_id)
        if not topic:
            return False
        session.delete(topic)
        session.commit()
        return True
    
    # ============================================
    # Tag Management
    # ============================================
    
    @staticmethod
    def create_tag(session: Session, data: TagCreate) -> DistillationTag:
        """Create a new tag."""
        tag = DistillationTag(**data.model_dump())
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag
    
    @staticmethod
    def list_tags(session: Session) -> List[DistillationTag]:
        """List all tags."""
        return session.exec(
            select(DistillationTag).order_by(DistillationTag.name)
        ).all()
    
    @staticmethod
    def get_or_create_tag(session: Session, name: str, color: Optional[str] = None) -> DistillationTag:
        """Get existing tag or create new one."""
        existing = session.exec(
            select(DistillationTag).where(DistillationTag.name == name)
        ).first()
        
        if existing:
            return existing
        
        tag = DistillationTag(name=name, color=color)
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag
    
    # ============================================
    # Task Management
    # ============================================
    
    @staticmethod
    def create_task(session: Session, data: TaskCreate, created_by: Optional[str] = None) -> DistillationTask:
        """Create a new task."""
        task_data = data.model_dump()
        task_data['variables'] = [v.model_dump() for v in data.variables]
        task_data['created_by'] = created_by
        
        task = DistillationTask(**task_data)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
    @staticmethod
    def get_task(session: Session, task_id: UUID) -> Optional[DistillationTask]:
        """Get a task by ID."""
        return session.get(DistillationTask, task_id)
    
    @staticmethod
    def list_tasks(
        session: Session,
        domain_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationTask]:
        """List tasks with filters."""
        query = select(DistillationTask)
        
        if domain_id:
            query = query.where(DistillationTask.domain_id == domain_id)
        if topic_id:
            query = query.where(DistillationTask.topic_id == topic_id)
        if is_active is not None:
            query = query.where(DistillationTask.is_active == is_active)
        
        query = query.order_by(desc(DistillationTask.updated_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_task(session: Session, task_id: UUID, data: TaskUpdate) -> Optional[DistillationTask]:
        """Update a task."""
        task = session.get(DistillationTask, task_id)
        if not task:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        if 'variables' in update_data and update_data['variables']:
            update_data['variables'] = [v.model_dump() if hasattr(v, 'model_dump') else v for v in update_data['variables']]
        
        for key, value in update_data.items():
            setattr(task, key, value)
        
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    
    @staticmethod
    def delete_task(session: Session, task_id: UUID) -> bool:
        """Delete a task."""
        task = session.get(DistillationTask, task_id)
        if not task:
            return False
        session.delete(task)
        session.commit()
        return True
    
    # ============================================
    # Run Execution
    # ============================================
    
    @staticmethod
    def create_run(
        session: Session,
        data: RunCreate,
        trigger_type: TriggerType = TriggerType.MANUAL,
        created_by: Optional[str] = None
    ) -> DistillationRun:
        """Create a new run."""
        run = DistillationRun(
            task_id=data.task_id,
            ad_hoc_prompt=data.ad_hoc_prompt,
            ad_hoc_system_prompt=data.ad_hoc_system_prompt,
            ad_hoc_models=data.ad_hoc_models,
            variables_used=data.variables,
            trigger_type=trigger_type.value,
            domain_id=data.domain_id,
            topic_id=data.topic_id,
            status=RunStatus.PENDING.value,
            created_by=created_by
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
    
    @staticmethod
    def get_run(session: Session, run_id: UUID) -> Optional[DistillationRun]:
        """Get a run by ID."""
        return session.get(DistillationRun, run_id)
    
    @staticmethod
    def list_runs(
        session: Session,
        task_id: Optional[UUID] = None,
        status: Optional[RunStatus] = None,
        trigger_type: Optional[TriggerType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationRun]:
        """List runs with filters."""
        query = select(DistillationRun)
        
        if task_id:
            query = query.where(DistillationRun.task_id == task_id)
        if status:
            query = query.where(DistillationRun.status == status.value)
        if trigger_type:
            query = query.where(DistillationRun.trigger_type == trigger_type.value)
        
        query = query.order_by(desc(DistillationRun.created_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    async def _call_llm(provider_name: str, model_name: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Call LLM provider and collect full response."""
        logger.info(f"Starting LLM call: provider={provider_name}, model={model_name}")
        try:
            provider = get_provider(provider_name, model_name)
            logger.info(f"Got provider instance for {provider_name}")
            
            full_content = []
            chunk_count = 0
            async for event in provider.stream_chat(messages=messages):
                event_type = event.get("type")
                if event_type == "delta":
                    content = event.get("content", "")
                    full_content.append(content)
                    chunk_count += 1
                elif event_type == "error":
                    error_msg = event.get("error", "Unknown error")
                    logger.error(f"LLM stream error: {error_msg}")
                    raise Exception(error_msg)
            
            final_content = "".join(full_content)
            logger.info(f"LLM call completed: {chunk_count} chunks, {len(final_content)} chars")
            
            return {
                "content": final_content,
                "usage": {}  # Token usage not available in streaming mode
            }
        except Exception as e:
            logger.error(f"LLM call failed for {provider_name}/{model_name}: {e}", exc_info=True)
            raise
    
    @staticmethod
    async def execute_run(session: Session, run: DistillationRun) -> DistillationRun:
        """Execute a run against SOTA models."""
        run.status = RunStatus.RUNNING.value
        run.started_at = datetime.utcnow()
        session.add(run)
        session.commit()
        
        try:
            # Determine prompt and models
            if run.task_id:
                task = session.get(DistillationTask, run.task_id)
                if not task:
                    raise ValueError(f"Task {run.task_id} not found")
                
                # Apply variables to template
                prompt = task.prompt_template
                for var_name, var_value in run.variables_used.items():
                    prompt = prompt.replace(f"{{{var_name}}}", str(var_value))
                
                system_prompt = task.system_prompt
                models = task.target_models
                
                # Inherit organization from task if not set
                if not run.domain_id:
                    run.domain_id = task.domain_id
                if not run.topic_id:
                    run.topic_id = task.topic_id
            else:
                # Ad-hoc run
                prompt = run.ad_hoc_prompt
                system_prompt = run.ad_hoc_system_prompt
                models = run.ad_hoc_models or ["gpt-4o"]
            
            if not prompt:
                raise ValueError("No prompt available for run")
            
            # Execute against each model
            responses = []
            errors = []
            for model_spec in models:
                # Parse provider:model format or assume openai
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
                
                logger.info(f"Executing model: {provider_name}/{model_name}")
                
                try:
                    start_time = datetime.utcnow()
                    
                    # Build messages
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    messages.append({"role": "user", "content": prompt})
                    
                    # Execute using streaming API
                    result = await DistillationService._call_llm(provider_name, model_name, messages)
                    
                    end_time = datetime.utcnow()
                    latency = int((end_time - start_time).total_seconds() * 1000)
                    
                    # Create response record
                    response = DistillationResponse(
                        run_id=run.id,
                        provider=provider_name,
                        model=model_name,
                        prompt_sent=prompt,
                        system_prompt_used=system_prompt,
                        response_text=result.get("content", ""),
                        tokens_input=result.get("usage", {}).get("prompt_tokens"),
                        tokens_output=result.get("usage", {}).get("completion_tokens"),
                        latency_ms=latency,
                        domain_id=run.domain_id,
                        topic_id=run.topic_id
                    )
                    session.add(response)
                    responses.append(response)
                    logger.info(f"Model {provider_name}/{model_name} completed successfully")
                    
                except Exception as e:
                    error_msg = f"{provider_name}/{model_name}: {str(e)}"
                    logger.error(f"Error executing model {model_spec}: {e}", exc_info=True)
                    errors.append(error_msg)
                    # Continue with other models
            
            session.commit()
            
            # Set status based on results
            if len(responses) == 0:
                run.status = RunStatus.FAILED.value
                run.error_message = "All models failed: " + "; ".join(errors)
            elif len(errors) > 0:
                run.status = RunStatus.COMPLETED.value  # Partial success
                run.error_message = "Some models failed: " + "; ".join(errors)
            else:
                run.status = RunStatus.COMPLETED.value
            run.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Run execution failed: {e}")
            run.status = RunStatus.FAILED.value
            run.error_message = str(e)
            run.completed_at = datetime.utcnow()
        
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
    
    # ============================================
    # Response Management
    # ============================================
    
    @staticmethod
    def get_response(session: Session, response_id: UUID) -> Optional[DistillationResponse]:
        """Get a response by ID."""
        return session.get(DistillationResponse, response_id)
    
    @staticmethod
    def get_responses_for_run(session: Session, run_id: UUID) -> List[DistillationResponse]:
        """Get all responses for a run."""
        return session.exec(
            select(DistillationResponse)
            .where(DistillationResponse.run_id == run_id)
            .order_by(DistillationResponse.created_at)
        ).all()
    
    @staticmethod
    def list_responses(
        session: Session,
        domain_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationResponse]:
        """List responses with filters."""
        query = select(DistillationResponse)
        
        if domain_id:
            query = query.where(DistillationResponse.domain_id == domain_id)
        if topic_id:
            query = query.where(DistillationResponse.topic_id == topic_id)
        if provider:
            query = query.where(DistillationResponse.provider == provider)
        if model:
            query = query.where(DistillationResponse.model == model)
        
        query = query.order_by(desc(DistillationResponse.created_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_response(session: Session, response_id: UUID, data: ResponseUpdate) -> Optional[DistillationResponse]:
        """Update a response (tags, domain, topic, rating)."""
        response = session.get(DistillationResponse, response_id)
        if not response:
            return None
        
        if data.domain_id is not None:
            response.domain_id = data.domain_id
        if data.topic_id is not None:
            response.topic_id = data.topic_id
        if data.quality_rating is not None:
            response.quality_rating = data.quality_rating
        
        # Handle tags
        if data.tag_ids is not None:
            # Remove existing tags
            session.exec(
                select(DistillationResponseTag)
                .where(DistillationResponseTag.response_id == response_id)
            )
            for tag_link in session.exec(
                select(DistillationResponseTag)
                .where(DistillationResponseTag.response_id == response_id)
            ).all():
                session.delete(tag_link)
            
            # Add new tags
            for tag_id in data.tag_ids:
                tag_link = DistillationResponseTag(response_id=response_id, tag_id=tag_id)
                session.add(tag_link)
        
        session.add(response)
        session.commit()
        session.refresh(response)
        return response
    
    @staticmethod
    def delete_response(session: Session, response_id: UUID) -> bool:
        """Delete a response and its related data."""
        response = session.get(DistillationResponse, response_id)
        if not response:
            return False
        
        # Delete related tags
        for tag_link in session.exec(
            select(DistillationResponseTag)
            .where(DistillationResponseTag.response_id == response_id)
        ).all():
            session.delete(tag_link)
        
        # Delete related banked entries
        for banked in session.exec(
            select(DistillationBanked)
            .where(DistillationBanked.response_id == response_id)
        ).all():
            session.delete(banked)
        
        session.delete(response)
        session.commit()
        return True
    
    # ============================================
    # Banking
    # ============================================
    
    @staticmethod
    def bank_response(session: Session, data: BankCreate, banked_by: Optional[str] = None) -> DistillationBanked:
        """Bank a response for curation."""
        # Check if already banked
        existing = session.exec(
            select(DistillationBanked)
            .where(DistillationBanked.response_id == data.response_id)
        ).first()
        
        if existing:
            # Update existing banked entry
            if data.domain_id is not None:
                existing.domain_id = data.domain_id
            if data.topic_id is not None:
                existing.topic_id = data.topic_id
            if data.quality_score is not None:
                existing.quality_score = data.quality_score
            if data.notes is not None:
                existing.notes = data.notes
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        
        # Create new banked entry
        banked = DistillationBanked(
            response_id=data.response_id,
            domain_id=data.domain_id,
            topic_id=data.topic_id,
            quality_score=data.quality_score,
            notes=data.notes,
            banked_by=banked_by
        )
        session.add(banked)
        session.commit()
        session.refresh(banked)
        return banked
    
    @staticmethod
    def get_banked(session: Session, banked_id: UUID) -> Optional[DistillationBanked]:
        """Get a banked response by ID."""
        return session.get(DistillationBanked, banked_id)
    
    @staticmethod
    def list_banked(
        session: Session,
        domain_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        status: Optional[BankedStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationBanked]:
        """List banked responses with filters."""
        query = select(DistillationBanked)
        
        if domain_id:
            query = query.where(DistillationBanked.domain_id == domain_id)
        if topic_id:
            query = query.where(DistillationBanked.topic_id == topic_id)
        if status:
            query = query.where(DistillationBanked.status == status.value)
        
        query = query.order_by(desc(DistillationBanked.banked_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_banked(
        session: Session,
        banked_id: UUID,
        data: BankedUpdate,
        reviewed_by: Optional[str] = None
    ) -> Optional[DistillationBanked]:
        """Update a banked response."""
        banked = session.get(DistillationBanked, banked_id)
        if not banked:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'status':
                setattr(banked, key, value.value if hasattr(value, 'value') else value)
            else:
                setattr(banked, key, value)
        
        if data.status is not None:
            banked.reviewed_by = reviewed_by
            banked.reviewed_at = datetime.utcnow()
        
        session.add(banked)
        session.commit()
        session.refresh(banked)
        return banked
    
    # ============================================
    # Comparisons
    # ============================================
    
    @staticmethod
    def create_comparison(
        session: Session,
        data: ComparisonCreate,
        run_id: Optional[UUID] = None,
        created_by: Optional[str] = None
    ) -> DistillationComparison:
        """Create a new comparison."""
        comparison = DistillationComparison(
            run_id=run_id,
            comparison_type=data.comparison_type.value,
            prompt_used=data.prompt_used,
            created_by=created_by
        )
        session.add(comparison)
        session.commit()
        session.refresh(comparison)
        
        # Add responses to comparison
        for i, response_id in enumerate(data.response_ids):
            label = chr(65 + i) if data.comparison_type == "blind" else None  # A, B, C...
            link = DistillationComparisonResponse(
                comparison_id=comparison.id,
                response_id=response_id,
                display_order=i,
                display_label=label
            )
            session.add(link)
        
        session.commit()
        return comparison
    
    @staticmethod
    def get_comparison(session: Session, comparison_id: UUID) -> Optional[DistillationComparison]:
        """Get a comparison by ID."""
        return session.get(DistillationComparison, comparison_id)
    
    @staticmethod
    def submit_vote(session: Session, data: VoteCreate, voter: Optional[str] = None) -> DistillationVote:
        """Submit a vote on a comparison."""
        vote = DistillationVote(
            comparison_id=data.comparison_id,
            vote_type=data.vote_type.value,
            winner_response_id=data.winner_response_id,
            rankings=data.rankings,
            ratings=data.ratings,
            voter=voter,
            notes=data.notes
        )
        session.add(vote)
        
        # Mark comparison as completed
        comparison = session.get(DistillationComparison, data.comparison_id)
        if comparison:
            comparison.status = "completed"
            session.add(comparison)
        
        session.commit()
        session.refresh(vote)
        return vote
    
    # ============================================
    # Interactive Chat
    # ============================================
    
    @staticmethod
    async def interactive_chat(
        session: Session,
        data: InteractiveChatRequest,
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute interactive chat with SOTA models."""
        # Create a run
        run = DistillationRun(
            ad_hoc_prompt=data.message,
            ad_hoc_system_prompt=data.system_prompt,
            ad_hoc_models=data.models,
            variables_used={},
            trigger_type=TriggerType.INTERACTIVE.value,
            domain_id=data.domain_id,
            topic_id=data.topic_id,
            status=RunStatus.PENDING.value,
            created_by=created_by
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        
        # Execute the run
        run = await DistillationService.execute_run(session, run)
        
        # Get responses
        responses = DistillationService.get_responses_for_run(session, run.id)
        
        result = {
            "run_id": run.id,
            "responses": responses,
            "comparison_id": None
        }
        
        # Create comparison if requested and multiple responses
        if data.create_comparison and len(responses) > 1:
            comparison_data = ComparisonCreate(
                response_ids=[r.id for r in responses],
                comparison_type="side_by_side",
                prompt_used=data.message
            )
            comparison = DistillationService.create_comparison(
                session, comparison_data, run_id=run.id, created_by=created_by
            )
            result["comparison_id"] = comparison.id
        
        return result
    
    # ============================================
    # Datasets
    # ============================================
    
    @staticmethod
    def create_dataset(session: Session, data: DatasetCreate, created_by: Optional[str] = None) -> DistillationDataset:
        """Create a new dataset."""
        dataset = DistillationDataset(
            name=data.name,
            version=data.version,
            description=data.description,
            dataset_type=data.dataset_type.value,
            domain_id=data.domain_id,
            selection_criteria=data.selection_criteria,
            created_by=created_by
        )
        session.add(dataset)
        session.commit()
        session.refresh(dataset)
        return dataset
    
    @staticmethod
    def get_dataset(session: Session, dataset_id: UUID) -> Optional[DistillationDataset]:
        """Get a dataset by ID."""
        return session.get(DistillationDataset, dataset_id)
    
    @staticmethod
    def list_datasets(
        session: Session,
        domain_id: Optional[UUID] = None,
        dataset_type: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationDataset]:
        """List datasets with filters."""
        query = select(DistillationDataset)
        
        if domain_id:
            query = query.where(DistillationDataset.domain_id == domain_id)
        if dataset_type:
            query = query.where(DistillationDataset.dataset_type == dataset_type)
        if status:
            query = query.where(DistillationDataset.status == status)
        
        query = query.order_by(desc(DistillationDataset.updated_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def add_items_to_dataset(
        session: Session,
        dataset_id: UUID,
        banked_ids: Optional[List[UUID]] = None,
        structured_ids: Optional[List[UUID]] = None,
        split: str = "train"
    ) -> int:
        """Add items to a dataset. Returns count of items added."""
        dataset = session.get(DistillationDataset, dataset_id)
        if not dataset:
            return 0
        
        count = 0
        current_order = dataset.item_count
        
        if banked_ids:
            for banked_id in banked_ids:
                item = DistillationDatasetItem(
                    dataset_id=dataset_id,
                    banked_id=banked_id,
                    split=split,
                    sequence_order=current_order + count
                )
                session.add(item)
                count += 1
        
        if structured_ids:
            for structured_id in structured_ids:
                item = DistillationDatasetItem(
                    dataset_id=dataset_id,
                    structured_id=structured_id,
                    split=split,
                    sequence_order=current_order + count
                )
                session.add(item)
                count += 1
        
        dataset.item_count += count
        dataset.updated_at = datetime.utcnow()
        session.add(dataset)
        session.commit()
        
        return count
    
    # ============================================
    # Phase 3: Enhanced Response Bank
    # ============================================
    
    @staticmethod
    def search_responses(
        session: Session,
        query: Optional[str] = None,
        domain_id: Optional[UUID] = None,
        topic_id: Optional[UUID] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tag_ids: Optional[List[UUID]] = None,
        is_banked: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Advanced search for responses with text search and filters."""
        base_query = select(DistillationResponse)
        
        # Apply filters
        if domain_id:
            base_query = base_query.where(DistillationResponse.domain_id == domain_id)
        if topic_id:
            base_query = base_query.where(DistillationResponse.topic_id == topic_id)
        if provider:
            base_query = base_query.where(DistillationResponse.provider == provider)
        if model:
            base_query = base_query.where(DistillationResponse.model == model)
        
        # Text search in response_text and prompt_sent
        if query:
            search_term = f"%{query}%"
            base_query = base_query.where(
                (DistillationResponse.response_text.ilike(search_term)) |
                (DistillationResponse.prompt_sent.ilike(search_term))
            )
        
        # Filter by tags
        if tag_ids:
            base_query = base_query.join(DistillationResponseTag).where(
                DistillationResponseTag.tag_id.in_(tag_ids)
            )
        
        # Filter by banked status
        if is_banked is not None:
            if is_banked:
                base_query = base_query.join(
                    DistillationBanked,
                    DistillationBanked.response_id == DistillationResponse.id
                )
            else:
                # Subquery to find banked responses
                banked_ids = select(DistillationBanked.response_id)
                base_query = base_query.where(~DistillationResponse.id.in_(banked_ids))
        
        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = session.exec(count_query).one()
        
        # Get paginated results
        results_query = base_query.order_by(desc(DistillationResponse.created_at)).offset(skip).limit(limit)
        responses = session.exec(results_query).all()
        
        return {
            "responses": responses,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    @staticmethod
    def get_response_tags(session: Session, response_id: UUID) -> List[DistillationTag]:
        """Get all tags for a response."""
        tag_links = session.exec(
            select(DistillationResponseTag)
            .where(DistillationResponseTag.response_id == response_id)
        ).all()
        
        tags = []
        for link in tag_links:
            tag = session.get(DistillationTag, link.tag_id)
            if tag:
                tags.append(tag)
        return tags
    
    @staticmethod
    def add_tags_to_response(session: Session, response_id: UUID, tag_names: List[str]) -> List[DistillationTag]:
        """Add tags to a response by name (creates tags if they don't exist)."""
        tags = []
        for name in tag_names:
            tag = DistillationService.get_or_create_tag(session, name.strip())
            tags.append(tag)
            
            # Check if link already exists
            existing = session.exec(
                select(DistillationResponseTag)
                .where(DistillationResponseTag.response_id == response_id)
                .where(DistillationResponseTag.tag_id == tag.id)
            ).first()
            
            if not existing:
                link = DistillationResponseTag(response_id=response_id, tag_id=tag.id)
                session.add(link)
        
        session.commit()
        return tags
    
    @staticmethod
    def remove_tag_from_response(session: Session, response_id: UUID, tag_id: UUID) -> bool:
        """Remove a tag from a response."""
        link = session.exec(
            select(DistillationResponseTag)
            .where(DistillationResponseTag.response_id == response_id)
            .where(DistillationResponseTag.tag_id == tag_id)
        ).first()
        
        if link:
            session.delete(link)
            session.commit()
            return True
        return False
    
    @staticmethod
    def get_response_statistics(session: Session) -> Dict[str, Any]:
        """Get statistics about responses."""
        total_responses = session.exec(
            select(func.count(DistillationResponse.id))
        ).one()
        
        total_banked = session.exec(
            select(func.count(DistillationBanked.id))
        ).one()
        
        # Responses by provider
        by_provider = session.exec(
            select(DistillationResponse.provider, func.count(DistillationResponse.id))
            .group_by(DistillationResponse.provider)
        ).all()
        
        # Responses by model
        by_model = session.exec(
            select(DistillationResponse.model, func.count(DistillationResponse.id))
            .group_by(DistillationResponse.model)
        ).all()
        
        return {
            "total_responses": total_responses,
            "total_banked": total_banked,
            "by_provider": {p: c for p, c in by_provider},
            "by_model": {m: c for m, c in by_model}
        }
    
    # ============================================
    # Phase 4: Enhanced Comparisons & Voting
    # ============================================
    
    @staticmethod
    def list_comparisons(
        session: Session,
        status: Optional[str] = None,
        comparison_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationComparison]:
        """List comparisons with optional filters."""
        query = select(DistillationComparison)
        
        if status:
            query = query.where(DistillationComparison.status == status)
        if comparison_type:
            query = query.where(DistillationComparison.comparison_type == comparison_type)
        
        query = query.order_by(desc(DistillationComparison.created_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def get_comparison_with_details(session: Session, comparison_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a comparison with all responses and votes."""
        comparison = session.get(DistillationComparison, comparison_id)
        if not comparison:
            return None
        
        # Get linked responses
        response_links = session.exec(
            select(DistillationComparisonResponse)
            .where(DistillationComparisonResponse.comparison_id == comparison_id)
            .order_by(DistillationComparisonResponse.display_order)
        ).all()
        
        responses = []
        for link in response_links:
            response = session.get(DistillationResponse, link.response_id)
            if response:
                responses.append({
                    "response": response,
                    "display_order": link.display_order,
                    "display_label": link.display_label
                })
        
        # Get votes
        votes = session.exec(
            select(DistillationVote)
            .where(DistillationVote.comparison_id == comparison_id)
            .order_by(DistillationVote.created_at)
        ).all()
        
        return {
            "comparison": comparison,
            "responses": responses,
            "votes": votes,
            "vote_count": len(votes)
        }
    
    @staticmethod
    def get_comparison_votes(session: Session, comparison_id: UUID) -> List[DistillationVote]:
        """Get all votes for a comparison."""
        return session.exec(
            select(DistillationVote)
            .where(DistillationVote.comparison_id == comparison_id)
            .order_by(DistillationVote.created_at)
        ).all()
    
    @staticmethod
    def get_vote_statistics(session: Session, comparison_id: UUID) -> Dict[str, Any]:
        """Get vote statistics for a comparison."""
        votes = session.exec(
            select(DistillationVote)
            .where(DistillationVote.comparison_id == comparison_id)
        ).all()
        
        total_votes = len(votes)
        winner_votes: Dict[str, int] = {}
        
        for vote in votes:
            if vote.winner_response_id:
                winner_id = str(vote.winner_response_id)
                winner_votes[winner_id] = winner_votes.get(winner_id, 0) + 1
        
        # Calculate percentages
        vote_percentages = {}
        if total_votes > 0:
            for response_id, count in winner_votes.items():
                vote_percentages[response_id] = round(count / total_votes * 100, 1)
        
        return {
            "total_votes": total_votes,
            "winner_counts": winner_votes,
            "vote_percentages": vote_percentages
        }
    
    @staticmethod
    def get_model_preference_stats(session: Session) -> Dict[str, Any]:
        """Get overall model preference statistics from all comparisons."""
        votes = session.exec(
            select(DistillationVote)
            .where(DistillationVote.winner_response_id.is_not(None))
        ).all()
        
        model_wins: Dict[str, int] = {}
        model_appearances: Dict[str, int] = {}
        
        for vote in votes:
            if vote.winner_response_id:
                winner_response = session.get(DistillationResponse, vote.winner_response_id)
                if winner_response:
                    model_key = f"{winner_response.provider}:{winner_response.model}"
                    model_wins[model_key] = model_wins.get(model_key, 0) + 1
        
        # Get all responses that have been in comparisons
        comparison_responses = session.exec(
            select(DistillationComparisonResponse)
        ).all()
        
        for cr in comparison_responses:
            response = session.get(DistillationResponse, cr.response_id)
            if response:
                model_key = f"{response.provider}:{response.model}"
                model_appearances[model_key] = model_appearances.get(model_key, 0) + 1
        
        # Calculate win rates
        win_rates: Dict[str, float] = {}
        for model, appearances in model_appearances.items():
            wins = model_wins.get(model, 0)
            win_rates[model] = round(wins / appearances * 100, 1) if appearances > 0 else 0
        
        return {
            "model_wins": model_wins,
            "model_appearances": model_appearances,
            "win_rates": win_rates,
            "total_votes": len(votes)
        }
    
    @staticmethod
    def create_blind_comparison(
        session: Session,
        response_ids: List[UUID],
        prompt_used: str,
        created_by: Optional[str] = None
    ) -> DistillationComparison:
        """Create a blind comparison (labels are A, B, C... without model info)."""
        import random
        
        # Shuffle response order for blind comparison
        shuffled_ids = response_ids.copy()
        random.shuffle(shuffled_ids)
        
        comparison = DistillationComparison(
            comparison_type="blind",
            prompt_used=prompt_used,
            created_by=created_by
        )
        session.add(comparison)
        session.commit()
        session.refresh(comparison)
        
        # Add responses with shuffled order and labels
        for i, response_id in enumerate(shuffled_ids):
            label = chr(65 + i)  # A, B, C...
            link = DistillationComparisonResponse(
                comparison_id=comparison.id,
                response_id=response_id,
                display_order=i,
                display_label=label
            )
            session.add(link)
        
        session.commit()
        return comparison
    
    # ============================================
    # Phase 5: Structuring
    # ============================================
    
    # Schema definitions for structured extraction
    SCHEMA_DEFINITIONS = {
        "qa_pair": {
            "name": "Q&A Pair",
            "description": "Question and answer pair with optional context",
            "fields": {
                "question": {"type": "string", "required": True, "description": "The question"},
                "answer": {"type": "string", "required": True, "description": "The answer"},
                "context": {"type": "string", "required": False, "description": "Optional context"},
                "difficulty": {"type": "string", "required": False, "enum": ["easy", "medium", "hard"]},
                "category": {"type": "string", "required": False}
            }
        },
        "instruction": {
            "name": "Instruction",
            "description": "Instruction-following format (Alpaca-style)",
            "fields": {
                "instruction": {"type": "string", "required": True, "description": "The instruction/task"},
                "input": {"type": "string", "required": False, "description": "Optional input context"},
                "output": {"type": "string", "required": True, "description": "Expected output"},
                "reasoning": {"type": "string", "required": False, "description": "Optional reasoning/explanation"}
            }
        },
        "summary": {
            "name": "Summary",
            "description": "Text summarization format",
            "fields": {
                "source_text": {"type": "string", "required": True, "description": "Original text"},
                "summary": {"type": "string", "required": True, "description": "Summary"},
                "key_points": {"type": "array", "required": False, "description": "List of key points"},
                "summary_type": {"type": "string", "required": False, "enum": ["brief", "detailed", "bullet"]}
            }
        },
        "conversation": {
            "name": "Conversation",
            "description": "Multi-turn conversation format",
            "fields": {
                "messages": {"type": "array", "required": True, "description": "List of {role, content} messages"},
                "system_prompt": {"type": "string", "required": False, "description": "System prompt if any"}
            }
        },
        "freeform": {
            "name": "Freeform",
            "description": "Flexible key-value format",
            "fields": {
                "content": {"type": "string", "required": True},
                "metadata": {"type": "object", "required": False}
            }
        }
    }
    
    @staticmethod
    def get_schema_definitions() -> Dict[str, Any]:
        """Get all available schema definitions."""
        return DistillationService.SCHEMA_DEFINITIONS
    
    @staticmethod
    def create_structured(
        session: Session,
        banked_id: UUID,
        schema_name: str,
        structured_data: Dict[str, Any],
        extraction_method: str = "manual",
        extracted_by: Optional[str] = None
    ) -> DistillationStructured:
        """Create a structured extraction from a banked response."""
        structured = DistillationStructured(
            banked_id=banked_id,
            schema_name=schema_name,
            structured_data=structured_data,
            extraction_method=extraction_method,
            extracted_by=extracted_by
        )
        session.add(structured)
        session.commit()
        session.refresh(structured)
        return structured
    
    @staticmethod
    def get_structured(session: Session, structured_id: UUID) -> Optional[DistillationStructured]:
        """Get a structured extraction by ID."""
        return session.get(DistillationStructured, structured_id)
    
    @staticmethod
    def get_structured_for_banked(session: Session, banked_id: UUID) -> List[DistillationStructured]:
        """Get all structured extractions for a banked response."""
        return session.exec(
            select(DistillationStructured)
            .where(DistillationStructured.banked_id == banked_id)
            .order_by(DistillationStructured.extracted_at)
        ).all()
    
    @staticmethod
    def list_structured(
        session: Session,
        schema_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationStructured]:
        """List structured extractions with optional filters."""
        query = select(DistillationStructured)
        
        if schema_name:
            query = query.where(DistillationStructured.schema_name == schema_name)
        
        query = query.order_by(desc(DistillationStructured.extracted_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_structured(
        session: Session,
        structured_id: UUID,
        structured_data: Dict[str, Any]
    ) -> Optional[DistillationStructured]:
        """Update structured data."""
        structured = session.get(DistillationStructured, structured_id)
        if not structured:
            return None
        
        structured.structured_data = structured_data
        session.add(structured)
        session.commit()
        session.refresh(structured)
        return structured
    
    @staticmethod
    def delete_structured(session: Session, structured_id: UUID) -> bool:
        """Delete a structured extraction."""
        structured = session.get(DistillationStructured, structured_id)
        if not structured:
            return False
        session.delete(structured)
        session.commit()
        return True
    
    @staticmethod
    async def llm_assisted_extraction(
        session: Session,
        banked_id: UUID,
        schema_name: str,
        extracted_by: Optional[str] = None
    ) -> Optional[DistillationStructured]:
        """Use LLM to extract structured data from a banked response."""
        banked = session.get(DistillationBanked, banked_id)
        if not banked:
            return None
        
        response = session.get(DistillationResponse, banked.response_id)
        if not response:
            return None
        
        schema_def = DistillationService.SCHEMA_DEFINITIONS.get(schema_name)
        if not schema_def:
            return None
        
        # Build extraction prompt
        fields_desc = []
        for field_name, field_info in schema_def["fields"].items():
            req = "required" if field_info.get("required") else "optional"
            desc = field_info.get("description", "")
            fields_desc.append(f"- {field_name} ({req}): {desc}")
        
        extraction_prompt = f"""Extract structured data from the following text into the "{schema_name}" format.

Fields to extract:
{chr(10).join(fields_desc)}

Text to extract from:
---
{response.response_text}
---

Original prompt that generated this:
{response.prompt_sent}

Return ONLY valid JSON matching this schema. No explanation or markdown."""
        
        try:
            # Use GPT-4 for extraction
            result = await DistillationService._call_llm("openai", "gpt-4o", [
                {"role": "system", "content": "You are a data extraction assistant. Extract structured data from text and return ONLY valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ])
            
            content = result.get("content", "")
            
            # Try to parse JSON from response
            import json
            # Clean up potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            structured_data = json.loads(content.strip())
            
            # Create structured record
            return DistillationService.create_structured(
                session,
                banked_id=banked_id,
                schema_name=schema_name,
                structured_data=structured_data,
                extraction_method="llm_assisted",
                extracted_by=extracted_by
            )
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None
    
    # ============================================
    # Phase 7: Dataset Export
    # ============================================
    
    @staticmethod
    def get_dataset_items(
        session: Session,
        dataset_id: UUID,
        split: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all items in a dataset with full data."""
        query = select(DistillationDatasetItem).where(
            DistillationDatasetItem.dataset_id == dataset_id
        )
        
        if split:
            query = query.where(DistillationDatasetItem.split == split)
        
        query = query.order_by(DistillationDatasetItem.sequence_order)
        items = session.exec(query).all()
        
        result = []
        for item in items:
            item_data = {
                "id": str(item.id),
                "split": item.split,
                "sequence_order": item.sequence_order,
                "added_at": item.added_at.isoformat() if item.added_at else None
            }
            
            # Get banked data if present
            if item.banked_id:
                banked = session.get(DistillationBanked, item.banked_id)
                if banked:
                    response = session.get(DistillationResponse, banked.response_id)
                    item_data["banked"] = {
                        "id": str(banked.id),
                        "quality_score": banked.quality_score,
                        "status": banked.status
                    }
                    if response:
                        item_data["response"] = {
                            "id": str(response.id),
                            "prompt": response.prompt_sent,
                            "response": response.response_text,
                            "provider": response.provider,
                            "model": response.model
                        }
            
            # Get structured data if present
            if item.structured_id:
                structured = session.get(DistillationStructured, item.structured_id)
                if structured:
                    item_data["structured"] = {
                        "id": str(structured.id),
                        "schema_name": structured.schema_name,
                        "data": structured.structured_data
                    }
            
            result.append(item_data)
        
        return result
    
    @staticmethod
    def export_dataset_jsonl(session: Session, dataset_id: UUID, split: Optional[str] = None) -> str:
        """Export dataset to JSONL format."""
        import json
        
        items = DistillationService.get_dataset_items(session, dataset_id, split)
        
        lines = []
        for item in items:
            # Format based on whether we have structured or raw data
            if "structured" in item and item["structured"]:
                export_data = item["structured"]["data"]
                export_data["_meta"] = {
                    "schema": item["structured"]["schema_name"],
                    "split": item["split"]
                }
            elif "response" in item and item["response"]:
                export_data = {
                    "prompt": item["response"]["prompt"],
                    "response": item["response"]["response"],
                    "_meta": {
                        "provider": item["response"]["provider"],
                        "model": item["response"]["model"],
                        "split": item["split"]
                    }
                }
            else:
                continue
            
            lines.append(json.dumps(export_data, ensure_ascii=False))
        
        return "\n".join(lines)
    
    @staticmethod
    def export_dataset_csv(session: Session, dataset_id: UUID, split: Optional[str] = None) -> str:
        """Export dataset to CSV format."""
        import csv
        import io
        
        items = DistillationService.get_dataset_items(session, dataset_id, split)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["split", "prompt", "response", "provider", "model", "schema", "structured_data"])
        
        for item in items:
            prompt = ""
            response = ""
            provider = ""
            model = ""
            schema = ""
            structured = ""
            
            if "response" in item and item["response"]:
                prompt = item["response"].get("prompt", "")
                response = item["response"].get("response", "")
                provider = item["response"].get("provider", "")
                model = item["response"].get("model", "")
            
            if "structured" in item and item["structured"]:
                schema = item["structured"].get("schema_name", "")
                import json
                structured = json.dumps(item["structured"].get("data", {}))
            
            writer.writerow([item["split"], prompt, response, provider, model, schema, structured])
        
        return output.getvalue()
    
    @staticmethod
    def export_dataset_alpaca(session: Session, dataset_id: UUID, split: Optional[str] = None) -> str:
        """Export dataset to Alpaca format (instruction, input, output)."""
        import json
        
        items = DistillationService.get_dataset_items(session, dataset_id, split)
        
        alpaca_data = []
        for item in items:
            entry = {}
            
            # Prefer structured instruction format
            if "structured" in item and item["structured"]:
                data = item["structured"]["data"]
                if item["structured"]["schema_name"] == "instruction":
                    entry = {
                        "instruction": data.get("instruction", ""),
                        "input": data.get("input", ""),
                        "output": data.get("output", "")
                    }
                elif item["structured"]["schema_name"] == "qa_pair":
                    entry = {
                        "instruction": data.get("question", ""),
                        "input": data.get("context", ""),
                        "output": data.get("answer", "")
                    }
            elif "response" in item and item["response"]:
                entry = {
                    "instruction": item["response"]["prompt"],
                    "input": "",
                    "output": item["response"]["response"]
                }
            
            if entry:
                alpaca_data.append(entry)
        
        return json.dumps(alpaca_data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def update_dataset_status(
        session: Session,
        dataset_id: UUID,
        status: str,
        export_format: Optional[str] = None,
        export_path: Optional[str] = None
    ) -> Optional[DistillationDataset]:
        """Update dataset status after export."""
        dataset = session.get(DistillationDataset, dataset_id)
        if not dataset:
            return None
        
        dataset.status = status
        if export_format:
            dataset.export_format = export_format
        if export_path:
            dataset.export_path = export_path
        dataset.updated_at = datetime.utcnow()
        
        session.add(dataset)
        session.commit()
        session.refresh(dataset)
        return dataset
    
    @staticmethod
    def remove_item_from_dataset(session: Session, dataset_id: UUID, item_id: UUID) -> bool:
        """Remove an item from a dataset."""
        item = session.get(DistillationDatasetItem, item_id)
        if not item or item.dataset_id != dataset_id:
            return False
        
        session.delete(item)
        
        # Update count
        dataset = session.get(DistillationDataset, dataset_id)
        if dataset:
            dataset.item_count = max(0, dataset.item_count - 1)
            dataset.updated_at = datetime.utcnow()
            session.add(dataset)
        
        session.commit()
        return True
    
    @staticmethod
    def update_item_split(session: Session, item_id: UUID, split: str) -> Optional[DistillationDatasetItem]:
        """Update the split for a dataset item."""
        item = session.get(DistillationDatasetItem, item_id)
        if not item:
            return None
        
        item.split = split
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def get_dataset_statistics(session: Session, dataset_id: UUID) -> Dict[str, Any]:
        """Get statistics for a dataset."""
        items = session.exec(
            select(DistillationDatasetItem)
            .where(DistillationDatasetItem.dataset_id == dataset_id)
        ).all()
        
        total = len(items)
        by_split = {}
        by_schema = {}
        has_structured = 0
        has_banked = 0
        
        for item in items:
            # Count by split
            by_split[item.split] = by_split.get(item.split, 0) + 1
            
            # Count structured vs banked
            if item.structured_id:
                has_structured += 1
                structured = session.get(DistillationStructured, item.structured_id)
                if structured:
                    by_schema[structured.schema_name] = by_schema.get(structured.schema_name, 0) + 1
            
            if item.banked_id:
                has_banked += 1
        
        return {
            "total_items": total,
            "by_split": by_split,
            "by_schema": by_schema,
            "has_structured": has_structured,
            "has_banked_only": has_banked - has_structured
        }
    
    # ============================================
    # Phase 6: Expert Review
    # ============================================
    
    @staticmethod
    def create_review_queue(
        session: Session,
        data: ReviewQueueCreate,
        created_by: Optional[str] = None
    ) -> DistillationReviewQueue:
        """Create a new review queue."""
        queue = DistillationReviewQueue(
            name=data.name,
            description=data.description,
            domain_id=data.domain_id,
            topic_id=data.topic_id,
            min_quality_score=data.min_quality_score,
            assigned_experts=data.assigned_experts,
            created_by=created_by
        )
        session.add(queue)
        session.commit()
        session.refresh(queue)
        return queue
    
    @staticmethod
    def get_review_queue(session: Session, queue_id: UUID) -> Optional[DistillationReviewQueue]:
        """Get a review queue by ID."""
        return session.get(DistillationReviewQueue, queue_id)
    
    @staticmethod
    def list_review_queues(
        session: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationReviewQueue]:
        """List review queues."""
        query = select(DistillationReviewQueue)
        
        if is_active is not None:
            query = query.where(DistillationReviewQueue.is_active == is_active)
        
        query = query.order_by(desc(DistillationReviewQueue.created_at)).offset(skip).limit(limit)
        return session.exec(query).all()
    
    @staticmethod
    def update_review_queue(
        session: Session,
        queue_id: UUID,
        data: ReviewQueueUpdate
    ) -> Optional[DistillationReviewQueue]:
        """Update a review queue."""
        queue = session.get(DistillationReviewQueue, queue_id)
        if not queue:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(queue, key, value)
        
        queue.updated_at = datetime.utcnow()
        session.add(queue)
        session.commit()
        session.refresh(queue)
        return queue
    
    @staticmethod
    def delete_review_queue(session: Session, queue_id: UUID) -> bool:
        """Delete a review queue."""
        queue = session.get(DistillationReviewQueue, queue_id)
        if not queue:
            return False
        session.delete(queue)
        session.commit()
        return True
    
    @staticmethod
    def get_queue_statistics(session: Session, queue_id: UUID) -> Dict[str, Any]:
        """Get statistics for a review queue."""
        items = session.exec(
            select(DistillationReviewItem)
            .where(DistillationReviewItem.queue_id == queue_id)
        ).all()
        
        total = len(items)
        by_status = {}
        avg_score = 0
        scored_count = 0
        
        for item in items:
            by_status[item.status] = by_status.get(item.status, 0) + 1
            if item.review_score is not None:
                avg_score += item.review_score
                scored_count += 1
        
        return {
            "total_items": total,
            "by_status": by_status,
            "pending_count": by_status.get("pending", 0),
            "completed_count": by_status.get("approved", 0) + by_status.get("rejected", 0),
            "avg_score": round(avg_score / scored_count, 2) if scored_count > 0 else None
        }
    
    @staticmethod
    def add_items_to_queue(
        session: Session,
        queue_id: UUID,
        data: ReviewItemCreate
    ) -> int:
        """Add banked items to a review queue."""
        count = 0
        for banked_id in data.banked_ids:
            # Check if already in queue
            existing = session.exec(
                select(DistillationReviewItem)
                .where(DistillationReviewItem.queue_id == queue_id)
                .where(DistillationReviewItem.banked_id == banked_id)
            ).first()
            
            if existing:
                continue
            
            item = DistillationReviewItem(
                queue_id=queue_id,
                banked_id=banked_id,
                priority=data.priority,
                assigned_to=data.assigned_to
            )
            session.add(item)
            count += 1
        
        session.commit()
        return count
    
    @staticmethod
    def get_review_item(session: Session, item_id: UUID) -> Optional[DistillationReviewItem]:
        """Get a review item by ID."""
        return session.get(DistillationReviewItem, item_id)
    
    @staticmethod
    def list_review_items(
        session: Session,
        queue_id: UUID,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[DistillationReviewItem]:
        """List review items in a queue."""
        query = select(DistillationReviewItem).where(
            DistillationReviewItem.queue_id == queue_id
        )
        
        if status:
            query = query.where(DistillationReviewItem.status == status)
        if assigned_to:
            query = query.where(DistillationReviewItem.assigned_to == assigned_to)
        
        query = query.order_by(
            desc(DistillationReviewItem.priority),
            DistillationReviewItem.created_at
        ).offset(skip).limit(limit)
        
        return session.exec(query).all()
    
    @staticmethod
    def get_next_review_item(
        session: Session,
        queue_id: UUID,
        reviewer: Optional[str] = None
    ) -> Optional[DistillationReviewItem]:
        """Get the next item to review (highest priority pending item)."""
        query = select(DistillationReviewItem).where(
            DistillationReviewItem.queue_id == queue_id,
            DistillationReviewItem.status == "pending"
        )
        
        # Optionally filter by assigned reviewer
        if reviewer:
            query = query.where(
                (DistillationReviewItem.assigned_to == reviewer) |
                (DistillationReviewItem.assigned_to == None)
            )
        
        query = query.order_by(
            desc(DistillationReviewItem.priority),
            DistillationReviewItem.created_at
        ).limit(1)
        
        item = session.exec(query).first()
        
        # Mark as in_review if found
        if item:
            item.status = "in_review"
            if reviewer:
                item.assigned_to = reviewer
            session.add(item)
            session.commit()
            session.refresh(item)
        
        return item
    
    @staticmethod
    def submit_review(
        session: Session,
        item_id: UUID,
        action: ReviewAction,
        reviewer: Optional[str] = None
    ) -> Optional[DistillationReviewItem]:
        """Submit a review decision on an item."""
        item = session.get(DistillationReviewItem, item_id)
        if not item:
            return None
        
        item.status = action.action.value
        item.review_notes = action.review_notes
        item.review_score = action.review_score
        item.reviewed_by = reviewer
        item.reviewed_at = datetime.utcnow()
        
        session.add(item)
        
        # Also update the banked item's status based on review
        banked = session.get(DistillationBanked, item.banked_id)
        if banked:
            if action.action == ReviewStatus.APPROVED:
                banked.status = "approved"
            elif action.action == ReviewStatus.REJECTED:
                banked.status = "rejected"
            elif action.action == ReviewStatus.NEEDS_REVISION:
                banked.status = "draft"
            banked.reviewed_by = reviewer
            banked.reviewed_at = datetime.utcnow()
            session.add(banked)
        
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def update_review_item(
        session: Session,
        item_id: UUID,
        data: ReviewItemUpdate
    ) -> Optional[DistillationReviewItem]:
        """Update a review item."""
        item = session.get(DistillationReviewItem, item_id)
        if not item:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == 'status' and value:
                setattr(item, key, value.value if hasattr(value, 'value') else value)
            else:
                setattr(item, key, value)
        
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    
    @staticmethod
    def remove_review_item(session: Session, item_id: UUID) -> bool:
        """Remove an item from a review queue."""
        item = session.get(DistillationReviewItem, item_id)
        if not item:
            return False
        session.delete(item)
        session.commit()
        return True
    
    @staticmethod
    def export_review_queue(
        session: Session,
        queue_id: UUID,
        export_format: str = "csv",
        exported_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export review queue items for offline review."""
        import json
        import csv
        import io
        
        items = session.exec(
            select(DistillationReviewItem)
            .where(DistillationReviewItem.queue_id == queue_id)
            .order_by(DistillationReviewItem.created_at)
        ).all()
        
        export_data = []
        for item in items:
            banked = session.get(DistillationBanked, item.banked_id)
            response = None
            if banked:
                response = session.get(DistillationResponse, banked.response_id)
            
            row = {
                "item_id": str(item.id),
                "banked_id": str(item.banked_id),
                "status": item.status,
                "priority": item.priority,
                "assigned_to": item.assigned_to or "",
                "review_notes": item.review_notes or "",
                "review_score": item.review_score,
                "prompt": response.prompt_sent if response else "",
                "response": response.response_text if response else "",
                "provider": response.provider if response else "",
                "model": response.model if response else "",
            }
            export_data.append(row)
        
        if export_format == "json":
            content = json.dumps(export_data, indent=2, ensure_ascii=False)
        else:  # csv
            output = io.StringIO()
            if export_data:
                writer = csv.DictWriter(output, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            content = output.getvalue()
        
        # Create export record
        export_record = DistillationReviewExport(
            queue_id=queue_id,
            export_format=export_format,
            item_count=len(items),
            exported_by=exported_by
        )
        session.add(export_record)
        session.commit()
        session.refresh(export_record)
        
        return {
            "export_id": str(export_record.id),
            "content": content,
            "item_count": len(items),
            "format": export_format
        }
    
    @staticmethod
    def import_review_ratings(
        session: Session,
        queue_id: UUID,
        items: List[Dict[str, Any]],
        imported_by: Optional[str] = None
    ) -> int:
        """Import review ratings from external review."""
        updated_count = 0
        
        for item_data in items:
            item_id = item_data.get("item_id")
            if not item_id:
                continue
            
            try:
                item = session.get(DistillationReviewItem, UUID(item_id))
                if not item or item.queue_id != queue_id:
                    continue
                
                # Update item
                if "status" in item_data:
                    item.status = item_data["status"]
                if "review_score" in item_data and item_data["review_score"] is not None:
                    item.review_score = float(item_data["review_score"])
                if "review_notes" in item_data:
                    item.review_notes = item_data["review_notes"]
                
                item.reviewed_by = imported_by
                item.reviewed_at = datetime.utcnow()
                session.add(item)
                
                # Also update banked status
                banked = session.get(DistillationBanked, item.banked_id)
                if banked:
                    if item.status == "approved":
                        banked.status = "approved"
                    elif item.status == "rejected":
                        banked.status = "rejected"
                    banked.reviewed_by = imported_by
                    banked.reviewed_at = datetime.utcnow()
                    session.add(banked)
                
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to import item {item_id}: {e}")
                continue
        
        session.commit()
        return updated_count
    
    @staticmethod
    def auto_populate_queue(
        session: Session,
        queue_id: UUID,
        limit: int = 100
    ) -> int:
        """Auto-populate a review queue based on its criteria."""
        queue = session.get(DistillationReviewQueue, queue_id)
        if not queue:
            return 0
        
        # Build query based on queue criteria
        query = select(DistillationBanked).where(
            DistillationBanked.status == "draft"
        )
        
        if queue.domain_id:
            query = query.where(DistillationBanked.domain_id == queue.domain_id)
        if queue.topic_id:
            query = query.where(DistillationBanked.topic_id == queue.topic_id)
        if queue.min_quality_score is not None:
            query = query.where(DistillationBanked.quality_score >= queue.min_quality_score)
        
        query = query.limit(limit)
        banked_items = session.exec(query).all()
        
        # Add to queue (avoiding duplicates)
        count = 0
        for banked in banked_items:
            existing = session.exec(
                select(DistillationReviewItem)
                .where(DistillationReviewItem.queue_id == queue_id)
                .where(DistillationReviewItem.banked_id == banked.id)
            ).first()
            
            if existing:
                continue
            
            item = DistillationReviewItem(
                queue_id=queue_id,
                banked_id=banked.id
            )
            session.add(item)
            count += 1
        
        session.commit()
        return count
