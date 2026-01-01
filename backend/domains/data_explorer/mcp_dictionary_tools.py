"""
MCP Data Dictionary Tools - Organized by 5 Use Cases

This module defines the MCP tool specifications for the Data Dictionary,
organized around the 5 core use cases:

1. DISCOVERY - Find and explore data assets
2. DOCUMENTATION - Read existing business definitions
3. CURATION - View suggested relationships and approval status
4. ANALYSIS - Query trust tiers, quality, fitness for use
5. UNDERSTANDING - Explain grain, semantics, guarantees

All tools are READ-ONLY to avoid adding entropy to the system.
"""

from typing import List, Dict, Any, Optional, TypedDict


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class ToolSchema(TypedDict):
    """Schema for an MCP tool definition."""
    name: str
    description: str
    use_case: str
    input_schema: dict
    output_description: str
    example_prompts: List[str]


# =============================================================================
# USE CASE 1: DISCOVERY
# Find and explore data assets
# =============================================================================

TOOL_DISCOVER_ASSETS = {
    "name": "discover_assets",
    "description": (
        "Discover data assets (tables/views) in the data dictionary. "
        "Use this as your starting point to find what data is available. "
        "Supports filtering by schema, business domain, trust tier, and search terms. "
        "Returns business metadata, ownership, and trust information."
    ),
    "use_case": "discovery",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "search": {
                "type": "string",
                "description": "Search term to find in table names, business names, or descriptions"
            },
            "schema": {
                "type": "string",
                "description": "Filter by schema name (e.g., 'public', 'sales')"
            },
            "business_domain": {
                "type": "string",
                "description": "Filter by business domain (e.g., 'Sales', 'Finance')"
            },
            "trust_tier": {
                "type": "string",
                "enum": ["certified", "trusted", "experimental", "deprecated"],
                "description": "Filter by trust level"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results (default: 25)",
                "default": 25
            }
        },
        "required": []
    },
    "output_description": (
        "List of assets with: schema_name, table_name, business_name, "
        "business_definition (truncated), business_domain, owner, trust_tier, "
        "trust_score, tags, row_count_estimate. Includes total count."
    ),
    "example_prompts": [
        "What tables do we have?",
        "Find tables related to customers",
        "Show me all certified data",
        "What's in the sales schema?",
        "List deprecated tables"
    ]
}


TOOL_DISCOVER_FIELDS = {
    "name": "discover_fields",
    "description": (
        "Discover columns/fields in a specific table. "
        "Returns all columns with their data types, semantic roles, and business names. "
        "Use this to understand the structure of a table."
    ),
    "use_case": "discovery",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "List of fields with: column_name, business_name, data_type, "
        "is_nullable, entity_role (primary_identifier, foreign_key, measure, "
        "dimension, etc.), ordinal_position."
    ),
    "example_prompts": [
        "What columns does the orders table have?",
        "Show me the fields in customers",
        "What's the structure of daily_sales?"
    ]
}


TOOL_DISCOVER_RELATIONSHIPS = {
    "name": "discover_relationships",
    "description": (
        "Discover relationships between tables. "
        "Shows how tables connect via foreign keys and semantic relationships. "
        "Use this to understand the data model and plan joins."
    ),
    "use_case": "discovery",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name (optional - omit for all schemas)"
            },
            "table": {
                "type": "string",
                "description": "Get relationships for specific table (optional)"
            },
            "status": {
                "type": "string",
                "enum": ["suggested", "approved", "all"],
                "description": "Filter by approval status (default: approved)",
                "default": "approved"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results (default: 50)",
                "default": 50
            }
        },
        "required": []
    },
    "output_description": (
        "List of relationships with: source (schema.table.column), "
        "target (schema.table.column), relationship_type, cardinality, "
        "confidence_score, status."
    ),
    "example_prompts": [
        "What tables are related to orders?",
        "Show me all foreign key relationships",
        "How does customers connect to other tables?"
    ]
}


# =============================================================================
# USE CASE 2: DOCUMENTATION
# Read existing business definitions and metadata
# =============================================================================

TOOL_GET_ASSET_DOCUMENTATION = {
    "name": "get_asset_documentation",
    "description": (
        "Get the full documentation for a data asset (table or view). "
        "Returns all business metadata including definition, domain, ownership, "
        "grain/row meaning, and known issues. "
        "Use this to understand what a table represents in business terms."
    ),
    "use_case": "documentation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Full asset documentation: business_name, business_definition, "
        "business_domain, grain, row_meaning, owner, steward, tags, "
        "known_issues, issue_tags, created_at, updated_at."
    ),
    "example_prompts": [
        "What is the orders table?",
        "Tell me about the customers table",
        "What does daily_sales represent?",
        "Who owns the transactions table?"
    ]
}


