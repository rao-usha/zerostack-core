# Data Dictionary - All Columns Documentation Fix

## Problem

When generating data dictionary documentation using AI analysis, only **10 columns** were being documented even though tables like `acs5_2021_b01001` have **332 columns**.

### Root Cause

1. **Token Limit Too Low**: The LLM was configured with `max_tokens=8000` for column documentation, which is insufficient for tables with many columns. Each column requires ~150-200 tokens in JSON format.

2. **No Clear Instruction**: The prompt didn't explicitly emphasize documenting ALL columns, allowing the LLM to decide to sample.

## Solution

### 1. Dynamic Token Limit (backend/domains/data_explorer/job_service.py)

Changed from fixed 8000 tokens to dynamic calculation:

```python
if analysis_type == "column_documentation":
    # Estimate total columns across all tables
    total_columns = 0
    for table in table_data:
        if "profile" in table and "column_profiles" in table["profile"]:
            total_columns += len(table["profile"]["column_profiles"])
    
    # Each column needs ~200 tokens (JSON structure + description)
    estimated_tokens = (total_columns * 200) + 1000
    
    # Set token limit with minimum of 8000 and maximum of 100000
    token_limit = max(8000, min(100000, estimated_tokens))
```

**Result**: 
- For `acs5_2021_b01001` with 332 columns: `token_limit = 67,400`
- Ensures enough tokens for complete documentation

### 2. Enhanced Prompt Instructions (backend/domains/data_explorer/analysis_prompts.py)

Added explicit requirements:

```
⚠️ CRITICAL REQUIREMENTS:
1. Document ALL columns - do not skip any columns
2. If a table has 332 columns, your response must have 332 entries
3. Do not sample or summarize - document each column individually
```

## How to Use

### Generate Complete Documentation

1. Go to **Data Analysis** page
2. Select a table (e.g., `acs5_2021_b01001`)
3. Choose "Document Columns" analysis type
4. Click "Run Analysis"
5. Wait for completion
6. **All columns** will now be documented in the Data Dictionary

### Update Individual Columns

You can update any column individually in the Data Dictionary UI:

1. Go to **Data Dictionary** page
2. Navigate to your database → schema → table
3. Find the column you want to edit
4. Click the **"Edit"** button next to the column
5. Update any fields:
   - Business Name
   - Business Description
   - Technical Description
   - Tags
6. Choose to either:
   - **"Save"** - Update the current version
   - **"Save as New Version"** - Create a new version with notes

### Version History

Each column maintains a full version history:

1. Click **"Version History"** to see all past versions
2. Each version shows:
   - Version number
   - Changes made
   - Who made them
   - When they were made
   - Version notes
3. You can **activate** any previous version to roll back changes

## Expected Behavior

### Before Fix
- Table with 332 columns → 10 dictionary entries
- Incomplete documentation
- Large gaps in coverage

### After Fix
- Table with 332 columns → 332 dictionary entries
- Complete documentation
- All columns covered

## Performance Considerations

### Token Usage
- Small tables (< 50 columns): ~10,000 tokens
- Medium tables (50-150 columns): ~30,000 tokens
- Large tables (150+ columns): ~50,000-100,000 tokens

### Cost Impact
For a table with 332 columns:
- Input tokens: ~5,000 (schema + samples)
- Output tokens: ~67,000 (332 columns × ~200 tokens)
- **Total**: ~72,000 tokens per analysis

At typical pricing:
- Claude Sonnet 4: ~$0.15-0.20 per run
- GPT-4: ~$0.20-0.30 per run

### Time Impact
- Small tables: 5-10 seconds
- Medium tables: 15-30 seconds
- Large tables: 30-60 seconds

## Testing

To verify the fix works:

1. Run analysis on `acs5_2021_b01001`
2. Check dictionary entries:

```sql
SELECT COUNT(*) 
FROM data_dictionary_entries 
WHERE table_name = 'acs5_2021_b01001' 
AND is_active = true;
```

Expected: **332** (not 10)

3. Verify all columns present:

```sql
SELECT column_name 
FROM data_dictionary_entries 
WHERE table_name = 'acs5_2021_b01001' 
AND is_active = true
ORDER BY column_name;
```

## Future Enhancements

### Batching for Very Large Tables (1000+ columns)

If you encounter tables with 1000+ columns, we may need to implement batching:

```python
# Pseudo-code for future batching
if total_columns > 500:
    # Split into batches of 200 columns
    batches = split_columns_into_batches(table_data, batch_size=200)
    
    for batch in batches:
        # Document each batch separately
        entries = document_batch(batch)
        # Merge entries
```

### Incremental Updates

For tables that change frequently, implement incremental documentation:

```python
# Only document new/changed columns
new_columns = get_undocumented_columns(table)
if new_columns:
    document_columns(new_columns)
```

## Files Changed

1. `backend/domains/data_explorer/job_service.py`
   - Added dynamic token limit calculation for column_documentation
   - Lines 213-229

2. `backend/domains/data_explorer/analysis_prompts.py`
   - Enhanced prompt with explicit ALL columns requirement
   - Lines 436-450

## Migration Notes

**No database migration required** - this is a runtime fix only.

Existing dictionary entries remain valid. Re-running analysis will:
- Add missing columns
- Update existing descriptions (based on versioning settings)
- Maintain version history

## Support

If you encounter tables where not all columns are documented after this fix:

1. Check the analysis job logs for token limit warnings
2. Verify the table actually has columns in the database
3. Ensure the LLM response wasn't truncated
4. Check for JSON parsing errors in job results
