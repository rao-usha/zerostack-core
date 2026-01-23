# PE Due Diligence Data Platform Plan

**Created:** 2026-01-23
**Status:** In Progress
**Goal:** Build comprehensive data ingestion and analysis platform for Private Equity due diligence

---

## Executive Summary

Transform ZeroStack into a PE due diligence platform that can:
1. Ingest data from any source (files, accounting systems, CRMs, HR systems)
2. Automatically detect data quality issues
3. Identify red flags and anomalies relevant to PE analysis
4. Generate comprehensive data profiles for target companies

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
├─────────────┬─────────────┬─────────────┬─────────────┬────────────┤
│  Data Room  │  Accounting │    CRM      │     HR      │  Custom    │
│  CSV/Excel  │   Codat     │  Merge.dev  │  Merge.dev  │   APIs     │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴─────┬──────┘
       │             │             │             │            │
       ▼             ▼             ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │  Schema   │  │  Type     │  │  Quality  │  │  Category │        │
│  │ Detection │  │ Inference │  │  Scoring  │  │ Detection │        │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ANALYSIS ENGINE                                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │  Anomaly  │  │   Trend   │  │  Red Flag │  │  Cross-   │        │
│  │ Detection │  │  Analysis │  │  Scanner  │  │  Reference│        │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     OUTPUT LAYER                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │  Reports  │  │  Alerts   │  │  Exports  │  │    API    │        │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase Overview

| Phase | Focus | Effort | Status |
|-------|-------|--------|--------|
| Phase 1 | File Ingestion | 1 day | ✅ Complete |
| Phase 2 | PE Analysis Engine | 2-3 days | 📝 Planned |
| Phase 3 | Codat Integration | 2-3 days | 📝 Planned |
| Phase 4 | Merge.dev Integration | 2-3 days | 📝 Planned |
| Phase 5 | Reporting & Dashboards | 2-3 days | 📝 Planned |

---

## Phase 1: File Ingestion (Data Room Support)

**Goal:** Accept any CSV/Excel file and automatically analyze it

### What's Built
- [x] Upload endpoint (`POST /api/v1/ingest/upload`)
- [x] Schema detection service
- [x] Type inference (string, integer, float, date, currency, percentage, email, etc.)
- [x] Quality scoring (0-100)
- [x] PE category detection (financial, customer, operational, sales, hr, inventory)
- [x] Sample data preview

### What's Missing

| ID | Task | Status | Effort |
|----|------|--------|--------|
| 1.1 | Create ingestion database tables | [x] Done | 1 hr |
| 1.2 | Persist uploaded files to storage | [x] Done | 1 hr |
| 1.3 | Build upload history API | [x] Done | 1 hr |
| 1.4 | Create frontend upload page | [x] Done | 2 hr |
| 1.5 | Add batch upload support | [x] Done | 1 hr |

### Task Details

#### 1.1 Create ingestion database tables
**File:** `backend/migrations/versions/036_add_ingestion_tables.py`

```sql
ingested_files:
  - id (uuid, pk)
  - filename (string)
  - original_filename (string)
  - file_size_bytes (int)
  - file_type (string)
  - storage_path (string)
  - upload_source (enum: manual, codat, merge, api)
  - quality_score (numeric)
  - row_count (int)
  - column_count (int)
  - detected_categories (jsonb)
  - analysis_result (jsonb)
  - deal_id (uuid, fk, nullable) -- for grouping by PE deal
  - uploaded_by (string)
  - uploaded_at (timestamp)
  - analyzed_at (timestamp)

pe_deals:
  - id (uuid, pk)
  - name (string)
  - target_company (string)
  - status (enum: active, closed, passed)
  - created_at (timestamp)
  - updated_at (timestamp)

ingestion_issues:
  - id (uuid, pk)
  - file_id (uuid, fk)
  - issue_type (enum: quality, anomaly, red_flag, missing_data)
  - severity (enum: low, medium, high, critical)
  - column_name (string, nullable)
  - description (text)
  - details (jsonb)
  - acknowledged (boolean)
  - acknowledged_by (string)
  - created_at (timestamp)
```

