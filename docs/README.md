# zerostack Documentation

Welcome to the zerostack documentation. This directory contains all technical documentation for the AI Native Data Platform.

## 📚 Documentation Structure

```
docs/
├── README.md                 # This file - documentation index
├── TECHNICAL_OVERVIEW.md     # Comprehensive technical documentation
│
├── features/                 # Feature documentation
│   ├── data-dictionary.md    # AI-powered data documentation
│   ├── ml-development.md     # ML recipe development & monitoring
│   ├── files.md              # Multi-source file management
│   ├── gdrive-integration.md # Google Drive integration
│   └── m5-dataset.md         # M5 forecasting dataset
│
├── setup/                    # Setup & installation guides
│   ├── INSTALLATION.md       # Installation instructions
│   ├── DATABASE_SETUP.md     # Database configuration
│   ├── ENVIRONMENT_VARIABLES.md
│   ├── MCP_DATA_EXPLORER_SETUP.md
│   └── ...
│
├── guides/                   # User guides & tutorials
│   ├── QUICKSTART.md         # Quick start guide
│   ├── START_HERE.md         # First steps
│   ├── START_DATA_EXPLORER.md
│   └── ...
│
├── testing/                  # Testing documentation
│   ├── README.md             # Testing overview
│   └── ...
│
├── plans/                    # Development roadmaps
│   ├── gpu-runner/
│   └── ml-compute-engine/
│
└── archive/                  # Historical documentation
    ├── bug-fixes/            # Bug fix notes
    └── implementation-notes/ # Implementation summaries
```

## 🚀 Quick Links

### Getting Started
- **[Quick Start](./guides/QUICKSTART.md)** - Get up and running in minutes
- **[Installation](./setup/INSTALLATION.md)** - Detailed setup instructions
- **[Docker Setup](./docker.md)** - Container configuration

### Features
- **[Data Dictionary](./features/data-dictionary.md)** - AI-powered database documentation
- **[ML Development](./features/ml-development.md)** - Recipe-based ML workflows
- **[Files](./features/files.md)** - Multi-source file management
- **[Google Drive](./features/gdrive-integration.md)** - Cloud storage integration

### Technical
- **[Technical Overview](./TECHNICAL_OVERVIEW.md)** - Complete system documentation
- **[API Reference](./api.md)** - API endpoints
- **[Development Guide](./development.md)** - Local development setup

### Testing
- **[Testing Guide](./testing.md)** - How to run tests
- **[Test Documentation](./testing/)** - Feature-specific test guides

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│                   http://localhost:3000                  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API + SSE
                         ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│                   http://localhost:8000                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │                 Domain Routers                     │  │
│  │  Chat │ Explorer │ ML Dev │ Dictionary │ Files    │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │                   LLM Providers                    │  │
│  │      OpenAI │ Anthropic │ Google │ xAI            │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│               PostgreSQL + pgvector                      │
│                   localhost:5432                         │
└─────────────────────────────────────────────────────────┘
```

## 📖 Main Features

| Feature | Description | Documentation |
|---------|-------------|---------------|
| **Data Dictionary** | AI-generated column documentation with versioning | [docs](./features/data-dictionary.md) |
| **ML Development** | Recipe-based ML workflows with monitoring | [docs](./features/ml-development.md) |
| **Data Explorer** | Database browsing and querying | [setup](./setup/DATA_EXPLORER_ENV_SETUP.md) |
| **Chat** | Multi-provider conversational AI | [guide](./guides/CHAT_WITH_DATA_COMPLETE.md) |
| **Files** | Multi-source file scanning and versioning | [docs](./features/files.md) |
| **Synthetic Data** | Privacy-safe data generation | [api](./api.md) |

## 🔧 Configuration

Key environment variables:

```bash
# Database
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex

# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Files Feature
FILES_ROOT=/path/to/files
FILES_CACHE_ROOT=/path/to/cache
```

See [Environment Variables](./setup/ENVIRONMENT_VARIABLES.md) for complete list.

## 📝 Contributing to Docs

When adding documentation:

1. **Features** → `docs/features/` - Comprehensive feature docs
2. **Setup guides** → `docs/setup/` - Installation and configuration
3. **User guides** → `docs/guides/` - How-to tutorials
4. **Testing** → `docs/testing/` - Test procedures
5. **Archive** → `docs/archive/` - Historical notes (read-only)

## 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Tailwind CSS](https://tailwindcss.com/docs)
