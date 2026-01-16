# Approval Workflow - Sanity Test Guide

## ✅ Pre-Flight Checks

### 1. Backend Status
```powershell
docker logs nex-backend-dev --tail 20
```
**Expected**: Should see `"Application startup complete"` with no errors

### 2. Frontend Status
```powershell
docker logs nex-frontend-dev --tail 10
```
**Expected**: Should see Vite dev server running

### 3. Database State Column
```powershell
docker exec nex_db_dev psql -U nex -d nex -c "SELECT state, COUNT(*) FROM data_dictionary_entries GROUP BY state;"
```
**Expected**: 
```
   state   | count 
-----------+-------
 published |   150
```

✅ **All 150 existing entries are published (correct!)**

---

## 🧪 UI Test Scenarios

### Test 1: State Badge Display (2 min)

**What**: Verify state badges are visible

**Steps**:
1. Open: `http://localhost:3000/data-dictionary`
2. Select: `explorer2` → `public` → `acs5_2021_b01001`
3. Scroll through column entries

**Expected**:
- ✅ Each entry shows a **green badge** saying "Published"
- ✅ Badge is next to the source badge (e.g., `llm_initial`)
- ✅ Version button shows (e.g., `v1`)

**Screenshot**:
```
geoid : character varying
[llm_initial] [Published] [v1] [Edit]
```

**✓ Pass** | **✗ Fail**

---

### Test 2: Create a Draft (3 min)

**What**: Edit an entry to create a draft

**Steps**:
1. Click **Edit** on the `geoid` column
2. Change business description to: `"Geographic Identifier - Census Block"`
3. Change technical description to: `"Primary key for geographic areas"`
4. Add tag: `"identifier"`
5. Click **Save** (not "Save as New Version")

**Expected**:
- ✅ Success message appears
- ✅ State badge changes: 🟢 **Published** → 🔵 **Draft**
- ✅ Version number increments: `v1` → `v2`
- ✅ **Edit** button still visible
- ✅ **Submit** button appears (yellow/amber color)

**Verify in UI**:
```
geoid : character varying
[human_edited] [Draft] [v2] [Edit] [Submit]
```

**✓ Pass** | **✗ Fail**

---

### Test 3: Submit for Approval (2 min)

**What**: Submit the draft for approval

**Steps**:
1. Find the `geoid` column (should be in Draft state)
2. Click the **Submit** button (yellow, with play icon)
3. Wait for alert

**Expected**:
- ✅ Alert: `"Entry submitted for approval"`
- ✅ State badge: 🔵 **Draft** → 🟡 **Pending Approval**
- ✅ **Edit** button disappears
- ✅ **Submit** button disappears
- ✅ **Approve** button appears (green, with checkmark)
- ✅ **Reject** button appears (red, with X)

**Verify in UI**:
```
geoid : character varying
[human_edited] [Pending Approval] [v2] [Approve] [Reject]
```

**✓ Pass** | **✗ Fail**

---

### Test 4: Approve Entry (2 min)

**What**: Approve a pending entry

**Steps**:
1. Find the `geoid` column (Pending Approval state)
2. Click **Approve** button (green)
3. When prompted, enter notes: `"Approved - good description"`
4. Click OK

**Expected**:
- ✅ Alert: `"Entry approved and published"`
- ✅ State badge: 🟡 **Pending Approval** → 🟢 **Published**
- ✅ **Approve/Reject** buttons disappear
- ✅ **Edit** button disappears (published is immutable)
- ✅ Only version history button remains

**Verify in UI**:
```
geoid : character varying
[human_edited] [Published] [v2] [Version History]
```

**✓ Pass** | **✗ Fail**

---

### Test 5: Reject Workflow (4 min)

**What**: Test rejection and rework flow

**Steps**:
1. Pick a different column (e.g., `name`)
2. Click **Edit**, change description to: `"Area name - needs more detail"`
3. Click **Save** → Creates Draft
4. Click **Submit** → Changes to Pending Approval
5. Click **Reject** button (red)
6. Enter reason: `"Please add examples and specify the format"`
7. Click OK

**Expected**:
- ✅ Alert: `"Entry rejected and returned to draft"`
- ✅ State badge: 🟡 **Pending Approval** → 🔵 **Draft**
- ✅ **Edit** button reappears
- ✅ **Submit** button reappears
- ✅ Can click Edit and modify the entry

**Now rework and resubmit**:
8. Click **Edit**
9. Update description: `"Area name - string format, e.g., 'Los Angeles County'"`
10. Click **Save**
11. Click **Submit** again

**Expected**:
- ✅ Can successfully resubmit after rejection
- ✅ State goes back to Pending Approval

**✓ Pass** | **✗ Fail**

---

