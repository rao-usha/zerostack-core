# Prompt Library - Complete Implementation! 🎨

## Overview

Fully implemented the **Prompt Library** - a comprehensive UI for managing, editing, cloning, and organizing all analysis prompt recipes with default recipe management.

---

## 📍 Where to Edit Prompts

You now have **TWO ways** to edit prompts:

### 1. **Prompt Library** (Main Interface)
**Location**: Data Analysis page → "Prompt Library" tab

**Features**:
- View all recipes grouped by analysis type
- Create new recipes from scratch
- Edit existing recipes
- Clone recipes
- Delete recipes
- Set default recipe per analysis type
- See which recipes are system vs user-created

### 2. **From Job Details** (Quick Iteration)
**Location**: Job Details → "Re-run with Different Prompt" button

**Features**:
- Edit prompts used in a specific job
- Save edited prompts as new recipe
- Re-run analysis with modified prompts

---

## 🎨 Prompt Library Features

### Tab Navigation
Navigate between:
- **Analysis Jobs** - Existing tab for running and viewing jobs
- **Prompt Library** - New tab for managing recipes

### Recipe List View

**Grouping**: Recipes are grouped by analysis action type:
- Data Profiling
- Data Quality Checks
- Outlier & Anomaly Detection
- Relationship Analysis
- Trend & Time-Series Analysis
- Pattern Discovery

