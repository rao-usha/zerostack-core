# Nex Backend Coding Rules

## 🚨 Critical Rules (Will Break the Build)

### 1. No Duplicate Table Definitions

**Rule**: Each SQLModel table (`table=True`) must be defined in **exactly one file**.

**Why**: SQLAlchemy registers tables globally. Defining the same `__tablename__` twice causes:
```
sqlalchemy.exc.InvalidRequestError: Table 'xxx' is already defined for this MetaData instance.
```

**✅ DO**:
```python
# File: domains/data_explorer/models.py
class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int
    name: str

# File: domains/auth/service.py
from domains.data_explorer.models import User  # Import, don't redefine
```

**❌ DON'T**:
```python
# File: domains/data_explorer/models.py
class User(SQLModel, table=True):
    __tablename__ = "users"
    # ...

# File: domains/auth/models.py
class User(SQLModel, table=True):  # ❌ ERROR: Duplicate definition
    __tablename__ = "users"
    # ...
```

**Enforcement**:
- Automated check: `python scripts/check_duplicate_tables.py`
- Pre-commit hook: Runs automatically on commit
- CI/CD: GitHub Actions workflow blocks merges
- Test: `pytest tests/test_no_duplicate_tables.py`

**How to Check Manually**:
```bash
cd backend
python scripts/check_duplicate_tables.py
```

### 2. Table Naming Conventions

**Rule**: Use snake_case for table names and avoid generic names.

**✅ Good table names**:
- `data_dictionary_entries`
- `analysis_jobs`
- `ml_model_versions`
- `user_preferences`

**❌ Bad table names**:
- `data` (too generic)
- `DataDictionaryEntries` (not snake_case)
- `dict_entries` (unclear abbreviation)

### 3. Model Organization

**Rule**: Organize models by domain, one domain per directory.

**Structure**:
```
domains/
├── data_explorer/
│   ├── db_models.py           # Data dictionary, analysis results
│   ├── job_models.py          # Analysis jobs
│   ├── metadata_models.py     # Metadata
│   └── dictionary_semantics_models.py  # Semantics, relationships
├── chat/
│   └── models.py              # Chat messages, sessions
├── ml_development/
│   └── models.py              # ML models, experiments
└── auth/
    └── models.py              # Users, permissions
```

**Rule**: If a table is used by multiple domains, put it in the **primary owner domain** and import elsewhere.

**Example**:
- `dictionary_entries` lives in `data_explorer/dictionary_semantics_models.py`
- Other modules import it: `from domains.data_explorer.dictionary_semantics_models import DictionaryEntry`

### 4. Avoiding Circular Imports

**Rule**: Import models, don't redefine them.

If you need a model from another domain:
```python
# ✅ Correct
from domains.data_explorer.dictionary_semantics_models import DictionaryEntry

# ❌ Wrong - creates circular dependency
from .. import DictionaryEntry
```

**Tip**: Use `TYPE_CHECKING` for type hints to avoid runtime imports:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domains.data_explorer.models import User

def process_user(user: "User") -> None:  # String annotation
    pass
```

## 📋 Best Practices

### Model Definition

1. **Always include `__tablename__`**:
   ```python
   class MyModel(SQLModel, table=True):
       __tablename__ = "my_models"  # Explicit is better than implicit
   ```

2. **Use UUIDs for distributed systems**:
   ```python
   id: Optional[UUID] = SQLField(
       default_factory=uuid4,
       sa_column=Column(PG_UUID(as_uuid=True), primary_key=True)
   )
   ```

3. **Add indexes for foreign keys**:
   ```python
   user_id: UUID = SQLField(sa_column=Column(PG_UUID(as_uuid=True), index=True))
   ```

4. **Document complex models**:
   ```python
   class ComplexModel(SQLModel, table=True):
       """
       Complex model for XYZ feature.
       
       Relationships:
       - One-to-many with Users via user_id
       - Many-to-many with Tags via junction table
       
       Indexes:
       - Composite index on (tenant_id, created_at) for efficient queries
       """
       __tablename__ = "complex_models"
   ```

### Migration Rules

1. **One feature, one migration**
2. **Always test migrations up and down**:
   ```bash
   alembic upgrade head
   alembic downgrade -1
   alembic upgrade head
   ```

3. **Include indexes in migrations**:
   ```python
   op.create_index('ix_users_email', 'users', ['email'], unique=True)
   ```

4. **Never modify old migrations** - create a new one instead

## 🛠️ Tools and Commands

### Check for Issues

```bash
# Check for duplicate tables
python scripts/check_duplicate_tables.py

# Run all pre-commit checks
pre-commit run --all-files

# Run linting
black backend/
isort backend/
flake8 backend/

# Run tests including duplicate check
pytest backend/tests/test_no_duplicate_tables.py -v
```

### Set Up Pre-Commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Now checks run automatically on commit
```

## 🔧 Fixing Duplicate Tables

If you encounter a duplicate table error:

1. **Find the duplicates**:
   ```bash
   python scripts/check_duplicate_tables.py
   ```

2. **Decide which definition to keep**:
   - Keep the most complete/feature-rich version
   - Keep the one in the primary domain
   - Document the decision

3. **Remove duplicates**:
   ```python
   # Option 1: Delete and import
   # from .other_models import MyTable
   
   # Option 2: Add comment explaining removal
   # NOTE: MyTable has been moved to other_models.py
   # Import from there: from .other_models import MyTable
   ```

4. **Update imports**:
   ```python
   # Update all files that used the old location
   from domains.data_explorer.dictionary_semantics_models import DictionaryEntry
   ```

5. **Test**:
   ```bash
   pytest backend/tests/test_no_duplicate_tables.py
   ```

## 📚 Reference

- SQLModel docs: https://sqlmodel.tiangolo.com/
- SQLAlchemy docs: https://docs.sqlalchemy.org/
- Alembic docs: https://alembic.sqlalchemy.org/

## ✅ Checklist for New Models

Before creating a new SQLModel table:

- [ ] Checked if table already exists: `python scripts/check_duplicate_tables.py`
- [ ] Used unique, descriptive snake_case table name
- [ ] Added proper indexes on foreign keys and common query fields
- [ ] Created Alembic migration
- [ ] Added docstring explaining the model's purpose
- [ ] Ran duplicate check: `python scripts/check_duplicate_tables.py`
- [ ] Ran tests: `pytest tests/test_no_duplicate_tables.py`
- [ ] Documented any cross-domain dependencies

---

**Last Updated**: 2025-12-17
**Enforcement Level**: 🔴 Critical - Breaks build if violated

