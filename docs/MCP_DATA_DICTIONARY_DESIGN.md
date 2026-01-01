# MCP Data Dictionary Tools - Design & Implementation

## Overview

This document describes the MCP (Model Context Protocol) tools that enable AI models (Claude, GPT, etc.) to interact with the Nex Data Dictionary through natural language conversations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User (via Chat)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (Claude/GPT)                          │
│  - Understands user intent                                   │
│  - Selects appropriate tools                                 │
│  - Synthesizes responses in natural language                 │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            mcp_dictionary_server.py                          │
│  - 16 tools organized by 5 use cases                         │
│  - HTTP client calls backend API                             │
│  - Formats responses for LLM consumption                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/REST
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend                             │
│  - /mcp/dictionary/* (new MCP-optimized endpoints)          │
│  - /data-dictionary/enhanced/*                               │
│  - /data-dictionary/* (semantics)                            │
└─────────────────────────────────────────────────────────────┘
```

## Design Principles

### 1. App as Deterministic Backbone
The AI doesn't directly manipulate data. Instead, it calls well-defined APIs that provide consistent, validated results.

### 2. Read-Only First
All 16 tools are **read-only** to avoid adding entropy to the system. The AI can discover, understand, and analyze - but not modify.

### 3. Organized by Use Case
Tools are grouped by the 5 core use cases users care about:
1. **Discovery** - Find and explore data assets
2. **Documentation** - Read existing business definitions
3. **Curation** - View relationships and approval status
4. **Analysis** - Query trust, quality, fitness for use
5. **Understanding** - Explain grain, semantics, joins

### 4. Rich Context for Conversation
Tools return enough context for the LLM to have meaningful conversations without excessive round-trips.

## Tools Reference

### Use Case 1: Discovery (3 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `discover_assets` | Find tables/views with filters | "What tables do we have?" |
| `discover_fields` | List columns in a table | "What columns does orders have?" |
| `discover_relationships` | Find table connections | "What's related to customers?" |

### Use Case 2: Documentation (3 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `get_asset_documentation` | Full table documentation | "Tell me about the orders table" |
| `get_field_documentation` | Column documentation | "What does customer_id mean?" |
| `get_documentation_summary` | Coverage overview | "What needs documentation?" |

### Use Case 3: Curation (3 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `get_pending_relationships` | Relationships awaiting review | "What relationships need approval?" |
| `get_relationship_details` | Stats for a relationship | "Tell me about this join" |
| `get_curation_status` | Overall curation stats | "How curated is our dictionary?" |

### Use Case 4: Analysis (3 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `check_data_quality` | Trust tier and issues | "Is orders trustworthy?" |
| `get_column_statistics` | Statistical profiles | "What's the distribution of status?" |
| `find_trusted_data` | Find approved data | "What data can I use for ML?" |

### Use Case 5: Understanding (4 tools)

| Tool | Purpose | Example Prompt |
|------|---------|----------------|
| `explain_table` | Comprehensive table context | "Explain the orders table" |
| `explain_grain` | What one row represents | "What's the grain of daily_sales?" |
| `explain_semantics` | Decision context & guarantees | "Who uses the revenue table?" |
| `explain_join` | How to join two tables | "How do I join orders and customers?" |

## File Structure

```
backend/
├── mcp_dictionary_server.py           # MCP server (main entry point)
├── mcp_server.py                      # Existing DB explorer MCP server
├── domains/
│   └── data_explorer/
│       ├── mcp_dictionary_tools.py    # Tool definitions
│       ├── mcp_dictionary_router.py   # Backend endpoints for MCP
│       ├── dictionary_enhanced_*.py   # Existing enhanced dictionary
│       └── dictionary_semantics_*.py  # Existing semantics
```

## Running the MCP Server

### Prerequisites

1. Backend API running at `http://localhost:8000`
2. Python 3.11+ with MCP SDK installed

### Start the Server

```bash
cd backend
python mcp_dictionary_server.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEX_API_BASE_URL` | `http://localhost:8000` | Backend API URL |

### Configure in Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nex-data-dictionary": {
      "command": "python",
      "args": ["c:/path/to/backend/mcp_dictionary_server.py"],
      "env": {
        "NEX_API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Backend Endpoints

### New MCP-Optimized Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /mcp/dictionary/search` | Full-text search across dictionary |
| `GET /mcp/dictionary/analyze-join` | Analyze join compatibility |
| `GET /mcp/dictionary/curation-stats` | Curation statistics |
| `GET /mcp/dictionary/quality-overview` | Quality distribution |
| `GET /mcp/dictionary/context/{schema}/{table}` | LLM context blob |

### Existing Endpoints Used

| Endpoint | Used By |
|----------|---------|
| `GET /data-dictionary/enhanced/assets` | discover_assets, find_trusted_data |
| `GET /data-dictionary/enhanced/assets/{id}/fields` | discover_fields |
| `GET /data-dictionary/enhanced/relationships` | discover_relationships |
| `GET /data-dictionary/enhanced/context/{conn}/{schema}/{table}` | explain_table |
| `GET /data-dictionary/enhanced/profiles` | get_column_statistics |

## Example Conversations

### Discovery Flow
```
User: "What customer data do we have?"
AI: → discover_assets(search="customer")
AI: "I found 5 tables related to customers:
     1. customers - Core customer records
     2. customer_orders - Order history by customer
     ..."
     
User: "Tell me about the customers table"
AI: → get_asset_documentation(schema="public", table="customers")
AI: "The customers table contains core customer profile data..."
```

### Analysis Flow
```
User: "I need data for a board report. What's reliable?"
AI: → find_trusted_data(use_case="reporting")
AI: "I found 8 certified tables approved for reporting:
     1. monthly_revenue (trust score: 95)
     2. daily_sales (trust score: 92)
     ..."
     
User: "Are there any known issues with monthly_revenue?"
AI: → check_data_quality(schema="finance", table="monthly_revenue")
AI: "monthly_revenue is certified with no known issues..."
```

### Understanding Flow
```
User: "I want to join orders with products"
AI: → explain_join(left_table="orders", right_table="products")
AI: "These tables don't have a direct relationship. 
     You'll need to go through order_items:
     orders → order_items → products
     
     Warning: This creates a 1:N:1 join..."
```

## Interaction Modes

The server supports 4 interaction modes:

| Mode | Use Cases | Personality |
|------|-----------|-------------|
| **Explorer** | All | Curious, thorough, educational |
| **Analyst** | Discovery, Analysis, Understanding | Precise, cautious about quality |
| **Steward** | Documentation, Curation, Analysis | Governance-focused, thorough |
| **Quick** | Discovery, Documentation | Concise, direct |

## Future Enhancements

### Phase 2: Write Operations
- Add curation tools (update definitions, approve relationships)
- Implement confirmation workflows
- Add audit logging for AI-initiated changes

### Phase 3: Advanced Features
- Semantic search using embeddings
- Multi-hop join path finding
- Impact analysis for changes
- Lineage exploration

## Response Format

All tools return structured responses optimized for LLM consumption:

```json
{
  "data": { ... },
  "summary": "Brief description of what was found",
  "suggestions": ["Next steps or related queries"]
}
```

## Error Handling

Errors are returned in a consistent format:

```json
{
  "error": {
    "message": "Human-readable error message",
    "code": "ERROR_CODE"
  }
}
```

Common error codes:
- `NotFound` - Requested resource doesn't exist
- `ValidationError` - Invalid parameters
- `APIError` - Backend API error
