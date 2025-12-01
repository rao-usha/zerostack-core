"""
Async job service for data analysis with MCP integration.

Manages background analysis jobs, integrates with MCP tools for dynamic data exploration,
and provides job status tracking.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import Session, select, desc
from .job_models import AnalysisJob
from .db_models import AIAnalysisResult, PromptRecipe
from .models import AnalysisRequest, AnalysisResult
from .analysis_prompts import AnalysisPromptTemplates
from .dictionary_service import upsert_dictionary_entries
from ..chat.service import ChatService
from llm.providers import get_provider

logger = logging.getLogger(__name__)


class AnalysisJobService:
    """Service for managing async analysis jobs."""
    
    @staticmethod
    def create_job(
        session: Session,
        name: str,
        tables: List[Dict[str, str]],
        analysis_types: List[str],
        provider: str,
        model: str,
        db_id: str = "default",
        context: Optional[str] = None,
        user_id: Optional[UUID] = None,
        tags: Optional[List[str]] = None,
        prompt_recipe_id: Optional[int] = None,
        prompt_overrides: Optional[Dict[str, Any]] = None
    ) -> AnalysisJob:
        """
        Create a new analysis job.
        
        Returns immediately with job ID. Actual analysis runs in background.
        """
        job = AnalysisJob(
            user_id=user_id,
            name=name,
            description=f"Analysis of {len(tables)} table(s) using {provider}/{model}",
            tables=tables,
            analysis_types=analysis_types,
            provider=provider,
            model=model,
            context=context,
            db_id=db_id,
            status="pending",
            progress=0,
            tags=tags or [],
            prompt_recipe_id=prompt_recipe_id,
            prompt_overrides=prompt_overrides
        )
        
        session.add(job)
        session.commit()
        session.refresh(job)
        
        return job
    
    @staticmethod
    def render_prompt_from_recipe(
        session: Session,
        recipe_id: int,
        action_type: str,
        table_data: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Render system_message and user_message from a prompt recipe.
        
        Returns:
            Tuple of (system_message, user_message)
        """
        recipe = session.get(PromptRecipe, recipe_id)
        if not recipe:
            raise ValueError(f"Prompt recipe {recipe_id} not found")
        
        if recipe.action_type != action_type:
            logger.warning(
                f"Recipe action_type={recipe.action_type} does not match job action_type={action_type}"
            )
        
        # Build schema summary and sample rows from table_data
        schema_summary = AnalysisPromptTemplates._build_schema_summary(table_data)
        sample_rows = AnalysisPromptTemplates._build_sample_rows(table_data)
        
        # Simple template substitution (can upgrade to Jinja2 later)
        user_message = recipe.user_template
        user_message = user_message.replace("{schema_summary}", schema_summary)
        user_message = user_message.replace("{sample_rows}", sample_rows)
        
        # Add context if provided
        if context:
            user_message = f"**Business Context**: {context}\n\n{user_message}"
        
        return recipe.system_message, user_message
    
    @staticmethod
    async def run_analysis_job(job_id: UUID, session: Session):
        """
        Execute analysis job in background using MCP tools.
        
        This method:
        1. Updates job status to 'running'
        2. Uses MCP tools to explore and profile data
        3. Sends context to LLM for analysis
        4. Saves results and updates job
        """
        job = session.get(AnalysisJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        # Update status to running
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.current_stage = "Initializing analysis..."
        job.progress = 5
        session.add(job)
        session.commit()
        
        try:
            # Stage 1: Gather data using MCP tools
            job.current_stage = "Gathering table data with MCP tools..."
            job.progress = 10
            session.add(job)
            session.commit()
            
            table_data = await AnalysisJobService._gather_data_with_mcp(
                tables=job.tables,
                db_id=job.db_id
            )
            
            # Stage 2: Run analysis for each analysis type
            job.current_stage = "Running specialized analyses..."
            job.progress = 30
            session.add(job)
            session.commit()
            
            combined_insights = {}
            all_recommendations = []
            
            provider = get_provider(job.provider, job.model)
            
            # Run each analysis type separately
            for i, analysis_type in enumerate(job.analysis_types):
                job.current_stage = f"Running {analysis_type} analysis..."
                base_progress = 30 + (i * 50 // len(job.analysis_types))
                job.progress = base_progress
                session.add(job)
                session.commit()
                
                # Build specialized prompt for this analysis type
                # Check if we should use a prompt recipe or default prompts
                if job.prompt_recipe_id:
                    try:
                        system_message, user_message = AnalysisJobService.render_prompt_from_recipe(
                            session=session,
                            recipe_id=job.prompt_recipe_id,
                            action_type=analysis_type,
                            table_data=table_data,
                            context=job.context
                        )
                        logger.info(f"Using prompt recipe {job.prompt_recipe_id} for {analysis_type}")
                    except Exception as e:
                        logger.warning(f"Failed to use recipe {job.prompt_recipe_id}: {e}. Falling back to default prompts.")
                        system_message, user_message = AnalysisPromptTemplates.build_analysis_prompt(
                            analysis_type=analysis_type,
                            table_data=table_data,
                            context=job.context
                        )
                else:
                    # Use default template-based prompts
                    system_message, user_message = AnalysisPromptTemplates.build_analysis_prompt(
                        analysis_type=analysis_type,
                        table_data=table_data,
                        context=job.context
                    )
                
                # Store prompts in job metadata for later retrieval/editing
                if not job.job_metadata:
                    job.job_metadata = {}
                if f"{analysis_type}_system_message" not in job.job_metadata:
                    job.job_metadata[f"{analysis_type}_system_message"] = system_message
                    job.job_metadata[f"{analysis_type}_user_message"] = user_message
                    session.add(job)
                    session.commit()
                
                messages = [
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
                
                # Collect streaming response
                full_response = ""
                async for event in provider.stream_chat(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=4000
                ):
                    if event["type"] == "delta":
                        full_response += event["content"]
                        # Update progress during generation
                        job.progress = min(base_progress + (len(full_response) // 200), base_progress + 40)
                        session.add(job)
                        session.commit()
                    elif event["type"] == "error":
                        raise Exception(f"LLM error: {event['error']}")
                
                # Parse results for this analysis type
                analysis_result = AnalysisJobService._parse_insights(full_response)
                
                # If parsing failed, store raw response for debugging
                if "parse_error" in analysis_result:
                    analysis_result["raw_response"] = full_response[:5000]
                
                # Special handling for column_documentation: ingest into data dictionary
                if analysis_type == "column_documentation" and "parse_error" not in analysis_result:
                    try:
                        # The LLM should return a list of dictionary entries
                        # Try to extract entries from the parsed result
                        entries_to_ingest = []
                        
                        # Check if the result is a list (expected format)
                        if isinstance(analysis_result, list):
                            entries_to_ingest = analysis_result
                        # Or if it's wrapped in a key
                        elif isinstance(analysis_result, dict):
                            # Try common keys
                            for key in ["entries", "columns", "dictionary_entries"]:
                                if key in analysis_result and isinstance(analysis_result[key], list):
                                    entries_to_ingest = analysis_result[key]
                                    break
                        
                        if entries_to_ingest:
                            # Ingest into dictionary
                            count = upsert_dictionary_entries(
                                session=session,
                                entries=entries_to_ingest,
                                database_name=job.db_id
                            )
                            logger.info(f"Ingested {count} dictionary entries from job {job_id}")
                            
                            # Add metadata about ingestion
                            analysis_result = {
                                "ingestion_summary": f"Successfully ingested {count} column definitions into data dictionary",
                                "entries": entries_to_ingest
                            }
                        else:
                            logger.warning(f"No dictionary entries found in column_documentation result for job {job_id}")
                            analysis_result["warning"] = "No entries found to ingest"
                    except Exception as ingest_error:
                        logger.error(f"Failed to ingest dictionary entries for job {job_id}: {ingest_error}")
                        analysis_result["ingestion_error"] = str(ingest_error)
                
                combined_insights[analysis_type] = analysis_result
                
                # Extract recommendations from this analysis
                if "recommended_remediations" in analysis_result:
                    all_recommendations.extend(analysis_result["recommended_remediations"])
                if "recommended_next_analyses" in analysis_result:
                    all_recommendations.extend(analysis_result["recommended_next_analyses"])
            
            # Stage 3: Generate AI-enhanced executive summary
            job.current_stage = "Generating executive summary..."
            job.progress = 85
            session.add(job)
            session.commit()
            
            # Generate AI summary of all findings
            ai_summary = await AnalysisJobService._generate_ai_summary(
                insights=combined_insights,
                table_data=table_data,
                analysis_types=job.analysis_types,
                provider=provider
            )
            
            # Stage 4: Combine and save results
            job.current_stage = "Finalizing results..."
            job.progress = 95
            session.add(job)
            session.commit()
            
            insights = combined_insights
            summary = ai_summary  # Use AI-generated summary instead of basic concatenation
            recommendations = list(dict.fromkeys(all_recommendations))[:15]  # Unique, max 15
            
            # Create analysis result record
            analysis_result = AIAnalysisResult(
                name=job.name,
                description=job.description,
                tables=job.tables,
                analysis_types=job.analysis_types,
                provider=job.provider,
                model=job.model,
                context=job.context,
                insights=insights,
                summary=summary,
                recommendations=recommendations,
                execution_metadata={
                    "job_id": str(job.id),
                    "table_count": len(job.tables),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": datetime.utcnow().isoformat(),
                    "used_mcp_tools": True
                },
                db_id=job.db_id,
                tags=job.tags
            )
            
            session.add(analysis_result)
            session.commit()
            session.refresh(analysis_result)
            
            # Update job with result
            job.status = "completed"
            job.result_id = analysis_result.id
            job.completed_at = datetime.utcnow()
            job.current_stage = "Analysis complete"
            job.progress = 100
            session.add(job)
            session.commit()
            
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}", exc_info=True)
            
            job.status = "failed"
            job.error_message = str(e)
            job.error_details = {"exception": str(e), "type": type(e).__name__}
            job.completed_at = datetime.utcnow()
            job.current_stage = "Failed"
            session.add(job)
            session.commit()
    
    @staticmethod
    async def _gather_data_with_mcp(
        tables: List[Dict[str, str]],
        db_id: str
    ) -> List[Dict[str, Any]]:
        """
        Gather data using MCP tools (same as Chat uses).
        
        Uses MCP tool execution to profile tables and sample data.
        """
        table_data = []
        
        for table in tables:
            schema = table.get('schema', 'public')
            table_name = table.get('table', '')
            
            if not table_name:
                continue
            
            try:
                # Use MCP profile_table tool
                profile_response = ChatService._execute_tool(
                    'profile_table',
                    {
                        'schema': schema,
                        'table': table_name,
                        'connection_id': db_id
                    }
                )
                
                # Use MCP sample_rows tool
                sample_response = ChatService._execute_tool(
                    'sample_rows',
                    {
                        'schema': schema,
                        'table': table_name,
                        'limit': 100,
                        'connection_id': db_id
                    }
                )
                
                # Extract data from MCP response
                if not profile_response.get('success'):
                    raise Exception(f"Profile failed: {profile_response.get('error', 'Unknown error')}")
                
                if not sample_response.get('success'):
                    raise Exception(f"Sample failed: {sample_response.get('error', 'Unknown error')}")
                
                profile_result = profile_response.get('data', {})
                sample_result = sample_response.get('data', {})
                
                table_info = {
                    "schema": schema,
                    "table": table_name,
                    "profile": profile_result,
                    "samples": sample_result.get('rows', [])[:50],  # Limit to 50 for prompt
                    "sample_count": len(sample_result.get('rows', []))
                }
                
                table_data.append(table_info)
                
            except Exception as e:
                logger.error(f"Error gathering data for {schema}.{table_name}: {str(e)}")
                table_data.append({
                    "schema": schema,
                    "table": table_name,
                    "error": str(e)
                })
        
        return table_data
    
    @staticmethod
    def _parse_insights(response: str) -> Dict[str, Any]:
        """Parse LLM JSON response with robust error handling."""
        import json
        import re
        
        original_response = response
        response = response.strip()
        
        # Try to extract JSON from markdown code blocks
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_block_match:
            response = json_block_match.group(1)
        else:
            # Remove markdown code block markers if present
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
        
        response = response.strip()
        
        # Try to find JSON object in the response
        if not response.startswith('{'):
            # Look for first { and last }
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1 and end > start:
                response = response[start:end+1]
        
        # Attempt to parse
        try:
            parsed = json.loads(response)
            
            # Validate it has expected structure
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a JSON object")
            
            return parsed
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {str(e)}")
            logger.debug(f"Response preview: {original_response[:500]}")
            
            # Try to extract insights from plain text as fallback
            lines = original_response.split('\n')
            insights = [line.strip() for line in lines if line.strip() and len(line.strip()) > 20][:10]
            
            return {
                "parse_error": f"{type(e).__name__}: {str(e)}",
                "raw_response": original_response[:10000],  # Store up to 10KB
                "key_insights": insights if insights else [
                    "The AI response could not be parsed as structured JSON.",
                    "Please review the raw response below for insights.",
                    "Consider re-running with a different model (GPT-4o recommended)."
                ],
                "extracted_text": insights
            }
    
    @staticmethod
    async def _generate_ai_summary(
        insights: Dict[str, Any],
        table_data: List[Dict[str, Any]],
        analysis_types: List[str],
        provider: Any
    ) -> str:
        """
        Generate an AI-enhanced executive summary of all analysis findings.
        
        This creates a cohesive, business-friendly summary that synthesizes
        findings from all analysis types into a clear narrative.
        """
        tables = [f"{t.get('schema')}.{t.get('table')}" for t in table_data if 'error' not in t]
        
        # Build a structured representation of findings for the LLM
        findings_text = f"# Analysis Results\n\n"
        findings_text += f"**Tables Analyzed**: {', '.join(tables)}\n"
        findings_text += f"**Analysis Types**: {', '.join(analysis_types)}\n\n"
        
        # Include executive summaries from each analysis
        for analysis_type, result in insights.items():
            findings_text += f"## {analysis_type.replace('_', ' ').title()}\n"
            if isinstance(result, dict):
                if "executive_summary" in result:
                    findings_text += f"{result['executive_summary']}\n\n"
                
                # Add key metrics/counts
                if "issues" in result and isinstance(result["issues"], list):
                    findings_text += f"- Found {len(result['issues'])} quality issues\n"
                if "anomalies" in result and isinstance(result["anomalies"], list):
                    findings_text += f"- Detected {len(result['anomalies'])} anomalies\n"
                if "relationships" in result and isinstance(result["relationships"], list):
                    findings_text += f"- Identified {len(result['relationships'])} relationships\n"
                if "trends" in result and isinstance(result["trends"], list):
                    findings_text += f"- Found {len(result['trends'])} trends\n"
                if "entries" in result and isinstance(result["entries"], list):
                    findings_text += f"- Documented {len(result['entries'])} columns\n"
                    
                findings_text += "\n"
            else:
                findings_text += f"(Structured data)\n\n"
        
        # Create summarization prompt
        system_message = """You are a senior data analyst creating executive summaries.

Your job is to synthesize multiple analysis results into a clear, actionable executive summary.

The summary should:
- Be 3-5 sentences maximum
- Highlight the most important findings
- Use business-friendly language (avoid jargon)
- Focus on actionable insights and priorities
- Be written for stakeholders who need the bottom line

Do NOT:
- Repeat the table names or analysis types (already shown in UI)
- Use technical jargon or field names
- Include markdown formatting
- List every finding - only the most critical ones"""

        user_message = f"""Based on these analysis results, write a concise executive summary:

{findings_text}

Return ONLY the executive summary text - no markdown, no headers, just 3-5 clear sentences."""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Generate summary with low temperature for consistency
            full_response = ""
            async for event in provider.stream_chat(
                messages=messages,
                temperature=0.2,
                max_tokens=500
            ):
                if event["type"] == "delta":
                    full_response += event["content"]
                elif event["type"] == "error":
                    logger.error(f"Error generating summary: {event['error']}")
                    return AnalysisJobService._generate_fallback_summary(insights, tables, analysis_types)
            
            # Clean up the response
            summary = full_response.strip()
            
            # Fallback if summary is too short or empty
            if len(summary) < 20:
                return AnalysisJobService._generate_fallback_summary(insights, tables, analysis_types)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate AI summary: {e}")
            return AnalysisJobService._generate_fallback_summary(insights, tables, analysis_types)
    
    @staticmethod
    def _generate_fallback_summary(insights: Dict[str, Any], tables: List[str], analysis_types: List[str]) -> str:
        """Generate a basic fallback summary if AI generation fails."""
        parts = [f"Analyzed {len(tables)} table(s) using {len(analysis_types)} analysis type(s)."]
        
        # Extract key counts
        issue_count = 0
        anomaly_count = 0
        relationship_count = 0
        
        for result in insights.values():
            if isinstance(result, dict):
                if "issues" in result and isinstance(result["issues"], list):
                    issue_count += len(result["issues"])
                if "anomalies" in result and isinstance(result["anomalies"], list):
                    anomaly_count += len(result["anomalies"])
                if "relationships" in result and isinstance(result["relationships"], list):
                    relationship_count += len(result["relationships"])
        
        if issue_count > 0:
            parts.append(f"Found {issue_count} quality issues.")
        if anomaly_count > 0:
            parts.append(f"Detected {anomaly_count} anomalies.")
        if relationship_count > 0:
            parts.append(f"Identified {relationship_count} relationships between columns.")
        
        return " ".join(parts)
    
    @staticmethod
    def _extract_recommendations(insights: Dict[str, Any]) -> List[str]:
        """Extract recommendations from combined analysis results."""
        # This is now handled during the analysis loop
        # This method is kept for compatibility but does minimal work
        return []
    
    @staticmethod
    def get_job(session: Session, job_id: UUID) -> Optional[AnalysisJob]:
        """Get job by ID."""
        return session.get(AnalysisJob, job_id)
    
    @staticmethod
    def list_jobs(
        session: Session,
        user_id: Optional[UUID] = None,
        db_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[AnalysisJob]:
        """List jobs with optional filters."""
        query = select(AnalysisJob).order_by(desc(AnalysisJob.created_at)).limit(limit)
        
        if user_id:
            query = query.where(AnalysisJob.user_id == user_id)
        if db_id:
            query = query.where(AnalysisJob.db_id == db_id)
        if status:
            query = query.where(AnalysisJob.status == status)
        
        return list(session.exec(query).all())
    
    @staticmethod
    def cancel_job(session: Session, job_id: UUID) -> bool:
        """Cancel a running or pending job."""
        job = session.get(AnalysisJob, job_id)
        if not job:
            return False
        
        if job.status in ['completed', 'failed', 'cancelled']:
            return False
        
        job.status = "cancelled"
        job.cancelled_at = datetime.utcnow()
        job.current_stage = "Cancelled by user"
        session.add(job)
        session.commit()
        
        return True
    
    @staticmethod
    def delete_job(session: Session, job_id: UUID) -> bool:
        """Delete a job (only if completed/failed/cancelled)."""
        job = session.get(AnalysisJob, job_id)
        if not job:
            return False
        
        if job.status in ['pending', 'running']:
            return False
        
        session.delete(job)
        session.commit()
        
        return True

