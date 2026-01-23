# ZeroStack (NEX.AI)

## AI Native Data Platform

A comprehensive, AI-powered data platform that serves as a one-stop solution for all data-related needs in large organizations. This platform eliminates data governance concerns while providing powerful analytics, predictive modeling, and data management capabilities.

## 🚀 Quick Start (Docker - Recommended)

```bash
# Clone and start everything
git clone <repository-url>
cd Nex

# Copy environment file and add your API keys
cp .env.example .env
# Edit .env to add OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.

# Start all services (database, minio, backend, frontend)
docker compose -p zerostack up -d

# View logs (optional)
docker compose -p zerostack logs -f
```

**Access:** http://localhost:3000

**Features to explore:**
- 📊 **Data Upload & Analysis** - CSV datasets with AI insights
- 🤖 **Predictive Modeling** - One-click ML models with feature importance
- 🔄 **Synthetic Data** - Privacy-safe synthetic dataset generation
- 📖 **Data Dictionary** - Business-focused data documentation

## Features

### 🚀 Core Capabilities

1. **Data Upload & Management**
   - Upload CSV datasets with automatic type detection
   - Store and manage multiple datasets with versioning
   - Real-time data preview and profiling

2. **Synthetic Data Generation**
   - Generate privacy-safe synthetic data from your datasets
   - Preserves statistical properties, correlations, and distributions
   - No data governance issues - completely synthetic

3. **Predictive Modeling**
   - Build regression and classification models with one click
   - Automatic feature engineering and selection
   - Performance metrics (R², accuracy, F1, precision, recall)
   - Feature importance analysis with SHAP values

4. **AI-Powered Insights**
   - Automatic strategic insights generation using advanced LLMs
   - Trend identification and anomaly detection
   - Correlation analysis and causal inference
   - Context-aware recommendations and actionable insights

5. **Natural Language Chat Interface**
   - Ask questions about your data in plain English
   - Get instant answers with statistical analysis
   - Dataset-aware responses with citations
   - Multi-dataset conversational context

6. **Data Quality Assessment**
   - Comprehensive data quality scoring (0-100)
   - Completeness, consistency, accuracy, and validity checks
   - Automated issue identification and prioritized recommendations
   - Quality trend monitoring over time

7. **Knowledge Gap Identification**
   - Identify missing features and data gaps
   - Temporal coverage analysis
   - Data diversity assessment
   - Relationship gap detection
   - Actionable recommendations

8. **Data Explorer** 🆕
   - Browse and explore Postgres databases directly
   - View schemas, tables, and column metadata
   - Preview table data with pagination
   - Execute ad-hoc SQL queries (read-only)
   - View table summary statistics
   - Built-in query safety validation

9. **MCP Data Explorer** ⚡ NEW
   - Model Context Protocol server for AI-powered database exploration
   - Native Claude Desktop integration for conversational data discovery
   - HTTP bridge for xAI, Gemini, ChatGPT, and other LLMs
   - 7 specialized tools: schema discovery, data profiling, safe querying
   - Multi-database support with automatic configuration detection
   - Enterprise-grade safety: read-only sessions, query validation, timeouts

10. **Chat with Your Data** 🆕 LATEST
   - Full ChatGPT-like experience integrated into the platform
   - Multi-provider support: OpenAI (GPT-4), Anthropic (Claude), Google (Gemini), xAI (Grok)
   - Real-time streaming responses with Server-Sent Events
   - Complete conversation persistence in Postgres
   - Automatic tool calling with MCP Data Explorer integration
   - Beautiful modern UI with conversation management
   - Ask questions, get insights, explore data conversationally

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Main database (via SQLAlchemy + psycopg)
- **Pandas** - Data manipulation and analysis
- **Scikit-learn** - Machine learning models
- **SQLite** - Lightweight database for data storage
- **NumPy, SciPy** - Numerical computations

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **Axios** - API client
- **Lucide React** - Icons

## Getting Started

## 🏗️ Architecture

NEX.AI consists of interconnected services:

### 🔧 **Core Services**
- **Main Backend** (Port 8000) - Core data platform with analytics, ML, and synthetic data generation
- **Frontend** (Port 3000) - Modern React UI for data exploration and management

