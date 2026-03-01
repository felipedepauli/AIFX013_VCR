# Product Requirements Document: Image Review Tool v2

## 1. Overview

### 1.1 Purpose
A web-based image review tool designed for efficient batch image review, annotation, and management with quality flag tracking.

### 1.2 Target Users
- Data annotators
- Dataset quality reviewers
- Machine learning engineers reviewing training data

---

## 2. Core Features

### 2.1 Image Grid Display (P0)

**Requirements:**
- Display images in configurable grid layouts
- Grid size options: 4, 9, 25, or 36 images
- Grid button/selector to switch between layouts
- Default: 4-image grid (2x2)
- Equal distribution of images in grid cells
- Responsive layout that maintains aspect ratios

**User Flow:**
1. User clicks grid size button
2. Options display: 2x2 (4), 3x3 (9), 5x5 (25), 6x6 (36)
3. Grid reflows to selected layout
4. Images fill grid sequentially from top-left to bottom-right

---

### 2.2 Label Visualization (P0)

**Requirements:**
- Draw labels/annotations on each image
- Toggle button to select which labels to display
- Support multiple label types simultaneously
- Labels persist with image state in JSON

**Label Controls:**
- Checkbox/multi-select interface for label types
- Individual label type visibility toggle
- Labels stored in per-image JSON files (same name as image)

**Label Structure:**
```
[User to provide label structure]
```

---

### 2.3 Image Controls (P0)

**Requirements:**
Each image must have controls at the top with the following actions:

#### 2.3.1 Select
- Checkbox or toggle to mark image for batch operations
- Visual indication when selected (border, overlay, etc.)
- Select state persists until operation or manual deselection

#### 2.3.2 Open Wider
- Opens image in larger view/modal
- Shows full resolution
- Maintains current label visibility settings
- Easy return to grid view

#### 2.3.3 Delete
- Removes image from filesystem
- Behavior controlled by deletion confirmation setting (see 2.4)
- Image disappears from grid immediately
- Next image fills the space automatically

---

### 2.4 Deletion Behavior Settings (P1)

**Requirements:**
- Setting toggle: "Confirm before deletion"
- When **enabled**: Show confirmation dialog for each delete action
- When **disabled**: Delete immediately without confirmation
- Applies to both individual and batch delete operations

**Confirmation Dialog:**
- Message: "Delete [filename]?" or "Delete [N] selected images?"
- Actions: "Delete" / "Cancel"

---

### 2.5 Batch Operations (P0)

#### 2.5.1 Batch Delete
**Requirements:**
- Control button: "Delete Selected"
- Deletes all images with active selection
- Respects deletion confirmation setting
- Grid updates immediately, filling with next images

#### 2.5.2 Batch Move
**Requirements:**
- Control button: "Move Selected"
- Moves selected images to target directory
- Target directories configurable in settings (see 2.9.2)
- Only directories in same parent as source images
- Moved images disappear from grid
- Next images fill the space

**User Flow:**
1. User selects multiple images
2. Clicks "Move Selected"
3. Dropdown/modal shows available target directories
4. User selects target
5. Images move and grid updates

---

### 2.6 Quality Flags (P0)

**Requirements:**
- Assign quality flags to images
- Multiple flags per image supported
- Flags display at bottom of each image
- Modal/panel for flag assignment

**User Flow:**
1. User clicks "Flag" button on image
2. Flag selection modal opens
3. User selects one or more flags from available options
4. Flags saved to master JSON
5. Flags display at bottom of image in grid

**Flag Display:**
- Compact visual representation (badges, icons, or text)
- Color-coded for easy recognition
- Does not obscure image content

---

### 2.7 Flag Categories (P1)

**Default Flags:**
- QUALITY_EXCELLENT
- QUALITY_GOOD
- QUALITY_FAIR
- QUALITY_POOR
- QUALITY_UNUSABLE
- BLUR
- OCCLUSION
- TRUNCATION
- LIGHTING_ISSUE
- ANNOTATION_ERROR

**Additional flags configurable via settings (see 2.8)**

---

### 2.8 Flag Management (P1)

**Requirements:**
- Settings interface to add/remove custom flags
- Only flags defined in settings can be assigned
- Flag list shared across all images in session

**Settings Interface:**
- List of current flags
- "Add Flag" button → Input field for new flag name
- Delete button per flag (with confirmation)
- Flag naming rules: UPPERCASE_WITH_UNDERSCORES

---

### 2.9 Settings Panel (P0)

#### 2.9.1 Access
- Gear icon (⚙️) in top-right corner
- Opens settings panel (modal or slide-out)

#### 2.9.2 Settings Structure

**Display Settings:**
- Grid size selection (4, 9, 25, 36)
- Label visibility defaults

