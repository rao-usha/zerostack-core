# Stream F: Quick Wins (Day 1-3)

**Priority:** LOW effort, HIGH impact
**Estimated Duration:** 1-3 days
**Dependencies:** None (can start immediately)

---

## Overview

These are small, self-contained tasks that can be completed in 1-2 hours each. Perfect for warming up or parallel execution.

---

## F1: Add Password Encryption for Data Connections

**File:** `backend/domains/data_connections/router.py:245`
**Effort:** 2 hours
**Impact:** CRITICAL security fix

**Current Code (Line 245):**
```python
# TODO: encrypt password before storing
```

**Implementation:**
```python
# backend/core/encryption.py (new file)
from cryptography.fernet import Fernet
import os

def get_encryption_key() -> bytes:
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        raise ValueError("ENCRYPTION_KEY environment variable not set")
    return key.encode()

def encrypt_password(password: str) -> str:
    f = Fernet(get_encryption_key())
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted.encode()).decode()

# Generate key (run once, save to env):
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Update data_connections/router.py:**
```python
from backend.core.encryption import encrypt_password, decrypt_password

# When saving connection:
connection.password = encrypt_password(request.password)

# When using connection:
actual_password = decrypt_password(connection.password)
```

**Add to .env.example:**
```bash
ENCRYPTION_KEY=your-fernet-key-here
```

---

## F2: Fix MLWorkbench to Use API Client

**File:** `frontend/src/pages/MLWorkbench.tsx`
**Effort:** 1 hour
**Impact:** Consistent error handling

**Current Pattern (WRONG):**
```typescript
const response = await fetch('/api/ml/recipes');
const data = await response.json();
```

**Correct Pattern:**
```typescript
import { api } from '@/api/client';

const { data } = await api.get('/ml/recipes');
```

**Search and Replace:**
1. Find all `fetch('/api/` in MLWorkbench.tsx
2. Replace with api client calls
3. Update error handling to use client's error handling

---

## F3: Wire Up Toast Notifications

**Files:** Multiple frontend pages
**Effort:** 2 hours
**Impact:** Better user feedback

**Step 1: Check if toast service exists**
Look in `frontend/src/` for existing toast implementation

**Step 2: If not exists, create simple toast:**
```typescript
// frontend/src/services/toast.ts
import { toast as sonnerToast } from 'sonner'; // or react-hot-toast

export const toast = {
  success: (message: string) => sonnerToast.success(message),
  error: (message: string) => sonnerToast.error(message),
  info: (message: string) => sonnerToast.info(message),
  warning: (message: string) => sonnerToast.warning(message),
};
```

**Step 3: Add ToastProvider to App.tsx:**
```typescript
import { Toaster } from 'sonner';

function App() {
  return (
    <>
      <Toaster position="top-right" />
      {/* rest of app */}
    </>
  );
}
```

**Step 4: Replace console.log with toasts:**
```typescript
// Before
console.log('Saved successfully');

// After
toast.success('Saved successfully');
```

---

## F4: Connect LineageDemo to Real API

**Files:** `frontend/src/pages/LineageDemo.tsx`, `frontend/src/pages/LineageFullDemo.tsx`
**Effort:** 2 hours
**Impact:** Demo pages show real data

**Current Code (mock data):**
```typescript
const mockNodes = [
  { id: '1', type: 'table', name: 'users' },
  // ... hardcoded data
];
```

**Updated Code:**
```typescript
import { api } from '@/api/client';
import { useEffect, useState } from 'react';

function LineageDemo() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(true);
  const [useMock, setUseMock] = useState(false);

  useEffect(() => {
    async function fetchLineage() {
      try {
        const { data } = await api.get('/lineage/graph');
        setNodes(data.nodes);
        setEdges(data.edges);
      } catch (error) {
        console.error('Failed to fetch lineage, using mock data');
        setUseMock(true);
        setNodes(mockNodes);
        setEdges(mockEdges);
      } finally {
        setLoading(false);
      }
    }
    fetchLineage();
  }, []);

  // Add toggle button for demo mode
  return (
    <div>
      <button onClick={() => setUseMock(!useMock)}>
        {useMock ? 'Use Real Data' : 'Use Demo Data'}
      </button>
      {/* render lineage graph */}
    </div>
  );
}
```

---

## F5: Add Basic Rate Limiting

**Files:** `backend/main.py`, `backend/core/rate_limit.py` (new)
**Effort:** 2 hours
**Impact:** API abuse prevention

**Step 1: Install slowapi:**
```bash
pip install slowapi
```

**Step 2: Create rate limit config:**
```python
# backend/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Rate limit decorators
def rate_limit(limit: str = "100/minute"):
    return limiter.limit(limit)
```

**Step 3: Add to main.py:**
```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.core.rate_limit import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Step 4: Apply to expensive endpoints:**
```python
from backend.core.rate_limit import limiter

@router.post("/chat/completions")
@limiter.limit("20/minute")
async def chat_completion(request: Request, ...):
    ...

@router.post("/synthetic/generate")
@limiter.limit("5/minute")
async def generate_synthetic(request: Request, ...):
    ...
```

---

## F6: Add Frontend Health Check

**Files:** `frontend/src/api/health.ts` (new), `frontend/src/App.tsx`
**Effort:** 1 hour
**Impact:** User knows when backend is down

**Step 1: Create health check utility:**
```typescript
// frontend/src/api/health.ts
import { api } from './client';

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const { data } = await api.get('/health');
    return data.status === 'ok';
  } catch {
    return false;
  }
}
```

**Step 2: Add health indicator to Layout:**
```typescript
// frontend/src/components/Layout.tsx
import { useEffect, useState } from 'react';
import { checkBackendHealth } from '@/api/health';

function HealthIndicator() {
  const [healthy, setHealthy] = useState(true);

  useEffect(() => {
    const check = async () => {
      const isHealthy = await checkBackendHealth();
      setHealthy(isHealthy);
    };

    check();
    const interval = setInterval(check, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  if (healthy) return null;

  return (
    <div className="bg-red-500 text-white text-center py-2">
      Backend connection lost. Some features may not work.
    </div>
  );
}
```

---

## Execution Order (Recommended)

All tasks can be done in parallel, but if sequential:

1. **F1** (Password Encryption) - Security critical
2. **F5** (Rate Limiting) - Security related
3. **F2** (MLWorkbench API Client) - Code quality
4. **F3** (Toast Notifications) - UX improvement
5. **F6** (Health Check) - UX improvement
6. **F4** (LineageDemo) - Feature enhancement

---

## Checklist

- [ ] F1: Password encryption added and tested
- [ ] F2: MLWorkbench uses API client
- [ ] F3: Toast notifications working
- [ ] F4: LineageDemo fetches real data
- [ ] F5: Rate limiting active on expensive endpoints
- [ ] F6: Health indicator shows backend status

---

## Notes

- Each task is independent and can be assigned to different developers
- All tasks have clear deliverables and can be verified immediately
- Total time: ~10 hours if done sequentially, ~2-3 hours if parallelized
- These fixes improve security, UX, and code quality with minimal risk
