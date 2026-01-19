# Nex Platform - Parallel Execution Plan

**Based on:** CODEBASE_IMPROVEMENT_PLAN.md
**Goal:** Maximize parallel execution to accelerate development
**Timeline:** 4-6 weeks with parallel streams

---

## Workstream Overview

```
Week 1-2          Week 2-3          Week 3-4          Week 4-5          Week 5-6
────────────────────────────────────────────────────────────────────────────────
STREAM A: Security ═══════════════════════════════►
STREAM B: Backend Features ═══════════════════════════════════════════►
STREAM C: Frontend ═══════════════════════════════════════════════════►
STREAM D: Testing ════════════════════════════════════════════════════►
STREAM E: Operations ═══════════════════════════════►
STREAM F: Quick Wins ════►
```

---

## Stream A: Security & Auth (CRITICAL PATH)

**Owner:** Backend Developer 1
**Priority:** CRITICAL - Blocks production deployment
**Dependencies:** None (can start immediately)

### Week 1
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| A1.1 Implement JWT authentication | `backend/domains/auth/` | HIGH | Working login/register |
| A1.2 Add password encryption | `backend/domains/data_connections/router.py:245` | LOW | Fernet encryption |
| A1.3 Create auth middleware | `backend/core/` | MEDIUM | Dependency injection |

### Week 2
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| A2.1 Implement RBAC | `backend/domains/auth/` | MEDIUM | Role definitions |
| A2.2 Add OAuth2 providers | `backend/domains/auth/` | MEDIUM | Google/GitHub login |
| A2.3 API key management | `backend/domains/auth/` | LOW | Token CRUD |

### Week 3
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| A3.1 Apply auth to all routers | All domain routers | MEDIUM | Protected endpoints |
| A3.2 Add rate limiting | `backend/core/` | MEDIUM | FastAPI middleware |
| A3.3 Session management | `backend/domains/auth/` | LOW | Session store |

**Exit Criteria:**
- [ ] All endpoints require authentication
- [ ] Passwords encrypted at rest
- [ ] RBAC functional (admin/editor/viewer)
- [ ] Rate limiting active

---

## Stream B: Backend Feature Completion

**Owner:** Backend Developer 2
**Priority:** HIGH
**Dependencies:** None (parallel with Stream A)

### Week 1-2: Insights Backend
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| B1.1 Implement insight generation | `backend/domains/insights/router.py` | MEDIUM | LLM-based insights |
| B1.2 Add trend detection | `backend/domains/insights/service.py` | MEDIUM | Trend algorithms |
| B1.3 Implement anomaly detection | `backend/domains/insights/service.py` | MEDIUM | Anomaly flags |
| B1.4 Add insight scheduling | `backend/domains/insights/` | LOW | Cron triggers |

### Week 2-3: Dataset Upload
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| B2.1 Implement file upload | `backend/domains/datasets/router.py` | MEDIUM | Stream to MinIO |
| B2.2 Add schema inference | `backend/domains/datasets/service.py` | MEDIUM | Auto-detect types |
| B2.3 Dataset versioning | `backend/domains/datasets/` | LOW | Version tracking |
| B2.4 Data quality profiling | `backend/domains/datasets/` | MEDIUM | Quality scores |

### Week 3-4: Jobs Queue
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| B3.1 Implement job queue | `backend/domains/jobs/router.py` | MEDIUM | Redis-backed queue |
| B3.2 Add job prioritization | `backend/domains/jobs/service.py` | LOW | Priority levels |
| B3.3 Job cancellation | `backend/domains/jobs/` | LOW | Cancel endpoint |
| B3.4 Job monitoring | `backend/domains/jobs/` | MEDIUM | Status dashboard |

### Week 4-5: Governance
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| B4.1 Implement access policies | `backend/domains/governance/router.py` | HIGH | Policy engine |
| B4.2 Approval workflows | `backend/domains/governance/` | MEDIUM | Approval states |
| B4.3 Audit logging | `backend/domains/governance/` | MEDIUM | Audit trail |
| B4.4 Compliance reporting | `backend/domains/governance/` | LOW | GDPR/HIPAA |

**Exit Criteria:**
- [ ] Insights generating from data
- [ ] Dataset upload working with versioning
- [ ] Background jobs processing
- [ ] Governance policies enforceable

---

## Stream C: Frontend Improvements

**Owner:** Frontend Developer
**Priority:** HIGH
**Dependencies:** Stream B for backend APIs

### Week 1-2: Component Splitting
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| C1.1 Split DataDictionary | `frontend/src/pages/DataDictionary.tsx` (1,745 lines) | HIGH | 4-5 components |
| C1.2 Split NotebookPage | `frontend/src/pages/NotebookPage.tsx` (912 lines) | MEDIUM | 3-4 components |
| C1.3 Split DataExplorer | `frontend/src/pages/DataExplorer.tsx` (915 lines) | MEDIUM | 3-4 components |

