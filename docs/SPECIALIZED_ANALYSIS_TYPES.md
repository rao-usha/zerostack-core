# Specialized Analysis Types

## Overview

The Data Analysis feature now supports 6 specialized analysis types, each with dedicated system prompts and structured JSON schemas. Each analysis type is focused on a specific aspect of data analysis, providing more targeted and actionable insights.

## Analysis Types

### 1. 📊 Data Profiling
**Purpose**: Describe structural and statistical properties of data

**What it does**:
- Column data types and cardinality
- Distinct value counts
- Basic statistics (min, max, mean, median, std_dev)
- Common values and distributions
- Missing value patterns

**What it does NOT do**:
- Anomaly detection
- Trend analysis
- Quality judgments (beyond describing nulls)
- Relationship inference

**JSON Schema**:
```json
{
  "executive_summary": "High-level summary of dataset structure",
  "tables": [
    {
      "table_name": "string",
      "row_count_estimate": "number or 'unknown'",
      "columns": [
        {
          "column_name": "string",
          "data_type": "string",
          "distinct_values_estimate": "number or 'unknown'",
          "example_values": ["value1", "value2"],
          "missing_values_count": "number or 'unknown'",
          "missing_values_percent": "number or 'unknown'",
          "basic_statistics": {
            "min": "number or 'n/a'",
            "max": "number or 'n/a'",
            "mean": "number or 'n/a'",
            "median": "number or 'n/a'",
            "std_dev": "number or 'n/a'"
          },
          "distribution_summary": "text description"
        }
      ]
    }
  ]
}
```

### 2. 🛡️ Data Quality Checks
**Purpose**: Identify data integrity issues

**What it does**:
- Missing data patterns
- Duplicate detection
- Invalid or inconsistent values
- Range violations
- Format violations
- Schema mismatches

**What it does NOT do**:
- Statistical anomaly detection
- Business meaning inference

**JSON Schema**:
```json
{
  "executive_summary": "Overall quality, key issues, and risk",
  "issues": [
    {
      "table_name": "string",
      "column_name": "string or null",
      "issue_type": "missing_data | duplicates | invalid_values | range_violation | format_violation | schema_mismatch | other",
      "severity": "low | medium | high",
      "description": "Short description",
      "evidence": "Concrete evidence from sample",
      "suggested_checks": ["Follow-up checks"]
    }
  ],
  "recommended_remediations": ["Concrete fix suggestions"]
}
```

### 3. ⚠️ Outlier & Anomaly Detection
**Purpose**: Identify unusual or extreme values

**What it does**:
- Unusual or extreme values
- Distribution shifts
- Surprising patterns
- Temporal anomalies (if time columns present)

**What it does NOT do**:
- General profiling
- Quality checks (unless supporting anomaly)

**JSON Schema**:
```json
{
  "executive_summary": "Overview of anomalies and their impact",
  "anomalies": [
    {
      "table_name": "string",
      "column_name": "string or null",
      "anomaly_type": "value_outlier | distribution_shift | sudden_spike | sudden_drop | category_surprise | other",
      "description": "What is unusual",
      "evidence": {
        "approximate_frequency": "e.g. 'affects ~2% of rows'",
        "approximate_magnitude": "e.g. '5x larger than median'",
        "time_context": "time-related pattern or null"
      },
      "severity": "low | medium | high",
      "possible_causes": ["Plausible causes"],
      "recommended_next_analyses": ["Follow-up analyses"]
    }
  ]
}
```

### 4. 🔗 Relationship Analysis
**Purpose**: Identify correlations and associations between columns

**What it does**:
- Pairwise and small-set relationships
- Associations and correlations
- Clear directional tendencies

