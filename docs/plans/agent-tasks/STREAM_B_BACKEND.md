# Stream B: Backend Feature Completion

**Priority:** HIGH
**Estimated Duration:** 5 weeks
**Dependencies:** None (parallel with Stream A)

---

## Overview

Complete stubbed backend features: Insights, Datasets, Jobs Queue, and Governance.

---

## Week 1-2: Insights Backend

### B1.1 Implement Insight Generation
**Files:** `backend/domains/insights/router.py`, `backend/domains/insights/service.py` (new)
**Effort:** MEDIUM
**Deliverable:** LLM-based insight generation

**Current Status:** All endpoints return 501 errors

**Requirements:**
- POST `/insights/generate` - Generate insights from data
- Use existing chat/LLM infrastructure
- Prompt engineering for data insights
- Store generated insights

**Implementation:**
```python
# Example insight generation flow
1. Receive dataset/table reference
2. Fetch sample data and statistics
3. Send to LLM with insight prompt
4. Parse and store insights
5. Return insight IDs
```

### B1.2 Add Trend Detection
**Files:** `backend/domains/insights/service.py`
**Effort:** MEDIUM
**Deliverable:** Trend detection algorithms

**Requirements:**
- Time-series trend analysis
- Moving averages
- Growth rate calculations
- Trend classification (up/down/stable)

### B1.3 Implement Anomaly Detection
**Files:** `backend/domains/insights/service.py`
**Effort:** MEDIUM
**Deliverable:** Anomaly flagging in data

**Requirements:**
- Statistical anomaly detection (z-score, IQR)
- Threshold-based alerts
- Anomaly severity levels
- Historical comparison

### B1.4 Add Insight Scheduling
**Files:** `backend/domains/insights/scheduler.py` (new)
**Effort:** LOW
**Deliverable:** Cron-triggered insight generation

**Requirements:**
- Link to existing scheduler infrastructure
- Configure insight refresh frequency
- Selective insight regeneration

---

## Week 2-3: Dataset Upload

### B2.1 Implement File Upload
**Files:** `backend/domains/datasets/router.py`, `backend/domains/datasets/service.py` (new)
**Effort:** MEDIUM
**Deliverable:** Stream uploads to MinIO

**Current Status:** Returns `{"status": "stub"}` (Line 37)

**Requirements:**
- Multipart file upload endpoint
- Stream to MinIO/object storage
- Compute SHA256 hash during upload
- Support CSV, Parquet, JSON formats

**Existing TODO (Line 37):**
```python
# TODO: stream to ObjectStore, compute sha256, basic sniff for schema
```

### B2.2 Add Schema Inference
**Files:** `backend/domains/datasets/service.py`
**Effort:** MEDIUM
**Deliverable:** Auto-detect column types

**Requirements:**
- Infer column types from sample data
- Detect date formats
- Identify categorical vs numerical
- Generate schema JSON

### B2.3 Dataset Versioning
**Files:** `backend/domains/datasets/models.py`, `backend/domains/datasets/service.py`
**Effort:** LOW
**Deliverable:** Version tracking for datasets

**Requirements:**
- Version number on each upload
- Link versions to same dataset
- Version comparison
- Rollback capability

### B2.4 Data Quality Profiling
**Files:** `backend/domains/datasets/profiler.py` (new)
**Effort:** MEDIUM
**Deliverable:** Quality scores on upload

**Requirements:**
- Completeness score (null %)
- Uniqueness check
- Format validation
- Statistical summary (min, max, mean, std)

---

## Week 3-4: Jobs Queue

### B3.1 Implement Job Queue
**Files:** `backend/domains/jobs/router.py`, `backend/domains/jobs/service.py` (new)
**Effort:** MEDIUM
**Deliverable:** Redis-backed background job queue

**Current Status:** All endpoints return 501 errors

**Requirements:**
- Job submission endpoint
- Job status tracking
- Use Redis for queue (or APScheduler)
- Worker process for job execution

### B3.2 Add Job Prioritization
**Files:** `backend/domains/jobs/service.py`
**Effort:** LOW
**Deliverable:** Priority levels for jobs

**Requirements:**
- Priority enum (low, normal, high, critical)
- Priority queue ordering
- Priority-based resource allocation

### B3.3 Job Cancellation
**Files:** `backend/domains/jobs/router.py`
**Effort:** LOW
**Deliverable:** Cancel running/queued jobs

**Requirements:**
- DELETE `/jobs/{job_id}` endpoint
- Graceful cancellation
- Status update to "cancelled"
- Cleanup on cancel

### B3.4 Job Monitoring
**Files:** `backend/domains/jobs/router.py`
**Effort:** MEDIUM
**Deliverable:** Job status dashboard data

**Requirements:**
- List all jobs with filters
- Job history and logs
- Aggregate statistics
- WebSocket for real-time updates (optional)

---

## Week 4-5: Governance

### B4.1 Implement Access Policies
**Files:** `backend/domains/governance/router.py`, `backend/domains/governance/service.py` (new)
**Effort:** HIGH
**Deliverable:** Policy engine for data access

**Current Status:** All endpoints return 501 errors

**Requirements:**
- Policy CRUD operations
- Policy types (allow/deny)
- Resource scoping (table, column, row)
- Policy evaluation engine

### B4.2 Approval Workflows
**Files:** `backend/domains/governance/workflows.py` (new)
**Effort:** MEDIUM
**Deliverable:** Multi-stage approval states

**Requirements:**
- Workflow definition (stages, approvers)
- Approval/rejection actions
- Notification on stage change
- Timeout handling

### B4.3 Audit Logging
**Files:** `backend/domains/governance/audit.py` (new)
**Effort:** MEDIUM
**Deliverable:** Comprehensive audit trail

**Requirements:**
- Log all data access
- Log policy changes
- Log approval decisions
- Queryable audit log endpoint

### B4.4 Compliance Reporting
**Files:** `backend/domains/governance/compliance.py` (new)
**Effort:** LOW
**Deliverable:** GDPR/HIPAA compliance reports

**Requirements:**
- Data inventory report
- Access history report
- PII exposure report
- Export to PDF/CSV

---

## Exit Criteria

- [ ] Insights generating from data
- [ ] Trend and anomaly detection working
- [ ] Dataset upload with versioning
- [ ] Schema inference on upload
- [ ] Background jobs processing
- [ ] Job monitoring available
- [ ] Governance policies enforceable
- [ ] Audit logging active

---

## Testing Requirements

Create tests for each domain:
- `backend/tests/test_insights.py`
- `backend/tests/test_datasets.py`
- `backend/tests/test_jobs.py`
- `backend/tests/test_governance.py`

---

## Related Files Reference

**Currently Stubbed:**
- `backend/domains/insights/router.py` - 501 errors
- `backend/domains/datasets/router.py` - Stub response
- `backend/domains/jobs/router.py` - 501 errors
- `backend/domains/governance/router.py` - 501 errors

**Services to Reference:**
- `backend/domains/chat/service.py` - LLM integration pattern
- `backend/services/object_store/` - MinIO integration
- `backend/services/scheduler.py` - Job scheduling pattern
- `backend/domains/data_explorer/dictionary_router.py` - Approval workflow pattern
