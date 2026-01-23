# Partial Features Completion Plan

**Created:** 2026-01-23
**Status:** In Progress
**Goal:** Complete 4 partially-built features to make them production-ready

---

## Overview

| Feature | Current | Target | Effort |
|---------|---------|--------|--------|
| Drift Detection | 100% | 100% | COMPLETE |
| Cost Analytics | 100% | 100% | COMPLETE |
| Model Registry | 100% | 100% | COMPLETE |
| Model Monitoring | 100% | 100% | COMPLETE |

---

## Development Process

For each task:
1. **Understand** - Read existing code, identify patterns
2. **Plan** - Define deliverables and interfaces
3. **Implement** - Migrations → Backend → Frontend
4. **Verify** - Test endpoints, UI, integration
5. **Complete** - Mark done, commit

---

## Feature 1: Drift Detection

### What Exists
- `backend/domains/drift/router.py` - 11 API endpoints defined
- `backend/services/drift_detector.py` - Basic comparison logic

### What's Missing
- Database tables (drift_checks, drift_alerts)
- Statistical tests (KS, chi-squared, PSI)
- Frontend dashboard

### Tasks

| ID | Task | Status | Blocked By |
|----|------|--------|------------|
| 1.1 | Create drift detection database migration | [x] Done | - |
| 1.2 | Implement statistical tests service | [x] Done | - |
| 1.3 | Build drift dashboard frontend page | [x] Done | - |
| 1.4 | Build drift visualization components | [x] Done | - |

### Task Details

#### 1.1 Create drift detection database migration
**File:** `backend/migrations/versions/XXX_add_drift_tables.py`

Tables to create:
```sql
drift_checks:
  - id (pk)
  - recipe_id (fk -> ml_recipes)
  - metric_name (string)
  - comparison_type (enum: greater_than, less_than, equals, range)
  - threshold_value (numeric)
  - threshold_upper (numeric, nullable)
  - severity (enum: low, medium, high, critical)
  - is_active (boolean)
  - check_frequency_minutes (int)
  - created_at, updated_at

drift_alerts:
  - id (pk)
  - check_id (fk -> drift_checks)
  - triggered_at (timestamp)
  - metric_value (numeric)
  - threshold_value (numeric)
  - severity (enum)
  - acknowledged (boolean)
  - acknowledged_by (string, nullable)
  - acknowledged_at (timestamp, nullable)
  - notes (text, nullable)
```

#### 1.2 Implement statistical tests service
**File:** `backend/services/statistical_tests.py`

Functions to implement:
```python
def kolmogorov_smirnov_test(baseline: List[float], current: List[float]) -> TestResult
def chi_squared_test(baseline: Dict[str, int], current: Dict[str, int]) -> TestResult
def population_stability_index(baseline: List[float], current: List[float]) -> float
def detect_drift(baseline_data, current_data, data_type: str) -> DriftResult
```

#### 1.3 Build drift dashboard frontend page
**File:** `frontend/src/pages/DriftDashboard.tsx`

Components:
- Summary cards (total checks, breached, unacknowledged)
- Drift checks table with filters
- Alert list with acknowledge buttons
- Add to sidebar in Layout.tsx

#### 1.4 Build drift visualization components
**Files:**
- `frontend/src/components/DriftTimeSeries.tsx`
- `frontend/src/components/DriftHistogram.tsx`
- `frontend/src/components/DriftAlertList.tsx`

---

## Feature 2: Cost Analytics

### What Exists
- `backend/services/cost_tracker.py` - CostTracker service with pricing lookup
- `backend/db/models.py` - gpu_pricing table, cost fields on ml_run

### What's Missing
- API router to expose cost data
- Cost aggregation service
- Budget tracking
- Frontend dashboard

### Tasks

| ID | Task | Status | Blocked By |
|----|------|--------|------------|
| 2.1 | Create cost analytics API router | [x] Done | - |
| 2.2 | Create cost aggregation service | [x] Done | - |
| 2.3 | Create budget tracking migration | [x] Done | - |
| 2.4 | Build cost analytics dashboard | [x] Done | - |

### Task Details

#### 2.1 Create cost analytics API router
**File:** `backend/domains/cost_analytics/router.py`

Endpoints:
```
GET  /api/v1/cost-analytics/summary?start=&end=
GET  /api/v1/cost-analytics/by-provider?start=&end=
GET  /api/v1/cost-analytics/by-model?start=&end=
GET  /api/v1/cost-analytics/trends?periods=7
GET  /api/v1/cost-analytics/runs?limit=50
POST /api/v1/cost-analytics/budgets
GET  /api/v1/cost-analytics/budgets
GET  /api/v1/cost-analytics/budgets/{id}/status
```

#### 2.2 Create cost aggregation service
**File:** `backend/domains/cost_analytics/service.py`

