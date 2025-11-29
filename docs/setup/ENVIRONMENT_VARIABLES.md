# Environment Variables Configuration

This guide explains how to configure environment variables for NEX.AI.

## Quick Start

For Docker deployment, most environment variables are already configured in `config/docker-compose.dev.yml`. You only need to set your OpenAI API key.

### Create `.env` file in project root:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here
```

That's it! The Data Explorer will automatically connect to the main NEX database.

## All Available Environment Variables

### Required

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for AI features | None (required) |

### Optional: Additional LLM Providers

| Variable | Description | Used For |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Chat with Data |
| `GOOGLE_API_KEY` | Google Gemini API key | Chat with Data |
| `XAI_API_KEY` | xAI Grok API key | Chat with Data |

### Data Explorer Configuration

By default, the Data Explorer connects to the main NEX database. You can override these to explore a different database:

| Variable | Description | Default |
|----------|-------------|---------|
| `EXPLORER_DB_HOST` | Database host | `localhost` (or `db` in Docker) |
| `EXPLORER_DB_PORT` | Database port | `5432` |
| `EXPLORER_DB_USER` | Database user | `nex` |
| `EXPLORER_DB_PASSWORD` | Database password | `nex` |
| `EXPLORER_DB_NAME` | Database name | `nex` |

### Multiple Databases (Advanced)

You can configure up to 5 additional databases for the Data Explorer:

**Database 2:**
- `EXPLORER2_DB_HOST`
- `EXPLORER2_DB_PORT`
- `EXPLORER2_DB_USER`
- `EXPLORER2_DB_PASSWORD`
- `EXPLORER2_DB_NAME`

**Database 3:**
- `EXPLORER3_DB_HOST`
- `EXPLORER3_DB_PORT`
- `EXPLORER3_DB_USER`
- `EXPLORER3_DB_PASSWORD`
- `EXPLORER3_DB_NAME`

And so on up to `EXPLORER5_DB_*`.

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |
| `DATABASE_URL` | Main database URL | `postgresql+psycopg://nex:nex@localhost:5432/nex` |
| `SECRET_KEY` | Application secret key | Auto-generated |

## Docker Configuration

When using Docker Compose, environment variables are set in `config/docker-compose.dev.yml`. The only variable you need to provide in your `.env` file is:

```bash
OPENAI_API_KEY=your-key-here
```

The Docker configuration automatically:
- Sets up the main NEX database connection
- Configures the Data Explorer to use the main database
- Sets appropriate defaults for development

## Local Development (Non-Docker)

If running locally without Docker, create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key-here

# Database (adjust if needed)
DATABASE_URL=postgresql+psycopg://nex:nex@localhost:5432/nex

# Data Explorer (points to main database by default)
EXPLORER_DB_HOST=localhost
EXPLORER_DB_PORT=5432
EXPLORER_DB_USER=nex
EXPLORER_DB_PASSWORD=nex
EXPLORER_DB_NAME=nex
```

## Exploring External Databases

To explore a database other than the main NEX database:

1. Set the `EXPLORER_DB_*` variables to point to your target database
2. Restart the backend service
3. The Data Explorer will now connect to your specified database

Example for exploring a production database:

```bash
EXPLORER_DB_HOST=prod-db.example.com
EXPLORER_DB_PORT=5432
EXPLORER_DB_USER=readonly_user
EXPLORER_DB_PASSWORD=secure_password
EXPLORER_DB_NAME=production_db
```

**Security Note:** The Data Explorer enforces read-only access for safety.

## Troubleshooting

### "Database Connection Failed" in Data Explorer

This usually means the `EXPLORER_DB_*` variables aren't set correctly.

**Solution for Docker users:**
- No action needed! The defaults in `docker-compose.dev.yml` should work
- If you see this error, restart the containers:
  ```bash
  docker-compose -f config/docker-compose.dev.yml down
  docker-compose -f config/docker-compose.dev.yml up -d
  ```

**Solution for local development:**
- Ensure your `.env` file has the correct database credentials
- Verify the database is running and accessible
- Check that the port is correct (5432 for the main NEX database)

### Missing OpenAI API Key

If AI features aren't working:

1. Create a `.env` file in the project root
2. Add: `OPENAI_API_KEY=your-key-here`
3. Restart the services

## See Also

- [Installation Guide](INSTALLATION.md)
- [Data Explorer Setup](DATA_EXPLORER_ENV_SETUP.md)
- [Docker Setup](../docker.md)

