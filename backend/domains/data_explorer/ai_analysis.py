"""
AI-powered data analysis service.

Performs exploratory data analysis, anomaly detection, and pattern identification
using LLM models on database tables.
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from llm.providers import get_provider
from .connection import get_explorer_connection
from .service import DataExplorerService
from .models import TableSelection, AnalysisRequest, AnalysisResult

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Service for AI-powered data analysis."""
    
    @staticmethod
    async def analyze_tables(request: AnalysisRequest) -> AnalysisResult:
        """
        Perform AI-powered analysis on selected tables.
        
        Args:
            request: Analysis request with tables, analysis types, and model config
            
        Returns:
            AnalysisResult with insights and recommendations
        """
        analysis_id = str(uuid4())
        start_time = time.time()
        
        try:
            # 1. Gather data from all selected tables
            table_data = await AIAnalysisService._gather_table_data(
                request.tables, 
                request.db_id
            )
            
            # 2. Build analysis prompt
            prompt = AIAnalysisService._build_analysis_prompt(
                table_data,
                request.analysis_types,
                request.context
            )
            
            # 3. Call LLM for analysis
            provider = get_provider(request.provider, request.model)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert data analyst specializing in exploratory data analysis, "
                              "anomaly detection, and pattern identification. Provide detailed, actionable insights "
                              "based on the data presented. Always structure your response as valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Stream and collect response
            full_response = ""
            async for event in provider.stream_chat(
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent analysis
                max_tokens=4000
            ):
                if event["type"] == "delta":
                    full_response += event["content"]
                elif event["type"] == "error":
                    raise Exception(f"LLM error: {event['error']}")
            
            # 4. Parse and structure the response
            insights = AIAnalysisService._parse_llm_response(full_response)
            
            # 5. Generate executive summary
            summary = AIAnalysisService._generate_summary(insights, table_data)
            
            # 6. Extract recommendations
            recommendations = AIAnalysisService._extract_recommendations(insights)
            
            execution_time = time.time() - start_time
            
            return AnalysisResult(
                analysis_id=analysis_id,
                tables=request.tables,
                analysis_types=request.analysis_types,
                provider=request.provider,
                model=request.model,
                insights=insights,
                summary=summary,
                recommendations=recommendations,
                metadata={
                    "execution_time_seconds": round(execution_time, 2),
                    "table_count": len(request.tables),
                    "total_rows_analyzed": sum(t.get("row_count", 0) for t in table_data),
                    "timestamp": datetime.utcnow().isoformat()
                },
                created_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def _gather_table_data(
        tables: List[Dict[str, str]],
        db_id: str
    ) -> List[Dict[str, Any]]:
        """
        Gather comprehensive data from all selected tables.
        
        Returns list of dicts with table metadata, samples, and statistics.
        """
        table_data = []
        
        for table in tables:
            try:
                schema = table.get('schema', 'public')
                table_name = table.get('table', '')
                
                # Skip if table name is empty
                if not table_name:
                    logger.warning(f"Skipping table with empty name: {table}")
                    continue
                
                # Get table profile with comprehensive statistics
                profile = DataExplorerService.profile_table(
                    schema=schema,
                    table=table_name,
                    max_distinct=20,
                    db_id=db_id
                )
                
                # Get sample rows (up to 100 for analysis)
                rows_response = DataExplorerService.get_table_rows(
                    schema=schema,
                    table=table_name,
                    page=1,
                    page_size=100,
                    db_id=db_id
                )
                
                # Get column metadata
                columns = DataExplorerService.get_columns(
                    schema=schema,
                    table=table_name,
                    db_id=db_id
                )
                
                table_info = {
                    "schema": schema,
                    "table": table_name,
                    "row_count": profile.get("total_rows", 0),
                    "column_count": len(columns),
                    "columns": [
                        {
                            "name": col.name,
                            "type": col.data_type,
                            "nullable": col.is_nullable
                        }
                        for col in columns
                    ],
                    "profile": profile.get("column_profiles", {}),
                    "sample_rows": rows_response.rows[:50],  # Limit to 50 for prompt size
                    "sample_row_count": len(rows_response.rows)
                }
                
                table_data.append(table_info)
                
            except Exception as e:
                schema = table.get('schema', 'unknown')
                table_name = table.get('table', 'unknown')
                logger.error(f"Error gathering data for {schema}.{table_name}: {str(e)}")
                # Continue with other tables
                table_data.append({
                    "schema": schema,
                    "table": table_name,
                    "error": str(e)
                })
        
        return table_data
    
    @staticmethod
    def _build_analysis_prompt(
        table_data: List[Dict[str, Any]],
        analysis_types: List[str],
        context: Optional[str]
    ) -> str:
        """Build comprehensive analysis prompt for the LLM."""
        
        # Build table descriptions
        table_descriptions = []
        for table in table_data:
            if "error" in table:
                table_descriptions.append(
                    f"**{table['schema']}.{table['table']}**: Error accessing table - {table['error']}"
                )
                continue
            
            desc = f"""
**Table: {table['schema']}.{table['table']}**
- Total Rows: {table['row_count']:,}
- Columns: {table['column_count']}

Column Details:
"""
            for col_name, col_profile in table['profile'].items():
                col_info = f"  • {col_name} ({col_profile.get('data_type', 'unknown')})"
                if col_profile.get('null_fraction', 0) > 0:
                    col_info += f" - {col_profile['null_fraction']*100:.1f}% null"
                if 'min' in col_profile and 'max' in col_profile:
                    col_info += f" - Range: [{col_profile['min']}, {col_profile['max']}]"
                if 'avg' in col_profile:
                    col_info += f" - Avg: {col_profile['avg']:.2f}"
                if col_profile.get('approx_distinct_count'):
                    col_info += f" - Distinct: {col_profile['approx_distinct_count']}"
                desc += col_info + "\n"
            
            # Add sample rows (limited)
            if table.get('sample_rows'):
                desc += f"\nSample Data (first 10 rows):\n"
                cols = [c['name'] for c in table['columns']]
                desc += f"Columns: {', '.join(cols)}\n"
                for i, row in enumerate(table['sample_rows'][:10]):
                    desc += f"  Row {i+1}: {row}\n"
            
            table_descriptions.append(desc)
        
        # Build analysis instructions
        analysis_instructions = {
            "eda": "Perform comprehensive exploratory data analysis including distributions, central tendencies, outliers, and data quality issues.",
            "anomaly": "Identify anomalies, outliers, and unusual patterns in the data. Flag data quality issues and potential errors.",
            "correlation": "Analyze correlations and relationships between columns, both within and across tables.",
            "quality": "Assess data quality including completeness, consistency, accuracy, and validity.",
            "trends": "Identify temporal trends, patterns, and seasonality if time-series data is present.",
            "patterns": "Discover hidden patterns, clusters, and interesting segments in the data."
        }
        
        requested_analyses = [
            f"- **{atype.upper()}**: {analysis_instructions.get(atype, 'General analysis')}"
            for atype in analysis_types
        ]
        
        context_section = f"\n\n**Business Context**: {context}" if context else ""
        
        prompt = f"""
You are analyzing the following database tables. Please provide a comprehensive analysis based on the requested analysis types.

{context_section}

# Tables to Analyze

{''.join(table_descriptions)}

# Requested Analysis Types

{chr(10).join(requested_analyses)}

# Instructions

Please provide your analysis in the following JSON format:

{{
  "eda": {{
    "overview": "General overview of the datasets",
    "distributions": ["Key distribution findings"],
    "outliers": ["Notable outliers or extreme values"],
    "data_quality_issues": ["Any data quality problems identified"]
  }},
  "anomaly_detection": {{
    "anomalies": [
      {{
        "table": "schema.table",
        "column": "column_name",
        "description": "Description of the anomaly",
        "severity": "high|medium|low",
        "affected_rows": "estimate or count"
      }}
    ],
    "patterns": ["Unusual patterns detected"]
  }},
  "correlations": {{
    "significant_correlations": [
      {{
        "columns": ["col1", "col2"],
        "relationship": "description",
        "strength": "strong|moderate|weak"
      }}
    ],
    "cross_table_relationships": ["Relationships across tables"]
  }},
  "quality_assessment": {{
    "overall_score": 0-100,
    "issues": [
      {{
        "table": "schema.table",
        "issue": "description",
        "severity": "critical|high|medium|low",
        "recommendation": "how to fix"
      }}
    ]
  }},
  "key_insights": ["Top 5-10 most important insights"],
  "recommendations": ["Actionable recommendations based on the analysis"]
}}

Focus on actionable insights and be specific with your findings. Reference actual column names and values from the data.
"""
        
        return prompt
    
    @staticmethod
    def _parse_llm_response(response: str) -> Dict[str, Any]:
        """Parse and structure the LLM response."""
        try:
            # Try to extract JSON from the response
            # Sometimes LLMs wrap JSON in markdown code blocks
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            elif response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            insights = json.loads(response)
            return insights
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            # Return raw response in a structured format
            return {
                "raw_response": response,
                "parse_error": str(e),
                "key_insights": ["Unable to parse structured insights. See raw_response."]
            }
    
    @staticmethod
    def _generate_summary(insights: Dict[str, Any], table_data: List[Dict[str, Any]]) -> str:
        """Generate an executive summary of the analysis."""
        
        table_names = [f"{t.get('schema', '')}.{t.get('table', '')}" for t in table_data if 'error' not in t]
        total_rows = sum(t.get('row_count', 0) for t in table_data if 'error' not in t)
        
        summary_parts = [
            f"Analysis of {len(table_names)} table(s): {', '.join(table_names)}",
            f"Total rows analyzed: {total_rows:,}"
        ]
        
        # Add key insights if available
        if "key_insights" in insights and insights["key_insights"]:
            summary_parts.append("\nKey Findings:")
            for insight in insights["key_insights"][:5]:
                summary_parts.append(f"• {insight}")
        
        # Add quality score if available
        if "quality_assessment" in insights:
            qa = insights["quality_assessment"]
            if "overall_score" in qa:
                summary_parts.append(f"\nOverall Data Quality Score: {qa['overall_score']}/100")
        
        # Add anomaly count if available
        if "anomaly_detection" in insights:
            anomalies = insights["anomaly_detection"].get("anomalies", [])
            if anomalies:
                high_severity = len([a for a in anomalies if a.get("severity") == "high"])
                summary_parts.append(f"\nAnomalies Detected: {len(anomalies)} ({high_severity} high severity)")
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def _extract_recommendations(insights: Dict[str, Any]) -> List[str]:
        """Extract actionable recommendations from the insights."""
        recommendations = []
        
        # Direct recommendations from insights
        if "recommendations" in insights:
            recommendations.extend(insights["recommendations"])
        
        # Recommendations from quality issues
        if "quality_assessment" in insights:
            issues = insights["quality_assessment"].get("issues", [])
            for issue in issues:
                if "recommendation" in issue:
                    recommendations.append(issue["recommendation"])
        
        # Recommendations from anomalies
        if "anomaly_detection" in insights:
            anomalies = insights["anomaly_detection"].get("anomalies", [])
            high_severity = [a for a in anomalies if a.get("severity") == "high"]
            if high_severity:
                recommendations.insert(0, 
                    f"Address {len(high_severity)} high-severity anomalies identified in the data")
        
        return list(dict.fromkeys(recommendations))[:10]  # Deduplicate and limit to 10