**Behavior Settings:**
- Confirm before deletion toggle

**Directory Settings:**
- List of available move-to directories
- Add directory button (creates directory if not exists)
- Remove directory button
- Directories must be siblings to source image directory

**Flag Settings:**
- Manage custom flags (see 2.8)
- View all available flags

**Data Settings:**
- Master JSON file location
- Auto-save interval

---

### 2.10 Data Persistence (P0)

#### 2.10.1 Master JSON File

**Requirements:**
- Single JSON file tracking all reviewed images
- File structure:

```json
{
  "images": [
    {
      "id": "img_0001",
      "path": "relative/path/to/image.jpg",
      "flags": ["QUALITY_GOOD", "BLUR"],
      "enabled_labels": {
        "label_type_1": true,
        "label_type_2": false
      },
      "reviewed_at": "2026-02-13T10:30:00Z",
      "reviewed_by": "user_id"
    }
  ],
  "metadata": {
    "version": "2.0",
    "created_at": "2026-02-13T09:00:00Z",
    "last_updated": "2026-02-13T10:30:00Z"
  }
}
```

**Fields:**
- `id`: Sequential identifier (img_0001, img_0002, etc.)
- `path`: Relative or absolute path to image
- `flags`: Array of assigned quality flags
- `enabled_labels`: Object mapping label types to visibility state
- `reviewed_at`: ISO 8601 timestamp of last review
- `reviewed_by`: Optional user identifier

#### 2.10.2 Per-Image Label JSON

**Requirements:**
- Each image has corresponding JSON file with same name
- Contains label/annotation data
- Structure: [User to provide]

**Example:**
- Image: `dataset/img_001.jpg`
- Labels: `dataset/img_001.json`

---

## 3. User Experience

### 3.1 Navigation Flow

1. **Initial Load**
   - Load images from configured directory
   - Display in default 4-image grid
   - Load existing flags from master JSON

2. **Review Workflow**
   - User reviews images in grid
   - Assigns flags as needed
   - Selects images for batch operations
   - Deletes or moves unwanted images
   - Grid automatically loads next images

3. **Settings Access**
   - Gear icon always visible
   - Quick access to configuration
   - Changes apply immediately

### 3.2 Keyboard Shortcuts (P2 - Future)

Potential shortcuts:
- `1`, `2`, `3`, `4`: Switch grid size
- `Space`: Toggle selection on focused image
- `Delete`: Delete selected images
- `F`: Open flag modal for selected images
- `→` / `←`: Navigate images

---

## 4. Technical Requirements

### 4.1 Frontend
- Responsive web interface
- Modern browser support (Chrome, Firefox, Safari, Edge)
- JavaScript framework (React/Vue/vanilla JS)
- CSS Grid for image layout

### 4.2 Backend
- Python/Flask or Node.js
- File system operations (move, delete)
- JSON read/write operations
- Directory scanning and management

### 4.3 Data
- JSON for structured data
- File-based storage (no database required)
- Atomic file operations for data integrity

### 4.4 Performance
- Lazy loading for large image sets
- Image thumbnail generation
- Efficient grid rendering (virtual scrolling for large grids)

---

## 5. Non-Functional Requirements

### 5.1 Usability
- Intuitive interface requiring minimal training
- Visual feedback for all actions
- Undo capability for accidental deletions (P2)

### 5.2 Reliability
- Data persistence on every change
- Graceful error handling
- Validation for file operations

### 5.3 Scalability
- Support for large datasets (1000+ images)
- Performance degradation graceful with grid size

---

## 6. Open Questions

1. **Label Structure**: What is the exact JSON structure for per-image labels?
2. **Image Formats**: Which image formats to support? (JPG, PNG, WEBP?)
3. **Image Sources**: Single directory or recursive directory scanning?
4. **Authentication**: Is user authentication required?
5. **Multi-user**: Support for concurrent users?
6. **History**: Track full revision history of flag changes?
7. **Export**: Export filtered/flagged image lists?
8. **Undo**: Implement undo/redo functionality?

---

## 7. Future Enhancements (Post-MVP)

- Keyboard shortcuts
- Bulk flag operations
- Search/filter by flags
- Export reports
- Annotation editing
- Image comparison view
- Statistics dashboard
- Batch import/export

---

## 8. Success Metrics

- Time to review N images
- Error rate in image categorization
- User satisfaction score
- Tool adoption rate
- Data quality improvement metrics

---

## 9. Timeline

**Phase 1**: Core grid display + basic controls (1 week)
**Phase 2**: Flag system + master JSON (1 week)
**Phase 3**: Settings panel + directory management (1 week)
**Phase 4**: Polish + testing (1 week)

---

## Appendix A: Label Structure

**[To be completed by user]**

Please provide the exact JSON structure for per-image label files.
