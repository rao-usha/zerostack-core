"""
Analysis prompt templates for specialized data analysis types.

Each analysis type has:
- A system message defining the LLM's role and constraints
- A user template with placeholders for {{schema_summary}} and {{sample_rows}}
- A specific JSON schema that must be returned
"""

from typing import Dict, Any, List, Optional


class AnalysisPromptTemplates:
    """Centralized prompt templates for all analysis types."""
    
    # Analysis type metadata
    ANALYSIS_TYPES = {
        "profiling": {
            "name": "Data Profiling",
            "description": "Structural and statistical properties of data",
            "icon": "BarChart3"
        },
        "quality": {
            "name": "Data Quality Checks",
            "description": "Missing data, duplicates, invalid values, violations",
            "icon": "Shield"
        },
        "anomaly": {
            "name": "Outlier & Anomaly Detection",
            "description": "Unusual values, distribution shifts, temporal anomalies",
            "icon": "AlertTriangle"
        },
        "relationships": {
            "name": "Relationship Analysis",
            "description": "Correlations and associations between columns",
            "icon": "TrendingUp"
        },
        "trends": {
            "name": "Trend & Time-Series Analysis",
            "description": "Temporal behavior, trends, seasonality, cycles",
            "icon": "TrendingUp"
        },
        "patterns": {
            "name": "Pattern Discovery",
            "description": "Higher-order patterns, clusters, segments, groups",
            "icon": "Brain"
        },
        "column_documentation": {
            "name": "Column Documentation",
            "description": "Generate data dictionary with business descriptions",
            "icon": "Book"
        }
    }
    
    @staticmethod
    def get_system_message(analysis_type: str) -> str:
        """Get system message for analysis type."""
        messages = {
            "profiling": """You are a senior data engineer performing DATA PROFILING on database tables.

Your job is to describe the structural and statistical properties of the data ONLY:
- Column data types
- Cardinality / distinct values
- Basic statistics for numeric columns
- Common values and distributions
- Missing value counts and basic patterns

You MUST NOT:
- Perform anomaly detection
- Infer trends over time
- Infer relationships between columns
- Judge data quality beyond describing nulls and simple counts

Your response MUST be valid JSON and MUST conform exactly to the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.
If you are unsure about something, state "unknown" rather than guessing.""",

            "quality": """You are a data quality specialist performing DATA QUALITY CHECKS on database tables.

Your job is to:
- Identify missing data patterns
- Identify duplicates (when detectable)
- Identify invalid or inconsistent values
- Identify range or format violations
- Identify potential schema mismatches

You MUST focus on rule-like, deterministic integrity issues.
You MUST NOT perform anomaly detection unrelated to explicit violations.
You MUST NOT infer business meaning beyond what the data clearly suggests.

Your response MUST be valid JSON and MUST conform exactly to the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.
If something is uncertain, mark it clearly as "potential_issue" with an explanation.""",

            "anomaly": """You are a statistician performing OUTLIER AND ANOMALY DETECTION on database tables.

Your job is to:
- Identify unusual or extreme values
- Identify distribution shifts or surprising patterns
- Identify temporal anomalies if time-like columns are present

You MUST:
- Clearly distinguish between strong and weak evidence of anomalies.
- Tie every anomaly to specific columns, tables, and simple metrics when possible.

You MUST NOT:
- Perform general profiling or quality checks unless they directly support an anomaly.
- Infer business meaning beyond what is needed to describe the anomaly.

Your response MUST be valid JSON matching the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.""",

            "relationships": """You are a data scientist performing RELATIONSHIP ANALYSIS between columns.

Your job is to:
- Identify and describe relationships between pairs or small sets of variables
- Focus on associations, correlations, and clear directional tendencies

You MUST:
- Stay focused on relationships (how variables move together).
- Prefer simple, interpretable descriptions over complex speculation.

You MUST NOT:
- Perform anomaly detection
- Perform trend analysis
- Perform clustering or high-order pattern discovery

Your response MUST be valid JSON matching the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.
If you are only inferring correlation qualitatively from sample data, state that clearly.""",

            "trends": """You are a time-series analyst performing TREND AND TIME-SERIES ANALYSIS.

Your job is to:
- Analyze columns that represent time or can be ordered in time
- Identify trends, seasonality, cycles, and change points

You MUST:
- Focus strictly on temporal behavior.
- Clearly specify which time-like column(s) you are using.

You MUST NOT:
- Perform anomaly detection beyond describing trend-related changes.
- Perform general profiling, correlations, or pattern discovery outside temporal context.

Your response MUST be valid JSON matching the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.
If no time-like columns are available, return a JSON object explaining that.""",

            "patterns": """You are a data scientist performing PATTERN DISCOVERY.

Your job is to:
- Identify higher-order patterns that are NOT simple pairwise correlations or basic trends
- Look for clusters, segments, groups of similar rows, and frequent combinations of values

You MUST:
- Focus on structural patterns such as clusters, segments, or recurring combinations.
- Clearly distinguish between well-supported patterns and speculative ones.

You MUST NOT:
- Re-describe simple correlations (those belong to relationship analysis).
- Do generic data profiling.
- Do anomaly detection or pure time-series trend analysis.

Your response MUST be valid JSON matching the schema provided.
Do NOT include markdown, backticks, or any text outside the JSON object.""",

            "column_documentation": """You are a senior data analyst creating a DATA DICTIONARY for database tables.

Your job is to infer:
- business_description (plain-language meaning of the column)
- technical_description (more exact meaning, if inferable)
- examples (2–3 sample values from the data)
- tags (PII, metric, identifier, category, currency, timestamp, enumeration, foreign_key, free_text, etc.)

You MUST base your answers only on:
- schema information
- sample rows
- column names and value patterns

You MUST NOT:
- invent domain-specific business rules unless strongly implied
- include markdown or any text outside the required JSON
- output anything except valid JSON

Always produce JSON matching the exact schema defined in the user template."""
        }
        
        return messages.get(analysis_type, "You are a data analyst.")
    
    @staticmethod
    def get_user_template(analysis_type: str) -> str:
        """Get user prompt template with placeholders."""
        templates = {
            "profiling": """We are profiling the following tables and columns:

{schema_summary}

Here is a sample of the data from the selected tables (truncated if necessary):

{sample_rows}

Using ONLY the information above, perform DATA PROFILING and return a JSON object with the following structure:

{{
  "executive_summary": "High-level summary of the dataset structure and basic characteristics.",
  "tables": [
    {{
      "table_name": "string",
      "row_count_estimate": "string or number if known, otherwise 'unknown'",
      "columns": [
        {{
          "column_name": "string",
          "data_type": "string (as observed, e.g., integer, float, text, datetime)",
          "distinct_values_estimate": "number or 'unknown'",
          "example_values": ["value1", "value2"],
          "missing_values_count": "number or 'unknown'",
          "missing_values_percent": "number or 'unknown'",
          "basic_statistics": {{
            "min": "number or 'n/a'",
            "max": "number or 'n/a'",
            "mean": "number or 'n/a'",
            "median": "number or 'n/a'",
            "std_dev": "number or 'n/a'"
          }},
          "distribution_summary": "Short text, e.g. 'approximately normal', 'right-skewed', 'categorical with few levels'."
        }}
      ]
    }}
  ]
}}

Return ONLY this JSON object and nothing else.""",

            "quality": """We are assessing DATA QUALITY for the following tables:

{schema_summary}

Here is a sample of the data (truncated if necessary):

{sample_rows}

Using ONLY the above, perform data quality checks and return a JSON object with the structure:

{{
  "executive_summary": "High-level summary of overall data quality, key issues, and overall risk.",
  "issues": [
    {{
      "table_name": "string",
      "column_name": "string or null if table-level issue",
      "issue_type": "one of: 'missing_data', 'duplicates', 'invalid_values', 'range_violation', 'format_violation', 'schema_mismatch', 'other'",
      "severity": "one of: 'low', 'medium', 'high'",
      "description": "Short description of the issue.",
      "evidence": "Concrete evidence from the sample or schema (e.g. '30% of rows are NULL', 'values outside expected range 0-1').",
      "suggested_checks": [
        "Specific follow-up checks the user could run to confirm this issue."
      ]
    }}
  ],
  "recommended_remediations": [
    "Concrete suggestions for fixing the highest impact issues."
  ]
}}

Return ONLY this JSON object and nothing else.""",

            "anomaly": """We are performing OUTLIER AND ANOMALY DETECTION on the following tables:

{schema_summary}

Here is a sample of the data (truncated if necessary):

{sample_rows}

Using ONLY the above, identify potential anomalies and return a JSON object with structure:

{{
  "executive_summary": "High-level overview of anomalies detected and their potential impact.",
  "anomalies": [
    {{
      "table_name": "string",
      "column_name": "string or null if multi-column or table-level",
      "anomaly_type": "one of: 'value_outlier', 'distribution_shift', 'sudden_spike', 'sudden_drop', 'category_surprise', 'other'",
      "description": "Short description of what is unusual.",
      "evidence": {{
        "approximate_frequency": "e.g. 'affects ~2% of rows in sample'",
        "approximate_magnitude": "e.g. 'values 5x larger than median'",
        "time_context": "If applicable, note any time-related pattern, else null"
      }},
      "severity": "one of: 'low', 'medium', 'high'",
      "possible_causes": [
        "Plausible causes stated cautiously"
      ],
      "recommended_next_analyses": [
        "Specific follow-up analyses to confirm or understand the anomaly"
      ]
    }}
  ]
}}

Return ONLY this JSON object and nothing else.""",

            "relationships": """We are performing RELATIONSHIP ANALYSIS on the following tables and columns:

{schema_summary}

Here is a sample of the data (truncated if necessary):

{sample_rows}

Using ONLY the above, identify notable relationships between variables and return a JSON object with structure:

{{
  "executive_summary": "High-level summary of the most important relationships observed.",
  "relationships": [
    {{
      "table_name": "string",
      "columns_involved": ["col1", "col2"],
      "relationship_type": "one of: 'positive_correlation', 'negative_correlation', 'non_linear', 'segment_difference', 'categorical_association', 'other'",
      "strength": "approximate qualitative rating: 'weak', 'moderate', 'strong', or 'unknown'",
      "description": "Plain-language description of the relationship.",
      "supporting_evidence": "Evidence from the sample or statistics, even approximate.",
      "caveats": [
        "Short caveats or limitations"
      ]
    }}
  ],
  "recommended_next_analyses": [
    "Concrete suggestions to further quantify or validate key relationships."
  ]
}}

Return ONLY this JSON object and nothing else.""",

            "trends": """We are performing TREND AND TIME-SERIES ANALYSIS on the following tables:

{schema_summary}

Here is a sample of the data, including any time-like columns (truncated if necessary):

{sample_rows}

Using ONLY the above, analyze time-based behavior and return a JSON object with structure:

{{
  "executive_summary": "High-level summary of overall trends, seasonality, and major temporal patterns.",
  "time_dimensions_considered": [
    {{
      "table_name": "string",
      "time_column": "string",
      "comment": "Short note about how this column is interpreted (e.g., 'daily timestamp')."
    }}
  ],
  "trends": [
    {{
      "table_name": "string",
      "time_column": "string",
      "target_columns": ["string"],
      "trend_type": "one of: 'increasing', 'decreasing', 'stable', 'mixed', 'unclear'",
      "description": "Plain-language description of the trend.",
      "approximate_period": "If applicable, describe any periodicity (e.g. 'weekly cycle'), else 'none' or 'unknown'."
    }}
  ],
  "change_points": [
    {{
      "table_name": "string",
      "time_column": "string",
      "target_column": "string",
      "approximate_position": "Text description like 'late in the period', 'middle', or 'not enough data'.",
      "description": "What changes and how (e.g. 'mean level shifts upward')."
    }}
  ],
  "seasonality_and_cycles": [
    {{
      "table_name": "string",
      "time_column": "string",
      "target_column": "string",
      "pattern_description": "Description of repeating patterns if any."
    }}
  ],
  "recommended_next_analyses": [
    "Specific suggestions for more formal time-series modeling or validation."
  ]
}}

If there are no usable time-like columns, return the same JSON structure with empty lists for 'trends', 'change_points', and 'seasonality_and_cycles' and explain this in 'executive_summary'.
Return ONLY this JSON object and nothing else.""",

            "patterns": """We are performing PATTERN DISCOVERY on the following tables:

{schema_summary}

Here is a sample of the data (truncated if necessary):

{sample_rows}

Using ONLY the above, identify higher-order patterns and return a JSON object with structure:

{{
  "executive_summary": "High-level summary of the most important structural patterns discovered.",
  "clusters_or_segments": [
    {{
      "table_name": "string",
      "segment_label": "string (e.g. 'high value, low frequency customers')",
      "defining_characteristics": [
        "Short bullet-style descriptors of how this segment differs from others."
      ],
      "approximate_prevalence": "Approximate share of rows in sample, e.g. 'about 20% of rows'.",
      "key_columns": ["string"]
    }}
  ],
  "frequent_patterns": [
    {{
      "table_name": "string",
      "description": "Description of the recurring combination (e.g. 'product A often purchased with product B').",
      "columns_involved": ["string"],
      "approximate_prevalence": "Textual approximation of how often this pattern occurs."
    }}
  ],
  "notable_subpopulations": [
    {{
      "table_name": "string",
      "filter_description": "Human-readable description of the subpopulation (e.g. 'orders with discount > 0.2').",
      "distinctive_properties": [
        "What makes this subpopulation behave differently."
      ]
    }}
  ],
  "recommended_next_analyses": [
    "Concrete suggestions to further investigate or operationalize the discovered patterns."
  ]
}}

Return ONLY this JSON object and nothing else.""",

            "column_documentation": """We are generating a data dictionary for these tables:

{{schema_summary}}

Here is a sample of the data:

{{sample_rows}}

Using ONLY this information, generate documentation for every column. 
Return a JSON list of entries, where each entry has this shape:

[
  {{
    "database_name": "<string>",
    "schema_name": "<string>",
    "table_name": "<string>",
    "column_name": "<string>",

    "business_name": "<short name or same as column if unknown>",
    "business_description": "<plain language meaning>",
    "technical_description": "<more precise meaning or null>",

    "data_type": "<observed data type>",
    "examples": ["value1", "value2"],
    "tags": ["string", "string"],

    "source": "llm_initial"
  }}
]

Return ONLY this JSON array and nothing else."""
        }
        
        return templates.get(analysis_type, "Analyze the data:\n\n{schema_summary}\n\n{sample_rows}")
    
    @staticmethod
    def build_analysis_prompt(
        analysis_type: str,
        table_data: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Build complete analysis prompt for a specific analysis type.
        
        Returns:
            Tuple of (system_message, user_message)
        """
        system_message = AnalysisPromptTemplates.get_system_message(analysis_type)
        user_template = AnalysisPromptTemplates.get_user_template(analysis_type)
        
        # Build schema summary
        schema_summary = AnalysisPromptTemplates._build_schema_summary(table_data)
        
        # Build sample rows
        sample_rows = AnalysisPromptTemplates._build_sample_rows(table_data)
        
        # Add context if provided
        if context:
            user_template = f"**Business Context**: {context}\n\n{user_template}"
        
        # Substitute placeholders
        user_message = user_template.format(
            schema_summary=schema_summary,
            sample_rows=sample_rows
        )
        
        return system_message, user_message
    
    @staticmethod
    def _build_schema_summary(table_data: List[Dict[str, Any]]) -> str:
        """Build schema summary from table data."""
        summaries = []
        
        for table in table_data:
            if "error" in table:
                summaries.append(
                    f"**{table['schema']}.{table['table']}**: Error - {table['error']}"
                )
                continue
            
            profile = table.get('profile', {})
            total_rows = profile.get('total_rows', 'Unknown')
            if isinstance(total_rows, (int, float)):
                total_rows_str = f"{int(total_rows):,}"
            else:
                total_rows_str = str(total_rows)
            
            summary = f"""**Table: {table['schema']}.{table['table']}**
- Total Rows: {total_rows_str}
- Column Count: {len(profile.get('column_profiles', {}))}

Columns:
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
                
                summary += col_info + "\n"
            
            summaries.append(summary)
        
        return "\n\n".join(summaries)
    
    @staticmethod
    def _build_sample_rows(table_data: List[Dict[str, Any]]) -> str:
        """Build sample rows display from table data."""
        samples = []
        
        for table in table_data:
            if "error" in table or not table.get('samples'):
                continue
            
            sample_rows = table['samples'][:10]  # First 10 rows
            
            if not sample_rows:
                continue
            
            sample_text = f"""**Table: {table['schema']}.{table['table']}** (showing {len(sample_rows)} of {table.get('sample_count', 'unknown')} sampled rows)

"""
            
            # Format as simple text representation
            for i, row in enumerate(sample_rows, 1):
                row_text = f"Row {i}: {row}\n"
                sample_text += row_text
            
            samples.append(sample_text)
        
        return "\n\n".join(samples) if samples else "No sample data available."

