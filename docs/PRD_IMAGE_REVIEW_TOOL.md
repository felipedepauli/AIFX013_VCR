# PRD: Image Review & Annotation Tool

## Product Overview

### Vision
A web-based tool for reviewing, annotating, and managing vehicle detection datasets with support for grid visualization, label editing, quality flagging, and batch operations.

### Problem Statement
Current annotation tools lack efficient batch review capabilities. Reviewers need to quickly scan multiple images, verify labels, flag quality issues, and reorganize datasets without switching between individual images.

### Target Users
- Data annotation reviewers
- ML engineers validating datasets
- Quality assurance teams

### Release Status

| Version | Status | Date |
|---------|--------|------|
| v1.0 | ✅ Complete | Feb 2026 |
| v1.1 (Filters) | 🔄 In Progress | Feb 2026 |

---

## Functional Requirements

### FR-01: Grid View Display ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01.1 | Display images in configurable grid: 2x2 (4), 3x3 (9), 5x5 (25), or 6x6 (36) | P0 | ✅ |
| FR-01.2 | Grid selector buttons in toolbar | P0 | ✅ |
| FR-01.3 | Images fill grid left-to-right, top-to-bottom | P0 | ✅ |
| FR-01.4 | When images are removed, remaining images shift to fill gaps | P0 | ✅ |
| FR-01.5 | Lazy loading for performance (load visible + buffer) | P1 | ✅ |
| FR-01.6 | Pagination controls (Previous/Next page) | P0 | ✅ |

### FR-02: Label Overlay on Images ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-02.1 | Draw labels at center of each detected object (bounding box) | P0 | ✅ |
| FR-02.2 | Each label on its own line, vertically stacked | P0 | ✅ |
| FR-02.3 | Label visibility toggle button (select which labels to show) | P0 | ✅ |
| FR-02.4 | Available labels from JSON: color, brand, model, label, type, sub_type | P0 | ✅ |
| FR-02.5 | If label not in JSON, display "NULL" | P0 | ✅ |
| FR-02.6 | Label text styling: semi-transparent background, readable font | P1 | ✅ |
| FR-02.7 | Draw bounding box rectangle around detected objects | P1 | ✅ |

### FR-03: Per-Image Controls ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-03.1 | Checkbox for selection (top-left corner) | P0 | ✅ |
| FR-03.2 | "Open Wider" button - opens image in modal/fullscreen | P0 | ✅ |
| FR-03.3 | "Delete" button - marks image for deletion | P0 | ✅ |
| FR-03.4 | Visual indicator when image is selected | P0 | ✅ |
| FR-03.5 | Hover state shows controls more prominently | P1 | ✅ |

### FR-04: Deletion Behavior ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-04.1 | Setting: "Skip delete confirmation" (default: OFF) | P0 | ✅ |
| FR-04.2 | When OFF: Show confirmation dialog before each delete | P0 | ✅ |
| FR-04.3 | When ON: Delete immediately without confirmation | P0 | ✅ |
| FR-04.4 | Deleted images removed from grid, next images fill space | P0 | ✅ |
| FR-04.5 | "Delete All Selected" bulk action button | P0 | ✅ |

### FR-05: Project Setup (Startup Modal) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-05.1 | On app launch, show Project Setup modal | P0 | ✅ |
| FR-05.2 | Field: Select directory with images (file browser) | P0 | ✅ |
| FR-05.3 | Field: Project name (used for JSON filename) | P0 | ✅ |
| FR-05.4 | Field: Default quality flags (multi-select) | P0 | ✅ |
| FR-05.5 | Field: Default perspective flags (multi-select) | P0 | ✅ |
| FR-05.6 | Field: Default visible labels | P0 | ✅ |
| FR-05.7 | Create project JSON: `{project_name}.json` | P0 | ✅ |
| FR-05.8 | If project JSON exists, load and skip defaults setup | P0 | ✅ |
| FR-05.9 | "Open Recent" dropdown for previously opened projects | P1 | ✅ |

