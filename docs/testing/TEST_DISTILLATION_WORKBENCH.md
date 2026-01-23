# Distillation Workbench - Test Plan

A comprehensive test plan for all features in the Distillation Workbench.

## Prerequisites

Before testing, ensure:
- [ ] Backend is running (`docker ps` shows `nex-backend` healthy)
- [ ] Frontend is running (`docker ps` shows `nex-frontend` healthy)
- [ ] Database migrations are applied (`docker exec nex-backend alembic current` shows `023_add_lineage_tracking`)
- [ ] At least one API key is configured (OpenAI, Anthropic, Google, or xAI)

Access the workbench at: `http://localhost:3000/distillation`

---

## 1. Interactive Chat

### 1.1 Basic Chat Functionality
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.1.1 | Load available models | Navigate to Interactive Chat | Models dropdown shows available providers (based on configured API keys) | |
| 1.1.2 | Single model chat | Select one model, type prompt, click Send | Response streams in with model name prefix | |
| 1.1.3 | Multi-model chat | Select 2-3 models, type prompt, click Send | All models respond concurrently, interleaved streaming | |
| 1.1.4 | Empty prompt handling | Leave prompt empty, click Send | Error message or disabled button | |
| 1.1.5 | Long prompt handling | Enter 1000+ character prompt, send | Response received without truncation | |

### 1.2 Model Selection
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.2.1 | Model tags display | Open model selector | Each model shows provider tag (openai, anthropic, etc.) | |
| 1.2.2 | Multiple selection | Click multiple models | All selected models highlighted | |
| 1.2.3 | Deselection | Click selected model again | Model deselected | |

### 1.3 Banking from Chat
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 1.3.1 | Bank a response | Click "Bank" on a response | Toast notification "Response banked!", appears in Response Bank | |
| 1.3.2 | Verify banked response | Go to Response Bank tab | Banked response visible with model info | |

---

## 2. Batch Generator

### 2.1 Template Management
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.1.1 | List built-in templates | Navigate to Batch Generator | Shows 5 built-in templates (QA Pair Generator, etc.) | |
| 2.1.2 | Template preview | Select a template in new batch form | Shows system prompt and user template preview | |

### 2.2 Batch Job Creation
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.2.1 | Create batch job | Click "+ New Batch Job", fill form, submit | Job created and appears in list | |
| 2.2.2 | Input parsing | Enter multi-line text input | Shows "X total requests" count | |
| 2.2.3 | Model selection | Select multiple models for batch | Each input runs against all selected models | |
| 2.2.4 | Parallelism setting | Adjust parallelism slider (1-10) | Slider updates value display | |
| 2.2.5 | Auto-bank toggle | Enable auto-bank checkbox | Setting saved in job | |

### 2.3 Batch Job Execution
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.3.1 | Job progress | Start batch job, watch progress | Progress bar updates, status changes | |
| 2.3.2 | View job items | Click on a running/completed job | Shows list of individual items with status | |
| 2.3.3 | Item output display | Click on completed item | Shows input, rendered prompt, and output | |
| 2.3.4 | Cancel job | Click cancel on running job | Job status changes to "cancelled" | |
| 2.3.5 | Bank batch item | Click "Bank" on completed item | Item marked as banked, appears in Response Bank | |

### 2.4 Error Handling
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 2.4.1 | Failed item display | Review job with failed items | Failed items show error message | |
| 2.4.2 | Partial completion | Job with mix of success/failure | Shows accurate completed/failed counts | |

---

## 3. Task Library

### 3.1 Task Management
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 3.1.1 | View tasks | Navigate to Task Library | Shows list of existing tasks | |
| 3.1.2 | Create task | Click "+ New Task", fill form, submit | New task appears in list | |
| 3.1.3 | Task details | Click on a task | Shows task details (name, prompt template, etc.) | |

---

## 4. Response Bank

### 4.1 Viewing Banked Responses
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.1.1 | List responses | Navigate to Response Bank | Shows all banked responses | |
| 4.1.2 | Response details | View a banked response | Shows prompt, response text, model, timestamp | |
| 4.1.3 | Quality rating | Check quality score display | Shows rating if set | |