#### 1.2 Persist uploaded files to storage
**File:** `backend/domains/data_ingestion/service.py`

- Save raw file to MinIO object storage
- Store metadata in database
- Link to deal if provided

#### 1.3 Build upload history API
**File:** `backend/domains/data_ingestion/router.py`

```
GET  /api/v1/ingest/files - List uploaded files
GET  /api/v1/ingest/files/{id} - Get file details + analysis
DELETE /api/v1/ingest/files/{id} - Delete file
GET  /api/v1/ingest/deals - List PE deals
POST /api/v1/ingest/deals - Create PE deal
GET  /api/v1/ingest/deals/{id}/files - Files for a deal
GET  /api/v1/ingest/issues - List all issues
GET  /api/v1/ingest/issues?file_id= - Issues for a file
POST /api/v1/ingest/issues/{id}/acknowledge - Acknowledge issue
```

#### 1.4 Create frontend upload page
**File:** `frontend/src/pages/DataIngestion.tsx`

Components:
- Drag-and-drop upload zone
- Upload progress indicator
- File list with quality scores
- Click to view analysis details
- Filter by deal, date, quality
- Issue summary panel

#### 1.5 Add batch upload support
- Accept multiple files in single request
- Process in parallel
- Return combined analysis

---

## Phase 2: PE Analysis Engine

**Goal:** Automatically detect issues and red flags in financial/operational data

### Tasks

| ID | Task | Status | Effort |
|----|------|--------|--------|
| 2.1 | Build anomaly detection service | [ ] Todo | 3 hr |
| 2.2 | Create red flag scanner | [ ] Todo | 3 hr |
| 2.3 | Build trend analysis service | [ ] Todo | 2 hr |
| 2.4 | Create cross-file reconciliation | [ ] Todo | 3 hr |
| 2.5 | Add AI-powered insights | [ ] Todo | 2 hr |

### Task Details

#### 2.1 Build anomaly detection service
**File:** `backend/domains/data_ingestion/anomaly_detector.py`

Detection methods:
- Statistical outliers (IQR, Z-score)
- Benford's Law for financial data
- Sudden trend changes
- Seasonal anomalies
- Missing period detection

```python
class AnomalyDetector:
    def detect_outliers(df: DataFrame, column: str) -> List[Anomaly]
    def check_benfords_law(df: DataFrame, column: str) -> BenfordResult
    def detect_trend_breaks(df: DataFrame, date_col: str, value_col: str) -> List[TrendBreak]
    def find_missing_periods(df: DataFrame, date_col: str, expected_freq: str) -> List[MissingPeriod]
```

#### 2.2 Create red flag scanner
**File:** `backend/domains/data_ingestion/red_flag_scanner.py`

PE-specific red flags:
- Revenue concentration (>30% from single customer)
- Margin compression trends
- Working capital anomalies
- Headcount vs revenue misalignment
- Unusual seasonality patterns
- Round number bias in financials
- Late-period revenue spikes
- Inventory buildup without sales growth

```python
class RedFlagScanner:
    def scan_revenue_concentration(df: DataFrame) -> List[RedFlag]
    def scan_margin_trends(df: DataFrame) -> List[RedFlag]
    def scan_working_capital(df: DataFrame) -> List[RedFlag]
    def scan_headcount_alignment(df: DataFrame) -> List[RedFlag]
    def scan_round_numbers(df: DataFrame) -> List[RedFlag]
    def scan_period_end_spikes(df: DataFrame) -> List[RedFlag]
```

#### 2.3 Build trend analysis service
**File:** `backend/domains/data_ingestion/trend_analyzer.py`

Capabilities:
- Linear trend detection
- Growth rate calculation (MoM, QoQ, YoY)
- Seasonality detection
- Forecast vs actual comparison
- Cohort analysis for customer data

#### 2.4 Create cross-file reconciliation
**File:** `backend/domains/data_ingestion/reconciliation.py`

Cross-reference checks:
- Revenue in P&L vs revenue in sales data
- Headcount in HR vs payroll expense
- Customer count consistency
- Inventory vs COGS relationship