### FR-06: Quality Flags System ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-06.1 | "Flag" button on each image - opens flag modal | P0 | ✅ |
| FR-06.2 | Modal shows Quality Flags and Perspective Flags sections | P0 | ✅ |
| FR-06.3 | Default Quality Flags: `bin`, `review`, `ok`, `move` | P0 | ✅ |
| FR-06.4 | Default Perspective Flags: `close-up-day`, `close-up-night`, `pan-day`, `pan-night`, `super_pan_day`, `super_pan_night`, `cropped-day`, `cropped-night` | P0 | ✅ |
| FR-06.5 | Multiple flags from each category can be applied | P0 | ✅ |
| FR-06.6 | Applied flags displayed at bottom of image (color-coded by type) | P0 | ✅ |
| FR-06.7 | "Flag Selected" bulk action to apply flags to all selected | P1 | ✅ |
| FR-06.8 | Filter view by flag (show only images with specific flag) | P2 | 🔄 Phase 10 |
| FR-06.9 | Flags stored in project JSON (not image JSON) | P0 | ✅ |
| FR-06.10 | If flag not in project JSON, apply defaults from startup | P0 | ✅ |

### FR-07: Settings Panel ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-07.1 | Gear icon (⚙️) in top-right corner | P0 | ✅ |
| FR-07.2 | Click opens settings modal/sidebar | P0 | ✅ |
| FR-07.3 | Setting: Skip delete confirmation (checkbox) | P0 | ✅ |
| FR-07.4 | Setting: Manage quality flags (add/remove) | P0 | ✅ |
| FR-07.5 | Setting: Manage perspective flags (add/remove) | P0 | ✅ |
| FR-07.6 | Setting: Select visible labels | P0 | ✅ |
| FR-07.7 | Settings persisted in project JSON | P0 | ✅ |
| FR-07.8 | Current project name displayed in header | P1 | ✅ |

### FR-08: Project Data (JSON) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-08.1 | One JSON file per project: `{project_name}.json` | P0 | ✅ |
| FR-08.2 | Project info: name, directory, created date, updated date | P0 | ✅ |
| FR-08.3 | Settings: quality_flags[], perspective_flags[], visible_labels[], skip_delete_confirmation | P0 | ✅ |
| FR-08.4 | Image entry: `{seq_id, path, quality_flags[], perspective_flags[], labels{}}` | P0 | ✅ |
| FR-08.5 | `seq_id`: Sequential numeric ID for easy reference | P0 | ✅ |
| FR-08.6 | `quality_flags`: Array of applied quality flags (e.g., ["ok", "review"]) | P0 | ✅ |
| FR-08.7 | `perspective_flags`: Array of applied perspective flags (e.g., ["pan-day"]) | P0 | ✅ |
| FR-08.8 | Auto-save project JSON on changes | P0 | ✅ |
| FR-08.9 | Load flags from project JSON; if missing, use project defaults | P0 | ✅ |

### FR-09: Label JSON Structure ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-09.1 | Read labels from `{image_name}.json` file | P0 | ✅ |
| FR-09.2 | Support multiple objects per image (array) | P0 | ✅ |
| FR-09.3 | Parse `rect` as [x, y, w, h] bounding box | P0 | ✅ |
| FR-09.4 | Extract: color, brand, model, label, type, sub_type, lp_coords | P0 | ✅ |
| FR-09.5 | Handle missing fields gracefully (show NULL) | P0 | ✅ |

### FR-10: Inline Label Editing ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-10.1 | Click on label text makes it editable | P0 | ✅ |
| FR-10.2 | Inline text input for editing | P0 | ✅ |
| FR-10.3 | Save on Enter or blur (click outside) | P0 | ✅ |
| FR-10.4 | Cancel on Escape | P0 | ✅ |
| FR-10.5 | Write changes directly to label JSON file | P0 | ✅ |
| FR-10.6 | Only update changed field, preserve other data | P0 | ✅ |
| FR-10.7 | No confirmation required for edits | P0 | ✅ |
| FR-10.8 | Visual feedback on successful save | P1 | ✅ |

