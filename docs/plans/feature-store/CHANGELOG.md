# Feature Store - Changelog

All notable changes to the Feature Store feature will be documented in this file.

---

## [Unreleased]

### Planned
- Phase 1: Foundation - Schema, CRUD APIs
- Phase 2: Transformations - SQL/Python execution
- Phase 3: Serving - Batch, PIT joins
- Phase 4: UI - Catalog, builder
- Phase 5: Advanced - Online store, scheduling

---

## [0.1.0] - Planning Complete

### Added
- Comprehensive planning document (PLAN.md)
- Architecture design
- Database schema design
- API design
- Implementation roadmap (5 phases, ~10 days)

### Architecture Decisions
- **Offline Store**: PostgreSQL + feature_values table
- **Online Store**: Redis (optional, Phase 5)
- **Transformations**: SQL (primary) + Python (sandboxed)
- **Versioning**: Immutable versions, new version on update

### Key Features Planned
- Entity-centric feature definitions
- SQL and Python transformations
- Feature versioning
- Feature sets (grouping)
- Point-in-time joins for training
- Batch and online serving
- Feature statistics
- Lineage integration

---

## Implementation Log

### 2026-01-16 - Planning Document Created
- Created comprehensive planning document
- Defined 5-phase implementation roadmap
- Designed database schema (8 tables)
- Designed REST API (6 endpoint groups)
- Documented integration points

---

## Future Releases

### [0.2.0] - Foundation (Planned)
- [ ] Database migration
- [ ] Entity CRUD
- [ ] Feature definition CRUD
- [ ] Feature set CRUD
- [ ] Basic API endpoints

### [0.3.0] - Transformations (Planned)
- [ ] SQL transformer
- [ ] Python transformer (sandboxed)
- [ ] Feature computation jobs
- [ ] Value storage

### [0.4.0] - Serving (Planned)
- [ ] Batch serving
- [ ] Point-in-time joins
- [ ] Training data generation
- [ ] Feature statistics

### [0.5.0] - UI (Planned)
- [ ] Feature catalog page
- [ ] Feature detail page
- [ ] Feature builder (SQL/Python)
- [ ] Statistics visualization

### [1.0.0] - Full Release (Planned)
- [ ] Online store (Redis)
- [ ] Scheduled computation
- [ ] Lineage integration
- [ ] Notebook integration
- [ ] Documentation