#### 2.5 Add AI-powered insights
**File:** `backend/domains/data_ingestion/ai_insights.py`

Use LLM to:
- Summarize key findings
- Explain anomalies in business context
- Suggest follow-up questions for management
- Generate executive summary

---

## Phase 3: Codat Integration (Accounting Systems)

**Goal:** Pull financial data directly from QuickBooks, Xero, NetSuite, etc.

### Codat Coverage
- QuickBooks Online/Desktop
- Xero
- Sage
- NetSuite
- FreshBooks
- Wave
- Zoho Books
- MYOB

### Tasks

| ID | Task | Status | Effort |
|----|------|--------|--------|
| 3.1 | Set up Codat sandbox account | [ ] Todo | 30 min |
| 3.2 | Create Codat connector service | [ ] Todo | 3 hr |
| 3.3 | Build company linking flow | [ ] Todo | 2 hr |
| 3.4 | Implement data sync endpoints | [ ] Todo | 3 hr |
| 3.5 | Map Codat schema to internal format | [ ] Todo | 2 hr |
| 3.6 | Build accounting data UI | [ ] Todo | 3 hr |

### Task Details

#### 3.1 Set up Codat sandbox account
- Sign up at codat.io
- Get API key
- Configure sandbox companies
- Test API connectivity

#### 3.2 Create Codat connector service
**File:** `backend/domains/connectors/codat/service.py`

```python
class CodatService:
    def create_company(name: str, deal_id: uuid) -> CodatCompany
    def get_link_url(company_id: str) -> str
    def list_connections(company_id: str) -> List[Connection]
    def sync_data(company_id: str, data_type: str) -> SyncResult
    def get_balance_sheet(company_id: str, period: str) -> BalanceSheet
    def get_profit_and_loss(company_id: str, period: str) -> ProfitAndLoss
    def get_invoices(company_id: str) -> List[Invoice]
    def get_customers(company_id: str) -> List[Customer]
    def get_bank_transactions(company_id: str) -> List[Transaction]
```

#### 3.3 Build company linking flow
**Files:**
- `backend/domains/connectors/codat/router.py`
- `frontend/src/pages/CodatConnect.tsx`

Flow:
1. User creates PE deal
2. User clicks "Connect Accounting"
3. Generate Codat link URL
4. Redirect to Codat hosted auth
5. Target company connects their accounting system
6. Webhook notifies of connection
7. Auto-sync financial data

#### 3.4 Implement data sync endpoints
```
POST /api/v1/connectors/codat/companies - Create company
GET  /api/v1/connectors/codat/companies/{id}/link - Get link URL
POST /api/v1/connectors/codat/companies/{id}/sync - Trigger sync
GET  /api/v1/connectors/codat/companies/{id}/balance-sheet
GET  /api/v1/connectors/codat/companies/{id}/profit-loss
GET  /api/v1/connectors/codat/companies/{id}/invoices
GET  /api/v1/connectors/codat/companies/{id}/customers
GET  /api/v1/connectors/codat/companies/{id}/bank-transactions
POST /api/v1/connectors/codat/webhook - Handle Codat webhooks
```

#### 3.5 Map Codat schema to internal format
Create normalized internal models that work across all accounting systems:
- StandardFinancials
- StandardCustomer
- StandardInvoice
- StandardTransaction

#### 3.6 Build accounting data UI
**File:** `frontend/src/pages/AccountingData.tsx`

Components:
- Financial statements viewer (P&L, Balance Sheet)
- Customer list with revenue breakdown
- Invoice aging report
- Bank reconciliation view
- Data freshness indicators

---

## Phase 4: Merge.dev Integration (HR & CRM)

**Goal:** Pull employee and customer data from HR and CRM systems

### Merge.dev Coverage

**HR/Payroll:**
- BambooHR, Gusto, Rippling, Workday, ADP, Paylocity, UKG

**CRM:**
- Salesforce, HubSpot, Pipedrive, Zoho CRM, Close