### 🗃️ **Databases & Infrastructure**
- **PostgreSQL + pgvector** (Port 5432) - Vector database for embeddings and relational data
- **Redis** (Port 6380) - Job queuing for background tasks

## 🐳 Docker Setup (Recommended)

### Prerequisites
- **Docker Desktop** (20.10+)
- **Git**
- **OpenAI API Key** (for AI features)

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd Nex

# Copy environment file and configure API keys
cp .env.example .env
# Edit .env to add your API keys (OPENAI_API_KEY, etc.)

# Start all services
docker compose -p zerostack up -d

# View logs (optional)
docker compose -p zerostack logs -f
```

### Access Points
| Service | URL | Description |
|---------|-----|-------------|
| Frontend UI | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000/docs | Swagger documentation |
| MinIO Console | http://localhost:9001 | Object storage UI (minioadmin/minioadmin) |
| PostgreSQL | localhost:5432 | Database (nex/nex) |

### Docker Commands

```bash
# Stop services
docker compose -p zerostack down

# Rebuild after code changes
docker compose -p zerostack build --no-cache
docker compose -p zerostack up -d

# View container status
docker compose -p zerostack ps

# View logs for specific service
docker compose -p zerostack logs -f backend
docker compose -p zerostack logs -f frontend

# Execute commands in containers
docker compose -p zerostack exec backend bash
docker compose -p zerostack exec frontend sh

# Full restart (removes volumes - WARNING: deletes data)
docker compose -p zerostack down -v
docker compose -p zerostack up -d
```

## ⚠️ Troubleshooting

### Common Issues

#### 1. Frontend shows "ERR_NAME_NOT_RESOLVED" for `backend:8000`

**Cause:** You're running the frontend outside Docker while the backend runs inside Docker.

**Solution:** Always use Docker Compose to run all services together:
```bash
docker compose -p zerostack up -d
```

**DO NOT** run `npm run dev` locally if your backend is in Docker. The Vite dev server inside Docker is already configured to proxy API requests to the backend service.

#### 2. Database connection errors

**Cause:** Database container not ready or wrong connection string.

**Solution:**
```bash
# Check if database is healthy
docker compose -p zerostack ps

# Wait for database to be ready, then restart backend
docker compose -p zerostack restart backend
```

#### 3. Changes not reflecting in frontend

**Cause:** Docker volume caching or browser cache.

**Solution:**
```bash
# Rebuild frontend container
docker compose -p zerostack build frontend
docker compose -p zerostack up -d frontend

# Or clear your browser cache (Ctrl+Shift+R)
```

#### 4. API requests returning 404

**Cause:** Backend not running or proxy misconfigured.

**Solution:**
```bash
# Check backend logs
docker compose -p zerostack logs backend

# Verify backend is responding
curl http://localhost:8000/docs
```

### Development Modes

| Mode | Command | When to Use |
|------|---------|-------------|
| **Full Docker** (Recommended) | `docker compose -p zerostack up -d` | Normal development |
| **Local Frontend + Docker Backend** | See below | Frontend debugging |
| **Full Local** | See below | Advanced debugging |

#### Local Frontend + Docker Backend

If you need to debug the frontend with hot reload outside Docker:

```bash
# 1. Start only backend services in Docker
docker compose -p zerostack up -d db minio minio-init backend

# 2. Run frontend locally (ensure DOCKER_ENV is NOT set)
cd frontend
unset DOCKER_ENV  # Important!
npm install
npm run dev
```

#### Full Local Development

```bash
# 1. Start PostgreSQL and MinIO
docker compose -p zerostack up -d db minio minio-init

# 2. Run backend locally
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex uvicorn main:app --reload --port 8000

