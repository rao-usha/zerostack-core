# NEX.AI - AI Native Data Platform

## Comprehensive Technical Documentation

**Version:** 1.0.0  
**Last Updated:** December 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Modules](#backend-modules)
   - [Core Infrastructure](#core-infrastructure)
   - [Domain Modules](#domain-modules)
   - [Service Layer](#service-layer)
   - [LLM Integration](#llm-integration)
5. [Frontend Modules](#frontend-modules)
   - [Pages](#pages)
   - [Components](#components)
   - [API Client](#api-client)
6. [Database & Migrations](#database--migrations)
7. [Configuration](#configuration)
8. [API Reference](#api-reference)
9. [Getting Started](#getting-started)
10. [Development Guide](#development-guide)

---

## Overview

NEX.AI is a comprehensive, AI-powered data platform designed as a one-stop solution for enterprise data needs. The platform combines traditional data management with cutting-edge AI capabilities including:

- **AI-Powered Data Analysis** - Automated insights generation using multiple LLM providers
- **Data Dictionary Management** - AI-generated and human-curated documentation with versioning
- **ML Recipe Development** - End-to-end machine learning workflow management
- **Conversational Data Access** - Chat with your data using natural language
- **Database Exploration** - Browse and query databases with built-in safety
- **Synthetic Data Generation** - Privacy-safe data creation
- **Data Quality Assessment** - Automated quality scoring and recommendations

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│                     http://localhost:3000                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API + SSE Streaming
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                           │
│                     http://localhost:8000                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Domain Routers                        │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐    │   │
│  │  │  Chat   │ │ Explorer│ │ML Dev   │ │ Eval Packs  │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────┘    │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐    │   │
│  │  │Dictionary│ │Insights │ │Datasets │ │ Governance  │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Services Layer                        │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │ Synthetic   │ │  Insights   │ │   Quality   │        │   │
│  │  │   Data      │ │  Generator  │ │  Analyzer   │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM Providers                         │   │
│  │     OpenAI │ Anthropic │ Google │ xAI                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                        │
│                      localhost:5432                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | Modern async Python web framework |
| **PostgreSQL** | Primary database with pgvector for embeddings |
| **SQLAlchemy/SQLModel** | ORM and database models |
| **Alembic** | Database migrations |
| **Pydantic** | Data validation and settings |
| **Pandas** | Data manipulation and analysis |
| **Scikit-learn** | Machine learning models |
| **OpenAI/Anthropic/Google/xAI SDKs** | LLM provider integrations |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | UI component framework |
| **TypeScript** | Type-safe JavaScript |
| **Vite** | Fast build tool and dev server |
| **Tailwind CSS** | Utility-first CSS framework |
| **React Router** | Client-side routing |
| **Axios** | HTTP client |
| **Lucide React** | Icon library |

---

## Backend Modules

### Core Infrastructure

#### `backend/core/config.py`
**Application Configuration**

Centralized settings management using Pydantic BaseSettings with environment variable support.

```python
class Settings(BaseSettings):
    # Application
    app_name: str = "NEX.AI - AI Native Data Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # Database
    database_url: str = "postgresql+psycopg://nex:nex@localhost:5432/nex"
    
    # LLM API Keys
    openai_api_key: Optional[str] = None
```

**Key Features:**
- Environment variable loading from `.env` files
- CORS origin configuration
- Database connection string management
- LLM API key storage

#### `backend/core/logging.py`
**Logging Configuration**

Structured logging setup with configurable log levels and file output.

#### `backend/main.py`
**Application Entry Point**

FastAPI application initialization with:
- CORS middleware configuration
- Router registration for all domain modules
- Service initialization
- Health check endpoints

**Registered Routers:**
- `auth_router` - Authentication
- `connectors_router` - Data source connectors
- `context_router` / `contexts_router` - Context management
- `personas_router` - AI persona configuration
- `mcp_router` - Model Context Protocol
- `datasets_router` - Dataset management
- `evaluations_router` - Model evaluations
- `governance_router` - Data governance
- `jobs_router` - Background job management
- `insights_router` - AI insights
- `data_explorer_router` - Database exploration
- `data_dictionary_router` - Data dictionary management
- `chat_router` - Conversational AI
- `ml_development_router` - ML recipe development
- `evaluation_packs_router` - Evaluation pack management

---

### Domain Modules

Each domain follows a consistent pattern:
- `models.py` - Pydantic/SQLModel data models
- `router.py` - FastAPI route handlers
- `service.py` - Business logic layer

---

#### `backend/domains/data_explorer/`
**Database Exploration Module**

Provides comprehensive database introspection and querying capabilities.

**Files:**
| File | Purpose |
|------|---------|
| `router.py` | API endpoints for schema/table/column browsing |
| `service.py` | Database introspection service |
| `connection.py` | Database connection management |
| `db_configs.py` | Multi-database configuration |
| `models.py` | Request/response models |
| `ai_analysis.py` | AI-powered data analysis |
| `ai_router.py` | AI analysis endpoints |
| `analysis_prompts.py` | LLM prompt templates |
| `job_service.py` | Analysis job management |
| `jobs_router.py` | Job management endpoints |
| `dictionary_router.py` | Data dictionary endpoints |
| `dictionary_service.py` | Dictionary management logic |
| `dictionary_enhanced_router.py` | Enhanced dictionary features |
| `dictionary_enhanced_service.py` | Advanced dictionary operations |
| `prompt_recipes_router.py` | Analysis prompt recipes |

**Key Endpoints:**
```
GET  /api/v1/data-explorer/databases     - List available databases
GET  /api/v1/data-explorer/schemas       - List schemas
GET  /api/v1/data-explorer/tables        - List tables in schema
GET  /api/v1/data-explorer/tables/{schema}/{table}/columns - Get columns
GET  /api/v1/data-explorer/tables/{schema}/{table}/rows    - Get table data
GET  /api/v1/data-explorer/tables/{schema}/{table}/summary - Get statistics
POST /api/v1/data-explorer/query         - Execute read-only SQL
```

**MCP HTTP Bridge Endpoints:**
For integration with non-MCP LLMs (xAI Grok, Google Gemini, ChatGPT):
```
POST /api/v1/data-explorer/tool/list_connections
POST /api/v1/data-explorer/tool/list_schemas
POST /api/v1/data-explorer/tool/list_tables
POST /api/v1/data-explorer/tool/get_table_info
POST /api/v1/data-explorer/tool/sample_rows
POST /api/v1/data-explorer/tool/profile_table
POST /api/v1/data-explorer/tool/run_query
```

**Safety Features:**
- Read-only query enforcement
- Query validation and sanitization
- Timeout limits (30 seconds)
- Row limit caps (500-1000 rows)

---

#### `backend/domains/chat/`
**Conversational AI Module**

Full ChatGPT-like experience with streaming responses and tool calling.

**Key Features:**
- Multi-provider support (OpenAI, Anthropic, Google, xAI)
- Real-time streaming via Server-Sent Events (SSE)
- Conversation persistence
- Data Explorer tool integration
- Message history management

**Endpoints:**
```
POST   /api/v1/chat/conversations                    - Create conversation
GET    /api/v1/chat/conversations                    - List conversations
GET    /api/v1/chat/conversations/{id}               - Get conversation with messages
PATCH  /api/v1/chat/conversations/{id}               - Update conversation
DELETE /api/v1/chat/conversations/{id}               - Delete conversation
POST   /api/v1/chat/conversations/{id}/messages      - Send message (streaming)
```

**Streaming Response Events:**
```javascript
event: delta       // Partial response content
event: tool_call   // LLM calling a tool
event: tool_result // Tool execution result
event: done        // Response complete
event: error       // Error occurred
```

---

#### `backend/domains/ml_development/`
**ML Recipe Development Module**

End-to-end machine learning workflow management with recipes, models, and runs.

**Core Concepts:**

| Concept | Description |
|---------|-------------|
| **Recipe** | Template defining ML workflow (features, pipeline, metrics) |
| **Version** | Immutable snapshot of recipe configuration |
| **Model** | Trained model instance from a recipe |
| **Run** | Execution of training/evaluation |
| **Monitor** | Performance and drift tracking |

**Model Families:**
- `pricing` - Price optimization, elasticity, margin optimization
- `forecasting` - Time series, ARIMA, Prophet, demand forecasting
- `next_best_action` - Recommendation engines, uplift modeling
- `location_scoring` - Site selection, trade area analysis

**Recipe Levels:**
- `beginner` - Simple configurations with defaults
- `intermediate` - More customization options
- `advanced` - Full control over all parameters

**Endpoints:**
```
# Recipes
GET    /api/v1/ml-development/recipes              - List recipes
GET    /api/v1/ml-development/recipes/{id}         - Get recipe
POST   /api/v1/ml-development/recipes              - Create recipe
PUT    /api/v1/ml-development/recipes/{id}         - Update recipe
DELETE /api/v1/ml-development/recipes/{id}         - Delete recipe
POST   /api/v1/ml-development/recipes/{id}/clone   - Clone recipe

# Versions
GET    /api/v1/ml-development/recipes/{id}/versions     - List versions
POST   /api/v1/ml-development/recipes/{id}/versions     - Create version

# Models
GET    /api/v1/ml-development/models               - List models
GET    /api/v1/ml-development/models/{id}          - Get model
POST   /api/v1/ml-development/models               - Register model

# Runs
GET    /api/v1/ml-development/runs                 - List runs
GET    /api/v1/ml-development/runs/{id}            - Get run details
POST   /api/v1/ml-development/runs                 - Create run

# Monitoring
GET    /api/v1/ml-development/models/{id}/monitoring   - Get snapshots
POST   /api/v1/ml-development/models/{id}/monitoring   - Create snapshot

# AI Assistant
POST   /api/v1/ml-development/chat                 - Chat with ML expert
```

---

#### `backend/domains/evaluation_packs/`
**Evaluation Pack Module**

Reusable evaluation criteria and benchmarks for ML models.

**Features:**
- Evaluation pack versioning
- Recipe-pack attachment
- Execution tracking
- Monitoring snapshots

**Endpoints:**
```
GET    /api/v1/evaluation-packs                    - List packs
GET    /api/v1/evaluation-packs/{id}               - Get pack
POST   /api/v1/evaluation-packs                    - Create pack
PUT    /api/v1/evaluation-packs/{id}               - Update pack
DELETE /api/v1/evaluation-packs/{id}               - Delete pack
POST   /api/v1/evaluation-packs/{id}/clone         - Clone pack

# Versions
GET    /api/v1/evaluation-packs/{id}/versions      - List versions
POST   /api/v1/evaluation-packs/{id}/versions      - Create version

# Recipe Attachment
POST   /api/v1/evaluation-packs/recipes/{id}/attach    - Attach pack
DELETE /api/v1/evaluation-packs/recipes/{id}/detach/{pack_id}

# Execution
POST   /api/v1/evaluation-packs/execute            - Execute pack on run
GET    /api/v1/evaluation-packs/runs/{id}/results  - Get run results

# Monitoring
POST   /api/v1/evaluation-packs/monitor            - Create snapshot
GET    /api/v1/evaluation-packs/models/{id}/snapshots
```

---

#### `backend/domains/datasets/`
**Dataset Management Module**

Upload, store, and manage CSV datasets with automatic profiling.

**Features:**
- CSV file upload with type detection
- Dataset versioning
- Statistical profiling
- Preview and pagination

---

#### `backend/domains/insights/`
**AI Insights Module**

AI-powered strategic insights generation from data.

---

#### `backend/domains/governance/`
**Data Governance Module**

Data access policies, lineage tracking, and compliance management.

---

#### `backend/domains/connectors/`
**Data Connectors Module**

Connect to external data sources (databases, APIs, files).

---

#### `backend/domains/context/` & `backend/domains/contexts/`
**Context Management Module**

AI context engineering and management for specialized responses.

---

#### `backend/domains/personas/`
**AI Personas Module**

Define and manage AI personas for specialized interactions.

---

#### `backend/domains/jobs/`
**Background Jobs Module**

Async job scheduling and execution management.

---

#### `backend/domains/evaluations/`
**Model Evaluations Module**

Track and compare model evaluation results.

---

#### `backend/domains/mcp/`
**Model Context Protocol Module**

Native MCP server for Claude Desktop integration.

---

#### `backend/domains/auth/`
**Authentication Module**

User authentication and authorization (JWT tokens).

---

### Service Layer

#### `backend/services/synthetic_data.py`
**Synthetic Data Generator**

Privacy-safe synthetic data generation that preserves statistical properties.

```python
class SyntheticDataGenerator:
    def generate(self, df: pd.DataFrame, num_rows: int = 1000) -> pd.DataFrame:
        """
        Generate synthetic data based on original dataset.
        
        For numeric columns: Gaussian distribution with original mean/std
        For categorical columns: Preserve original distribution
        For datetime columns: Generate dates in similar range
        """
```

**Key Features:**
- Maintains statistical distributions
- Preserves categorical proportions
- Handles numeric, datetime, and categorical types
- Configurable row count

---

#### `backend/services/insights.py`
**Insights Generator**

AI-powered strategic insights from datasets.

```python
class InsightsGenerator:
    def generate(self, df: pd.DataFrame, context: str) -> Dict[str, Any]:
        """
        Generate comprehensive insights including:
        - summary: Dataset overview
        - trends: Increasing/decreasing patterns
        - anomalies: Outlier detection (IQR method)
        - correlations: Strong variable relationships
        - recommendations: Strategic suggestions
        - key_metrics: Statistical summaries
        - executive_kpis: Top-level business metrics
        - growth_metrics: Period-over-period growth
        - risk_indicators: Volatility and outlier analysis
        - performance_score: Overall health assessment
        """
```

---

#### `backend/services/data_quality.py`
**Data Quality Analyzer**

Comprehensive data quality assessment.

**Quality Dimensions:**
- **Completeness** - Missing value analysis
- **Consistency** - Data type and format validation
- **Accuracy** - Outlier and anomaly detection
- **Validity** - Business rule compliance

---

#### `backend/services/knowledge_gaps.py`
**Knowledge Gap Identifier**

Identify missing features and data gaps for better analysis.

---

#### `backend/services/documents/`
**Document Processing**

Document upload, parsing, and summarization services.

---

### LLM Integration

#### `backend/llm/providers.py`
**Multi-Provider LLM Abstraction**

Unified interface for multiple LLM providers with streaming and tool calling.

**Supported Providers:**

| Provider | Models | Features |
|----------|--------|----------|
| **OpenAI** | GPT-4, GPT-4 Turbo | Streaming, Tool Calling |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | Streaming, Tool Calling |
| **Google** | Gemini Pro, Gemini Ultra | Streaming, Function Calling |
| **xAI** | Grok | Streaming, Tool Calling |

**Usage:**
```python
from llm.providers import get_provider

provider = get_provider("openai", "gpt-4-turbo-preview")
async for event in provider.stream_chat(messages, tools):
    if event["type"] == "delta":
        print(event["content"])
    elif event["type"] == "tool_call":
        # Handle tool call
```

**Event Types:**
```python
{"type": "delta", "content": str}           # Text content
{"type": "tool_call", "tool_name": str, "tool_input": dict}  # Tool request
{"type": "done", "finish_reason": str}      # Completion
{"type": "error", "error": str}             # Error
```

---

## Frontend Modules

### Pages

| Page | Route | Description |
|------|-------|-------------|
| `Dashboard.tsx` | `/` | Main dashboard with overview metrics |
| `DataUpload.tsx` | `/upload` | CSV file upload interface |
| `Contexts.tsx` | `/contexts` | Context management |
| `Distillation.tsx` | `/distillation` | Data distillation explorer |
| `DataExplorer.tsx` | `/explorer` | Database schema browser |
| `DataAnalysis.tsx` | `/analysis` | AI-powered data analysis |
| `DataDictionary.tsx` | `/dictionary` | Data dictionary management |
| `ModelLibrary.tsx` | `/model-development` | ML recipe library |
| `RecipeDetail.tsx` | `/model-development/recipes/:id` | Recipe configuration |
| `ModelDetail.tsx` | `/model-development/models/:id` | Model details |
| `RunDetail.tsx` | `/model-development/runs/:id` | Run details |
| `MLChat.tsx` | `/model-development/chat` | ML expert chat |
| `Chat.tsx` | `/chat` | General data chat |
| `Insights.tsx` | `/insights` | AI insights dashboard |
| `Quality.tsx` | `/quality` | Data quality assessment |
| `KnowledgeGaps.tsx` | `/gaps` | Knowledge gap analysis |
| `Models.tsx` | `/models` | Predictive model building |
| `SyntheticData.tsx` | `/synthetic` | Synthetic data generation |

---

### Components

| Component | Purpose |
|-----------|---------|
| `Layout.tsx` | Main application layout with navigation |
| `DataTable.tsx` | Reusable data table with sorting/pagination |
| `FloatingChat.tsx` | Floating chat widget |
| `JsonViewer.tsx` | JSON data visualization |
| `AIAnalysisTab.tsx` | AI analysis display component |
| `PromptLibrary.tsx` | Analysis prompt templates |
| `RecipeEditor.tsx` | ML recipe configuration editor |

---

### API Client

#### `frontend/src/api/client.ts`

Axios-based API client with:
- Base URL configuration
- Error handling
- Request/response interceptors
- TypeScript interfaces

---

## Database & Migrations

### Migration Files

Located in `backend/migrations/versions/`:

| Migration | Description |
|-----------|-------------|
| `001_bootstrap_nex_schema.py` | Initial schema setup |
| `002_add_chat_tables.py` | Chat conversations and messages |
| `003_add_ai_analysis_tables.py` | AI analysis job tables |
| `004_add_enhanced_metadata.py` | Enhanced metadata columns |
| `005_add_analysis_jobs.py` | Analysis job management |
| `006_add_prompt_recipes.py` | Prompt recipe storage |
| `007_add_recipe_fields_to_jobs.py` | Link recipes to jobs |
| `008_add_data_dictionary.py` | Data dictionary tables |
| `009_add_dictionary_versioning.py` | Dictionary version control |
| `009_add_ml_model_development.py` | ML development tables |
| `010_add_evaluation_packs.py` | Evaluation pack tables |
| `011_add_enhanced_dictionary.py` | Enhanced dictionary features |

### Running Migrations

```bash
cd backend
alembic upgrade head
```

---

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex

# API Keys (at least one required for AI features)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
XAI_API_KEY=...

# Application
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Security
SECRET_KEY=your-secret-key-here
```

---

## API Reference

### Health Endpoints

```http
GET /
Response: {"message": "NEX.AI - AI Native Data Platform API", "status": "running"}

GET /health
Response: {"status": "healthy", "service": "NEX.AI API", "database": "connected"}

GET /health/config
Response: {"openai_api_key_configured": true, "from_settings": true, ...}
```

### Core Data Endpoints

```http
POST /api/upload                    # Upload CSV dataset
GET  /api/datasets                  # List all datasets
GET  /api/dataset/{id}              # Get dataset preview
POST /api/synthetic/generate        # Generate synthetic data
POST /api/models/predictive         # Build ML model
POST /api/insights/generate         # Generate AI insights
POST /api/chat                      # Chat about data
GET  /api/quality/{id}              # Data quality report
GET  /api/knowledge-gaps/{id}       # Knowledge gap analysis
```

---

## Getting Started

### Prerequisites

- **Docker Desktop** (20.10+) for containerized deployment
- **Python 3.11+** for local development
- **Node.js 18+** for frontend development
- **PostgreSQL 14+** with pgvector extension
- At least one LLM API key (OpenAI, Anthropic, Google, or xAI)

### Docker Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Nex

# Start all services
docker-compose -f config/docker-compose.dev.yml up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Local Development

```bash
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp env_example_for_data_explorer.txt .env
# Edit .env with your configuration
uvicorn main:app --reload --port 8000

# Frontend setup (separate terminal)
cd frontend
npm install
npm run dev
```

### Database Setup

```bash
# Windows
.\setup_nex_db.bat

# Unix/Mac
./setup_nex_db.sh

# Or manually with Docker
docker run -d \
  --name nex-postgres \
  -e POSTGRES_USER=nex \
  -e POSTGRES_PASSWORD=nex \
  -e POSTGRES_DB=nex \
  -p 5432:5432 \
  ankane/pgvector

# Run migrations
cd backend
alembic upgrade head
```

---

## Development Guide

### Project Structure

```
Nex/
├── backend/
│   ├── core/               # Core configuration and utilities
│   ├── db/                 # Database models and meta
│   ├── domains/            # Business domain modules
│   │   ├── auth/           # Authentication
│   │   ├── chat/           # Conversational AI
│   │   ├── connectors/     # Data source connectors
│   │   ├── context/        # Context management
│   │   ├── data_explorer/  # Database exploration
│   │   ├── datasets/       # Dataset management
│   │   ├── evaluation_packs/
│   │   ├── evaluations/    # Model evaluations
│   │   ├── governance/     # Data governance
│   │   ├── insights/       # AI insights
│   │   ├── jobs/           # Background jobs
│   │   ├── mcp/            # Model Context Protocol
│   │   ├── ml_development/ # ML recipe development
│   │   └── personas/       # AI personas
│   ├── llm/                # LLM provider integrations
│   ├── migrations/         # Alembic migrations
│   ├── scripts/            # Utility scripts
│   └── services/           # Business services
│
├── frontend/
│   └── src/
│       ├── api/            # API client
│       ├── components/     # Reusable components
│       └── pages/          # Page components
│
├── config/                 # Docker and build configs
├── docs/                   # Documentation
├── scripts/                # Project-level scripts
└── tests/                  # Integration tests
```

### Adding a New Domain Module

1. Create domain directory: `backend/domains/my_domain/`
2. Create required files:
   - `__init__.py`
   - `models.py` - Pydantic/SQLModel models
   - `router.py` - FastAPI router
   - `service.py` - Business logic
3. Register router in `backend/main.py`
4. Create database migration if needed

### Testing

```bash
# Backend tests
cd backend
pytest

# Specific test file
pytest tests/test_health.py

# Frontend tests
cd frontend
npm test
```

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Use strict mode, interface-first design
- **Documentation**: Docstrings for all public functions

---

## License

This is a prototype application for demonstration and research purposes.

---

**🚀 Ready to explore AI-native data management? Start with:**
```bash
docker-compose -f config/docker-compose.dev.yml up -d
```
**Then visit: http://localhost:3000**
