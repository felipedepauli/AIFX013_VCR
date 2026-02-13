# Development Plan: Image Review & Annotation Tool

## Project Overview

**Project Name:** Image Review Tool  
**Tech Stack:** Python Flask + Vanilla JS/HTML/CSS  
**Status:** v1.0 Complete ✅ | v1.1 (Filters) In Progress 🔄

---

## Release History

| Version | Status | Phases | Date |
|---------|--------|--------|------|
| v1.0 | ✅ Complete | Phase 1-9 | Feb 2026 |
| v1.1 | 🔄 In Progress | Phase 10 (Filters) | Feb 2026 |

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

## Phase 1: Project Setup & Infrastructure (Day 1)

### 1.1 Project Setup Modal (Startup)
- [ ] Create startup modal that opens on launch
- [ ] Directory selector (browse for image folder)
- [ ] Project name input field
- [ ] Default quality flags checkboxes: `bin`, `review`, `ok`, `move`
- [ ] Default perspective flags checkboxes: `close-up-day`, `close-up-night`, etc.
- [ ] Default visible labels selection
- [ ] "Create Project" button
- [ ] "Open Recent" dropdown for existing projects

### 1.2 Project Manager Class
- [ ] Create `ProjectManager` class for project JSON operations
- [ ] `create_project(name, directory, defaults)` method
- [ ] `load_project(name)` method
- [ ] `save_project()` auto-save method
- [ ] Generate project file: `{project_name}.json`

### 1.3 Data Layer
- [ ] Create `LabelManager` class for per-image JSON operations
- [ ] Implement image discovery (scan directory for images)
- [ ] Map images to their JSON label files
- [ ] Initialize image entries in project JSON

### 1.4 Flask App & Routes
- [ ] Create `image_review_tool.py` main file
- [ ] Setup Flask routes structure
- [ ] Create HTML template skeleton
- [ ] Setup CSS grid system for responsive layout

### 1.5 API Endpoints (Basic)
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

**Deliverable:** Working project setup flow + basic Flask app

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

## Phase 2: Grid View Display (Day 2)

### 2.1 Image Grid Component
- [ ] Create CSS grid with 2x2, 3x3, 5x5, 6x6 layouts
- [ ] Implement grid selector buttons
- [ ] Add pagination logic (calculate pages based on grid size)
- [ ] Create image card component

### 2.2 Image Loading & Display
- [ ] Implement thumbnail generation (resize for grid)
- [ ] Create base64 encoding for web display
- [ ] Add lazy loading with intersection observer
- [ ] Implement page navigation (Previous/Next)

### 2.3 API Endpoints
```python
GET  /api/images?page=1&grid_size=9   # Paginated images
GET  /api/thumbnail/<id>               # Get thumbnail
```

**Deliverable:** Working grid view with pagination

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

## Phase 3: Label Overlay System (Day 2-3)

### 3.1 Label Rendering
- [ ] Parse label JSON for each image
- [ ] Calculate bounding box center point
- [ ] Draw labels on canvas overlay
- [ ] Stack multiple labels vertically
- [ ] Handle NULL values for missing labels

### 3.2 Label Visibility Controls
- [ ] Create label toggle checkboxes
- [ ] Implement label filter state
- [ ] Update display when labels toggled
- [ ] Persist label visibility in settings

### 3.3 Bounding Box Drawing
- [ ] Draw rectangles from `rect` [x,y,w,h]
- [ ] Color coding for different objects
- [ ] Semi-transparent fill

### 3.4 API Endpoints
```python
GET  /api/labels/<image_id>           # Get labels for image
POST /api/settings/visible_labels     # Update visible labels
```

**Deliverable:** Images with label overlays

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

## Phase 4: Per-Image Controls (Day 3)

### 4.1 Control Buttons
- [ ] Create selection checkbox (top-left)
- [ ] Create "Open Wider" button with modal
- [ ] Create "Delete" button
- [ ] Create "Flag" button
- [ ] Style hover states

### 4.2 Selection System
- [ ] Track selected images in state
- [ ] Visual indicator for selected images
- [ ] Select/Deselect all functionality
- [ ] Selection counter in toolbar

### 4.3 Modal: Open Wider
- [ ] Create fullscreen modal component
- [ ] Load full-resolution image
- [ ] Display all labels
- [ ] Close on click outside / Escape

### 4.4 API Endpoints
```python
POST /api/select                      # Update selection state
GET  /api/image/<id>/full             # Get full resolution
```

**Deliverable:** Interactive image cards with controls

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

## Phase 5: Delete Operations (Day 4)

### 5.1 Delete Functionality
- [ ] Single image delete button handler
- [ ] Confirmation dialog (when setting OFF)
- [ ] "Skip confirmation" setting toggle in UI
- [ ] Bulk delete for selected images
- [ ] Remove from grid, shift remaining images
- [ ] Update project JSON (remove image entry)

### 5.2 API Endpoints
```python
POST /api/delete/<image_id>           # Delete single
POST /api/delete/bulk                 # Delete selected
```

**Deliverable:** Working delete with file operations

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

## Phase 6: Flags System - Quality & Perspective (Day 4-5)

