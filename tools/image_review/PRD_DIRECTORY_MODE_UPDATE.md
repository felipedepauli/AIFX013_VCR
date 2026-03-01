# PRD Update: Directory-Based Navigation

## 1. Summary

**Objective**: Replace the project-based image loading with directory-based navigation while keeping ALL existing functionality intact.

**Key Principle**: The only changes are HOW users select what to view. Everything else (grid, labels, flags, filters, shortcuts) remains EXACTLY the same.

---

## 2. What Changes

### 2.1 Remove
- Project dropdown in toolbar
- Project configuration screen
- `/api/projects` endpoint
- `project.yaml` file dependency
- `projectData` JavaScript object

### 2.2 Add
- **Directories tab** in sidebar (alongside existing Filters tab)
- **Activate button** to mark directory as dataset
- **Directory path display** in toolbar (replaces project dropdown)
- **Recursive toggle** in toolbar
- **`.dataset.json`** file at directory root (stores flags)

### 2.3 Keep Unchanged (DO NOT TOUCH)
- Image grid rendering (`renderImageGrid()`)
- Label drawing (`drawLabels()`, `renderLabelOverlay()`)
- Image cards HTML/CSS
- Filter panel functionality
- Quality/perspective flag UI
- Keyboard shortcuts
- Pagination
- Settings panel
- All existing CSS styling
- Move/delete operations
- Image modal/zoom

---

## 3. User Flow

### 3.1 Startup
1. App loads with empty grid
2. Sidebar shows two tabs: **Filters** | **Directories**
3. Directories tab shows file browser starting at configured base path
4. User navigates to desired directory

### 3.2 Selecting a Directory
1. User clicks directory in tree
2. Directory is highlighted (selected)
3. User clicks **"Activate"** button
4. `.dataset.json` is created at directory root (if not exists)
5. Images load into grid using **existing `loadImages()` function**

### 3.3 Working with Images
- EXACTLY as before
- Same grid, same labels, same flags, same shortcuts
- Flags stored in `.dataset.json` instead of per-image JSON

### 3.4 Recursive Mode
- Toggle in toolbar switches between:
  - **Direct**: Only images in selected directory
  - **Recursive**: All images in directory and subdirectories

---

## 4. Technical Changes

### 4.1 Backend

#### New Endpoint: `/api/browse/images`
```python
GET /api/browse/images?path=/abs/path&mode=direct|recursive

Response: {
    "success": true,
    "images": [...],  # SAME format as existing /api/images
    "total": 150,
    "page": 1,
    "per_page": 50
}
```

**Implementation**: Reuse existing image-finding logic, just change source from project config to directory path.

#### Existing `/api/images` 
- Keep unchanged OR redirect internally from `/api/browse/images`

#### New Endpoint: `/api/browse/activate`
```python
POST /api/browse/activate
Body: { "path": "/abs/path" }

Response: { "success": true }
```
- Creates `.dataset.json` at path if not exists

#### `.dataset.json` Structure
```json
{
    "created_at": "2026-02-13T10:00:00Z",
    "image_flags": {
        "image_001": {
            "quality_flag": "ok",
            "perspective_flag": "pan-day"
        }
    }
}
```

### 4.2 Frontend

#### Sidebar Modification
```javascript
// Add tab switching logic
// Filters tab: existing filter panel content
// Directories tab: directory tree browser
```

#### Directory Browser
- Collapsible tree view
- Click to select, double-click to navigate into
- "Activate" button when directory selected

#### Toolbar Modification
```javascript
// Replace project dropdown with:
// [📁 /path/to/directory] [Direct ▼] [⟳ Refresh]
```

#### State Changes
```javascript
// Remove:
- projectData global

// Add:
let browseState = {
    activePath: null,      // Currently active directory
    displayMode: 'direct', // 'direct' or 'recursive'
    metadata: null         // Loaded .dataset.json
};
```

#### Load Integration
```javascript
// When directory activated:
async function activateDirectory(path) {
    await fetch('/api/browse/activate', { 
        method: 'POST', 
        body: JSON.stringify({ path }) 
    });
    browseState.activePath = path;
    
    // USE EXISTING loadImages() - just change the source!
    loadImages(1);  // Existing function
}

// Modify loadImages() to check browseState.activePath
// instead of projectData
```

---

## 5. Implementation Phases

### Phase 1: Backend (30 min)
1. Add `/api/browse/images` endpoint
2. Add `/api/browse/activate` endpoint  
3. Modify flag storage to use `.dataset.json`

### Phase 2: Sidebar Tabs (30 min)
1. Add tab switching HTML/CSS
2. Move filter panel into "Filters" tab
3. Add "Directories" tab with tree browser

### Phase 3: Directory Browser (45 min)
1. Implement tree view (reuse existing filesystem API)
2. Add click/double-click handlers
3. Add "Activate" button

### Phase 4: Toolbar Update (20 min)
1. Replace project dropdown with path display
2. Add recursive toggle
3. Add refresh button

### Phase 5: Integration (30 min)
1. Connect directory selection to `loadImages()`
2. Update flag save/load to use `.dataset.json`
3. Remove project-related code

### Phase 6: Testing (30 min)
1. Verify all existing features work
2. Test flag persistence
3. Test recursive mode

---

## 6. Files to Modify

| File | Changes |
|------|---------|
| `app.py` | Add 2 new endpoints, modify flag storage |
| `static/js/app.js` | Add browseState, tab switching, tree browser, update loadImages() |
| `templates/index.html` | Add tabs HTML, update toolbar |
| `static/css/styles.css` | Add tab styles, tree styles |

---

## 7. Risk Mitigation

### Risk: Breaking existing functionality
**Mitigation**: 
- Make minimal changes to existing functions
- Test each existing feature after integration
- Keep existing API endpoints working

### Risk: Flag data migration
**Mitigation**:
- New `.dataset.json` format is independent
- Old per-image JSON flags still readable
- Can migrate on first load if needed

---

## 8. Success Criteria

1. ✅ User can browse directories in sidebar
2. ✅ User can activate any directory
3. ✅ Images load into SAME grid as before
4. ✅ Labels display EXACTLY as before
5. ✅ Flags work (saved to `.dataset.json`)
6. ✅ Filters work
7. ✅ Keyboard shortcuts work
8. ✅ All existing features unchanged