Functions:
```python
def get_cost_summary(start: datetime, end: datetime) -> CostSummary
def get_costs_by_provider(start: datetime, end: datetime) -> List[ProviderCost]
def get_costs_by_model(start: datetime, end: datetime) -> List[ModelCost]
def get_cost_trends(periods: int, granularity: str) -> List[CostTrend]
def check_budget_status(budget_id: int) -> BudgetStatus
```

#### 2.3 Create budget tracking migration
**File:** `backend/migrations/versions/XXX_add_cost_budgets.py`

Tables:
```sql
cost_budgets:
  - id (pk)
  - name (string)
  - budget_amount_usd (numeric)
  - period (enum: daily, weekly, monthly)
  - alert_threshold_percent (int, default 80)
  - scope_type (enum: global, provider, model)
  - scope_id (string, nullable)
  - is_active (boolean)
  - created_at, updated_at

cost_budget_alerts:
  - id (pk)
  - budget_id (fk)
  - triggered_at (timestamp)
  - current_spend_usd (numeric)
  - budget_amount_usd (numeric)
  - percent_used (int)
```

#### 2.4 Build cost analytics dashboard
**File:** `frontend/src/pages/CostAnalytics.tsx`

Components:
- Summary cards (total spend, this month, projected)
- Cost over time line chart
- Cost by provider pie chart
- Cost by model bar chart
- Budget status cards
- Recent runs table

---

## Feature 3: Model Registry

### What Exists
- `backend/domains/ml_development/router.py` - Basic model CRUD
- `backend/db/models.py` - ml_model table with status field
- Status values: draft, staging, production, retired

### What's Missing
- Promotion/demotion API
- Promotion history tracking
- Validation rules
- Frontend registry UI

### Tasks

| ID | Task | Status | Blocked By |
|----|------|--------|------------|
| 3.1 | Create model promotion API endpoints | [x] Done | - |
| 3.2 | Create promotion history migration | [x] Done | - |
| 3.3 | Add promotion validation service | [x] Done | - |
| 3.4 | Build Model Registry frontend page | [x] Done | 3.1, 3.2, 3.3 |
| 3.5 | Build promotion dialog component | [x] Done | 3.3 |

### Task Details

#### 3.1 Create model promotion API endpoints
**File:** `backend/domains/ml_development/router.py` (add to existing)

New endpoints:
```
POST /api/v1/ml-development/models/{id}/promote
  Body: { target_status: "staging"|"production", notes: string }

POST /api/v1/ml-development/models/{id}/demote
  Body: { target_status: "draft"|"staging", notes: string }

POST /api/v1/ml-development/models/{id}/rollback
  Body: { to_promotion_id: int }

GET  /api/v1/ml-development/models/{id}/promotion-history
```

#### 3.2 Create promotion history migration
**File:** `backend/migrations/versions/XXX_add_model_promotions.py`

Table:
```sql
ml_model_promotions:
  - id (pk)
  - model_id (fk -> ml_models)
  - from_status (string)
  - to_status (string)
  - promoted_by (string)
  - promotion_notes (text)
  - validation_results (jsonb)
  - promoted_at (timestamp)
```

#### 3.3 Add promotion validation service
**File:** `backend/domains/ml_development/promotion_service.py`

Functions:
```python
def validate_promotion(model_id: int, target_status: str) -> ValidationResult
def get_promotion_requirements(target_status: str) -> List[Requirement]
def execute_promotion(model_id: int, target_status: str, notes: str, user: str) -> Promotion
def rollback_promotion(model_id: int, to_promotion_id: int, user: str) -> Promotion
```

Validation rules:
- draft → staging: Must have at least one completed run with metrics
- staging → production: Must have run in last 7 days, no critical drift alerts
- Any demotion: Allowed with notes

#### 3.4 Build Model Registry frontend page
**File:** `frontend/src/pages/ModelRegistry.tsx`

Layout:
- Kanban board with 4 columns (Draft, Staging, Production, Retired)
- Model cards with: name, recipe, key metrics, last updated
- Click card to expand details
- Promote/demote buttons on cards
- Filter by recipe, search

#### 3.5 Build promotion dialog component
**File:** `frontend/src/components/ModelPromotionDialog.tsx`

Features:
- Shows current → target status
- Lists validation requirements with pass/fail
- Notes textarea (required)
- Confirm/Cancel buttons
- Disabled if validation fails

---

## Feature 4: Model Monitoring

### What Exists
- `backend/domains/ml_development/router.py` - 2 monitoring endpoints
- `backend/db/models.py` - ml_monitor_snapshot table (generic JSON storage)

### What's Missing
- Structured latency/error tracking tables
- Health score calculation
- SLA configuration
- Frontend monitoring dashboard

### Tasks

| ID | Task | Status | Blocked By |
|----|------|--------|------------|
| 4.1 | Create monitoring metrics migration | [x] Done | - |
| 4.2 | Create monitoring analytics service | [x] Done | - |
| 4.3 | Create monitoring API router | [x] Done | - |
| 4.4 | Build model monitoring dashboard | [x] Done | 4.1, 4.2, 4.3 |
| 4.5 | Build monitoring visualization components | [x] Done | 4.2 |