**For Each Recipe**, you can see:
- Name
- Default badge (if it's the default for its type)
- System badge (if it's a seed recipe)
- Default provider/model (if set)
- Last updated date

**Actions Available**:
- ⭐ **Set as Default** - Make this recipe the default for its analysis type
- ✏️ **Edit** - Modify recipe content
- 📋 **Clone** - Create a copy to customize
- 🗑️ **Delete** - Remove recipe (with confirmation)

### Recipe Editor

**Creating New Recipe**:
1. Click "New Recipe" button in Prompt Library
2. Fill in form fields:
   - Recipe Name *
   - Analysis Action Type *
   - Default Provider (optional)
   - Default Model (optional)
   - Make default checkbox
   - System Message *
   - User Message Template *
3. Click "Create Recipe"

**Editing Existing Recipe**:
1. Click "Edit" button on any recipe
2. Modify fields (action type cannot be changed)
3. Click "Update Recipe"

**Form Fields**:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Display name for the recipe |
| Action Type | Yes | Which analysis this applies to (locked when editing) |
| Default Provider | No | Suggested LLM provider (openai, anthropic, google, xai) |
| Default Model | No | Suggested model name |
| Make Default | No | Set as default recipe for this action type |
| System Message | Yes | Defines AI's role and constraints |
| User Template | Yes | Instructions with `{{schema_summary}}` and `{{sample_rows}}` placeholders |

---

## 🔧 Technical Implementation

### Backend Changes

#### 1. Enhanced CRUD API

**File**: `backend/domains/data_explorer/prompt_recipes_router.py`

**New Features**:
- **Default Management**: Only one recipe can be default per `action_type`
- **Clone Endpoint**: `POST /prompt-recipes/{id}/clone`
- **Protected Deletes**: Seed recipes require `force=true` flag

**New Endpoints**:
```python
POST   /api/v1/data-explorer/prompt-recipes/{id}/clone  # Clone recipe
DELETE /api/v1/data-explorer/prompt-recipes/{id}?force=true  # Force delete
```

**Metadata Fields**:
```json
{
  "is_default": true,        // Only one per action_type
  "source": "seed|user",     // Origin of recipe
  "cloned_from": 123,        // If cloned, original ID
  "version": "1.0",
  "created_by": "system"
}
```

#### 2. Default Recipe Logic

When `is_default` is set to `true`:
1. Find all recipes with same `action_type`
2. Set their `is_default` to `false`
3. Set current recipe's `is_default` to `true`

This ensures only ONE default per action type.

### Frontend Changes

#### 1. New Components

**`PromptLibrary.tsx`** (336 lines):
- Main library interface
- Recipe listing grouped by action type
- Delete confirmation modal
- Integrates with RecipeEditor

**`RecipeEditor.tsx`** (272 lines):
- Full-featured form for creating/editing recipes
- Validation (name, system message, user template required)
- Default checkbox management
- Template placeholder hints

#### 2. Updated DataAnalysis Page

**Tab System**:
```typescript
const [activeTab, setActiveTab] = useState<'jobs' | 'prompts'>('jobs')
```

**Navigation**:
- Two tabs at top: "Analysis Jobs" | "Prompt Library"
- Existing job views wrapped in `{activeTab === 'jobs' && <> ... </>}`
- New prompts view: `{activeTab === 'prompts' && <PromptLibrary />}`

**Quick Access Link**:
Added "Manage Recipes →" link in job creation form next to recipe dropdown

#### 3. Updated API Client

**New Functions**:
```typescript
export const clonePromptRecipe = async (recipeId: number)
export const deletePromptRecipe = async (recipeId: number, force: boolean)
```

---

## 🎯 User Workflows

### Workflow 1: Create Custom Recipe

```
1. Go to Data Analysis
2. Click "Prompt Library" tab
3. Click "New Recipe"
4. Fill in form:
   - Name: "Healthcare Data Profiling v1"
   - Action Type: Data Profiling
   - System Message: Custom healthcare context
   - User Template: Add HIPAA compliance checks
   - Check "Make default"
5. Click "Create Recipe"
6. Recipe is now the default for Data Profiling!
```

### Workflow 2: Clone and Customize

```
1. Go to Prompt Library
2. Find "Data Profiling - Default v1"
3. Click "Clone" (📋 icon)
4. Recipe copied as "Data Profiling - Default v1 (copy)"
5. Click "Edit" on the copy
6. Customize for your use case
7. Set as default if desired
8. Save
```

### Workflow 3: Edit from Job

```
1. Complete an analysis job
2. Review results
3. Click "Re-run with Different Prompt"
4. Edit system/user messages
5. Check "Save as new prompt recipe"
6. Enter name: "Custom Quality Checks v2"
7. Click "Re-run Analysis"
8. New recipe created AND new job started
```

### Workflow 4: Manage Defaults

```
1. Go to Prompt Library
2. See recipes grouped by type
3. Find recipe you want as default
4. Click "Set as Default" (⭐ icon)
5. Recipe now has "Default" badge
6. Previous default loses badge
7. New analyses use this recipe automatically
```

---

## 🔒 Access Control & Safety

### Protected Operations

**Seed Recipe Deletion**:
- Seed recipes (metadata.source === "seed") are protected
- Attempting to delete shows error
- Must use `force=true` flag to delete

**Default Recipe**:
- Cannot have multiple defaults per action type
- Backend enforces this rule
- Frontend shows current default with star badge

### Validation

**Backend**:
- Name required
- System message required
- User template required
- Action type must be valid

**Frontend**:
- Real-time validation
- Submit button disabled if invalid
- Clear error messages

---

## 📊 Data Model

### PromptRecipe Table

```sql
CREATE TABLE prompt_recipes (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    action_type VARCHAR(100) NOT NULL,  -- Index
    default_provider VARCHAR(50),        -- Index
    default_model VARCHAR(100),
    system_message TEXT NOT NULL,
    user_template TEXT NOT NULL,
    recipe_metadata JSONB,  -- Contains is_default, source, etc.
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### Recipe Metadata Schema

```typescript
{
  is_default?: boolean       // True if default for action_type
  source?: 'seed' | 'user'   // Origin of recipe
  cloned_from?: number       // Original recipe ID if cloned
  version?: string           // Version identifier
  created_by?: string        // User/system identifier
  description?: string       // Additional notes
  tags?: string[]            // Categorization
}
```

---

## 🎨 UI Design

### Color Scheme

**Default Recipe**:
- Border: `#a8d8ff` (blue)
- Badge: Blue background

**Normal Recipe**:
- Border: `rgba(168, 216, 255, 0.15)` (subtle blue)

**System Recipe Badge**:
- Background: `rgba(100, 150, 255, 0.2)`
- Text: `#7ea8ff`

### Icons

| Action | Icon | Color |
|--------|------|-------|
| Set Default | ⭐ Star | Blue (#a8d8ff) |
| Edit | ✏️ Edit | Blue (#a8d8ff) |
| Clone | 📋 Copy | Blue (#a8d8ff) |
| Delete | 🗑️ Trash | Red (#ff6b6b) |

### Layout

**Tab Bar**:
- Underline style
- Active tab: Blue underline
- Inactive tab: Gray text

**Recipe Cards**:
- Card layout with actions on right
- Grouped by action type
- Expandable sections (future)

---

## 🚀 Performance Considerations

### Optimization

**Initial Load**:
- Fetch all recipes once on mount
- Group in memory (fast)
- No pagination needed (typically < 100 recipes)

**Mutations**:
- Optimistic updates (clone appears immediately)
- Reload after server confirmation
- Clear cache on logout

**Default Management**:
- Server-side enforcement ensures consistency
- Client refreshes list after setting default

---

## 🔮 Future Enhancements

### Phase 2 (Next Sprint)

**Recipe Versioning**:
- Track changes over time
- Revert to previous versions
- Compare versions (diff view)

**Recipe Sharing**:
- Export recipe as JSON
- Import from file/URL
- Team recipe library

**Advanced Editor**:
- Syntax highlighting for JSON schemas
- Template variable autocomplete
- Preview mode (see how placeholders render)

### Phase 3 (Future)

**Recipe Analytics**:
- Track usage per recipe
- Success rates
- Popular recipes

**AI-Assisted Editing**:
- Suggest improvements
- Generate recipes from examples
- Auto-detect issues

**Collaboration**:
- Comments on recipes
- Change requests
- Approval workflows

---

## 📝 Migration Guide

### From Previous Version

If you have jobs using old recipe system:
1. Existing jobs continue to work
2. Old recipes automatically upgraded
3. Set new defaults as needed
4. No data migration required

### Updating Seed Recipes

To update the 6 default recipes:
1. Edit them in Prompt Library
2. OR delete and re-run seed script
3. OR create improved versions and set as default

---

## ✅ Complete Feature Checklist

From the updated master prompt, all requirements met:

✅ **Backend**:
- ✅ is_default management in metadata
- ✅ One default per action_type enforced
- ✅ Clone endpoint implemented
- ✅ Protected seed deletion
- ✅ Update recipe PATCH with default logic

✅ **Frontend - Prompt Library**:
- ✅ "Prompts" tab in Data Analysis
- ✅ List recipes grouped by action_type
- ✅ Show recipe details (name, type, provider/model)
- ✅ Default badge display
- ✅ Source badge (System/User)
- ✅ Create new recipe
- ✅ Edit existing recipe
- ✅ Clone recipe
- ✅ Delete recipe with confirmation
- ✅ Set as default action

✅ **Frontend - Recipe Editor**:
- ✅ Form with all fields
- ✅ Action type selector (locked when editing)
- ✅ Default provider/model inputs
- ✅ "Make default" checkbox
- ✅ System message textarea
- ✅ User template textarea
- ✅ Template placeholder hints
- ✅ Validation
- ✅ Save/Cancel actions

✅ **Integration**:
- ✅ "Manage Recipes" link in job form
- ✅ Tab navigation works
- ✅ Default recipes used automatically
- ✅ 6 seed recipes available

---

## 🎉 Complete!

**You can now edit prompts in two places:**

1. **Prompt Library** → Full management interface
2. **Job Details** → Quick iteration from results

**All recipes are editable, cloneable, and manageable through a beautiful, intuitive UI!** 🚀

---

## 📞 Quick Reference

### Navigate to Prompt Library

```
1. Go to http://localhost:3000/data-analysis
2. Click "Prompt Library" tab
3. Start creating/editing recipes!
```

### API Endpoints

```
GET    /api/v1/data-explorer/prompt-recipes/
POST   /api/v1/data-explorer/prompt-recipes/
GET    /api/v1/data-explorer/prompt-recipes/{id}
PATCH  /api/v1/data-explorer/prompt-recipes/{id}
DELETE /api/v1/data-explorer/prompt-recipes/{id}
POST   /api/v1/data-explorer/prompt-recipes/{id}/clone
```

### Key Files

```
Backend:
- domains/data_explorer/prompt_recipes_router.py
- domains/data_explorer/db_models.py

Frontend:
- src/components/PromptLibrary.tsx (new)
- src/components/RecipeEditor.tsx (new)
- src/pages/DataAnalysis.tsx (updated)
- src/api/client.ts (updated)
```

**Happy prompt engineering!** ✨

