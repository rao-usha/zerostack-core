# Bug Fix: DataDictionary loadEntries is not defined

## Problem

When trying to manually update a column in the Data Dictionary UI, users got this error:

```
Failed to update entry: loadEntries is not defined
```

This error occurred after:
1. Clicking "Edit" on a column
2. Making changes
3. Clicking "Save" or "Save as New Version"

## Root Cause

The `DataDictionary.tsx` component has a function named `loadDictionary()` (line 138) that loads dictionary entries from the API.

However, two other functions were trying to call a non-existent function `loadEntries()`:

1. **`saveEntry()`** (line 218) - Called after saving edits
2. **`activateVersion()`** (line 256) - Called after activating a version

This was likely a refactoring oversight where the function was renamed but not all references were updated.

## Solution

**File**: `frontend/src/pages/DataDictionary.tsx`

### Fix 1: saveEntry function (line 218)

**Before**:
```typescript
const saveEntry = async (entryId: number, createNewVersion: boolean = false) => {
  try {
    setSaving(true)
    const updated = await updateDictionaryEntry(entryId, {
      ...editForm,
      create_new_version: createNewVersion,
      version_notes: createNewVersion ? versionNotes || 'Manual edit - new version' : undefined
    })
    
    // Reload entries to get updated version numbers
    await loadEntries()  // ❌ Function doesn't exist
    
    setEditingEntry(null)
    setEditForm({})
    setVersionNotes('')
  } catch (err: any) {
    console.error('Failed to update entry:', err)
    alert('Failed to update entry: ' + (err.response?.data?.detail || err.message))
  } finally {
    setSaving(false)
  }
}
```

**After**:
```typescript
const saveEntry = async (entryId: number, createNewVersion: boolean = false) => {
  try {
    setSaving(true)
    const updated = await updateDictionaryEntry(entryId, {
      ...editForm,
      create_new_version: createNewVersion,
      version_notes: createNewVersion ? versionNotes || 'Manual edit - new version' : undefined
    })
    
    // Reload entries to get updated version numbers
    await loadDictionary()  // ✅ Correct function name
    
    setEditingEntry(null)
    setEditForm({})
    setVersionNotes('')
  } catch (err: any) {
    console.error('Failed to update entry:', err)
    alert('Failed to update entry: ' + (err.response?.data?.detail || err.message))
  } finally {
    setSaving(false)
  }
}
```

### Fix 2: activateVersion function (line 256)

**Before**:
```typescript
const activateVersion = async (versionId: number) => {
  try {
    setSaving(true)
    await activateDictionaryVersion(versionId)
    
    // Reload entries
    await loadEntries()  // ❌ Function doesn't exist
    
    // Close modal
    setViewingVersions(null)
    setVersions([])
  } catch (err: any) {
    console.error('Failed to activate version:', err)
    alert('Failed to activate version: ' + (err.response?.data?.detail || err.message))
  } finally {
    setSaving(false)
  }
}
```

**After**:
```typescript
const activateVersion = async (versionId: number) => {
  try {
    setSaving(true)
    await activateDictionaryVersion(versionId)
    
    // Reload entries
    await loadDictionary()  // ✅ Correct function name
    
    // Close modal
    setViewingVersions(null)
    setVersions([])
  } catch (err: any) {
    console.error('Failed to activate version:', err)
    alert('Failed to activate version: ' + (err.response?.data?.detail || err.message))
  } finally {
    setSaving(false)
  }
}
```

## Impact

### Before Fix
- ❌ Editing columns in Data Dictionary UI failed
- ❌ Activating old versions failed
- ❌ Users got "loadEntries is not defined" error
- ❌ Changes were NOT saved to backend (API call succeeded, but UI error interrupted)

### After Fix
- ✅ Editing columns works correctly
- ✅ Save and "Save as New Version" both work
- ✅ Activating previous versions works
- ✅ UI refreshes to show updated data
- ✅ No JavaScript errors

## Testing

### Test 1: Edit and Save
1. Go to Data Dictionary
2. Select a table with documented columns
3. Click "Edit" on any column
4. Change the description
5. Click "Save"
6. **Expected**: Entry saves successfully, UI refreshes, no error

### Test 2: Save as New Version
1. Edit a column
2. Enter version notes
3. Click "Save as New Version"
4. **Expected**: New version created, version number increments, UI refreshes

### Test 3: Version History
1. Click "Version History" on a column
2. Click "Activate" on an older version
3. **Expected**: Old version becomes active, UI refreshes, modal closes

## Files Changed

- `frontend/src/pages/DataDictionary.tsx` (2 lines changed)
  - Line 218: `loadEntries()` → `loadDictionary()`
  - Line 256: `loadEntries()` → `loadDictionary()`

## Related Features

This fix enables the following workflows:
- Manual editing of LLM-generated documentation
- Creating new versions to track changes
- Rolling back to previous versions
- Viewing version history

---

**Status**: ✅ Fixed  
**Date**: 2026-01-01  
**Priority**: High (blocks core feature)  
**Breaking Changes**: None