**What it does NOT do**:
- Anomaly detection
- Trend analysis
- High-order pattern discovery (that's a separate type)

**JSON Schema**:
```json
{
  "executive_summary": "Most important relationships observed",
  "relationships": [
    {
      "table_name": "string",
      "columns_involved": ["col1", "col2"],
      "relationship_type": "positive_correlation | negative_correlation | non_linear | segment_difference | categorical_association | other",
      "strength": "weak | moderate | strong | unknown",
      "description": "Plain-language description",
      "supporting_evidence": "Evidence from sample",
      "caveats": ["Short caveats"]
    }
  ],
  "recommended_next_analyses": ["Suggestions to quantify relationships"]
}
```

### 5. 📈 Trend & Time-Series Analysis
**Purpose**: Analyze temporal behavior and patterns

**What it does**:
- Time-ordered column analysis
- Trends, seasonality, cycles
- Change points

**What it does NOT do**:
- Anomaly detection (beyond trend-related changes)
- General profiling or correlations

**Special behavior**: If no time-like columns are available, returns empty lists with explanation.

**JSON Schema**:
```json
{
  "executive_summary": "Overall trends, seasonality, and temporal patterns",
  "time_dimensions_considered": [
    {
      "table_name": "string",
      "time_column": "string",
      "comment": "How this column is interpreted"
    }
  ],
  "trends": [
    {
      "table_name": "string",
      "time_column": "string",
      "target_columns": ["string"],
      "trend_type": "increasing | decreasing | stable | mixed | unclear",
      "description": "Plain-language description",
      "approximate_period": "periodicity or 'none'"
    }
  ],
  "change_points": [
    {
      "table_name": "string",
      "time_column": "string",
      "target_column": "string",
      "approximate_position": "text description",
      "description": "What changes and how"
    }
  ],
  "seasonality_and_cycles": [
    {
      "table_name": "string",
      "time_column": "string",
      "target_column": "string",
      "pattern_description": "Repeating patterns"
    }
  ],
  "recommended_next_analyses": ["Time-series modeling suggestions"]
}
```

### 6. 🧠 Pattern Discovery
**Purpose**: Identify higher-order structural patterns

**What it does**:
- Clusters and segments
- Groups of similar rows
- Frequent value combinations
- Notable subpopulations

**What it does NOT do**:
- Simple pairwise correlations (use Relationship Analysis)
- Generic profiling
- Anomaly or trend detection

**JSON Schema**:
```json
{
  "executive_summary": "Most important structural patterns",
  "clusters_or_segments": [
    {
      "table_name": "string",
      "segment_label": "descriptive label",
      "defining_characteristics": ["Bullet descriptors"],
      "approximate_prevalence": "e.g. 'about 20% of rows'",
      "key_columns": ["string"]
    }
  ],
  "frequent_patterns": [
    {
      "table_name": "string",
      "description": "Recurring combination description",
      "columns_involved": ["string"],
      "approximate_prevalence": "How often this occurs"
    }
  ],
  "notable_subpopulations": [
    {
      "table_name": "string",
      "filter_description": "Subpopulation description",
      "distinctive_properties": ["What makes it different"]
    }
  ],
  "recommended_next_analyses": ["Pattern operationalization suggestions"]
}
```

## Implementation Architecture

### Backend Components

1. **`analysis_prompts.py`**: Central repository for all prompts
   - System messages with role and constraints
   - User templates with `{schema_summary}` and `{sample_rows}` placeholders
   - JSON schema specifications
   - Helper methods for building prompts

2. **`job_service.py`**: Analysis execution
   - Runs each analysis type separately
   - Combines results from multiple analysis types
   - Robust JSON parsing with fallback handling

3. **`models.py`**: Data validation
   - Updated valid analysis types
   - Changed defaults to `['profiling', 'quality']`

### Frontend Components

1. **`DataAnalysis.tsx`**: Main UI
   - Updated analysis type options with icons and descriptions
   - Changed default selection to `['profiling', 'quality']`
   - Display logic for structured results

## Key Features

### Separation of Concerns
Each analysis type has a clear, focused purpose. This prevents:
- Mixed responsibilities
- Conflicting interpretations
- Overly generic results

### Structured Output
Every analysis type returns a specific JSON schema:
- Predictable structure for UI rendering
- Easy to parse and store
- Consistent format across providers

### Flexibility
Users can run:
- Single analysis types for focused insights
- Multiple types for comprehensive analysis
- Different combinations for different use cases

### MCP Integration
All analysis types use MCP tools for:
- Dynamic schema discovery
- Safe data sampling
- Column profiling and statistics

## Usage Examples

### Example 1: Quick Data Check
```
Analysis Types: ['profiling', 'quality']
Purpose: Understand data structure and identify obvious issues
Time: ~30-60 seconds
```

### Example 2: Deep Anomaly Investigation
```
Analysis Types: ['profiling', 'anomaly', 'quality']
Purpose: Profile data, then find quality issues and statistical anomalies
Time: ~60-90 seconds
```

### Example 3: Comprehensive Analysis
```
Analysis Types: ['profiling', 'quality', 'anomaly', 'relationships', 'trends', 'patterns']
Purpose: Full data understanding across all dimensions
Time: ~3-5 minutes
```

### Example 4: Time-Series Focus
```
Analysis Types: ['profiling', 'trends']
Purpose: Understand temporal behavior
Time: ~30-60 seconds
```

## Best Practices

### When to Use Each Type

**Always start with**: `profiling` + `quality`
- Establishes baseline understanding
- Identifies critical issues early

**Add `anomaly`** when:
- Data has unexpected characteristics
- Looking for data errors or surprises

**Add `relationships`** when:
- Need to understand correlations
- Looking for predictive features
- Planning modeling work

**Add `trends`** when:
- Time-series data is present
- Seasonality is suspected
- Change detection is needed

**Add `patterns`** when:
- Looking for customer/user segments
- Need to understand subpopulations
- Clustering insights are valuable

### Model Selection

**Recommended models**:
- **GPT-4o**: Best balance of speed and quality
- **GPT-4 Turbo**: Highest quality, slower
- **Claude 3.5 Sonnet**: Excellent reasoning, good for complex patterns
- **Gemini Pro**: Fast, good for profiling

**Avoid**:
- GPT-3.5: May struggle with JSON schema compliance
- Smaller models: May miss subtle patterns

### Performance Optimization

**For faster results**:
- Select fewer analysis types
- Use smaller sample sizes (configure in MCP)
- Use faster models (GPT-4o Mini, Gemini Flash)

**For better quality**:
- Select all relevant analysis types
- Use GPT-4 Turbo or Claude 3.5 Sonnet
- Provide business context

## Future Enhancements

### Potential Additions
1. **Custom Analysis Types**: User-defined prompts and schemas
2. **Analysis Pipelines**: Chain analyses with dependencies
3. **Scheduled Analysis**: Recurring analysis jobs
4. **Diff Analysis**: Compare analysis results over time
5. **Export Options**: PDF reports, PowerPoint slides

### Integration Opportunities
1. **Alerting**: Notify on high-severity issues
2. **Auto-Remediation**: Suggest SQL fixes for quality issues
3. **Dashboards**: Visualize trends and patterns
4. **ML Integration**: Feed insights into model training

## Migration from Old Types

### Old → New Mapping
- `eda` → `profiling`
- `correlation` → `relationships`
- `quality` → `quality` (same)
- `anomaly` → `anomaly` (same)
- `trends` → `trends` (same)
- `patterns` → `patterns` (same)

### Breaking Changes
- Default analysis types changed from `['eda', 'anomaly']` to `['profiling', 'quality']`
- JSON response structure is different for each type
- System prompts are more restrictive

### Backward Compatibility
- Old analysis type names are no longer accepted
- Existing jobs with old types will need to be re-run
- Frontend dropdowns updated to show new types only

