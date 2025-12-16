# Update: Create New Version on Edit ✅

## What Changed

You can now **create a new version** when editing dictionary entries, giving you full control over whether to update in place or preserve the current version.

---

## New UI Features

### Two Save Options

When editing a column in the Data Dictionary, you now have **two buttons**:

1. **"Save"** (green) - Updates the current version in place
2. **"New Version"** (purple) - Creates a new version and preserves the old one

### Version Notes Field

A new **Version Notes** input field appears at the top of the edit form:
- Optional text field
- Explains what changed in this version
- Only used when clicking "New Version"
- Helpful hint: "💡 Click 'New Version' to preserve current version and create a new one"

---

## How It Works

### Scenario 1: Update in Place (Default)
```
1. Click "Edit" on a column
2. Make your changes
3. Click "Save" (green button)
4. ✅ Current version updates, version number stays the same
```

**Use when**: Minor corrections, typo fixes, clarifications

### Scenario 2: Create New Version
```
1. Click "Edit" on a column
2. Make your changes
3. (Optional) Add version notes: "Updated based on new business requirements"
4. Click "New Version" (purple button)
5. ✅ New version created (v2, v3, etc.)
6. ✅ Old version preserved but deactivated
7. ✅ You can view/activate old version anytime via version history
```

**Use when**: Significant changes, different interpretations, want to keep history

---

## Backend Changes

### API Update (`dictionary_router.py`)

**New Request Fields**:
```python
class DictionaryEntryUpdate(BaseModel):
    business_name: Optional[str] = None
    business_description: Optional[str] = None
    technical_description: Optional[str] = None
    tags: Optional[List[str]] = None
    create_new_version: bool = False  # NEW
    version_notes: Optional[str] = None  # NEW
```

**Logic**:
- If `create_new_version=False` → Updates entry in place
- If `create_new_version=True`:
  1. Deactivates current version (`is_active=False`)
  2. Creates new version with `version_number + 1`
  3. New version becomes active
  4. Copies unchanged fields from old version
  5. Applies your edits to new version
  6. Sets `source="human_edited"`

---

## Frontend Changes

### State Management (`DataDictionary.tsx`)

**New State**:
```typescript
const [versionNotes, setVersionNotes] = useState<string>('')
```

**Updated Save Function**:
```typescript
const saveEntry = async (entryId: number, createNewVersion: boolean = false) => {
  const updated = await updateDictionaryEntry(entryId, {
    ...editForm,
    create_new_version: createNewVersion,
    version_notes: createNewVersion ? versionNotes || 'Manual edit - new version' : undefined
  })
  
  await loadEntries()  // Refresh to show new version number
  // ... cleanup
}
```

### UI Elements

**Version Notes Input** (appears when editing):
```tsx
<div style={{ /* purple background */ }}>
  <label>Version Notes (optional)</label>
  <input
    value={versionNotes}
    onChange={(e) => setVersionNotes(e.target.value)}
    placeholder="What changed? (used when saving as new version)"
  />
  <p>💡 Click "New Version" to preserve current version</p>
</div>
```

**Save Buttons**:
```tsx
{/* Update in place */}
<button onClick={() => saveEntry(column.id, false)}>
  <Save /> Save
</button>

{/* Create new version */}
<button onClick={() => saveEntry(column.id, true)}>
  <History /> New Version
</button>

<button onClick={cancelEditing}>
  <X /> Cancel
</button>
```

---

## User Experience Flow

### Example: Updating a Column Definition

**Initial State**: `users.email` is at version 1
- Business Description: "Email address"
- Source: `llm_initial`

**User Action 1**: Minor typo fix
1. Edit: Change to "Email address for user login"
2. Click **"Save"**
3. Result: Still version 1, description updated

**User Action 2**: Major rewrite
1. Edit: Change to "Primary contact email, used for authentication and notifications"
2. Add version notes: "Expanded definition to include all use cases"
3. Click **"New Version"**
4. Result:
   - Version 2 created (active)
   - Version 1 preserved (inactive)
   - Version badge shows "v2"
   - Can view/compare both in version history

**User Action 3**: Revert to simpler definition
1. Click "v2" badge → Opens version history
2. See version 1: "Email address for user login"
3. Click "Activate" on version 1
4. Result: Version 1 becomes active again

---

## Benefits

### 1. **Flexibility**
- Quick fixes don't clutter version history
- Significant changes are preserved
- You decide what's worth versioning

### 2. **Safety**
- Never lose your work
- Can always revert to previous versions
- Compare different interpretations

### 3. **Collaboration**
- Version notes explain changes
- Team can see evolution of definitions
- Easy to discuss which version is better

### 4. **AI Integration**
- When AI re-runs, it creates new version
- Your manual versions are preserved
- Can compare AI vs human definitions

---

## API Examples

### Update In Place
```bash
PATCH /api/v1/data-dictionary/42
{
  "business_description": "Updated description",
  "create_new_version": false
}
```

**Response**: Same entry ID, updated fields

### Create New Version
```bash
PATCH /api/v1/data-dictionary/42
{
  "business_description": "Completely new description",
  "create_new_version": true,
  "version_notes": "Rewrote based on stakeholder feedback"
}
```

**Response**: New entry with `id=43`, `version_number=2`, `is_active=true`

---

## Visual Guide

### Edit Form Layout

```
┌─────────────────────────────────────────────┐
│ 📝 Editing: user_email                      │
├─────────────────────────────────────────────┤
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 🟣 Version Notes (optional)             │ │
│ │ ┌─────────────────────────────────────┐ │ │
│ │ │ What changed? (used when saving...) │ │ │
│ │ └─────────────────────────────────────┘ │ │
│ │ 💡 Click "New Version" to preserve...  │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Business Name                               │
│ ┌─────────────────────────────────────────┐ │
│ │ User Email                              │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Business Description                        │
│ ┌─────────────────────────────────────────┐ │
│ │ Primary contact email for user...       │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ [🟢 Save] [🟣 New Version] [🔴 Cancel]      │
└─────────────────────────────────────────────┘
```

---

## Testing Checklist

✅ **Basic Editing**
- [x] "Save" button updates in place
- [x] Version number stays the same
- [x] Changes persist after refresh

✅ **New Version Creation**
- [x] "New Version" button creates new version
- [x] Version number increments (v1 → v2)
- [x] Old version preserved in history
- [x] Old version marked inactive
- [x] New version is active

✅ **Version Notes**
- [x] Optional field works
- [x] Notes saved with new version
- [x] Notes visible in version history
- [x] Default note if left empty

✅ **UI/UX**
- [x] Both buttons visible when editing
- [x] Buttons disabled while saving
- [x] Loading state shows "Saving..."
- [x] UI refreshes after save
- [x] Version badge updates to new number

✅ **Integration**
- [x] Works with version history modal
- [x] Can activate old versions
- [x] Version comparison still works
- [x] No conflicts with AI-generated versions

---

## Summary

You now have **full control** over versioning:

- **Quick edits** → Click "Save" (updates in place)
- **Significant changes** → Click "New Version" (preserves history)
- **Add context** → Fill in version notes
- **Never lose work** → All versions preserved
- **Easy comparison** → View history anytime

This gives you the best of both worlds: the simplicity of in-place updates when you need it, and the safety of versioning when it matters.

**Ready to use now!** 🎉