### Test 6: Version History with States (3 min)

**What**: Verify version history shows state badges

**Steps**:
1. Click the version button on `geoid` (should say `v2`)
2. Modal opens

**Expected**:
- ✅ Modal title: "Version History"
- ✅ Shows subtitle: `public.acs5_2021_b01001.geoid`
- ✅ Lists all versions (v2, v1)
- ✅ Active version (v2) highlighted in green
- ✅ Active version shows green "Active" badge
- ✅ **Each version shows its state badge**:
  - v2 (active): [Published]
  - v1: [Published]
- ✅ Each version shows creation date
- ✅ Version notes visible
- ✅ Can see full content (description, tags, etc.)

**✓ Pass** | **✗ Fail**

---

### Test 7: Rollback to Previous Version (3 min)

**What**: Activate an older published version

**Steps**:
1. With version history modal open (from Test 6)
2. Find version v1 (the original)
3. Scroll down to see the **Activate** button
4. Click **Activate** on v1
5. Confirm if prompted
6. Modal closes

**Expected**:
- ✅ Modal closes
- ✅ Entry refreshes
- ✅ Content reverts to v1 description
- ✅ Version number increments: `v2` → `v3`
- ✅ State remains: 🟢 **Published**
- ✅ Re-open version history:
  - v3 is now active (pointing to v1 content)
  - v2 is inactive
  - v1 is inactive

**✓ Pass** | **✗ Fail**

---

### Test 8: Published Entry is Immutable (1 min)

**What**: Verify you can't edit published entries

**Steps**:
1. Find any entry with 🟢 **Published** state
2. Look for Edit button

**Expected**:
- ✅ **No Edit button** visible for published entries
- ✅ Only version history button available
- ✅ To edit, you'd need to rollback or wait for next AI update

**✓ Pass** | **✗ Fail**

---

## 🔧 API Test Scenarios

### Test 9: API Endpoint - Submit for Approval

**Run the test script**:
```powershell
.\test_approval_workflow.ps1
```

**Or manually**:
```powershell
# 1. Get an entry ID (find a draft)
$entries = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/?database_name=explorer2&active_only=true" -Method Get
$draftEntry = $entries | Where-Object { $_.state -eq "draft" } | Select-Object -First 1
$entryId = $draftEntry.id

# 2. Submit for approval
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/submit-for-approval" -Method Post
Write-Host "New state: $($result.state)"  # Should be "pending_approval"
```

**Expected**:
- ✅ Returns entry with `state: "pending_approval"`
- ✅ No errors in backend logs

**✓ Pass** | **✗ Fail**

---

### Test 10: API Endpoint - Approve Entry

```powershell
# Find a pending entry
$entries = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/?database_name=explorer2&active_only=true" -Method Get
$pendingEntry = $entries | Where-Object { $_.state -eq "pending_approval" } | Select-Object -First 1
$entryId = $pendingEntry.id

# Approve it
$body = @{ notes = "API test approval" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/approve" -Method Post -Body $body -ContentType "application/json"
Write-Host "New state: $($result.state)"  # Should be "published"
```

**Expected**:
- ✅ Returns entry with `state: "published"`
- ✅ Version notes include "Approved: API test approval"

**✓ Pass** | **✗ Fail**

---

### Test 11: API Endpoint - Reject Entry

```powershell
# Create a draft and submit it first, then:
$entryId = 123  # Replace with actual ID

$body = @{ notes = "Need more examples" } | ConvertTo-Json
$result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/reject" -Method Post -Body $body -ContentType "application/json"
Write-Host "New state: $($result.state)"  # Should be "draft"
```

**Expected**:
- ✅ Returns entry with `state: "draft"`
- ✅ Version notes include "Rejected: Need more examples"

**✓ Pass** | **✗ Fail**

---

### Test 12: Error Handling - Invalid State Transitions

**Test invalid transitions**:

```powershell
# Try to submit a published entry (should fail)
$publishedEntry = $entries | Where-Object { $_.state -eq "published" } | Select-Object -First 1
try {
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$($publishedEntry.id)/submit-for-approval" -Method Post
} catch {
    Write-Host "Expected error: $($_.Exception.Message)"
}
```

**Expected Errors**:
- ✅ Submit published → Error: "Can only submit draft entries"
- ✅ Approve draft → Error: "Can only approve pending entries"
- ✅ Reject published → Error: "Can only reject pending entries"

**✓ Pass** | **✗ Fail**

---

## 📊 Database Verification

### Test 13: Check State Distribution

```powershell
docker exec nex_db_dev psql -U nex -d nex -c "SELECT state, COUNT(*) as count, is_active FROM data_dictionary_entries GROUP BY state, is_active ORDER BY state, is_active;"
```

