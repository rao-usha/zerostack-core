# Data Dictionary Approval Workflow

## Overview

The Data Dictionary now includes a **Draft → Pending Approval → Published** workflow that allows you to manage dictionary entries through a formal approval process.

---

## State Machine

```
┌─────────┐
│  Draft  │ (Working copy - can edit freely)
└─────────┘
     │
     │ Submit for Approval
     ↓
┌──────────────────┐
│ Pending Approval │ (Under review - cannot edit)
└──────────────────┘
     │         │
     │ Approve │ Reject
     ↓         ↓
┌───────────┐ ┌─────────┐
│ Published │ │  Draft  │ (Rework and resubmit)
│ (immutable)│ └─────────┘
└───────────┘
     │
     │ Rollback (via version history)
     ↓
┌───────────┐
│ Published │ (Previous version becomes active)
│ (v1)      │
└───────────┘
```

---

## States

### 1. **Draft** 🔵
- **Color**: Blue
- **Editable**: ✅ Yes
- **Actions Available**:
  - **Edit**: Modify business name, description, technical details, and tags
  - **Submit for Approval**: Move to pending approval state

**When to use**: Working on new documentation, making updates, or after a rejection.

---

### 2. **Pending Approval** 🟡
- **Color**: Yellow/Amber
- **Editable**: ❌ No
- **Actions Available**:
  - **Approve**: Publish the entry (makes it immutable and visible to all)
  - **Reject**: Return to draft state for rework

**When to use**: Entry is ready for review by a data steward or governance team.

---

### 3. **Published** 🟢
- **Color**: Green
- **Editable**: ❌ No (immutable)
- **Actions Available**:
  - **View Version History**: See all historical versions
  - **Rollback**: Activate a previous published version

**When to use**: Approved and finalized documentation that is visible to all users.

---

## User Journey

### Scenario 1: Creating New Documentation

1. **AI generates initial documentation** → Created as `published` (auto-approved for AI-generated content)
2. **User edits a column** → Creates new version as `draft`
3. **User clicks "Submit"** → State changes to `pending_approval`
4. **Approver reviews** → Clicks "Approve" → State changes to `published`

---

### Scenario 2: Rejected Entry

1. **User submits draft** → State: `pending_approval`
2. **Approver finds issues** → Clicks "Reject" with reason
3. **Entry returns to** → State: `draft`
4. **User makes corrections** → Edits the entry
5. **User resubmits** → State: `pending_approval`
6. **Approver approves** → State: `published`

---

### Scenario 3: Rolling Back

1. **Published version has errors** → User notices mistake
2. **User opens version history** → Sees all versions
3. **User clicks "Activate" on previous version** → Old version becomes active
4. **Current version** → Remains as inactive published version
5. **User can edit again** → Creates new draft for corrections

---

## UI Guide

### Dictionary Entry Display

Each column entry now shows:

- **Column Name**: `geoid`
- **Data Type**: `character varying`
- **Source Badge**: `llm_initial` or `human_edited`
- **State Badge**: Color-coded state indicator
- **Version Button**: View version history
- **Action Buttons** (state-dependent):
  - **Draft**: Edit, Submit
  - **Pending**: Approve, Reject
  - **Published**: (view only)

---

### Version History

When you click the version number button:

- See all versions with their states
- Active version highlighted in green
- Each version shows:
  - Version number
  - State badge
  - Active indicator (if current)
  - Created date
  - Version notes
  - Full content (business name, description, etc.)
  - **Rollback button** for inactive published versions

---

## API Endpoints

### Workflow Actions

```http
POST /api/v1/data-dictionary/{entry_id}/submit-for-approval
```
- **Requires**: Entry state = `draft`
- **Result**: Entry state → `pending_approval`

```http
POST /api/v1/data-dictionary/{entry_id}/approve
Body: { "notes": "Looks good!" }
```
- **Requires**: Entry state = `pending_approval`
- **Result**: Entry state → `published`

```http
POST /api/v1/data-dictionary/{entry_id}/reject
Body: { "notes": "Please add more details" }
```
- **Requires**: Entry state = `pending_approval`
- **Result**: Entry state → `draft`

```http
POST /api/v1/data-dictionary/{entry_id}/publish
Body: { "notes": "Auto-approved" }
```
- **Requires**: Entry state = `draft`
- **Result**: Entry state → `published`
- **Use case**: Admin override, auto-approval for trusted sources