# 3. Run frontend locally (in another terminal)
cd frontend
npm install
npm run dev
```

## Usage Guide

### 🏠 **Dashboard**
- Overview of all datasets, models, and recent activity
- Quick access to all platform features
- System health monitoring

### 📤 **Upload Data**
- Drag & drop or select CSV files
- Automatic data type detection and profiling
- Preview data before processing
- Support for large datasets with streaming upload

### 🧠 **Generate Insights**
- AI-powered strategic insights using GPT-4
- Trend identification and anomaly detection
- Correlation analysis with statistical significance
- Context-aware recommendations and actionable insights

### 🤖 **Predictive Models**
- One-click model building for regression/classification
- Automatic feature engineering and selection
- Performance metrics with confidence intervals
- Feature importance with SHAP value explanations
- Model comparison and versioning

### 🔄 **Synthetic Data**
- Generate privacy-safe synthetic datasets
- Preserve statistical properties and relationships
- Configurable generation parameters
- Quality validation of synthetic data

### 📊 **Data Quality**
- Comprehensive quality scoring (0-100)
- Automated issue detection and prioritization
- Quality trend monitoring
- Actionable improvement recommendations

### 🔍 **Knowledge Gaps**
- ML-powered gap identification
- Temporal coverage analysis
- Data diversity assessment
- Relationship gap detection

### 💬 **Chat Interface**
- Natural language queries about your data
- Multi-dataset conversational context
- Statistical analysis with citations
- Visual chart generation from text queries

### ⚡ **🆕 MCP Data Explorer**
- **NEW**: AI-powered database exploration with Model Context Protocol
- **Claude Desktop Integration**: Native conversational database access
  - "What tables are in my database?"
  - "Profile the orders table and show me data quality issues"
  - "Find all customers who made purchases last month"
- **Universal LLM Support**: HTTP bridge for xAI, Gemini, ChatGPT
- **7 Specialized Tools**: Discovery, profiling, and safe querying
- **Multi-Database**: Explore multiple Postgres instances simultaneously
- **Enterprise Safety**: Read-only sessions, query validation, resource limits

**Quick Start:**
```bash
# Test the MCP server
cd backend
python mcp_server.py

# Or use HTTP bridge (already running with docker-compose)
curl -X POST http://localhost:8000/api/v1/data-explorer/tool/list_tables \
  -H "Content-Type: application/json" \
  -d '{"schema": "public"}'