**Component Breakdown for DataDictionary:**
```
DataDictionary.tsx (1,745 lines) →
├── DictionaryHeader.tsx (~100 lines)
├── DictionarySearchBar.tsx (~150 lines)
├── DictionaryEntryList.tsx (~400 lines)
├── DictionaryEntryDetail.tsx (~500 lines)
├── DictionaryApprovalModal.tsx (~200 lines)
├── DictionaryVersionHistory.tsx (~200 lines)
└── DictionaryContext.tsx (~100 lines) [state management]
```

### Week 2-3: Error Handling & UX
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| C2.1 Create Toast service | `frontend/src/services/toast.ts` | LOW | Global toast |
| C2.2 Add error boundaries | `frontend/src/components/` | MEDIUM | Error UI |
| C2.3 Fix MLWorkbench API client | `frontend/src/pages/MLWorkbench.tsx` | LOW | Use axios client |
| C2.4 Add loading skeletons | `frontend/src/components/` | MEDIUM | Skeleton components |

### Week 3-4: Feature Integration
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| C3.1 Connect LineageDemo to API | `frontend/src/pages/LineageDemo.tsx` | LOW | Real data |
| C3.2 Expand SyntheticData page | `frontend/src/pages/SyntheticData.tsx` | MEDIUM | Export, stats |
| C3.3 Add Insights UI (after B1) | `frontend/src/pages/Insights.tsx` | MEDIUM | Working insights |
| C3.4 Add retry mechanisms | All pages | MEDIUM | Retry buttons |

### Week 4-5: Polish
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| C4.1 Extract inline styles | Multiple pages | HIGH | Tailwind classes |
| C4.2 Add keyboard shortcuts | `frontend/src/hooks/` | MEDIUM | Shortcut docs |
| C4.3 Accessibility (ARIA) | Multiple components | MEDIUM | Screen reader support |

**Exit Criteria:**
- [ ] No component > 500 lines
- [ ] Consistent error handling
- [ ] All pages use API client
- [ ] Loading states everywhere

---

## Stream D: Testing

**Owner:** QA Engineer / Backend Developer 3
**Priority:** HIGH
**Dependencies:** Streams A, B for testable features

### Week 1-2: Critical Tests (Parallel with development)
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| D1.1 Notebook execution tests | `backend/tests/test_notebooks.py` | MEDIUM | Cell execution |
| D1.2 Synthetic data tests | `backend/tests/test_synthetic.py` | MEDIUM | Generation tests |
| D1.3 Auth tests (after A1) | `backend/tests/test_auth.py` | MEDIUM | Login/RBAC tests |

### Week 2-3: Integration Tests
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| D2.1 Data connection tests | `backend/tests/test_data_connections.py` | MEDIUM | Connection tests |
| D2.2 GPU adapter tests (mocked) | `backend/tests/test_gpu_adapter.py` | MEDIUM | Mocked RunPod |
| D2.3 Lineage parsing tests | `backend/tests/test_lineage.py` | MEDIUM | SQL parsing |

### Week 3-4: Domain Tests
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| D3.1 Drift detection tests | `backend/tests/test_drift.py` | LOW | Alert tests |
| D3.2 ML development tests | `backend/tests/test_ml_development.py` | MEDIUM | State machine |
| D3.3 Scheduling tests | `backend/tests/test_scheduling.py` | LOW | Cron tests |

### Week 4-5: E2E & Coverage
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| D4.1 E2E tests (Playwright) | `tests/e2e/` | HIGH | Critical paths |
| D4.2 Coverage report | `pytest.ini` | LOW | 70%+ target |
| D4.3 Performance benchmarks | `backend/tests/benchmarks/` | MEDIUM | Baseline metrics |

**Exit Criteria:**
- [ ] All new features have tests
- [ ] Overall coverage > 70%
- [ ] E2E tests for critical paths
- [ ] CI pipeline green

---

## Stream E: Operations & Infrastructure

**Owner:** DevOps / Backend Developer
**Priority:** MEDIUM
**Dependencies:** None

### Week 1-2: Notifications
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| E1.1 Email notification delivery | `backend/services/notifications.py` | MEDIUM | SMTP integration |
| E1.2 Slack notification delivery | `backend/services/notifications.py` | LOW | Webhook |
| E1.3 Webhook notifications | `backend/services/notifications.py` | LOW | Custom webhooks |
| E1.4 Wire to scheduler | `backend/services/scheduler.py:281-287` | LOW | Trigger on events |

### Week 2-3: Partial Feature Completion
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| E2.1 Synthetic data loading | `backend/domains/synthetic/router.py:181,192` | LOW | Load from storage |
| E2.2 Drift statistical tests | `backend/services/drift_detector.py` | MEDIUM | KS-test, Chi-sq |
| E2.3 Evaluation pack metrics | `backend/domains/evaluation_packs/` | MEDIUM | Standard metrics |

### Week 3: Documentation
| Task | Files | Effort | Deliverable |
|------|-------|--------|-------------|
| E3.1 OpenAPI documentation | FastAPI auto-gen | MEDIUM | Swagger UI |
| E3.2 API usage examples | `docs/api/` | LOW | Code samples |

