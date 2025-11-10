# API Documentation

## Service Endpoints

### Main Backend (Port 8000)
- **Base URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/healthz

### NEX-Collector (Port 8080)
- **Base URL**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs (Swagger UI)
- **Health Check**: http://localhost:8080/healthz

### Frontend (Port 3000)
- **Base URL**: http://localhost:3000
- **UI**: Modern React application

## Main Backend API Endpoints

### Data Management
- `POST /api/upload` - Upload CSV datasets with automatic processing
- `GET /api/datasets` - List all uploaded datasets
- `GET /api/dataset/{dataset_id}` - Get detailed dataset information

### AI Features
- `POST /api/synthetic/generate` - Generate privacy-safe synthetic data
- `POST /api/models/predictive` - Build ML models (regression/classification)
- `POST /api/insights/generate` - Generate AI-powered strategic insights
- `POST /api/chat` - Natural language queries about datasets
- `GET /api/quality/{dataset_id}` - Comprehensive data quality assessment
- `GET /api/knowledge-gaps/{dataset_id}` - Identify missing data and gaps

### Context Management
- `GET /api/v1/contexts` - List available contexts
- `POST /api/v1/contexts` - Create new context
- `GET /api/v1/contexts/{id}` - Get context details
- `POST /api/v1/contexts/{id}/documents` - Upload documents to context
- `POST /api/v1/contexts/{id}/layers` - Add context processing layers

## NEX-Collector API Endpoints

### Context Aggregation
- `GET /v1/contexts/variants` - List all context variants with filtering
- `GET /v1/contexts/variants/{id}` - Get specific variant details
- `POST /v1/contexts/variants/compose` - Mix & match variants to create new contexts
- `POST /v1/aggregate/sample` - Generate new contexts via LLM sampling

### Dataset Distillation
- `POST /v1/datasets/distill/examples` - Generate synthetic training examples
- `POST /v1/datasets/distill/build` - Build fine-tune datasets from examples
- `GET /v1/datasets` - List all distilled datasets
- `GET /v1/datasets/{id}` - Get dataset manifest details

### Context Documents
- `POST /v1/contexts` - Create new context documents
- `GET /v1/contexts/{id}` - Get context document details
- `POST /v1/contexts/{id}/variants` - Create context variants

## Authentication

The NEX-Collector service uses a simple token-based authentication:
- **Header**: `Authorization: Bearer dev-secret`
- **Default Token**: `dev-secret` (for development)

## Data Formats

### Dataset Upload
```json
POST /api/upload
Content-Type: multipart/form-data

{
  "file": "<CSV file>",
  "name": "dataset_name",
  "description": "optional description"
}
```

### Synthetic Data Generation
```json
POST /api/synthetic/generate
{
  "dataset_id": "ds-1234567890",
  "num_rows": 1000,
  "quality_threshold": 0.95
}
```

### Predictive Model Building
```json
POST /api/models/predictive
{
  "dataset_id": "ds-1234567890",
  "target_column": "sales",
  "model_type": "regression",
  "test_size": 0.2
}
```

### AI Insights Generation
```json
POST /api/insights/generate
{
  "dataset_id": "ds-1234567890",
  "context": "retail business analysis",
  "focus_areas": ["trends", "anomalies", "correlations"]
}
```

### Natural Language Chat
```json
POST /api/chat
{
  "query": "What are the top selling products?",
  "dataset_id": "ds-1234567890",
  "context": "sales analysis"
}
```

## Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Descriptive error message",
  "details": { ... }
}
```

## Rate Limiting

- **Main Backend**: No rate limiting in development
- **NEX-Collector**: No rate limiting in development
- **OpenAI API**: Subject to OpenAI rate limits (depends on your API plan)

## Error Codes

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid API key/token)
- `404` - Not Found (resource doesn't exist)
- `422` - Validation Error (invalid data format)
- `500` - Internal Server Error (server-side issues)

## WebSocket Support

Real-time features are planned for future releases. Currently, all interactions are REST-based.

## SDKs and Libraries

No official SDKs are available yet. Use standard HTTP clients:
- **Python**: `requests` or `httpx`
- **JavaScript**: `fetch` or `axios`
- **cURL**: Command-line HTTP client

## Examples

### Upload Dataset
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@data.csv" \
  -F "name=My Dataset"
```

### Generate Insights
```bash
curl -X POST http://localhost:8000/api/insights/generate \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "ds-1234567890",
    "context": "business analysis"
  }'
```

### Chat Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key trends?",
    "dataset_id": "ds-1234567890"
  }'
```

## Monitoring

### Health Endpoints
- `GET /healthz` - Basic health check
- `GET /health/config` - Configuration validation
- `GET /health/db` - Database connectivity check

### Logs
- Container logs: `docker-compose logs -f [service]`
- Application logs: Available in container stdout/stderr

## Troubleshooting

### Common Issues

1. **"Dataset not found"**
   - Ensure dataset ID is correct
   - Check if dataset upload completed successfully

2. **"OpenAI API key not configured"**
   - Set `OPENAI_API_KEY` environment variable
   - Restart backend service

3. **"Context variant not found"**
   - Verify variant ID exists
   - Check NEX-Collector service is running

4. **"Rate limit exceeded"**
   - OpenAI API limits reached
   - Wait or upgrade API plan

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
docker-compose restart backend
```

## Versioning

- **API Version**: v1 (current)
- **Breaking Changes**: Communicated via GitHub releases
- **Deprecation**: 3-month notice period

## Support

- **Documentation**: This API reference
- **Interactive Docs**: `/docs` endpoints when services are running
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
