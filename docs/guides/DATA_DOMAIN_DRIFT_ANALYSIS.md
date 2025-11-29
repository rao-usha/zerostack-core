# Data Domain Drift Analysis

This document compares the current database schema and domain models against the specified core data domain structure.

## Executive Summary

**Status**: ⚠️ **Partial Alignment with Significant Gaps**

The codebase has most core domains implemented but several are missing or structured differently than specified. Relationships are mostly encoded in JSON rather than proper relational tables.

---

## Domain-by-Domain Analysis

### ✅ 1. Contexts - **MOSTLY ALIGNED**

**Current State:**
- ✅ `contexts` table (Context entity)
- ✅ `context_versions` table (ContextVersion entity) 
- ✅ `context_layers` table (ContextLayer entity)
- ✅ Content-addressed `digest` field in context_versions

**Drift/Issues:**
- ⚠️ **Relationships stored in JSON**: `context_versions.data_refs` stores dataset_version_ids, persona_ids, and MCP tools as JSON array instead of proper many-to-many tables
- ⚠️ **Layers structure**: `context_layers` is tied to `context_id` instead of `context_version_id` - layers should be version-specific per spec
- ✅ Digest calculation appears correct (sha256 of spec)

**Spec Compliance:**
- Entities: ✅ Context, ContextVersion, ContextLayer all exist
- Keys/Links: ⚠️ ContextVersion ↔ DatasetVersion relationship is JSON, not relational
- Ops: Partially implemented (create, layer exist; snapshot/export need verification)

---

### ✅ 2. Datasets - **ALIGNED**

**Current State:**
- ✅ `datasets` table (Dataset entity)
- ✅ `dataset_versions` table (DatasetVersion entity)
- ✅ `connectors` table (ConnectorRef entity)
- ✅ Dataset 1→* DatasetVersion relationship

**Drift/Issues:**
- ⚠️ **Missing fields in dataset_versions**:
  - No `path` or `hash` field for stored object reference
  - No `schema` field (JSON for column definitions/types)
  - No `stats` field (JSON for statistical summaries)
- ✅ `summary` field exists (Text)

**Spec Compliance:**
- Entities: ✅ Dataset, DatasetVersion, ConnectorRef all exist
- Keys/Links: ✅ DatasetVersion properly linked to Dataset
- Ops: Partially implemented

---

### ⚠️ 3. Evaluations - **MOSTLY ALIGNED**

**Current State:**
- ✅ `eval_scenarios` table (EvalScenario entity)
- ✅ `eval_runs` table (EvalRun entity)
- ✅ EvalRun ↔ ContextVersion relationship (foreign key)
- ✅ EvalScenario 1→* EvalRun relationship

**Drift/Issues:**
- ⚠️ **EvalMetric stored in JSON**: `eval_runs.metrics` is JSON instead of separate `eval_metrics` table
- ✅ Relationship structure matches spec

**Spec Compliance:**
- Entities: ⚠️ EvalScenario, EvalRun exist; EvalMetric should be separate table
- Keys/Links: ✅ EvalRun ↔ ContextVersion, EvalScenario relationships correct
- Ops: Partially implemented

---

### ❌ 4. Synthetic Data - **MISSING**

**Current State:**
- ❌ No `synth_policies` table
- ❌ No `synth_jobs` table  
- ❌ No `synth_artifacts` table
- ⚠️ Some code exists in `backend/services/synthetic_data.py` but no DB schema

**Drift/Issues:**
- **Complete domain missing from database schema**
- Synthetic data models exist in Pydantic (`SyntheticDataRequest`, `SyntheticDataResult`) but no persistence layer
- No linkage to DatasetVersion for derived/augmented data

**Spec Compliance:**
- Entities: ❌ None exist
- Keys/Links: ❌ None exist
- Ops: ❌ None exist

---

### ⚠️ 5. Dictionaries (Shareable) - **STRUCTURAL MISMATCH**

**Current State:**
- ⚠️ `context_dictionaries` table exists but is context-scoped, not org-scoped shareable
- Stored as JSON `entries` field (term → definition mapping)
- No separate `dictionary_entries` table

