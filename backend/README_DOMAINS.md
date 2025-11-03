# NEX.AI Backend Domain Architecture

This document describes the domain-first backend architecture with all feature stubs.

## Structure

```
backend/
├── core/                    # Core utilities
│   ├── config.py           # Application configuration
│   ├── logging.py          # Logging setup
│   └── models.py           # Base Pydantic models
├── domains/                 # Domain modules
│   ├── auth/               # Authentication & authorization
│   ├── connectors/         # Data source connectors
│   ├── context/            # Context engine (versioning, lineage)
│   ├── datasets/           # Dataset registry & transforms
│   ├── evaluations/        # Model evaluations
│   ├── governance/         # Policies, approvals, audit log
│   ├── insights/           # Lightweight reporting
│   ├── jobs/               # Async job queue
│   ├── mcp/                # MCP tools registry
│   └── personas/           # User personas
├── services/                # Legacy services (existing)
└── main.py                 # FastAPI app with all routers
```

## Domain Modules

Each domain follows a consistent structure:
- `models.py` - Pydantic schemas
- `service.py` - Business logic interfaces (stubs)
- `router.py` - FastAPI endpoints (stubs)

### Auth Domain (`/api/v1/auth`)
- User registration & authentication
- Organization management
- API token management
- Roles & permissions

**Status**: Stubs only - TODO: Implement JWT, password hashing, RBAC

### Connectors Domain (`/api/v1/connectors`)
- Extensible connector registry
- Connectors: Postgres, Snowflake, S3, HTTP, Files
- Connection testing
- Credential management

**Status**: Stubs only - TODO: Implement connector interfaces & drivers

### Context Domain (`/api/v1/context`)
- Versioning (semantic versioning)
- Data lineage tracking
- Snapshots (full/incremental)
- Context store (key-value)

**Status**: Stubs only - TODO: Implement versioning logic, lineage graph

### Datasets Domain (`/api/v1/datasets`)
- Dataset registry
- Transform pipeline
- Synthetic data generation
- Schema management

**Status**: Stubs only - TODO: Integrate with existing upload functionality

### Evaluations Domain (`/api/v1/evaluations`)
- Evaluation runner
- Scenario management
- Metrics calculation
- Report generation

**Status**: Stubs only - TODO: Implement evaluation engine

### Governance Domain (`/api/v1/governance`)
- Policy management
- Approval workflows
- Audit logging
- Policy evaluation

**Status**: Stubs only - TODO: Implement policy engine

### Insights Domain (`/api/v1/insights`)
- Insight generation
- Report creation
- Statistical analysis

**Status**: Stubs only - TODO: Implement analysis logic

### Jobs Domain (`/api/v1/jobs`)
- Async job queue interface
- Job status tracking
- Priority handling
- Retry logic

**Status**: Stubs only - TODO: Integrate queue backend (Redis/RabbitMQ)

### MCP Domain (`/api/v1/mcp`)
- MCP tool registry
- Tool execution runner
- Tool schema validation

**Status**: Stubs only - TODO: Implement MCP protocol support

### Personas Domain (`/api/v1/personas`)
- Persona management
- Versioning
- Governance integration

**Status**: Stubs only - TODO: Implement persona engine

## Implementation Notes

All services return `NotImplementedError` with TODO comments. The structure is ready for iterative implementation:

1. **Phase 1**: Core auth + datasets (migrate existing functionality)
2. **Phase 2**: Connectors + context engine
3. **Phase 3**: Evaluations + governance
4. **Phase 4**: MCP + personas + jobs

## API Endpoints

All endpoints are available under `/api/v1/{domain}/...` but return `501 Not Implemented` until services are implemented.

### Legacy Endpoints

Existing endpoints remain functional:
- `POST /api/upload`
- `GET /api/datasets`
- `POST /api/chat`
- etc.

These should be gradually migrated to the new domain structure.

## Configuration

Settings are loaded from environment variables (see `core/config.py`). Default values work for local development.

## Next Steps

1. Implement authentication first (required for other domains)
2. Migrate existing dataset functionality to new domain structure
3. Implement connectors one by one (start with file, then Postgres, etc.)
4. Build context engine (versioning + lineage)
5. Implement governance policies

Each domain can be implemented independently, following the interfaces defined in `service.py` files.

