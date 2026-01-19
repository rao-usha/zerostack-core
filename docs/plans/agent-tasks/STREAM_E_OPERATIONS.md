# Stream E: Operations & Infrastructure

**Priority:** MEDIUM
**Estimated Duration:** 3 weeks
**Dependencies:** None (runs independently)

---

## Overview

Complete partial features in operations: notifications, drift statistical tests, and documentation.

---

## Week 1-2: Notifications

### E1.1 Email Notification Delivery
**Files:** `backend/services/notifications.py`
**Effort:** MEDIUM
**Deliverable:** SMTP email integration

**Current Status:** Notification service exists (540 LOC) but delivery is stubbed

**Location of TODO:** `scheduler.py:281`
```python
# TODO: Implement email notification
```

**Requirements:**
- SMTP configuration (host, port, credentials)
- Email template system
- HTML email support
- Attachment support
- Retry on failure

**Implementation:**
```python
# backend/services/notifications.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, smtp_host, smtp_port, username, password):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    async def send(self, to: str, subject: str, body: str, html: bool = False):
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = to

        content_type = 'html' if html else 'plain'
        msg.attach(MIMEText(body, content_type))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.sendmail(self.username, to, msg.as_string())
```

### E1.2 Slack Notification Delivery
**Files:** `backend/services/notifications.py`
**Effort:** LOW
**Deliverable:** Slack webhook integration

**Location of TODO:** `scheduler.py:284`
```python
# TODO: Implement Slack notification
```

**Requirements:**
- Slack webhook URL configuration
- Message formatting (blocks, attachments)
- Channel routing
- Error notifications with stack traces

**Implementation:**
```python
class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, message: str, channel: str = None, blocks: list = None):
        payload = {"text": message}
        if channel:
            payload["channel"] = channel
        if blocks:
            payload["blocks"] = blocks

        async with httpx.AsyncClient() as client:
            await client.post(self.webhook_url, json=payload)
```

### E1.3 Webhook Notifications
**Files:** `backend/services/notifications.py`
**Effort:** LOW
**Deliverable:** Generic webhook support

**Location of TODO:** `scheduler.py:287`
```python
# TODO: Implement webhook notification
```

**Requirements:**
- Configurable webhook URLs
- Custom payload templates
- Authentication headers
- Retry with exponential backoff

### E1.4 Wire Notifications to Scheduler
**Files:** `backend/services/scheduler.py:281-287`
**Effort:** LOW
**Deliverable:** Trigger notifications on events

**Events to Notify:**
- Schedule execution complete
- Schedule execution failed
- Drift alert triggered
- Job completed/failed

**Implementation:**
```python
# In scheduler.py
async def _execute_schedule(self, schedule_id: str):
    try:
        result = await self._run_job(schedule_id)
        await self.notifier.send_success(schedule_id, result)
    except Exception as e:
        await self.notifier.send_failure(schedule_id, e)
```

---

## Week 2-3: Partial Feature Completion

### E2.1 Synthetic Data Loading from Storage
**Files:** `backend/domains/synthetic/router.py:181,192`
**Effort:** LOW
**Deliverable:** Load datasets from storage for generation

**Current TODOs:**
```python
# Line 181: TODO: Load dataset from storage
# Line 192: TODO: Load table from connection
```

**Implementation:**
```python
# Line 181 - Load from MinIO/object storage
async def load_dataset_from_storage(dataset_id: str) -> pd.DataFrame:
    object_store = get_object_store()
    data = await object_store.get_object(f"datasets/{dataset_id}")
    return pd.read_parquet(io.BytesIO(data))

# Line 192 - Load from database connection
async def load_table_from_connection(connection_id: str, table_name: str) -> pd.DataFrame:
    conn = await get_connection(connection_id)
    return pd.read_sql(f"SELECT * FROM {table_name}", conn)
```

### E2.2 Drift Statistical Tests
**Files:** `backend/services/drift_detector.py`
**Effort:** MEDIUM
**Deliverable:** KS-test and Chi-squared drift detection

**Current Status:** Basic comparison types exist, statistical tests missing

