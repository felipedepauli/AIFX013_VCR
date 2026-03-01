# Development Plan: Image Review & Annotation Tool

## Project Overview

**Project Name:** Image Review Tool → Dataset Review Tool (v2.0)  
**Tech Stack:** Python Flask + Vanilla JS/HTML/CSS + MongoDB  
**Status:** v1.0 Complete ✅ | v1.1 (Filters) ✅ | v1.2 (Vehicle Direction) ✅ | v2.0 (Dataset Management) 📋 | v2.1 (Datasets Dashboard) ✅ | v2.2 (Dataset Sync) 📋

---

## Release History

| Version | Status | Phases | Date |
|---------|--------|--------|------|
| v1.0 | ✅ Complete | Phase 1-9 | Feb 2026 |
| v1.1 | ✅ Complete | Phase 10 (Filters) | Feb 2026 |
| v1.2 | ✅ Complete | Phase 11 (Vehicle Direction) | Feb 2026 |
| v2.0 | 🔄 In Progress (93%) | Phase 12-15 (Dataset Management) | Feb 2026 |
| v2.1 | ✅ Complete | Phase 23-25 (Datasets Dashboard) | Feb 2026 |
| v2.2 | ✅ Done | Phase 26 (Dataset Info → MongoDB Sync) | Feb 2026 |

---

## Directory Structure

### Tool Location

```
/home/pauli/temp/AIFX013_VCR/
└── tools/
    └── image_review/
        ├── app.py                    # Main Flask application
        ├── README.md                 # Incremental testing guide (updated each phase)
        ├── requirements.txt          # Python dependencies
        ├── static/
        │   ├── css/
        │   │   └── styles.css        # All CSS styles
        │   └── js/
        │       └── app.js            # All JavaScript
        ├── templates/
        │   └── index.html            # Main HTML template
        ├── projects/                 # Project JSON files
        │   └── .gitkeep
        └── tests/
            └── test_app.py           # Unit tests
```

### Data Directories (Reference)

```
/home/pauli/temp/AIFX013_VCR/
├── images/
│   └── xywh/
│       └── v4/
│           └── test/                 # Default test dataset
│               ├── 000000_XYZ123.jpg
│               └── 000000_XYZ123.json
├── data/
│   └── all_images_vFinal/
│       └── crops/                    # Another dataset location
└── docs/
    ├── PRD_IMAGE_REVIEW_TOOL.md
    ├── DEV_PLAN_IMAGE_REVIEW_TOOL.md
    └── specs/
        └── spec_phase*.md            # Phase specifications
```

### Key Paths

| Path | Purpose |
|------|---------|
| `tools/image_review/` | Tool root directory |
| `tools/image_review/app.py` | Main Flask application |
| `tools/image_review/projects/` | Project JSON storage |
| `tools/image_review/README.md` | Testing guide (incremental) |
| `images/xywh/v4/test/` | Default test dataset |

---

## README Increments

The `tools/image_review/README.md` file will be **updated at each phase** with:
1. Current features available
2. How to run the tool
3. How to test each feature
4. Expected behavior
5. Known limitations

See **README Increment** section at end of each phase.

---

## Phase 1: Project Setup & Infrastructure (Day 1) ✅

### 1.1 Project Setup Modal (Startup) ✅
- [x] Create startup modal that opens on launch
- [x] Directory selector (browse for image folder)
- [x] Project name input field
- [x] Default quality flags checkboxes: `bin`, `review`, `ok`, `move`
- [x] Default perspective flags checkboxes: `close-up-day`, `close-up-night`, etc.
- [x] Default visible labels selection
- [x] "Create Project" button
- [x] "Open Recent" dropdown for existing projects

### 1.2 Project Manager Class ✅
- [x] Create `ProjectManager` class for project JSON operations
- [x] `create_project(name, directory, defaults)` method
- [x] `load_project(name)` method
- [x] `save_project()` auto-save method
- [x] Generate project file: `{project_name}.json`

### 1.3 Data Layer ✅
- [x] Create `LabelManager` class for per-image JSON operations
- [x] Implement image discovery (scan directory for images)
- [x] Map images to their JSON label files
- [x] Initialize image entries in project JSON

### 1.4 Flask App & Routes ✅
- [x] Create `image_review_tool.py` main file
- [x] Setup Flask routes structure
- [x] Create HTML template skeleton
- [x] Setup CSS grid system for responsive layout

### 1.5 API Endpoints (Basic) ✅
```python
# Project endpoints
GET  /                           # Main page (shows setup modal)
POST /api/project/create         # Create new project
GET  /api/project/load/<name>    # Load existing project
GET  /api/project/recent         # List recent projects
GET  /api/browse_directory       # Browse for directory

# Core endpoints
GET  /api/images                 # Get paginated image list
GET  /api/image/<id>             # Get single image data
GET  /api/settings               # Get current settings
POST /api/settings               # Update settings
```

**Deliverable:** Working project setup flow + basic Flask app ✅

### README Increment (Phase 1)

```markdown
# Image Review Tool

## Quick Start

1. Install dependencies:
   ```bash
   cd tools/image_review
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open browser: http://localhost:5000

## Testing Phase 1

### Test 1.1: Startup Modal
- [ ] Open http://localhost:5000
- [ ] Verify startup modal appears automatically
- [ ] Verify "Create Project" and "Open Recent" sections are visible

### Test 1.2: Create New Project
- [ ] Type project name: `test_project`
- [ ] Click "Browse" and select: `/home/pauli/temp/AIFX013_VCR/images/xywh/v4/test`
- [ ] Click "Create Project"
- [ ] Verify `projects/test_project.json` is created
- [ ] Verify image count is shown (should be > 0)

### Test 1.3: Open Recent Project
- [ ] Refresh page (F5)
- [ ] Verify `test_project` appears in "Open Recent"
- [ ] Click to open it
- [ ] Verify project loads successfully

## Current Features
- ✅ Project setup modal
- ✅ Create new project
- ✅ Load existing project
- ✅ Basic Flask server

## Known Limitations
- Grid view not implemented yet
- Images not displayed yet
```

---

## Phase 2: Grid View Display (Day 2) ✅

### 2.1 Image Grid Component ✅
- [x] Create CSS grid with 2x2, 3x3, 5x5, 6x6 layouts
- [x] Implement grid selector buttons
- [x] Add pagination logic (calculate pages based on grid size)
- [x] Create image card component
- [x] **BONUS:** Custom NxM grid size modal

### 2.2 Image Loading & Display ✅
- [x] Implement thumbnail generation (resize for grid)
- [x] Create base64 encoding for web display
- [x] Add lazy loading with intersection observer
- [x] Implement page navigation (Previous/Next)

### 2.3 API Endpoints ✅
```python
GET  /api/images?page=1&grid_size=9   # Paginated images
GET  /api/thumbnail/<id>               # Get thumbnail
```

**Deliverable:** Working grid view with pagination ✅

### README Increment (Phase 2)

```markdown
# Image Review Tool

## Quick Start

1. Install dependencies:
   ```bash
   cd tools/image_review
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open browser: http://localhost:5000

## Testing Phase 2

### Test 2.1: Grid Display
- [ ] Create/open a project with images
- [ ] Verify images display in a 3×3 grid (default)
- [ ] Verify thumbnails are loaded (not full resolution)

### Test 2.2: Grid Size Selector
- [ ] Click "2×2" button → verify 4 images shown
- [ ] Click "3×3" button → verify 9 images shown
- [ ] Click "5×5" button → verify 25 images shown
- [ ] Click "6×6" button → verify 36 images shown

### Test 2.3: Pagination
- [ ] Verify page indicator shows "Page 1 of X"
- [ ] Click "Next" → verify next page loads
- [ ] Click "Previous" → verify previous page loads
- [ ] Use keyboard arrows (← →) → verify navigation works

## Current Features
- ✅ Project setup modal
- ✅ Create/Load projects
- ✅ Grid view (2×2, 3×3, 5×5, 6×6)
- ✅ Pagination with keyboard support
- ✅ Thumbnail generation

## Known Limitations
- Labels not displayed on images yet
- No selection or controls yet
```

