# Test script for approval workflow API
# Run this from the project root

Write-Host "=== Testing Approval Workflow API ===" -ForegroundColor Cyan
Write-Host ""

# 1. Get a dictionary entry
Write-Host "1. Fetching dictionary entries..." -ForegroundColor Yellow
$entries = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/?database_name=explorer2&schema_name=public&table_name=acs5_2021_b01001&active_only=true" -Method Get
$testEntry = $entries[0]
Write-Host "   Found entry: $($testEntry.column_name) (ID: $($testEntry.id), State: $($testEntry.state))" -ForegroundColor Green
Write-Host ""

# Store the entry ID
$entryId = $testEntry.id

# 2. Check current state
Write-Host "2. Current state: $($testEntry.state)" -ForegroundColor Yellow
Write-Host ""

# 3. Test based on current state
if ($testEntry.state -eq "draft") {
    Write-Host "3. Testing: Submit for Approval" -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/submit-for-approval" -Method Post
        Write-Host "   ✓ Success! New state: $($result.state)" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
} elseif ($testEntry.state -eq "pending_approval") {
    Write-Host "3a. Testing: Approve Entry" -ForegroundColor Yellow
    try {
        $body = @{ notes = "Test approval from API" } | ConvertTo-Json
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/approve" -Method Post -Body $body -ContentType "application/json"
        Write-Host "   ✓ Success! New state: $($result.state)" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "3b. Alternative: Test Reject (commented out to avoid conflicts)" -ForegroundColor Gray
    # Uncomment to test reject instead:
    # $body = @{ notes = "Test rejection from API" } | ConvertTo-Json
    # $result = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/data-dictionary/$entryId/reject" -Method Post -Body $body -ContentType "application/json"
} elseif ($testEntry.state -eq "published") {
    Write-Host "3. Entry is published (immutable)" -ForegroundColor Cyan
    Write-Host "   To test workflow, first edit it from the UI to create a draft." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - Check the UI at http://localhost:3000/data-dictionary"
Write-Host "  - Verify the state badge updated"
Write-Host "  - Check version history"
