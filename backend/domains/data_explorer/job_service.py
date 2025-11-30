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
from .db_models import AIAnalysisResult
from .models import AnalysisRequest, AnalysisResult
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
        tags: Optional[List[str]] = None
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
            tags=tags or []
        )
        
        session.add(job)
        session.commit()
        session.refresh(job)
        
        return job
    
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
            
            # Stage 2: Build analysis prompt
            job.current_stage = "Building analysis prompt..."
            job.progress = 30
            session.add(job)
            session.commit()
            
            prompt = AnalysisJobService._build_mcp_analysis_prompt(
                table_data=table_data,
                analysis_types=job.analysis_types,
                context=job.context
            )
            
            # Stage 3: Run AI analysis
            job.current_stage = f"Analyzing with {job.provider}/{job.model}..."
            job.progress = 40
            session.add(job)
            session.commit()
            
            provider = get_provider(job.provider, job.model)
            
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert data analyst. You MUST respond with ONLY valid JSON, no other text.\n\n"
                        "CRITICAL: Your entire response must be a single JSON object. Do not include any "
                        "explanatory text before or after the JSON. Do not wrap the JSON in markdown code blocks.\n\n"
                        "Return a comprehensive analysis as a JSON object with the structure specified in the user prompt."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
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
                    job.progress = min(40 + (len(full_response) // 100), 90)
                    session.add(job)
                    session.commit()
                elif event["type"] == "error":
                    raise Exception(f"LLM error: {event['error']}")
            
            # Stage 4: Parse and save results
            job.current_stage = "Parsing and saving results..."
            job.progress = 95
            session.add(job)
            session.commit()
            
            insights = AnalysisJobService._parse_insights(full_response)
            
            # If parsing failed, store raw response for debugging
            if "parse_error" in insights:
                insights["raw_response"] = full_response[:5000]  # Limit to 5KB for storage
            
            summary = AnalysisJobService._generate_summary(insights, table_data)
            recommendations = AnalysisJobService._extract_recommendations(insights)
            
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
    def _build_mcp_analysis_prompt(
        table_data: List[Dict[str, Any]],
        analysis_types: List[str],
        context: Optional[str]
    ) -> str:
        """Build analysis prompt using MCP-gathered data."""
        
        table_descriptions = []
        for table in table_data:
            if "error" in table:
                table_descriptions.append(
                    f"**{table['schema']}.{table['table']}**: Error - {table['error']}"
                )
                continue
            
            profile = table.get('profile', {})
            total_rows = profile.get('total_rows', 'Unknown')
            if isinstance(total_rows, (int, float)):
                total_rows_str = f"{int(total_rows):,}"
            else:
                total_rows_str = str(total_rows)
            
            desc = f"""
**Table: {table['schema']}.{table['table']}**
- Total Rows: {total_rows_str}
- Column Count: {len(profile.get('column_profiles', {}))}

Column Profiles:
"""
            for col_name, col_profile in profile.get('column_profiles', {}).items():
                col_info = f"  • {col_name} ({col_profile.get('data_type', 'unknown')})"
                
                # Null fraction
                null_frac = col_profile.get('null_fraction', 0)
                if null_frac > 0:
                    try:
                        col_info += f" - {float(null_frac)*100:.1f}% null"
                    except (ValueError, TypeError):
                        col_info += f" - {null_frac}% null"
                
                # Range
                if 'min' in col_profile and 'max' in col_profile:
                    col_info += f" - Range: [{col_profile['min']}, {col_profile['max']}]"
                
                # Average
                if 'avg' in col_profile:
                    try:
                        col_info += f" - Avg: {float(col_profile['avg']):.2f}"
                    except (ValueError, TypeError):
                        col_info += f" - Avg: {col_profile['avg']}"
                
                # Distinct count
                distinct_count = col_profile.get('approx_distinct_count')
                if distinct_count:
                    if isinstance(distinct_count, (int, float)):
                        col_info += f" - Distinct: {int(distinct_count):,}"
                    else:
                        col_info += f" - Distinct: {distinct_count}"
                
                desc += col_info + "\n"
            
            # Add sample data
            if table.get('samples'):
                desc += f"\nSample Data (first 10 rows): {len(table['samples'])} rows sampled\n"
            
            table_descriptions.append(desc)
        
        context_section = f"\n\n**Business Context**: {context}" if context else ""
        
        analysis_instructions = {
            "eda": "Comprehensive EDA: distributions, outliers, quality issues",
            "anomaly": "Anomaly detection: unusual patterns, data errors",
            "correlation": "Correlation analysis: relationships within/across tables",
            "quality": "Data quality: completeness, consistency, accuracy",
            "trends": "Trend analysis: temporal patterns, seasonality",
            "patterns": "Pattern discovery: clusters, segments, hidden insights"
        }
        
        requested = "\n".join([
            f"- **{t.upper()}**: {analysis_instructions.get(t, t)}"
            for t in analysis_types
        ])
        
        return f"""
Analyze these database tables using the profiling data gathered via MCP tools:
{context_section}

# Tables
{''.join(table_descriptions)}

# Analysis Types Requested
{requested}

# CRITICAL OUTPUT REQUIREMENTS

Your response MUST be a single valid JSON object with NO additional text.
Do NOT wrap in markdown code blocks (```json).
Do NOT add any explanatory text before or after the JSON.
Start your response with {{ and end with }}.

# Required JSON Structure

{{
  "eda": {{
    "overview": "Brief overview of data characteristics",
    "key_statistics": {{"table.column": {{"metric": "value"}}}},
    "distributions": [{{"column": "name", "type": "normal/skewed/uniform", "notes": "..."}}],
    "outliers": [{{"column": "name", "count": 0, "examples": [...]}}],
    "data_quality_issues": [{{"issue": "...", "severity": "high/medium/low", "affected_columns": [...]}}]
  }},
  "anomaly_detection": {{
    "anomalies": [{{
      "table": "schema.table",
      "column": "column_name",
      "description": "What makes this anomalous",
      "severity": "high",
      "recommendation": "How to fix or investigate"
    }}],
    "patterns": ["Unusual pattern 1", "Unusual pattern 2"]
  }},
  "correlations": {{
    "significant_correlations": [{{
      "columns": ["col1", "col2"],
      "coefficient": 0.85,
      "interpretation": "Strong positive relationship"
    }}],
    "cross_table_relationships": ["Description of relationships between tables"]
  }},
  "quality_assessment": {{
    "overall_score": 85,
    "completeness": {{"score": 90, "notes": "..."}},
    "consistency": {{"score": 80, "notes": "..."}},
    "accuracy": {{"score": 85, "notes": "..."}},
    "issues": [{{
      "table": "schema.table",
      "issue": "Specific issue description",
      "severity": "high",
      "recommendation": "How to fix"
    }}]
  }},
  "key_insights": [
    "Most important finding 1",
    "Most important finding 2",
    "Most important finding 3"
  ],
  "recommendations": [
    "Specific actionable recommendation 1",
    "Specific actionable recommendation 2",
    "Specific actionable recommendation 3"
  ]
}}

REMEMBER: Return ONLY the JSON object above. No markdown, no explanations, just pure JSON.
"""
    
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
    def _generate_summary(insights: Dict[str, Any], table_data: List[Dict[str, Any]]) -> str:
        """Generate executive summary."""
        tables = [f"{t.get('schema')}.{t.get('table')}" for t in table_data if 'error' not in t]
        
        parts = [f"Analysis of {len(tables)} table(s): {', '.join(tables)}"]
        
        if "key_insights" in insights:
            parts.append("\nKey Findings:")
            for insight in insights["key_insights"][:5]:
                parts.append(f"• {insight}")
        
        if "quality_assessment" in insights and "overall_score" in insights["quality_assessment"]:
            parts.append(f"\nData Quality Score: {insights['quality_assessment']['overall_score']}/100")
        
        if "anomaly_detection" in insights:
            anomalies = insights["anomaly_detection"].get("anomalies", [])
            if anomalies:
                high = len([a for a in anomalies if a.get("severity") == "high"])
                parts.append(f"\nAnomalies: {len(anomalies)} ({high} high severity)")
        
        return "\n".join(parts)
    
    @staticmethod
    def _extract_recommendations(insights: Dict[str, Any]) -> List[str]:
        """Extract recommendations."""
        recs = []
        
        if "recommendations" in insights:
            recs.extend(insights["recommendations"])
        
        if "quality_assessment" in insights:
            for issue in insights["quality_assessment"].get("issues", []):
                if "recommendation" in issue:
                    recs.append(issue["recommendation"])
        
        return list(dict.fromkeys(recs))[:10]
    
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

