# Setting Up Context Engineering

Follow these steps to get Context Engineering working:

## 1. Restart Backend (to pick up new routes)

```bash
# If running in Docker:
docker-compose restart backend

# Or rebuild if needed:
docker-compose up -d --build backend

# If running locally:
# Stop the backend and restart it
```

## 2. Run Database Migrations (to create new tables)

```bash
# Enter the backend container
docker-compose exec backend bash

# Or if running locally, cd into backend directory
cd backend

# Run migrations
alembic upgrade head
```

If you get an error about missing tables, you may need to create a new migration:

```bash
# Create a new migration for the context tables
alembic revision -m "add_context_engineering_tables"

# Then edit the migration file to include:
# - context_layers table
# - context_dictionaries table  
# - Updated context_versions table with digest and layers columns

# Or auto-generate:
alembic revision --autogenerate -m "add_context_engineering_tables"

# Then apply:
alembic upgrade head
```

## 3. Restart Frontend (to see new UI)

```bash
# If running in Docker:
docker-compose restart frontend

# Or rebuild if needed:
docker-compose up -d --build frontend

# If running locally with Vite:
# The frontend should hot-reload automatically
# Or restart the dev server
```

## 4. Access the UI

1. Open your browser to `http://localhost:3000` (or your frontend URL)
2. Click on "Contexts" in the sidebar
3. Start creating contexts!

## Verification

Test the API directly:

```bash
# List contexts
curl -H "X-Org-ID: demo" http://localhost:8000/api/v1/contexts

# Create a context
curl -X POST http://localhost:8000/api/v1/contexts \
  -H "Content-Type: application/json" \
  -H "X-Org-ID: demo" \
  -d '{
    "name": "Test Context",
    "description": "A test context"
  }'
```

## Troubleshooting

- **404 on contexts routes**: Backend not restarted - restart it
- **Database errors**: Migrations not run - run migrations
- **UI not showing**: Frontend not restarted - restart it
- **CORS errors**: Check backend CORS settings in `core/config.py`

