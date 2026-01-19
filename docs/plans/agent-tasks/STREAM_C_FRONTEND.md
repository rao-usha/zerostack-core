# Stream C: Frontend Improvements

**Priority:** HIGH
**Estimated Duration:** 5 weeks
**Dependencies:** Stream B for backend APIs (can mock initially)

---

## Overview

Split large components, standardize error handling, and improve UX across the frontend.

---

## Week 1-2: Component Splitting

### C1.1 Split DataDictionary (LARGEST - 1,745 lines)
**File:** `frontend/src/pages/DataDictionary.tsx`
**Effort:** HIGH
**Deliverable:** 5-7 smaller components

**Target Structure:**
```
frontend/src/pages/DataDictionary/
├── index.tsx                    (~100 lines) - Main page, routing
├── DictionaryHeader.tsx         (~100 lines) - Title, actions
├── DictionarySearchBar.tsx      (~150 lines) - Search, filters
├── DictionaryEntryList.tsx      (~400 lines) - Entry table/cards
├── DictionaryEntryDetail.tsx    (~500 lines) - Single entry view
├── DictionaryApprovalModal.tsx  (~200 lines) - Approval workflow modal
├── DictionaryVersionHistory.tsx (~200 lines) - Version timeline
└── useDictionary.ts             (~100 lines) - Custom hook for state
```

**Key Extractions:**
1. State management → custom hook `useDictionary`
2. Search/filter UI → `DictionarySearchBar`
3. Table/list rendering → `DictionaryEntryList`
4. Entry detail panel → `DictionaryEntryDetail`
5. Modals → separate modal components

### C1.2 Split NotebookPage (912 lines)
**File:** `frontend/src/pages/NotebookPage.tsx`
**Effort:** MEDIUM
**Deliverable:** 3-4 smaller components

**Target Structure:**
```
frontend/src/pages/Notebook/
├── index.tsx              (~150 lines) - Main page
├── NotebookToolbar.tsx    (~150 lines) - Actions, run controls
├── NotebookCell.tsx       (~300 lines) - Single cell component
├── NotebookCellOutput.tsx (~150 lines) - Output rendering
├── NotebookSidebar.tsx    (~100 lines) - Variables, history
└── useNotebook.ts         (~150 lines) - State management
```

### C1.3 Split DataExplorer (915 lines)
**File:** `frontend/src/pages/DataExplorer.tsx`
**Effort:** MEDIUM
**Deliverable:** 3-4 smaller components

**Target Structure:**
```
frontend/src/pages/DataExplorer/
├── index.tsx              (~100 lines) - Main page
├── ExplorerSidebar.tsx    (~200 lines) - Schema tree
├── ExplorerQueryPanel.tsx (~250 lines) - SQL editor
├── ExplorerResults.tsx    (~250 lines) - Result table
├── ExplorerColumnInfo.tsx (~100 lines) - Column details
└── useExplorer.ts         (~100 lines) - State management
```

---

## Week 2-3: Error Handling & UX

### C2.1 Create Toast Service
**Files:** `frontend/src/services/toast.ts` (new), `frontend/src/components/ToastProvider.tsx` (new)
**Effort:** LOW
**Deliverable:** Global toast notification system

**Requirements:**
- `toast.success()`, `toast.error()`, `toast.info()`, `toast.warning()`
- Auto-dismiss with configurable duration
- Stack multiple toasts
- Action buttons in toasts

**Implementation:**
```typescript
// Usage example
import { toast } from '@/services/toast';

toast.success('Entry saved successfully');
toast.error('Failed to load data', { action: { label: 'Retry', onClick: refetch }});
```

### C2.2 Add Error Boundaries
**Files:** `frontend/src/components/ErrorBoundary.tsx` (new)
**Effort:** MEDIUM
**Deliverable:** Graceful error handling UI

**Requirements:**
- Catch React rendering errors
- Display friendly error message
- "Try again" button
- Log errors for debugging

### C2.3 Fix MLWorkbench API Client
**File:** `frontend/src/pages/MLWorkbench.tsx`
**Effort:** LOW
**Deliverable:** Use axios client instead of raw fetch

**Current Problem:**
```typescript
// Currently uses raw fetch
const response = await fetch('/api/ml/...');
```

**Fix:**
```typescript
// Should use the API client
import { api } from '@/api/client';
const response = await api.get('/ml/...');
```