---

## Phase 3: Label Overlay System (Day 2-3) ✅

### 3.1 Label Rendering ✅
- [x] Parse label JSON for each image
- [x] Calculate bounding box center point
- [x] Draw labels on canvas overlay
- [x] Stack multiple labels vertically
- [x] Handle NULL values for missing labels

### 3.2 Label Visibility Controls ✅
- [x] Create label toggle checkboxes
- [x] Implement label filter state
- [x] Update display when labels toggled
- [x] Persist label visibility in settings

### 3.3 Bounding Box Drawing ✅
- [x] Draw rectangles from `rect` [x,y,w,h]
- [x] Color coding for different objects
- [x] Semi-transparent fill

### 3.4 API Endpoints ✅
```python
GET  /api/labels/<image_id>           # Get labels for image
POST /api/settings/visible_labels     # Update visible labels
```

**Deliverable:** Images with label overlays ✅

### README Increment (Phase 3)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 3

### Test 3.1: Label Display
- [ ] Open a project with labeled images
- [ ] Verify labels appear overlaid on images
- [ ] Verify labels are positioned at bounding box center
- [ ] Verify multiple labels stack vertically

### Test 3.2: Label Visibility Toggle
- [ ] Find the label toggle checkboxes in toolbar
- [ ] Uncheck "brand" → verify brand labels disappear
- [ ] Check "brand" → verify brand labels reappear
- [ ] Uncheck all → verify no labels shown

### Test 3.3: Label Values
- [ ] Verify `color` label shows color value (e.g., "White", "Black")
- [ ] Verify `NULL` is shown for missing values
- [ ] Check image with multiple objects → verify all labels shown

### Test 3.4: Bounding Boxes
- [ ] Verify colored rectangles around objects
- [ ] Verify boxes match object positions

## Current Features
- ✅ Project setup modal
- ✅ Grid view with pagination
- ✅ Label overlays on images
- ✅ Label visibility toggles
- ✅ Bounding box display

## Known Limitations
- Cannot select images yet
- Cannot delete or flag yet
```

---

## Phase 4: Per-Image Controls (Day 3) ✅

### 4.1 Control Buttons ✅
- [x] Create selection checkbox (top-left)
- [x] Create "Open Wider" button with modal
- [x] Create "Delete" button
- [x] Create "Flag" button
- [x] Style hover states

### 4.2 Selection System ✅
- [x] Track selected images in state
- [x] Visual indicator for selected images
- [x] Select/Deselect all functionality
- [x] Selection counter in toolbar

### 4.3 Modal: Open Wider ✅
- [x] Create fullscreen modal component
- [x] Load full-resolution image
- [x] Display all labels
- [x] Close on click outside / Escape

### 4.4 API Endpoints ✅
```python
POST /api/select                      # Update selection state
GET  /api/image/<id>/full             # Get full resolution
```

**Deliverable:** Interactive image cards with controls ✅

### README Increment (Phase 4)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 4

### Test 4.1: Selection Checkbox
- [ ] Hover over image → verify checkbox appears (top-left)
- [ ] Click checkbox → verify image gets selected border
- [ ] Click checkbox again → verify deselection
- [ ] Verify selection counter updates in toolbar

### Test 4.2: Multi-Selection
- [ ] Select first image
- [ ] Shift+Click 5th image → verify images 1-5 selected
- [ ] Click "Select All" → verify all images on page selected
- [ ] Click "Deselect All" → verify all deselected

### Test 4.3: Open Wider Modal
- [ ] Hover over image → click expand button (🔍)
- [ ] Verify modal opens with full-resolution image
- [ ] Verify all labels visible in modal
- [ ] Press Escape → verify modal closes
- [ ] Click outside modal → verify modal closes

### Test 4.4: Control Button Visibility
- [ ] Hover over image → verify control buttons appear:
  - [ ] Checkbox (top-left)
  - [ ] Expand (top-right)
  - [ ] Delete (bottom-left)
  - [ ] Flag (bottom-right)
- [ ] Move mouse away → buttons hide (except if selected)

## Current Features
- ✅ Project setup and grid view
- ✅ Label overlays
- ✅ Image selection (single, shift, all)
- ✅ Open wider modal
- ✅ Per-image control buttons

## Known Limitations
- Delete button shows but doesn't work yet
- Flag button shows but doesn't work yet
```

---

## Phase 5: Delete Operations (Day 4) ✅

### 5.1 Delete Functionality ✅
- [x] Single image delete button handler
- [x] Confirmation dialog (when setting OFF)
- [x] "Skip confirmation" setting toggle in UI
- [x] Bulk delete for selected images
- [x] Remove from grid, shift remaining images
- [x] Update project JSON (remove image entry)

### 5.2 API Endpoints ✅
```python
POST /api/delete/<image_id>           # Delete single
POST /api/delete/bulk                 # Delete selected
```

**Deliverable:** Working delete with file operations ✅

### README Increment (Phase 5)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 5

### Test 5.1: Single Image Delete
- [ ] Hover over an image → click Delete button (🗑️)
- [ ] Verify confirmation dialog appears
- [ ] Click "Cancel" → verify image NOT deleted
- [ ] Click Delete again → Click "Delete" in dialog
- [ ] Verify image removed from grid
- [ ] Verify image file deleted from disk
- [ ] Verify JSON file deleted from disk

### Test 5.2: Bulk Delete
- [ ] Select 3 images using checkboxes
- [ ] Click "Delete Selected" in toolbar
- [ ] Verify confirmation shows "Delete 3 images?"
- [ ] Confirm delete
- [ ] Verify all 3 images removed from grid and disk

### Test 5.3: Skip Confirmation Setting
- [ ] Open Settings (⚙️) → enable "Skip delete confirmation"
- [ ] Delete an image → verify NO confirmation dialog
- [ ] Image should be deleted immediately

### Test 5.4: Keyboard Delete
- [ ] Select image(s)
- [ ] Press `Delete` or `Backspace`
- [ ] Verify delete action triggered

⚠️ **WARNING:** Test on a COPY of your data! Deletions are permanent.

## Current Features
- ✅ Project setup and grid view
- ✅ Label overlays and visibility
- ✅ Image selection
- ✅ Single and bulk delete
- ✅ Delete confirmation (toggleable)
- ✅ Keyboard shortcut (Delete)