### FR-11: Filter Panel (v1.1) 🔄

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-11.1 | Collapsible left sidebar filter panel | P0 | 🔄 |
| FR-11.2 | Filter by label values (color, brand, model, type, etc.) | P0 | 🔄 |
| FR-11.3 | Filter by quality flags | P0 | 🔄 |
| FR-11.4 | Filter by perspective flags | P0 | 🔄 |
| FR-11.5 | Multiple filters can be combined (AND logic) | P0 | 🔄 |
| FR-11.6 | Active filters shown as removable chips | P0 | 🔄 |
| FR-11.7 | "Clear All Filters" button | P0 | 🔄 |
| FR-11.8 | Real-time filter count (show matching images) | P1 | 🔄 |
| FR-11.9 | Filter state persisted in session | P1 | 🔄 |
| FR-11.10 | Search/filter within filter options | P2 | 🔄 |
| FR-11.11 | Toggle sidebar visibility with keyboard shortcut | P1 | 🔄 |

---

## Non-Functional Requirements

### NFR-01: Performance
- Load 36 images in under 2 seconds
- Image thumbnails cached for grid view
- Full resolution loaded only for "Open Wider"

### NFR-02: Usability
- Keyboard shortcuts for common actions
- Responsive design (minimum 1280px width)
- Clear visual feedback for all actions

### NFR-03: Reliability
- Auto-save all changes
- Backup JSON before destructive operations
- Error handling with user-friendly messages

### NFR-04: Technology
- Python Flask backend (like re_annotate_colors_web.py)
- HTML/CSS/JavaScript frontend
- No external JS dependencies (vanilla JS)
- PIL/Pillow for image processing

---

## Data Models

### Project JSON Schema
```json
{
  "version": "1.0",
  "project_name": "vehicle_colors_v4",
  "directory": "images/xywh/v4/test",
  "created": "2026-02-12T10:00:00",
  "updated": "2026-02-12T15:30:00",
  "settings": {
    "skip_delete_confirmation": false,
    "quality_flags": ["bin", "review", "ok", "move"],
    "perspective_flags": ["close-up-day", "close-up-night", "pan-day", "pan-night", "super_pan_day", "super_pan_night", "cropped-day", "cropped-night"],
    "visible_labels": ["color", "brand", "model", "type"],
    "default_quality_flag": "review",
    "default_perspective_flag": null
  },
  "images": [
    {
      "seq_id": 1,
      "path": "images/xywh/v4/test/000000_ASH4662_1.jpg",
      "json_path": "images/xywh/v4/test/000000_ASH4662_1.json",
      "quality_flags": ["ok"],
      "perspective_flags": ["pan-day"],
      "labels": {
        "color": "silver",
        "brand": "honda",
        "type": "auto"
      }
    }
  ]
}
```

### Label JSON Schema (per image)
```json
[
  {
    "rect": [1, 580, 562, 563],
    "color": "silver",
    "brand": "honda",
    "model": "city",
    "label": "car",
    "type": "auto",
    "sub_type": "au - sedan compacto",
    "lp_coords": ""
  }
]
```

---

