# Stream D: Testing

**Priority:** HIGH
**Estimated Duration:** 5 weeks
**Dependencies:** Streams A, B for testable features

---

## Overview

Add comprehensive test coverage for new and existing features. Target: 70%+ coverage.

---

## Current Coverage Status

**Well Tested (80%+):**
| Area | Files | Notes |
|------|-------|-------|
| Files Domain | 5 test files | test_files_*.py |
| Files Encryption | test_files_encryption.py | 100% |
| Dictionary Semantics | test_dictionary_semantics.py | 80% |
| Health Check | test_health.py | 100% |

**Needs Testing:**
| Area | Priority | Current Coverage |
|------|----------|------------------|
| Notebooks | CRITICAL | 0% |
| Synthetic Data | CRITICAL | 0% |
| GPU Runner | HIGH | 0% |
| Data Connections | HIGH | ~20% |
| Auth (after Stream A) | HIGH | 0% |
| Drift Detection | MEDIUM | ~10% |
| Lineage | MEDIUM | ~20% |
| ML Development | MEDIUM | ~30% |
| Scheduling | LOW | ~40% |

---

## Week 1-2: Critical Tests

### D1.1 Notebook Execution Tests
**File:** `backend/tests/test_notebooks.py` (new)
**Effort:** MEDIUM
**Deliverable:** Cell execution tests

**Test Cases:**
```python
# Test SQL cell execution
def test_execute_sql_cell():
    # Create notebook, add SQL cell, execute, verify results

# Test Python cell execution
def test_execute_python_cell():
    # Create notebook, add Python cell, execute, verify output

# Test cell ordering
def test_cell_reorder():
    # Create cells, reorder, verify positions

# Test session variables
def test_session_variables():
    # Set variable in one cell, use in another

# Test error handling
def test_cell_execution_error():
    # Execute invalid SQL/Python, verify error response

# Test export
def test_notebook_export_parquet():
    # Execute query, export to Parquet, verify file
```

### D1.2 Synthetic Data Tests
**File:** `backend/tests/test_synthetic.py` (new)
**Effort:** MEDIUM
**Deliverable:** Generation and quality tests

**Test Cases:**
```python
# Test basic generation
def test_generate_synthetic_data():
    # Create config, generate, verify output shape

# Test privacy levels
def test_privacy_level_high():
    # Generate with high privacy, verify PII handling

# Test SDV model types
def test_ctgan_generation():
    # Test CTGAN model
def test_gaussian_copula_generation():
    # Test GaussianCopula model

# Test quality metrics
def test_quality_evaluation():
    # Generate data, run quality check, verify KS-test

# Test PII detection
def test_pii_detection():
    # Input data with PII, verify detection
```

### D1.3 Auth Tests (after Stream A)
**File:** `backend/tests/test_auth.py` (new)
**Effort:** MEDIUM
**Deliverable:** Authentication flow tests
**Dependency:** Stream A completion

**Test Cases:**
```python
# Registration
def test_user_registration():
def test_registration_duplicate_email():
def test_registration_weak_password():

# Login
def test_login_success():
def test_login_invalid_credentials():
def test_login_returns_jwt():

# Token validation
def test_jwt_validation():
def test_expired_token():
def test_invalid_token():

# RBAC
def test_admin_access():
def test_editor_access():
def test_viewer_access():
def test_unauthorized_access():

# OAuth
def test_oauth_google_callback():
def test_oauth_github_callback():

# API Keys
def test_api_key_authentication():
def test_api_key_revocation():
```

---

## Week 2-3: Integration Tests

### D2.1 Data Connection Tests
**File:** `backend/tests/test_data_connections.py` (new/expand)
**Effort:** MEDIUM
**Deliverable:** Connection lifecycle tests

**Test Cases:**
```python
# Connection CRUD
def test_create_connection():
def test_update_connection():
def test_delete_connection():
def test_list_connections():

# Connection testing
def test_test_connection_success():
def test_test_connection_failure():

# Password encryption (after Stream A)
def test_password_encrypted_at_rest():
def test_password_decrypted_for_use():

# Schema scanning
def test_scan_tables():
def test_scan_columns():
```

### D2.2 GPU Adapter Tests (Mocked)
**File:** `backend/tests/test_gpu_adapter.py` (new)
**Effort:** MEDIUM
**Deliverable:** Mocked RunPod integration tests

**Test Cases:**
```python
# Mock RunPod API responses
@pytest.fixture
def mock_runpod():
    # Setup mocked RunPod responses

# Test GPU listing
def test_list_available_gpus(mock_runpod):

# Test job submission
def test_submit_job(mock_runpod):
def test_job_status(mock_runpod):
def test_job_cancellation(mock_runpod):

# Test SSH execution
def test_ssh_job_execution(mock_runpod):

# Test error handling
def test_gpu_unavailable(mock_runpod):
def test_job_timeout(mock_runpod):
```

### D2.3 Lineage Parsing Tests
**File:** `backend/tests/test_lineage.py` (new)
**Effort:** MEDIUM
**Deliverable:** SQL parsing and lineage extraction tests