### 4.2 Response Actions
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 4.2.1 | Delete response | Click delete on banked response | Response removed, toast confirmation | |
| 4.2.2 | Edit notes | Update notes on banked response | Notes saved | |

---

## 5. Compare

### 5.1 Comparison Creation
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.1.1 | Create comparison | Click new comparison, select responses | Comparison created | |
| 5.1.2 | Side-by-side view | Open comparison | Shows responses side-by-side | |

### 5.2 Voting
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 5.2.1 | Cast vote | Click vote button on preferred response | Vote recorded, UI updates | |
| 5.2.2 | View vote results | Check comparison after voting | Shows vote counts | |

---

## 6. Structure

### 6.1 Banked Response View
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.1.1 | View banked content | Navigate to Structure tab | Shows banked responses with full content (prompt + response) | |
| 6.1.2 | Content preview | Check banked item display | Shows prompt_sent and response_text | |

### 6.2 Schema Selection
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.2.1 | Select schema | Choose schema from dropdown | Schema selected | |
| 6.2.2 | Extract structure | Click extract on banked response | Structured data created | |

### 6.3 Dataset Integration
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 6.3.1 | Select multiple items | Use checkboxes to select banked items | Selection count updates | |
| 6.3.2 | Bulk add to dataset | Select items, choose split, add to dataset | Items added with correct split | |
| 6.3.3 | Individual add | Use per-item dropdown to add to dataset | Single item added | |
| 6.3.4 | Split selection | Choose train/validation/test split | Correct split assigned | |

---

## 7. Expert Review

### 7.1 Review Queue Management
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.1.1 | Create queue | Click create queue, fill details | Queue created | |
| 7.1.2 | View queues | Navigate to Expert Review | Shows list of review queues | |

### 7.2 Review Actions
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 7.2.1 | Approve item | Click approve on review item | Item status changes to approved | |
| 7.2.2 | Reject item | Click reject on review item | Item status changes to rejected | |
| 7.2.3 | Add feedback | Enter feedback, submit | Feedback saved | |

---

## 8. Datasets

### 8.1 Dataset Management
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.1.1 | Create dataset | Click create, enter name/description | Dataset created | |
| 8.1.2 | View datasets | Navigate to Datasets tab | Shows list of datasets with item counts | |
| 8.1.3 | Delete dataset | Click delete on dataset | Dataset removed | |

### 8.2 Dataset Items
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.2.1 | View items | Click on dataset | Shows list of items with split tags | |
| 8.2.2 | Expand item | Click expand on dataset item | Shows prompt/response content | |
| 8.2.3 | Change split | Use split selector on item | Split updated | |
| 8.2.4 | Remove item | Click remove on dataset item | Item removed from dataset | |

### 8.3 Split Distribution
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 8.3.1 | Split balance | Add items with different splits | Shows train/val/test counts | |

---

## 9. Lineage & Process Discovery (NEW)

### 9.1 Model Contributions
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.1.1 | Load contributions | Navigate to Lineage, click Refresh | Model contribution cards appear | |
| 9.1.2 | View statistics | Check model cards | Shows total responses, banked count, bank rate, dataset rate | |
| 9.1.3 | Progress bar | Check mini progress bars | Bar width matches bank rate | |
| 9.1.4 | Multiple models | Use multiple models in chat/batch | All models appear in contributions | |

### 9.2 Dataset Provenance
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.2.1 | Select dataset | Click dataset button in Provenance section | Provenance data loads | |
| 9.2.2 | Total items | Check stats | Shows correct total item count | |
| 9.2.3 | By model breakdown | Review "By Model" section | Shows count per model used | |
| 9.2.4 | By purpose breakdown | Review "By Purpose" section | Shows count per purpose tag (if any) | |
| 9.2.5 | Unique sources | Check unique sources count | Shows distinct source response count | |
| 9.2.6 | Date range | Check date range display | Shows earliest to latest date | |