## User Interface Mockup

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🖼️ Image Review Tool - vehicle_colors_v4   [2x2] [3x3] [5x5] [6x6]    ⚙️  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Labels: [color ▼] [brand ▼] [type ▼]  |  Actions: [Delete Selected] [Flag] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐                          │
│  │ [☐] [🔍] [🗑️] [🏷️] │  │ [☑] [🔍] [🗑️] [🏷️] │                          │
│  │                     │  │                     │                          │
│  │    ┌─────────┐      │  │    ┌─────────┐      │                          │
│  │    │  🚗    │      │  │    │  🚗    │      │                          │
│  │    │ silver  │      │  │    │ white   │      │                          │
│  │    │ honda   │      │  │    │ toyota  │      │                          │
│  │    │ auto    │      │  │    │ auto    │      │                          │
│  │    └─────────┘      │  │    └─────────┘      │                          │
│  │                     │  │                     │                          │
│  │ [ok] [pan-day]      │  │ [review]            │                          │
│  └─────────────────────┘  └─────────────────────┘                          │
│                                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐                          │
│  │ [☐] [🔍] [🗑️] [🏷️] │  │ [☐] [🔍] [🗑️] [🏷️] │                          │
│  │         ...         │  │         ...         │                          │
│  └─────────────────────┘  └─────────────────────┘                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Page 1 of 125  |  Total: 500 images  |  Selected: 2  |  ◀ Prev  Next ▶    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `←` / `→` | Previous / Next page |
| `A` | Select all on current page |
| `D` | Deselect all |
| `Delete` | Delete selected images |
| `F` | Flag selected (opens flag modal) |
| `Q` | Quick quality flag (cycles: bin → review → ok → move) |
| `P` | Quick perspective flag modal |
| `Escape` | Close any open modal |
| `1-4` | Switch grid size (1=2x2, 2=3x3, 3=5x5, 4=6x6) |
| `,` | Open settings |
| `?` | Show keyboard shortcuts help |
| `Space` | Open hovered image wider |
| `[` | Toggle filter panel (v1.1) |

---

## User Interface Mockup (v1.1 with Filter Panel)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ 🖼️ Image Review Tool - vehicle_colors_v4   [2x2] [3x3] [5x5] [6x6]  [?] ⚙️            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ Labels: [color ▼]  |  Active: [color: white ✕] [ok ✕]        [Clear All] 42 of 500    │
├────────────────────┬────────────────────────────────────────────────────────────────────┤
│ ◀ FILTERS          │                                                                    │
│                    │  ┌─────────────────────┐  ┌─────────────────────┐                  │
│ ┌────────────────┐ │  │ [☐] [🔍] [🗑️] [🏷️] │  │ [☑] [🔍] [🗑️] [🏷️] │                  │
│ │ 🔍 Search...   │ │  │    [white]          │  │    [white]          │                  │
│ └────────────────┘ │  │    [toyota]         │  │    [honda]          │                  │
│                    │  │ [ok] [pan-day]      │  │ [ok]                │                  │
│ ▼ Quality Flags    │  └─────────────────────┘  └─────────────────────┘                  │
│   ☑ ok       (25)  │                                                                    │
│   ☐ review   (12)  │  ┌─────────────────────┐  ┌─────────────────────┐                  │
│   ☐ bin       (5)  │  │         ...         │  │         ...         │                  │
│                    │  └─────────────────────┘  └─────────────────────┘                  │
│ ▼ Perspective      │                                                                    │
│   ☐ pan-day  (18)  │                                                                    │
│   ☐ pan-night (8)  │                                                                    │
│                    │                                                                    │
│ ▼ Color            │                                                                    │
│   ☑ white    (42)  │                                                                    │
│   ☐ black    (38)  │                                                                    │
│   ☐ silver   (25)  │                                                                    │
│   [Show more...]   │                                                                    │
│                    │                                                                    │
│ ▼ Brand            │                                                                    │
│   ☐ toyota   (30)  │                                                                    │
│   ☐ honda    (28)  │                                                                    │
│   [Show more...]   │                                                                    │
├────────────────────┴────────────────────────────────────────────────────────────────────┤
│ Page 1 of 5  |  Filtered: 42 / 500  |  Selected: 2  |  ◀ Prev  Next ▶                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large datasets slow performance | High | Pagination, lazy loading, thumbnails |
| Accidental deletions | High | Confirmation setting, backup before delete |
| JSON corruption on edit | Medium | Write to temp file, then rename |
| Browser memory issues with many images | Medium | Limit loaded images, cleanup unused |

---

## Success Metrics

- Review 500+ images per session without performance degradation
- Complete batch operations (delete/flag) in under 1 second
- Zero data loss from accidental operations
- User satisfaction: reduce review time by 50% vs single-image tools

---

## Out of Scope (v1.0)

- Image editing (crop, rotate, adjust)
- Multi-user collaboration
- Version history/undo for JSON edits
- Export to other annotation formats
- Integration with ML training pipelines
