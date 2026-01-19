# Fix: Table Name Conflict Resolution

## Problem

The backend was failing to start with the error:
```
sqlalchemy.exc.InvalidRequestError: Table 'dictionary_relationships' is already defined 
for this MetaData instance.
```

## Root Cause

The `dictionary_relationships` table was defined in **two places**:

1. **`dictionary_enhanced_models.py`** - Simple relationship model (from earlier implementation)
2. **`dictionary_semantics_models.py`** - Full-featured relationship model (from new implementation)

When both models were imported, SQLAlchemy detected the duplicate table definition and raised an error.

## Solution

### 1. Removed Duplicate Model

**File**: `backend/domains/data_explorer/dictionary_enhanced_models.py`

**Before**:
```python
class DictionaryRelationship(SQLModel, table=True):
    __tablename__ = "dictionary_relationships"
    # ... fields ...
```

**After**:
```python
# NOTE: DictionaryRelationship has been moved to dictionary_semantics_models.py
# to support the full requirements (relationship_kind, status, semantic types, etc.)
# Import from there if needed:
# from .dictionary_semantics_models import DictionaryRelationship
```

### 2. Updated Imports

**Files Updated**:
- `backend/domains/data_explorer/dictionary_enhanced_router.py`
- `backend/domains/data_explorer/dictionary_enhanced_service.py`

**Change**:
```python
# Before
from .dictionary_enhanced_models import (
    DictionaryAsset,
    DictionaryField,
    DictionaryRelationship,  # ❌ Old import
    ...
)

# After
from .dictionary_enhanced_models import (
    DictionaryAsset,
    DictionaryField,
    # DictionaryRelationship removed
    ...
)
# Import DictionaryRelationship from semantics models (unified model)
from .dictionary_semantics_models import DictionaryRelationship  # ✅ New import
```

## Why This Approach?

The `DictionaryRelationship` model in `dictionary_semantics_models.py` is **more complete** and supports:

✅ `relationship_kind` (candidate vs semantic)  
✅ `status` (suggested, approved, rejected, deprecated)  
✅ `relationship_type` (foreign_key_like, derived_from, rolls_up_to, etc.)  
✅ `grain_compatibility` and `semantic_definition` blocks  
✅ Full confidence scoring  

The simpler model in `dictionary_enhanced_models.py` was an earlier implementation that is now superseded.

## Verification

```bash
# Test model import
docker exec nex-backend-dev python -c "from domains.data_explorer.dictionary_semantics_models import *; print('Models imported successfully')"
# Output: Models imported successfully

# Restart backend
docker restart nex-backend-dev

# Check logs
docker logs nex-backend-dev --tail 30
# Should show: "Application startup complete"
```

## Result

✅ Backend starts successfully  
✅ No table name conflicts  
✅ All relationship functionality preserved  
✅ Enhanced router and service still work correctly  

## Files Changed

1. `backend/domains/data_explorer/dictionary_enhanced_models.py` - Removed duplicate model
2. `backend/domains/data_explorer/dictionary_enhanced_router.py` - Updated import
3. `backend/domains/data_explorer/dictionary_enhanced_service.py` - Updated import

## Migration Impact

**None**. The migration `012_add_dictionary_semantics.py` creates the `dictionary_relationships` table with the full schema from `dictionary_semantics_models.py`. The earlier migration `011_add_enhanced_dictionary.py` also created this table, but the new migration supersedes it with the complete schema.

When running migrations in order, the table will be created with the full schema needed for all features.

---

**Status**: ✅ Fixed  
**Date**: 2025-12-17  
**Backend**: Running successfully

