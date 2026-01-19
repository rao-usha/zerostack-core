# Work In Progress Tracker

**Purpose:** Coordinate parallel agent work. Check before starting, update when done.
**Master Checklist:** See [MASTER_CHECKLIST.md](agent-tasks/MASTER_CHECKLIST.md) for full task list by priority.

**Rules:**
1. Before starting a task, check if it's already claimed
2. Add your agent ID and start time when you begin
3. Mark complete with end time when done
4. If a task is stale (>24h with no update), it can be reclaimed

---

## Active Work

### Tier 1: Critical Features (Highest Priority)

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| 1.1: Dataset Upload | 🟡 AVAILABLE | - | - | - | CRITICAL - users can't import data |
| 1.2: Insights Generation | 🟡 AVAILABLE | - | - | - | Frontend exists, backend stubbed |
| 1.3: Notification Delivery | 🟡 AVAILABLE | - | - | - | Completes drift/schedules |

### Tier 2: High-Value Differentiators

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| 2.1: Feature Store | 🟡 AVAILABLE | - | - | - | Prevents duplicate work |
| 2.2: Complete Synthetic Data | 🟡 AVAILABLE | - | - | - | Just needs data loading |
| 2.3: Model Deployment | 🟡 AVAILABLE | - | - | - | Makes models useful |
| 2.4: Enhanced Drift Detection | 🟡 AVAILABLE | - | - | - | Statistical tests |

### Tier 3: Operational Value

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| 3.1: Query History/Saved Queries | 🟡 AVAILABLE | - | - | - | QoL improvement |
| 3.2: Notebook Templates | 🟡 AVAILABLE | - | - | - | Speed up workflows |
| 3.3: Background Jobs Queue | 🟡 AVAILABLE | - | - | - | Long-running tasks |

### Tier 4: UX & Polish

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| 4.1: Split Large Components | 🟡 AVAILABLE | - | - | - | DataDictionary, Notebook, Explorer |
| 4.2: Error Handling (remaining) | 🟡 AVAILABLE | - | - | - | Boundaries, skeletons |
| 4.3: Keyboard Shortcuts | 🟡 AVAILABLE | - | - | - | Power user features |

### Tier 5: Testing

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| 5.1: Critical Feature Tests | 🟡 AVAILABLE | - | - | - | Notebooks, Synthetic |
| 5.2: Integration Tests | 🟡 AVAILABLE | - | - | - | GPU, Lineage, Connections |
| 5.3: E2E Tests | 🟡 AVAILABLE | - | - | - | Playwright setup |

---

## Completed (Stream F Quick Wins)

| Task | Status | Agent | Started | Completed | Notes |
|------|--------|-------|---------|-----------|-------|
| F1: Password encryption | ✅ COMPLETE | tab-1 | 2026-01-19 | 2026-01-19 | Fernet in core/encryption.py |
| F2: MLWorkbench API client | ✅ COMPLETE | tab-2 | 2026-01-19 | 2026-01-19 | Uses axios client |
| F3: Toast notifications | ✅ COMPLETE | tab-2 | 2026-01-19 | 2026-01-19 | ToastContext + useToast |
| F4: LineageDemo real API | ✅ COMPLETE | tab-1 | 2026-01-19 | 2026-01-19 | Demo/Live toggle |
| F5: Rate limiting | ✅ COMPLETE | tab-1 | 2026-01-19 | 2026-01-19 | slowapi in core/rate_limit.py |
| F6: Frontend health check | ✅ COMPLETE | tab-2 | 2026-01-19 | 2026-01-19 | HealthIndicator in Layout |

---

## Status Legend

- 🟡 AVAILABLE - Ready to start
- 🔵 IN PROGRESS - Being worked on
- ✅ COMPLETE - Done
- ⛔ BLOCKED - Waiting on dependency
- 🔴 FAILED - Needs investigation

---

## How to Update

**Claiming a task:**
```
| 1.1: Dataset Upload | 🔵 IN PROGRESS | tab-1 | 2026-01-19 | - | Working on upload endpoint |
```

**Completing a task:**
```
| 1.1: Dataset Upload | ✅ COMPLETE | tab-1 | 2026-01-19 | 2026-01-19 | MinIO integration done |
```

---

## Recommended Next Actions

**For Backend Focus:**
1. **1.1 Dataset Upload** - Highest impact, enables data import
2. **1.2 Insights Generation** - Frontend is waiting
3. **1.3 Notification Delivery** - Quick to wire up

**For Frontend Focus:**
1. **4.1 Split Large Components** - Improves maintainability
2. **Insights UI** - After backend is done
3. **Synthetic Data UI enhancements** - Export, comparison

**For Full-Stack:**
1. **1.1 Dataset Upload** - Backend + frontend together
2. **2.2 Complete Synthetic Data** - Small gaps to fill
