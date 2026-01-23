# Feature Store - Comprehensive Planning Document

## Executive Summary

A Feature Store is a centralized repository for storing, versioning, and serving machine learning features. It enables:
- **Reusability** - Define features once, use across multiple models
- **Consistency** - Same feature logic for training and inference
- **Point-in-time correctness** - Prevent data leakage in training
- **Discovery** - Find and share features across teams
- **Governance** - Track feature lineage and usage

This document outlines the architecture, implementation, and integration of a Feature Store for the NEX platform.

---

## Table of Contents

1. [What is a Feature Store?](#1-what-is-a-feature-store)
2. [Use Cases & Business Value](#2-use-cases--business-value)
3. [Core Concepts](#3-core-concepts)
4. [Architecture Design](#4-architecture-design)
5. [Database Schema](#5-database-schema)
6. [API Design](#6-api-design)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Integration Points](#8-integration-points)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. What is a Feature Store?

### 1.1 Definition

A Feature Store is a data management layer specifically designed for machine learning features. It sits between raw data sources and ML models, providing:

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│  Raw Data   │───>│  Feature Store  │───>│  ML Models  │
│  Sources    │    │                 │    │             │
└─────────────┘    │  - Transform    │    └─────────────┘
                   │  - Store        │
                   │  - Version      │
                   │  - Serve        │
                   └─────────────────┘
```

### 1.2 Why Feature Stores Matter

| Problem | Without Feature Store | With Feature Store |
|---------|----------------------|-------------------|
| **Duplicate Work** | Each model rebuilds same features | Define once, reuse everywhere |
| **Training/Serving Skew** | Different code paths cause bugs | Single source of truth |
| **Data Leakage** | Accidentally use future data | Point-in-time lookups |
| **Discovery** | Features hidden in notebooks | Searchable catalog |
| **Freshness** | Manual updates | Automated pipelines |

### 1.3 Feature Store vs. Data Warehouse

| Aspect | Data Warehouse | Feature Store |
|--------|---------------|---------------|
| **Primary Users** | Analysts, BI | ML Engineers, Data Scientists |
| **Data Model** | Star/Snowflake schema | Entity-centric features |
| **Time Semantics** | Current state | Point-in-time historical |
| **Access Pattern** | Batch queries | Low-latency serving |
| **Versioning** | Schema versions | Feature definition versions |

---

## 2. Use Cases & Business Value

### 2.1 Primary Use Cases

#### 2.1.1 Feature Reusability
```
Before:                          After:
┌─────────┐                     ┌─────────┐
│ Model A │ age_bucket logic    │ Model A │──┐
└─────────┘                     └─────────┘  │
┌─────────┐                     ┌─────────┐  │  ┌──────────────┐
│ Model B │ age_bucket logic    │ Model B │──┼─>│ age_bucket   │
└─────────┘ (copy-pasted)       └─────────┘  │  │ feature def  │
┌─────────┐                     ┌─────────┐  │  └──────────────┘
│ Model C │ age_bucket logic    │ Model C │──┘
└─────────┘ (slightly different) └─────────┘
```

**Value:** 50-80% reduction in feature engineering time

#### 2.1.2 Training/Serving Consistency

```python
# PROBLEM: Training vs Serving Skew
# Training code (Python)
df['age_bucket'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 100])

# Serving code (Java) - subtle bug!
if (age < 18) bucket = "young";      // Bug: should be <=
else if (age < 35) bucket = "adult";
```

**With Feature Store:** Same transformation code used everywhere

#### 2.1.3 Point-in-Time Correctness

```
Timeline:  ──────────────────────────────────────>
           Jan 1        Jan 15        Feb 1

User signs up ─┐
               │
               ▼
User purchases ──────────┐
                         │
                         ▼
Train model ─────────────────────────┐
                                     │
Without PIT: Model sees Jan 15       │
purchase when training on Jan 1      ▼
user signup = DATA LEAKAGE!
```

**With Feature Store:** Get features as-of specific timestamp

#### 2.1.4 Feature Discovery

```
Data Scientist: "I need user engagement features"

Without Feature Store:
- Search through old notebooks
- Ask colleagues on Slack
- Rebuild from scratch

With Feature Store:
- Search catalog: "engagement"
- Find: user_click_rate, user_session_duration, user_page_views
- One-click add to training set
```

### 2.2 Business Value Quantification

| Benefit | Typical Impact |
|---------|----------------|
| Feature engineering time | 50-80% reduction |
| Model development cycle | 30-40% faster |
| Feature-related bugs | 60-70% reduction |
| Onboarding new team members | 50% faster |
| Feature governance/compliance | Fully auditable |

---

## 3. Core Concepts

### 3.1 Entities

An **Entity** represents a business object that features describe.

```python
# Entity examples
entities = [
    Entity(name="user", join_keys=["user_id"]),
    Entity(name="product", join_keys=["product_id"]),
    Entity(name="transaction", join_keys=["user_id", "product_id"]),
]
```

### 3.2 Features

A **Feature** is a measurable property of an entity used for ML.

```python
Feature(
    name="user_purchase_count_30d",
    entity="user",
    dtype="int64",
    description="Number of purchases in last 30 days",
    transformation="""
        SELECT 
            user_id,
            COUNT(*) as user_purchase_count_30d
        FROM purchases
        WHERE purchase_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY user_id
    """,
    owner="data-team",
    tags=["purchases", "engagement", "30d-window"],
)
```

### 3.3 Feature Sets (Feature Groups)

A **Feature Set** is a collection of related features, typically computed together.

```python
FeatureSet(
    name="user_engagement_features",
    entity="user",
    features=[
        "user_click_rate_7d",
        "user_session_duration_avg",
        "user_page_views_7d",
        "user_last_active_days",
    ],
    description="User engagement metrics for churn prediction",
)
```

### 3.4 Feature Versions

Features are **versioned** to track changes over time.

```
user_purchase_count_30d
├── v1 (2024-01-01) - Initial version
├── v2 (2024-03-15) - Fixed timezone bug
└── v3 (2024-06-01) - Excluded refunds
```

### 3.5 Offline vs Online Store

| Store | Purpose | Latency | Use Case |
|-------|---------|---------|----------|
| **Offline Store** | Training data | Seconds-minutes | Batch training |
| **Online Store** | Real-time serving | Milliseconds | Model inference |

```
┌─────────────────────────────────────────────────────────┐
│                    FEATURE STORE                         │
│                                                          │
│  ┌─────────────────┐       ┌─────────────────┐          │
│  │  Offline Store  │       │  Online Store   │          │
│  │  (PostgreSQL/   │       │  (Redis/        │          │
│  │   Parquet)      │       │   DynamoDB)     │          │
│  │                 │       │                 │          │
│  │  Historical     │  ───> │  Latest         │          │
│  │  feature values │ sync  │  feature values │          │
│  │  for training   │       │  for serving    │          │
│  └─────────────────┘       └─────────────────┘          │
│           │                         │                    │
│           ▼                         ▼                    │
│  ┌─────────────────┐       ┌─────────────────┐          │
│  │ Training        │       │ Real-time       │          │
│  │ Pipeline        │       │ Inference       │          │
│  └─────────────────┘       └─────────────────┘          │
└─────────────────────────────────────────────────────────┘
```

### 3.6 Point-in-Time Joins

Critical for preventing data leakage during training.

```sql
-- Point-in-Time Join
-- Get features as they existed at the time of each event

SELECT 
    e.user_id,
    e.event_timestamp,
    f.user_purchase_count_30d
FROM events e
LEFT JOIN LATERAL (
    SELECT user_purchase_count_30d
    FROM user_features f
    WHERE f.user_id = e.user_id
      AND f.feature_timestamp <= e.event_timestamp
    ORDER BY f.feature_timestamp DESC
    LIMIT 1
) f ON true;
```

---

## 4. Architecture Design

### 4.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ Feature Catalog │  │ Feature Builder │  │ Feature Sets    │         │
│  │ (search/browse) │  │ (SQL/Python)    │  │ (grouping)      │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
└───────────┼─────────────────────┼─────────────────────┼─────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    /api/v1/features/*                            │   │
│  │  GET /entities   POST /features   GET /feature-sets   GET /serve │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FEATURE STORE DOMAIN                             │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   Router     │  │   Service    │  │  Transformer │  │  Registry  │  │
│  │              │─▶│              │─▶│              │  │            │  │
│  │ - endpoints  │  │ - CRUD       │  │ - SQL exec   │  │ - versions │  │
│  │ - validation │  │ - compute    │  │ - Python     │  │ - metadata │  │
│  │              │  │ - serve      │  │   exec       │  │            │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └────────────┘  │
│                           │                                             │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐
│  OFFLINE STORE   │ │ ONLINE STORE │ │  COMPUTE ENGINE  │
│                  │ │              │ │                  │
│  PostgreSQL      │ │  Redis       │ │  Local / RunPod  │
│  + Parquet       │ │  (optional)  │ │  (feature comp)  │
│                  │ │              │ │                  │
└──────────────────┘ └──────────────┘ └──────────────────┘
```

### 4.2 Domain Structure

```
backend/domains/feature_store/
├── __init__.py
├── router.py              # API endpoints
├── service.py             # Core business logic
├── models.py              # Pydantic models (request/response)
├── db_models.py           # SQLAlchemy models
├── registry.py            # Feature versioning & metadata
├── transformers/
│   ├── __init__.py
│   ├── base.py            # Abstract transformer interface
│   ├── sql_transformer.py # SQL-based transformations
│   └── python_transformer.py  # Python-based transformations
├── stores/
│   ├── __init__.py
│   ├── offline_store.py   # PostgreSQL/Parquet storage
│   └── online_store.py    # Redis for real-time serving
├── serving/
│   ├── __init__.py
│   ├── batch_serving.py   # Batch feature retrieval
│   └── online_serving.py  # Low-latency serving
└── utils/
    ├── __init__.py
    ├── point_in_time.py   # PIT join logic
    └── validation.py      # Feature validation
```

### 4.3 Data Flow

```
1. FEATURE DEFINITION
   ┌─────────────────┐
   │ User defines    │
   │ feature via UI  │───────┐
   │ or API          │       │
   └─────────────────┘       │
                             ▼
2. FEATURE COMPUTATION       
   ┌─────────────────┐    ┌─────────────────┐
   │ SQL/Python      │───>│ Execute on      │
   │ transformation  │    │ data sources    │
   └─────────────────┘    └────────┬────────┘
                                   │
                                   ▼
3. STORAGE                   
   ┌─────────────────┐    ┌─────────────────┐
   │ Store in        │    │ (Optional)      │
   │ Offline Store   │───>│ Sync to Online  │
   │ (PostgreSQL)    │    │ Store (Redis)   │
   └─────────────────┘    └─────────────────┘
                                   │
                                   ▼
4. SERVING                   
   ┌─────────────────┐    ┌─────────────────┐
   │ Training:       │    │ Inference:      │
   │ Batch retrieval │    │ Real-time       │
   │ with PIT joins  │    │ lookup          │
   └─────────────────┘    └─────────────────┘
```

---

## 5. Database Schema

### 5.1 Core Tables

```sql
-- Entities (business objects that features describe)
CREATE TABLE feature_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    join_keys JSONB NOT NULL,  -- ["user_id"] or ["user_id", "product_id"]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Feature definitions
CREATE TABLE feature_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    entity_id UUID REFERENCES feature_entities(id),
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Data type
    dtype VARCHAR(50) NOT NULL,  -- int64, float64, string, bool, datetime
    
    -- Transformation
    transformation_type VARCHAR(20) NOT NULL,  -- sql, python
    transformation_code TEXT NOT NULL,
    
    -- Source
    source_connection_id UUID REFERENCES data_connections(id),
    source_table VARCHAR(255),
    
    -- Metadata
    description TEXT,
    owner VARCHAR(100),
    tags TEXT[],
    
    -- Computation settings
    computation_mode VARCHAR(20) DEFAULT 'on_demand',  -- on_demand, scheduled, streaming
    refresh_schedule VARCHAR(100),  -- cron expression
    ttl_seconds INTEGER,  -- time-to-live for cached values
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, deprecated
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(name, version)
);

-- Feature sets (groups of related features)
CREATE TABLE feature_sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    entity_id UUID REFERENCES feature_entities(id),
    description TEXT,
    owner VARCHAR(100),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Feature set membership
CREATE TABLE feature_set_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_set_id UUID REFERENCES feature_sets(id) ON DELETE CASCADE,
    feature_definition_id UUID REFERENCES feature_definitions(id),
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(feature_set_id, feature_definition_id)
);

-- Computed feature values (offline store)
CREATE TABLE feature_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_definition_id UUID REFERENCES feature_definitions(id),
    entity_key JSONB NOT NULL,  -- {"user_id": "123"} or {"user_id": "123", "product_id": "456"}
    value JSONB NOT NULL,
    feature_timestamp TIMESTAMP NOT NULL,  -- when the feature was valid
    computed_at TIMESTAMP DEFAULT NOW(),
    
    -- Index for efficient PIT lookups
    UNIQUE(feature_definition_id, entity_key, feature_timestamp)
);

-- Create index for point-in-time queries
CREATE INDEX idx_feature_values_pit 
ON feature_values (feature_definition_id, entity_key, feature_timestamp DESC);

-- Feature computation jobs
CREATE TABLE feature_computation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_definition_id UUID REFERENCES feature_definitions(id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    rows_computed INTEGER,
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feature usage tracking (which models use which features)
CREATE TABLE feature_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_definition_id UUID REFERENCES feature_definitions(id),
    recipe_id UUID,  -- ML recipe that uses this feature
    run_id UUID,     -- Specific run
    used_at TIMESTAMP DEFAULT NOW()
);

-- Feature statistics
CREATE TABLE feature_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_definition_id UUID REFERENCES feature_definitions(id),
    computed_at TIMESTAMP DEFAULT NOW(),
    
    -- Statistics
    row_count BIGINT,
    null_count BIGINT,
    distinct_count BIGINT,
    
    -- Numeric stats (if applicable)
    mean DOUBLE PRECISION,
    std DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    percentiles JSONB,  -- {p25: x, p50: x, p75: x, p99: x}
    
    -- Categorical stats (if applicable)
    top_values JSONB,  -- [{value: x, count: n}, ...]
    
    -- Distribution
    histogram JSONB
);
```

### 5.2 Migration File

```python
# backend/migrations/versions/028_add_feature_store.py

"""Add feature store tables

Revision ID: 028
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Feature entities
    op.create_table(
        'feature_entities',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('join_keys', JSONB, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100)),
    )
    
    # Feature definitions
    op.create_table(
        'feature_definitions',
        sa.Column('id', UUID, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('entity_id', UUID, sa.ForeignKey('feature_entities.id')),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('dtype', sa.String(50), nullable=False),
        sa.Column('transformation_type', sa.String(20), nullable=False),
        sa.Column('transformation_code', sa.Text, nullable=False),
        sa.Column('source_connection_id', UUID),
        sa.Column('source_table', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('owner', sa.String(100)),
        sa.Column('tags', sa.ARRAY(sa.Text)),
        sa.Column('computation_mode', sa.String(20), default='on_demand'),
        sa.Column('refresh_schedule', sa.String(100)),
        sa.Column('ttl_seconds', sa.Integer),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.UniqueConstraint('name', 'version'),
    )
    
    # ... (other tables)

def downgrade():
    op.drop_table('feature_statistics')
    op.drop_table('feature_usage')
    op.drop_table('feature_computation_jobs')
    op.drop_table('feature_values')
    op.drop_table('feature_set_features')
    op.drop_table('feature_sets')
    op.drop_table('feature_definitions')
    op.drop_table('feature_entities')
```

---

## 6. API Design

### 6.1 Entities API

```
# List entities
GET /api/v1/features/entities
Response: { entities: [{ id, name, description, join_keys }] }

# Create entity
POST /api/v1/features/entities
Body: { name: "user", description: "...", join_keys: ["user_id"] }

# Get entity
GET /api/v1/features/entities/{entity_id}
```

### 6.2 Feature Definitions API

```
# List features
GET /api/v1/features/definitions
Query: ?entity=user&tags=engagement&search=purchase
Response: { features: [...], total: 42 }

# Create feature
POST /api/v1/features/definitions
Body: {
  name: "user_purchase_count_30d",
  entity_id: "uuid",
  dtype: "int64",
  transformation_type: "sql",
  transformation_code: "SELECT user_id, COUNT(*) ...",
  source_connection_id: "uuid",
  description: "Number of purchases in last 30 days",
  tags: ["purchases", "30d-window"]
}
Response: { id, name, version: 1, status: "draft" }

# Get feature
GET /api/v1/features/definitions/{feature_id}
Response: { id, name, entity, versions: [...], statistics: {...} }

# Update feature (creates new version)
PUT /api/v1/features/definitions/{feature_id}
Body: { transformation_code: "...", description: "Fixed bug" }
Response: { id, name, version: 2 }

# Activate feature
POST /api/v1/features/definitions/{feature_id}/activate
Response: { status: "active" }

# Deprecate feature
POST /api/v1/features/definitions/{feature_id}/deprecate
Response: { status: "deprecated" }
```

### 6.3 Feature Sets API

```
# List feature sets
GET /api/v1/features/sets
Response: { feature_sets: [...] }

# Create feature set
POST /api/v1/features/sets
Body: {
  name: "user_engagement_features",
  entity_id: "uuid",
  feature_ids: ["uuid1", "uuid2", "uuid3"],
  description: "Features for churn prediction"
}

# Get feature set
GET /api/v1/features/sets/{set_id}
Response: { id, name, features: [...] }

# Add feature to set
POST /api/v1/features/sets/{set_id}/features
Body: { feature_id: "uuid" }

# Remove feature from set
DELETE /api/v1/features/sets/{set_id}/features/{feature_id}
```

### 6.4 Computation API

```
# Compute feature values
POST /api/v1/features/definitions/{feature_id}/compute
Body: {
  start_date: "2024-01-01",
  end_date: "2024-12-31",
  entity_keys: ["user_123", "user_456"]  # optional, null = all
}
Response: { job_id, status: "running" }

# Get computation job status
GET /api/v1/features/jobs/{job_id}
Response: { job_id, status, progress, rows_computed }

# Compute feature set
POST /api/v1/features/sets/{set_id}/compute
Body: { start_date, end_date }
```

### 6.5 Serving API

```
# Get feature values (batch)
POST /api/v1/features/serve/batch
Body: {
  feature_ids: ["uuid1", "uuid2"],
  entity_keys: [
    { user_id: "123" },
    { user_id: "456" }
  ],
  timestamp: "2024-06-15T10:00:00Z"  # point-in-time (optional)
}
Response: {
  results: [
    { entity_key: { user_id: "123" }, features: { feature1: 10, feature2: 0.5 } },
    { entity_key: { user_id: "456" }, features: { feature1: 25, feature2: 0.8 } }
  ]
}

# Get feature values (online - single entity)
GET /api/v1/features/serve/online
Query: ?features=uuid1,uuid2&user_id=123
Response: { user_id: "123", feature1: 10, feature2: 0.5, timestamp: "..." }

# Get training dataset
POST /api/v1/features/serve/training-data
Body: {
  feature_set_id: "uuid",
  events: [
    { entity_key: { user_id: "123" }, event_timestamp: "2024-01-15" },
    { entity_key: { user_id: "456" }, event_timestamp: "2024-01-20" }
  ]
}
Response: {
  columns: ["user_id", "event_timestamp", "feature1", "feature2"],
  data: [...],
  download_url: "/api/v1/features/serve/download/uuid"
}
```

### 6.6 Statistics API

```
# Get feature statistics
GET /api/v1/features/definitions/{feature_id}/statistics
Response: {
  row_count: 1000000,
  null_rate: 0.02,
  distinct_count: 500,
  mean: 42.5,
  std: 15.2,
  percentiles: { p25: 30, p50: 40, p75: 55, p99: 95 },
  histogram: { bins: [...], counts: [...] }
}

# Compute statistics
POST /api/v1/features/definitions/{feature_id}/statistics/compute
Response: { job_id }
```

---

## 7. Implementation Roadmap

### 7.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION TIMELINE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1        Phase 2         Phase 3         Phase 4        Phase 5  │
│  Foundation     Transforms      Serving         UI             Advanced │
│  ─────────     ──────────      ───────         ──             ──────── │
│  ████████      ██████          ██████          ████           ████      │
│                                                                          │
│  2 days        1-2 days        1-2 days        1-2 days       1-2 days  │
│                                                                          │
│  Schema        SQL exec        Batch serve     Catalog UI     Online    │
│  API CRUD      Python exec     PIT joins       Feature        Scheduling│
│  Entities      Validation      Stats           Builder        Lineage   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Phase 1: Foundation (Days 1-2)

**Goal:** Core data model and CRUD operations

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 1.1 | Create domain structure | 1h |
| 1.2 | Database migration (028_add_feature_store.py) | 2h |
| 1.3 | Pydantic models (models.py) | 2h |
| 1.4 | DB models (db_models.py) | 1h |
| 1.5 | Entity CRUD service | 2h |
| 1.6 | Feature definition CRUD | 3h |
| 1.7 | Feature set CRUD | 2h |
| 1.8 | Router endpoints | 3h |
| 1.9 | Basic tests | 2h |

**Deliverables:**
- `/api/v1/features/entities` - CRUD
- `/api/v1/features/definitions` - CRUD
- `/api/v1/features/sets` - CRUD
- Feature versioning working

**Success Criteria:**
- Can create entities, features, feature sets via API
- Feature versions increment correctly

### 7.3 Phase 2: Transformations (Days 3-4)

**Goal:** Execute SQL and Python feature transformations

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 2.1 | SQL transformer implementation | 3h |
| 2.2 | Python transformer (sandboxed) | 4h |
| 2.3 | Feature computation job service | 3h |
| 2.4 | Store computed values | 2h |
| 2.5 | Computation API endpoints | 2h |
| 2.6 | Feature validation (data types, nulls) | 2h |
| 2.7 | Tests | 2h |

**Deliverables:**
- SQL features computed from connected databases
- Python features with pandas/numpy
- Computed values stored in `feature_values` table
- Validation ensures correct data types

**Success Criteria:**
- SQL feature computes successfully
- Python feature with pandas works
- Values stored with timestamps

### 7.4 Phase 3: Serving (Days 5-6)

**Goal:** Retrieve features for training and inference

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 3.1 | Batch serving implementation | 3h |
| 3.2 | Point-in-time join logic | 4h |
| 3.3 | Training data generation | 3h |
| 3.4 | Feature statistics computation | 2h |
| 3.5 | Serving API endpoints | 2h |
| 3.6 | Export to Parquet/CSV | 2h |
| 3.7 | Tests | 2h |

**Deliverables:**
- `/api/v1/features/serve/batch` - working
- Point-in-time joins prevent data leakage
- Training dataset export
- Feature statistics (mean, std, histogram)

**Success Criteria:**
- PIT join returns correct historical values
- Training dataset generated correctly
- Statistics match expected values

### 7.5 Phase 4: UI (Days 7-8)

**Goal:** Feature catalog and builder UI

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 4.1 | Feature catalog page | 4h |
| 4.2 | Feature detail page | 3h |
| 4.3 | Feature builder (SQL/Python editor) | 4h |
| 4.4 | Feature set management | 2h |
| 4.5 | Statistics visualization | 3h |
| 4.6 | Search and filtering | 2h |

**Deliverables:**
- Feature catalog with search
- Feature detail with stats, versions, usage
- SQL/Python editor for transformations
- Feature set grouping UI

**Success Criteria:**
- User can browse and search features
- User can create feature via UI
- Statistics displayed correctly

### 7.6 Phase 5: Advanced Features (Days 9-10)

**Goal:** Online store, scheduling, lineage

**Tasks:**

| Task | Description | Effort |
|------|-------------|--------|
| 5.1 | Online store (Redis) integration | 4h |
| 5.2 | Scheduled feature computation | 3h |
| 5.3 | Lineage integration | 3h |
| 5.4 | Feature usage tracking | 2h |
| 5.5 | Notebook integration | 2h |
| 5.6 | Documentation | 2h |
| 5.7 | End-to-end tests | 2h |

**Deliverables:**
- Low-latency online serving (if Redis available)
- Cron-based feature refresh
- Feature lineage in lineage graph
- Feature usage from ML runs

**Success Criteria:**
- Online serving < 10ms latency
- Scheduled computation runs on cron
- Lineage visible in UI

### 7.7 Milestone Summary

| Milestone | Target | Key Deliverables |
|-----------|--------|------------------|
| M1: Foundation | Day 2 | CRUD APIs working |
| M2: Transforms | Day 4 | SQL/Python execution |
| M3: Serving | Day 6 | Batch serving + PIT |
| M4: UI | Day 8 | Feature catalog |
| M5: Advanced | Day 10 | Online + scheduling |

---

## 8. Integration Points

### 8.1 Data Connections

```python
# Features can use existing data connections
Feature(
    name="user_total_orders",
    source_connection_id="postgres-prod",  # Existing connection
    transformation_code="""
        SELECT user_id, COUNT(*) as total_orders
        FROM orders
        GROUP BY user_id
    """
)
```

### 8.2 Notebooks

```python
# In Python notebook cell
from nex.features import get_features

# Get features for training
training_df = get_features(
    feature_set="user_engagement",
    entity_keys=df['user_id'].tolist(),
    timestamp_col='event_time'
)

# Use in model training
X = training_df[feature_columns]
y = training_df['target']
model.fit(X, y)
```

### 8.3 ML Recipes

```python
# Recipe can declare feature dependencies
recipe = MLRecipe(
    name="churn_prediction",
    feature_sets=["user_engagement", "user_transactions"],
    # Features auto-fetched during training
)
```

### 8.4 Data Lineage

```
Feature Store integrates with existing lineage:

┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Data        │───>│ Feature     │───>│ ML Model    │
│ Connection  │    │ Definition  │    │ (Recipe)    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │
       └──────────────────┴──────────────────┘
                    Lineage Graph
```

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PIT join performance | Medium | High | Proper indexing, materialized views |
| Python execution security | Medium | High | Sandboxed executor (existing) |
| Large feature values | Low | Medium | Pagination, streaming |
| Schema changes | Low | Medium | Migration strategy |

### 9.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Feature compute failures | Medium | Medium | Retry logic, alerts |
| Stale features | Medium | Medium | TTL, freshness monitoring |
| Version conflicts | Low | Low | Clear versioning policy |

### 9.3 Adoption Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Complexity for users | Medium | Medium | Good UI, documentation |
| Migration from notebooks | Medium | Low | Import tools, gradual adoption |

---

## Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Entity** | Business object that features describe (user, product) |
| **Feature** | Measurable property used for ML |
| **Feature Set** | Collection of related features |
| **Point-in-Time (PIT)** | Historical feature value at specific timestamp |
| **Offline Store** | Storage for batch training data |
| **Online Store** | Low-latency storage for inference |
| **Feature Drift** | Change in feature distribution over time |

### B. Example Features

```sql
-- User engagement features
user_login_count_7d:
  SELECT user_id, COUNT(*) 
  FROM logins 
  WHERE login_time >= NOW() - INTERVAL '7 days'
  GROUP BY user_id

user_avg_session_duration:
  SELECT user_id, AVG(duration_seconds)
  FROM sessions
  GROUP BY user_id

-- Transaction features  
user_total_spend_30d:
  SELECT user_id, SUM(amount)
  FROM transactions
  WHERE txn_date >= CURRENT_DATE - 30
  GROUP BY user_id

user_avg_order_value:
  SELECT user_id, AVG(order_total)
  FROM orders
  GROUP BY user_id
```

### C. References

**Industry Feature Stores:**
- Feast (open source): https://feast.dev/
- Tecton: https://www.tecton.ai/
- Databricks Feature Store
- AWS SageMaker Feature Store
- Vertex AI Feature Store

**Papers:**
- "Feature Stores for ML" - Tecton whitepaper
- "Feast: Feature Store for Machine Learning" - Google

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: NEX Platform Team*