**ATS:**
- Greenhouse, Lever, Workable, JazzHR

### Tasks

| ID | Task | Status | Effort |
|----|------|--------|--------|
| 4.1 | Set up Merge.dev sandbox | [ ] Todo | 30 min |
| 4.2 | Create Merge connector service | [ ] Todo | 3 hr |
| 4.3 | Build HR data sync | [ ] Todo | 2 hr |
| 4.4 | Build CRM data sync | [ ] Todo | 2 hr |
| 4.5 | Create HR/CRM analysis views | [ ] Todo | 3 hr |

### Task Details

#### 4.2 Create Merge connector service
**File:** `backend/domains/connectors/merge/service.py`

```python
class MergeService:
    # HR endpoints
    def get_employees(linked_account_id: str) -> List[Employee]
    def get_employments(linked_account_id: str) -> List[Employment]
    def get_teams(linked_account_id: str) -> List[Team]
    def get_time_off(linked_account_id: str) -> List[TimeOff]

    # CRM endpoints
    def get_contacts(linked_account_id: str) -> List[Contact]
    def get_accounts(linked_account_id: str) -> List[Account]
    def get_opportunities(linked_account_id: str) -> List[Opportunity]
    def get_activities(linked_account_id: str) -> List[Activity]
```

#### 4.5 Create HR/CRM analysis views
**Files:**
- `frontend/src/pages/HRAnalysis.tsx`
- `frontend/src/pages/CRMAnalysis.tsx`

HR Analysis:
- Headcount over time
- Tenure distribution
- Department breakdown
- Compensation analysis (if available)
- Turnover metrics

CRM Analysis:
- Pipeline value and velocity
- Customer concentration
- Win rate trends
- Sales rep productivity
- Churn indicators

---

## Phase 5: Reporting & Dashboards

**Goal:** Comprehensive PE due diligence reporting

### Tasks

| ID | Task | Status | Effort |
|----|------|--------|--------|
| 5.1 | Create deal dashboard | [ ] Todo | 3 hr |
| 5.2 | Build data quality scorecard | [ ] Todo | 2 hr |
| 5.3 | Create red flag summary view | [ ] Todo | 2 hr |
| 5.4 | Build export/report generator | [ ] Todo | 3 hr |
| 5.5 | Add executive summary AI | [ ] Todo | 2 hr |

### Task Details

#### 5.1 Create deal dashboard
**File:** `frontend/src/pages/DealDashboard.tsx`

Sections:
- Deal overview (target company, status, team)
- Data sources connected
- Overall data quality score
- Key metrics summary
- Red flags & issues
- Recent activity

#### 5.2 Build data quality scorecard
Components:
- Completeness score per data source
- Freshness indicators
- Consistency checks
- Coverage gaps

#### 5.3 Create red flag summary view
- Grouped by category (financial, operational, customer)
- Severity indicators
- Supporting evidence
- Recommended follow-ups

#### 5.4 Build export/report generator
Export formats:
- PDF executive summary
- Excel data pack
- PowerPoint slides
- JSON/API for integration

#### 5.5 Add executive summary AI
Use LLM to generate:
- 1-page deal summary
- Key findings narrative
- Risk assessment
- Recommended due diligence areas

---

## Data Categories & Red Flags

### Financial Data
| Metric | Red Flag Threshold |
|--------|-------------------|
| Revenue concentration | >30% from single customer |
| Gross margin trend | Declining 3+ consecutive periods |
| Working capital days | >90 days or trending up |
| Revenue vs cash | >20% divergence |
| Round numbers | >30% of transactions |
| Period-end spikes | >40% of monthly revenue in last week |

### Customer Data
| Metric | Red Flag Threshold |
|--------|-------------------|
| Customer churn | >15% annual |
| Logo churn vs revenue churn | >2x difference |
| Customer concentration | Top 10 = >50% revenue |
| Cohort retention | <70% at 12 months |
| NRR | <100% |

### Operational Data
| Metric | Red Flag Threshold |
|--------|-------------------|
| Revenue per employee | Declining trend |
| Headcount growth vs revenue | >2x revenue growth |
| Employee tenure | <2 years average |
| Management turnover | >30% in 2 years |