```

See [MCP_DATA_EXPLORER_SETUP.md](docs/setup/MCP_DATA_EXPLORER_SETUP.md) for complete setup guide.

## 🔌 API Documentation

- **Main Backend**: http://localhost:8000/docs (Swagger UI)

### Key Endpoints
- `POST /api/upload` - Upload and analyze CSV datasets
- `POST /api/synthetic/generate` - Create privacy-safe synthetic data
- `POST /api/models/predictive` - Build ML models with explanations
- `POST /api/insights/generate` - Generate AI-powered insights
- `POST /api/chat` - Natural language data queries

### Data Explorer 🆕
- `GET /api/v1/data-explorer/health` - Check database connection
- `GET /api/v1/data-explorer/schemas` - List all schemas
- `GET /api/v1/data-explorer/tables` - List tables in a schema
- `GET /api/v1/data-explorer/tables/{schema}/{table}/columns` - Get table columns
- `GET /api/v1/data-explorer/tables/{schema}/{table}/rows` - Get table rows (paginated)
- `GET /api/v1/data-explorer/tables/{schema}/{table}/summary` - Get table statistics
- `POST /api/v1/data-explorer/query` - Execute read-only SQL query

See [DATA_EXPLORER.md](backend/DATA_EXPLORER.md) for detailed documentation.

### MCP Data Explorer ⚡ NEW
- **MCP Server:** `python backend/mcp_server.py` - Native MCP protocol server
- **HTTP Bridge:** `/api/v1/data-explorer/tool/*` - REST endpoints for non-MCP LLMs
  - `POST /tool/list_connections` - List available databases
  - `POST /tool/list_schemas` - List database schemas
  - `POST /tool/list_tables` - List tables in schema
  - `POST /tool/get_table_info` - Get table column metadata
  - `POST /tool/sample_rows` - Sample table data
  - `POST /tool/profile_table` - Get comprehensive statistics
  - `POST /tool/run_query` - Execute safe SELECT queries

See [MCP_DATA_EXPLORER_SETUP.md](docs/setup/MCP_DATA_EXPLORER_SETUP.md) for quick setup or [docs/mcp-data-explorer.md](docs/mcp-data-explorer.md) for complete documentation.

## Project Structure

```
Nex/
├── backend/                    # Main data platform
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── domains/               # Business domain modules
│   │   ├── datasets/         # Dataset management
│   │   ├── contexts/         # Context engineering
│   │   ├── insights/         # AI insights generation
│   │   └── models/           # Predictive modeling
│   └── services/             # Core services
│       ├── synthetic_data.py # Privacy-safe data generation
│       ├── data_quality.py   # Quality assessment
│       └── knowledge_gaps.py # Gap identification
│
├── frontend/                  # React TypeScript UI
│   ├── src/
│   │   ├── pages/            # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── DataUpload.tsx
│   │   │   └── SyntheticData.tsx
│   │   ├── components/       # Reusable components
│   │   ├── api/              # API client
│   │   └── App.tsx           # Main app component
│   ├── package.json
│   └── tailwind.config.js
│
├── docs/                      # 📚 Documentation
│   ├── guides/               # User guides and tutorials
│   │   ├── QUICKSTART.md
│   │   ├── START_HERE.md
│   │   ├── START_DATA_EXPLORER.md
│   │   └── NEXT_STEPS.md
│   ├── setup/                # Setup and installation guides
│   │   ├── INSTALLATION.md
│   │   ├── SETUP_GUIDE.md
│   │   ├── DATA_EXPLORER_ENV_SETUP.md
│   │   └── MCP_DATA_EXPLORER_SETUP.md
│   ├── api.md                # API documentation
│   ├── development.md        # Development guide
│   ├── docker.md             # Docker setup
│   ├── testing.md            # Testing guide
│   ├── RUN_TESTS.md          # Test execution
│   ├── BRANDING.md           # Brand guidelines
│   └── COLOR_SCHEME.md       # Design system
│
├── config/                    # ⚙️ Configuration files
│   ├── docker-compose.yml    # Production deployment
│   ├── docker-compose.dev.yml # Development environment
│   ├── docker-compose.ci.yml # CI/CD configuration
│   ├── Makefile              # Build automation
│   ├── pytest.ini            # Test configuration
│   └── requirements-dev.txt  # Dev dependencies
│
├── scripts/                   # 🔧 Utility scripts
│   ├── start.sh              # Start all services
│   ├── start_backend.sh      # Start backend only
│   ├── start_frontend.sh     # Start frontend only
│   ├── install_all.sh        # Install dependencies
│   ├── install_node.sh       # Install Node.js
│   ├── check_setup.sh        # Verify setup
│   └── agent_ci.sh           # CI automation
│
├── tests/                     # 🧪 Test files
│   ├── test_context_api.py
│   ├── test_document_upload.py
│   ├── test_summarization_full.py
│   └── test_summarization_integration.py
│
├── example_data/              # Sample datasets
│   └── sample_sales_data.csv
│
└── README.md                  # This file
```

## ⭐ Key Features

- **🛡️ Privacy-First**: Synthetic data generation eliminates governance concerns
- **🤖 AI-Native**: GPT-4 integration with explainable AI insights
- **📊 Full Analytics**: Statistical analysis, ML modeling, and quality assessment
- **💬 Natural Language**: Plain English queries about your data
- **📖 Data Dictionary**: Business-focused documentation with approval workflows

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](./docs/guides/QUICKSTART.md)** - Get up and running in minutes
- **[Start Here](./docs/guides/START_HERE.md)** - First steps with NEX.AI
- **[Installation Guide](./docs/setup/INSTALLATION.md)** - Detailed installation instructions
- **[Setup Guide](./docs/setup/SETUP_GUIDE.md)** - Complete setup walkthrough

### Technical Documentation
- **[Docker Setup](./docs/docker.md)** - Complete container configuration
- **[API Reference](./docs/api.md)** - Full endpoint documentation
- **[Development](./docs/development.md)** - Local setup and debugging
- **[Testing](./docs/testing.md)** - Quality assurance and CI/CD

### Feature Guides
- **[Data Explorer](./docs/guides/START_DATA_EXPLORER.md)** - Database exploration guide
- **[MCP Setup](./docs/setup/MCP_DATA_EXPLORER_SETUP.md)** - Model Context Protocol configuration
- **[Next Steps](./docs/guides/NEXT_STEPS.md)** - What to do after setup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This is a prototype application for demonstration and research purposes.

---

**🚀 Ready to explore AI-native data management? Start with `docker compose -p zerostack up -d` and visit http://localhost:3000**