---

## Backend Implementation

### Database Schema

**New Column**: `data_dictionary_entries.state`
- **Type**: `VARCHAR(50)`
- **Default**: `'draft'`
- **Index**: Yes (for filtering by state)
- **Values**: `'draft'`, `'pending_approval'`, `'published'`

**Migration**: All existing entries are set to `'published'` for backward compatibility.

---

### Service Functions

**File**: `backend/domains/data_explorer/dictionary_service.py`

```python
def submit_for_approval(session: Session, entry_id: int) -> DataDictionaryEntry:
    """Submit a draft entry for approval."""
    # Changes state from 'draft' to 'pending_approval'

def approve_entry(session: Session, entry_id: int, approver_notes: str = None) -> DataDictionaryEntry:
    """Approve a pending entry and publish it."""
    # Changes state from 'pending_approval' to 'published'

def reject_entry(session: Session, entry_id: int, rejection_reason: str = None) -> DataDictionaryEntry:
    """Reject a pending entry and return it to draft state."""
    # Changes state from 'pending_approval' back to 'draft'

def publish_draft_directly(session: Session, entry_id: int, publish_notes: str = None) -> DataDictionaryEntry:
    """Publish a draft entry directly without approval workflow."""
    # Changes state from 'draft' to 'published' (admin override)
```

---

### Router Endpoints

**File**: `backend/domains/data_explorer/dictionary_router.py`

All workflow endpoints follow the pattern:
- **POST** `/api/v1/data-dictionary/{entry_id}/{action}`
- **Request**: Optional notes in body
- **Response**: Updated `DictionaryEntry` with new state
- **Errors**: 400 if invalid state transition

---

## Frontend Implementation

### Components Updated

**File**: `frontend/src/pages/DataDictionary.tsx`

**New Functions**:
- `handleSubmitForApproval(entryId)`: Submit draft for approval
- `handleApprove(entryId)`: Approve pending entry
- `handleReject(entryId)`: Reject pending entry
- `handlePublish(entryId)`: Direct publish (admin)
- `renderStateBadge(state)`: Render color-coded state badge

**UI Changes**:
1. **State badge** added next to source badge
2. **Workflow buttons** conditionally rendered based on state:
   - **Draft** → Edit, Submit buttons
   - **Pending** → Approve, Reject buttons
   - **Published** → View-only (no edit button)
3. **Version history** now shows state badge for each version

---

### API Client Functions

**File**: `frontend/src/api/client.ts`

```typescript
export const submitForApproval = async (entryId: number): Promise<DictionaryEntry>
export const approveEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry>
export const rejectEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry>
export const publishEntry = async (entryId: number, notes?: string): Promise<DictionaryEntry>
```

---

## Testing Guide

### Manual Testing Workflow

**Prerequisites**:
- Backend running: `docker restart nex-backend-dev`
- Frontend running: `docker restart nex-frontend-dev`
- Sample data: At least one dictionary entry

---

### Test Case 1: Submit for Approval

1. Navigate to **Data Dictionary**
2. Select a database/schema/table
3. Find a column with state = `draft`
4. Click **Edit**, make a change, click **Save**
5. Click **Submit** button
6. ✅ **Expected**: State badge changes to `Pending Approval` (yellow)
7. ✅ **Expected**: Edit button disappears
8. ✅ **Expected**: Approve and Reject buttons appear

---

### Test Case 2: Approve Entry

1. Find a column with state = `pending_approval`
2. Click **Approve** button
3. Enter approval notes (optional) when prompted
4. Click OK
5. ✅ **Expected**: State badge changes to `Published` (green)
6. ✅ **Expected**: Approve and Reject buttons disappear
7. ✅ **Expected**: Entry is now immutable

---

### Test Case 3: Reject Entry

1. Find a column with state = `pending_approval`
2. Click **Reject** button
3. Enter rejection reason when prompted (e.g., "Please add more examples")
4. Click OK
5. ✅ **Expected**: State badge changes to `Draft` (blue)
6. ✅ **Expected**: Edit and Submit buttons reappear
7. ✅ **Expected**: Version notes show rejection reason

---

### Test Case 4: Version History