### C2.4 Add Loading Skeletons
**Files:** `frontend/src/components/Skeleton.tsx` (new)
**Effort:** MEDIUM
**Deliverable:** Skeleton loading states

**Requirements:**
- Generic skeleton components (text, card, table row)
- Replace blank loading states
- Shimmer animation
- Match actual content layout

---

## Week 3-4: Feature Integration

### C3.1 Connect LineageDemo to Real API
**Files:** `frontend/src/pages/LineageDemo.tsx`, `frontend/src/pages/LineageFullDemo.tsx`
**Effort:** LOW
**Deliverable:** Real lineage data instead of mocks

**Current Status:** Uses hardcoded mock data

**Requirements:**
- Replace mock data with API calls to `/api/lineage/`
- Handle loading and error states
- Keep demo mode option for offline

### C3.2 Expand SyntheticData Page
**File:** `frontend/src/pages/SyntheticData.tsx` (currently ~200 lines)
**Effort:** MEDIUM
**Deliverable:** Full-featured synthetic data UI

**Add Features:**
- Export generated data (CSV, JSON, Parquet)
- Quality metrics visualization
- Privacy score display
- Generation history
- Comparison view (real vs synthetic)

### C3.3 Add Insights UI
**File:** `frontend/src/pages/Insights.tsx`
**Effort:** MEDIUM
**Deliverable:** Working insights page
**Dependency:** Stream B (B1.1-B1.4 backend)

**Requirements:**
- Insight cards with trend charts
- Anomaly highlighting
- Filter by data source
- Insight detail view
- Regenerate insights action

### C3.4 Add Retry Mechanisms
**Files:** All page components
**Effort:** MEDIUM
**Deliverable:** Retry buttons on API failures

**Requirements:**
- Detect API failures
- Show "Retry" button
- Exponential backoff option
- Maximum retry count

---

## Week 4-5: Polish

### C4.1 Extract Inline Styles
**Files:** Multiple pages with inline styles
**Effort:** HIGH
**Deliverable:** Consistent Tailwind classes

**Pages with Inline Styles:**
- Search for `style={{` across frontend
- Replace with Tailwind utilities
- Create custom utility classes if needed

### C4.2 Add Keyboard Shortcuts
**Files:** `frontend/src/hooks/useKeyboardShortcuts.ts` (new)
**Effort:** MEDIUM
**Deliverable:** Documented keyboard navigation

**Shortcuts to Implement:**
- `Ctrl+K` - Global search
- `Ctrl+S` - Save current item
- `Esc` - Close modals
- Arrow keys - Navigate lists
- `?` - Show shortcuts help

### C4.3 Accessibility Improvements
**Files:** Multiple components
**Effort:** MEDIUM
**Deliverable:** Screen reader support

**Requirements:**
- Add ARIA labels to interactive elements
- Ensure keyboard navigability
- Color contrast compliance
- Focus indicators

---

## Exit Criteria

- [ ] No component > 500 lines
- [ ] All API calls use axios client
- [ ] Toast notifications working
- [ ] Error boundaries in place
- [ ] Loading skeletons everywhere
- [ ] LineageDemo uses real API
- [ ] Keyboard shortcuts documented

---

## Component Size Targets

| Before | After | Target |
|--------|-------|--------|
| DataDictionary.tsx (1,745) | 5-7 files | <300 each |
| NotebookPage.tsx (912) | 4-5 files | <300 each |
| DataExplorer.tsx (915) | 4-5 files | <300 each |

---

## Testing Requirements

- Test component splitting doesn't break functionality
- Test toast notifications appear correctly
- Test error boundaries catch errors
- Test keyboard shortcuts work

---

## Related Files Reference

**API Client (use this):**
- `frontend/src/api/client.ts`

**Existing Components (patterns):**
- `frontend/src/components/Layout.tsx`
- `frontend/src/pages/Dashboard.tsx`

**Pages to Update:**
- `frontend/src/pages/DataDictionary.tsx`
- `frontend/src/pages/NotebookPage.tsx`
- `frontend/src/pages/DataExplorer.tsx`
- `frontend/src/pages/MLWorkbench.tsx`
- `frontend/src/pages/LineageDemo.tsx`
- `frontend/src/pages/SyntheticData.tsx`