### 6.1 Flag Modal Component
- [ ] Two-section modal: Quality Flags + Perspective Flags
- [ ] Quality flags section with checkboxes (default: bin, review, ok, move)
- [ ] Perspective flags section with checkboxes (default: close-up-day, close-up-night, pan-day, pan-night, super_pan_day, super_pan_night, cropped-day, cropped-night)
- [ ] Apply/Cancel buttons
- [ ] Load current flags from project JSON for image

### 6.2 Flag Display
- [ ] Display flags at bottom of image card
- [ ] Color-code by type (quality = blue, perspective = green)
- [ ] Compact display for multiple flags

### 6.3 Bulk Operations
- [ ] "Flag Selected" button in toolbar
- [ ] Apply flags to all selected images
- [ ] Quick keyboard shortcut Q (cycle quality) and P (perspective modal)

### 6.4 Flag Storage
- [ ] Store flags in project JSON per image
- [ ] If no flags set, apply project defaults
- [ ] Read flags from project JSON on load

### 6.5 Flag Configuration (Settings)
- [ ] UI to add new quality flags
- [ ] UI to add new perspective flags
- [ ] UI to remove flags
- [ ] Persist to project JSON

### 6.6 API Endpoints
```python
GET  /api/flags                           # List all flags (quality + perspective)
POST /api/flags/quality                   # Add quality flag
POST /api/flags/perspective               # Add perspective flag
DELETE /api/flags/<type>/<name>           # Remove flag
POST /api/image/<id>/flags                # Update image flags
POST /api/flags/bulk                      # Bulk update flags
```

**Deliverable:** Complete dual-category flag system

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

## Phase 7: Inline Label Editing (Day 5)

### 7.1 Editable Labels
- [ ] Click-to-edit on label text
- [ ] Inline input field component
- [ ] Save on Enter/blur
- [ ] Cancel on Escape
- [ ] Visual feedback on save

### 7.2 JSON Update Logic
- [ ] Read current JSON
- [ ] Update only changed field
- [ ] Write back to file (atomic)
- [ ] Handle multiple objects in JSON
- [ ] Error handling for file operations

### 7.3 API Endpoints
```python
PUT  /api/labels/<image_id>/<obj_idx>/<field>  # Update label field
```

**Deliverable:** Working inline editing with JSON persistence

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

## Phase 8: Settings Panel (Day 5-6)

### 8.1 Settings UI
- [ ] Gear icon button (⚙️)
- [ ] Settings sidebar/modal
- [ ] Tab sections: General, Labels, Quality Flags, Perspective Flags

### 8.2 Settings Sections
- [ ] General: Skip delete confirmation, project info display
- [ ] Labels: Toggle visible labels
- [ ] Quality Flags: Add/remove quality flags
- [ ] Perspective Flags: Add/remove perspective flags
- [ ] Defaults: Set default quality/perspective flags for new images

### 8.3 Persistence
- [ ] Save settings to project JSON
- [ ] Load settings from project on startup
- [ ] Real-time UI updates
- [ ] Display current project name in header

**Deliverable:** Complete settings panel

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

## Phase 9: Polish & Testing (Day 6-7)

### 9.1 Keyboard Shortcuts
- [ ] Implement all shortcuts from PRD
- [ ] Show shortcuts help modal
- [ ] Visual indicators for shortcuts

### 9.2 Error Handling
- [ ] File operation errors
- [ ] Network errors
- [ ] Invalid data handling
- [ ] User-friendly error messages

### 9.3 Performance Optimization
- [ ] Image caching
- [ ] Debounce API calls
- [ ] Memory cleanup

### 9.4 Testing
- [ ] Test with large datasets (1000+ images)
- [ ] Test all CRUD operations
- [ ] Test edge cases (missing JSON, etc.)

**Deliverable:** Production-ready tool

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

### v1.1 - Filter Panel 🔄

12. 🔄 Phase 10: Filter Panel (In Progress)

---

## Phase 10: Filter Panel (v1.1)

### Overview
Add a collapsible left sidebar filter panel to filter images by labels and flags.

### 10.1 Filter Panel UI
- [ ] Create collapsible left sidebar component
- [ ] Add toggle button in header (`[` key shortcut)
- [ ] Smooth slide animation for open/close
- [ ] Persist panel state in session

### 10.2 Filter Sections
- [ ] Quality Flags section with checkboxes
- [ ] Perspective Flags section with checkboxes
- [ ] Label sections (Color, Brand, Model, Type, etc.)
- [ ] Collapsible sections with expand/collapse
- [ ] Show count of matching images per option

### 10.3 Filter Logic
- [ ] AND logic for multiple filters
- [ ] Real-time filtering (no submit button)
- [ ] Update pagination for filtered results
- [ ] Cache filter results for performance

### 10.4 Active Filters Display
- [ ] Show active filters as chips in toolbar
- [ ] Click chip to remove individual filter
- [ ] "Clear All Filters" button
- [ ] Show filtered count vs total count

### 10.5 Search Within Filters
- [ ] Search box at top of filter panel
- [ ] Filter options as user types
- [ ] Highlight matching options

### 10.6 API Endpoints
```python
GET  /api/filter/options          # Get all filterable options with counts
GET  /api/images?filters=...      # Get images with filter query
```

**Deliverable:** Complete filter panel with label and flag filtering

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