**Exit Criteria:**
- [ ] Notifications working (email, Slack)
- [ ] Drift detection statistical tests
- [ ] OpenAPI docs generated

---

## Stream F: Quick Wins (Day 1-3)

**Owner:** Any available developer
**Priority:** LOW effort, HIGH impact
**Dependencies:** None

| Task | Effort | Owner | Deliverable |
|------|--------|-------|-------------|
| F1 Add password encryption | 2 hrs | Any | Fernet in data_connections |
| F2 Fix MLWorkbench API client | 1 hr | Frontend | Use axios |
| F3 Wire up Toast notifications | 2 hrs | Frontend | Consistent toasts |
| F4 Connect LineageDemo to API | 2 hrs | Frontend | Real lineage data |
| F5 Add basic rate limiting | 2 hrs | Backend | SlowAPI middleware |
| F6 Add frontend health check | 1 hr | Frontend | Backend ping |

**All Quick Wins can be done in parallel on Day 1-2**

---

## Dependency Graph

```
                    ┌─────────────┐
                    │ Quick Wins  │ (Day 1-3)
                    │  Stream F   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Security    │  │   Backend     │  │   Frontend    │
│   Stream A    │  │   Stream B    │  │   Stream C    │
│  (Critical)   │  │  (Features)   │  │    (UI)       │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │                  │    ┌─────────────┘
        │                  │    │ (waits for APIs)
        │                  ▼    ▼
        │          ┌───────────────┐
        │          │   Testing     │
        │          │   Stream D    │
        │          └───────────────┘
        │                  │
        ▼                  ▼
┌─────────────────────────────────────────────┐
│              Production Ready               │
└─────────────────────────────────────────────┘

Stream E (Operations) runs independently throughout
```

---

## Team Allocation (Suggested)

| Stream | Role | Commitment |
|--------|------|------------|
| Stream A | Backend Dev 1 | 100% for 3 weeks |
| Stream B | Backend Dev 2 | 100% for 5 weeks |
| Stream C | Frontend Dev | 100% for 5 weeks |
| Stream D | QA / Backend Dev 3 | 100% for 5 weeks |
| Stream E | DevOps / Part-time | 50% for 3 weeks |
| Stream F | Anyone | Day 1-3 sprint |

**Minimum Team:** 3 developers (combine streams)
**Optimal Team:** 5 developers (full parallelism)

---

## Weekly Milestones

### Week 1 Checkpoint
- [ ] Quick wins complete (F1-F6)
- [ ] JWT auth working (A1.1)
- [ ] Password encryption added (A1.2)
- [ ] DataDictionary split started (C1.1)
- [ ] Notebook tests written (D1.1)

### Week 2 Checkpoint
- [ ] RBAC implemented (A2.1)
- [ ] Insights backend started (B1.1-B1.2)
- [ ] Component splitting complete (C1.1-C1.3)
- [ ] Notifications working (E1.1-E1.3)
- [ ] Synthetic tests complete (D1.2)

### Week 3 Checkpoint
- [ ] Auth applied to all routers (A3.1)
- [ ] Dataset upload working (B2.1-B2.3)
- [ ] Error handling standardized (C2.1-C2.3)
- [ ] Integration tests complete (D2.1-D2.3)

### Week 4 Checkpoint
- [ ] Jobs queue implemented (B3.1-B3.4)
- [ ] Frontend features integrated (C3.1-C3.4)
- [ ] Domain tests complete (D3.1-D3.3)
- [ ] OpenAPI docs generated (E3.1)

### Week 5 Checkpoint
- [ ] Governance implemented (B4.1-B4.4)
- [ ] Frontend polished (C4.1-C4.3)
- [ ] E2E tests passing (D4.1)
- [ ] 70%+ test coverage (D4.2)

### Week 6: Integration & Release
- [ ] All streams merged
- [ ] Full regression testing
- [ ] Performance validation
- [ ] Production deployment ready

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Auth delays block production | Start Stream A first, no dependencies |
| Backend APIs delay frontend | Frontend can mock APIs initially |
| Testing bottleneck | Start tests as features complete |
| Single point of failure | Document everything, no silos |

---

## Communication Plan

- **Daily standup:** 15 min, stream leads
- **Weekly sync:** 1 hr, all streams
- **Blockers:** Slack immediately
- **PR reviews:** Same-day turnaround

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Features complete | 100% of stubs implemented |
| Test coverage | 70%+ |
| Component size | No file > 500 lines |
| Security | All endpoints protected |
| Performance | <500ms API response |

---

## Getting Started

1. **Day 1:** Assign stream owners, start Quick Wins (Stream F)
2. **Day 2:** Kick off all parallel streams
3. **Day 3:** First PR reviews, establish velocity
4. **Week 1 end:** Checkpoint meeting, adjust plan

Start with: `Stream F Quick Wins` + `Stream A Security` + `Stream C Frontend Splitting`