TOOL_GET_FIELD_DOCUMENTATION = {
    "name": "get_field_documentation",
    "description": (
        "Get the full documentation for a specific column/field. "
        "Returns business name, definition, semantic role, and any known issues. "
        "Use this to understand what a column means and how to use it."
    ),
    "use_case": "documentation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "column": {
                "type": "string",
                "description": "Column name"
            }
        },
        "required": ["schema", "table", "column"]
    },
    "output_description": (
        "Field documentation: column_name, business_name, business_definition, "
        "data_type, is_nullable, entity_role, tags, known_issues."
    ),
    "example_prompts": [
        "What does customer_id mean?",
        "Explain the status column in orders",
        "What is the order_date field?"
    ]
}


TOOL_GET_DOCUMENTATION_SUMMARY = {
    "name": "get_documentation_summary",
    "description": (
        "Get a documentation summary for multiple assets or a schema. "
        "Returns brief documentation for each asset to understand coverage. "
        "Use this to see what's documented and what needs attention."
    ),
    "use_case": "documentation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name (optional)"
            },
            "include_undocumented": {
                "type": "boolean",
                "description": "Include assets without documentation (default: true)",
                "default": True
            }
        },
        "required": []
    },
    "output_description": (
        "Summary with: assets with documentation, assets without documentation, "
        "documentation coverage percentage, list of each asset with "
        "has_definition, has_owner, has_grain flags."
    ),
    "example_prompts": [
        "What's documented in the sales schema?",
        "Show documentation coverage",
        "What tables need documentation?"
    ]
}


# =============================================================================
# USE CASE 3: CURATION
# View suggested relationships and approval status
# =============================================================================

TOOL_GET_PENDING_RELATIONSHIPS = {
    "name": "get_pending_relationships",
    "description": (
        "Get relationships that are pending review (suggested but not approved). "
        "Shows AI-discovered relationships waiting for human approval. "
        "Use this to see what relationships need review."
    ),
    "use_case": "curation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Filter by schema"
            },
            "min_confidence": {
                "type": "number",
                "description": "Minimum confidence score (0.0-1.0)",
                "default": 0.0
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results (default: 50)",
                "default": 50
            }
        },
        "required": []
    },
    "output_description": (
        "List of pending relationships with: source, target, relationship_type, "
        "cardinality, confidence_score, suggested_join_sql, created_at."
    ),
    "example_prompts": [
        "What relationships need approval?",
        "Show pending suggestions",
        "What did the AI discover?"
    ]
}


TOOL_GET_RELATIONSHIP_DETAILS = {
    "name": "get_relationship_details",
    "description": (
        "Get full details about a specific relationship including stats. "
        "Shows match rate, null rates, uniqueness, and suggested SQL. "
        "Use this to evaluate if a relationship should be approved."
    ),
    "use_case": "curation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "source_schema": {
                "type": "string",
                "description": "Source schema"
            },
            "source_table": {
                "type": "string",
                "description": "Source table"
            },
            "source_column": {
                "type": "string",
                "description": "Source column"
            },
            "target_schema": {
                "type": "string",
                "description": "Target schema"
            },
            "target_table": {
                "type": "string",
                "description": "Target table"
            },
            "target_column": {
                "type": "string",
                "description": "Target column"
            }
        },
        "required": ["source_schema", "source_table", "source_column", 
                     "target_schema", "target_table", "target_column"]
    },
    "output_description": (
        "Full relationship details: type, cardinality, status, confidence_score, "
        "match_rate_sample, left_null_rate, right_unique, suggested_join_sql, "
        "grain_compatibility, notes, created_at, created_by."
    ),
    "example_prompts": [
        "Tell me about the relationship between orders.customer_id and customers.id",
        "What are the stats for this join?"
    ]
}


TOOL_GET_CURATION_STATUS = {
    "name": "get_curation_status",
    "description": (
        "Get overall curation status and statistics for the data dictionary. "
        "Shows counts of approved, pending, rejected relationships and documentation coverage. "
        "Use this to understand how well-curated the data dictionary is."
    ),
    "use_case": "curation",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Filter by schema (optional)"
            }
        },
        "required": []
    },
    "output_description": (
        "Curation statistics: total_assets, documented_assets, "
        "total_relationships, approved_relationships, pending_relationships, "
        "rejected_relationships, avg_confidence_score, curation_percentage."
    ),
    "example_prompts": [
        "How curated is our data dictionary?",
        "What's the curation status?",
        "How many relationships need review?"
    ]
}


