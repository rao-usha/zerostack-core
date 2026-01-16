# Synthetic Data - Changelog

All notable changes to the synthetic data feature will be documented in this file.

---

## [Unreleased]

### Planned
- Phase 2: Privacy - PII detection, Faker integration
- Phase 3: Quality - Enhanced metrics and visualizations
- Phase 4: UI - Generation wizard, quality dashboard
- Phase 5: Integration - Lineage, notebooks, GPU execution

---

## [0.2.0] - 2026-01-15 - Phase 1 Complete

### Added
- **SDV Integration** - Added `sdv>=1.10.0` and `faker>=22.0.0` to requirements
- **New Domain** - `backend/domains/synthetic/` with full structure
- **Three Synthesizers:**
  - `GaussianCopulaSynthesizer` - Fast, preserves correlations (recommended default)
  - `CTGANSynthesizer` - Deep learning, highest quality
  - `TVAESynthesizer` - Stable VAE alternative
- **Quality Evaluator** - Automatic quality scoring with:
  - Per-column KS test scores
  - Correlation preservation metrics
  - Overall quality score (0-1)
  - Recommendations and warnings
- **Database Migration** - `027_add_synthetic_data.py` with tables:
  - `synthetic_jobs` - Job tracking
  - `synthetic_datasets` - Generated datasets
  - `synthetic_quality_reports` - Quality metrics
  - `synthetic_column_configs` - Per-column settings
- **API Endpoints:**
  - `GET /api/v1/synthetic/synthesizers` - List available synthesizers
  - `POST /api/v1/synthetic/generate-from-csv` - Generate from uploaded CSV
  - `GET /api/v1/synthetic/jobs/{id}` - Job status
  - `GET /api/v1/synthetic/datasets` - List synthetic datasets
  - `GET /api/v1/synthetic/datasets/{id}` - Get dataset info
  - `GET /api/v1/synthetic/datasets/{id}/download` - Download CSV/Parquet
  - `GET /api/v1/synthetic/datasets/{id}/preview` - Preview rows
  - `GET /api/v1/synthetic/datasets/{id}/quality` - Quality report
- **Tests** - Basic test suite in `backend/tests/test_synthetic.py`

### Architecture
- Base synthesizer interface for extensibility
- Service layer with async database operations
- Quality evaluation decoupled from synthesis

---

## [0.1.0] - Current State

### Existing (Basic Implementation)
- Simple column-by-column statistical sampling
- Basic API endpoint `/api/synthetic/generate`
- Frontend page for generation
- Domain models defined

### Known Limitations
- No correlation preservation between columns
- No privacy guarantees
- No quality metrics
- No PII detection or handling
- Single synthesizer approach only

---

## Implementation Log

### 2026-01-15 - Planning Document Created
- Created comprehensive planning document (PLAN.md)
- Evaluated approaches: statistical, ML, deep learning
- Selected SDV as primary library
- Defined 5-phase implementation roadmap
- Documented API design and architecture

---

## Future Releases

### [0.2.0] - Foundation (Planned)
- [ ] SDV library integration
- [ ] GaussianCopulaSynthesizer
- [ ] CTGANSynthesizer
- [ ] TVAESynthesizer
- [ ] New API endpoints
- [ ] Job tracking

### [0.3.0] - Privacy (Planned)
- [ ] PII auto-detection
- [ ] Faker-based PII replacement
- [ ] Privacy level configuration
- [ ] Privacy risk scoring

### [0.4.0] - Quality (Planned)
- [ ] Statistical fidelity metrics
- [ ] Correlation preservation scoring
- [ ] Quality report generation
- [ ] Distribution visualizations

### [0.5.0] - UI (Planned)
- [ ] Generation wizard
- [ ] Quality dashboard
- [ ] Column configuration UI
- [ ] Progress tracking

### [1.0.0] - Full Release (Planned)
- [ ] Platform integration complete
- [ ] Data lineage tracking
- [ ] Notebook integration
- [ ] GPU execution support
- [ ] Full documentation