**Drift/Issues:**
- ❌ **Wrong structure**: Should be `dictionaries` (org-scoped) and `dictionary_entries` (with foreign key to dictionaries)
- ❌ **Current**: `context_dictionaries` is tied to `context_id` (context-specific)
- ❌ **Spec**: Dictionaries should be shareable, referenced by ContextLayer(kind=dictionary) via ID
- Current implementation doesn't allow reuse across contexts

**Spec Compliance:**
- Entities: ❌ Wrong structure; need standalone Dictionary and DictionaryEntry tables
- Keys/Links: ❌ Should be referenced by ContextLayer, not embedded in context
- Ops: Partially implemented but at wrong scope

---

### ⚠️ 6. Personas (Profiles) - **MOSTLY ALIGNED**

**Current State:**
- ✅ `personas` table (Persona entity)
- ✅ Org-scoped (has `org_id`)
- ⚠️ `PersonaVersion` exists in Pydantic models (`backend/domains/personas/models.py`) but **no DB table**

**Drift/Issues:**
- ⚠️ **PersonaVersion table missing**: Spec says "PersonaVersion (optional later)" but Pydantic model exists without DB persistence
- ✅ Referenced by ContextLayer(kind=persona) - implemented via JSON in data_refs
- ⚠️ No explicit many-to-many table for ContextVersion ↔ Persona

**Spec Compliance:**
- Entities: ⚠️ Persona exists; PersonaVersion model exists but no table
- Keys/Links: ⚠️ Referenced by ContextLayer but relationship is JSON-based
- Ops: Partially implemented

---

### ⚠️ 7. Governance - **PARTIAL**

**Current State:**
- ✅ `policies` table (Policy entity)
- ✅ `audit_log` table (AuditLog entity)
- ❌ **No `policy_checks` table** to track policy evaluations on entities

**Drift/Issues:**
- ❌ **PolicyCheck table missing**: Spec says "PolicyCheck *—1 {ContextVersion|DatasetVersion|SynthJob|EvalRun}" but this table doesn't exist
- No way to track which policies were checked against which entities
- No enforcement history

**Spec Compliance:**
- Entities: ⚠️ Policy, AuditLog exist; PolicyCheck missing
- Keys/Links: ❌ PolicyCheck relationships missing
- Ops: Policy creation exists; policy checking/evaluation infrastructure missing

---

### ⚠️ 8. Versioning & Lineage - **MODELS EXIST, NO DB TABLES**

**Current State:**
- ⚠️ `Snapshot` and `LineageEdge` exist as Pydantic models in `backend/domains/context/models.py`
- ❌ **No database tables** for `snapshots` or `lineage_edges`

**Drift/Issues:**
- ❌ **No persistence**: Models exist but can't be stored/queried
- ❌ **No lineage graph storage**: Can't track DatasetVersion → ContextVersion → EvalRun/SynthArtifact edges
- No digest computation tracking

**Spec Compliance:**
- Entities: ❌ Snapshot, LineageEdge models exist but no tables
- Keys/Links: ❌ No database relationships
- Ops: ❌ No implementation

---

### ✅ 9. Orgs & Access - **ALIGNED**

**Current State:**
- ✅ `orgs` table (Org entity)
- ✅ `users` table (User entity)
- ⚠️ `role` stored as string in users table (no separate Role table - spec says "Role" but this is acceptable for MVP)
- ❌ No `tokens` table explicitly (may be handled elsewhere)

**Spec Compliance:**
- Entities: ✅ Org, User exist; Role is string (acceptable)
- Purpose: ✅ Tenancy, RBAC structure in place

---

### ⚠️ 10. Jobs & Artifacts - **PARTIAL**

**Current State:**
- ✅ `jobs` table (Job entity)
- ❌ **No `artifacts` table** for durable outputs (exported packs, reports)

**Drift/Issues:**
- ❌ **Artifacts table missing**: No way to store exported packs, reports, or other job outputs
- Jobs table exists but no linkage to artifacts

