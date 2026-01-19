# Master Task Checklist - Prioritized by Feature Importance

**Last Updated:** January 2026
**Purpose:** Single source of truth for all tasks, ordered by user/business value

---

## Quick Navigation

| Tier | Focus | Status |
|------|-------|--------|
| [Tier 1](#tier-1-critical-features) | Critical Features | Enables core workflows |
| [Tier 2](#tier-2-high-value-differentiators) | Differentiators | Competitive advantage |
| [Tier 3](#tier-3-operational-value) | Operations | Day-to-day usability |
| [Tier 4](#tier-4-ux--polish) | UX & Polish | Better experience |
| [Tier 5](#tier-5-testing--quality) | Testing | Stability |
| [Tier 6](#tier-6-infrastructure) | Infrastructure | Platform reliability |

---

## Tier 1: Critical Features
*These features directly enable users to accomplish core workflows*

### 1.1 Dataset Upload & Storage
**Impact:** CRITICAL - Users cannot import their own data without this
**Current Status:** Returns `{"status": "stub"}`
**Effort:** 3-4 days
**Files:** `backend/domains/datasets/router.py`, `service.py` (new)

| Task | Status | Notes |
|------|--------|-------|
| [ ] 1.1.1 Implement multipart file upload endpoint | | Stream to MinIO |
| [ ] 1.1.2 Compute SHA256 hash during upload | | For versioning |
| [ ] 1.1.3 Support CSV, Parquet, JSON formats | | File type detection |
| [ ] 1.1.4 Add schema inference on upload | | Auto-detect column types |
| [ ] 1.1.5 Implement dataset versioning | | Link versions to same dataset |
| [ ] 1.1.6 Add data quality profiling | | Completeness, uniqueness, stats |
| [ ] 1.1.7 Create frontend upload UI | | Drag-drop, progress bar |

**Reference:** `backend/services/object_store/` for MinIO integration pattern

---

### 1.2 Insights Generation
**Impact:** HIGH - Frontend exists but backend is completely stubbed
**Current Status:** All endpoints return 501 errors
**Effort:** 3-4 days
**Files:** `backend/domains/insights/router.py`, `service.py` (new)

| Task | Status | Notes |
|------|--------|-------|
| [ ] 1.2.1 Implement POST `/insights/generate` | | Use LLM infrastructure |
| [ ] 1.2.2 Create insight prompt templates | | Data-aware prompts |
| [ ] 1.2.3 Store generated insights in DB | | With metadata |
| [ ] 1.2.4 Add trend detection algorithms | | Moving avg, growth rate |
| [ ] 1.2.5 Implement anomaly detection | | Z-score, IQR methods |
| [ ] 1.2.6 Connect frontend to new API | | Update Insights.tsx |
| [ ] 1.2.7 Add insight scheduling | | Link to scheduler |

**Reference:** `backend/domains/chat/service.py` for LLM integration pattern

---

### 1.3 Notification Delivery
**Impact:** HIGH - Drift alerts and schedule notifications are dead-ends
**Current Status:** TODOs at `scheduler.py:281-287`
**Effort:** 2-3 days
**Files:** `backend/services/notifications.py`, `scheduler.py`

| Task | Status | Notes |
|------|--------|-------|
| [ ] 1.3.1 Implement SMTP email delivery | | With templates |
| [ ] 1.3.2 Implement Slack webhook integration | | Block formatting |
| [ ] 1.3.3 Implement generic webhook notifications | | Custom payloads |
| [ ] 1.3.4 Wire notifications to scheduler events | | Success/failure |
| [ ] 1.3.5 Wire notifications to drift alerts | | Alert severity |
| [ ] 1.3.6 Add notification preferences UI | | User settings |

**Environment Variables Needed:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SLACK_WEBHOOK_URL=
```

---

## Tier 2: High-Value Differentiators
*Features that make the platform more powerful than alternatives*

### 2.1 Feature Store
**Impact:** HIGH - Prevents duplicate feature engineering work
**Current Status:** Not implemented
**Effort:** 5-6 days
**Files:** `backend/domains/feature_store/` (new)

| Task | Status | Notes |
|------|--------|-------|
| [ ] 2.1.1 Design feature definition schema | | SQL or Python |
| [ ] 2.1.2 Implement feature CRUD endpoints | | Versioned |
| [ ] 2.1.3 Add point-in-time feature lookups | | For ML training |
| [ ] 2.1.4 Implement feature sets (groups) | | Reusable bundles |
| [ ] 2.1.5 Add auto-compute for new data | | Scheduled refresh |
| [ ] 2.1.6 Create feature statistics/profiling | | Distribution, nulls |
| [ ] 2.1.7 Build feature store UI | | Browse, search, use |

---

### 2.2 Complete Synthetic Data
**Impact:** HIGH - Core feature is partial, just needs data loading
**Current Status:** TODOs at `synthetic/router.py:181,192`
**Effort:** 2-3 days
**Files:** `backend/domains/synthetic/router.py`, `service.py`

| Task | Status | Notes |
|------|--------|-------|
| [ ] 2.2.1 Implement dataset loading from MinIO | | Line 181 TODO |
| [ ] 2.2.2 Implement table loading from connections | | Line 192 TODO |
| [ ] 2.2.3 Add export formats (CSV, JSON, Parquet) | | Download generated data |
| [ ] 2.2.4 Add quality metrics visualization | | Charts in frontend |
| [ ] 2.2.5 Implement privacy score display | | Risk indicators |
| [ ] 2.2.6 Add generation history | | Track past jobs |
| [ ] 2.2.7 Create real vs synthetic comparison view | | Side-by-side |

---

### 2.3 Model Deployment
**Impact:** HIGH - Models are useless if they can't serve predictions
**Current Status:** Not implemented
**Effort:** 5-6 days
**Files:** `backend/domains/ml_deployment/` (new)

| Task | Status | Notes |
|------|--------|-------|
| [ ] 2.3.1 Design deployment architecture | | Container-based |
| [ ] 2.3.2 Implement one-click deploy from registry | | From model version |
| [ ] 2.3.3 Create auto-generated REST API | | Input/output schema |
| [ ] 2.3.4 Add batch prediction endpoint | | Bulk inference |
| [ ] 2.3.5 Add real-time prediction endpoint | | Low-latency |
| [ ] 2.3.6 Implement A/B deployment | | Traffic splitting |
| [ ] 2.3.7 Add endpoint monitoring/scaling | | Metrics, autoscale |
| [ ] 2.3.8 Build deployment management UI | | Status, logs, scale |

---

### 2.4 Enhanced Drift Detection
**Impact:** MEDIUM - Statistical rigor for drift detection
**Current Status:** Basic comparison only
**Effort:** 2-3 days
**Files:** `backend/services/drift_detector.py`

| Task | Status | Notes |
|------|--------|-------|
| [ ] 2.4.1 Add KS-test for numerical columns | | scipy.stats |
| [ ] 2.4.2 Add Chi-squared test for categorical | | Distribution shift |
| [ ] 2.4.3 Implement PSI (Population Stability Index) | | Industry standard |
| [ ] 2.4.4 Add feature importance drift | | Track ML features |
| [ ] 2.4.5 Implement automated retraining triggers | | Based on drift |
| [ ] 2.4.6 Add drift visualization over time | | Charts |

---

## Tier 3: Operational Value
*Makes the platform more usable day-to-day*

### 3.1 Query History & Saved Queries
**Impact:** MEDIUM - Users re-type same queries repeatedly
**Current Status:** Not implemented
**Effort:** 2 days
**Files:** `backend/domains/data_explorer/`

| Task | Status | Notes |
|------|--------|-------|
| [ ] 3.1.1 Add query history table/model | | Store executed queries |
| [ ] 3.1.2 Implement save query endpoint | | Name, description |
| [ ] 3.1.3 Add query history list endpoint | | With pagination |
| [ ] 3.1.4 Create saved queries list endpoint | | Personal/shared |
| [ ] 3.1.5 Build query history sidebar UI | | Quick access |
| [ ] 3.1.6 Add query search/filter | | By content, date |

---

### 3.2 Notebook Templates
**Impact:** MEDIUM - Speed up common workflows
**Current Status:** Not implemented
**Effort:** 1-2 days
**Files:** `backend/domains/notebooks/`

| Task | Status | Notes |
|------|--------|-------|
| [ ] 3.2.1 Create template model | | Name, cells, tags |
| [ ] 3.2.2 Add template CRUD endpoints | | Create, list, use |
| [ ] 3.2.3 Implement "New from template" | | Clone with variables |
| [ ] 3.2.4 Create built-in templates | | EDA, ML, reporting |
| [ ] 3.2.5 Add template gallery UI | | Browse, preview |

---

### 3.3 Background Jobs Queue
**Impact:** MEDIUM - Long-running tasks block users
**Current Status:** Returns 501 errors
**Effort:** 3-4 days
**Files:** `backend/domains/jobs/router.py`, `service.py` (new)

| Task | Status | Notes |
|------|--------|-------|
| [ ] 3.3.1 Implement Redis-backed job queue | | Or APScheduler |
| [ ] 3.3.2 Add job submission endpoint | | With priority |
| [ ] 3.3.3 Add job status tracking | | Progress, logs |
| [ ] 3.3.4 Implement job cancellation | | Graceful stop |
| [ ] 3.3.5 Add job monitoring dashboard | | List, filter, stats |
| [ ] 3.3.6 Create worker process | | Execute queued jobs |

---

### 3.4 Export Enhancements
**Impact:** LOW - More flexibility for users
**Current Status:** Only Parquet/CSV
**Effort:** 1 day

| Task | Status | Notes |
|------|--------|-------|
| [ ] 3.4.1 Add JSON export for datasets | | Pretty-printed |
| [ ] 3.4.2 Add Excel export for datasets | | openpyxl |
| [ ] 3.4.3 Add notebook export as .py | | Code only |
| [ ] 3.4.4 Add notebook export as .sql | | SQL cells only |

---

## Tier 4: UX & Polish
*Makes existing features feel better*

### 4.1 Split Large Frontend Components
**Impact:** MEDIUM - Maintainability, faster development
**Effort:** 3-4 days total

| Task | Status | Notes |
|------|--------|-------|
| [ ] 4.1.1 Split DataDictionary.tsx (1,745 lines) | | 5-7 components |
| [ ] 4.1.2 Split NotebookPage.tsx (912 lines) | | 4-5 components |
| [ ] 4.1.3 Split DataExplorer.tsx (915 lines) | | 4-5 components |

**Target:** No component > 500 lines

---

### 4.2 Error Handling & Loading States
**Impact:** MEDIUM - Better user experience
**Effort:** 2-3 days

| Task | Status | Notes |
|------|--------|-------|
| [x] 4.2.1 Create Toast notification service | ✅ F3 | ToastContext done |
| [ ] 4.2.2 Add Error Boundaries | | Catch React errors |
| [x] 4.2.3 Fix MLWorkbench to use API client | ✅ F2 | Done |
| [ ] 4.2.4 Add loading skeletons | | Replace blank states |
| [ ] 4.2.5 Add retry buttons on failures | | With backoff |

---

### 4.3 Keyboard Shortcuts
**Impact:** LOW - Power user productivity
**Effort:** 1-2 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 4.3.1 Add Ctrl+K for global search | | Command palette |
| [ ] 4.3.2 Add Ctrl+S for save | | Context-aware |
| [ ] 4.3.3 Add Esc to close modals | | Global handler |
| [ ] 4.3.4 Add ? for shortcuts help | | Overlay |

---

## Tier 5: Testing & Quality
*Stability and confidence in changes*

### 5.1 Critical Feature Tests
**Impact:** HIGH - New features have 0% coverage
**Effort:** 3-4 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 5.1.1 Add notebook execution tests | | CRITICAL |
| [ ] 5.1.2 Add synthetic data generation tests | | CRITICAL |
| [ ] 5.1.3 Add dataset upload tests | | After 1.1 |
| [ ] 5.1.4 Add insights generation tests | | After 1.2 |

---

### 5.2 Integration Tests
**Impact:** MEDIUM - Catch cross-component issues
**Effort:** 3-4 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 5.2.1 Add GPU adapter tests (mocked) | | RunPod integration |
| [ ] 5.2.2 Add lineage parsing tests | | SQL edge cases |
| [ ] 5.2.3 Add data connection tests | | CRUD + encryption |
| [ ] 5.2.4 Add drift detection tests | | Statistical tests |

---

### 5.3 E2E Tests
**Impact:** MEDIUM - Catch user-facing regressions
**Effort:** 4-5 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 5.3.1 Setup Playwright | | Test infrastructure |
| [ ] 5.3.2 Add data explorer E2E | | Query execution |
| [ ] 5.3.3 Add notebook E2E | | Cell execution |
| [ ] 5.3.4 Add distillation E2E | | Response curation |

---

## Tier 6: Infrastructure
*Platform reliability and governance*

### 6.1 Evaluation Pack Metrics
**Impact:** MEDIUM - Standard ML evaluation
**Effort:** 2 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 6.1.1 Add classification metrics | | Accuracy, F1, ROC |
| [ ] 6.1.2 Add regression metrics | | MSE, RMSE, R2 |
| [ ] 6.1.3 Add NLP metrics | | BLEU, ROUGE |

---

### 6.2 Governance & Policies
**Impact:** LOW (for now) - Enterprise requirement
**Effort:** 5+ days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 6.2.1 Implement access policies | | Allow/deny rules |
| [ ] 6.2.2 Add approval workflows | | Multi-stage |
| [ ] 6.2.3 Implement audit logging | | All actions |
| [ ] 6.2.4 Add compliance reporting | | GDPR, HIPAA |

---

### 6.3 OpenAPI Documentation
**Impact:** LOW - Developer experience
**Effort:** 2 days

| Task | Status | Notes |
|------|--------|-------|
| [ ] 6.3.1 Add descriptions to all endpoints | | Swagger UI |
| [ ] 6.3.2 Document request/response schemas | | Examples |
| [ ] 6.3.3 Create API usage examples | | Per domain |

---

## Completed Tasks (Stream F Quick Wins)

| Task | Completed By | Date |
|------|-------------|------|
| [x] F1: Password encryption | tab-1 | 2026-01-19 |
| [x] F2: MLWorkbench API client | tab-2 | 2026-01-19 |
| [x] F3: Toast notifications | tab-2 | 2026-01-19 |
| [x] F4: LineageDemo real API | tab-1 | 2026-01-19 |
| [x] F5: Rate limiting | tab-1 | 2026-01-19 |
| [x] F6: Frontend health check | tab-2 | 2026-01-19 |

---

## Effort Estimates Summary

| Tier | Total Effort | Tasks |
|------|--------------|-------|
| Tier 1: Critical | ~10 days | 20 tasks |
| Tier 2: Differentiators | ~15 days | 27 tasks |
| Tier 3: Operational | ~8 days | 18 tasks |
| Tier 4: UX & Polish | ~7 days | 14 tasks |
| Tier 5: Testing | ~11 days | 12 tasks |
| Tier 6: Infrastructure | ~9 days | 10 tasks |
| **Total** | **~60 days** | **101 tasks** |

---

## Recommended Execution Order

### Sprint 1 (Week 1-2): Core Data Flow
1. **1.1 Dataset Upload** - Unblocks data import
2. **1.2 Insights Generation** - Frontend waiting for backend

### Sprint 2 (Week 3-4): Complete Existing Features
3. **1.3 Notification Delivery** - Completes drift/schedules
4. **2.2 Complete Synthetic Data** - Quick win, mostly done

### Sprint 3 (Week 5-6): ML Value
5. **2.3 Model Deployment** - Makes trained models useful
6. **2.4 Enhanced Drift Detection** - Production monitoring

### Sprint 4 (Week 7-8): Polish & Scale
7. **4.1 Split Large Components** - Maintainability
8. **5.1-5.2 Testing** - Stability

### Sprint 5+ (Week 9+): Advanced
9. **2.1 Feature Store** - Advanced capability
10. **6.2 Governance** - Enterprise readiness

---

## How to Use This Checklist

1. **Pick a task** - Start from Tier 1
2. **Update status** - Mark `[ ]` as `[x]` when done
3. **Track in WORK_IN_PROGRESS.md** - Claim task before starting
4. **Commit often** - Small, focused commits

---

*This replaces the old Stream-based organization. Old files (STREAM_A-F) kept for reference.*
