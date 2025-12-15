# 🧪 Data Dictionary System - Test Guide

## Quick Test Procedure

Follow these steps to verify the Data Dictionary system is working correctly:

---

## ✅ Test 1: Verify Backend Setup

### Check Database Migration
```bash
docker exec nex-backend-dev alembic current
```
**Expected**: Should show `008_dictionary` as the current revision

### Check Prompt Recipes
```bash
docker exec nex-backend-dev python -c "
from sqlmodel import Session, select
from db_session import engine
from domains.data_explorer.db_models import PromptRecipe

with Session(engine) as s:
    recipes = s.exec(select(PromptRecipe)).all()
    print(f'Total recipes: {len(recipes)}')
    for r in recipes:
        if r.action_type == 'column_documentation':
            print(f'✓ Found: {r.name} (ID: {r.id})')
"
```
**Expected**: Should find "Column Documentation - Default v1" recipe

### Check API Endpoint
```bash
curl http://localhost:8000/api/v1/data-dictionary/ | jq
```
**Expected**: Returns JSON array (may be empty initially)

---

## ✅ Test 2: Run Column Documentation Job

### Via UI (Recommended)

1. **Navigate to Data Analysis**
   - Open: http://localhost:3000/analysis
   - Or click "Data Analysis" in sidebar

2. **Create New Job**
   - Click "New Analysis" button
   - Enter job name: "Test Dictionary Generation"

3. **Select Tables**
   - Choose database connection
   - Select 1-3 tables to analyze

4. **Select Analysis Type**
   - Check **"Column Documentation"** checkbox
   - Uncheck other analysis types (optional)

5. **Configure LLM**
   - Provider: OpenAI (or your preferred provider)
   - Model: gpt-4o (recommended)
   - Context: (optional) "E-commerce database for online store"

6. **Submit Job**
   - Click "Create Job"
   - Job appears in jobs list with status "pending"

7. **Monitor Progress**
   - Status changes: pending → running → completed
   - Progress bar shows 0% → 100%
   - Current stage updates during execution

8. **View Results**
   - Click on completed job
   - Scroll to "Column Documentation" section
   - Should see: "Successfully ingested N column definitions into data dictionary"

---

## ✅ Test 3: View Data Dictionary

### Via UI

1. **Navigate to Data Dictionary**
   - Open: http://localhost:3000/dictionary
   - Or click "Data Dictionary" in sidebar

2. **Verify Entries**
   - Should see entries grouped by schema and table
   - Each entry shows:
     - Column name
     - Business description
     - Technical description (if provided)
     - Data type
     - Example values
     - Tags (e.g., PII, metric, identifier)
     - Source: "llm_initial"

3. **Test Filters**
   - Use schema dropdown to filter
   - Use table dropdown to filter
   - Use search box to find specific columns

4. **Verify Content Quality**
   - Business descriptions should be plain language
   - Examples should match actual data
   - Tags should be relevant (PII, metric, timestamp, etc.)

### Via API

```bash
# List all entries
curl http://localhost:8000/api/v1/data-dictionary/ | jq

# Filter by schema
curl "http://localhost:8000/api/v1/data-dictionary/?schema_name=public" | jq

# Get specific table
curl http://localhost:8000/api/v1/data-dictionary/tables/default/public/users | jq

# Get formatted context for prompts
curl "http://localhost:8000/api/v1/data-dictionary/context/default/public?table_names=users,orders" | jq
```

---

## ✅ Test 4: Verify Ingestion Logic

### Test Upsert Behavior

1. **Run Initial Job**
   - Run column documentation on a table
   - Note the entry IDs and descriptions

2. **Run Again on Same Table**
   - Create another column documentation job
   - Select the same table
   - Run with different context or model

3. **Verify Update**
   - Check Data Dictionary page
   - Entries should be updated (not duplicated)
   - `updated_at` timestamp should be newer
   - Source should still be "llm_initial"

4. **Test Human Edit Protection**
   - Use API to update an entry:
   ```bash
   curl -X PATCH http://localhost:8000/api/v1/data-dictionary/1 \
     -H "Content-Type: application/json" \
     -d '{"business_description": "MANUALLY EDITED DESCRIPTION"}'
   ```
   - Verify source changes to "human_edited"
   - Run another column documentation job on same table
   - Verify manually edited entry is NOT overwritten

---

## ✅ Test 5: Frontend Integration

### Data Analysis Page

1. **Check Action Option**
   - Go to Data Analysis → New Analysis
   - Verify "Column Documentation" appears in analysis types
   - Icon should be a Book
   - Description: "Generate data dictionary with business descriptions"

2. **Check Job Results**
   - Run a column documentation job
   - View completed job details
   - Should show ingestion summary
   - Should show list of entries generated

### Data Dictionary Page

