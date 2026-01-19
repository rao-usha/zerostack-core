# Stream A: Security & Auth (CRITICAL PATH)

**Priority:** CRITICAL - Blocks production deployment
**Estimated Duration:** 3 weeks
**Dependencies:** None (can start immediately)

---

## Overview

Implement authentication, authorization, and security features. This is the critical path - production deployment is blocked until complete.

---

## Week 1 Tasks

### A1.1 Implement JWT Authentication
**Files:** `backend/domains/auth/router.py`, `backend/domains/auth/service.py`
**Effort:** HIGH
**Deliverable:** Working login/register endpoints

**Requirements:**
- User registration with email/password
- Login endpoint returning JWT tokens
- Token refresh mechanism
- Password hashing with bcrypt
- Token validation middleware

**Implementation Notes:**
- Current `backend/domains/auth/router.py` returns 501 for all endpoints
- Use `python-jose` for JWT handling
- Store users in PostgreSQL with SQLAlchemy model

### A1.2 Add Password Encryption for Data Connections
**Files:** `backend/domains/data_connections/router.py:245`
**Effort:** LOW
**Deliverable:** Fernet encryption for stored credentials

**Requirements:**
- Generate encryption key (store in env vars)
- Encrypt passwords before database storage
- Decrypt when establishing connections
- Migrate existing plaintext passwords

**Current Code (Line 245):**
```python
# TODO: encrypt password before storing
```

### A1.3 Create Auth Middleware
**Files:** `backend/core/auth.py` (new), `backend/core/dependencies.py`
**Effort:** MEDIUM
**Deliverable:** FastAPI dependency injection for auth

**Requirements:**
- `get_current_user` dependency
- `require_auth` decorator
- Token extraction from headers
- User context in request state

---

## Week 2 Tasks

### A2.1 Implement Role-Based Access Control (RBAC)
**Files:** `backend/domains/auth/models.py`, `backend/db/models.py`
**Effort:** MEDIUM
**Deliverable:** Role definitions and permission checks

**Roles:**
- `admin` - Full access
- `editor` - Create/edit resources
- `viewer` - Read-only access

**Requirements:**
- Role model with permissions
- User-role association
- Permission checking middleware
- Role assignment endpoints

### A2.2 Add OAuth2 Providers
**Files:** `backend/domains/auth/oauth.py` (new)
**Effort:** MEDIUM
**Deliverable:** Google and GitHub login

**Requirements:**
- OAuth2 flow implementation
- Callback handling
- Account linking (OAuth to existing user)
- New user creation from OAuth

### A2.3 API Key Management
**Files:** `backend/domains/auth/api_keys.py` (new)
**Effort:** LOW
**Deliverable:** Token CRUD for programmatic access

**Requirements:**
- Generate API keys per user
- Key listing and revocation
- Key-based authentication (alternative to JWT)
- Rate limiting per key

---

## Week 3 Tasks

### A3.1 Apply Auth to All Routers
**Files:** All files in `backend/domains/*/router.py`
**Effort:** MEDIUM
**Deliverable:** Protected endpoints across platform

**Approach:**
- Add `Depends(get_current_user)` to all routers
- Some endpoints may need role checks
- Document which endpoints need which roles

**Domains to Update:**
- [ ] chat
- [ ] data_explorer
- [ ] data_connections
- [ ] datasets
- [ ] distillation
- [ ] drift
- [ ] evaluation_packs
- [ ] files
- [ ] governance
- [ ] insights
- [ ] jobs
- [ ] lineage
- [ ] ml_development
- [ ] notebooks
- [ ] schedules
- [ ] synthetic

### A3.2 Add Rate Limiting
**Files:** `backend/core/rate_limit.py` (new), `backend/main.py`
**Effort:** MEDIUM
**Deliverable:** FastAPI middleware for rate limiting

**Requirements:**
- Use `slowapi` library
- Rate limits per user/IP
- Different limits for different endpoints
- 429 response on limit exceeded

### A3.3 Session Management
**Files:** `backend/domains/auth/sessions.py` (new)
**Effort:** LOW
**Deliverable:** Session tracking and invalidation

**Requirements:**
- Track active sessions per user
- Session listing endpoint
- Session revocation (logout everywhere)
- Session timeout configuration

---

## Exit Criteria

- [ ] All endpoints require authentication
- [ ] Passwords encrypted at rest
- [ ] RBAC functional (admin/editor/viewer)
- [ ] OAuth2 working (Google, GitHub)
- [ ] API keys can be generated
- [ ] Rate limiting active
- [ ] Sessions can be managed

---

## Testing Requirements

Create tests in `backend/tests/test_auth.py`:
- [ ] Registration flow
- [ ] Login/logout flow
- [ ] JWT token validation
- [ ] RBAC permission checks
- [ ] OAuth2 callback handling
- [ ] API key authentication
- [ ] Rate limit enforcement

---

## Related Files Reference

**Existing (to modify):**
- `backend/domains/auth/router.py` - Currently stubbed
- `backend/domains/data_connections/router.py:245` - Password TODO
- `backend/main.py` - Add middleware

**To Create:**
- `backend/core/auth.py` - Auth utilities
- `backend/domains/auth/service.py` - Auth business logic
- `backend/domains/auth/models.py` - User, Role, Session models
- `backend/domains/auth/oauth.py` - OAuth2 providers
- `backend/domains/auth/api_keys.py` - API key management