---

## API Summary

### Ingestion
```
POST /api/v1/ingest/upload              - Upload and analyze file
GET  /api/v1/ingest/files               - List uploaded files
GET  /api/v1/ingest/files/{id}          - Get file details
GET  /api/v1/ingest/deals               - List PE deals
POST /api/v1/ingest/deals               - Create deal
GET  /api/v1/ingest/deals/{id}/summary  - Deal summary
GET  /api/v1/ingest/issues              - List all issues
```

### Connectors
```
# Codat (Accounting)
POST /api/v1/connectors/codat/companies
GET  /api/v1/connectors/codat/companies/{id}/link
GET  /api/v1/connectors/codat/companies/{id}/financials

# Merge (HR/CRM)
POST /api/v1/connectors/merge/link
GET  /api/v1/connectors/merge/{id}/employees
GET  /api/v1/connectors/merge/{id}/customers
GET  /api/v1/connectors/merge/{id}/opportunities
```

### Analysis
```
POST /api/v1/analysis/anomalies         - Run anomaly detection
POST /api/v1/analysis/red-flags         - Scan for red flags
POST /api/v1/analysis/reconcile         - Cross-file reconciliation
GET  /api/v1/analysis/trends            - Trend analysis
POST /api/v1/analysis/ai-summary        - AI-generated summary
```

---

## Environment Variables

```env
# Codat
CODAT_API_KEY=
CODAT_WEBHOOK_SECRET=

# Merge.dev
MERGE_API_KEY=
MERGE_WEBHOOK_SECRET=

# Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=pe-files

# AI (for summaries)
OPENAI_API_KEY=
```

---

## Testing Checklist

### Phase 1 - File Ingestion
- [ ] Upload CSV, verify schema detection
- [ ] Upload Excel with multiple sheets
- [ ] Verify quality score calculation
- [ ] Test PE category detection
- [ ] Verify file persistence
- [ ] Test issue creation

### Phase 2 - Analysis Engine
- [ ] Detect statistical outliers
- [ ] Verify Benford's Law check
- [ ] Test trend break detection
- [ ] Verify red flag triggers
- [ ] Test cross-file reconciliation

### Phase 3 - Codat
- [ ] Create sandbox company
- [ ] Complete OAuth flow
- [ ] Sync balance sheet
- [ ] Sync P&L
- [ ] Verify data mapping

### Phase 4 - Merge.dev
- [ ] Link HR system
- [ ] Sync employee data
- [ ] Link CRM
- [ ] Sync opportunity data
- [ ] Verify unified schema

### Phase 5 - Reporting
- [ ] Generate deal summary
- [ ] Export to PDF
- [ ] Export to Excel
- [ ] AI summary generation

---

## Progress Log

| Date | Task | Status | Notes |
|------|------|--------|-------|
| 2026-01-23 | Plan created | Done | 5 phases defined |
| 2026-01-23 | 1.0 Basic upload endpoint | Done | POST /api/v1/ingest/upload working |
| 2026-01-23 | 1.1 Create ingestion tables | Done | Migration 036_add_ingestion_tables.py |
| 2026-01-23 | 1.2-1.3 Persistence + API | Done | Full CRUD for deals, files, issues |
| 2026-01-23 | 1.4 Frontend upload page | Done | DataIngestion.tsx with drag-drop |
| 2026-01-23 | 1.5 Batch upload support | Done | Multiple file upload supported |
| | | | |

---

## Recovery Guide

If session fails, resume by:
1. Check this file for last completed task
2. Run `docker compose -p zerostack up -d` to ensure services running
3. Test upload endpoint: `curl -X POST http://localhost:8000/api/v1/ingest/upload -F "file=@test.csv"`
4. Continue from next uncompleted task

---

## Quick Start (Current State)

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8000

# Test upload (from backend directory)
python test_upload.py

# Or use curl
curl -X POST "http://localhost:8000/api/v1/ingest/upload" \
  -F "file=@your_data.csv"
```
