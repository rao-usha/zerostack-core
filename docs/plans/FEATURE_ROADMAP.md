# NEX Platform - Feature Roadmap

## Current State Summary

### ✅ Built & Working

| Category | Feature | Status |
|----------|---------|--------|
| **Data Connections** | PostgreSQL/MySQL/Snowflake connections | ✅ Complete |
| **Data Connections** | Table scanning & quality analysis | ✅ Complete |
| **Data Connections** | Recipe compatibility detection | ✅ Complete |
| **SQL Notebooks** | Create/edit notebooks with cells | ✅ Complete |
| **SQL Notebooks** | Execute SQL queries | ✅ Complete |
| **SQL Notebooks** | Save results as datasets | ✅ Complete |
| **Datasets** | Export to Parquet/CSV in MinIO | ✅ Complete |
| **Datasets** | Preview, download, delete | ✅ Complete |
| **ML Recipes** | Recipe definitions & versions | ✅ Complete |
| **ML Execution** | Local execution | ✅ Complete |
| **ML Execution** | RunPod GPU execution | ✅ Complete |
| **ML Execution** | SSH-based execution on pods | ✅ Complete |
| **Run Tracking** | Status, metrics, logs, artifacts | ✅ Complete |
| **Run Tracking** | Run comparison | ✅ Complete |
| **Cost Tracking** | GPU pricing & cost estimation | ✅ Complete |
| **Drift Detection** | Basic drift checks | ✅ Complete |
| **Schedules** | APScheduler integration | ✅ Complete |

---

## Phase 1: Data Engineering Foundation (Next)

### 1.1 Python Notebooks
**Priority: HIGH** | **Effort: 3-4 days**

Extend SQL notebooks to support Python cells.

- [ ] Python cell type in notebook
- [ ] Execute Python on connected compute (local/RunPod)
- [ ] Access datasets from Python cells
- [ ] Save DataFrames as datasets
- [ ] Install custom pip packages per notebook

**Why:** Users need to do feature engineering, data transformation, and EDA beyond SQL.

---

### 1.2 Feature Store
**Priority: HIGH** | **Effort: 5-6 days**

Reusable feature definitions that can be versioned and shared.

- [ ] Feature definitions (SQL/Python)
- [ ] Feature versioning
- [ ] Point-in-time feature lookups
- [ ] Feature sets (groups of features)
- [ ] Auto-compute features for new data
- [ ] Feature statistics & profiling

**Why:** Prevents duplicate feature engineering work, ensures consistency.

---

### 1.3 Data Lineage
**Priority: MEDIUM** | **Effort: 3-4 days**

Track where data comes from and where it goes.

- [ ] Connection → Table → Dataset → Model lineage
- [ ] Visual lineage graph
- [ ] Impact analysis (what breaks if X changes)
- [ ] Lineage in run details

**Why:** Critical for debugging, compliance, and understanding data flow.

---

## Phase 2: Model Operations

### 2.1 Model Registry
**Priority: HIGH** | **Effort: 4-5 days**

Centralized model versioning and lifecycle management.

- [ ] Model versions (auto from runs)
- [ ] Model stages (dev → staging → production)
- [ ] Model metadata (metrics, parameters, lineage)
- [ ] Model comparison UI
- [ ] Promotion workflow with approval
- [ ] Model rollback

**Why:** Production ML needs versioned, governed model management.

---

### 2.2 Model Deployment
**Priority: HIGH** | **Effort: 5-6 days**

Deploy models as REST API endpoints.

- [ ] One-click deploy from model registry
- [ ] Auto-generated REST API
- [ ] Batch prediction endpoint
- [ ] Real-time prediction endpoint
- [ ] A/B deployment (traffic splitting)
- [ ] Endpoint monitoring & scaling

**Why:** Models are useless if they can't serve predictions.

---

### 2.3 Custom Model Upload
**Priority: MEDIUM** | **Effort: 2-3 days**

Upload pre-trained models (not just train from scratch).

- [ ] Upload model files (pickle, ONNX, PyTorch, etc.)
- [ ] Define input/output schema
- [ ] Register as model version
- [ ] Deploy uploaded models

**Why:** Many users have existing models they want to operationalize.

---

## Phase 3: Monitoring & Observability

### 3.1 Model Monitoring Dashboard
**Priority: HIGH** | **Effort: 4-5 days**

Real-time monitoring of deployed models.

- [ ] Prediction volume metrics
- [ ] Latency percentiles (p50, p95, p99)
- [ ] Error rates
- [ ] Input drift detection
- [ ] Output drift detection
- [ ] Custom metric alerts

**Why:** Production models need continuous monitoring.

---

### 3.2 Enhanced Drift Detection
**Priority: MEDIUM** | **Effort: 3-4 days**

More sophisticated drift analysis.