1. **Check Layout**
   - Header with Book icon
   - Title: "Data Dictionary"
   - Subtitle about AI-generated documentation

2. **Check Filters**
   - Schema dropdown (populated from entries)
   - Table dropdown (filtered by schema)
   - Search box

3. **Check Entry Display**
   - Grouped by schema → table
   - Each column shows all fields
   - Tags displayed as badges
   - Source indicator visible

4. **Check Empty State**
   - If no entries exist, should show helpful message
   - Prompt to run column documentation job

---

## ✅ Test 6: End-to-End Workflow

### Complete User Journey

1. **Start Fresh**
   - Clear existing dictionary entries (optional):
   ```sql
   TRUNCATE TABLE data_dictionary_entries;
   ```

2. **Analyze Database**
   - Create column documentation job
   - Select multiple tables (3-5)
   - Use meaningful context
   - Run with GPT-4o

3. **Review Results**
   - Check job completed successfully
   - View ingestion count
   - Navigate to Data Dictionary

4. **Explore Dictionary**
   - Browse all entries
   - Test filters and search
   - Verify quality of descriptions

5. **Refine Entries**
   - Identify any incorrect descriptions
   - Use API to update them
   - Verify source changes to "human_edited"

6. **Re-run Analysis**
   - Run another column documentation job
   - Same tables, different context
   - Verify human edits preserved
   - Verify AI entries updated

7. **Use in Future Work**
   - Get dictionary context via API
   - Include in custom prompts
   - Verify improved analysis quality

---

## 🐛 Troubleshooting

### Issue: No recipes found

**Solution**: Run seed script
```bash
docker exec nex-backend-dev python scripts/seed_prompt_recipes.py
```

### Issue: Job fails with parse error

**Possible causes**:
- LLM returned invalid JSON
- Model doesn't follow instructions well

**Solutions**:
- Use GPT-4o or Claude 3.5 Sonnet
- Check job error details
- Verify prompt recipe is correct

### Issue: Entries not appearing in dictionary

**Check**:
1. Job completed successfully?
2. Job result shows ingestion summary?
3. Check database directly:
```bash
docker exec nex-postgres-dev psql -U nex -d nex -c "SELECT COUNT(*) FROM data_dictionary_entries;"
```

### Issue: Frontend not showing entries

**Check**:
1. Backend API working?
   ```bash
   curl http://localhost:8000/api/v1/data-dictionary/
   ```
2. Browser console for errors
3. Network tab for failed requests

---

## 📊 Expected Results

### After First Run

- **Job Status**: Completed
- **Ingestion Count**: N entries (where N = total columns analyzed)
- **Dictionary Entries**: All columns from selected tables
- **Entry Quality**:
  - Business descriptions are plain language
  - Examples match actual data
  - Tags are relevant and accurate
  - Data types are correct

### After Multiple Runs

- **No Duplicates**: Same column = same entry (updated)
- **Human Edits Preserved**: Manually edited entries not overwritten
- **AI Updates Applied**: Non-edited entries get latest AI analysis
- **Audit Trail**: `updated_at` timestamps track changes

---

## ✨ Success Criteria

✅ **Backend**
- Migration applied successfully
- Prompt recipe exists in database
- API endpoints return data
- Ingestion pipeline works

✅ **Frontend**
- Column Documentation option visible
- Jobs can be created and run
- Data Dictionary page loads
- Entries display correctly

✅ **Integration**
- Jobs complete successfully
- Entries appear in dictionary
- Filters and search work
- Human edits preserved

✅ **Quality**
- Descriptions are meaningful
- Examples are accurate
- Tags are relevant
- No duplicates or errors

---

## 🎉 Next Steps After Testing

1. **Run on Production Tables**
   - Analyze your real database schema
   - Generate comprehensive dictionary

2. **Review and Refine**
   - Check AI-generated descriptions
   - Edit any incorrect entries
   - Add missing business context

3. **Use in Analysis**
   - Include dictionary context in prompts
   - Improve quality of other analyses
   - Build on persistent knowledge

4. **Share with Team**
   - Onboard new members using dictionary
   - Use as data documentation
   - Reference in data governance

---

## 📝 Test Checklist

- [ ] Backend migration applied (008_dictionary)
- [ ] Prompt recipe seeded
- [ ] API endpoints accessible
- [ ] Column Documentation option in UI
- [ ] Can create and run job
- [ ] Job completes successfully
- [ ] Entries ingested into database
- [ ] Data Dictionary page loads
- [ ] Entries display correctly
- [ ] Filters and search work
- [ ] Can update entries via API
- [ ] Human edits preserved on re-run
- [ ] No duplicate entries created
- [ ] Dictionary context API works

---

**Ready to test? Start with Test 1 and work your way through!** 🚀

