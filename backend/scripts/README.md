# Backend Scripts

This directory contains utility scripts for maintaining code quality and preventing common issues.

## Scripts

### `check_duplicate_tables.py`

**Purpose**: Detects duplicate SQLModel table definitions that would cause SQLAlchemy errors.

**Usage**:
```bash
cd backend
python scripts/check_duplicate_tables.py
```

**Exit Codes**:
- `0` - No duplicates found ✅
- `1` - Duplicates detected ❌

**Example Output**:
```
🔍 Checking for duplicate SQLModel table definitions...

📊 Found 45 table definitions across 42 unique tables

❌ ERROR: Duplicate table definition found: 'dictionary_relationships'
   Found in 2 locations:
   - domains/data_explorer/dictionary_enhanced_models.py:147
   - domains/data_explorer/dictionary_semantics_models.py:263

   SOLUTION: Keep only ONE definition of this table.
   If multiple models need it, import from a single source.

❌ FAILED: Duplicate table definitions detected!
```

**Integration**:
- ✅ Pre-commit hook (runs on commit)
- ✅ GitHub Actions (runs on PR)
- ✅ Pytest test (runs with test suite)

**When to Run**:
- Before committing model changes
- After merging branches with model changes
- When you see SQLAlchemy table registration errors

### Adding New Scripts

When adding new validation scripts:

1. Make them executable:
   ```bash
   chmod +x backend/scripts/your_script.py
   ```

2. Add shebang line:
   ```python
   #!/usr/bin/env python3
   ```

3. Document in this README

4. Add to pre-commit hooks if applicable:
   ```yaml
   # In .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: your-check
         name: Your Check
         entry: python backend/scripts/your_script.py
         language: system
   ```

5. Add test in `backend/tests/`:
   ```python
   def test_your_check():
       # Test your validation
       pass
   ```

## Related Files

- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `.github/workflows/check-duplicate-tables.yml` - CI/CD workflow
- `backend/tests/test_no_duplicate_tables.py` - Pytest integration
- `backend/CODING_RULES.md` - Detailed coding guidelines