## Known Limitations
- Flag system not implemented yet
- Cannot edit labels yet
```

---

## Phase 6: Flags System - Quality & Perspective (Day 4-5) ✅

### 6.1 Flag Modal Component ✅
- [x] Two-section modal: Quality Flags + Perspective Flags
- [x] Quality flags section with checkboxes (default: bin, review, ok, move)
- [x] Perspective flags section with checkboxes (default: close-up-day, close-up-night, pan-day, pan-night, super_pan_day, super_pan_night, cropped-day, cropped-night)
- [x] Apply/Cancel buttons
- [x] Load current flags from project JSON for image

### 6.2 Flag Display ✅
- [x] Display flags at bottom of image card
- [x] Color-code by type (quality = blue, perspective = green)
- [x] Compact display for multiple flags

### 6.3 Bulk Operations ✅
- [x] "Flag Selected" button in toolbar
- [x] Apply flags to all selected images
- [x] Quick keyboard shortcut Q (cycle quality) and P (perspective modal)

### 6.4 Flag Storage ✅
- [x] Store flags in project JSON per image
- [x] If no flags set, apply project defaults
- [x] Read flags from project JSON on load

### 6.5 Flag Configuration (Settings) ✅
- [x] UI to add new quality flags
- [x] UI to add new perspective flags
- [x] UI to remove flags
- [x] Persist to project JSON

### 6.6 API Endpoints ✅
```python
GET  /api/flags                           # List all flags (quality + perspective)
POST /api/flags/quality                   # Add quality flag
POST /api/flags/perspective               # Add perspective flag
DELETE /api/flags/<type>/<name>           # Remove flag
POST /api/image/<id>/flags                # Update image flags
POST /api/flags/bulk                      # Bulk update flags
```

**Deliverable:** Complete dual-category flag system ✅

### README Increment (Phase 6)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 6

### Test 6.1: Flag Modal - Single Image
- [ ] Hover over image → click Flag button (🏷️)
- [ ] Verify flag modal opens with two sections:
  - [ ] Quality Flags: bin, review, ok, move
  - [ ] Perspective Flags: close-up-day, close-up-night, pan-day, etc.
- [ ] Check "ok" in Quality section
- [ ] Check "pan-day" in Perspective section
- [ ] Click "Apply"
- [ ] Verify flag pills appear on image card

### Test 6.2: Flag Display
- [ ] Verify quality flags show as blue pills
- [ ] Verify perspective flags show as green pills
- [ ] Verify flags persist after page navigation
- [ ] Verify flags persist after refresh

### Test 6.3: Bulk Flagging
- [ ] Select 5 images
- [ ] Click "Flag Selected" in toolbar
- [ ] Select bulk mode: "Set flags (replace)"
- [ ] Check "review" 
- [ ] Click Apply
- [ ] Verify all 5 images now show "review" flag

### Test 6.4: Bulk Flag Modes
- [ ] Test "Add to existing" mode → flags are added, not replaced
- [ ] Test "Remove flags" mode → specified flags are removed

### Test 6.5: Keyboard Shortcuts
- [ ] Select image → press `Q` → cycles through quality flags
- [ ] Select image → press `P` → opens perspective flag modal
- [ ] Hover image → press `F` → opens full flag modal

## Current Features
- ✅ All previous features
- ✅ Quality flags (bin, review, ok, move)
- ✅ Perspective flags (8 defaults)
- ✅ Single and bulk flagging
- ✅ Flag pills display
- ✅ Keyboard shortcuts (Q, P, F)

## Known Limitations
- Cannot edit labels inline yet
- Settings panel not complete yet
```

---

## Phase 7: Inline Label Editing (Day 5) ✅

### 7.1 Editable Labels ✅
- [x] Click-to-edit on label text
- [x] Inline input field component
- [x] Save on Enter/blur
- [x] Cancel on Escape
- [x] Visual feedback on save

### 7.2 JSON Update Logic ✅
- [x] Read current JSON
- [x] Update only changed field
- [x] Write back to file (atomic)
- [x] Handle multiple objects in JSON
- [x] Error handling for file operations

### 7.3 API Endpoints ✅
```python
PUT  /api/labels/<image_id>/<obj_idx>/<field>  # Update label field
```

**Deliverable:** Working inline editing with JSON persistence ✅

### README Increment (Phase 7)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 7

### Test 7.1: Click-to-Edit Label
- [ ] Open a project with labeled images
- [ ] Click on a label value (e.g., "White" under color)
- [ ] Verify input field appears
- [ ] Type new value: "Black"
- [ ] Press Enter
- [ ] Verify label updates on screen

### Test 7.2: Save Persistence
- [ ] Edit a label as above
- [ ] Refresh page (F5)
- [ ] Verify edited label still shows new value
- [ ] Check the JSON file in images folder → verify value updated

### Test 7.3: Cancel Edit
- [ ] Click on a label to edit
- [ ] Type something
- [ ] Press Escape
- [ ] Verify original value restored (not saved)

### Test 7.4: Tab Navigation
- [ ] Click on a label to edit
- [ ] Press Tab
- [ ] Verify saves current and moves to next label
- [ ] Press Shift+Tab
- [ ] Verify saves and moves to previous label

### Test 7.5: Multiple Objects
- [ ] Find image with multiple objects (check JSON has multiple entries)
- [ ] Edit label for 2nd object
- [ ] Verify only that object's label is updated in JSON

## Current Features
- ✅ All previous features (grid, labels, delete, flags)
- ✅ Inline label editing (click to edit)
- ✅ Save on Enter or blur
- ✅ Cancel on Escape
- ✅ Tab navigation between labels
- ✅ JSON file persistence

## Known Limitations
- Settings panel not complete
- No keyboard shortcuts help yet
```

---

## Phase 8: Settings Panel (Day 5-6) ✅

### 8.1 Settings UI ✅
- [x] Gear icon button (⚙️)
- [x] Settings sidebar/modal
- [x] Tab sections: General, Labels, Quality Flags, Perspective Flags

### 8.2 Settings Sections ✅
- [x] General: Skip delete confirmation, project info display
- [x] Labels: Toggle visible labels
- [x] Quality Flags: Add/remove quality flags
- [x] Perspective Flags: Add/remove perspective flags
- [x] Defaults: Set default quality/perspective flags for new images

### 8.3 Persistence ✅
- [x] Save settings to project JSON
- [x] Load settings from project on startup
- [x] Real-time UI updates
- [x] Display current project name in header

**Deliverable:** Complete settings panel ✅

### README Increment (Phase 8)

```markdown
# Image Review Tool

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 8

### Test 8.1: Open Settings
- [ ] Click gear icon (⚙️) in toolbar
- [ ] Verify settings modal opens
- [ ] Verify project info section shows:
  - [ ] Project name
  - [ ] Directory path
  - [ ] Image count
  - [ ] Created date

### Test 8.2: General Settings
- [ ] Toggle "Skip delete confirmation"
- [ ] Close settings → test delete → verify behavior changed
- [ ] Change default grid size → verify applied

### Test 8.3: Visible Labels Configuration
- [ ] Uncheck "brand" in visible labels
- [ ] Close settings → verify "brand" not shown in grid
- [ ] Refresh page → verify setting persisted

### Test 8.4: Quality Flags Management
- [ ] Click "+ Add" in quality flags section
- [ ] Type: "urgent"
- [ ] Click Add → verify "urgent" appears in list
- [ ] Click ✕ on a flag → verify removed
- [ ] Test flagging an image → verify new flag available

### Test 8.5: Perspective Flags Management
- [ ] Add new perspective flag: "drone-view"
- [ ] Verify it appears in flag modal when flagging images
- [ ] Remove a perspective flag → verify removed from modal

### Test 8.6: Keyboard Shortcut
- [ ] Press `,` (comma) key
- [ ] Verify settings modal opens

## Current Features
- ✅ All previous features
- ✅ Settings modal with project info
- ✅ Skip delete confirmation toggle
- ✅ Visible labels configuration
- ✅ Add/remove quality flags
- ✅ Add/remove perspective flags
- ✅ Settings persistence

## Known Limitations
- Keyboard shortcuts help not implemented
- Final polish pending
```

---

## Phase 9: Polish & Testing (Day 6-7) ✅

### 9.1 Keyboard Shortcuts ✅
- [x] Implement all shortcuts from PRD
- [x] Show shortcuts help modal
- [x] Visual indicators for shortcuts

### 9.2 Error Handling ✅
- [x] File operation errors
- [x] Network errors
- [x] Invalid data handling
- [x] User-friendly error messages

### 9.3 Performance Optimization ✅
- [x] Image caching
- [x] Debounce API calls
- [x] Memory cleanup

### 9.4 Testing ✅
- [x] Test with large datasets (1000+ images)
- [x] Test all CRUD operations
- [x] Test edge cases (missing JSON, etc.)

**Deliverable:** Production-ready tool ✅

### README Increment (Phase 9 - FINAL)

```markdown
# Image Review Tool

A web-based tool for reviewing and annotating image datasets with labels, flags, and batch operations.

## Installation

```bash
cd tools/image_review
pip install -r requirements.txt
```

## Usage

```bash
python app.py
# Open: http://localhost:5000
```

## Features

### Grid View
- Multiple layouts: 2×2, 3×3, 5×5, 6×6
- Pagination with keyboard navigation (← →)
- Thumbnail preview with labels overlay

