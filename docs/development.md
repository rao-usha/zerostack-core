# Development Guide

## Prerequisites

### System Requirements
- **Python 3.11+**
- **Node.js 18+**
- **PostgreSQL 16+** (with pgvector extension)
- **Redis 7+**
- **Docker Desktop** (optional, for containerized development)

### API Keys
- **OpenAI API Key** (required for AI features)
- Get from: https://platform.openai.com/api-keys

## Local Development Setup

### Option 1: Docker Development (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd Nex

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Seed sample data (optional)
docker exec nex-collector-api-1 python scripts/seed_demo.py

# Access application
open http://localhost:3000
```

### Option 2: Manual Setup

#### 1. Database Setup

```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name nex_db \
  -e POSTGRES_USER=nex \
  -e POSTGRES_PASSWORD=nex \
  -e POSTGRES_DB=nex \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# Start Redis
docker run -d \
  --name nex-redis \
  -p 6380:6379 \
  redis:7
```

#### 2. Environment Configuration

Create `.env` file:
```bash
# OpenAI API Key (required)
OPENAI_API_KEY=sk-your-openai-key-here

# Database
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex

# Development settings
DEBUG=true
LOG_LEVEL=DEBUG

# CORS settings
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### 3. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py
```

#### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 5. NEX-Collector Setup (Optional)

```bash
cd nex-collector

# Install dependencies (if not using Docker)
pip install -r requirements.txt

# Run collector service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## Project Structure

```
Nex/
├── backend/                    # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── core/                  # Core configuration
│   ├── domains/               # Business logic modules
│   │   ├── datasets/         # Dataset management
│   │   ├── contexts/         # Context engineering
│   │   ├── insights/         # AI insights generation
│   │   ├── models/           # Predictive modeling
│   │   └── evaluations/      # Model evaluation
│   └── services/             # Core business services
│       ├── synthetic_data.py # Privacy-safe data generation
│       ├── data_quality.py   # Quality assessment
│       ├── insights.py       # Insights generation
│       └── chat.py           # Natural language processing
│
├── frontend/                  # React TypeScript UI
│   ├── src/
│   │   ├── pages/            # Page components
│   │   ├── components/       # Reusable UI components
│   │   ├── api/              # API client
│   │   └── App.tsx           # Main application component
│   ├── package.json
│   └── vite.config.ts        # Build configuration
│
├── nex-collector/             # Data distillation pipeline
│   ├── app/
│   │   ├── routes/           # API endpoints
│   │   ├── distill/          # Distillation algorithms
│   │   ├── ingest/           # Data ingestion pipeline
│   │   └── providers/        # LLM providers (OpenAI, etc.)
│   ├── scripts/              # Utility scripts
│   └── data/packs/           # Pre-built distillation datasets
│
└── docs/                     # Documentation
    ├── api.md               # API reference
    ├── docker.md            # Docker setup
    ├── development.md       # This file
    └── testing.md           # Testing guide
```

## Development Workflow

### 1. Code Changes

```bash
# Backend changes
cd backend
# Make changes to Python files
# Backend auto-reloads in Docker dev mode

# Frontend changes
cd frontend
# Make changes to React/TypeScript files
# Frontend hot-reloads automatically
```

### 2. Database Migrations

```bash
# Backend database changes
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head

# NEX-Collector database changes
cd nex-collector
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### 3. Testing

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests (if configured)
cd frontend
npm test
```

### 4. Building

```bash
# Build all Docker images
docker-compose build

# Build specific service
docker-compose build backend

# Build frontend for production
cd frontend
npm run build
```

## Debugging

### Backend Debugging

```bash
# View logs
docker-compose logs -f backend

# Execute commands in container
docker-compose exec backend bash

# Debug Python code
docker-compose exec backend python -c "import pdb; pdb.set_trace()"
```

### Frontend Debugging

```bash
# View browser console
# Open DevTools in browser at http://localhost:3000

# View build logs
cd frontend
npm run dev  # Shows compilation errors

# Check for linting issues
npm run lint
```

### Database Debugging

```bash
# Connect to database
docker-compose exec db psql -U nex -d nex

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v  # Removes volumes
docker-compose up -d db
```

## Environment Variables

### Required
- `OPENAI_API_KEY` - OpenAI API key for AI features

### Optional
- `DEBUG` - Enable debug mode (default: false)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS` - Allowed CORS origins (comma-separated)

### Docker-Specific
- `VITE_API_URL` - Frontend API URL for Docker builds

## Code Quality

### Linting and Formatting

```bash
# Backend (if configured)
cd backend
black .                    # Format Python code
ruff check .              # Lint Python code
mypy .                    # Type checking

# Frontend
cd frontend
npm run lint             # ESLint
npm run format           # Prettier
```

### Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## API Development

### Backend API Testing

```bash
# Manual testing
curl -X GET http://localhost:8000/healthz

# Using HTTPie
pip install httpie
http GET http://localhost:8000/api/datasets

# Using Postman/Insomnia
# Import from docs/api.md examples
```

### Frontend API Integration

```bash
# Check API client
cd frontend/src/api
# Update client.ts for new endpoints

# Test API calls
cd frontend
npm run dev
# Use browser network tab to inspect API calls
```

## Performance Monitoring

### Application Metrics

```bash
# Backend health checks
curl http://localhost:8000/healthz

# Database performance
docker-compose exec db psql -U nex -d nex -c "SELECT * FROM pg_stat_activity;"

# Memory usage
docker stats
```

### Profiling

```bash
# Python profiling (backend)
pip install py-spy
py-spy top --pid $(pgrep -f "uvicorn")

# React profiling (frontend)
# Use React DevTools Profiler tab
```

## Deployment

### Production Considerations

1. **Environment Variables**
   - Use strong `SECRET_KEY`
   - Configure proper `DATABASE_URL`
   - Set production `CORS_ORIGINS`

2. **Security**
   - Enable HTTPS with reverse proxy
   - Configure proper authentication
   - Use environment-specific API keys

3. **Scaling**
   - Use `docker-compose.prod.yml` for production
   - Configure resource limits
   - Set up monitoring and logging

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml build

# Deploy
docker-compose -f docker-compose.yml up -d

# Set up reverse proxy (nginx example)
docker run -d \
  --name nginx-proxy \
  -p 80:80 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf \
  nginx
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key not configured"**
   ```bash
   # Check environment
   docker-compose exec backend env | grep OPENAI

   # Update .env file
   echo "OPENAI_API_KEY=sk-your-key" >> .env
   docker-compose restart backend
   ```

2. **Database connection failed**
   ```bash
   # Check database status
   docker-compose ps db

   # View database logs
   docker-compose logs db

   # Reset database
   docker-compose down -v
   docker-compose up -d db
   ```

3. **Port conflicts**
   ```bash
   # Find process using port
   lsof -i :8000

   # Change port in docker-compose.yml
   sed -i 's/8000:8000/8001:8000/' docker-compose.yml
   docker-compose up -d
   ```

4. **Frontend build fails**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **Documentation**: Check this development guide first
- **Logs**: Always check container logs: `docker-compose logs -f [service]`

## Contributing Guidelines

1. **Code Style**
   - Follow existing patterns
   - Use type hints in Python
   - Use TypeScript in frontend
   - Run linters before committing

2. **Testing**
   - Write tests for new features
   - Ensure existing tests pass
   - Test both happy path and error cases

3. **Documentation**
   - Update docs for API changes
   - Add docstrings to Python functions
   - Update this guide for new workflows

4. **Commits**
   - Use clear, descriptive commit messages
   - Reference issue numbers when applicable
   - Keep commits focused and atomic
