# GPU Runner Quick Start

Run ML models on remote GPU infrastructure with automatic results banking.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- (Optional) Remote GPU VM with SSH access

## Setup

### 1. Start Services

```bash
# From project root
docker compose -p nex up -d
```

This starts:
- PostgreSQL database
- MinIO object storage (S3-compatible)
- NEX backend API
- NEX frontend

### 2. Run Migration

```bash
cd backend
alembic upgrade head
```

### 3. Seed Data

```bash
cd backend
python -m scripts.seed_gpu_runner
```

### 4. Build Recipe Container

```bash
cd recipes/forecast_m5_v1
docker build -t nex/forecast-m5:v1 .
```

## Usage

### Access the UI

- Frontend: http://localhost:3000
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- API Docs: http://localhost:8000/docs

### Navigate to Highlighted Datasets

1. Go to http://localhost:3000/model-development/datasets
2. You'll see the M5 Forecasting dataset with `NOT_PRESENT` state

### Upload Dataset

1. Download M5 data from [Kaggle](https://www.kaggle.com/competitions/m5-forecasting-accuracy/data)
2. Click "Upload Data" on the M5 dataset card
3. Select the CSV files (calendar.csv, sales_train_validation.csv, sell_prices.csv)
4. Click "Upload Files"
5. State changes to `AVAILABLE`

### Run a Forecast

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/ml-development/runs \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_id": "recipe_m5_forecast_v1",
    "recipe_version_id": "ver_m5_forecast_v1_100",
    "run_type": "train",
    "compute_target": "local"
  }'
```

### View Results

1. Go to http://localhost:3000/model-development/assets
2. Successful runs automatically create temporal assets
3. Promote valuable results to permanent

## Configuration

### Local Development (Default)

```env
COMPUTE_ADAPTER=local
```

### SSH to Remote GPU

```env
COMPUTE_ADAPTER=ssh
SSH_HOST=your-gpu-vm.example.com
SSH_USER=ubuntu
SSH_KEY_PATH=/path/to/key.pem
```

### Kubernetes Gateway

```env
COMPUTE_ADAPTER=k8s_gateway
K8S_GATEWAY_URL=http://gateway.example.com
K8S_NAMESPACE=nex-compute
```

## API Endpoints

### Highlighted Datasets

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/highlighted-datasets` | List all datasets |
| `POST /api/v1/highlighted-datasets/{id}/resolve` | Check/trigger availability |
| `POST /api/v1/highlighted-datasets/{id}/upload` | Upload data file |
| `POST /api/v1/highlighted-datasets/{id}/upload/complete` | Finalize upload |

### Derived Assets

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/ml-development/assets` | List all assets |
| `POST /api/v1/ml-development/assets/{id}/promote` | Promote to permanent |
| `DELETE /api/v1/ml-development/assets/{id}` | Delete asset |

## Architecture

```
┌─────────────────┐      ┌─────────────────┐
│  Highlighted    │      │    ml_run       │
│   Datasets      │─────▶│  (extended)     │
│  (catalog)      │      │  + compute_target│
└─────────────────┘      └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │ ComputeAdapter  │
                         │ (local/ssh/k8s) │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │  Recipe Container│
                         │  (forecast_m5)  │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │ DerivedAsset    │
                         │ (temporal/perm) │
                         └─────────────────┘
```

## Troubleshooting

### MinIO not accessible
```bash
# Check if MinIO is running
docker logs nex-minio

# Manually create bucket
docker exec nex-minio mc mb local/nex-data
```

### Migration fails
```bash
# Check current revision
alembic current

# Run specific migration
alembic upgrade 020_add_gpu_runner
```

### Container build fails
```bash
# Build with no cache
docker build --no-cache -t nex/forecast-m5:v1 .
```

## Files Created

```
backend/
├── domains/highlighted_datasets/   # New domain
├── services/object_store/          # S3 client
├── services/compute/               # Compute adapters
├── services/interaction_logger.py  # Audit logging
├── migrations/versions/020_*.py    # Schema migration
└── scripts/seed_gpu_runner.py      # Seed data

frontend/src/pages/
├── HighlightedDatasets.tsx         # Dataset catalog UI
└── DerivedAssets.tsx               # Assets management UI

recipes/forecast_m5_v1/             # Containerized recipe
├── Dockerfile
├── requirements.txt
└── run.py

docs/plans/gpu-runner/              # Implementation plan
├── PLAN.md
└── CHANGELOG.md
```