**Test Cases:**
```python
# SQL parsing
def test_parse_simple_select():
def test_parse_join_query():
def test_parse_subquery():
def test_parse_cte():
def test_parse_aggregation():

# Lineage extraction
def test_extract_table_lineage():
def test_extract_column_lineage():
def test_detect_edge_type():

# ML query detection
def test_detect_ml_query():

# Graph operations
def test_bfs_traversal():
def test_cycle_detection():
def test_impact_analysis():
```

---

## Week 3-4: Domain Tests

### D3.1 Drift Detection Tests
**File:** `backend/tests/test_drift.py` (new)
**Effort:** LOW
**Deliverable:** Drift check and alert tests

**Test Cases:**
```python
# Drift check CRUD
def test_create_drift_check():
def test_run_drift_check():
def test_list_alerts():

# Comparison types
def test_absolute_comparison():
def test_percentage_comparison():

# Alert system
def test_alert_creation():
def test_alert_acknowledgment():
def test_alert_severity():

# Statistical tests (after Stream E)
def test_ks_test_drift():
def test_chi_squared_drift():
```

### D3.2 ML Development Tests
**File:** `backend/tests/test_ml_development.py` (new/expand)
**Effort:** MEDIUM
**Deliverable:** State machine and workflow tests

**Test Cases:**
```python
# Recipe CRUD
def test_create_recipe():
def test_version_recipe():
def test_delete_recipe():

# Run management
def test_create_run():
def test_run_state_transitions():
def test_run_metrics():

# State machine
def test_state_machine_transitions():
def test_retry_logic():
def test_error_patterns():

# Derived assets
def test_create_derived_asset():
def test_asset_ttl():
def test_asset_promotion():

# Run comparison
def test_compare_runs():
```

### D3.3 Scheduling Tests
**File:** `backend/tests/test_scheduling.py` (new/expand)
**Effort:** LOW
**Deliverable:** Scheduler functionality tests

**Test Cases:**
```python
# Schedule CRUD
def test_create_schedule():
def test_update_schedule():
def test_delete_schedule():

# Cron parsing
def test_cron_expression():
def test_next_run_calculation():

# Execution
def test_manual_trigger():
def test_pause_resume():

# Run history
def test_run_history_recorded():
def test_run_status_tracking():
```

---

## Week 4-5: E2E & Coverage

### D4.1 E2E Tests with Playwright
**Files:** `tests/e2e/` (new directory)
**Effort:** HIGH
**Deliverable:** Critical path E2E tests

**Test Scenarios:**
```typescript
// tests/e2e/auth.spec.ts
test('user can register and login', async ({ page }) => {
  // Navigate to register, fill form, submit
  // Verify redirect to dashboard
});

// tests/e2e/data-explorer.spec.ts
test('user can explore database', async ({ page }) => {
  // Login, navigate to explorer
  // Select table, view data
  // Execute query
});

// tests/e2e/notebook.spec.ts
test('user can create and run notebook', async ({ page }) => {
  // Create notebook, add cells
  // Execute cells, verify output
});

// tests/e2e/distillation.spec.ts
test('user can curate responses', async ({ page }) => {
  // Create domain, compare models
  // Vote on responses
});
```

### D4.2 Coverage Report
**File:** `pytest.ini`, `pyproject.toml`
**Effort:** LOW
**Deliverable:** 70%+ coverage target

**Setup:**
```ini
# pytest.ini
[pytest]
addopts = --cov=backend --cov-report=html --cov-report=term-missing
```

**Coverage Targets:**
| Domain | Target |
|--------|--------|
| auth | 80% |
| chat | 70% |
| data_explorer | 70% |
| notebooks | 80% |
| synthetic | 80% |
| distillation | 60% |
| ml_development | 70% |
| Overall | 70% |

### D4.3 Performance Benchmarks
**Files:** `backend/tests/benchmarks/` (new)
**Effort:** MEDIUM
**Deliverable:** Baseline performance metrics

**Benchmarks:**
```python
# API response times
def benchmark_data_explorer_query():
    # Target: <500ms for 1000 rows

def benchmark_chat_streaming():
    # Target: <100ms to first token

def benchmark_notebook_execution():
    # Target: <2s for simple SQL

def benchmark_synthetic_generation():
    # Target: <30s for 1000 rows
```

---

## Exit Criteria

- [ ] All new features have tests
- [ ] Overall coverage > 70%
- [ ] E2E tests for critical paths
- [ ] CI pipeline green
- [ ] Performance baselines established

---

## Test Infrastructure

### Fixtures Location
`backend/tests/fixtures/`

### Conftest Setup
`backend/tests/conftest.py`

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=backend

# Specific domain
pytest backend/tests/test_notebooks.py

# E2E tests
npx playwright test
```

---

## Related Files Reference

**Existing Test Files:**
- `backend/tests/test_files_*.py` - Pattern to follow
- `backend/tests/test_health.py` - Simple endpoint test
- `backend/tests/conftest.py` - Fixtures setup

**Test Configuration:**
- `backend/pytest.ini`
- `backend/requirements-test.txt`
