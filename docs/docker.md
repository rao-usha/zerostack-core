# Docker Setup Guide

This guide explains how to run NEX.AI using Docker.

## Prerequisites

- Docker Desktop (or Docker Engine + Docker Compose)
- At least 2GB of free disk space
- Ports 3000 and 8000 available

## Quick Start (Production)

1. **Build and start containers:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Stop containers:**
   ```bash
   docker-compose down
   ```

## Development Mode

For development with hot reload:

```bash
docker-compose -f docker-compose.dev.yml up
```

This mounts your source code and enables:
- Backend hot reload (uvicorn --reload)
- Frontend dev server with HMR
- Easier debugging

## Building Images

### Build all images:
```bash
docker-compose build
```

### Build specific service:
```bash
docker-compose build backend
docker-compose build frontend
```

### Build with no cache:
```bash
docker-compose build --no-cache
```

## Environment Variables

Create a `.env` file in the root directory (optional):

```env
SECRET_KEY=your-secret-key-here
DEBUG=false
DATABASE_URL=sqlite:///./data_storage/datasets.db
LOG_LEVEL=INFO
```

Or set them in `docker-compose.yml` directly.

## Data Persistence

Backend data is persisted in `./backend/data_storage/` which is mounted as a volume. Your uploaded datasets and database will persist between container restarts.

## Troubleshooting

### Port already in use
If ports 3000 or 8000 are already in use, edit `docker-compose.yml`:
```yaml
ports:
  - "3001:80"  # Change frontend port
  - "8001:8000"  # Change backend port
```

### Container won't start
Check logs:
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Rebuild after code changes
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### View container status
```bash
docker-compose ps
```

### Execute commands in containers
```bash
# Backend shell
docker-compose exec backend /bin/bash

# Frontend shell
docker-compose exec frontend /bin/sh
```

### Clean everything (including volumes)
```bash
docker-compose down -v
docker system prune -a
```

## Health Checks

Both services include health checks:
- Backend: Checks `/` endpoint
- Frontend: Checks nginx status

View health status:
```bash
docker-compose ps
```

## Production Deployment

For production:

1. **Set strong SECRET_KEY** in environment
2. **Use proper database** (PostgreSQL instead of SQLite)
3. **Enable HTTPS** with reverse proxy (nginx/traefik)
4. **Set resource limits** in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

5. **Use docker-compose.prod.yml** (create with production settings)

## Services

- **backend**: FastAPI application on port 8000
- **frontend**: Nginx serving React app on port 3000 (mapped to 80 internally)

Both services are on the `nex-network` bridge network and can communicate via service names.

## Volume Mounts

- `./backend/data_storage` → `/app/data_storage` (backend data persistence)
- In dev mode: Source code is also mounted for hot reload