**Expected** (after running UI tests):
```
   state         | count | is_active 
-----------------+-------+-----------
 draft           |     1 |     t
 pending_approval|     1 |     t
 published       |   148 |     t
 published       |     2 |     f
```

**Explanation**:
- 1 draft entry (active)
- 1 pending approval entry (active)
- 148 published entries (active)
- 2 published entries (inactive - old versions)

**✓ Pass** | **✗ Fail**

---

### Test 14: Version Notes Tracking

```powershell
docker exec nex_db_dev psql -U nex -d nex -c "SELECT column_name, version_number, state, LEFT(version_notes, 50) as notes FROM data_dictionary_entries WHERE column_name = 'geoid' ORDER BY version_number DESC LIMIT 3;"
```

**Expected**:
```
 column_name | version_number |   state   |                  notes                  
-------------+----------------+-----------+----------------------------------------
 geoid       |              2 | published | Manual edit...Approved: Approved - good description
 geoid       |              1 | published | Initial documentation
```

**✓ Pass** | **✗ Fail**

---

## 🐛 Edge Case Tests

### Test 15: Multiple Transitions

**Scenario**: Draft → Pending → Reject → Draft → Pending → Approve → Published

**Steps**:
1. Edit a column → Draft
2. Submit → Pending
3. Reject → Back to Draft
4. Edit again
5. Submit → Pending
6. Approve → Published

**Expected**:
- ✅ All transitions work smoothly
- ✅ Version notes track all actions
- ✅ No errors at any stage

**✓ Pass** | **✗ Fail**

---

### Test 16: Concurrent Edits (Advanced)

**Scenario**: What happens if two users try to work on the same entry?

**Steps**:
1. Open Data Dictionary in two browser windows
2. In Window 1: Edit a column → Save as draft
3. In Window 2: Refresh → Try to edit the same column

**Expected**:
- ✅ Window 2 sees the draft state
- ✅ Cannot have two drafts of the same entry simultaneously
- ✅ Last save wins

**✓ Pass** | **✗ Fail**

---

## 📝 Test Results Summary

| Test # | Test Name | Status | Notes |
|--------|-----------|--------|-------|
| 1 | State Badge Display | ⏳ | |
| 2 | Create Draft | ⏳ | |
| 3 | Submit for Approval | ⏳ | |
| 4 | Approve Entry | ⏳ | |
| 5 | Reject Workflow | ⏳ | |
| 6 | Version History | ⏳ | |
| 7 | Rollback | ⏳ | |
| 8 | Published Immutable | ⏳ | |
| 9 | API Submit | ⏳ | |
| 10 | API Approve | ⏳ | |
| 11 | API Reject | ⏳ | |
| 12 | Error Handling | ⏳ | |
| 13 | Database State | ⏳ | |
| 14 | Version Notes | ⏳ | |
| 15 | Multiple Transitions | ⏳ | |
| 16 | Concurrent Edits | ⏳ | |

**Legend**: ✅ Pass | ❌ Fail | ⏳ Not Run

---

## 🚨 Common Issues & Fixes

### Issue: State badge not showing
**Fix**: Hard refresh browser (Ctrl+Shift+R)

### Issue: Buttons not appearing
**Fix**: Check browser console for errors. Verify frontend restarted.

### Issue: "Can only submit draft entries" error
**Fix**: Entry is not in draft state. Check current state badge.

### Issue: Edit button missing on draft
**Fix**: Entry might be pending or published. Check state badge.

### Issue: API returns 400 error
**Fix**: Check you're using the correct entry ID and state transition.

---

## ✅ Quick Smoke Test (5 min)

**Minimal test to verify everything works**:

1. ✅ Open Data Dictionary → See state badges
2. ✅ Edit a column → See Draft badge
3. ✅ Click Submit → See Pending Approval badge
4. ✅ Click Approve → See Published badge
5. ✅ Open version history → See state badges on each version

**If all 5 work** → ✅ Feature is working!

---

## 📊 Expected Test Results

After completing all tests, you should have:

- ✅ **16/16 tests passing**
- ✅ Multiple entries in different states (draft, pending, published)
- ✅ Version history tracking all state transitions
- ✅ No errors in backend/frontend logs
- ✅ Database shows correct state distribution

---

## 🎓 Next Steps After Testing

1. **Production Considerations**:
   - Add role-based permissions (who can approve?)
   - Implement email notifications
   - Add audit logging

2. **Optional Enhancements**:
   - Auto-publish after X days
   - Bulk approval/rejection
   - Approval workflow dashboard

3. **Documentation**:
   - Update user guide with workflow screenshots
   - Train data stewards on approval process
   - Document governance policies

---

**Ready to test?** Start with the Quick Smoke Test, then dive into individual scenarios! 🚀