### Label System
- View labels at bounding box positions
- Toggle label visibility per type
- Click-to-edit inline editing
- Changes saved directly to JSON files

### Selection & Batch Operations
- Single click or shift-click selection
- Select/Deselect all on page
- Bulk delete and bulk flagging

### Flags
- **Quality flags:** bin, review, ok, move (customizable)
- **Perspective flags:** close-up-day, pan-night, etc. (customizable)
- Single and bulk flagging with 3 modes (set, add, remove)

### Settings
- Project info display
- Skip delete confirmation
- Add/remove custom flags
- Configure visible labels

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← → | Previous/Next page |
| 1-4 | Grid size (2×2 to 6×6) |
| A | Select all on page |
| D | Deselect all |
| Delete | Delete selected |
| F | Flag selected/hovered |
| Q | Quick quality flag cycle |
| P | Perspective flag modal |
| Space | Open hovered image |
| , | Open settings |
| ? | Show shortcuts help |
| Esc | Close modal / Deselect |

## Testing Checklist

### Project Management
- [ ] Create new project
- [ ] Load existing project
- [ ] Switch between projects

### Grid View
- [ ] All grid sizes work (2×2, 3×3, 5×5, 6×6)
- [ ] Pagination works correctly
- [ ] Keyboard navigation (← →) works

### Labels
- [ ] Labels display at correct positions
- [ ] Toggle visibility works
- [ ] Inline editing works
- [ ] Changes persist to JSON files

### Selection
- [ ] Single selection works
- [ ] Shift+click range selection works
- [ ] Select/Deselect all works
- [ ] Selection counter updates

### Delete
- [ ] Single delete works
- [ ] Bulk delete works
- [ ] Confirmation dialog appears (unless disabled)
- [ ] Files removed from disk

### Flags
- [ ] Single image flagging works
- [ ] Bulk flagging (all 3 modes) works
- [ ] Flags display as pills
- [ ] Custom flags can be added/removed

### Settings
- [ ] All settings persist after refresh
- [ ] Custom flags appear in flag modal
- [ ] Visible labels configuration works

### Keyboard Shortcuts
- [ ] All shortcuts from table work

## Project Structure

```
tools/image_review/
├── app.py                    # Flask application
├── README.md                 # This file
├── requirements.txt          # Dependencies
├── static/
│   ├── css/styles.css
│   └── js/app.js
├── templates/index.html
├── projects/                 # Project JSON files
└── tests/test_app.py
```

## Known Limitations

1. No undo for deletions
2. Single user only (no concurrent access)
3. Local filesystem only (no cloud storage)
4. No image editing (view and label only)

## Troubleshooting

**Images not loading?**
- Check the image directory path is correct
- Ensure images are .jpg, .jpeg, or .png

**Labels not showing?**
- Verify JSON files exist alongside images
- Check JSON format matches expected schema