### 9.3 Audit Trail
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.3.1 | View audit logs | Click Refresh in Lineage tab | Audit trail section shows recent activity | |
| 9.3.2 | Action badges | Check log entries | Color-coded badges (green=banked, blue=created, etc.) | |
| 9.3.3 | Model info | Check entries with model info | Shows provider/model name | |
| 9.3.4 | Timestamps | Check log entry times | Shows formatted date/time | |

### 9.4 Purpose Tags
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 9.4.1 | View standard purposes | Check Purpose Tags Reference section | Shows all standard purpose tags | |
| 9.4.2 | Purpose list | Verify purposes | customer_faq, compliance_training, agent_reasoning, tool_use, instruction_following, knowledge_base, code_generation, classification, summarization, extraction, other | |

---

## 10. Statistics

### 10.1 Overview Stats
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 10.1.1 | Load stats | Navigate to Statistics tab | Shows response counts, model breakdown | |
| 10.1.2 | Response breakdown | Check by-model stats | Accurate counts per model | |

---

## 11. Cross-Feature Integration Tests

### 11.1 Full Pipeline
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 11.1.1 | Chat → Bank → Dataset | 1. Chat with model, 2. Bank response, 3. Add to dataset | Response traceable through pipeline | |
| 11.1.2 | Batch → Bank → Structure → Dataset | 1. Run batch job, 2. Bank items, 3. Structure extraction, 4. Add to dataset | All steps complete successfully | |
| 11.1.3 | Lineage verification | After pipeline, check Lineage tab | Shows model contributions updated, dataset provenance accurate | |

### 11.2 Data Consistency
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 11.2.1 | Banked count sync | Bank responses, check Response Bank count | Count matches actual items | |
| 11.2.2 | Dataset item count | Add items to dataset, verify count | Dataset shows correct item count | |
| 11.2.3 | Model contribution accuracy | Compare contributions to actual activity | Contribution stats match reality | |

---

## 12. Error Handling & Edge Cases

### 12.1 API Errors
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 12.1.1 | Invalid API key | Use invalid API key, send chat | Error message displayed, not crash | |
| 12.1.2 | Network timeout | Simulate slow network | Appropriate timeout handling | |
| 12.1.3 | Rate limiting | Send many rapid requests | Rate limit message, graceful handling | |

### 12.2 UI Edge Cases
| # | Test Case | Steps | Expected Result | Pass/Fail |
|---|-----------|-------|-----------------|-----------|
| 12.2.1 | Empty states | View tabs with no data | Appropriate empty state messages | |
| 12.2.2 | Long content | Bank very long response | Content truncated/scrollable | |
| 12.2.3 | Special characters | Use special chars in prompts | Characters preserved correctly | |

---

## Test Execution Summary

| Feature | Total Tests | Passed | Failed | Blocked |
|---------|-------------|--------|--------|---------|
| Interactive Chat | 8 | | | |
| Batch Generator | 11 | | | |
| Task Library | 3 | | | |
| Response Bank | 5 | | | |
| Compare | 4 | | | |
| Structure | 7 | | | |
| Expert Review | 5 | | | |
| Datasets | 7 | | | |
| Lineage | 13 | | | |
| Statistics | 2 | | | |
| Integration | 5 | | | |
| Error Handling | 6 | | | |
| **TOTAL** | **76** | | | |

---

## Quick Smoke Test (5 minutes)

For rapid validation, run these critical tests:

1. [ ] **Chat**: Send prompt to one model → response streams
2. [ ] **Bank**: Click bank on response → toast appears
3. [ ] **Batch**: Create batch job with 2 inputs → job runs
4. [ ] **Dataset**: Add banked item to dataset → count updates
5. [ ] **Lineage**: Load model contributions → cards appear
6. [ ] **Provenance**: Select dataset → breakdown shows

---

## Notes

- **Date**: _______________
- **Tester**: _______________
- **Build/Version**: _______________
- **Environment**: Docker / Local / CI

### Issues Found
| ID | Feature | Description | Severity | Status |
|----|---------|-------------|----------|--------|
| | | | | |

### Comments
_______________________________________________________
_______________________________________________________
_______________________________________________________