- [ ] Statistical tests (KS, Chi-squared, PSI)
- [ ] Feature importance drift
- [ ] Concept drift detection
- [ ] Automated retraining triggers
- [ ] Drift visualization over time

**Why:** Models degrade over time; need to detect and respond.

---

### 3.3 Cost Analytics
**Priority: MEDIUM** | **Effort: 2-3 days**

Detailed cost breakdown and optimization suggestions.

- [ ] Cost by user/team
- [ ] Cost by recipe/model
- [ ] Cost trends over time
- [ ] Idle resource detection
- [ ] Cost optimization recommendations
- [ ] Budget alerts

**Why:** GPU compute is expensive; need visibility and control.

---

## Phase 4: Collaboration & Governance

### 4.1 Teams & Access Control
**Priority: MEDIUM** | **Effort: 4-5 days**

Multi-user support with permissions.

- [ ] User authentication (OAuth/SAML)
- [ ] Teams/workspaces
- [ ] Role-based access (viewer, editor, admin)
- [ ] Resource ownership
- [ ] Sharing controls

**Why:** Enterprise adoption requires proper access control.

---

### 4.2 Audit Logging
**Priority: MEDIUM** | **Effort: 2-3 days**

Track all user actions for compliance.

- [ ] Action logging (create, update, delete, execute)
- [ ] User attribution
- [ ] Searchable audit log
- [ ] Export for compliance
- [ ] Retention policies

**Why:** Required for SOC2, GDPR, and general security.

---

### 4.3 Comments & Annotations
**Priority: LOW** | **Effort: 2-3 days**

Collaboration features on artifacts.

- [ ] Comments on notebooks
- [ ] Comments on runs
- [ ] Comments on models
- [ ] @mentions and notifications
- [ ] Comment threads

**Why:** Team collaboration on ML work.

---

## Phase 5: Advanced ML Features

### 5.1 Experiment Tracking
**Priority: MEDIUM** | **Effort: 3-4 days**

Structured experiment management.

- [ ] Experiment groups
- [ ] Hyperparameter tracking
- [ ] Metric comparison charts
- [ ] Best run selection
- [ ] Experiment templates

**Why:** Systematic experimentation improves model quality.

---

### 5.2 AutoML
**Priority: LOW** | **Effort: 5-6 days**

Automated model selection and tuning.

- [ ] Auto feature selection
- [ ] Algorithm selection
- [ ] Hyperparameter optimization
- [ ] Ensemble generation
- [ ] AutoML job tracking

**Why:** Democratizes ML for non-experts.

---

### 5.3 Spark Integration
**Priority: MEDIUM** | **Effort: 4-5 days**

Execute on Spark clusters for big data.

- [ ] Spark cluster connection
- [ ] PySpark cells in notebooks
- [ ] Distributed feature engineering
- [ ] Spark-based training
- [ ] Cluster management UI

**Why:** Some datasets are too large for single-machine processing.

---

## Suggested Implementation Order

### Immediate (Next 2 weeks)
1. **Python Notebooks** - Extends existing notebook infra
2. **Model Registry** - Foundation for model ops

### Short-term (2-4 weeks)
3. **Model Deployment** - Makes models useful
4. **Feature Store** - Improves data quality

### Medium-term (1-2 months)
5. **Model Monitoring Dashboard**
6. **Data Lineage**
7. **Enhanced Drift Detection**

### Long-term (2-3 months)
8. **Teams & Access Control**
9. **Audit Logging**
10. **Spark Integration**
11. **AutoML**

---

## Quick Wins (< 1 day each)

These can be done anytime for incremental improvement:

- [ ] Keyboard shortcuts in notebooks (Ctrl+S to save, Ctrl+Enter to run)
- [ ] Notebook autosave
- [ ] Duplicate notebook/cell
- [ ] Export notebook as .py or .sql
- [ ] Run history search/filter
- [ ] Favorite/star datasets
- [ ] Dataset tags
- [ ] Dark/light mode toggle
- [ ] Mobile-responsive improvements
- [ ] Loading skeletons instead of spinners

---

## Technical Debt to Address

- [ ] Consolidate duplicate API patterns
- [ ] Add comprehensive error handling
- [ ] Improve test coverage (currently minimal)
- [ ] Add request rate limiting
- [ ] Implement proper caching
- [ ] Database query optimization
- [ ] Frontend state management (consider Zustand/Redux)
- [ ] API documentation (OpenAPI/Swagger)

---

## Architecture Considerations

For Phase 2+, consider:

1. **Kubernetes** - For model serving at scale
2. **Redis** - For caching and real-time features
3. **Kafka/Pulsar** - For event streaming (predictions, alerts)
4. **Vector DB** - If adding embedding/similarity features
5. **MLflow** - Potential integration for experiment tracking

---

*Last updated: January 2026*