# =============================================================================
# USE CASE 4: ANALYSIS
# Query trust tiers, quality, fitness for use
# =============================================================================

TOOL_CHECK_DATA_QUALITY = {
    "name": "check_data_quality",
    "description": (
        "Check the data quality and trust information for a table or column. "
        "Returns trust tier, trust score, approval status, and known issues. "
        "Use this to assess if data is fit for your intended use."
    ),
    "use_case": "analysis",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "column": {
                "type": "string",
                "description": "Specific column (optional)"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Quality information: trust_tier, trust_score (0-100), "
        "approved_for_reporting, approved_for_ml, known_issues, issue_tags, "
        "null_fraction (if column), validation_state."
    ),
    "example_prompts": [
        "Is the orders table trustworthy?",
        "Can I use customers for ML?",
        "What are the known issues with sales data?",
        "Is revenue approved for reporting?"
    ]
}


TOOL_GET_COLUMN_STATISTICS = {
    "name": "get_column_statistics",
    "description": (
        "Get statistical profile for columns in a table. "
        "Returns null rates, distinct counts, distributions, and type-specific stats. "
        "Use this to understand actual data characteristics."
    ),
    "use_case": "analysis",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            },
            "column": {
                "type": "string",
                "description": "Specific column (optional - returns all if omitted)"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Column statistics: null_count, null_fraction, distinct_count, "
        "uniqueness_fraction. For numeric: min, max, avg, stddev, median. "
        "For categorical: top_values with counts. For strings: length stats. "
        "For dates: earliest, latest."
    ),
    "example_prompts": [
        "How many nulls in the email column?",
        "What's the distribution of status?",
        "Show me stats for the orders table",
        "What are the min/max values for price?"
    ]
}


TOOL_FIND_TRUSTED_DATA = {
    "name": "find_trusted_data",
    "description": (
        "Find data assets that meet specific trust and quality criteria. "
        "Use this to find reliable data for reporting, ML, or analysis."
    ),
    "use_case": "analysis",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "use_case": {
                "type": "string",
                "enum": ["reporting", "ml", "analysis"],
                "description": "Intended use case"
            },
            "min_trust_tier": {
                "type": "string",
                "enum": ["certified", "trusted", "experimental"],
                "description": "Minimum trust tier (default: trusted)",
                "default": "trusted"
            },
            "business_domain": {
                "type": "string",
                "description": "Filter by business domain"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results (default: 25)",
                "default": 25
            }
        },
        "required": ["use_case"]
    },
    "output_description": (
        "List of qualifying assets sorted by trust_score: table_name, "
        "schema_name, business_name, trust_tier, trust_score, owner."
    ),
    "example_prompts": [
        "What data can I use for a board report?",
        "Find certified tables for ML",
        "Which sales data is trusted?",
        "What's the most reliable customer data?"
    ]
}


# =============================================================================
# USE CASE 5: UNDERSTANDING
# Explain grain, semantics, and guarantees
# =============================================================================

TOOL_EXPLAIN_TABLE = {
    "name": "explain_table",
    "description": (
        "Get a comprehensive explanation of a table for conversation context. "
        "Returns everything needed to understand and discuss a table: "
        "what it is, what one row represents, who uses it, and how to use it correctly. "
        "This is the primary tool for understanding an asset in depth."
    ),
    "use_case": "understanding",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Comprehensive explanation including: what the table is (business_name, "
        "business_definition), grain (what one row represents), ownership, "
        "trust information, key columns with their roles, relationships to "
        "other tables, and usage guidance."
    ),
    "example_prompts": [
        "Explain the orders table",
        "Tell me everything about customers",
        "I need to understand daily_sales",
        "Help me work with the transactions table"
    ]
}


TOOL_EXPLAIN_GRAIN = {
    "name": "explain_grain",
    "description": (
        "Explain what one row represents in a table (the grain). "
        "Understanding grain is critical for correct aggregations and joins. "
        "Returns the entity, primary key, time grain, and aggregation guidance."
    ),
    "use_case": "understanding",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Grain explanation: entity (what the table is about), "
        "row_meaning (what one row represents), primary_key (unique columns), "
        "natural_key, time_grain (if applicable), aggregation_guidance."
    ),
    "example_prompts": [
        "What does one row in orders represent?",
        "What's the grain of daily_sales?",
        "How should I aggregate this table?",
        "What's the primary key?"
    ]
}


