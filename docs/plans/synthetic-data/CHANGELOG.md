# Synthetic Data - Changelog

All notable changes to the synthetic data feature will be documented in this file.

---

## [Unreleased]

### Planned
- Phase 4: UI - Generation wizard, quality dashboard
- Phase 5: Integration - Lineage, notebooks, GPU execution

---

## [0.5.0] - 2026-01-16 - Persistent Storage

### Added
- **SyntheticDataStorage** (`storage.py`)
  - Save/load synthetic datasets to S3/MinIO
  - Save source data samples for quality comparisons
  - Presigned URL generation for downloads
  - Storage info and cleanup methods

- **ObjectStorePaths extensions**
  - `synthetic_root()`, `synthetic_data()`, `synthetic_manifest()`
  - `synthetic_quality_report()`, `synthetic_source_sample()`
  - `create_synthetic_manifest()` helper

- **LRU Cache** for recent datasets (10 items)
  - Reduces repeated S3 fetches
  - Automatic eviction of old entries

- **New API Endpoints:**
  - `DELETE /datasets/{id}` - Delete dataset and storage
  - `GET /datasets/{id}/storage-info` - Storage details
  - Updated `/download` with presigned URL option

### Changed
- Router now loads data from S3 instead of in-memory cache
- `generate-from-csv` saves to S3 after generation
- Service includes `update_dataset_storage()` and `delete_dataset()`
- All quality visualization endpoints load from storage
- Downloads can use presigned URLs for large files

### Storage Layout
```
synthetic/{dataset_id}/
├── data.parquet           # Main data file
├── data.csv               # CSV copy for easy download
├── manifest.json          # Dataset metadata
├── quality_report.json    # Quality metrics
└── source_sample.parquet  # Source data for comparisons
```

---

## [0.4.0] - 2026-01-16 - Phase 3 Complete (Quality Metrics)

### Added
- **Quality Module** (`quality/`) - Comprehensive quality evaluation
  - Moved evaluator to dedicated quality module
  - Enhanced organization for quality-related code

- **ML Utility Evaluator** (`quality/ml_utility.py`)
  - TSTR (Train on Synthetic, Test on Real) methodology
  - Supports classification and regression tasks
  - Auto-detection of task type
  - Feature importance correlation analysis
  - Comparison with TRTR (Train Real, Test Real) baseline
  - Utility ratio scoring

- **Detection Evaluator** (`quality/detection.py`)
  - Tests if classifier can distinguish real vs synthetic
  - Multiple classifier ensemble (RandomForest, LogisticRegression)
  - Cross-validation scoring
  - Identifies most distinguishing features
  - Detection difficulty score (higher = better synthetic)

- **Quality Visualizer** (`quality/visualizations.py`)
  - Histogram data for numeric column comparison
  - Category comparison for categorical columns
  - Correlation matrix comparison (real vs synthetic vs diff)
  - Summary statistics generator
  - JSON-serializable output for frontend charts

- **New API Endpoints:**
  - `GET /datasets/{id}/distributions` - Distribution comparison data
  - `GET /datasets/{id}/correlations` - Correlation matrix comparison
  - `GET /datasets/{id}/stats` - Summary statistics comparison
  - `GET /datasets/{id}/ml-utility` - ML utility evaluation
  - `GET /datasets/{id}/detection` - Detection score evaluation
  - `GET /datasets/{id}/quality-dashboard` - Combined quality dashboard

- **Quality Tests** - 12+ new tests for quality metrics

### Changed
- Quality evaluator now part of `quality/` module
- Router includes quality visualization endpoints
- Source data cached for quality analysis

---

## [0.3.0] - 2026-01-16 - Phase 2 Complete (Privacy)

### Added
- **PII Detection Service** (`privacy/pii_detector.py`)
  - Auto-detect 15+ PII types: email, phone, SSN, names, addresses, etc.
  - Detection by column name patterns and content regex
  - Confidence scoring and detection method reporting
  - Summary generation with recommendations

- **Faker-based PII Generator** (`privacy/faker_generator.py`)
  - Replace detected PII with realistic fake data
  - Preserve null patterns from source data
  - Consistent identity generation (related name/email)
  - Support for 15+ PII types

- **Privacy Risk Scorer** (`privacy/risk_scorer.py`)
  - Uniqueness risk: detect quasi-identifier columns
  - Similarity risk: nearest-neighbor distance analysis
  - Outlier risk: detect reproducible extreme values
  - Overall risk level (low/medium/high) with recommendations

- **New API Endpoints:**
  - `POST /detect-pii` - Analyze CSV for PII columns
  - `GET /datasets/{id}/privacy-risk` - Privacy risk assessment
  - `GET /privacy/pii-types` - List supported PII types

- **Updated generate-from-csv:**
  - New parameters: `privacy_level`, `auto_detect_pii`, `anonymize_pii`
  - Privacy levels: standard, enhanced, strict
  - Automatic PII handling in enhanced/strict modes

- **Privacy Tests** - 15+ new tests for privacy features

### Changed
- Service now integrates PII detection and handling into synthesis workflow
- Quality reports include privacy metrics when privacy_level != standard
- Column info includes PII flags and types

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
