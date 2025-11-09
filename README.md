# NEX.AI

## AI Native Data Platform

A comprehensive, AI-powered data platform that serves as a one-stop solution for all data-related needs in large organizations. This platform eliminates data governance concerns while providing powerful analytics, predictive modeling, and **AI-native data distillation** capabilities.

## 🚀 Quick Start (Docker)

```bash
# Clone and start everything
git clone <repository-url>
cd Nex

# Start all services (database, backend, frontend, distillation)
docker-compose -f docker-compose.dev.yml up -d

# Seed sample distillation data
```bash
docker exec nex-collector-api-1 python scripts/seed_demo.py
```

**Access:** http://localhost:3000

**Features to explore:**
- 📊 **Data Upload & Analysis** - CSV datasets with AI insights
- 🤖 **Predictive Modeling** - One-click ML models with feature importance
- 🔄 **Synthetic Data** - Privacy-safe synthetic dataset generation
- 🧪 **Distillation Explorer** - Browse AI-generated contexts and training data

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
   - Identify missing features and data gaps using ML
   - Temporal coverage analysis and gap filling recommendations
   - Data diversity assessment and bias detection
   - Relationship gap detection with network analysis

8. **🆕 Data Distillation Explorer**
   - **NEW**: Explore contexts and synthetic datasets from distillation pipeline
   - Browse AI-generated domain knowledge and context variants
   - View distillation statistics and dataset metadata
   - Interactive exploration of fine-tune packs and training data

## 🏗️ Architecture

NEX.AI consists of three interconnected services:

### 🔧 **Core Services**
- **Main Backend** (Port 8000) - Core data platform with analytics, ML, and synthetic data generation
- **Frontend** (Port 3000) - Modern React UI for data exploration and management
- **NEX-Collector** (Port 8080) - Data distillation pipeline for context aggregation and dataset building

### 🗃️ **Databases & Infrastructure**
- **PostgreSQL + pgvector** (Port 5432) - Vector database for embeddings and relational data
- **NEX-Collector DB** - Separate instance for distillation metadata
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

# Start all services (database, backend, frontend, distillation)
docker-compose -f docker-compose.dev.yml up -d

# Seed sample distillation data (optional)
docker exec nex-collector-api-1 python scripts/seed_demo.py

# View logs (optional)
docker-compose -f docker-compose.dev.yml logs -f
```

### Access Points
- **Frontend UI**: http://localhost:3000
- **Main API Docs**: http://localhost:8000/docs
- **Distillation API**: http://localhost:8080/docs
- **Health Checks**: All services include health endpoints

### Docker Commands

```bash
# Stop services
docker-compose -f docker-compose.dev.yml down

# Rebuild after code changes
docker-compose -f docker-compose.dev.yml build --no-cache

# View container status
docker-compose -f docker-compose.dev.yml ps

# Execute commands in containers
docker-compose -f docker-compose.dev.yml exec backend bash
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

### 🧪 **🆕 Distillation Explorer**
- **NEW**: Explore AI-generated contexts and variants
- Browse domain knowledge across personas/tasks/styles
- View distillation pipeline statistics
- Interactive exploration of fine-tune datasets
- Sample data packs for retail, insurance, and finance domains

## 🔌 API Documentation

- **Main Backend**: http://localhost:8000/docs (Swagger UI)
- **Distillation API**: http://localhost:8080/docs (Swagger UI)

### Key Endpoints
- `POST /api/upload` - Upload and analyze CSV datasets
- `POST /api/synthetic/generate` - Create privacy-safe synthetic data
- `POST /api/models/predictive` - Build ML models with explanations
- `POST /api/insights/generate` - Generate AI-powered insights
- `POST /api/chat` - Natural language data queries

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
│   │   │   ├── SyntheticData.tsx
│   │   │   └── Distillation.tsx # 🆕 NEW
│   │   ├── components/       # Reusable components
│   │   ├── api/              # API client
│   │   └── App.tsx           # Main app component
│   ├── package.json
│   └── tailwind.config.js
│
├── nex-collector/             # Data distillation pipeline
│   ├── app/
│   │   ├── routes/           # API routes
│   │   ├── distill/          # Distillation pipeline
│   │   │   ├── sampler.py    # Example sampling
│   │   │   ├── builder.py    # Dataset building
│   │   │   └── rationales.py # Teacher outputs
│   │   ├── ingest/           # Data ingestion
│   │   │   ├── generator.py  # Context generation
│   │   │   └── embed.py      # Vector embeddings
│   │   └── providers/        # LLM providers
│   ├── data/packs/           # Pre-built datasets
│   │   ├── retail-customer-service@1.0.0/
│   │   ├── insurance-underwriter-risk-assessment@1.0.0/
│   │   └── macys-retail-customer-service@1.0.0/
│   └── scripts/              # Seed and utility scripts
│       ├── seed_demo.py      # Demo data seeding
│       └── seed_insurance_dataset.py
│
├── docker-compose.yml        # Production deployment
├── docker-compose.dev.yml    # Development environment
└── README.md
```

## 📦 Sample Data Packs

NEX includes pre-built distillation data packs for immediate exploration:
- **🛍️ Retail Customer Service** - Macy's support scenarios with multiple personas
- **💼 Insurance Underwriting** - Risk assessment with different tolerance levels
- **🏦 Finance Analysis** - CFO persona for financial decision-making
- **🏪 General Retail** - Broad retail contexts for domain generalization

## ⭐ Key Features

- **🛡️ Privacy-First**: Synthetic data generation eliminates governance concerns
- **🤖 AI-Native**: GPT-4 integration with explainable AI insights
- **🔬 Data Distillation**: Teacher-student distillation for specialized models
- **📊 Full Analytics**: Statistical analysis, ML modeling, and quality assessment
- **💬 Natural Language**: Plain English queries about your data

## 📚 Documentation

- **[Docker Setup](./docs/docker.md)** - Complete container configuration
- **[API Reference](./docs/api.md)** - Full endpoint documentation
- **[Development](./docs/development.md)** - Local setup and debugging
- **[Testing](./docs/testing.md)** - Quality assurance and CI/CD

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This is a prototype application for demonstration and research purposes.

---

**🚀 Ready to explore AI-native data distillation? Start with `docker-compose -f docker-compose.dev.yml up -d` and visit http://localhost:3000**

