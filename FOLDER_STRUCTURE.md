# NEX.AI Folder Structure

This document describes the organized folder structure of the NEX.AI project.

## 📁 Root Directory Organization

### Core Application Folders

- **`backend/`** - Main FastAPI data platform
  - Core business logic, API endpoints, and services
  - Database models and migrations
  - Domain-driven design structure

- **`frontend/`** - React TypeScript UI
  - Modern web interface built with Vite
  - Component-based architecture
  - Tailwind CSS styling

- **`nex-collector/`** - Data distillation pipeline
  - Context generation and aggregation
  - AI-powered data distillation
  - Pre-built data packs

### Supporting Folders

- **`docs/`** - 📚 All project documentation
  - `guides/` - User guides and tutorials
  - `setup/` - Installation and setup instructions
  - Technical documentation (API, development, testing)

- **`config/`** - ⚙️ Configuration files
  - Docker Compose files (dev, prod, CI)
  - Build configurations (Makefile, pytest.ini)
  - Development dependencies

- **`scripts/`** - 🔧 Utility and automation scripts
  - Installation scripts
  - Start/stop scripts
  - Data seeding scripts
  - CI/CD automation

- **`tests/`** - 🧪 Root-level test files
  - Integration tests
  - API tests
  - End-to-end tests

- **`example_data/`** - Sample datasets for testing

## 📄 Key Files in Root

- **`README.md`** - Main project documentation (start here!)
- **`FOLDER_STRUCTURE.md`** - This file

## 🗂️ Documentation Organization

### `docs/guides/`
Quick start guides and feature tutorials:
- `START_HERE.md` - First steps
- `QUICKSTART.md` - Quick start guide
- `START_DATA_EXPLORER.md` - Data Explorer guide
- `NEXT_STEPS.md` - What to do after setup

### `docs/setup/`
Installation and configuration guides:
- `INSTALLATION.md` - Installation instructions
- `SETUP_GUIDE.md` - Complete setup walkthrough
- `DATA_EXPLORER_ENV_SETUP.md` - Data Explorer setup
- `MCP_DATA_EXPLORER_SETUP.md` - MCP configuration

### `docs/` (root level)
Technical documentation:
- `api.md` - API reference
- `development.md` - Development guide
- `docker.md` - Docker setup
- `testing.md` - Testing guide
- `BRANDING.md` - Brand guidelines
- `COLOR_SCHEME.md` - Design system

## 🔧 Scripts Organization

### Installation & Setup
- `install_all.sh` - Install all dependencies
- `install_node.sh` - Install Node.js
- `check_setup.sh` - Verify installation

### Running Services
- `start.sh` - Start all services
- `start_backend.sh` - Start backend only
- `start_frontend.sh` - Start frontend only

### Data Management
- `load_data_packs.py` - Load sample data packs
- `load_packs.py` - Alternative data loader
- `seed_nex_collector.py` - Seed distillation data

### CI/CD & Testing
- `agent_ci.sh` - CI automation
- `run_summarization_tests.sh` - Run summarization tests

## ⚙️ Configuration Files

### Docker
- `docker-compose.yml` - Production deployment
- `docker-compose.dev.yml` - Development environment
- `docker-compose.ci.yml` - CI/CD configuration

### Build & Test
- `Makefile` - Build automation commands
- `pytest.ini` - Test configuration
- `requirements-dev.txt` - Development dependencies

## 🧪 Tests Organization

Root-level integration and API tests:
- `test_context_api.py` - Context API tests
- `test_document_upload.py` - Document upload tests
- `test_summarization_full.py` - Full summarization tests
- `test_summarization_integration.py` - Integration tests

Note: Each service (`backend/`, `nex-collector/`) also has its own `tests/` folder for unit tests.

## 🚀 Quick Navigation

| I want to... | Go to... |
|-------------|----------|
| Get started quickly | `docs/guides/START_HERE.md` |
| Install the platform | `docs/setup/INSTALLATION.md` |
| Learn the API | `docs/api.md` |
| Run tests | `docs/testing.md` or `docs/RUN_TESTS.md` |
| Configure Docker | `config/docker-compose.dev.yml` |
| Start services | `scripts/start.sh` |
| Load sample data | `scripts/load_data_packs.py` |

## 📝 Notes

- All markdown documentation has been moved to `docs/` for better organization
- Configuration files are centralized in `config/` for easier management
- Scripts are consolidated in `scripts/` for quick access
- Tests are organized by scope (root-level integration, service-level unit)

---

**Need help?** Check `README.md` or explore the `docs/guides/` folder!