**Spec Compliance:**
- Entities: ⚠️ Job exists; Artifact missing
- Purpose: ⚠️ Async queue exists; durable outputs storage missing

---

## Relationship Analysis

### Current Relationships (from DB models):

✅ **Implemented:**
- Dataset 1—* DatasetVersion ✓
- Context 1—* ContextVersion ✓
- EvalScenario 1—* EvalRun ✓
- EvalRun *—1 ContextVersion ✓
- Users *—1 Org ✓

❌ **Missing or Wrong:**
- ContextVersion *—* DatasetVersion (stored as JSON in `data_refs`)
- ContextVersion *—* Dictionary (wrong: dictionaries are context-scoped)
- ContextVersion *—* Persona (stored as JSON in `data_refs`)
- SynthJob 1—* SynthArtifact *—1 DatasetVersion (entire domain missing)
- PolicyCheck *—1 {ContextVersion|DatasetVersion|SynthJob|EvalRun} (table missing)
- AuditLog *—1 Org (exists but structure may differ)

---

## Missing Tables Summary

1. **synth_policies** - Synthetic data generation policies
2. **synth_jobs** - Synthetic data generation jobs
3. **synth_artifacts** - Synthetic data artifacts linked to DatasetVersions
4. **dictionaries** - Standalone shareable dictionaries (org-scoped)
5. **dictionary_entries** - Dictionary entries with foreign key to dictionaries
6. **persona_versions** - Persona versioning (optional per spec but model exists)
7. **policy_checks** - Policy evaluation results on entities
8. **snapshots** - Versioning snapshots
9. **lineage_edges** - Lineage graph edges
10. **artifacts** - Job outputs (exported packs, reports)
11. **eval_metrics** - Evaluation metrics (currently in JSON)
12. **tokens** - API tokens (if not handled elsewhere)

---

## Missing Fields Summary

1. **dataset_versions**:
   - `path` or `object_url` - Storage location
   - `hash` or `sha256` - Content hash
   - `schema` (JSON) - Column definitions/types
   - `stats` (JSON) - Statistical summaries

2. **context_layers**:
   - Should link to `context_version_id` not just `context_id` (layers are version-specific)

3. **Relationships should be tables**:
   - `context_version_dataset_versions` (many-to-many)
   - `context_version_personas` (many-to-many)
   - `context_version_dictionaries` (many-to-many, when dictionaries are standalone)

---

## Recommendations

### High Priority (Core Functionality)
1. **Create Synthetic Data domain tables** (synth_policies, synth_jobs, synth_artifacts)
2. **Restructure Dictionaries** to be org-scoped shareable entities
3. **Add PolicyCheck table** for governance tracking
4. **Add missing DatasetVersion fields** (schema, stats, storage location)

### Medium Priority (Data Quality)
5. **Create relationship tables** for ContextVersion ↔ DatasetVersion, Persona, Dictionary (instead of JSON)
6. **Split EvalMetric** into separate table from JSON storage
7. **Add Artifacts table** for job outputs
8. **Link context_layers to context_version_id** instead of context_id

### Low Priority (Nice to Have)
9. **Create Snapshot and LineageEdge tables** (if versioning/lineage features are needed)
10. **Add PersonaVersion table** (optional per spec but model exists)
11. **Consider Token table** if not handled elsewhere

---

## Storage Hints Compliance

- ✅ Postgres tables for entities: Mostly compliant
- ✅ Object store for files: Not explicitly in schema but `dataset_versions` should have URL/hash fields
- ✅ Content-addressed ContextVersion.digest: ✅ Implemented
- ⚠️ Object store fields missing: No `sha256` or `url` fields in dataset_versions for stored objects

---

## Endpoints vs Spec

**Spec says**: `/datasets/upload`, `/contexts`, `/contexts/{id}/layers`, `/contexts/{id}/version`, `/evals/run`, `/dictionaries`, `/personas`, `/policies/check`

**Current**: Need to verify all endpoints exist, but structure suggests most are implemented or stubbed.

