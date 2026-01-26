"""
Chat service layer.

Handles chat conversation management, message persistence, LLM orchestration,
and integration with MCP/Data Explorer tools and Data Dictionary tools.
"""

import json
import logging
from typing import AsyncIterator, List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlmodel import Session, select, desc
from sqlalchemy import func

from .models import (
    ChatConversation, ChatMessage,
    ConversationCreate, MessageCreate,
    ConversationResponse, MessageResponse,
    ConversationWithMessages
)
from ..data_explorer.service import DataExplorerService
from ..data_explorer import dictionary_enhanced_service as dict_service
from ..data_explorer import dictionary_service as original_dict_service
from ..data_explorer.db_models import DataDictionaryEntry
from llm.providers import get_provider

logger = logging.getLogger(__name__)


# Define Data Explorer tools for LLM function calling
DATA_EXPLORER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_connections",
            "description": "List all available database connections. Use this first to discover which databases you can explore.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_schemas",
            "description": "List all schemas in a database (excluding system schemas). Returns schema names with table counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID (default: 'default')",
                        "default": "default"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "List all tables and views in a schema. Returns table names, types (table/view), and row estimates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {
                        "type": "string",
                        "description": "Database connection ID",
                        "default": "default"
                    },
                    "schema": {
                        "type": "string",
                        "description": "Schema name",
                        "default": "public"
                    }
                },
                "required": ["schema"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_table_info",
            "description": "Get detailed column metadata for a specific table. Use before querying to understand structure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sample_rows",
            "description": "Sample rows from a table with pagination. Use to preview actual data.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "limit": {"type": "integer", "description": "Number of rows (default: 50, max: 500)", "default": 50},
                    "offset": {"type": "integer", "description": "Offset (default: 0)", "default": 0}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "profile_table",
            "description": "Generate comprehensive statistical profile for a table including null counts, distinct values, min/max/avg for numeric columns, and top values for categorical columns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "max_distinct": {"type": "integer", "description": "Max distinct values for categorical columns", "default": 50}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_query",
            "description": "Execute a custom SQL query (SELECT only, read-only). Query timeout is 30 seconds, max 1000 rows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "sql": {"type": "string", "description": "SQL query to execute (SELECT only)"},
                    "page": {"type": "integer", "description": "Page number", "default": 1},
                    "page_size": {"type": "integer", "description": "Rows per page (max: 1000)", "default": 100}
                },
                "required": ["sql"]
            }
        }
    },
    # EXPORT TOOLS
    {
        "type": "function",
        "function": {
            "name": "export_query_to_s3",
            "description": "Export SQL query results to S3 as parquet or CSV. Use this to save query results for later use, sharing, or analysis in other tools.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL query to export (SELECT only)"},
                    "name": {"type": "string", "description": "Name for the export (used in filename)"},
                    "format": {"type": "string", "enum": ["parquet", "csv"], "description": "Output format", "default": "parquet"},
                    "connection_id": {"type": "string", "default": "default"},
                    "description": {"type": "string", "description": "Optional description of what this export contains"},
                    "compression": {"type": "string", "enum": ["snappy", "gzip", "none"], "description": "Compression type", "default": "snappy"}
                },
                "required": ["sql", "name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "export_table_to_s3",
            "description": "Export an entire table to S3 as parquet or CSV. Optionally limit rows for large tables.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "name": {"type": "string", "description": "Name for the export"},
                    "format": {"type": "string", "enum": ["parquet", "csv"], "description": "Output format", "default": "parquet"},
                    "connection_id": {"type": "string", "default": "default"},
                    "limit": {"type": "integer", "description": "Max rows to export (omit for all rows)"},
                    "compression": {"type": "string", "enum": ["snappy", "gzip", "none"], "description": "Compression type", "default": "snappy"}
                },
                "required": ["schema", "table", "name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_exports",
            "description": "List all data exports with their status, size, and download availability.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "running", "completed", "failed"], "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Max results", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_export_status",
            "description": "Get detailed status and metadata for a specific export by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "export_id": {"type": "string", "description": "Export ID (UUID)"}
                },
                "required": ["export_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_export_download_url",
            "description": "Get a temporary download URL for a completed export. URL expires in 1 hour.",
            "parameters": {
                "type": "object",
                "properties": {
                    "export_id": {"type": "string", "description": "Export ID (UUID)"}
                },
                "required": ["export_id"]
            }
        }
    },
    # MATERIALIZED VIEW TOOLS
    {
        "type": "function",
        "function": {
            "name": "create_materialized_view",
            "description": "Create a materialized view from a SQL query. Materialized views store query results physically for faster access. Use for frequently-run expensive queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for the materialized view (letters, numbers, underscores only)"},
                    "source_query": {"type": "string", "description": "SELECT query defining the view contents"},
                    "schema_name": {"type": "string", "description": "Schema to create view in", "default": "public", "enum": ["public", "analytics", "reports", "views"]},
                    "description": {"type": "string", "description": "Description of what this view contains"},
                    "connection_id": {"type": "string", "default": "default"},
                    "with_data": {"type": "boolean", "description": "Populate view immediately (true) or create empty (false)", "default": True}
                },
                "required": ["name", "source_query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "refresh_materialized_view",
            "description": "Refresh a materialized view to update its data from the source query. Use when underlying data has changed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "view_id": {"type": "string", "description": "View ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "View name (alternative to view_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"},
                    "concurrently": {"type": "boolean", "description": "Refresh without locking reads (requires unique index)", "default": False}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "drop_materialized_view",
            "description": "Drop (delete) a materialized view. This cannot be undone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "view_id": {"type": "string", "description": "View ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "View name (alternative to view_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_materialized_views",
            "description": "List all managed materialized views with their status, size, and last refresh time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema_name": {"type": "string", "description": "Filter by schema"},
                    "status": {"type": "string", "enum": ["active", "refreshing", "failed", "creating"], "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Max results", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_materialized_view_info",
            "description": "Get detailed information about a specific materialized view including source query, refresh history, and errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "view_id": {"type": "string", "description": "View ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "View name (alternative to view_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"}
                },
                "required": []
            }
        }
    },
    # STORED PROCEDURE TOOLS
    {
        "type": "function",
        "function": {
            "name": "create_stored_procedure",
            "description": "Create a stored procedure (function) in the database. Use for reusable business logic, data transformations, or complex operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name for the procedure (letters, numbers, underscores only)"},
                    "source_code": {"type": "string", "description": "Function body (the code inside the function, not CREATE FUNCTION wrapper)"},
                    "schema_name": {"type": "string", "description": "Schema to create procedure in", "default": "public", "enum": ["public", "analytics", "reports", "procedures"]},
                    "description": {"type": "string", "description": "Description of what this procedure does"},
                    "language": {"type": "string", "description": "Procedure language", "default": "plpgsql", "enum": ["plpgsql", "sql"]},
                    "parameters": {
                        "type": "array",
                        "description": "Function parameters as [{name, type, default?, mode?}]",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "default": {"type": "string"},
                                "mode": {"type": "string", "enum": ["IN", "OUT", "INOUT"]}
                            }
                        }
                    },
                    "return_type": {"type": "string", "description": "Return type (omit for void)"},
                    "returns_set": {"type": "boolean", "description": "Whether function returns multiple rows", "default": False},
                    "volatility": {"type": "string", "description": "Function volatility", "default": "volatile", "enum": ["volatile", "stable", "immutable"]},
                    "connection_id": {"type": "string", "default": "default"}
                },
                "required": ["name", "source_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_stored_procedure",
            "description": "Execute a stored procedure with optional arguments. Returns the result set.",
            "parameters": {
                "type": "object",
                "properties": {
                    "procedure_id": {"type": "string", "description": "Procedure ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "Procedure name (alternative to procedure_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"},
                    "arguments": {
                        "type": "object",
                        "description": "Named arguments to pass to the procedure",
                        "additionalProperties": True
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "drop_stored_procedure",
            "description": "Drop (delete) a stored procedure. This cannot be undone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "procedure_id": {"type": "string", "description": "Procedure ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "Procedure name (alternative to procedure_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_stored_procedures",
            "description": "List all managed stored procedures with their status and execution stats.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema_name": {"type": "string", "description": "Filter by schema"},
                    "language": {"type": "string", "description": "Filter by language", "enum": ["plpgsql", "sql"]},
                    "status": {"type": "string", "enum": ["active", "failed", "creating"], "description": "Filter by status"},
                    "limit": {"type": "integer", "description": "Max results", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stored_procedure_info",
            "description": "Get detailed information about a specific stored procedure including source code, parameters, and execution history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "procedure_id": {"type": "string", "description": "Procedure ID (UUID) or use name with schema"},
                    "name": {"type": "string", "description": "Procedure name (alternative to procedure_id)"},
                    "schema_name": {"type": "string", "description": "Schema name if using name", "default": "public"}
                },
                "required": []
            }
        }
    }
]


# =============================================================================
# DATA DICTIONARY TOOLS
# Tools for exploring and understanding the curated data dictionary
# =============================================================================

DATA_DICTIONARY_TOOLS = [
    # DISCOVERY TOOLS
    {
        "type": "function",
        "function": {
            "name": "discover_assets",
            "description": "Discover data assets (tables/views) in the data dictionary. Use this to find what data is available with business context, ownership, and trust information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "search": {"type": "string", "description": "Search term for table names, business names, or descriptions"},
                    "schema": {"type": "string", "description": "Filter by schema name"},
                    "business_domain": {"type": "string", "description": "Filter by domain (e.g., 'Sales', 'Finance')"},
                    "trust_tier": {"type": "string", "enum": ["certified", "trusted", "experimental", "deprecated"]},
                    "limit": {"type": "integer", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_documented_tables",
            "description": "List all tables that have data dictionary documentation (column definitions). Use this to see which tables have been documented with business descriptions, examples, and metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Filter by schema name (default: public)", "default": "public"},
                    "include_column_details": {"type": "boolean", "description": "Include column counts and sample definitions", "default": True}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discover_relationships",
            "description": "Discover relationships between tables in the data dictionary. Shows how tables connect via foreign keys and semantic relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Filter by schema"},
                    "table": {"type": "string", "description": "Get relationships for specific table"},
                    "limit": {"type": "integer", "default": 50}
                },
                "required": []
            }
        }
    },
    # DOCUMENTATION TOOLS
    {
        "type": "function",
        "function": {
            "name": "get_asset_documentation",
            "description": "Get full documentation for a data asset (table/view) including business definition, domain, ownership, grain, and known issues.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_field_documentation",
            "description": "Get documentation for a specific column including business name, definition, semantic role, and data type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    # ANALYSIS TOOLS
    {
        "type": "function",
        "function": {
            "name": "check_data_quality",
            "description": "Check trust tier, quality score, approval status, and known issues for a table. Use to assess if data is fit for your use case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_trusted_data",
            "description": "Find data assets that are approved for specific use cases like reporting or ML training.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "use_case": {"type": "string", "enum": ["reporting", "ml", "analysis"], "description": "Intended use case"},
                    "min_trust_tier": {"type": "string", "enum": ["certified", "trusted", "experimental"], "default": "trusted"},
                    "business_domain": {"type": "string", "description": "Filter by business domain"},
                    "limit": {"type": "integer", "default": 25}
                },
                "required": ["use_case"]
            }
        }
    },
    # UNDERSTANDING TOOLS
    {
        "type": "function",
        "function": {
            "name": "explain_table",
            "description": "Get a comprehensive explanation of a table including what it is, what one row represents (grain), ownership, trust info, key columns, and relationships.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_grain",
            "description": "Explain what one row represents in a table (the grain). Critical for correct aggregations and joins.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["schema", "table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_join",
            "description": "Explain how to join two tables safely. Analyzes relationships, suggests join columns, warns about fanout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "left_schema": {"type": "string", "description": "Left table schema"},
                    "left_table": {"type": "string", "description": "Left table name"},
                    "right_schema": {"type": "string", "description": "Right table schema"},
                    "right_table": {"type": "string", "description": "Right table name"}
                },
                "required": ["left_schema", "left_table", "right_schema", "right_table"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_dictionary",
            "description": "Search the data dictionary using natural language. Searches table names, column names, business definitions, and tags.",
            "parameters": {
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "default": "default"},
                    "query": {"type": "string", "description": "Search query"},
                    "scope": {"type": "string", "enum": ["all", "tables", "columns", "definitions"], "default": "all"},
                    "schema": {"type": "string", "description": "Limit to specific schema"},
                    "limit": {"type": "integer", "default": 20}
                },
                "required": ["query"]
            }
        }
    },
    # UPDATE TOOLS - for modifying dictionary entries
    {
        "type": "function",
        "function": {
            "name": "preview_dictionary_update",
            "description": "Preview proposed changes to a data dictionary entry BEFORE saving. Shows current vs proposed values. The user must confirm before changes are saved. Creates a DRAFT that needs to be published.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name to update"},
                    "business_name": {"type": "string", "description": "New business-friendly name for the column"},
                    "business_description": {"type": "string", "description": "New business description explaining what this column means"},
                    "technical_description": {"type": "string", "description": "New technical description with implementation details"},
                    "examples": {"type": "array", "items": {"type": "string"}, "description": "Example values for this column"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_dictionary_update",
            "description": "Save a dictionary update as a DRAFT. After confirming, use publish_dictionary_entry to make it active, or submit_for_approval if approval workflow is required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name to update"},
                    "business_name": {"type": "string", "description": "New business-friendly name"},
                    "business_description": {"type": "string", "description": "New business description"},
                    "technical_description": {"type": "string", "description": "New technical description"},
                    "examples": {"type": "array", "items": {"type": "string"}, "description": "Example values"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags"},
                    "version_notes": {"type": "string", "description": "Notes explaining why this update was made"},
                    "auto_publish": {"type": "boolean", "description": "If true, automatically publish the draft (skip approval workflow)", "default": True}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "publish_dictionary_entry",
            "description": "Publish a draft dictionary entry directly, making it the active version. Use after save_dictionary_update if auto_publish was false.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the draft entry to publish"},
                    "notes": {"type": "string", "description": "Optional notes about the publication"}
                },
                "required": ["entry_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_for_approval",
            "description": "Submit a draft dictionary entry for approval. Changes state from 'draft' to 'pending_approval'. Use when approval workflow is required.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the draft entry to submit for approval"}
                },
                "required": ["entry_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_pending_approvals",
            "description": "List all dictionary entries pending approval. Shows entries waiting for review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Optional: filter by schema"},
                    "table": {"type": "string", "description": "Optional: filter by table"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "approve_dictionary_entry",
            "description": "Approve a pending dictionary entry and publish it. Changes state from 'pending_approval' to 'published'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the pending entry to approve"},
                    "notes": {"type": "string", "description": "Optional approver notes"}
                },
                "required": ["entry_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reject_dictionary_entry",
            "description": "Reject a pending dictionary entry and return it to draft state. Changes state from 'pending_approval' back to 'draft'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the pending entry to reject"},
                    "reason": {"type": "string", "description": "Reason for rejection"}
                },
                "required": ["entry_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_column_history",
            "description": "Get the version history of a column's documentation. Shows all versions with state, source, and timestamps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "schema": {"type": "string", "description": "Schema name"},
                    "table": {"type": "string", "description": "Table name"},
                    "column": {"type": "string", "description": "Column name"}
                },
                "required": ["schema", "table", "column"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rollback_column_version",
            "description": "Rollback a column's documentation to a previous version. Use get_column_history first to see available versions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entry_id": {"type": "integer", "description": "The ID of the version to restore (from get_column_history)"}
                },
                "required": ["entry_id"]
            }
        }
    }
]