1. Click the version number button (e.g., `v2`) on any column
2. ✅ **Expected**: Modal opens showing all versions
3. ✅ **Expected**: Each version shows its state badge
4. ✅ **Expected**: Active version is highlighted in green
5. For an inactive published version, click **Activate**
6. ✅ **Expected**: Modal closes, that version becomes active
7. ✅ **Expected**: Version number increments

---

### Test Case 5: Edit After Approval

1. Find a column with state = `published`
2. ✅ **Expected**: No Edit button available
3. Open version history
4. Click **Activate** on a previous version
5. ✅ **Expected**: That version becomes active
6. Now create a new edit:
   - Since published is immutable, you'd need to create a new entry manually or through chat

---

## Future Enhancements (Optional)

### Auto-Approval After X Days

**Configuration**:
```python
# In settings
DICTIONARY_AUTO_APPROVE_DAYS = 7  # Auto-publish drafts after 7 days of no changes
```

**Implementation**:
- Background job runs daily
- Finds drafts with `updated_at` > 7 days ago
- Calls `publish_draft_directly(entry_id, notes="Auto-approved after 7 days")`
- Optional: Filter by table/schema-level settings

---

### Approval Roles

**Future State**:
- Add `approved_by` and `rejected_by` fields
- Track who performed workflow actions
- Implement role-based permissions (e.g., only "data_stewards" can approve)

---

### Email Notifications

**Triggers**:
- Entry submitted for approval → Email to approvers
- Entry approved → Email to creator
- Entry rejected → Email to creator with reason

---

## Files Changed

### Backend

1. `backend/domains/data_explorer/db_models.py`
   - Added `state: str` field to `DataDictionaryEntry`

2. `backend/domains/data_explorer/dictionary_service.py`
   - Added `submit_for_approval()`
   - Added `approve_entry()`
   - Added `reject_entry()`
   - Added `publish_draft_directly()`

3. `backend/domains/data_explorer/dictionary_router.py`
   - Added `state` to `DictionaryEntryResponse`
   - Added workflow endpoints:
     - `POST /{entry_id}/submit-for-approval`
     - `POST /{entry_id}/approve`
     - `POST /{entry_id}/reject`
     - `POST /{entry_id}/publish`

4. `backend/migrations/versions/013_add_dictionary_state_workflow.py`
   - New migration (applied directly to DB)

---

### Frontend

1. `frontend/src/api/client.ts`
   - Added `state` to `DictionaryEntry` interface
   - Added workflow API functions

2. `frontend/src/pages/DataDictionary.tsx`
   - Added workflow action handlers
   - Added `renderStateBadge()` helper
   - Updated column display to show state badge
   - Updated button rendering based on state
   - Updated version history to show state badges

---

### Documentation

1. `DICTIONARY_APPROVAL_WORKFLOW.md` (this file)
   - Complete user guide and technical documentation

---

## Troubleshooting

### "Can only submit draft entries"

**Cause**: Trying to submit an entry that is already `pending_approval` or `published`.

**Solution**: Check current state. If published, you cannot edit it. Use version history to rollback or create a new draft.

---

### "Can only approve pending entries"

**Cause**: Trying to approve an entry that is not `pending_approval`.

**Solution**: Entry must be submitted for approval first.

---

### State badge not updating

**Cause**: Frontend cache not refreshed.

**Solution**: Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)

---

### Edit button missing

**Cause**: Entry state is `pending_approval` or `published`.

**Solution**: 
- **If pending**: Wait for approval or rejection
- **If published**: Entry is immutable. Use version history to activate an older version if needed.

---

## Summary

✅ **Implemented**:
- 3-state workflow: Draft → Pending Approval → Published
- State badges with color coding
- Workflow action buttons (Submit, Approve, Reject)
- Version history shows state for each version
- Backend API endpoints
- Database migration

✅ **Benefits**:
- **Quality Control**: Human review before publishing
- **Audit Trail**: Version history tracks all changes and states
- **Rollback**: Easily revert to previous published versions
- **Immutability**: Published entries cannot be accidentally modified

🚀 **Ready to Test**: Refresh your browser and navigate to the Data Dictionary!

---

**Status**: ✅ Complete  
**Date**: 2026-01-01  
**Backend**: Running  
**Frontend**: Running  
**Database**: Updated