TOOL_EXPLAIN_SEMANTICS = {
    "name": "explain_semantics",
    "description": (
        "Get semantic information about a table including decision context, "
        "guarantees, and validation state. Use this to understand how data "
        "should be used and what you can rely on."
    ),
    "use_case": "understanding",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "schema": {
                "type": "string",
                "description": "Schema name"
            },
            "table": {
                "type": "string",
                "description": "Table name"
            }
        },
        "required": ["schema", "table"]
    },
    "output_description": (
        "Semantic information: decision_context (who uses it, for what decisions), "
        "semantic_guarantees (invariants, freshness, aggregation rules, failure modes), "
        "validation_state (confidence, sources, last validated)."
    ),
    "example_prompts": [
        "Who uses the revenue table?",
        "What can I rely on with this data?",
        "How fresh is the sales data?",
        "What are the guarantees for this table?"
    ]
}


TOOL_EXPLAIN_JOIN = {
    "name": "explain_join",
    "description": (
        "Explain how to join two tables correctly and safely. "
        "Analyzes grain compatibility, suggests join type, and warns about issues. "
        "Use this before writing queries that join tables."
    ),
    "use_case": "understanding",
    "input_schema": {
        "type": "object",
        "properties": {
            "connection_id": {
                "type": "string",
                "description": "Database connection ID",
                "default": "default"
            },
            "left_schema": {
                "type": "string",
                "description": "Left table schema"
            },
            "left_table": {
                "type": "string",
                "description": "Left table name"
            },
            "right_schema": {
                "type": "string",
                "description": "Right table schema"
            },
            "right_table": {
                "type": "string",
                "description": "Right table name"
            }
        },
        "required": ["left_schema", "left_table", "right_schema", "right_table"]
    },
    "output_description": (
        "Join explanation: can_join, join_columns, recommended_join_type, "
        "cardinality, grain_compatible, warnings (fanout, nulls), "
        "safe_aggregations, example_sql."
    ),
    "example_prompts": [
        "How do I join orders and customers?",
        "Can I safely join these tables?",
        "What's the right way to connect products to order_items?",
        "Will this join cause fanout?"
    ]
}


# =============================================================================
# TOOL REGISTRY
# =============================================================================

# All tools organized by use case
TOOLS_BY_USE_CASE = {
    "discovery": [
        TOOL_DISCOVER_ASSETS,
        TOOL_DISCOVER_FIELDS,
        TOOL_DISCOVER_RELATIONSHIPS,
    ],
    "documentation": [
        TOOL_GET_ASSET_DOCUMENTATION,
        TOOL_GET_FIELD_DOCUMENTATION,
        TOOL_GET_DOCUMENTATION_SUMMARY,
    ],
    "curation": [
        TOOL_GET_PENDING_RELATIONSHIPS,
        TOOL_GET_RELATIONSHIP_DETAILS,
        TOOL_GET_CURATION_STATUS,
    ],
    "analysis": [
        TOOL_CHECK_DATA_QUALITY,
        TOOL_GET_COLUMN_STATISTICS,
        TOOL_FIND_TRUSTED_DATA,
    ],
    "understanding": [
        TOOL_EXPLAIN_TABLE,
        TOOL_EXPLAIN_GRAIN,
        TOOL_EXPLAIN_SEMANTICS,
        TOOL_EXPLAIN_JOIN,
    ],
}

# Flat list of all tools
ALL_TOOLS: List[dict] = []
for use_case, tools in TOOLS_BY_USE_CASE.items():
    ALL_TOOLS.extend(tools)


def get_tool_by_name(name: str) -> Optional[dict]:
    """Get a tool definition by name."""
    for tool in ALL_TOOLS:
        if tool["name"] == name:
            return tool
    return None


def get_tools_for_use_case(use_case: str) -> List[dict]:
    """Get all tools for a use case."""
    return TOOLS_BY_USE_CASE.get(use_case, [])


def get_all_tool_names() -> List[str]:
    """Get list of all tool names."""
    return [tool["name"] for tool in ALL_TOOLS]


# =============================================================================
# INTERACTION MODES
# =============================================================================

INTERACTION_MODES = {
    "explorer": {
        "name": "Explorer",
        "description": "General discovery and exploration of data assets",
        "default_use_cases": ["discovery", "documentation", "understanding"],
        "personality": "curious, thorough, educational"
    },
    "analyst": {
        "name": "Analyst", 
        "description": "Help with queries, joins, and data analysis",
        "default_use_cases": ["discovery", "analysis", "understanding"],
        "personality": "precise, cautious about data quality"
    },
    "steward": {
        "name": "Steward",
        "description": "Review documentation and curation status",
        "default_use_cases": ["documentation", "curation", "analysis"],
        "personality": "governance-focused, thorough"
    },
    "quick": {
        "name": "Quick",
        "description": "Fast answers with minimal context",
        "default_use_cases": ["discovery", "documentation"],
        "personality": "concise, direct"
    }
}
