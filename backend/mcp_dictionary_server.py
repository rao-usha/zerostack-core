#!/usr/bin/env python3
"""
MCP Data Dictionary Server

This MCP (Model Context Protocol) server exposes Data Dictionary capabilities
as tools that any LLM can use conversationally.

Organized around 5 use cases:
1. DISCOVERY - Find and explore data assets
2. DOCUMENTATION - Read existing business definitions
3. CURATION - View suggested relationships and approval status  
4. ANALYSIS - Query trust tiers, quality, fitness for use
5. UNDERSTANDING - Explain grain, semantics, guarantees

Architecture:
- MCP server acts as thin wrapper around HTTP API
- All business logic lives in FastAPI backend
- Consistent behavior with web UI

Usage:
    python mcp_dictionary_server.py

Environment Variables:
    NEX_API_BASE_URL - Backend API URL (default: http://localhost:8000)
"""

import asyncio
import json
import os
import sys
import logging
import httpx
from typing import Any, Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from domains.data_explorer.mcp_dictionary_tools import (
    ALL_TOOLS,
    get_tool_by_name,
    INTERACTION_MODES
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_dictionary_server")

# Configuration
API_BASE_URL = os.environ.get("NEX_API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = 30.0

# Initialize MCP server
app = Server("nex-data-dictionary")


# =============================================================================
# HTTP CLIENT
# =============================================================================

class DictionaryAPIClient:
    """HTTP client for the Data Dictionary API."""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=API_TIMEOUT)
    
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """Make GET request to API."""
        url = f"{self.base_url}{path}"
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global API client
api_client = DictionaryAPIClient()


# =============================================================================
# RESPONSE FORMATTING
# =============================================================================

def format_response(data: Any, summary: str = None, suggestions: List[str] = None) -> Dict:
    """Format response for LLM consumption."""
    response = {"data": data}
    
    if summary:
        response["summary"] = summary
    
    if suggestions:
        response["suggestions"] = suggestions
    
    return response


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


# =============================================================================
# TOOL IMPLEMENTATIONS - DISCOVERY
# =============================================================================

async def handle_discover_assets(args: Dict) -> Dict:
    """Handle discover_assets tool."""
    params = {
        "connection_id": args.get("connection_id", "default"),
        "limit": args.get("limit", 25),
        "offset": 0
    }
    
    if args.get("search"):
        params["search"] = args["search"]
    if args.get("schema"):
        params["schema"] = args["schema"]
    if args.get("business_domain"):
        params["business_domain"] = args["business_domain"]
    if args.get("trust_tier"):
        params["trust_tier"] = args["trust_tier"]
    
    result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    # Format for LLM
    assets = []
    for asset in result.get("results", []):
        assets.append({
            "schema": asset.get("schema_name"),
            "table": asset.get("table_name"),
            "business_name": asset.get("business_name"),
            "description": truncate_text(asset.get("business_definition", "")),
            "domain": asset.get("business_domain"),
            "owner": asset.get("owner"),
            "trust_tier": asset.get("trust_tier"),
            "trust_score": asset.get("trust_score"),
            "tags": asset.get("tags", []),
            "row_count": asset.get("row_count_estimate")
        })
    
    summary = f"Found {result.get('total', len(assets))} data assets"
    if args.get("search"):
        summary += f" matching '{args['search']}'"
    
    return format_response(
        {"assets": assets, "total": result.get("total", len(assets))},
        summary=summary,
        suggestions=["Use get_asset_documentation to learn more about a specific table"]
    )


async def handle_discover_fields(args: Dict) -> Dict:
    """Handle discover_fields tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    # First get the asset to get its ID
    params = {
        "connection_id": connection_id,
        "schema": schema,
        "search": table,
        "limit": 1
    }
    
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if not asset_result.get("results"):
        return format_response(
            {"error": f"Table {schema}.{table} not found in dictionary"},
            summary=f"Table {schema}.{table} not found"
        )
    
    asset = asset_result["results"][0]
    asset_id = asset["id"]
    
    # Get fields
    fields_result = await api_client.get(f"/data-dictionary/enhanced/assets/{asset_id}/fields")
    
    fields = []
    for field in fields_result:
        fields.append({
            "column": field.get("column_name"),
            "business_name": field.get("business_name"),
            "data_type": field.get("data_type"),
            "nullable": field.get("is_nullable"),
            "role": field.get("entity_role"),
            "position": field.get("ordinal_position")
        })
    
    return format_response(
        {"table": f"{schema}.{table}", "fields": fields},
        summary=f"Table {schema}.{table} has {len(fields)} columns",
        suggestions=["Use get_field_documentation to learn more about a specific column"]
    )


async def handle_discover_relationships(args: Dict) -> Dict:
    """Handle discover_relationships tool."""
    params = {
        "connection_id": args.get("connection_id", "default"),
    }
    
    if args.get("schema"):
        params["schema"] = args["schema"]
    if args.get("table"):
        params["table"] = args["table"]
    
    result = await api_client.get("/data-dictionary/enhanced/relationships", params)
    
    relationships = []
    for rel in result:
        relationships.append({
            "source": f"{rel.get('source_schema')}.{rel.get('source_table')}.{rel.get('source_column')}",
            "target": f"{rel.get('target_schema')}.{rel.get('target_table')}.{rel.get('target_column')}",
            "cardinality": rel.get("cardinality"),
            "confidence": rel.get("confidence"),
        })
    
    summary = f"Found {len(relationships)} relationships"
    if args.get("table"):
        summary += f" for {args.get('schema', '')}.{args['table']}"
    
    return format_response(
        {"relationships": relationships},
        summary=summary
    )


# =============================================================================
# TOOL IMPLEMENTATIONS - DOCUMENTATION
# =============================================================================

async def handle_get_asset_documentation(args: Dict) -> Dict:
    """Handle get_asset_documentation tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    result = await api_client.get(
        f"/data-dictionary/enhanced/context/{connection_id}/{schema}/{table}"
    )
    
    if "error" in result:
        return format_response(
            {"error": result["error"]},
            summary=f"Table {schema}.{table} not found"
        )
    
    table_info = result.get("table", {})
    
    doc = {
        "table": f"{schema}.{table}",
        "business_name": table_info.get("business_name"),
        "business_definition": table_info.get("definition"),
        "business_domain": table_info.get("domain"),
        "grain": table_info.get("grain"),
        "trust_tier": table_info.get("trust_tier"),
        "trust_score": table_info.get("trust_score"),
        "row_count": table_info.get("row_count")
    }
    
    # Try to get full asset for owner/steward info
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if asset_result.get("results"):
        asset = asset_result["results"][0]
        doc["owner"] = asset.get("owner")
        doc["steward"] = asset.get("steward")
        doc["tags"] = asset.get("tags", [])
        doc["known_issues"] = asset.get("known_issues")
    
    return format_response(
        doc,
        summary=f"{table_info.get('business_name', table)}: {truncate_text(table_info.get('definition', 'No description'), 100)}"
    )


async def handle_get_field_documentation(args: Dict) -> Dict:
    """Handle get_field_documentation tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    column = args["column"]
    
    # Get asset ID
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if not asset_result.get("results"):
        return format_response(
            {"error": f"Table {schema}.{table} not found"},
            summary=f"Table not found"
        )
    
    asset_id = asset_result["results"][0]["id"]
    
    # Get fields
    fields_result = await api_client.get(f"/data-dictionary/enhanced/assets/{asset_id}/fields")
    
    # Find the specific field
    field = None
    for f in fields_result:
        if f.get("column_name", "").lower() == column.lower():
            field = f
            break
    
    if not field:
        return format_response(
            {"error": f"Column {column} not found in {schema}.{table}"},
            summary=f"Column not found"
        )
    
    doc = {
        "table": f"{schema}.{table}",
        "column": field.get("column_name"),
        "business_name": field.get("business_name"),
        "business_definition": field.get("business_definition"),
        "data_type": field.get("data_type"),
        "nullable": field.get("is_nullable"),
        "entity_role": field.get("entity_role"),
        "tags": field.get("tags", []),
        "known_issues": field.get("known_issues")
    }
    
    return format_response(
        doc,
        summary=f"{field.get('business_name', column)}: {field.get('entity_role', 'unknown')} ({field.get('data_type')})"
    )


async def handle_get_documentation_summary(args: Dict) -> Dict:
    """Handle get_documentation_summary tool."""
    connection_id = args.get("connection_id", "default")
    
    params = {"connection_id": connection_id, "limit": 500}
    if args.get("schema"):
        params["schema"] = args["schema"]
    
    result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    assets = result.get("results", [])
    documented = []
    undocumented = []
    
    for asset in assets:
        has_def = bool(asset.get("business_definition"))
        has_owner = bool(asset.get("owner"))
        has_grain = bool(asset.get("grain") or asset.get("row_meaning"))
        
        entry = {
            "table": f"{asset.get('schema_name')}.{asset.get('table_name')}",
            "has_definition": has_def,
            "has_owner": has_owner,
            "has_grain": has_grain
        }
        
        if has_def:
            documented.append(entry)
        else:
            undocumented.append(entry)
    
    total = len(assets)
    coverage = (len(documented) / total * 100) if total > 0 else 0
    
    return format_response(
        {
            "total_assets": total,
            "documented": len(documented),
            "undocumented": len(undocumented),
            "coverage_percent": round(coverage, 1),
            "documented_assets": documented[:10],  # First 10
            "undocumented_assets": undocumented[:10]  # First 10
        },
        summary=f"Documentation coverage: {coverage:.1f}% ({len(documented)}/{total} assets)"
    )


# =============================================================================
# TOOL IMPLEMENTATIONS - CURATION
# =============================================================================

async def handle_get_pending_relationships(args: Dict) -> Dict:
    """Handle get_pending_relationships tool."""
    params = {
        "status": "suggested",
        "limit": args.get("limit", 50),
        "offset": 0
    }
    
    if args.get("schema"):
        params["schema"] = args["schema"]
    
    result = await api_client.get("/data-dictionary/relationships", params)
    
    pending = []
    for rel in result.get("results", []):
        if args.get("min_confidence") and rel.get("confidence_score", 0) < args["min_confidence"]:
            continue
            
        pending.append({
            "source": f"{rel.get('left_ref', {}).get('schema')}.{rel.get('left_ref', {}).get('table')}.{rel.get('left_ref', {}).get('column')}",
            "target": f"{rel.get('right_ref', {}).get('schema')}.{rel.get('right_ref', {}).get('table')}.{rel.get('right_ref', {}).get('column')}",
            "type": rel.get("relationship_type"),
            "cardinality": rel.get("cardinality"),
            "confidence": rel.get("confidence_score"),
            "created_at": rel.get("created_at")
        })
    
    return format_response(
        {"pending_relationships": pending, "count": len(pending)},
        summary=f"{len(pending)} relationships pending review"
    )


async def handle_get_relationship_details(args: Dict) -> Dict:
    """Handle get_relationship_details tool."""
    # Build the relationship identifier
    source = f"{args['source_schema']}.{args['source_table']}.{args['source_column']}"
    target = f"{args['target_schema']}.{args['target_table']}.{args['target_column']}"
    
    # Get relationships for the source table
    params = {
        "schema": args["source_schema"],
        "table": args["source_table"]
    }
    
    result = await api_client.get("/data-dictionary/enhanced/relationships", params)
    
    # Find the matching relationship
    rel = None
    for r in result:
        r_source = f"{r.get('source_schema')}.{r.get('source_table')}.{r.get('source_column')}"
        r_target = f"{r.get('target_schema')}.{r.get('target_table')}.{r.get('target_column')}"
        
        if r_source == source and r_target == target:
            rel = r
            break
    
    if not rel:
        return format_response(
            {"error": f"Relationship not found: {source} -> {target}"},
            summary="Relationship not found"
        )
    
    return format_response({
        "source": source,
        "target": target,
        "relationship_type": rel.get("relationship_type", "unknown"),
        "cardinality": rel.get("cardinality"),
        "confidence": rel.get("confidence"),
        "status": rel.get("status", "unknown"),
        "notes": rel.get("notes")
    })


async def handle_get_curation_status(args: Dict) -> Dict:
    """Handle get_curation_status tool."""
    params = {"connection_id": args.get("connection_id", "default")}
    if args.get("schema"):
        params["schema"] = args["schema"]
    
    # Use the new MCP-optimized endpoint
    try:
        result = await api_client.get("/mcp/dictionary/curation-stats", params)
        
        return format_response({
            "total_assets": result.get("total_assets", 0),
            "documented_assets": result.get("documented_assets", 0),
            "documentation_percent": result.get("documentation_coverage", 0),
            "total_relationships": result.get("total_relationships", 0),
            "approved_relationships": result.get("approved_relationships", 0),
            "pending_relationships": result.get("pending_relationships", 0),
            "total_fields": result.get("total_fields", 0),
            "documented_fields": result.get("documented_fields", 0)
        }, summary=f"{result.get('documented_assets', 0)}/{result.get('total_assets', 0)} assets documented ({result.get('documentation_coverage', 0)}%)")
    except Exception:
        # Fallback to manual calculation if new endpoint not available
        asset_params = {"connection_id": args.get("connection_id", "default"), "limit": 500}
        if args.get("schema"):
            asset_params["schema"] = args["schema"]
        
        assets_result = await api_client.get("/data-dictionary/enhanced/assets", asset_params)
        assets = assets_result.get("results", [])
        documented = sum(1 for a in assets if a.get("business_definition"))
        
        return format_response({
            "total_assets": len(assets),
            "documented_assets": documented,
            "documentation_percent": round(documented / len(assets) * 100, 1) if assets else 0,
        }, summary=f"{documented}/{len(assets)} assets documented")


# =============================================================================
# TOOL IMPLEMENTATIONS - ANALYSIS
# =============================================================================

async def handle_check_data_quality(args: Dict) -> Dict:
    """Handle check_data_quality tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    # Get asset
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if not result.get("results"):
        return format_response(
            {"error": f"Table {schema}.{table} not found"},
            summary="Table not found"
        )
    
    asset = result["results"][0]
    
    quality = {
        "table": f"{schema}.{table}",
        "trust_tier": asset.get("trust_tier"),
        "trust_score": asset.get("trust_score"),
        "approved_for_reporting": asset.get("approved_for_reporting", False),
        "approved_for_ml": asset.get("approved_for_ml", False),
        "known_issues": asset.get("known_issues"),
        "issue_tags": asset.get("issue_tags", [])
    }
    
    # If column specified, get column-level info
    if args.get("column"):
        asset_id = asset["id"]
        fields = await api_client.get(f"/data-dictionary/enhanced/assets/{asset_id}/fields")
        
        for field in fields:
            if field.get("column_name", "").lower() == args["column"].lower():
                quality["column"] = field.get("column_name")
                quality["column_trust_tier"] = field.get("trust_tier")
                quality["column_trust_score"] = field.get("trust_score")
                quality["column_known_issues"] = field.get("known_issues")
                break
    
    # Generate summary
    tier = asset.get("trust_tier", "unknown")
    score = asset.get("trust_score", 0)
    summary = f"{tier.upper()} (score: {score}/100)"
    if asset.get("known_issues"):
        summary += " - has known issues"
    
    return format_response(quality, summary=summary)


async def handle_get_column_statistics(args: Dict) -> Dict:
    """Handle get_column_statistics tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    params = {
        "connection_id": connection_id,
        "schema": schema,
        "table": table,
        "latest": True
    }
    
    result = await api_client.get("/data-dictionary/enhanced/profiles", params)
    
    # Filter by column if specified
    if args.get("column"):
        result = [p for p in result if p.get("column_name", "").lower() == args["column"].lower()]
    
    profiles = []
    for p in result:
        profile = {
            "column": p.get("column_name"),
            "null_count": p.get("null_count"),
            "null_fraction": p.get("null_fraction"),
            "distinct_count": p.get("distinct_count") or p.get("distinct_count_estimate"),
            "uniqueness_fraction": p.get("uniqueness_fraction")
        }
        
        # Add numeric stats if present
        if p.get("numeric_min") is not None:
            profile["min"] = p.get("numeric_min")
            profile["max"] = p.get("numeric_max")
            profile["avg"] = p.get("numeric_avg")
            profile["stddev"] = p.get("numeric_stddev")
        
        # Add top values if present
        if p.get("top_values"):
            profile["top_values"] = p.get("top_values")[:5]
        
        # Add string stats if present
        if p.get("min_length") is not None:
            profile["min_length"] = p.get("min_length")
            profile["max_length"] = p.get("max_length")
            profile["avg_length"] = p.get("avg_length")
        
        # Add date stats if present
        if p.get("earliest_value"):
            profile["earliest"] = str(p.get("earliest_value"))
            profile["latest"] = str(p.get("latest_value"))
        
        profiles.append(profile)
    
    return format_response(
        {"table": f"{schema}.{table}", "profiles": profiles},
        summary=f"Statistics for {len(profiles)} columns in {schema}.{table}"
    )


async def handle_find_trusted_data(args: Dict) -> Dict:
    """Handle find_trusted_data tool."""
    connection_id = args.get("connection_id", "default")
    use_case = args["use_case"]
    min_tier = args.get("min_trust_tier", "trusted")
    
    # Map tier to include higher tiers
    tier_order = ["deprecated", "experimental", "trusted", "certified"]
    min_tier_idx = tier_order.index(min_tier) if min_tier in tier_order else 2
    valid_tiers = tier_order[min_tier_idx:]
    
    params = {
        "connection_id": connection_id,
        "limit": args.get("limit", 25)
    }
    
    if args.get("business_domain"):
        params["business_domain"] = args["business_domain"]
    
    result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    # Filter by use case and trust tier
    qualified = []
    for asset in result.get("results", []):
        tier = asset.get("trust_tier", "experimental")
        if tier not in valid_tiers:
            continue
        
        # Check use case approval
        if use_case == "reporting" and not asset.get("approved_for_reporting"):
            continue
        if use_case == "ml" and not asset.get("approved_for_ml"):
            continue
        
        qualified.append({
            "schema": asset.get("schema_name"),
            "table": asset.get("table_name"),
            "business_name": asset.get("business_name"),
            "trust_tier": tier,
            "trust_score": asset.get("trust_score"),
            "owner": asset.get("owner")
        })
    
    # Sort by trust score
    qualified.sort(key=lambda x: x.get("trust_score", 0), reverse=True)
    
    return format_response(
        {"assets": qualified[:args.get("limit", 25)], "count": len(qualified)},
        summary=f"Found {len(qualified)} assets qualified for {use_case}"
    )


# =============================================================================
# TOOL IMPLEMENTATIONS - UNDERSTANDING
# =============================================================================

async def handle_explain_table(args: Dict) -> Dict:
    """Handle explain_table tool - comprehensive table explanation."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    # Get full context
    context = await api_client.get(
        f"/data-dictionary/enhanced/context/{connection_id}/{schema}/{table}"
    )
    
    if "error" in context:
        return format_response(
            {"error": context["error"]},
            summary=f"Table {schema}.{table} not found"
        )
    
    table_info = context.get("table", {})
    columns = context.get("columns", [])
    relationships = context.get("relationships", [])
    
    # Get asset for additional info
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    asset = asset_result.get("results", [{}])[0] if asset_result.get("results") else {}
    
    # Build comprehensive explanation
    explanation = {
        "identity": {
            "full_name": f"{schema}.{table}",
            "business_name": table_info.get("business_name"),
            "description": table_info.get("definition"),
            "domain": table_info.get("domain")
        },
        "grain": {
            "description": table_info.get("grain") or asset.get("row_meaning"),
            "row_count": table_info.get("row_count")
        },
        "ownership": {
            "owner": asset.get("owner"),
            "steward": asset.get("steward")
        },
        "trust": {
            "tier": table_info.get("trust_tier"),
            "score": table_info.get("trust_score"),
            "approved_for_reporting": asset.get("approved_for_reporting", False),
            "approved_for_ml": asset.get("approved_for_ml", False),
            "known_issues": asset.get("known_issues")
        },
        "key_columns": [],
        "relationships": []
    }
    
    # Add key columns (identifiers, foreign keys, important measures)
    for col in columns:
        role = col.get("role", "other")
        if role in ["primary_identifier", "foreign_key", "measure"]:
            explanation["key_columns"].append({
                "column": col.get("name"),
                "business_name": col.get("business_name"),
                "role": role,
                "type": col.get("data_type")
            })
    
    # Add relationships
    for rel in relationships:
        explanation["relationships"].append({
            "direction": rel.get("direction"),
            "connects": rel.get("to") if rel.get("direction") == "outgoing" else rel.get("from"),
            "cardinality": rel.get("cardinality")
        })
    
    # Generate summary
    summary = f"{table_info.get('business_name', table)}"
    if table_info.get("definition"):
        summary += f": {truncate_text(table_info['definition'], 100)}"
    
    return format_response(
        explanation,
        summary=summary,
        suggestions=[
            "Use explain_grain to understand row-level meaning",
            "Use explain_join to understand how to connect to other tables"
        ]
    )


async def handle_explain_grain(args: Dict) -> Dict:
    """Handle explain_grain tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    # Get asset
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if not asset_result.get("results"):
        return format_response(
            {"error": f"Table {schema}.{table} not found"},
            summary="Table not found"
        )
    
    asset = asset_result["results"][0]
    asset_id = asset["id"]
    
    # Get fields to identify primary key
    fields = await api_client.get(f"/data-dictionary/enhanced/assets/{asset_id}/fields")
    
    primary_key = []
    for field in fields:
        if field.get("entity_role") == "primary_identifier":
            primary_key.append(field.get("column_name"))
    
    grain = {
        "table": f"{schema}.{table}",
        "grain_description": asset.get("grain") or asset.get("row_meaning"),
        "primary_key": primary_key if primary_key else None,
        "aggregation_guidance": None
    }
    
    # Add aggregation guidance based on grain
    if grain["grain_description"]:
        grain["aggregation_guidance"] = (
            f"Each row represents: {grain['grain_description']}. "
            "Aggregate accordingly to avoid double-counting."
        )
    
    summary = grain["grain_description"] or f"Grain not documented for {schema}.{table}"
    
    return format_response(grain, summary=summary)


async def handle_explain_semantics(args: Dict) -> Dict:
    """Handle explain_semantics tool."""
    connection_id = args.get("connection_id", "default")
    schema = args["schema"]
    table = args["table"]
    
    # Get asset for basic info
    params = {"connection_id": connection_id, "schema": schema, "search": table, "limit": 1}
    asset_result = await api_client.get("/data-dictionary/enhanced/assets", params)
    
    if not asset_result.get("results"):
        return format_response(
            {"error": f"Table {schema}.{table} not found"},
            summary="Table not found"
        )
    
    asset = asset_result["results"][0]
    
    # Note: Full semantics would come from dictionary_entry_semantics
    # For now, we provide what's available from the asset
    
    semantics = {
        "table": f"{schema}.{table}",
        "decision_context": {
            "domain": asset.get("business_domain"),
            "owner": asset.get("owner"),
            "steward": asset.get("steward")
        },
        "guarantees": {
            "trust_tier": asset.get("trust_tier"),
            "trust_score": asset.get("trust_score"),
            "known_issues": asset.get("known_issues"),
            "approved_for_reporting": asset.get("approved_for_reporting", False),
            "approved_for_ml": asset.get("approved_for_ml", False)
        },
        "validation": {
            "last_updated": asset.get("updated_at")
        }
    }
    
    return format_response(
        semantics,
        summary=f"Semantics for {schema}.{table} - {asset.get('trust_tier', 'unknown')} tier"
    )


async def handle_explain_join(args: Dict) -> Dict:
    """Handle explain_join tool."""
    connection_id = args.get("connection_id", "default")
    left_schema = args["left_schema"]
    left_table = args["left_table"]
    right_schema = args["right_schema"]
    right_table = args["right_table"]
    
    # Use the new MCP-optimized endpoint
    try:
        params = {
            "connection_id": connection_id,
            "left_schema": left_schema,
            "left_table": left_table,
            "right_schema": right_schema,
            "right_table": right_table
        }
        
        result = await api_client.get("/mcp/dictionary/analyze-join", params)
        
        if result.get("can_join"):
            if result.get("join_type") == "direct":
                summary = f"Direct join via {result.get('join_columns', {}).get('left')} → {result.get('join_columns', {}).get('right')} ({result.get('cardinality', 'unknown')})"
            else:
                path = result.get("path", [])
                summary = f"Indirect join through {len(path) - 2} intermediate table(s)"
        else:
            summary = "No relationship path found"
        
        return format_response(result, summary=summary)
        
    except Exception:
        # Fallback to manual lookup if new endpoint not available
        params = {
            "connection_id": connection_id,
            "schema": left_schema,
            "table": left_table
        }
        
        relationships = await api_client.get("/data-dictionary/enhanced/relationships", params)
        
        # Find direct relationship between tables
        direct_rel = None
        for rel in relationships:
            if (rel.get("target_schema") == right_schema and 
                rel.get("target_table") == right_table):
                direct_rel = rel
                break
            if (rel.get("source_schema") == right_schema and 
                rel.get("source_table") == right_table):
                direct_rel = rel
                break
        
        if direct_rel:
            explanation = {
                "can_join": True,
                "join_type": "direct",
                "join_columns": {
                    "left": f"{direct_rel.get('source_column')}",
                    "right": f"{direct_rel.get('target_column')}"
                },
                "cardinality": direct_rel.get("cardinality"),
                "warnings": [],
                "example_sql": f"""SELECT *
FROM {left_schema}.{left_table} l
LEFT JOIN {right_schema}.{right_table} r
  ON l.{direct_rel.get('source_column')} = r.{direct_rel.get('target_column')}"""
            }
            
            if direct_rel.get("cardinality") == "one_to_many":
                explanation["warnings"].append("1:N join - aggregations may cause fanout")
            
            summary = f"Direct join ({direct_rel.get('cardinality', 'unknown')})"
        else:
            explanation = {
                "can_join": False,
                "message": f"No direct relationship found",
                "suggestion": "Use discover_relationships to find join paths"
            }
            summary = "No direct relationship found"
        
        return format_response(explanation, summary=summary)


# =============================================================================
# TOOL ROUTER
# =============================================================================

TOOL_HANDLERS = {
    # Discovery
    "discover_assets": handle_discover_assets,
    "discover_fields": handle_discover_fields,
    "discover_relationships": handle_discover_relationships,
    # Documentation
    "get_asset_documentation": handle_get_asset_documentation,
    "get_field_documentation": handle_get_field_documentation,
    "get_documentation_summary": handle_get_documentation_summary,
    # Curation
    "get_pending_relationships": handle_get_pending_relationships,
    "get_relationship_details": handle_get_relationship_details,
    "get_curation_status": handle_get_curation_status,
    # Analysis
    "check_data_quality": handle_check_data_quality,
    "get_column_statistics": handle_get_column_statistics,
    "find_trusted_data": handle_find_trusted_data,
    # Understanding
    "explain_table": handle_explain_table,
    "explain_grain": handle_explain_grain,
    "explain_semantics": handle_explain_semantics,
    "explain_join": handle_explain_join,
}


# =============================================================================
# MCP SERVER HANDLERS
# =============================================================================

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    tools = []
    
    for tool_def in ALL_TOOLS:
        tools.append(Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def["input_schema"]
        ))
    
    return tools


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool execution."""
    
    try:
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        
        result = await handler(arguments)
        
        # Convert result to JSON string
        result_json = json.dumps(result, indent=2, default=str)
        
        return [TextContent(
            type="text",
            text=result_json
        )]
        
    except httpx.HTTPStatusError as e:
        logger.error(f"API error for tool {name}: {e}")
        error_result = {
            "error": {
                "message": f"API error: {e.response.status_code}",
                "details": str(e)
            }
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]
        
    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        error_result = {
            "error": {
                "message": str(e),
                "code": type(e).__name__
            }
        }
        return [TextContent(
            type="text",
            text=json.dumps(error_result, indent=2)
        )]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Nex Data Dictionary MCP Server")
    logger.info(f"Backend API URL: {API_BASE_URL}")
    logger.info(f"Available tools: {len(ALL_TOOLS)}")
    
    for use_case, tools in [
        ("discovery", 3), ("documentation", 3), ("curation", 3),
        ("analysis", 3), ("understanding", 4)
    ]:
        logger.info(f"  - {use_case}: {tools} tools")
    
    # Test backend connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                logger.info("Backend API is healthy")
            else:
                logger.warning(f"Backend API returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Could not connect to backend API: {e}")
        logger.warning("MCP server will start, but tools may fail until backend is available")
    
    # Start the stdio server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Server ready - waiting for client connections")
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