# ML Development tools for the chat assistant
ML_DEVELOPMENT_TOOLS = [
    # RECIPE DISCOVERY
    {
        "type": "function",
        "function": {
            "name": "list_ml_recipes",
            "description": "List ML recipes with optional filters. Recipes define reusable ML model patterns.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_family": {
                        "type": "string",
                        "enum": ["pricing", "next_best_action", "location_scoring", "forecasting"],
                        "description": "Filter by model family"
                    },
                    "level": {
                        "type": "string",
                        "enum": ["baseline", "industry", "client"],
                        "description": "Filter by recipe level"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "approved", "archived"],
                        "description": "Filter by status"
                    },
                    "limit": {"type": "integer", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ml_recipe",
            "description": "Get details about a specific ML recipe including its configuration and versions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "string", "description": "The recipe ID"}
                },
                "required": ["recipe_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_recipe_versions",
            "description": "List all versions of an ML recipe. Shows the evolution of the recipe manifest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "string", "description": "The recipe ID"}
                },
                "required": ["recipe_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recipe_version",
            "description": "Get a specific version of an ML recipe including the full manifest.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "string", "description": "The recipe ID"},
                    "version_id": {"type": "string", "description": "The version ID"}
                },
                "required": ["recipe_id", "version_id"]
            }
        }
    },
    # MODEL MANAGEMENT
    {
        "type": "function",
        "function": {
            "name": "list_ml_models",
            "description": "List registered ML models with optional filters. Models are trained instances of recipes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_family": {
                        "type": "string",
                        "enum": ["pricing", "next_best_action", "location_scoring", "forecasting"],
                        "description": "Filter by model family"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["draft", "staging", "production", "retired"],
                        "description": "Filter by status"
                    },
                    "limit": {"type": "integer", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ml_model",
            "description": "Get details about a specific ML model including its recipe, status, and owner.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string", "description": "The model ID"}
                },
                "required": ["model_id"]
            }
        }
    },
    # RUN MANAGEMENT
    {
        "type": "function",
        "function": {
            "name": "list_ml_runs",
            "description": "List ML runs (training, evaluation, or backtest). Shows execution history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string", "description": "Filter by model ID"},
                    "recipe_id": {"type": "string", "description": "Filter by recipe ID"},
                    "status": {
                        "type": "string",
                        "enum": ["queued", "running", "succeeded", "failed"],
                        "description": "Filter by status"
                    },
                    "limit": {"type": "integer", "default": 25}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_ml_run",
            "description": "Get details about a specific ML run including metrics, artifacts, and logs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "description": "The run ID"}
                },
                "required": ["run_id"]
            }
        }
    },
    # MONITORING
    {
        "type": "function",
        "function": {
            "name": "get_model_monitoring",
            "description": "Get monitoring snapshots for a model. Shows performance, drift, and alerts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "model_id": {"type": "string", "description": "The model ID"},
                    "limit": {"type": "integer", "default": 10, "description": "Number of snapshots to return"}
                },
                "required": ["model_id"]
            }
        }
    },
    # SYNTHETIC EXAMPLES
    {
        "type": "function",
        "function": {
            "name": "get_synthetic_example",
            "description": "Get synthetic example data for a recipe. Useful for testing and understanding the expected data format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipe_id": {"type": "string", "description": "The recipe ID"}
                },
                "required": ["recipe_id"]
            }
        }
    },
    # SUMMARY/OVERVIEW
    {
        "type": "function",
        "function": {
            "name": "get_ml_summary",
            "description": "Get a summary of ML development status including recipe counts, model counts, recent runs, and production models.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Combine all tools
ALL_CHAT_TOOLS = DATA_EXPLORER_TOOLS + DATA_DICTIONARY_TOOLS + ML_DEVELOPMENT_TOOLS


class ChatService:
    """Service for managing chat conversations and messages."""
    
    @staticmethod
    def create_conversation(session: Session, data: ConversationCreate) -> ChatConversation:
        """Create a new chat conversation."""
        conversation = ChatConversation(
            title=data.title,
            provider=data.provider,
            model=data.model,
            connection_id=data.connection_id,
            meta=data.meta
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation
    
    @staticmethod
    def list_conversations(
        session: Session,
        skip: int = 0,
        limit: int = 50,
        provider: Optional[str] = None
    ) -> List[ConversationResponse]:
        """List conversations ordered by updated_at desc."""
        query = select(ChatConversation)
        
        if provider:
            query = query.where(ChatConversation.provider == provider)
        
        query = query.order_by(desc(ChatConversation.updated_at)).offset(skip).limit(limit)
        
        conversations = session.exec(query).all()
        
        # Add message count
        results = []
        for conv in conversations:
            count_query = select(func.count(ChatMessage.id)).where(
                ChatMessage.conversation_id == conv.id
            )
            message_count = session.exec(count_query).one()
            
            conv_dict = conv.model_dump()
            conv_dict['message_count'] = message_count
            results.append(ConversationResponse(**conv_dict))
        
        return results
    
    @staticmethod
    def get_conversation(session: Session, conversation_id: UUID) -> Optional[ChatConversation]:
        """Get a conversation by ID."""
        return session.get(ChatConversation, conversation_id)
    
    @staticmethod
    def get_conversation_with_messages(
        session: Session,
        conversation_id: UUID
    ) -> Optional[ConversationWithMessages]:
        """Get conversation with full message history."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return None
        
        # Get messages ordered by sequence
        messages_query = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.sequence)
        
        messages = session.exec(messages_query).all()
        
        return ConversationWithMessages(
            **conversation.model_dump(),
            message_count=len(messages),
            messages=[MessageResponse(**msg.model_dump()) for msg in messages]
        )
    
    @staticmethod
    def update_conversation(
        session: Session,
        conversation_id: UUID,
        title: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatConversation]:
        """Update conversation metadata."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return None
        
        if title is not None:
            conversation.title = title
        if meta is not None:
            conversation.meta = meta
        
        conversation.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(conversation)
        return conversation
    
    @staticmethod
    def delete_conversation(session: Session, conversation_id: UUID) -> bool:
        """Delete a conversation and all its messages."""
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            return False
        
        session.delete(conversation)
        session.commit()
        return True
    
    @staticmethod
    def _get_next_sequence(session: Session, conversation_id: UUID) -> int:
        """Get next sequence number for a conversation."""
        query = select(func.max(ChatMessage.sequence)).where(
            ChatMessage.conversation_id == conversation_id
        )
        max_seq = session.exec(query).one()
        return (max_seq or 0) + 1
    
    @staticmethod
    def _save_message(
        session: Session,
        conversation_id: UUID,
        role: str,
        content: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_input: Optional[Dict[str, Any]] = None,
        tool_output: Optional[Dict[str, Any]] = None,
        raw_request: Optional[Dict[str, Any]] = None,
        raw_response: Optional[Dict[str, Any]] = None
    ) -> ChatMessage:
        """Save a message to the database."""
        sequence = ChatService._get_next_sequence(session, conversation_id)
        
        message = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sequence=sequence,
            provider=provider,
            model=model,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            raw_request=raw_request,
            raw_response=raw_response
        )
        
        session.add(message)
        session.commit()
        session.refresh(message)
        return message
    
    @staticmethod
    def _execute_tool(tool_name: str, tool_input: Dict[str, Any], session: Session = None) -> Dict[str, Any]:
        """Execute a Data Explorer or Data Dictionary tool and return result."""
        connection_id = tool_input.get("connection_id", "default")
        
        try:
            if tool_name == "list_connections":
                from ..data_explorer.db_configs import get_database_configs
                configs = get_database_configs()
                return {
                    "success": True,
                    "data": [
                        {
                            "id": config.id,
                            "label": f"{config.name} ({config.description})",
                            "host": config.host,
                            "port": config.port,
                            "database": config.database
                        }
                        for config in configs
                    ]
                }
            
            elif tool_name == "list_schemas":
                schemas = DataExplorerService.get_schemas(db_id=connection_id)
                return {
                    "success": True,
                    "data": [{"name": s.name, "table_count": s.table_count} for s in schemas]
                }
            
            elif tool_name == "list_tables":
                schema = tool_input.get("schema", "public")
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                return {
                    "success": True,
                    "data": [
                        {
                            "schema": t.schema,
                            "name": t.name,
                            "type": t.type,
                            "row_estimate": t.row_estimate
                        }
                        for t in tables
                    ]
                }
            
            elif tool_name == "get_table_info":
                columns = DataExplorerService.get_columns(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    db_id=connection_id
                )
                return {
                    "success": True,
                    "data": {
                        "schema": tool_input["schema"],
                        "table": tool_input["table"],
                        "columns": [
                            {
                                "name": c.name,
                                "data_type": c.data_type,
                                "is_nullable": c.is_nullable,
                                "default": c.default,
                                "ordinal_position": c.ordinal_position
                            }
                            for c in columns
                        ]
                    }
                }
            
            elif tool_name == "sample_rows":
                limit = tool_input.get("limit", 50)
                offset = tool_input.get("offset", 0)
                page = (offset // limit) + 1
                
                result = DataExplorerService.get_table_rows(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    page=page,
                    page_size=min(limit, 500),
                    db_id=connection_id
                )
                return {
                    "success": True,
                    "data": {
                        "schema": result.schema,
                        "table": result.table,
                        "columns": result.columns,
                        "rows": result.rows,
                        "total_rows": result.total_rows
                    }
                }
            
            elif tool_name == "profile_table":
                max_distinct = tool_input.get("max_distinct", 50)
                result = DataExplorerService.profile_table(
                    schema=tool_input["schema"],
                    table=tool_input["table"],
                    max_distinct=max_distinct,
                    db_id=connection_id
                )
                return {"success": True, "data": result}
            
            elif tool_name == "run_query":
                result = DataExplorerService.execute_query(
                    sql=tool_input["sql"],
                    page=tool_input.get("page", 1),
                    page_size=tool_input.get("page_size", 100),
                    db_id=connection_id
                )

                response_data = {
                    "columns": result.columns,
                    "rows": result.rows,
                    "total_rows_estimate": result.total_rows_estimate,
                    "execution_time_ms": result.execution_time_ms,
                    "error": result.error
                }

                if not result.error:
                    row_count = len(result.rows)
                    response_data["summary"] = (
                        f"Query returned {row_count} row(s) "
                        f"in {result.execution_time_ms:.2f}ms"
                    )

                return {
                    "success": not bool(result.error),
                    "data": response_data
                }

            # =================================================================
            # DATA EXPORT TOOLS
            # =================================================================

            elif tool_name == "export_query_to_s3":
                return ChatService._execute_export_query_to_s3(session, tool_input)

            elif tool_name == "export_table_to_s3":
                return ChatService._execute_export_table_to_s3(session, tool_input)

            elif tool_name == "list_exports":
                return ChatService._execute_list_exports(session, tool_input)

            elif tool_name == "get_export_status":
                return ChatService._execute_get_export_status(session, tool_input)

            elif tool_name == "get_export_download_url":
                return ChatService._execute_get_export_download_url(session, tool_input)

            # =================================================================
            # MATERIALIZED VIEW TOOLS
            # =================================================================

            elif tool_name == "create_materialized_view":
                return ChatService._execute_create_materialized_view(session, tool_input)

            elif tool_name == "refresh_materialized_view":
                return ChatService._execute_refresh_materialized_view(session, tool_input)

            elif tool_name == "drop_materialized_view":
                return ChatService._execute_drop_materialized_view(session, tool_input)

            elif tool_name == "list_materialized_views":
                return ChatService._execute_list_materialized_views(session, tool_input)

            elif tool_name == "get_materialized_view_info":
                return ChatService._execute_get_materialized_view_info(session, tool_input)

            # =================================================================
            # STORED PROCEDURE TOOLS
            # =================================================================

            elif tool_name == "create_stored_procedure":
                return ChatService._execute_create_stored_procedure(session, tool_input)

            elif tool_name == "execute_stored_procedure":
                return ChatService._execute_execute_stored_procedure(session, tool_input)

            elif tool_name == "drop_stored_procedure":
                return ChatService._execute_drop_stored_procedure(session, tool_input)

            elif tool_name == "list_stored_procedures":
                return ChatService._execute_list_stored_procedures(session, tool_input)

            elif tool_name == "get_stored_procedure_info":
                return ChatService._execute_get_stored_procedure_info(session, tool_input)

            # =================================================================
            # DATA DICTIONARY TOOLS
            # =================================================================

            elif tool_name == "discover_assets":
                return ChatService._execute_discover_assets(session, tool_input)
            
            elif tool_name == "list_documented_tables":
                return ChatService._execute_list_documented_tables(session, tool_input)
            
            elif tool_name == "discover_relationships":
                return ChatService._execute_discover_relationships(session, tool_input)
            
            elif tool_name == "get_asset_documentation":
                return ChatService._execute_get_asset_documentation(session, tool_input)
            
            elif tool_name == "get_field_documentation":
                return ChatService._execute_get_field_documentation(session, tool_input)
            
            elif tool_name == "check_data_quality":
                return ChatService._execute_check_data_quality(session, tool_input)
            
            elif tool_name == "find_trusted_data":
                return ChatService._execute_find_trusted_data(session, tool_input)
            
            elif tool_name == "explain_table":
                return ChatService._execute_explain_table(session, tool_input)
            
            elif tool_name == "explain_grain":
                return ChatService._execute_explain_grain(session, tool_input)
            
            elif tool_name == "explain_join":
                return ChatService._execute_explain_join(session, tool_input)
            
            elif tool_name == "search_dictionary":
                return ChatService._execute_search_dictionary(session, tool_input)
            
            # UPDATE TOOLS
            elif tool_name == "preview_dictionary_update":
                return ChatService._execute_preview_dictionary_update(session, tool_input)
            
            elif tool_name == "save_dictionary_update":
                return ChatService._execute_save_dictionary_update(session, tool_input)
            
            elif tool_name == "publish_dictionary_entry":
                return ChatService._execute_publish_dictionary_entry(session, tool_input)
            
            elif tool_name == "submit_for_approval":
                return ChatService._execute_submit_for_approval(session, tool_input)
            
            elif tool_name == "list_pending_approvals":
                return ChatService._execute_list_pending_approvals(session, tool_input)
            
            elif tool_name == "approve_dictionary_entry":
                return ChatService._execute_approve_dictionary_entry(session, tool_input)
            
            elif tool_name == "reject_dictionary_entry":
                return ChatService._execute_reject_dictionary_entry(session, tool_input)

            elif tool_name == "get_column_history":
                return ChatService._execute_get_column_history(session, tool_input)

            elif tool_name == "rollback_column_version":
                return ChatService._execute_rollback_column_version(session, tool_input)

            # =================================================================
            # ML DEVELOPMENT TOOLS
            # =================================================================
            
            elif tool_name == "list_ml_recipes":
                return ChatService._execute_list_ml_recipes(tool_input)
            
            elif tool_name == "get_ml_recipe":
                return ChatService._execute_get_ml_recipe(tool_input)
            
            elif tool_name == "list_recipe_versions":
                return ChatService._execute_list_recipe_versions(tool_input)
            
            elif tool_name == "get_recipe_version":
                return ChatService._execute_get_recipe_version(tool_input)
            
            elif tool_name == "list_ml_models":
                return ChatService._execute_list_ml_models(tool_input)
            
            elif tool_name == "get_ml_model":
                return ChatService._execute_get_ml_model(tool_input)
            
            elif tool_name == "list_ml_runs":
                return ChatService._execute_list_ml_runs(tool_input)
            
            elif tool_name == "get_ml_run":
                return ChatService._execute_get_ml_run(tool_input)
            
            elif tool_name == "get_model_monitoring":
                return ChatService._execute_get_model_monitoring(tool_input)
            
            elif tool_name == "get_synthetic_example":
                return ChatService._execute_get_synthetic_example(tool_input)
            
            elif tool_name == "get_ml_summary":
                return ChatService._execute_get_ml_summary(tool_input)

            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            logger.error(f"Tool execution error: {tool_name} - {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def stream_chat_response(
        session: Session,
        conversation_id: UUID,
        user_message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        connection_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat response with tool calling support.
        
        Yields stream events:
        - {"event": "delta", "data": {"content": str}}
        - {"event": "tool_call", "data": {"tool_name": str, "tool_input": dict}}
        - {"event": "tool_result", "data": {"tool_name": str, "result": dict}}
        - {"event": "done", "data": {"message_id": str}}
        - {"event": "error", "data": {"error": str}}
        """
        conversation = session.get(ChatConversation, conversation_id)
        if not conversation:
            yield {"event": "error", "data": {"error": "Conversation not found"}}
            return
        
        # Use conversation settings if not overridden
        provider = provider or conversation.provider
        model = model or conversation.model
        connection_id = connection_id or conversation.connection_id or "default"
        
        # Save user message
        ChatService._save_message(
            session,
            conversation_id=conversation_id,
            role="user",
            content=user_message
        )
        
        # Get conversation history
        messages_query = select(ChatMessage).where(
            ChatMessage.conversation_id == conversation_id
        ).order_by(ChatMessage.sequence)
        
        history = session.exec(messages_query).all()
        
        # Convert to LLM format with proper tool call handling
        llm_messages = []
        i = 0
        while i < len(history):
            msg = history[i]
            
            if msg.role == "user":
                llm_messages.append({"role": "user", "content": msg.content})
                i += 1
            
            elif msg.role == "assistant":
                llm_messages.append({"role": "assistant", "content": msg.content})
                i += 1
            
            elif msg.role == "tool":
                # Group consecutive tool messages
                tool_messages = []
                tool_calls = []
                
                while i < len(history) and history[i].role == "tool":
                    tool_msg = history[i]
                    # Generate a short tool call ID (max 40 chars for OpenAI)
                    # Use first 32 chars of UUID hex (no dashes)
                    tool_call_id = str(tool_msg.id).replace('-', '')[:32]
                    
                    # Build tool call for assistant message
                    tool_calls.append({
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_msg.tool_name,
                            "arguments": json.dumps(tool_msg.tool_input) if tool_msg.tool_input else "{}"
                        }
                    })
                    
                    # Build tool result message
                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_msg.tool_output) if tool_msg.tool_output else "{}"
                    })
                    
                    i += 1
                
                # Add assistant message with tool calls
                llm_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": tool_calls
                })
                
                # Add all tool result messages
                llm_messages.extend(tool_messages)
            
            else:
                # Skip unknown roles
                i += 1
        
        logger.info(f"Loaded {len(llm_messages)} messages for LLM context")
        if logger.isEnabledFor(logging.DEBUG):
            for idx, msg in enumerate(llm_messages):
                role = msg.get("role")
                has_content = bool(msg.get("content"))
                has_tool_calls = bool(msg.get("tool_calls"))
                logger.debug(f"  [{idx}] role={role}, has_content={has_content}, has_tool_calls={has_tool_calls}")
        
        # Get LLM provider
        try:
            llm = get_provider(provider=provider, model=model)
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {e}")
            yield {"event": "error", "data": {"error": str(e)}}
            return
        
        # Stream response with tool calling loop
        assistant_content = []
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"Chat iteration {iteration}, message count: {len(llm_messages)}")
                
                has_tool_call = False
                pending_tool_calls = []
                tool_call_messages = []  # Track assistant messages with tool calls
                
                async for event in llm.stream_chat(
                    messages=llm_messages,
                    tools=ALL_CHAT_TOOLS,
                    tool_choice="auto"
                ):
                    logger.debug(f"Stream event: {event['type']}")
                    
                    if event["type"] == "delta":
                        # Stream text delta
                        content = event["content"]
                        assistant_content.append(content)
                        yield {"event": "delta", "data": {"content": content}}
                    
                    elif event["type"] == "tool_call":
                        has_tool_call = True
                        tool_name = event["tool_name"]
                        tool_input = event["tool_input"]
                        # Use the tool_call_id from the event, or generate a short one
                        tool_call_id = event.get("tool_call_id", f"{tool_name}_{iteration}")
                        
                        logger.info(f"Tool call: {tool_name} with input: {tool_input}")
                        
                        yield {"event": "tool_call", "data": {
                            "tool_name": tool_name,
                            "tool_input": tool_input
                        }}
                        
                        # Execute tool
                        tool_output = ChatService._execute_tool(tool_name, tool_input, session)
                        logger.info(f"Tool result: {tool_name} - success: {tool_output.get('success')}")
                        
                        # Save tool call
                        ChatService._save_message(
                            session,
                            conversation_id=conversation_id,
                            role="tool",
                            tool_name=tool_name,
                            tool_input=tool_input,
                            tool_output=tool_output
                        )
                        
                        yield {"event": "tool_result", "data": {
                            "tool_name": tool_name,
                            "result": tool_output
                        }}
                        
                        # Accumulate tool calls for the assistant message
                        pending_tool_calls.append({
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_input)
                            }
                        })
                        
                        # Also accumulate for adding to messages
                        tool_call_messages.append({
                            "id": tool_call_id,
                            "name": tool_name,
                            "output": tool_output
                        })
                    
                    elif event["type"] == "done":
                        logger.info(f"Stream done, had_tool_call: {has_tool_call}, finish_reason: {event.get('finish_reason')}")
                        
                        # If we had tool calls, add them to messages and continue
                        if has_tool_call and tool_call_messages:
                            # Add assistant message with tool calls (required by OpenAI)
                            llm_messages.append({
                                "role": "assistant",
                                "content": None,
                                "tool_calls": pending_tool_calls
                            })
                            
                            # Add all tool results
                            for tool_call in tool_call_messages:
                                llm_messages.append({
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "content": json.dumps(tool_call["output"])
                                })
                            
                            # Clear for next iteration
                            pending_tool_calls = []
                            tool_call_messages = []
                            break  # Break inner loop, continue outer while loop
                        
                        # No tool calls - save final response and exit
                        final_content = "".join(assistant_content)
                        logger.info(f"Final content length: {len(final_content)}")
                        
                        if final_content.strip():
                            message = ChatService._save_message(
                                session,
                                conversation_id=conversation_id,
                                role="assistant",
                                content=final_content,
                                provider=provider,
                                model=model
                            )
                            
                            # Auto-generate title if this is the first exchange
                            if not conversation.title and len(history) <= 2:
                                title = user_message[:50] + ("..." if len(user_message) > 50 else "")
                                conversation.title = title
                                session.commit()
                            
                            yield {"event": "done", "data": {"message_id": str(message.id)}}
                        else:
                            yield {"event": "done", "data": {"message_id": None}}
                        
                        return  # Exit completely
                    
                    elif event["type"] == "error":
                        logger.error(f"Stream error: {event.get('error')}")
                        yield {"event": "error", "data": {"error": event["error"]}}
                        return
                
                # If we didn't have tool calls in this iteration, exit
                if not has_tool_call:
                    logger.warning("Stream ended without tool calls or completion")
                    break
            
            # Max iterations reached
            if iteration >= max_iterations:
                logger.warning(f"Max iterations ({max_iterations}) reached")
                final_content = "".join(assistant_content)
                if final_content.strip():
                    message = ChatService._save_message(
                        session,
                        conversation_id=conversation_id,
                        role="assistant",
                        content=final_content,
                        provider=provider,
                        model=model
                    )
                    yield {"event": "done", "data": {"message_id": str(message.id)}}
                else:
                    yield {"event": "error", "data": {"error": "Max iterations reached without response"}}
        
        except Exception as e:
            logger.error(f"Chat streaming error: {e}", exc_info=True)
            yield {"event": "error", "data": {"error": str(e)}}

    # =========================================================================
    # DATA EXPORT TOOL HANDLERS
    # =========================================================================

    @staticmethod
    def _execute_export_query_to_s3(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute export_query_to_s3 tool - exports query results to S3."""
        import asyncio

        async def _run_export():
            from ..data_explorer.export_service import DataExportService
            from db import async_session_maker

            sql = tool_input.get("sql")
            name = tool_input.get("name")
            format_type = tool_input.get("format", "parquet")
            connection_id = tool_input.get("connection_id", "default")
            description = tool_input.get("description")
            compression = tool_input.get("compression", "snappy")

            if not sql or not name:
                return {"success": False, "error": "sql and name are required"}

            # Sanitize name for filename
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            output_path = f"exports/{safe_name}.{format_type}"

            async with async_session_maker() as async_session:
                export_service = DataExportService(async_session)
                result = await export_service.export_query(
                    sql=sql,
                    name=name,
                    output_path=output_path,
                    format=format_type,
                    connection_id=connection_id,
                    description=description,
                    compression=compression if compression != "none" else None,
                )

            return {
                "success": True,
                "data": {
                    "export_id": result["export_id"],
                    "status": result["status"],
                    "destination_uri": result["destination_uri"],
                    "row_count": result["row_count"],
                    "column_count": result["column_count"],
                    "file_size_bytes": result["file_size_bytes"],
                    "format": result["format"],
                    "duration_seconds": result["duration_seconds"],
                    "message": f"Successfully exported {result['row_count']} rows to {result['destination_uri']}"
                }
            }

        try:
            # Run async code in event loop
            try:
                loop = asyncio.get_running_loop()
                # Already in async context, create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_export())
                    return future.result(timeout=300)
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(_run_export())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Export query error: {e}")
            return {"success": False, "error": f"Export failed: {str(e)}"}

    @staticmethod
    def _execute_export_table_to_s3(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute export_table_to_s3 tool - exports entire table to S3."""
        import asyncio

        async def _run_export():
            from ..data_explorer.export_service import DataExportService
            from db import async_session_maker

            schema = tool_input.get("schema")
            table = tool_input.get("table")
            name = tool_input.get("name")
            format_type = tool_input.get("format", "parquet")
            connection_id = tool_input.get("connection_id", "default")
            limit = tool_input.get("limit")
            compression = tool_input.get("compression", "snappy")

            if not schema or not table or not name:
                return {"success": False, "error": "schema, table, and name are required"}

            # Sanitize name for filename
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            output_path = f"exports/{safe_name}.{format_type}"

            async with async_session_maker() as async_session:
                export_service = DataExportService(async_session)
                result = await export_service.export_table(
                    schema=schema,
                    table=table,
                    name=name,
                    output_path=output_path,
                    format=format_type,
                    connection_id=connection_id,
                    compression=compression if compression != "none" else None,
                    limit=limit,
                )

            return {
                "success": True,
                "data": {
                    "export_id": result["export_id"],
                    "status": result["status"],
                    "destination_uri": result["destination_uri"],
                    "row_count": result["row_count"],
                    "column_count": result["column_count"],
                    "file_size_bytes": result["file_size_bytes"],
                    "format": result["format"],
                    "duration_seconds": result["duration_seconds"],
                    "message": f"Successfully exported {result['row_count']} rows from {schema}.{table} to {result['destination_uri']}"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_export())
                    return future.result(timeout=300)
            except RuntimeError:
                return asyncio.run(_run_export())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Export table error: {e}")
            return {"success": False, "error": f"Export failed: {str(e)}"}

    @staticmethod
    def _execute_list_exports(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list_exports tool - lists all exports."""
        import asyncio

        async def _run_list():
            from ..data_explorer.export_service import DataExportService
            from db import async_session_maker

            status_filter = tool_input.get("status")
            limit = tool_input.get("limit", 25)

            async with async_session_maker() as async_session:
                export_service = DataExportService(async_session)
                exports, total = await export_service.list_exports(
                    limit=limit,
                    status=status_filter,
                )

            return {
                "success": True,
                "data": {
                    "exports": exports,
                    "total": total,
                    "message": f"Found {total} export(s)"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_list())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_list())
        except Exception as e:
            logger.error(f"List exports error: {e}")
            return {"success": False, "error": f"Failed to list exports: {str(e)}"}

    @staticmethod
    def _execute_get_export_status(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_export_status tool - gets detailed export status."""
        import asyncio
        from uuid import UUID as PyUUID

        export_id = tool_input.get("export_id")
        if not export_id:
            return {"success": False, "error": "export_id is required"}

        try:
            export_uuid = PyUUID(export_id)
        except ValueError:
            return {"success": False, "error": "Invalid export_id format"}

        async def _run_get():
            from ..data_explorer.export_service import DataExportService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                export_service = DataExportService(async_session)
                export = await export_service.get_export(export_uuid)

            if not export:
                return {"success": False, "error": f"Export {export_id} not found"}

            return {"success": True, "data": export}

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_get())
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(_run_get())
        except Exception as e:
            logger.error(f"Get export status error: {e}")
            return {"success": False, "error": f"Failed to get export: {str(e)}"}

    @staticmethod
    def _execute_get_export_download_url(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_export_download_url tool - gets presigned download URL."""
        import asyncio
        from uuid import UUID as PyUUID

        export_id = tool_input.get("export_id")
        if not export_id:
            return {"success": False, "error": "export_id is required"}

        try:
            export_uuid = PyUUID(export_id)
        except ValueError:
            return {"success": False, "error": "Invalid export_id format"}

        async def _run_get_url():
            from ..data_explorer.export_service import DataExportService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                export_service = DataExportService(async_session)

                # Check export exists and is completed
                export = await export_service.get_export(export_uuid)
                if not export:
                    return {"success": False, "error": f"Export {export_id} not found"}

                if export["status"] != "completed":
                    return {"success": False, "error": f"Export is not completed (status: {export['status']})"}

                # Generate presigned URL
                download_url = await export_service.generate_download_url(export_uuid)

            if not download_url:
                return {"success": False, "error": "Could not generate download URL"}

            return {
                "success": True,
                "data": {
                    "export_id": export_id,
                    "download_url": download_url,
                    "expires_in_seconds": 3600,
                    "message": "Download URL valid for 1 hour"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_get_url())
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(_run_get_url())
        except Exception as e:
            logger.error(f"Get download URL error: {e}")
            return {"success": False, "error": f"Failed to generate download URL: {str(e)}"}

    # =========================================================================
    # MATERIALIZED VIEW TOOL HANDLERS
    # =========================================================================

    @staticmethod
    def _execute_create_materialized_view(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_materialized_view tool - creates a new materialized view."""
        import asyncio

        name = tool_input.get("name")
        source_query = tool_input.get("source_query")

        if not name:
            return {"success": False, "error": "name is required"}
        if not source_query:
            return {"success": False, "error": "source_query is required"}

        async def _run_create():
            from ..data_explorer.materialized_view_service import MaterializedViewService
            from db import async_session_maker

            schema_name = tool_input.get("schema_name", "public")
            description = tool_input.get("description")
            connection_id = tool_input.get("connection_id", "default")
            with_data = tool_input.get("with_data", True)

            async with async_session_maker() as async_session:
                mv_service = MaterializedViewService(async_session)
                result = await mv_service.create_materialized_view(
                    name=name,
                    source_query=source_query,
                    schema_name=schema_name,
                    description=description,
                    connection_id=connection_id,
                    with_data=with_data,
                )

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Created materialized view {schema_name}.{name} with {result.get('row_count', 0)} rows"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_create())
                    return future.result(timeout=300)
            except RuntimeError:
                return asyncio.run(_run_create())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Create materialized view error: {e}")
            return {"success": False, "error": f"Failed to create view: {str(e)}"}

    @staticmethod
    def _execute_refresh_materialized_view(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute refresh_materialized_view tool - refreshes a materialized view."""
        import asyncio
        from uuid import UUID as PyUUID

        view_id = tool_input.get("view_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")
        concurrently = tool_input.get("concurrently", False)

        if not view_id and not name:
            return {"success": False, "error": "Either view_id or name is required"}

        async def _run_refresh():
            from ..data_explorer.materialized_view_service import MaterializedViewService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                mv_service = MaterializedViewService(async_session)

                # Get view by ID or name
                if view_id:
                    try:
                        uuid = PyUUID(view_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid view_id format"}
                else:
                    view = await mv_service.get_view_by_name(name, schema_name)
                    if not view:
                        return {"success": False, "error": f"View {schema_name}.{name} not found"}
                    uuid = PyUUID(view["id"])

                result = await mv_service.refresh_materialized_view(
                    view_id=uuid,
                    concurrently=concurrently,
                )

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Refreshed view {result['schema_name']}.{result['name']} ({result['row_count']} rows in {result['duration_ms']}ms)"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_refresh())
                    return future.result(timeout=600)
            except RuntimeError:
                return asyncio.run(_run_refresh())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Refresh materialized view error: {e}")
            return {"success": False, "error": f"Failed to refresh view: {str(e)}"}

    @staticmethod
    def _execute_drop_materialized_view(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute drop_materialized_view tool - drops a materialized view."""
        import asyncio
        from uuid import UUID as PyUUID

        view_id = tool_input.get("view_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")

        if not view_id and not name:
            return {"success": False, "error": "Either view_id or name is required"}

        async def _run_drop():
            from ..data_explorer.materialized_view_service import MaterializedViewService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                mv_service = MaterializedViewService(async_session)

                # Get view by ID or name
                if view_id:
                    try:
                        uuid = PyUUID(view_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid view_id format"}
                else:
                    view = await mv_service.get_view_by_name(name, schema_name)
                    if not view:
                        return {"success": False, "error": f"View {schema_name}.{name} not found"}
                    uuid = PyUUID(view["id"])

                result = await mv_service.drop_materialized_view(view_id=uuid)

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Dropped materialized view {result['schema_name']}.{result['name']}"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_drop())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_drop())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Drop materialized view error: {e}")
            return {"success": False, "error": f"Failed to drop view: {str(e)}"}

    @staticmethod
    def _execute_list_materialized_views(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list_materialized_views tool - lists all managed materialized views."""
        import asyncio

        async def _run_list():
            from ..data_explorer.materialized_view_service import MaterializedViewService
            from db import async_session_maker

            schema_name = tool_input.get("schema_name")
            status = tool_input.get("status")
            limit = tool_input.get("limit", 25)

            async with async_session_maker() as async_session:
                mv_service = MaterializedViewService(async_session)
                views, total = await mv_service.list_views(
                    limit=limit,
                    schema_name=schema_name,
                    status=status,
                )

            return {
                "success": True,
                "data": {
                    "views": views,
                    "total": total,
                    "message": f"Found {total} materialized view(s)"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_list())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_list())
        except Exception as e:
            logger.error(f"List materialized views error: {e}")
            return {"success": False, "error": f"Failed to list views: {str(e)}"}

    @staticmethod
    def _execute_get_materialized_view_info(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_materialized_view_info tool - gets detailed view information."""
        import asyncio
        from uuid import UUID as PyUUID

        view_id = tool_input.get("view_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")

        if not view_id and not name:
            return {"success": False, "error": "Either view_id or name is required"}

        async def _run_get():
            from ..data_explorer.materialized_view_service import MaterializedViewService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                mv_service = MaterializedViewService(async_session)

                if view_id:
                    try:
                        uuid = PyUUID(view_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid view_id format"}
                    view = await mv_service.get_view(uuid)
                else:
                    view = await mv_service.get_view_by_name(name, schema_name)

                if not view:
                    return {"success": False, "error": f"View not found"}

            return {"success": True, "data": view}

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_get())
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(_run_get())
        except Exception as e:
            logger.error(f"Get materialized view info error: {e}")
            return {"success": False, "error": f"Failed to get view info: {str(e)}"}

    # =========================================================================
    # STORED PROCEDURE TOOL HANDLERS
    # =========================================================================

    @staticmethod
    def _execute_create_stored_procedure(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_stored_procedure tool - creates a new stored procedure."""
        import asyncio

        name = tool_input.get("name")
        source_code = tool_input.get("source_code")

        if not name:
            return {"success": False, "error": "name is required"}
        if not source_code:
            return {"success": False, "error": "source_code is required"}

        async def _run_create():
            from ..data_explorer.stored_procedure_service import StoredProcedureService
            from db import async_session_maker

            schema_name = tool_input.get("schema_name", "public")
            description = tool_input.get("description")
            language = tool_input.get("language", "plpgsql")
            parameters = tool_input.get("parameters", [])
            return_type = tool_input.get("return_type")
            returns_set = tool_input.get("returns_set", False)
            volatility = tool_input.get("volatility", "volatile")
            connection_id = tool_input.get("connection_id", "default")

            async with async_session_maker() as async_session:
                proc_service = StoredProcedureService(async_session)
                result = await proc_service.create_procedure(
                    name=name,
                    source_code=source_code,
                    schema_name=schema_name,
                    description=description,
                    language=language,
                    parameters=parameters,
                    return_type=return_type,
                    returns_set=returns_set,
                    volatility=volatility,
                    connection_id=connection_id,
                )

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Created procedure {schema_name}.{name}"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_create())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_create())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Create stored procedure error: {e}")
            return {"success": False, "error": f"Failed to create procedure: {str(e)}"}

    @staticmethod
    def _execute_execute_stored_procedure(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute execute_stored_procedure tool - runs a stored procedure."""
        import asyncio
        from uuid import UUID as PyUUID

        procedure_id = tool_input.get("procedure_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")
        arguments = tool_input.get("arguments", {})

        if not procedure_id and not name:
            return {"success": False, "error": "Either procedure_id or name is required"}

        async def _run_execute():
            from ..data_explorer.stored_procedure_service import StoredProcedureService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                proc_service = StoredProcedureService(async_session)

                # Get procedure by ID or name
                if procedure_id:
                    try:
                        uuid = PyUUID(procedure_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid procedure_id format"}
                else:
                    proc = await proc_service.get_procedure_by_name(name, schema_name)
                    if not proc:
                        return {"success": False, "error": f"Procedure {schema_name}.{name} not found"}
                    uuid = PyUUID(proc["id"])

                result = await proc_service.execute_procedure(
                    proc_id=uuid,
                    arguments=arguments,
                )

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Executed {result['schema_name']}.{result['name']} - {result['row_count']} row(s) in {result['duration_ms']}ms"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_execute())
                    return future.result(timeout=300)
            except RuntimeError:
                return asyncio.run(_run_execute())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Execute stored procedure error: {e}")
            return {"success": False, "error": f"Failed to execute procedure: {str(e)}"}

    @staticmethod
    def _execute_drop_stored_procedure(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute drop_stored_procedure tool - drops a stored procedure."""
        import asyncio
        from uuid import UUID as PyUUID

        procedure_id = tool_input.get("procedure_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")

        if not procedure_id and not name:
            return {"success": False, "error": "Either procedure_id or name is required"}

        async def _run_drop():
            from ..data_explorer.stored_procedure_service import StoredProcedureService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                proc_service = StoredProcedureService(async_session)

                # Get procedure by ID or name
                if procedure_id:
                    try:
                        uuid = PyUUID(procedure_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid procedure_id format"}
                else:
                    proc = await proc_service.get_procedure_by_name(name, schema_name)
                    if not proc:
                        return {"success": False, "error": f"Procedure {schema_name}.{name} not found"}
                    uuid = PyUUID(proc["id"])

                result = await proc_service.drop_procedure(proc_id=uuid)

            return {
                "success": True,
                "data": {
                    **result,
                    "message": f"Dropped procedure {result['schema_name']}.{result['name']}"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_drop())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_drop())
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Drop stored procedure error: {e}")
            return {"success": False, "error": f"Failed to drop procedure: {str(e)}"}

    @staticmethod
    def _execute_list_stored_procedures(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute list_stored_procedures tool - lists all managed procedures."""
        import asyncio

        async def _run_list():
            from ..data_explorer.stored_procedure_service import StoredProcedureService
            from db import async_session_maker

            schema_name = tool_input.get("schema_name")
            language = tool_input.get("language")
            status = tool_input.get("status")
            limit = tool_input.get("limit", 25)

            async with async_session_maker() as async_session:
                proc_service = StoredProcedureService(async_session)
                procedures, total = await proc_service.list_procedures(
                    limit=limit,
                    schema_name=schema_name,
                    language=language,
                    status=status,
                )

            return {
                "success": True,
                "data": {
                    "procedures": procedures,
                    "total": total,
                    "message": f"Found {total} stored procedure(s)"
                }
            }

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_list())
                    return future.result(timeout=60)
            except RuntimeError:
                return asyncio.run(_run_list())
        except Exception as e:
            logger.error(f"List stored procedures error: {e}")
            return {"success": False, "error": f"Failed to list procedures: {str(e)}"}

    @staticmethod
    def _execute_get_stored_procedure_info(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_stored_procedure_info tool - gets detailed procedure information."""
        import asyncio
        from uuid import UUID as PyUUID

        procedure_id = tool_input.get("procedure_id")
        name = tool_input.get("name")
        schema_name = tool_input.get("schema_name", "public")

        if not procedure_id and not name:
            return {"success": False, "error": "Either procedure_id or name is required"}

        async def _run_get():
            from ..data_explorer.stored_procedure_service import StoredProcedureService
            from db import async_session_maker

            async with async_session_maker() as async_session:
                proc_service = StoredProcedureService(async_session)

                if procedure_id:
                    try:
                        uuid = PyUUID(procedure_id)
                    except ValueError:
                        return {"success": False, "error": "Invalid procedure_id format"}
                    proc = await proc_service.get_procedure(uuid)
                else:
                    proc = await proc_service.get_procedure_by_name(name, schema_name)

                if not proc:
                    return {"success": False, "error": "Procedure not found"}

            return {"success": True, "data": proc}

        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, _run_get())
                    return future.result(timeout=30)
            except RuntimeError:
                return asyncio.run(_run_get())
        except Exception as e:
            logger.error(f"Get stored procedure info error: {e}")
            return {"success": False, "error": f"Failed to get procedure info: {str(e)}"}

    # =========================================================================
    # DATA DICTIONARY TOOL HANDLERS
    # =========================================================================
    
    @staticmethod
    def _execute_discover_assets(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discover_assets tool - cross-references database tables with BOTH dictionary sources."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            trust_tier = tool_input.get("trust_tier")
            business_domain = tool_input.get("business_domain")
            schema = tool_input.get("schema", "public")
            search = (tool_input.get("search") or "").lower()
            limit = tool_input.get("limit", 25)
            
            # === SOURCE 1: Enhanced dictionary (dictionary_assets - table-level) ===
            dict_results, dict_total = dict_service.search_assets(
                session=session,
                connection_id=connection_id,
                schema_name=schema if schema != "public" else None,
                search_term=None,
                trust_tier=None,
                business_domain=None,
                limit=500,
                offset=0
            )
            
            # Build lookup by schema.table
            enhanced_lookup = {}
            for asset in dict_results:
                key = f"{asset.schema_name}.{asset.table_name}".lower()
                enhanced_lookup[key] = asset
            
            # === SOURCE 2: Original dictionary (data_dictionary_entries - column-level) ===
            # Get distinct tables that have column definitions
            original_entries = session.exec(
                select(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name,
                    func.count(DataDictionaryEntry.id).label("column_count")
                ).where(
                    DataDictionaryEntry.schema_name == schema,
                    DataDictionaryEntry.is_active == True
                ).group_by(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name
                )
            ).all()
            
            # Build lookup for original dictionary
            original_lookup = {}
            for entry in original_entries:
                key = f"{entry.schema_name}.{entry.table_name}".lower()
                original_lookup[key] = {
                    "schema": entry.schema_name,
                    "table": entry.table_name,
                    "columns_documented": entry.column_count
                }
            
            logger.info(f"Found {len(enhanced_lookup)} tables in enhanced dict, {len(original_lookup)} in original dict")
            
            # === SOURCE 3: Raw tables from database (nexdata) ===
            raw_tables = []
            try:
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                raw_tables = list(tables)
            except Exception as e:
                logger.warning(f"Could not get raw tables: {e}")
            
            # === MERGE all sources ===
            assets = []
            in_dictionary = 0
            not_in_dictionary = 0
            
            # Track which tables we've processed
            processed_keys = set()
            
            for t in raw_tables:
                key = f"{t.schema}.{t.name}".lower()
                processed_keys.add(key)
                
                enhanced_entry = enhanced_lookup.get(key)
                original_entry = original_lookup.get(key)
                has_dictionary = bool(enhanced_entry or original_entry)
                
                # Apply search filter
                if search:
                    name_match = search in t.name.lower()
                    business_match = enhanced_entry and enhanced_entry.business_name and search in enhanced_entry.business_name.lower()
                    desc_match = enhanced_entry and enhanced_entry.business_definition and search in enhanced_entry.business_definition.lower()
                    if not (name_match or business_match or desc_match):
                        continue
                
                # Apply trust_tier filter (enhanced dictionary only)
                if trust_tier:
                    if not enhanced_entry or enhanced_entry.trust_tier != trust_tier:
                        continue
                
                # Apply business_domain filter (enhanced dictionary only)
                if business_domain:
                    if not enhanced_entry or enhanced_entry.business_domain != business_domain:
                        continue
                
                if has_dictionary:
                    in_dictionary += 1
                    asset_data = {
                        "schema": t.schema,
                        "table": t.name,
                        "type": t.type,
                        "row_count": t.row_estimate,
                        "in_dictionary": True,
                        "dictionary_sources": []
                    }
                    
                    if enhanced_entry:
                        asset_data["dictionary_sources"].append("dictionary_assets")
                        asset_data["business_name"] = enhanced_entry.business_name
                        asset_data["description"] = (enhanced_entry.business_definition or "")[:200]
                        asset_data["domain"] = enhanced_entry.business_domain
                        asset_data["owner"] = enhanced_entry.owner
                        asset_data["trust_tier"] = enhanced_entry.trust_tier
                        asset_data["trust_score"] = enhanced_entry.trust_score
                        asset_data["tags"] = enhanced_entry.tags or []
                    
                    if original_entry:
                        asset_data["dictionary_sources"].append("data_dictionary_entries")
                        asset_data["columns_documented"] = original_entry["columns_documented"]
                        if not enhanced_entry:
                            # Only original dictionary - add basic info
                            asset_data["note"] = f"Has {original_entry['columns_documented']} column definitions"
                    
                    assets.append(asset_data)
                else:
                    not_in_dictionary += 1
                    # Only include non-dictionary tables if not filtering by dictionary-only fields
                    if not trust_tier and not business_domain:
                        assets.append({
                            "schema": t.schema,
                            "table": t.name,
                            "type": t.type,
                            "row_count": t.row_estimate,
                            "in_dictionary": False,
                            "dictionary_sources": [],
                            "business_name": None,
                            "description": None,
                            "trust_tier": "not_curated",
                            "note": "Not yet in data dictionary"
                        })
            
            # Also add any original dict entries for tables not in raw_tables
            for key, orig in original_lookup.items():
                if key not in processed_keys:
                    in_dictionary += 1
                    assets.append({
                        "schema": orig["schema"],
                        "table": orig["table"],
                        "type": "table",
                        "row_count": None,
                        "in_dictionary": True,
                        "dictionary_sources": ["data_dictionary_entries"],
                        "columns_documented": orig["columns_documented"],
                        "note": f"Has {orig['columns_documented']} column definitions (table not in current connection)"
                    })
            
            # Sort: dictionary entries first (by columns_documented or trust_score), then non-dictionary
            assets.sort(key=lambda x: (
                0 if x.get("in_dictionary") else 1,
                -(x.get("columns_documented") or 0),
                -(x.get("trust_score") or 0)
            ))
            
            # Build summary
            total = len(assets)
            if trust_tier or business_domain:
                summary = f"Found {total} assets matching filters"
                if trust_tier:
                    summary += f" (trust_tier='{trust_tier}')"
                if business_domain:
                    summary += f" (domain='{business_domain}')"
            else:
                summary = f"Found {total} tables in {schema} schema: {in_dictionary} have data dictionary entries, {not_in_dictionary} not yet documented"
            
            return {
                "success": True,
                "data": {
                    "assets": assets[:limit],
                    "total": total,
                    "in_dictionary": in_dictionary,
                    "not_in_dictionary": not_in_dictionary,
                    "tables_with_column_definitions": len(original_lookup),
                    "tables_with_enhanced_metadata": len(enhanced_lookup),
                    "summary": summary
                }
            }
        except Exception as e:
            logger.error(f"discover_assets error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_documented_tables(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List all tables that have data dictionary documentation."""
        try:
            schema = tool_input.get("schema", "public")
            include_details = tool_input.get("include_column_details", True)
            
            # Query the data_dictionary_entries table for documented tables
            query = session.exec(
                select(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name,
                    func.count(DataDictionaryEntry.id).label("column_count"),
                    func.min(DataDictionaryEntry.created_at).label("first_documented"),
                    func.max(DataDictionaryEntry.updated_at).label("last_updated")
                ).where(
                    DataDictionaryEntry.schema_name == schema,
                    DataDictionaryEntry.is_active == True
                ).group_by(
                    DataDictionaryEntry.schema_name,
                    DataDictionaryEntry.table_name
                ).order_by(
                    DataDictionaryEntry.table_name
                )
            ).all()
            
            documented_tables = []
            for row in query:
                table_info = {
                    "schema": row.schema_name,
                    "table": row.table_name,
                    "columns_documented": row.column_count,
                    "first_documented": row.first_documented.isoformat() if row.first_documented else None,
                    "last_updated": row.last_updated.isoformat() if row.last_updated else None
                }
                
                if include_details:
                    # Get sample column definitions for this table
                    sample_columns = session.exec(
                        select(DataDictionaryEntry).where(
                            DataDictionaryEntry.schema_name == row.schema_name,
                            DataDictionaryEntry.table_name == row.table_name,
                            DataDictionaryEntry.is_active == True
                        ).limit(5)
                    ).all()
                    
                    table_info["sample_columns"] = [
                        {
                            "column": col.column_name,
                            "business_name": col.business_name,
                            "description": (col.business_description or "")[:100]
                        }
                        for col in sample_columns
                    ]
                
                documented_tables.append(table_info)
            
            return {
                "success": True,
                "data": {
                    "documented_tables": documented_tables,
                    "total_tables": len(documented_tables),
                    "total_columns_documented": sum(t["columns_documented"] for t in documented_tables),
                    "schema": schema,
                    "summary": f"Found {len(documented_tables)} tables with data dictionary documentation in {schema} schema, covering a total of {sum(t['columns_documented'] for t in documented_tables)} column definitions"
                }
            }
        except Exception as e:
            logger.error(f"list_documented_tables error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_discover_relationships(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute discover_relationships tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input.get("schema")
            table = tool_input.get("table")
            
            relationships = []
            
            if schema and table:
                try:
                    rels = dict_service.get_relationships_for_table(
                        session, connection_id, schema, table
                    )
                    for rel in rels:
                        # Handle both old (source_schema) and new (left_ref) model structures
                        if hasattr(rel, 'source_schema'):
                            relationships.append({
                                "source": f"{rel.source_schema}.{rel.source_table}.{rel.source_column}",
                                "target": f"{rel.target_schema}.{rel.target_table}.{rel.target_column}",
                                "cardinality": rel.cardinality,
                                "confidence": getattr(rel, 'confidence', None)
                            })
                        elif hasattr(rel, 'left_ref') and rel.left_ref:
                            left = rel.left_ref
                            right = rel.right_ref or {}
                            relationships.append({
                                "source": f"{left.get('schema', '')}.{left.get('table', '')}.{left.get('column', '')}",
                                "target": f"{right.get('schema', '')}.{right.get('table', '')}.{right.get('column', '')}",
                                "cardinality": rel.cardinality,
                                "confidence": rel.confidence_score
                            })
                except Exception as e:
                    logger.warning(f"Could not get relationships for table: {e}")
            else:
                # Get all relationships from semantics model
                from ..data_explorer.dictionary_semantics_models import DictionaryRelationship
                rels = list(session.exec(select(DictionaryRelationship).limit(tool_input.get("limit", 50))).all())
                
                for rel in rels:
                    left = rel.left_ref or {}
                    right = rel.right_ref or {}
                    relationships.append({
                        "source": f"{left.get('schema', '')}.{left.get('table', '')}.{left.get('column', '')}",
                        "target": f"{right.get('schema', '')}.{right.get('table', '')}.{right.get('column', '')}",
                        "type": rel.relationship_type,
                        "cardinality": rel.cardinality,
                        "status": rel.status,
                        "confidence": rel.confidence_score
                    })
            
            return {
                "success": True,
                "data": {
                    "relationships": relationships,
                    "count": len(relationships),
                    "message": f"Found {len(relationships)} relationships" + (f" for {schema}.{table}" if table else "")
                }
            }
        except Exception as e:
            logger.error(f"discover_relationships error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_asset_documentation(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_asset_documentation tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            result_data = {
                "table": f"{schema}.{table}",
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_assets - table-level)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                result_data["sources"].append("dictionary_assets")
                result_data["enhanced_dictionary"] = {
                    "business_name": asset.business_name,
                    "business_definition": asset.business_definition,
                    "business_domain": asset.business_domain,
                    "grain": asset.grain or asset.row_meaning,
                    "owner": asset.owner,
                    "steward": asset.steward,
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "tags": asset.tags or [],
                    "known_issues": asset.known_issues,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml
                }
            
            # Check 2: Original dictionary (data_dictionary_entries - column-level)
            # Try with connection_id as database_name first, then "default"
            original_entries = original_dict_service.get_dictionary_for_tables(
                session, connection_id, schema, [table], active_only=True
            )
            if not original_entries:
                original_entries = original_dict_service.get_dictionary_for_tables(
                    session, "default", schema, [table], active_only=True
                )
            if not original_entries:
                # Try with "nexdata" as database_name
                original_entries = original_dict_service.get_dictionary_for_tables(
                    session, "nexdata", schema, [table], active_only=True
                )
            
            if original_entries:
                result_data["sources"].append("data_dictionary_entries")
                result_data["column_definitions"] = [
                    {
                        "column_name": e.column_name,
                        "business_name": e.business_name,
                        "business_description": e.business_description,
                        "technical_description": e.technical_description,
                        "data_type": e.data_type,
                        "examples": e.examples or [],
                        "tags": e.tags or [],
                        "source": e.source,
                        "version": e.version_number
                    }
                    for e in original_entries
                ]
                result_data["column_count_documented"] = len(original_entries)
            
            # Check 3: Raw database structure if nothing else found
            if not result_data["sources"]:
                try:
                    columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                    tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                    table_info = next((t for t in tables if t.name == table), None)
                    
                    if columns:
                        result_data["sources"].append("database")
                        result_data["raw_structure"] = {
                            "row_count": table_info.row_estimate if table_info else None,
                            "type": table_info.type if table_info else "table",
                            "column_count": len(columns),
                            "columns": [
                                {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                                for c in columns
                            ]
                        }
                        result_data["message"] = "Table found in database but no dictionary documentation exists."
                    else:
                        return {"success": False, "error": f"Table {schema}.{table} not found"}
                except Exception as e:
                    return {"success": False, "error": f"Table {schema}.{table} not found: {str(e)}"}
            
            # Add summary
            if "data_dictionary_entries" in result_data["sources"]:
                result_data["summary"] = f"Found {len(result_data.get('column_definitions', []))} column definitions in data dictionary"
            elif "dictionary_assets" in result_data["sources"]:
                result_data["summary"] = "Found table-level documentation in enhanced dictionary"
            else:
                result_data["summary"] = "Table exists but no documentation found"
            
            return {"success": True, "data": result_data}
        except Exception as e:
            logger.error(f"get_asset_documentation error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_field_documentation(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_field_documentation tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            result_data = {
                "table": f"{schema}.{table}",
                "column": column,
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_fields)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                fields = dict_service.get_fields_for_asset(session, asset.id)
                for f in fields:
                    if f.column_name.lower() == column.lower():
                        result_data["sources"].append("dictionary_fields")
                        result_data["enhanced"] = {
                            "column_name": f.column_name,
                            "business_name": f.business_name,
                            "business_definition": f.business_definition,
                            "data_type": f.data_type,
                            "nullable": f.is_nullable,
                            "entity_role": f.entity_role,
                            "tags": f.tags or [],
                            "known_issues": f.known_issues,
                            "trust_tier": f.trust_tier,
                            "trust_score": f.trust_score
                        }
                        break
            
            # Check 2: Original dictionary (data_dictionary_entries)
            # Try multiple database_name variations
            for db_name in [connection_id, "default", "nexdata"]:
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                
                if entry:
                    result_data["sources"].append("data_dictionary_entries")
                    result_data["original"] = {
                        "column_name": entry.column_name,
                        "business_name": entry.business_name,
                        "business_description": entry.business_description,
                        "technical_description": entry.technical_description,
                        "data_type": entry.data_type,
                        "examples": entry.examples or [],
                        "tags": entry.tags or [],
                        "source": entry.source,
                        "version": entry.version_number
                    }
                    break
            
            # Check 3: Raw column info if no dictionary entry found
            if not result_data["sources"]:
                try:
                    columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                    for c in columns:
                        if c.name.lower() == column.lower():
                            result_data["sources"].append("database")
                            result_data["raw"] = {
                                "column_name": c.name,
                                "data_type": c.data_type,
                                "nullable": c.is_nullable,
                                "default": c.default,
                                "position": c.ordinal_position
                            }
                            result_data["message"] = "Column found but no dictionary documentation exists."
                            break
                    
                    if not result_data["sources"]:
                        return {"success": False, "error": f"Column {column} not found in {schema}.{table}"}
                except Exception as e:
                    return {"success": False, "error": f"Could not get column info: {str(e)}"}
            
            # Merge results for best available data
            if "data_dictionary_entries" in result_data["sources"]:
                orig = result_data.get("original", {})
                result_data["best"] = {
                    "column_name": orig.get("column_name"),
                    "business_name": orig.get("business_name"),
                    "description": orig.get("business_description"),
                    "technical_description": orig.get("technical_description"),
                    "data_type": orig.get("data_type"),
                    "examples": orig.get("examples", []),
                    "tags": orig.get("tags", [])
                }
            elif "dictionary_fields" in result_data["sources"]:
                enh = result_data.get("enhanced", {})
                result_data["best"] = {
                    "column_name": enh.get("column_name"),
                    "business_name": enh.get("business_name"),
                    "description": enh.get("business_definition"),
                    "data_type": enh.get("data_type"),
                    "entity_role": enh.get("entity_role"),
                    "tags": enh.get("tags", [])
                }
            
            return {"success": True, "data": result_data}
        except Exception as e:
            logger.error(f"get_field_documentation error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_check_data_quality(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute check_data_quality tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            
            if not asset:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            return {
                "success": True,
                "data": {
                    "table": f"{schema}.{table}",
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml,
                    "known_issues": asset.known_issues,
                    "issue_tags": asset.issue_tags or [],
                    "summary": f"{asset.trust_tier.upper()} tier (score: {asset.trust_score}/100)"
                }
            }
        except Exception as e:
            logger.error(f"check_data_quality error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_find_trusted_data(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute find_trusted_data tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            use_case = tool_input["use_case"]
            min_tier = tool_input.get("min_trust_tier", "trusted")
            
            # Get all assets from dictionary
            results, total = dict_service.search_assets(
                session=session,
                connection_id=connection_id,
                business_domain=tool_input.get("business_domain"),
                limit=200,
                offset=0
            )
            
            # Check if dictionary is empty
            if total == 0:
                return {
                    "success": True,
                    "data": {
                        "assets": [],
                        "count": 0,
                        "use_case": use_case,
                        "message": (
                            "No assets found in the data dictionary. "
                            "The dictionary needs to be synced and assets need to be curated with trust tiers. "
                            "Use list_tables to see raw database tables."
                        )
                    }
                }
            
            # Filter by trust tier and use case
            tier_order = {"deprecated": 0, "experimental": 1, "trusted": 2, "certified": 3}
            min_tier_level = tier_order.get(min_tier, 2)
            
            qualified = []
            for asset in results:
                tier_level = tier_order.get(asset.trust_tier, 1)
                if tier_level < min_tier_level:
                    continue
                
                if use_case == "reporting" and not asset.approved_for_reporting:
                    continue
                if use_case == "ml" and not asset.approved_for_ml:
                    continue
                
                qualified.append({
                    "schema": asset.schema_name,
                    "table": asset.table_name,
                    "business_name": asset.business_name,
                    "trust_tier": asset.trust_tier,
                    "trust_score": asset.trust_score,
                    "owner": asset.owner
                })
            
            # Sort by trust score
            qualified.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
            
            # Build message
            if qualified:
                message = f"Found {len(qualified)} assets qualified for {use_case}"
            else:
                message = (
                    f"No assets found with trust tier '{min_tier}' or higher that are approved for {use_case}. "
                    f"Found {total} total assets in dictionary, but none meet the criteria."
                )
            
            return {
                "success": True,
                "data": {
                    "assets": qualified[:tool_input.get("limit", 25)],
                    "count": len(qualified),
                    "use_case": use_case,
                    "total_in_dictionary": total,
                    "message": message
                }
            }
        except Exception as e:
            logger.error(f"find_trusted_data error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_table(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_table tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            explanation = {
                "full_name": f"{schema}.{table}",
                "sources": []
            }
            
            # Check 1: Enhanced dictionary (dictionary_assets)
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            if asset:
                explanation["sources"].append("dictionary_assets")
                context = dict_service.get_dictionary_context(
                    session=session,
                    connection_id=connection_id,
                    schema_name=schema,
                    table_name=table
                )
                
                explanation["identity"] = {
                    "business_name": context["table"].get("business_name"),
                    "description": context["table"].get("definition"),
                    "domain": context["table"].get("domain")
                }
                explanation["grain"] = {
                    "description": context["table"].get("grain"),
                    "row_count": context["table"].get("row_count")
                }
                explanation["ownership"] = {
                    "owner": asset.owner,
                    "steward": asset.steward
                }
                explanation["trust"] = {
                    "tier": asset.trust_tier,
                    "score": asset.trust_score,
                    "approved_for_reporting": asset.approved_for_reporting,
                    "approved_for_ml": asset.approved_for_ml,
                    "known_issues": asset.known_issues
                }
                explanation["relationships"] = context.get("relationships", [])
            
            # Check 2: Original dictionary (data_dictionary_entries - column-level)
            original_entries = None
            for db_name in [connection_id, "default", "nexdata"]:
                entries = original_dict_service.get_dictionary_for_tables(
                    session, db_name, schema, [table], active_only=True
                )
                if entries:
                    original_entries = entries
                    break
            
            if original_entries:
                explanation["sources"].append("data_dictionary_entries")
                explanation["column_definitions"] = [
                    {
                        "column_name": e.column_name,
                        "business_name": e.business_name,
                        "description": e.business_description,
                        "technical_description": e.technical_description,
                        "data_type": e.data_type,
                        "examples": e.examples or [],
                        "tags": e.tags or []
                    }
                    for e in original_entries
                ]
                explanation["documented_columns"] = len(original_entries)
            
            # Check 3: Raw database structure
            try:
                columns = DataExplorerService.get_columns(schema=schema, table=table, db_id=connection_id)
                tables = DataExplorerService.get_tables(schema=schema, db_id=connection_id)
                table_info = next((t for t in tables if t.name == table), None)
                
                if columns:
                    explanation["sources"].append("database")
                    explanation["structure"] = {
                        "type": table_info.type if table_info else "table",
                        "row_count": table_info.row_estimate if table_info else None,
                        "total_columns": len(columns)
                    }
                    
                    # If no dictionary, include all columns
                    if "data_dictionary_entries" not in explanation["sources"]:
                        explanation["columns"] = [
                            {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                            for c in columns
                        ]
                        
                        # Infer key columns from naming
                        key_columns = []
                        for col in columns:
                            name_lower = col.name.lower()
                            if name_lower == 'id' or name_lower.endswith('_id'):
                                key_columns.append({
                                    "name": col.name,
                                    "type": col.data_type,
                                    "inferred_role": "identifier" if name_lower == 'id' else "possible_foreign_key"
                                })
                        if key_columns:
                            explanation["inferred_keys"] = key_columns
            except Exception as e:
                logger.warning(f"Could not get raw structure: {e}")
            
            # Generate summary
            if not explanation["sources"]:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            if "data_dictionary_entries" in explanation["sources"]:
                doc_count = explanation.get("documented_columns", 0)
                total_count = explanation.get("structure", {}).get("total_columns", doc_count)
                explanation["summary"] = f"Found {doc_count} column definitions in data dictionary (out of {total_count} total columns)"
            elif "dictionary_assets" in explanation["sources"]:
                explanation["summary"] = "Found in enhanced dictionary with table-level documentation"
            else:
                explanation["summary"] = "Table exists in database but has no dictionary documentation"
            
            return {"success": True, "data": explanation}
        except Exception as e:
            logger.error(f"explain_table error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_grain(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_grain tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            schema = tool_input["schema"]
            table = tool_input["table"]
            
            asset = dict_service.get_asset_by_table(session, connection_id, schema, table)
            
            if not asset:
                return {"success": False, "error": f"Table {schema}.{table} not found"}
            
            # Get fields to find primary key
            fields = dict_service.get_fields_for_asset(session, asset.id)
            primary_key = [f.column_name for f in fields if f.entity_role == "primary_identifier"]
            
            grain_description = asset.grain or asset.row_meaning
            
            return {
                "success": True,
                "data": {
                    "table": f"{schema}.{table}",
                    "grain_description": grain_description,
                    "primary_key": primary_key or None,
                    "aggregation_guidance": (
                        f"Each row represents: {grain_description}. Aggregate accordingly."
                        if grain_description else
                        "Grain not documented. Review table structure before aggregating."
                    )
                }
            }
        except Exception as e:
            logger.error(f"explain_grain error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_explain_join(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute explain_join tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            left_schema = tool_input["left_schema"]
            left_table = tool_input["left_table"]
            right_schema = tool_input["right_schema"]
            right_table = tool_input["right_table"]
            
            # Try to get relationships for left table
            try:
                rels = dict_service.get_relationships_for_table(
                    session, connection_id, left_schema, left_table
                )
            except Exception as e:
                logger.warning(f"Could not get relationships: {e}")
                rels = []
            
            # Find direct relationship - handle both model structures
            direct_rel = None
            left_col = None
            right_col = None
            
            for rel in rels:
                # Try old model structure (source_schema, source_table, etc.)
                if hasattr(rel, 'source_schema') and hasattr(rel, 'target_schema'):
                    if (rel.target_schema == right_schema and rel.target_table == right_table):
                        direct_rel = rel
                        left_col = rel.source_column
                        right_col = rel.target_column
                        break
                    if (rel.source_schema == right_schema and rel.source_table == right_table):
                        direct_rel = rel
                        left_col = rel.target_column
                        right_col = rel.source_column
                        break
                # Try new model structure (left_ref, right_ref)
                elif hasattr(rel, 'left_ref') and rel.left_ref:
                    left = rel.left_ref
                    right = rel.right_ref or {}
                    if (right.get('schema') == right_schema and right.get('table') == right_table):
                        direct_rel = rel
                        left_col = left.get('column')
                        right_col = right.get('column')
                        break
                    if (left.get('schema') == right_schema and left.get('table') == right_table):
                        direct_rel = rel
                        left_col = right.get('column')
                        right_col = left.get('column')
                        break
            
            if direct_rel and left_col and right_col:
                warnings = []
                cardinality = direct_rel.cardinality
                if cardinality == "one_to_many":
                    warnings.append("1:N join - aggregations on the 'one' side may cause fanout")
                elif cardinality == "many_to_many":
                    warnings.append("N:M join - use with caution, consider aggregating first")
                
                return {
                    "success": True,
                    "data": {
                        "can_join": True,
                        "join_type": "direct",
                        "join_columns": {"left": left_col, "right": right_col},
                        "cardinality": cardinality,
                        "warnings": warnings,
                        "example_sql": f"""SELECT *
FROM {left_schema}.{left_table} l
LEFT JOIN {right_schema}.{right_table} r
  ON l.{left_col} = r.{right_col}"""
                    }
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "can_join": False,
                        "message": f"No direct relationship found between {left_schema}.{left_table} and {right_schema}.{right_table}",
                        "suggestion": "Check table structure with get_table_info or use discover_relationships to explore connections"
                    }
                }
        except Exception as e:
            logger.error(f"explain_join error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_search_dictionary(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute search_dictionary tool."""
        try:
            connection_id = tool_input.get("connection_id", "default")
            query = tool_input["query"]
            scope = tool_input.get("scope", "all")
            schema = tool_input.get("schema")
            limit = tool_input.get("limit", 20)
            
            results = []
            
            # Search assets (tables)
            if scope in ("all", "tables", "definitions"):
                assets, _ = dict_service.search_assets(
                    session=session,
                    connection_id=connection_id,
                    schema_name=schema,
                    search_term=query,
                    limit=limit
                )
                
                for asset in assets:
                    relevance = "high" if query.lower() in (asset.table_name or "").lower() else "medium"
                    results.append({
                        "match_type": "table",
                        "schema": asset.schema_name,
                        "table": asset.table_name,
                        "business_name": asset.business_name,
                        "description": (asset.business_definition or "")[:150],
                        "relevance": relevance
                    })
            
            # Search fields (columns) - would need additional service method
            # For now, just return table results
            
            # Sort by relevance
            relevance_order = {"high": 0, "medium": 1, "low": 2}
            results.sort(key=lambda x: relevance_order.get(x.get("relevance", "low"), 2))
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "results": results[:limit],
                    "count": len(results)
                }
            }
        except Exception as e:
            logger.error(f"search_dictionary error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_preview_dictionary_update(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Preview proposed changes to a dictionary entry before saving."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            # Get current published/active entry OR any existing draft
            current_entry = None
            draft_entry = None
            db_name = "default"
            
            for try_db_name in ["default", "nexdata"]:
                # Check for active/published entry
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == try_db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                if entry:
                    current_entry = entry
                    db_name = try_db_name
                
                # Check for existing draft
                draft = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == try_db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.state == "draft"
                    )
                ).first()
                if draft:
                    draft_entry = draft
                    db_name = try_db_name
                
                if current_entry or draft_entry:
                    break
            
            # Use draft if exists, otherwise current
            base_entry = draft_entry or current_entry
            
            # Build the preview
            current_values = {}
            if base_entry:
                current_values = {
                    "business_name": base_entry.business_name,
                    "business_description": base_entry.business_description,
                    "technical_description": base_entry.technical_description,
                    "examples": base_entry.examples or [],
                    "tags": base_entry.tags or [],
                    "version": base_entry.version_number,
                    "state": base_entry.state,
                    "source": base_entry.source,
                    "entry_id": base_entry.id
                }
            else:
                current_values = {
                    "business_name": None,
                    "business_description": None,
                    "technical_description": None,
                    "examples": [],
                    "tags": [],
                    "version": 0,
                    "state": None,
                    "source": None,
                    "entry_id": None
                }
            
            # Build proposed values and track changes
            proposed_values = {}
            changes = []
            fields_to_update = ["business_name", "business_description", "technical_description", "examples", "tags"]
            
            for field in fields_to_update:
                if field in tool_input and tool_input[field] is not None:
                    proposed_values[field] = tool_input[field]
                    if tool_input[field] != current_values.get(field):
                        changes.append({
                            "field": field,
                            "current": current_values.get(field),
                            "proposed": tool_input[field]
                        })
                else:
                    proposed_values[field] = current_values.get(field)
            
            if not changes:
                return {
                    "success": True,
                    "data": {
                        "message": "No changes detected. The proposed values are the same as the current values.",
                        "column": f"{schema}.{table}.{column}",
                        "current_state": current_values.get("state"),
                        "current": current_values
                    }
                }
            
            workflow_info = "Changes will create a draft. Use auto_publish=true to publish immediately, or submit_for_approval for review workflow."
            if draft_entry:
                workflow_info = f"An existing draft (v{draft_entry.version_number}) will be updated."
            
            return {
                "success": True,
                "data": {
                    "message": "Please review the proposed changes below. Say 'confirm' or 'save' to apply them.",
                    "column": f"{schema}.{table}.{column}",
                    "is_new_entry": base_entry is None,
                    "has_existing_draft": draft_entry is not None,
                    "current_version": current_values.get("version", 0),
                    "current_state": current_values.get("state"),
                    "changes": changes,
                    "current": current_values,
                    "proposed": proposed_values,
                    "workflow": workflow_info,
                    "action_required": "User must confirm to save these changes"
                }
            }
        except Exception as e:
            logger.error(f"preview_dictionary_update error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_save_dictionary_update(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Save a dictionary update - creates/updates a draft, optionally auto-publishes."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            version_notes = tool_input.get("version_notes", "Updated via chat")
            auto_publish = tool_input.get("auto_publish", True)  # Default to auto-publish for simplicity
            
            # Find current entry and any existing draft
            current_entry = None
            draft_entry = None
            db_name = "default"
            
            for try_db_name in ["default", "nexdata"]:
                # Check for active/published entry
                entry = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == try_db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.is_active == True
                    )
                ).first()
                if entry:
                    current_entry = entry
                    db_name = try_db_name
                
                # Check for existing draft
                draft = session.exec(
                    select(DataDictionaryEntry).where(
                        DataDictionaryEntry.database_name == try_db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column,
                        DataDictionaryEntry.state == "draft"
                    )
                ).first()
                if draft:
                    draft_entry = draft
                    db_name = try_db_name
                
                if current_entry or draft_entry:
                    break
            
            # Determine base entry for values
            base_entry = draft_entry or current_entry
            
            if draft_entry:
                # Update existing draft
                if "business_name" in tool_input:
                    draft_entry.business_name = tool_input["business_name"]
                if "business_description" in tool_input:
                    draft_entry.business_description = tool_input["business_description"]
                if "technical_description" in tool_input:
                    draft_entry.technical_description = tool_input["technical_description"]
                if "examples" in tool_input:
                    draft_entry.examples = tool_input["examples"]
                if "tags" in tool_input:
                    draft_entry.tags = tool_input["tags"]
                
                draft_entry.source = "human_edited"
                draft_entry.version_notes = version_notes
                draft_entry.updated_at = datetime.utcnow()
                session.add(draft_entry)
                session.commit()
                session.refresh(draft_entry)
                
                result_entry = draft_entry
                
            elif current_entry:
                # Create new draft from published entry
                from sqlalchemy import func as sqla_func
                max_version = session.exec(
                    select(sqla_func.max(DataDictionaryEntry.version_number)).where(
                        DataDictionaryEntry.database_name == db_name,
                        DataDictionaryEntry.schema_name == schema,
                        DataDictionaryEntry.table_name == table,
                        DataDictionaryEntry.column_name == column
                    )
                ).first()
                
                new_entry = DataDictionaryEntry(
                    database_name=db_name,
                    schema_name=schema,
                    table_name=table,
                    column_name=column,
                    version_number=(max_version or 0) + 1,
                    is_active=False,  # Draft is not active until published
                    state="draft",
                    version_notes=version_notes,
                    business_name=tool_input.get("business_name", current_entry.business_name),
                    business_description=tool_input.get("business_description", current_entry.business_description),
                    technical_description=tool_input.get("technical_description", current_entry.technical_description),
                    data_type=current_entry.data_type,
                    examples=tool_input.get("examples", current_entry.examples),
                    tags=tool_input.get("tags", current_entry.tags),
                    source="human_edited"
                )
                session.add(new_entry)
                session.commit()
                session.refresh(new_entry)
                result_entry = new_entry
                
            else:
                # Create brand new entry as draft
                new_entry = DataDictionaryEntry(
                    database_name=db_name,
                    schema_name=schema,
                    table_name=table,
                    column_name=column,
                    version_number=1,
                    is_active=False,  # Draft is not active until published
                    state="draft",
                    version_notes=version_notes,
                    business_name=tool_input.get("business_name"),
                    business_description=tool_input.get("business_description"),
                    technical_description=tool_input.get("technical_description"),
                    data_type=tool_input.get("data_type"),
                    examples=tool_input.get("examples", []),
                    tags=tool_input.get("tags", []),
                    source="human_edited"
                )
                session.add(new_entry)
                session.commit()
                session.refresh(new_entry)
                result_entry = new_entry
            
            # Auto-publish if requested
            if auto_publish and result_entry.state == "draft":
                try:
                    result_entry = original_dict_service.publish_draft_directly(
                        session, result_entry.id, f"Auto-published: {version_notes}"
                    )
                    state_msg = "published"
                except Exception as pub_err:
                    logger.warning(f"Auto-publish failed: {pub_err}")
                    state_msg = "draft (auto-publish failed)"
            else:
                state_msg = result_entry.state
            
            return {
                "success": True,
                "data": {
                    "message": f"Successfully saved dictionary update for {schema}.{table}.{column}",
                    "column": f"{schema}.{table}.{column}",
                    "entry_id": result_entry.id,
                    "version": result_entry.version_number,
                    "state": state_msg,
                    "is_active": result_entry.is_active,
                    "updated_at": result_entry.updated_at.isoformat() if result_entry.updated_at else None,
                    "saved_values": {
                        "business_name": result_entry.business_name,
                        "business_description": result_entry.business_description,
                        "technical_description": result_entry.technical_description,
                        "examples": result_entry.examples or [],
                        "tags": result_entry.tags or []
                    },
                    "next_steps": "Entry is now active." if result_entry.is_active else "Use publish_dictionary_entry or submit_for_approval to make this active."
                }
            }
        except Exception as e:
            logger.error(f"save_dictionary_update error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_column_history(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get version history for a column's dictionary entry."""
        try:
            schema = tool_input["schema"]
            table = tool_input["table"]
            column = tool_input["column"]
            
            # Try to find versions with different database_name values
            versions = []
            for db_name in ["default", "nexdata"]:
                db_versions = original_dict_service.get_column_versions(
                    session=session,
                    database_name=db_name,
                    schema_name=schema,
                    table_name=table,
                    column_name=column
                )
                if db_versions:
                    versions = db_versions
                    break
            
            if not versions:
                return {
                    "success": True,
                    "data": {
                        "message": f"No version history found for {schema}.{table}.{column}",
                        "column": f"{schema}.{table}.{column}",
                        "versions": []
                    }
                }
            
            version_history = []
            for v in versions:
                version_history.append({
                    "entry_id": v.id,
                    "version": v.version_number,
                    "state": v.state,
                    "is_active": v.is_active,
                    "source": v.source,
                    "business_name": v.business_name,
                    "business_description": (v.business_description or "")[:100] + ("..." if v.business_description and len(v.business_description) > 100 else ""),
                    "version_notes": v.version_notes,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "updated_at": v.updated_at.isoformat() if v.updated_at else None
                })
            
            # Summarize states
            drafts = [v for v in version_history if v["state"] == "draft"]
            pending = [v for v in version_history if v["state"] == "pending_approval"]
            published = [v for v in version_history if v["state"] == "published"]
            
            return {
                "success": True,
                "data": {
                    "column": f"{schema}.{table}.{column}",
                    "total_versions": len(versions),
                    "summary": {
                        "drafts": len(drafts),
                        "pending_approval": len(pending),
                        "published": len(published)
                    },
                    "versions": version_history,
                    "tip": "Use rollback_column_version with entry_id to restore, or publish_dictionary_entry to publish a draft"
                }
            }
        except Exception as e:
            logger.error(f"get_column_history error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_rollback_column_version(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Rollback a column to a previous version."""
        try:
            entry_id = tool_input["entry_id"]
            
            # Get the entry to rollback to
            target_entry = session.get(DataDictionaryEntry, entry_id)
            if not target_entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            # Use the existing activate_version function
            activated = original_dict_service.activate_version(session, entry_id)
            
            return {
                "success": True,
                "data": {
                    "message": f"Successfully rolled back {target_entry.schema_name}.{target_entry.table_name}.{target_entry.column_name} to version {activated.version_number}",
                    "column": f"{target_entry.schema_name}.{target_entry.table_name}.{target_entry.column_name}",
                    "restored_version": activated.version_number,
                    "state": activated.state,
                    "restored_values": {
                        "business_name": activated.business_name,
                        "business_description": activated.business_description,
                        "technical_description": activated.technical_description,
                        "examples": activated.examples,
                        "tags": activated.tags
                    }
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"rollback_column_version error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_publish_dictionary_entry(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Publish a draft dictionary entry directly."""
        try:
            entry_id = tool_input["entry_id"]
            notes = tool_input.get("notes", "Published via chat")
            
            entry = session.get(DataDictionaryEntry, entry_id)
            if not entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            if entry.state != "draft":
                return {"success": False, "error": f"Can only publish draft entries. Current state: {entry.state}"}
            
            published = original_dict_service.publish_draft_directly(session, entry_id, notes)
            
            return {
                "success": True,
                "data": {
                    "message": f"Successfully published {published.schema_name}.{published.table_name}.{published.column_name}",
                    "entry_id": published.id,
                    "column": f"{published.schema_name}.{published.table_name}.{published.column_name}",
                    "version": published.version_number,
                    "state": published.state,
                    "is_active": published.is_active
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"publish_dictionary_entry error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_submit_for_approval(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a draft entry for approval."""
        try:
            entry_id = tool_input["entry_id"]
            
            entry = session.get(DataDictionaryEntry, entry_id)
            if not entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            if entry.state != "draft":
                return {"success": False, "error": f"Can only submit draft entries. Current state: {entry.state}"}
            
            submitted = original_dict_service.submit_for_approval(session, entry_id)
            
            return {
                "success": True,
                "data": {
                    "message": f"Submitted {submitted.schema_name}.{submitted.table_name}.{submitted.column_name} for approval",
                    "entry_id": submitted.id,
                    "column": f"{submitted.schema_name}.{submitted.table_name}.{submitted.column_name}",
                    "version": submitted.version_number,
                    "state": submitted.state,
                    "next_step": "An approver can now approve or reject this entry using approve_dictionary_entry or reject_dictionary_entry"
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"submit_for_approval error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_pending_approvals(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List all dictionary entries pending approval."""
        try:
            schema_filter = tool_input.get("schema")
            table_filter = tool_input.get("table")
            
            query = select(DataDictionaryEntry).where(
                DataDictionaryEntry.state == "pending_approval"
            )
            
            if schema_filter:
                query = query.where(DataDictionaryEntry.schema_name == schema_filter)
            if table_filter:
                query = query.where(DataDictionaryEntry.table_name == table_filter)
            
            query = query.order_by(
                DataDictionaryEntry.updated_at.desc()
            )
            
            pending_entries = session.exec(query).all()
            
            results = []
            for entry in pending_entries:
                results.append({
                    "entry_id": entry.id,
                    "column": f"{entry.schema_name}.{entry.table_name}.{entry.column_name}",
                    "version": entry.version_number,
                    "business_name": entry.business_name,
                    "business_description": (entry.business_description or "")[:100],
                    "source": entry.source,
                    "submitted_at": entry.updated_at.isoformat() if entry.updated_at else None
                })
            
            return {
                "success": True,
                "data": {
                    "count": len(results),
                    "pending_entries": results,
                    "message": f"Found {len(results)} entries pending approval" if results else "No entries pending approval",
                    "actions": "Use approve_dictionary_entry or reject_dictionary_entry with the entry_id"
                }
            }
        except Exception as e:
            logger.error(f"list_pending_approvals error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_approve_dictionary_entry(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Approve a pending dictionary entry."""
        try:
            entry_id = tool_input["entry_id"]
            notes = tool_input.get("notes")
            
            entry = session.get(DataDictionaryEntry, entry_id)
            if not entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            if entry.state != "pending_approval":
                return {"success": False, "error": f"Can only approve pending entries. Current state: {entry.state}"}
            
            approved = original_dict_service.approve_entry(session, entry_id, notes)
            
            return {
                "success": True,
                "data": {
                    "message": f"Approved and published {approved.schema_name}.{approved.table_name}.{approved.column_name}",
                    "entry_id": approved.id,
                    "column": f"{approved.schema_name}.{approved.table_name}.{approved.column_name}",
                    "version": approved.version_number,
                    "state": approved.state,
                    "is_active": approved.is_active
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"approve_dictionary_entry error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_reject_dictionary_entry(session: Session, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Reject a pending dictionary entry."""
        try:
            entry_id = tool_input["entry_id"]
            reason = tool_input.get("reason", "Rejected via chat")
            
            entry = session.get(DataDictionaryEntry, entry_id)
            if not entry:
                return {"success": False, "error": f"Entry with ID {entry_id} not found"}
            
            if entry.state != "pending_approval":
                return {"success": False, "error": f"Can only reject pending entries. Current state: {entry.state}"}
            
            rejected = original_dict_service.reject_entry(session, entry_id, reason)
            
            return {
                "success": True,
                "data": {
                    "message": f"Rejected {rejected.schema_name}.{rejected.table_name}.{rejected.column_name} - returned to draft",
                    "entry_id": rejected.id,
                    "column": f"{rejected.schema_name}.{rejected.table_name}.{rejected.column_name}",
                    "version": rejected.version_number,
                    "state": rejected.state,
                    "rejection_reason": reason,
                    "next_step": "The entry is now a draft again and can be edited before resubmitting"
                }
            }
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"reject_dictionary_entry error: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # ML DEVELOPMENT TOOL IMPLEMENTATIONS
    # =========================================================================
    
    @staticmethod
    def _get_ml_services():
        """Get ML service instances."""
        from sqlalchemy import create_engine
        from core.config import settings
        from domains.ml_development.service import (
            MLRecipeService, MLRecipeVersionService, MLModelService,
            MLRunService, MLMonitorService, MLSyntheticExampleService
        )
        
        engine = create_engine(settings.database_url)
        return {
            "recipe": MLRecipeService(engine),
            "version": MLRecipeVersionService(engine),
            "model": MLModelService(engine),
            "run": MLRunService(engine),
            "monitor": MLMonitorService(engine),
            "example": MLSyntheticExampleService(engine)
        }
    
    @staticmethod
    def _execute_list_ml_recipes(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List ML recipes."""
        try:
            services = ChatService._get_ml_services()
            
            recipes = services["recipe"].list_recipes(
                model_family=tool_input.get("model_family"),
                level=tool_input.get("level"),
                status=tool_input.get("status"),
                limit=tool_input.get("limit", 25)
            )
            
            # Format for chat display
            formatted = []
            for r in recipes:
                formatted.append({
                    "id": r["id"],
                    "name": r["name"],
                    "model_family": r["model_family"],
                    "level": r["level"],
                    "status": r["status"],
                    "tags": r.get("tags", []),
                    "updated_at": r["updated_at"].isoformat() if r.get("updated_at") else None
                })
            
            # Group by model family for summary
            by_family = {}
            for r in formatted:
                family = r["model_family"]
                if family not in by_family:
                    by_family[family] = 0
                by_family[family] += 1
            
            return {
                "success": True,
                "data": {
                    "recipes": formatted,
                    "total": len(formatted),
                    "by_family": by_family,
                    "summary": f"Found {len(formatted)} ML recipes"
                }
            }
        except Exception as e:
            logger.error(f"list_ml_recipes error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_ml_recipe(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about a specific ML recipe."""
        try:
            services = ChatService._get_ml_services()
            recipe_id = tool_input["recipe_id"]
            
            recipe = services["recipe"].get_recipe(recipe_id)
            if not recipe:
                return {"success": False, "error": f"Recipe {recipe_id} not found"}
            
            # Get versions
            versions = services["version"].list_versions(recipe_id)
            
            return {
                "success": True,
                "data": {
                    "recipe": {
                        "id": recipe["id"],
                        "name": recipe["name"],
                        "model_family": recipe["model_family"],
                        "level": recipe["level"],
                        "status": recipe["status"],
                        "parent_id": recipe.get("parent_id"),
                        "tags": recipe.get("tags", []),
                        "created_at": recipe["created_at"].isoformat() if recipe.get("created_at") else None,
                        "updated_at": recipe["updated_at"].isoformat() if recipe.get("updated_at") else None
                    },
                    "versions_count": len(versions),
                    "latest_version": versions[0]["version_number"] if versions else None
                }
            }
        except Exception as e:
            logger.error(f"get_ml_recipe error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_recipe_versions(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List all versions of an ML recipe."""
        try:
            services = ChatService._get_ml_services()
            recipe_id = tool_input["recipe_id"]
            
            versions = services["version"].list_versions(recipe_id)
            
            formatted = []
            for v in versions:
                formatted.append({
                    "version_id": v["version_id"],
                    "version_number": v["version_number"],
                    "created_by": v.get("created_by"),
                    "change_note": v.get("change_note"),
                    "created_at": v["created_at"].isoformat() if v.get("created_at") else None
                })
            
            return {
                "success": True,
                "data": {
                    "recipe_id": recipe_id,
                    "versions": formatted,
                    "total": len(formatted)
                }
            }
        except Exception as e:
            logger.error(f"list_recipe_versions error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_recipe_version(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific recipe version with manifest."""
        try:
            services = ChatService._get_ml_services()
            version_id = tool_input["version_id"]
            
            version = services["version"].get_version(version_id)
            if not version:
                return {"success": False, "error": f"Version {version_id} not found"}
            
            return {
                "success": True,
                "data": {
                    "version_id": version["version_id"],
                    "recipe_id": version["recipe_id"],
                    "version_number": version["version_number"],
                    "manifest": version.get("manifest_json", {}),
                    "change_note": version.get("change_note"),
                    "created_by": version.get("created_by"),
                    "created_at": version["created_at"].isoformat() if version.get("created_at") else None
                }
            }
        except Exception as e:
            logger.error(f"get_recipe_version error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_ml_models(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List ML models."""
        try:
            services = ChatService._get_ml_services()
            
            models = services["model"].list_models(
                model_family=tool_input.get("model_family"),
                status=tool_input.get("status"),
                limit=tool_input.get("limit", 25)
            )
            
            formatted = []
            for m in models:
                formatted.append({
                    "id": m["id"],
                    "name": m["name"],
                    "model_family": m["model_family"],
                    "status": m["status"],
                    "recipe_id": m["recipe_id"],
                    "owner": m.get("owner"),
                    "updated_at": m["updated_at"].isoformat() if m.get("updated_at") else None
                })
            
            # Count by status
            by_status = {}
            for m in formatted:
                status = m["status"]
                if status not in by_status:
                    by_status[status] = 0
                by_status[status] += 1
            
            return {
                "success": True,
                "data": {
                    "models": formatted,
                    "total": len(formatted),
                    "by_status": by_status,
                    "production_count": by_status.get("production", 0)
                }
            }
        except Exception as e:
            logger.error(f"list_ml_models error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_ml_model(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about a specific ML model."""
        try:
            services = ChatService._get_ml_services()
            model_id = tool_input["model_id"]
            
            model = services["model"].get_model(model_id)
            if not model:
                return {"success": False, "error": f"Model {model_id} not found"}
            
            # Get recipe info
            recipe = services["recipe"].get_recipe(model["recipe_id"])
            
            # Get recent runs for this model
            runs = services["run"].list_runs(model_id=model_id, limit=5)
            
            return {
                "success": True,
                "data": {
                    "model": {
                        "id": model["id"],
                        "name": model["name"],
                        "model_family": model["model_family"],
                        "status": model["status"],
                        "owner": model.get("owner"),
                        "recipe_id": model["recipe_id"],
                        "recipe_version_id": model["recipe_version_id"],
                        "created_at": model["created_at"].isoformat() if model.get("created_at") else None,
                        "updated_at": model["updated_at"].isoformat() if model.get("updated_at") else None
                    },
                    "recipe_name": recipe["name"] if recipe else None,
                    "recent_runs": len(runs),
                    "last_run_status": runs[0]["status"] if runs else None
                }
            }
        except Exception as e:
            logger.error(f"get_ml_model error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_list_ml_runs(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """List ML runs."""
        try:
            services = ChatService._get_ml_services()
            
            runs = services["run"].list_runs(
                model_id=tool_input.get("model_id"),
                recipe_id=tool_input.get("recipe_id"),
                status=tool_input.get("status"),
                limit=tool_input.get("limit", 25)
            )
            
            formatted = []
            for r in runs:
                formatted.append({
                    "id": r["id"],
                    "run_type": r["run_type"],
                    "status": r["status"],
                    "model_id": r.get("model_id"),
                    "recipe_id": r["recipe_id"],
                    "started_at": r["started_at"].isoformat() if r.get("started_at") else None,
                    "finished_at": r["finished_at"].isoformat() if r.get("finished_at") else None,
                    "has_metrics": bool(r.get("metrics_json"))
                })
            
            # Count by status
            by_status = {}
            for r in formatted:
                status = r["status"]
                if status not in by_status:
                    by_status[status] = 0
                by_status[status] += 1
            
            return {
                "success": True,
                "data": {
                    "runs": formatted,
                    "total": len(formatted),
                    "by_status": by_status
                }
            }
        except Exception as e:
            logger.error(f"list_ml_runs error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_ml_run(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get details about a specific ML run."""
        try:
            services = ChatService._get_ml_services()
            run_id = tool_input["run_id"]
            
            run = services["run"].get_run(run_id)
            if not run:
                return {"success": False, "error": f"Run {run_id} not found"}
            
            return {
                "success": True,
                "data": {
                    "run": {
                        "id": run["id"],
                        "run_type": run["run_type"],
                        "status": run["status"],
                        "model_id": run.get("model_id"),
                        "recipe_id": run["recipe_id"],
                        "recipe_version_id": run["recipe_version_id"],
                        "started_at": run["started_at"].isoformat() if run.get("started_at") else None,
                        "finished_at": run["finished_at"].isoformat() if run.get("finished_at") else None
                    },
                    "metrics": run.get("metrics_json", {}),
                    "artifacts": run.get("artifacts_json", {}),
                    "logs": run.get("logs_text", "")[:500] if run.get("logs_text") else None
                }
            }
        except Exception as e:
            logger.error(f"get_ml_run error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_model_monitoring(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get monitoring snapshots for a model."""
        try:
            services = ChatService._get_ml_services()
            model_id = tool_input["model_id"]
            limit = tool_input.get("limit", 10)
            
            snapshots = services["monitor"].list_snapshots(model_id, limit=limit)
            
            if not snapshots:
                return {
                    "success": True,
                    "data": {
                        "model_id": model_id,
                        "message": "No monitoring snapshots found for this model",
                        "snapshots": []
                    }
                }
            
            formatted = []
            for s in snapshots:
                formatted.append({
                    "id": s["id"],
                    "captured_at": s["captured_at"].isoformat() if s.get("captured_at") else None,
                    "performance_metrics": s.get("performance_metrics_json", {}),
                    "drift_metrics": s.get("drift_metrics_json", {}),
                    "alerts": s.get("alerts_json", {})
                })
            
            # Check for any alerts
            has_alerts = any(s.get("alerts") for s in formatted)
            
            return {
                "success": True,
                "data": {
                    "model_id": model_id,
                    "snapshots": formatted,
                    "total": len(formatted),
                    "has_active_alerts": has_alerts,
                    "latest_snapshot": formatted[0] if formatted else None
                }
            }
        except Exception as e:
            logger.error(f"get_model_monitoring error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_synthetic_example(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get synthetic example for a recipe."""
        try:
            services = ChatService._get_ml_services()
            recipe_id = tool_input["recipe_id"]
            
            example = services["example"].get_example(recipe_id)
            if not example:
                return {
                    "success": True,
                    "data": {
                        "recipe_id": recipe_id,
                        "message": "No synthetic example found for this recipe",
                        "example": None
                    }
                }
            
            return {
                "success": True,
                "data": {
                    "recipe_id": recipe_id,
                    "example": {
                        "id": example["id"],
                        "dataset_schema": example.get("dataset_schema_json", {}),
                        "sample_rows": example.get("sample_rows_json", [])[:5],  # Limit rows
                        "example_run": example.get("example_run_json", {}),
                        "created_at": example["created_at"].isoformat() if example.get("created_at") else None
                    }
                }
            }
        except Exception as e:
            logger.error(f"get_synthetic_example error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _execute_get_ml_summary(tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall ML development summary."""
        try:
            services = ChatService._get_ml_services()
            
            # Get counts
            recipes = services["recipe"].list_recipes(limit=500)
            models = services["model"].list_models(limit=500)
            runs = services["run"].list_runs(limit=100)
            
            # Count by status
            recipe_by_status = {}
            for r in recipes:
                status = r["status"]
                recipe_by_status[status] = recipe_by_status.get(status, 0) + 1
            
            model_by_status = {}
            for m in models:
                status = m["status"]
                model_by_status[status] = model_by_status.get(status, 0) + 1
            
            run_by_status = {}
            for r in runs:
                status = r["status"]
                run_by_status[status] = run_by_status.get(status, 0) + 1
            
            # Count by family
            recipe_by_family = {}
            for r in recipes:
                family = r["model_family"]
                recipe_by_family[family] = recipe_by_family.get(family, 0) + 1
            
            # Recent activity
            recent_runs = runs[:5] if runs else []
            
            return {
                "success": True,
                "data": {
                    "summary": {
                        "total_recipes": len(recipes),
                        "total_models": len(models),
                        "total_runs": len(runs),
                        "production_models": model_by_status.get("production", 0),
                        "approved_recipes": recipe_by_status.get("approved", 0)
                    },
                    "recipes_by_status": recipe_by_status,
                    "recipes_by_family": recipe_by_family,
                    "models_by_status": model_by_status,
                    "runs_by_status": run_by_status,
                    "recent_runs": [
                        {
                            "id": r["id"],
                            "run_type": r["run_type"],
                            "status": r["status"],
                            "started_at": r["started_at"].isoformat() if r.get("started_at") else None
                        }
                        for r in recent_runs
                    ]
                }
            }
        except Exception as e:
            logger.error(f"get_ml_summary error: {e}")
            return {"success": False, "error": str(e)}