### Task Details

#### 4.1 Create monitoring metrics migration
**File:** `backend/migrations/versions/XXX_add_monitoring_metrics.py`

Tables:
```sql
model_latency_metrics:
  - id (pk)
  - model_id (fk -> ml_models)
  - recorded_at (timestamp)
  - p50_ms (numeric)
  - p95_ms (numeric)
  - p99_ms (numeric)
  - request_count (int)
  - window_minutes (int)

model_error_rates:
  - id (pk)
  - model_id (fk -> ml_models)
  - recorded_at (timestamp)
  - total_requests (int)
  - error_count (int)
  - error_types (jsonb)  -- {"timeout": 5, "validation": 2}
  - window_minutes (int)

model_sla_config:
  - id (pk)
  - model_id (fk -> ml_models, unique)
  - max_latency_p95_ms (int)
  - max_error_rate_percent (numeric)
  - alerting_enabled (boolean)
  - created_at, updated_at
```

#### 4.2 Create monitoring analytics service
**File:** `backend/domains/model_monitoring/service.py`

Functions:
```python
def record_latency_metrics(model_id: int, latencies: List[float]) -> None
def record_error(model_id: int, error_type: str) -> None
def get_latency_history(model_id: int, hours: int) -> List[LatencyMetrics]
def get_error_history(model_id: int, hours: int) -> List[ErrorMetrics]
def calculate_health_score(model_id: int) -> HealthScore  # 0-100
def check_sla_compliance(model_id: int) -> SLAStatus
def get_monitoring_summary(model_id: int) -> MonitoringSummary
```

Health score formula:
- Latency score: 100 if p95 < SLA, decreases linearly
- Error score: 100 - (error_rate * 10), min 0
- Health = (latency_score + error_score) / 2

#### 4.3 Create monitoring API router
**File:** `backend/domains/model_monitoring/router.py`

Endpoints:
```
GET  /api/v1/model-monitoring/{model_id}/summary
GET  /api/v1/model-monitoring/{model_id}/latency?hours=24
GET  /api/v1/model-monitoring/{model_id}/errors?hours=24
GET  /api/v1/model-monitoring/{model_id}/health-score
POST /api/v1/model-monitoring/{model_id}/sla
GET  /api/v1/model-monitoring/{model_id}/sla/status
POST /api/v1/model-monitoring/{model_id}/record  # For recording metrics
```

#### 4.4 Build model monitoring dashboard
**File:** `frontend/src/pages/ModelMonitoring.tsx`

Layout:
- Model selector dropdown (production models)
- Health score gauge (large, center)
- Latency chart (p50, p95, p99 lines)
- Error rate chart (area chart)
- SLA status card (compliant/breached)
- Recent issues table

#### 4.5 Build monitoring visualization components
**Files:**
- `frontend/src/components/HealthScoreGauge.tsx` - Circular 0-100 gauge
- `frontend/src/components/LatencyChart.tsx` - Multi-line chart with SLA threshold
- `frontend/src/components/ErrorRateChart.tsx` - Area chart
- `frontend/src/components/SLAStatusCard.tsx` - Compliance indicator

---

## Progress Tracking

### Completion Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-01-23 | Plan created | Done | 22 tasks defined |
| 2026-01-23 | 1.1 Create drift tables migration | Done | 032_add_drift_tables.py created |
| 2026-01-23 | 1.2 Implement statistical tests | Done | statistical_tests.py with KS, chi-sq, PSI |
| 2026-01-23 | 1.3 Build drift dashboard | Done | DriftDashboard.tsx with summary, checks, alerts |
| 2026-01-23 | 1.4 Build drift visualizations | Done | DriftTimeSeries, DriftHistogram, DriftAlertList |
| 2026-01-23 | 2.1-2.4 Cost Analytics Feature | Done | Full domain with router, service, migration, UI |
| 2026-01-23 | 3.1-3.5 Model Registry Feature | Done | Promotion API, history, validation, Kanban UI |
| 2026-01-23 | 4.1-4.5 Model Monitoring Feature | Done | Migration, service, API, dashboard, charts |
| | | | |

### Commits

| Commit | Feature | Date |
|--------|---------|------|
| | | |

---

## Recovery Guide

If session fails, resume by:
1. Check this file for last completed task
2. Run `alembic upgrade head` to ensure migrations are applied
3. Run `docker compose -p zerostack ps` to check services
4. Continue from next uncompleted task

### Common Issues

| Issue | Solution |
|-------|----------|
| Migration fails | `alembic downgrade -1` then fix |
| Import error | Check __init__.py exports |
| API 404 | Check router registered in main.py |
| Frontend blank | Check console, verify API proxy |