**Tests to Implement:**
```python
from scipy import stats

def ks_test_drift(baseline: np.array, current: np.array, threshold: float = 0.05) -> dict:
    """Kolmogorov-Smirnov test for numerical columns."""
    statistic, p_value = stats.ks_2samp(baseline, current)
    return {
        "test": "ks_test",
        "statistic": statistic,
        "p_value": p_value,
        "drift_detected": p_value < threshold
    }

def chi_squared_drift(baseline: pd.Series, current: pd.Series, threshold: float = 0.05) -> dict:
    """Chi-squared test for categorical columns."""
    # Create contingency table
    baseline_counts = baseline.value_counts()
    current_counts = current.value_counts()

    # Align categories
    all_categories = set(baseline_counts.index) | set(current_counts.index)
    baseline_aligned = [baseline_counts.get(c, 0) for c in all_categories]
    current_aligned = [current_counts.get(c, 0) for c in all_categories]

    statistic, p_value = stats.chisquare(current_aligned, f_exp=baseline_aligned)
    return {
        "test": "chi_squared",
        "statistic": statistic,
        "p_value": p_value,
        "drift_detected": p_value < threshold
    }

def population_stability_index(baseline: pd.Series, current: pd.Series, bins: int = 10) -> dict:
    """PSI for distribution shift detection."""
    # Bin the data
    baseline_hist, bin_edges = np.histogram(baseline, bins=bins)
    current_hist, _ = np.histogram(current, bins=bin_edges)

    # Calculate PSI
    baseline_pct = baseline_hist / len(baseline)
    current_pct = current_hist / len(current)

    # Avoid division by zero
    baseline_pct = np.where(baseline_pct == 0, 0.0001, baseline_pct)
    current_pct = np.where(current_pct == 0, 0.0001, current_pct)

    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))

    return {
        "test": "psi",
        "value": psi,
        "drift_detected": psi > 0.25  # Common threshold
    }
```

### E2.3 Evaluation Pack Metrics
**Files:** `backend/domains/evaluation_packs/router.py`, `backend/domains/evaluation_packs/metrics.py` (new)
**Effort:** MEDIUM
**Deliverable:** Standard ML evaluation metrics

**Metrics to Implement:**
```python
# Classification metrics
def accuracy(y_true, y_pred): ...
def precision(y_true, y_pred, average='weighted'): ...
def recall(y_true, y_pred, average='weighted'): ...
def f1_score(y_true, y_pred, average='weighted'): ...
def roc_auc(y_true, y_scores): ...
def confusion_matrix(y_true, y_pred): ...

# Regression metrics
def mse(y_true, y_pred): ...
def rmse(y_true, y_pred): ...
def mae(y_true, y_pred): ...
def r2_score(y_true, y_pred): ...
def mape(y_true, y_pred): ...

# NLP metrics (for distillation)
def bleu_score(reference, candidate): ...
def rouge_score(reference, candidate): ...
```

---

## Week 3: Documentation

### E3.1 OpenAPI Documentation
**Files:** `backend/main.py`, FastAPI auto-generation
**Effort:** MEDIUM
**Deliverable:** Complete Swagger UI documentation

**Requirements:**
- Add descriptions to all endpoints
- Document request/response schemas
- Add example values
- Group endpoints by domain

**Implementation:**
```python
# In each router
@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Get item by ID",
    description="Retrieves a single item by its unique identifier.",
    responses={
        200: {"description": "Item found"},
        404: {"description": "Item not found"},
    }
)
async def get_item(item_id: str):
    """
    Get an item from the database.

    - **item_id**: The unique identifier of the item
    """
    ...
```

### E3.2 API Usage Examples
**Files:** `docs/api/examples/` (new directory)
**Effort:** LOW
**Deliverable:** Code samples for each domain

**Examples to Create:**
- `examples/data_explorer.md` - Query execution examples
- `examples/notebooks.md` - Notebook creation and execution
- `examples/distillation.md` - Response curation workflow
- `examples/ml_development.md` - Recipe and run management
- `examples/synthetic.md` - Synthetic data generation

---

## Exit Criteria

- [ ] Email notifications working
- [ ] Slack notifications working
- [ ] Webhook notifications working
- [ ] Synthetic data loads from storage
- [ ] Drift detection has statistical tests
- [ ] Evaluation packs have standard metrics
- [ ] OpenAPI docs complete with examples

---

## Environment Variables Required

```bash
# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=notifications@example.com
SMTP_PASSWORD=app-password

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# Object Storage (for synthetic data loading)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
```

---

## Related Files Reference

**Notification Service:**
- `backend/services/notifications.py` (540 LOC)

**Scheduler:**
- `backend/services/scheduler.py:281-287` - Notification TODOs

**Synthetic Data:**
- `backend/domains/synthetic/router.py:181,192` - Loading TODOs

**Drift Detection:**
- `backend/services/drift_detector.py` (424 LOC)

**Evaluation Packs:**
- `backend/domains/evaluation_packs/router.py` (~200 LOC)