**Changes not saving?**
- Check file permissions
- Verify project JSON is writable
```

---

## Implementation Files

> **Note:** See "Directory Structure" section at top for full details.

| File | Purpose | Phase |
|------|---------|-------|
| `tools/image_review/app.py` | Main Flask application | 1 |
| `tools/image_review/requirements.txt` | Python dependencies | 1 |
| `tools/image_review/templates/index.html` | HTML template | 1 |
| `tools/image_review/static/css/styles.css` | All CSS styles | 1-9 |
| `tools/image_review/static/js/app.js` | All JavaScript | 1-9 |
| `tools/image_review/projects/*.json` | Project data files | 1 |
| `tools/image_review/README.md` | Testing guide (incremental) | 1-9 |

### Dependencies (requirements.txt)

```
flask>=2.0
pillow>=9.0
```

---

## Implementation Order (Recommended)

```
Day 1:  Phase 1 (Project Setup + Infrastructure)
Day 2:  Phase 2 (Grid View) + Phase 3 start (Labels)
Day 3:  Phase 3 finish + Phase 4 (Controls)
Day 4:  Phase 5 (Delete) + Phase 6 start (Flags)
Day 5:  Phase 6 finish (Quality + Perspective) + Phase 7 (Inline Edit)
Day 6:  Phase 8 (Settings) + Phase 9 start (Polish)
Day 7:  Phase 9 finish + Testing + Bug fixes
```

---

## Key Technical Decisions

### 1. Image Processing
- Use PIL to resize images for thumbnails (max 300x300)
- Cache thumbnails in memory during session
- Full resolution loaded only on "Open Wider"

### 2. State Management
- Server-side state for persistence (project JSON)
- Client-side state for UI interactions (JavaScript)
- Sync on actions (delete, flag)
- Each project is independent with its own JSON

### 3. File Operations
- Atomic writes (write to temp, then rename)
- Backup before destructive operations
- Handle concurrent access (file locks)

### 4. Grid Reflow
- When image removed, server returns updated list
- Client re-renders grid with new data
- No full page reload needed (AJAX)

---

## API Response Format

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed",
  "error": null
}
```

---

## Risk Mitigation During Development

1. **Start with read-only operations** (view, navigate) before write operations
2. **Test file operations** on copy of data first
3. **Implement backup** before any delete/modify code
4. **Add logging** for all file operations
5. **Create test dataset** with edge cases

---

## Completion Status

### v1.0 - Core Features ✅

1. ✅ Create PRD document
2. ✅ Create development plan
3. ✅ Phase 1: Project Setup & Infrastructure
4. ✅ Phase 2: Grid View Display
5. ✅ Phase 3: Label Overlay System
6. ✅ Phase 4: Per-Image Controls
7. ✅ Phase 5: Delete Operations
8. ✅ Phase 6: Flags System
9. ✅ Phase 7: Inline Label Editing
10. ✅ Phase 8: Settings Panel
11. ✅ Phase 9: Polish & Testing

### v1.1 - Filter Panel ✅

12. ✅ Phase 10: Filter Panel (Complete)

### v1.2 - Vehicle Direction Flag ✅

13. ✅ Phase 11: Vehicle Direction Flag (Complete)

### v2.0 - Dataset Management System 🔄 (93%)

14. 🔄 Phase 12: File System Browser (90% - missing Recent Datasets dropdown, breadcrumb)
15. ❌ Phase 13: Directory Operations (Not Started)
16. ✅ Phase 14: Dataset Activation System (Complete)
17. ✅ Phase 15: Dataset Metadata Panel (Complete)

---

## Phase 10: Filter Panel (v1.1) ✅

### Overview
Add a collapsible left sidebar filter panel to filter images by labels and flags.

### 10.1 Filter Panel UI ✅
- [x] Create collapsible left sidebar component
- [x] Add toggle button in header (`[` key shortcut)
- [x] Smooth slide animation for open/close
- [x] Persist panel state in session

### 10.2 Filter Sections ✅
- [x] Quality Flags section with checkboxes
- [x] Perspective Flags section with checkboxes
- [x] Label sections (Color, Brand, Model, Type, etc.)
- [x] Collapsible sections with expand/collapse
- [x] Show count of matching images per option

### 10.3 Filter Logic ✅
- [x] AND logic for multiple filters
- [x] Real-time filtering (no submit button)
- [x] Update pagination for filtered results
- [x] Cache filter results for performance

### 10.4 Active Filters Display ✅
- [x] Show active filters as chips in toolbar
- [x] Click chip to remove individual filter
- [x] "Clear All Filters" button
- [x] Show filtered count vs total count

### 10.5 Search Within Filters ✅
- [x] Search box at top of filter panel
- [x] Filter options as user types
- [x] Highlight matching options

### 10.6 API Endpoints ✅
```python
GET  /api/filter/options          # Get all filterable options with counts
GET  /api/images?filters=...      # Get images with filter query
```

**Deliverable:** Complete filter panel with label and flag filtering ✅

### README Increment (Phase 10)

```markdown
## Testing Phase 10

### Test 10.1: Filter Panel Toggle
- [ ] Click filter toggle button (◀) in header
- [ ] Verify sidebar slides in from left
- [ ] Press `[` key → verify toggle works
- [ ] Click again → verify sidebar collapses

### Test 10.2: Filter by Quality Flag
- [ ] Expand "Quality Flags" section
- [ ] Check "ok" checkbox
- [ ] Verify grid updates to show only images with "ok" flag
- [ ] Verify footer shows "Filtered: X / Total"

### Test 10.3: Filter by Label
- [ ] Expand "Color" section
- [ ] Check "white" checkbox
- [ ] Verify only images with color=white are shown
- [ ] Combine with flag filter → verify AND logic

### Test 10.4: Active Filter Chips
- [ ] Apply multiple filters
- [ ] Verify chips appear in toolbar: [color: white ✕] [ok ✕]
- [ ] Click ✕ on chip → verify filter removed
- [ ] Click "Clear All" → verify all filters cleared

### Test 10.5: Filter Counts
- [ ] Verify each filter option shows count: "white (42)"
- [ ] Apply filter → verify counts update for remaining options
```

---

See **[spec_phase10_filters.md](specs/spec_phase10_filters.md)** for detailed implementation specifications.

---

## Phase 11: Vehicle Direction Flag (v1.2) ✅

### Overview
Add a per-vehicle binary direction flag (`front`/`back`) to indicate whether a vehicle is coming toward the camera or going away. This flag is stored in the label JSON (per-vehicle), not the project JSON, because the same image can contain vehicles going in different directions.

### 11.1 Direction Flag Data Model ✅
- [x] Add `direction` field to vehicle objects in label JSON
- [x] Default value: `front` when field is missing
- [x] Valid values: `front`, `back`
- [x] Persist changes directly to label JSON file

### 11.2 Direction Indicator UI (Grid View) ✅
- [x] Display direction indicator on each bounding box
- [x] Visual: ⬆️ (front) or ⬇️ (back) arrow icon
- [x] Position: corner of bounding box (top-right)
- [x] Semi-transparent background for readability

### 11.3 Direction Toggle Interaction ✅
- [x] Click on indicator toggles `front` ↔ `back`
- [x] Immediate save to label JSON (no modal)
- [x] Visual feedback: brief flash/animation on change
- [x] No confirmation required

### 11.4 Direction Indicator UI (Modal View) ✅
- [x] Display direction indicator in "Open Wider" modal
- [x] Same toggle behavior as grid view
- [x] Larger clickable area for easier interaction

### 11.5 Filter by Direction ✅
- [x] Add "Direction" section in filter panel
- [x] Options: `front`, `back`
- [x] Show counts per direction
- [x] Integrate with existing filter logic

### 11.6 API Endpoints ✅
```python
POST /api/vehicle/<image_id>/<vehicle_idx>/direction   # Toggle direction
     Body: {"direction": "front" | "back"}
GET  /api/filter/options                               # Include direction counts
```

**Deliverable:** Complete vehicle direction flag system ✅

**Deliverable:** Complete vehicle direction flag with toggle and filtering

### README Increment (Phase 11)

```markdown
## Testing Phase 11

### Test 11.1: Direction Indicator Display
- [ ] Open project with vehicle images
- [ ] Verify each vehicle shows direction indicator (⬆️ default)
- [ ] Indicator appears at corner of bounding box

### Test 11.2: Direction Toggle
- [ ] Click on direction indicator
- [ ] Verify toggles from ⬆️ (front) to ⬇️ (back)
- [ ] Click again → verify toggles back to ⬆️ (front)
- [ ] Open label JSON file → verify `direction` field updated

### Test 11.3: Direction in Modal
- [ ] Open image in modal (🔍)
- [ ] Verify direction indicator visible on each vehicle
- [ ] Toggle direction in modal → verify update persists

### Test 11.4: Filter by Direction
- [ ] Open filter panel
- [ ] Expand "Direction" section
- [ ] Check "front" → verify only front-facing vehicles shown
- [ ] Check "back" → verify only back-facing vehicles shown

### Test 11.5: Mixed Directions
- [ ] Find image with multiple vehicles
- [ ] Set different directions for each vehicle
- [ ] Verify each vehicle maintains its own direction state
```

---

See **[spec_phase11_vehicle_direction.md](specs/spec_phase11_vehicle_direction.md)** for detailed implementation specifications.

---

## Phase 12: File System Browser (v2.0)

### Overview
Replace project-centric model with a file system browser. Left panel shows directory tree for navigation.

### 12.1 Directory Tree Component
- [ ] Create collapsible left panel for directory browser
- [ ] Render directory tree with expand/collapse nodes
- [ ] Single-click to select directory, double-click to navigate into
- [ ] Visual folder icons with indentation
- [ ] Show only directories (no files in tree)

### 12.2 Base Path Configuration
- [ ] Add configurable base path setting (restrict navigation scope)
- [ ] Store base path in app settings
- [ ] Validate paths are within base path
- [ ] Default base path could be configurable on startup

### 12.3 Navigation
- [ ] Breadcrumb showing current path in footer/header
- [ ] Back button to go up one level
- [ ] Path display in status bar

### 12.4 Recent Datasets
- [ ] Store recently opened datasets in localStorage
- [ ] "Recent Datasets" dropdown for quick switching
- [ ] Show dataset name and path
- [ ] Limit to last 10 datasets

### 12.5 API Endpoints
```python
GET  /api/filesystem/browse?path=...      # Get directory contents
GET  /api/filesystem/tree?path=...        # Get directory tree structure
POST /api/config/base_path                # Set base path
GET  /api/config/base_path                # Get base path
GET  /api/recent_datasets                 # Get recent datasets list
```

**Deliverable:** Working directory browser with navigation

### README Increment (Phase 12)

```markdown
## Testing Phase 12

### Test 12.1: Directory Browser
- [ ] Launch app → left panel shows directory tree
- [ ] Click folder → folder is selected/highlighted
- [ ] Double-click folder → navigate into folder
- [ ] Grid is empty until dataset activated

### Test 12.2: Base Path
- [ ] Configure base path in settings
- [ ] Verify cannot navigate outside base path
- [ ] Tree shows only directories within base

### Test 12.3: Recent Datasets
- [ ] Activate a dataset
- [ ] Open dropdown → see dataset in recent list
- [ ] Click recent dataset → loads that dataset
```

---

## Phase 13: Dataset Activation System (v2.0)

### Overview
Implement dataset activation model where a directory becomes the "active dataset" with images shown in grid.

### 13.1 Activation Logic
- [ ] "Activate Dataset" button in right panel
- [ ] When clicked, selected directory becomes dataset root
- [ ] Load images from dataset directory into grid
- [ ] Store dataset as "active" state

### 13.2 Display Modes
- [ ] Toggle: Direct (only this folder) vs Recursive (include subdirs)
- [ ] Default mode is "Direct"
- [ ] Show mode selector in footer/toolbar
- [ ] Re-scan images when mode changes

### 13.3 Subdirectory Navigation
- [ ] Double-click subdirectory in grid/tree → navigate into it
- [ ] Working directory changes, dataset root stays same
- [ ] Show path relative to dataset root
- [ ] Settings/flags inherited from dataset root

### 13.4 Deactivation
- [ ] "Deactivate Dataset" button
- [ ] Clears grid, returns to browse mode
- [ ] To make subdirectory its own dataset: deactivate first, then activate subdirectory

### 13.5 Dataset JSON
- [ ] Create `.dataset.json` at dataset root on activation
- [ ] Store settings, metadata, image flags in this file
- [ ] Each dataset has independent configuration

### 13.6 API Endpoints
```python
POST /api/dataset/activate               # Activate directory as dataset
POST /api/dataset/deactivate             # Deactivate current dataset
GET  /api/dataset/info                   # Get current dataset info
POST /api/dataset/display_mode           # Set direct/recursive mode
```

**Deliverable:** Working dataset activation with display modes

### README Increment (Phase 13)

```markdown
## Testing Phase 13

### Test 13.1: Dataset Activation
- [ ] Select directory in browser
- [ ] Click "Activate Dataset" button
- [ ] Verify images appear in grid
- [ ] Verify `.dataset.json` created

### Test 13.2: Display Modes
- [ ] With dataset active, toggle to "Recursive"
- [ ] Verify images from subdirs appear
- [ ] Toggle back to "Direct"
- [ ] Verify only direct images shown

### Test 13.3: Subdirectory Navigation
- [ ] Double-click subdirectory
- [ ] Verify navigation into subdir
- [ ] Verify dataset root unchanged
- [ ] Verify settings inherited
```

---

## Phase 14: Dataset Metadata Panel (v2.0)

### Overview
Add right panel with computed statistics and editable metadata for dataset analysis.

### 14.1 Right Panel UI
- [ ] Collapsible right panel component
- [ ] Collapse/expand button (like left panel)
- [ ] Panel header with "DATASET INFO"

### 14.2 Computed Statistics
- [ ] Total images (recursive count through all subdirs)
- [ ] Images per immediate subfolder (train/test/valid breakdown)
- [ ] Samples per class based on configurable fields (label, color, model)
- [ ] Auto-refresh stats when dataset changes

### 14.3 Editable Metadata Fields
- [ ] Name: text input (auto-filled from directory name)
- [ ] Description: textarea
- [ ] Camera View: multi-select (frontal, traseira, panorâmica, closeup, super-panorâmica)
- [ ] Quality: select (poor, fair, good, excellent)
- [ ] Verdict: select (keep ✅, revise 🔄, remove ❌)
- [ ] Cycle: select (first, second, third, fourth, fifth)
- [ ] Notes: textarea

### 14.4 Auto-Save
- [ ] Save metadata changes to `.dataset.json` on blur/change
- [ ] Visual feedback on save (brief highlight or icon)
- [ ] Debounce saves for text fields

### 14.5 Configuration
- [ ] Setting for which fields to use for class stats (label, color, model)
- [ ] Store in dataset settings

### 14.6 API Endpoints
```python
GET  /api/dataset/stats                  # Get computed statistics
GET  /api/dataset/metadata               # Get metadata
POST /api/dataset/metadata               # Update metadata
POST /api/dataset/settings               # Update settings (class_stats_fields, etc.)
```

**Deliverable:** Complete metadata panel with statistics

### README Increment (Phase 14)

```markdown
## Testing Phase 14

### Test 14.1: Statistics Display
- [ ] Activate dataset with train/test/valid subdirs
- [ ] Verify total count shown
- [ ] Verify breakdown by subfolder
- [ ] Verify class counts by label

### Test 14.2: Metadata Editing
- [ ] Edit name field → verify saves
- [ ] Change quality dropdown → verify saves
- [ ] Set verdict to "revise" → verify saves
- [ ] Check `.dataset.json` contains metadata

### Test 14.3: Panel Collapse
- [ ] Click collapse button → panel collapses
- [ ] Click expand → panel expands
- [ ] Data persists across collapse/expand
```

---

## Phase 15: Directory Operations (v2.0)

### Overview
Add directory management: create, delete, move, rename directories.

### 15.1 Create Directory
- [ ] "New Folder" button in directory panel
- [ ] Prompt for folder name
- [ ] Create in currently selected directory
- [ ] Validate name (no special chars, etc.)
- [ ] Refresh tree after creation

### 15.2 Delete Directory
- [ ] "Delete" button (with confirmation)
- [ ] Move to system trash if possible, else permanent delete
- [ ] Cannot delete non-empty dirs without confirmation
- [ ] Cannot delete dataset root while active
- [ ] Refresh tree after deletion

### 15.3 Move Directory
- [ ] "Move" button opens modal
- [ ] Select destination from tree
- [ ] Move directory with all contents
- [ ] Update any paths in `.dataset.json` if needed
- [ ] Refresh tree after move

### 15.4 Rename Directory
- [ ] "Rename" option (right-click or button)
- [ ] Inline edit or modal prompt
- [ ] Validate new name
- [ ] Update `.dataset.json` if renamed
- [ ] Refresh tree after rename

### 15.5 Safety
- [ ] Path validation (stay within base path)
- [ ] Confirmation for destructive operations
- [ ] Cannot operate on dataset root while active (except rename metadata)
- [ ] Error handling with user feedback

### 15.6 API Endpoints
```python
POST /api/filesystem/mkdir               # Create directory
DELETE /api/filesystem/rmdir             # Delete directory
POST /api/filesystem/move                # Move directory
POST /api/filesystem/rename              # Rename directory
```

**Deliverable:** Full directory management capabilities

### README Increment (Phase 15)

```markdown
## Testing Phase 15

### Test 15.1: Create Directory
- [ ] Click "New Folder"
- [ ] Enter name → verify created
- [ ] Verify appears in tree

### Test 15.2: Delete Directory
- [ ] Select empty directory
- [ ] Click delete → confirm → verify deleted
- [ ] Try delete non-empty → verify warning

### Test 15.3: Move Directory
- [ ] Select directory
- [ ] Click move → select destination
- [ ] Verify moved with contents

### Test 15.4: Rename Directory
- [ ] Select directory
- [ ] Rename → verify name changed
- [ ] If was dataset, verify metadata updated
```

---

See specs for detailed implementation:
- **[spec_phase12_filesystem_browser.md](specs/spec_phase12_filesystem_browser.md)**
- **[spec_phase13_dataset_activation.md](specs/spec_phase13_dataset_activation.md)**
- **[spec_phase14_dataset_metadata.md](specs/spec_phase14_dataset_metadata.md)**
- **[spec_phase15_directory_operations.md](specs/spec_phase15_directory_operations.md)**

---

## Phase 23: MongoDB Backend & Dataset Registry (v2.1)

### Overview
Set up server-side MongoDB integration for persistent dataset registry. pymongo connects to local MongoDB, providing CRUD API endpoints. Computes dataset statistics (total images, per-class counts, spatial bbox stats) and generates 4 representative thumbnails.

### 23.1 MongoDB Connection
- [x] Install `pymongo` dependency
- [x] Initialize MongoDB connection at app startup (`MONGODB_URI` env var, default `localhost:27017`)
- [x] Create `image_review_tool` database, `datasets` collection
- [x] Unique index on `root_path`
- [x] Graceful fallback if MongoDB unavailable (app works, dashboard disabled)
- [x] `requires_mongodb` decorator for protected endpoints

### 23.2 Dataset Document Schema
- [x] Define schema: `_id`, `name`, `root_path`, `registered_at`, `updated_at`
- [x] `metadata`: description, camera_view, quality, verdict, cycle, notes, model_compatibility
- [x] `statistics`: total_images, class_counts (car/motorcycle/truck/bus), spatial (position mean/var, area mean/var)
- [x] `thumbnails`: paths (4 cached JPEGs), generated_at

### 23.3 Statistics Computation
- [x] `_compute_dataset_statistics(root_path)` — walks all subdirs, reads JSON labels
- [x] Count images by class (label field: car, motorcycle, truck, bus)
- [x] Compute bounding box spatial stats: position center mean/variance, area mean/variance
- [x] Uses numpy for efficient calculation

### 23.4 Thumbnail Generation
- [x] `_generate_dataset_thumbnails(root_path, dataset_id)` — picks 1st, 25%, 75%, last image
- [x] Resize to 200×200 with Pillow (LANCZOS)
- [x] Cache in `static/cache/thumbnails/{dataset_id}_{0-3}.jpg`
- [x] Handles small datasets (< 4 images) gracefully

### 23.5 API Endpoints
```python
GET  /api/datasets/status              # MongoDB status check ✅
GET  /api/datasets                     # List all (summary view) ✅
POST /api/datasets                     # Register new dataset ✅
GET  /api/datasets/<id>                # Full detail ✅
PUT  /api/datasets/<id>                # Update metadata ✅
DELETE /api/datasets/<id>              # Unregister (files untouched) ✅
POST /api/datasets/<id>/refresh        # Re-compute stats + thumbnails ✅
GET  /api/datasets/<id>/thumbnails/<i> # Serve cached thumbnail (0-3) ✅
```

### 23.6 Serialization
- [x] `serialize_dataset(doc)` — full document → JSON
- [x] `serialize_dataset_summary(doc)` — lightweight for list view
- [x] Add `path_exists` field (via `os.path.isdir`) to summaries

**Deliverable:** Complete MongoDB data layer with statistics and thumbnails

### README Increment (Phase 23)

```markdown
## Testing Phase 23

### Test 23.1: MongoDB Connection
- [ ] Start MongoDB: `mongod`
- [ ] Start app: `python app.py`
- [ ] Console shows: "[MongoDB] Connected to ..."
- [ ] `GET /api/datasets/status` → `{"mongodb_available": true}`

### Test 23.2: Stop MongoDB, Restart App
- [ ] Stop `mongod`
- [ ] Restart app → console shows fallback message
- [ ] All existing features still work
- [ ] `GET /api/datasets` → 503

### Test 23.3: Register Dataset via API
- [ ] Activate a dataset (existing flow)
- [ ] `POST /api/datasets {"root_path": "/path/to/dataset"}` → 201
- [ ] Verify statistics: total_images > 0, class_counts populated
- [ ] Verify 4 thumbnails in static/cache/thumbnails/
- [ ] Same POST again → 409 duplicate

### Test 23.4: CRUD Operations
- [ ] `GET /api/datasets` → list with registered dataset
- [ ] `GET /api/datasets/<id>` → full document
- [ ] `PUT /api/datasets/<id>` with metadata → updated
- [ ] `POST /api/datasets/<id>/refresh` → stats re-computed
- [ ] `DELETE /api/datasets/<id>` → unregistered, thumbnails cleaned
```

---

## Phase 24: Datasets Left Panel & Registration (v2.1)

### Overview
Rename the left panel "Directories" tab to **Datasets**. Add a registered datasets list (from MongoDB) at the top, with **[+ Add Current]** and **[📊 Dashboard]** buttons. Remove the "Recent" button from the top-right toolbar. Implement the registration flow from the UI.

### 24.1 Left Panel Tab Rename
- [x] Rename "Directories" tab button text to "Datasets"
- [x] Update `data-tab` attribute and related JS references
- [x] Verify tab switching still works with Filters tab

### 24.2 Registered Datasets Section
- [x] Add "Registered (N)" collapsible section at top of panel
- [x] Fetch list from `GET /api/datasets` on init
- [x] Render each dataset: status dot (verdict color), name, path, image count
- [x] Click → activate dataset (reuse browse-mode activation)
- [x] Highlight currently active dataset
- [x] Show "Path not found" warning for missing paths
- [x] Empty state: "No datasets registered yet"

### 24.3 Action Buttons
- [x] **[+ Add Current]** — registers currently activated dataset to MongoDB
  - Disabled when no dataset active or MongoDB unavailable
  - Calls `POST /api/datasets` with current `browseState.activePath`
  - Shows notification on success/duplicate/error
- [x] **[📊 Dashboard]** — opens dashboard modal (Phase 25)
  - Disabled when MongoDB unavailable

### 24.4 Browse Directories Section
- [x] Move existing directory tree below a "Browse Directories" sub-header
- [x] Add divider line between registered and browse sections
- [x] All existing directory browsing functionality preserved

### 24.5 Remove "Recent" Button
- [x] Delete "Recent" button from top-right toolbar HTML
- [x] Remove `loadRecentDatasets()` and related JS if present
- [x] Clean up any recent datasets state/storage

### 24.6 Integration
- [x] Call `initDatasetsPanel()` on app startup
- [x] Call `updateAddCurrentButton()` on dataset activate/deactivate
- [x] Call `renderRegisteredDatasets()` after registration changes
- [x] MongoDB unavailable → buttons grayed, message shown, no errors

**Deliverable:** Datasets panel with registered list, add/dashboard buttons, no Recent button

### README Increment (Phase 24)

```markdown
## Testing Phase 24

### Test 24.1: Tab Rename
- [ ] Left panel tab now reads "Datasets" (not "Directories")
- [ ] Click Datasets ↔ Filters tabs → both work

### Test 24.2: Registered Datasets List
- [ ] No datasets → shows empty state message
- [ ] Register a dataset (via Phase 23 API or Add Current)
- [ ] Verify it appears in list with name, path, status dot
- [ ] Click on it → navigates to dir, activates dataset
- [ ] Active dataset highlighted in list

### Test 24.3: Add Current Button
- [ ] No dataset active → button disabled
- [ ] Activate a dataset → button enabled
- [ ] Click → dataset registered, appears in list
- [ ] Click again → "already registered" toast

### Test 24.4: Recent Button Removed
- [ ] No "Recent" button in top-right toolbar
- [ ] No console errors related to recent datasets

### Test 24.5: MongoDB Unavailable
- [ ] Stop MongoDB, restart app
- [ ] "+ Add Current" and "Dashboard" buttons grayed out
- [ ] Empty state says "MongoDB not available"
- [ ] All other features work normally
```

---

## Phase 25: Datasets Dashboard Modal & Detail View (v2.1)

### Overview
Implement the full-screen dashboard modal. Lists all registered datasets as cards with 4 thumbnails, metadata summary, and "Open" action. Clicking a card shows a detail view with editable metadata, full statistics (class counts + spatial), and actions (Open, Remove, Refresh).

### 25.1 Dashboard Modal Structure
- [x] Full-screen overlay modal (`z-index: 10000`)
- [x] Header: title, ← Back button (detail only), ✕ Close button
- [x] Two views: Card Grid (default) and Detail View
- [x] Escape key: detail → grid → close

### 25.2 Card Grid View
- [x] Fetch all datasets via `GET /api/datasets`
- [x] Render cards in responsive grid: `repeat(auto-fill, minmax(380px, 1fr))`
- [x] Each card displays:
  - Status dot (verdict color) + name
  - 4 thumbnail images (from `/api/datasets/<id>/thumbnails/<i>`)
  - Path (truncated), cycle, quality, model compatibility
  - Total images count
  - "Open" button (activates dataset, closes modal)
  - ⚠️ warning badge if path not found
- [x] Click on card body → opens detail view
- [x] Empty state: instructions to add datasets

### 25.3 Detail View
- [x] Fetch full document via `GET /api/datasets/<id>`
- [x] Thumbnail strip: 4 larger images (180×180)
- [x] Two-column layout (responsive: stacks on narrow screens):
  - **Left — Metadata (editable):** name, (path read-only), description, camera view, quality, verdict, cycle, model compatibility, notes
  - **Right — Statistics (read-only):** total images, class counts (car/motorcycle/truck/bus), spatial stats (position μ/σ², area μ/σ²), computed timestamp

### 25.4 Auto-Save
- [x] All editable fields auto-save on change (debounced 500ms)
- [x] Calls `PUT /api/datasets/<id>` with updated metadata
- [x] Refreshes left panel registered list after save

### 25.5 Detail Actions
- [x] **[Open Dataset]** — closes modal, activates dataset in main view
- [x] **[🗑️ Remove from Dashboard]** — confirmation prompt, `DELETE /api/datasets/<id>`, returns to grid
- [x] **[🔄 Refresh Statistics]** — `POST /api/datasets/<id>/refresh`, reloads detail view

### 25.6 Path Validation
- [x] If `path_exists: false` in summary → card shows warning badge, reduced opacity
- [x] Detail view shows "⚠️ Path not found" next to path
- [x] "Open Dataset" disabled if path not found

### 25.7 Keyboard Shortcuts
- [x] `Escape` in detail view → back to grid
- [x] `Escape` in grid view → close modal
- [x] No interference with main app shortcuts while modal is open

**Deliverable:** Complete dashboard modal with card grid, detail view, and all CRUD actions

### README Increment (Phase 25)

```markdown
## Testing Phase 25

### Test 25.1: Open Dashboard
- [ ] Click "📊 Dashboard" in left panel → full-screen modal opens
- [ ] Escape closes modal

### Test 25.2: Card Grid
- [ ] Registered datasets shown as cards
- [ ] Each card: name, 4 thumbnails, path, cycle, quality, model, total count
- [ ] "Open" button → dataset activates, modal closes
- [ ] Click card → detail view opens

### Test 25.3: Detail View
- [ ] 4 larger thumbnails shown at top
- [ ] All metadata fields populated and editable
- [ ] Change quality dropdown → auto-saved
- [ ] Change model compatibility → auto-saved
- [ ] Type in Notes → auto-saved

### Test 25.4: Statistics
- [ ] Total images, car/motorcycle/truck/bus counts shown
- [ ] Position mean/variance shown
- [ ] Area mean/variance shown
- [ ] "Refresh" button re-computes

### Test 25.5: Actions
- [ ] "Open Dataset" → activates, closes modal
- [ ] "Remove" → confirmation → card disappears
- [ ] "← Back" → returns to card grid

### Test 25.6: Path Not Found
- [ ] Register dataset, then rename the dir on disk
- [ ] Refresh dashboard → card shows ⚠️, reduced opacity
- [ ] Detail view shows warning next to path
```

---

See specs for detailed implementation:
- **[spec_phase23_mongodb_backend.md](specs/spec_phase23_mongodb_backend.md)**
- **[spec_phase24_datasets_panel.md](specs/spec_phase24_datasets_panel.md)**
- **[spec_phase25_dashboard_modal.md](specs/spec_phase25_dashboard_modal.md)**

---

## Phase 26: Dataset Info → MongoDB Sync & Dataset Config (v2.2)

### Overview
Eliminate the dual-source-of-truth problem between `.dataset.json` and MongoDB. When a dataset is registered, all metadata edits from the Dataset Info panel sync to MongoDB on save. The "Stats Config" section is expanded into "Dataset Config" — storing operational settings (visible labels, quality flags, stats fields) that are applied automatically when the dataset is opened. MongoDB becomes the metadata authority for registered datasets.

### 26.1 MongoDB Schema Extension
- [x] Add `config` field to MongoDB dataset document
- [x] `config.stats_fields` — array of field names for statistics
- [x] `config.visible_labels` — array of label fields shown in grid overlay
- [x] `config.quality_flags` — array of quality flag option strings
- [x] `config.skip_delete_confirmation` — boolean
- [x] Add `metadata.trainable_models` — array of `{name, enabled, preprocessing}`
- [x] Add `metadata.attributes` — array of `{name, enabled}`
- [x] Update `POST /api/datasets` (register) to read full config + trainable_models + attributes from `.dataset.json`
- [x] Lazy migration: on `GET /api/datasets/<id>`, if `config` field is missing, return defaults

### 26.2 Metadata Sync on Save
- [x] Backend helper `_find_registered_dataset(root_path)` — lookup MongoDB doc by path
- [x] Backend helper `_sync_metadata_to_mongodb(root_path, metadata_updates)` — update MongoDB document
- [x] Modify `PUT /api/dataset/metadata` to also update MongoDB if dataset is registered
- [x] Sync fields: name, description, camera_view, quality, verdict, cycle, notes
- [x] Sync trainable_models to `metadata.trainable_models` in MongoDB
- [x] Sync attributes to `metadata.attributes` in MongoDB
- [x] If MongoDB write fails → log warning, don't block `.dataset.json` save
- [x] Frontend: after save success, if synced, show "✓ Synced to DB" notification

### 26.3 Rename Stats Config → Dataset Config
- [x] HTML: rename section title "Stats Config" → "Dataset Config"
- [x] HTML: add Visible Labels checkbox group (color, brand, model, label, type, sub_type, lp_coords)
- [x] HTML: add Quality Flags editable list (add/remove items)
- [x] JS: `saveStatsConfig()` → `saveDatasetConfig()` — collects stats_fields + visible_labels + quality_flags
- [x] Backend: new `PUT /api/dataset/config` replaces `PUT /api/dataset/stats-config`
- [x] Backend: `PUT /api/dataset/config` writes to `.dataset.json` AND MongoDB (if registered)
- [x] CSS: style the new config fields consistently

### 26.4 Apply Config on Dataset Open
- [x] Backend: `POST /api/browse/activate` — check if `root_path` is registered in MongoDB
- [x] If registered: load metadata + config from MongoDB, merge with `.dataset.json` `image_flags`
- [x] If not registered: unchanged legacy flow (load from `.dataset.json`)
- [x] Frontend: on activation response, apply `config.visible_labels` → update `visibleLabels`
- [x] Frontend: apply `config.quality_flags` → update `projectData.settings.quality_flags`
- [x] Frontend: apply `config.stats_fields` → pass to `loadDatasetStats()`
- [x] Frontend: populate Dataset Config section with loaded values

### 26.5 Sync Indicator
- [x] Add sync status element to metadata panel header
- [x] States: "✓ Synced" (green) | "Local only" (orange) | "⚠ Sync failed" (red)
- [x] On dataset activation: check MongoDB registration → set indicator
- [x] On save success: update indicator based on sync result

### 26.6 Dashboard Bidirectional Consistency
- [x] Dashboard detail view edits (`PUT /api/datasets/<id>`) also write to `.dataset.json`
- [x] When opening Dataset Info after dashboard edit → shows latest values
- [x] When opening Dashboard after panel edit → shows latest values
- [x] Both views always reflect the same data

---

### Test 26.1: Metadata Sync
- [ ] Activate a registered dataset
- [ ] Edit name/description/verdict in Dataset Info panel → Save
- [ ] Open Dashboard → detail shows updated values
- [ ] Edit in Dashboard → go back to Dataset Info → shows updated values

### Test 26.2: Trainable Models + Attributes Sync
- [ ] Toggle a model in Dataset Info → check MongoDB document updated
- [ ] Add custom attribute → check MongoDB document updated
- [ ] Open Dashboard detail → trainable_models and attributes visible

### Test 26.3: Dataset Config
- [ ] Change visible labels in Dataset Config → Apply
- [ ] Grid overlay shows only selected labels
- [ ] Deactivate, reactivate → same visible labels applied
- [ ] Change quality flags → Apply → quality flag options update

### Test 26.4: Apply Config on Open
- [ ] Register dataset with custom config (stats_fields=label only, visible_labels=color,type)
- [ ] Deactivate → reactivate
- [ ] Stats section shows only "label" field
- [ ] Grid overlay shows only "color" and "type"
- [ ] Quality flags match saved config

### Test 26.5: Non-Registered Dataset (Backwards Compat)
- [ ] Activate a directory that is NOT registered in MongoDB
- [ ] Dataset Info panel works normally (save to `.dataset.json` only)
- [ ] Sync indicator shows "Local only"
- [ ] Stats Config / Dataset Config works via `.dataset.json`

### Test 26.6: Lazy Migration
- [ ] Dataset registered before v2.2 (no `config` field in MongoDB)
- [ ] Open in v2.2 → config defaults applied, no errors
- [ ] Save config → `config` field created in MongoDB

---

See spec for detailed implementation:
- **[spec_phase26_dataset_sync.md](specs/spec_phase26_dataset_sync.md)**






















































Errors:
1. OK! I can't open the imagens
2. The labels are not being changed when I press Q. I prefer to use the numbers (from 1 to n) that change the quality image. I hover the image and pressn the number and it change the quality


1. The direction must to be in the view dropdown;
2. I want a new set of labels aside quality
3. I want a color for each cycle, and a differente view for each one
4. Create a convetion to the dataset (all the vehicles labeled, as an example)