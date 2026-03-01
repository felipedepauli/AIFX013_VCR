# PRD: Image Review & Annotation Tool

## 1. Product Overview

### Vision
A web-based tool for reviewing, annotating, and managing vehicle detection datasets with support for grid visualization, label editing, quality flagging, bounding box editing, batch operations, and dataset-level statistics powered by MongoDB.

### Problem Statement
Current annotation tools lack efficient batch review capabilities. Reviewers need to quickly scan multiple images, verify labels, flag quality issues, and reorganize datasets without switching between individual images.

### Target Users
- Data annotation reviewers
- ML engineers validating datasets
- Quality assurance teams

---

## 2. Architecture

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask |
| Frontend | Vanilla HTML/CSS/JavaScript |
| Image Processing | PIL/Pillow |
| Data Storage | JSON files + MongoDB (statistics) |
| Statistics DB | MongoDB (local instance) |

### Application Modes

The tool supports two operating modes:

| Mode | Description | Data Storage |
|------|-------------|--------------|
| **Project Mode** | Create named projects with configured directory and settings | `{project_name}.json` in `projects/` folder |
| **Directory Browse Mode** | Navigate and activate any directory as a dataset | `.dataset.json` at dataset root |

### Server-Side Dataset Registry

A central registry file (`datasets_registry.json`) stored alongside `app.py` tracks all datasets ever activated across the system. This registry:

- Maps unique dataset names to their directory paths
- Enables "Recent Datasets" quick-access in the UI
- Is structured for easy future migration to MongoDB

#### Registry Schema

```json
{
  "version": "1.0",
  "datasets": [
    {
      "name": "day_v0_panoramic",
      "path": "/home/pauli/temp/AIFX013_VCR/images/xywh/day_v0",
      "created_at": "2026-02-19T10:00:00",
      "last_accessed": "2026-02-19T15:30:00",
      "cycle": "Overview",
      "image_count": 1234
    }
  ]
}
```

**Constraints:**
- Dataset names must be **globally unique** across the registry
- Names are independent of directory names (user-editable)
- The name in the registry and in `.dataset.json` must stay in sync

---

## 3. Functional Requirements

### FR-01: Grid View Display

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-01.1 | Display images in configurable grid: 2×2 (4), 3×3 (9), 5×5 (25), or 6×6 (36) | P0 |
| FR-01.2 | Grid selector buttons in toolbar | P0 |
| FR-01.3 | Images fill grid left-to-right, top-to-bottom | P0 |
| FR-01.4 | When images are removed, remaining images shift to fill gaps | P0 |
| FR-01.5 | Thumbnail generation with caching (sizes: 400/300/200/150 per grid) | P1 |
| FR-01.6 | Pagination with Previous/Next page buttons in footer | P0 |
| FR-01.7 | Custom NxM grid size via modal (columns × rows, max 10×10) | P2 |
| FR-01.8 | Responsive grid: media queries adjust columns for smaller viewports | P1 |

### FR-02: Label Overlay on Images

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-02.1 | Draw labels at center of each detected object (bounding box) | P0 |
| FR-02.2 | Each label on its own line, vertically stacked | P0 |
| FR-02.3 | Label visibility toggle dropdown (select which labels to show) | P0 |
| FR-02.4 | Available labels from JSON: `color`, `brand`, `model`, `label`, `type`, `sub_type`, `lp_coords` | P0 |
| FR-02.5 | If label not in JSON, display "NULL" | P0 |
| FR-02.6 | Label text styling: semi-transparent background, readable font | P1 |
| FR-02.7 | Draw bounding box rectangle around detected objects | P1 |
| FR-02.8 | Toggle bounding box visibility from label dropdown | P1 |
| FR-02.9 | Bounding box colors respond to the current dataset Cycle (see below) | P0 |

#### Cycle-based Bounding Box Coloring
The active Cycle (from dataset metadata) dictates which label property determines the bounding box color:
- **Overview, Bounding Box, Type cycles:** Color determined by `label` value (e.g., car, truck).
- **Color cycle:** Color determined by `color` value (e.g., silver, black).
- **Brand and Model cycle:** Color determined by `model` value (e.g., city, civic).

### FR-03: Per-Image Controls

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-03.1 | Checkbox for selection (top-left corner) | P0 |
| FR-03.2 | "Open Wider" button — opens image in fullscreen modal | P0 |
| FR-03.3 | "Delete" button — marks/removes image | P0 |
| FR-03.4 | "Flag" button — opens quality flag assignment modal | P0 |
| FR-03.5 | Visual indicator when image is selected (highlighted border) | P0 |
| FR-03.6 | Hover state reveals controls over gradient overlay | P1 |

### FR-04: Deletion Behavior

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-04.1 | Setting: "Skip delete confirmation" (default: OFF) | P0 |
| FR-04.2 | When OFF: Show confirmation dialog before each delete | P0 |
| FR-04.3 | When ON: Delete immediately without confirmation | P0 |
| FR-04.4 | Deleted images removed from grid; remaining images re-flow | P0 |
| FR-04.5 | "Delete All Selected" bulk action button | P0 |
| FR-04.6 | After deletion, stay on current page (don't reset to page 1) | P0 |

### FR-05: Project Mode (Startup Modal)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-05.1 | On app launch, show Project Setup modal | P0 |
| FR-05.2 | Field: Select directory with images (file browser modal) | P0 |
| FR-05.3 | Field: Project name (used for JSON filename) | P0 |
| FR-05.4 | Field: Default quality flags (multi-select) | P0 |
| FR-05.5 | Field: Default visible labels | P0 |
| FR-05.6 | Create project JSON: `{project_name}.json` | P0 |
| FR-05.7 | If project JSON exists, load and skip defaults setup | P0 |
| FR-05.8 | "Open Recent" dropdown for previously opened projects | P1 |

### FR-06: Quality Flags System

Quality flags are **per-vehicle** flags (applied to individual detected objects within an image, not to the image as a whole).

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-06.1 | "Flag" button on each image — opens quality flag modal | P0 |
| FR-06.2 | Modal shows available quality flags for assignment | P0 |
| FR-06.3 | Default Quality Flags: `bin`, `review`, `ok`, `move` | P0 |
| FR-06.4 | Multiple flags can be applied per vehicle | P0 |
| FR-06.5 | Applied flags displayed at bottom of image card (color-coded badges) | P0 |
| FR-06.6 | "Flag Selected" bulk action to apply flags to all selected images | P1 |
| FR-06.7 | Quick quality flag: number keys 1-9 on hover/selected | P1 |
| FR-06.8 | Cycle quality flag with `Q` key | P1 |
| FR-06.9 | Flags stored in project JSON or `.dataset.json` | P0 |
| FR-06.10 | "Apply to All" — set a quality flag on all images at once | P1 |

> [!IMPORTANT]
> **Perspective flags are removed.** They have been replaced by the Trainable Models configuration (FR-16), which is a dataset-level setting rather than a per-image/per-vehicle flag.

### FR-07: Settings Panel

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-07.1 | Gear icon (⚙️) in toolbar | P0 |
| FR-07.2 | Click opens settings modal | P0 |
| FR-07.3 | Setting: Skip delete confirmation (checkbox) | P0 |
| FR-07.4 | Setting: Manage quality flags (add/remove custom flags) | P0 |
| FR-07.5 | Setting: Select visible labels | P0 |
| FR-07.6 | Setting: Default quality flag for new images | P1 |
| FR-07.7 | Settings persisted in project JSON or `.dataset.json` | P0 |
| FR-07.8 | Current project/dataset name displayed in header | P1 |

### FR-08: Inline Label Editing

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-08.1 | Click on label text makes it editable (inline input) | P0 |
| FR-08.2 | Save on Enter or blur (click outside) | P0 |
| FR-08.3 | Cancel on Escape | P0 |
| FR-08.4 | Write changes directly to label JSON file | P0 |
| FR-08.5 | Only update changed field; preserve other data | P0 |
| FR-08.6 | No confirmation required for edits | P0 |
| FR-08.7 | Visual feedback on successful save (notification) | P1 |

### FR-09: Image Modal (Open Wider)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-09.1 | Full-resolution image display in modal overlay | P0 |
| FR-09.2 | Navigate between images with left/right arrows | P0 |
| FR-09.3 | Label overlays visible in modal view | P0 |
| FR-09.4 | Bounding box overlays visible in modal view | P0 |
| FR-09.5 | Close with Escape or clicking outside | P0 |

### FR-10: Bounding Box Editor

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-10.1 | Drag to resize existing bounding boxes in modal view | P0 |
| FR-10.2 | Draw new bounding boxes | P1 |
| FR-10.3 | Delete selected bounding box (Delete key) | P0 |
| FR-10.4 | Save bbox changes to label JSON file | P0 |
| FR-10.5 | Cancel edit mode with Escape | P0 |
| FR-10.6 | Visual selection highlight on active bbox | P1 |

### FR-11: Vehicle Direction Flag

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-11.1 | Binary "direction" flag per vehicle object: `front` or `back` | P0 |
| FR-11.2 | Default value is `front` when field is missing | P0 |
| FR-11.3 | Display direction indicator on each vehicle bounding box | P0 |
| FR-11.4 | Click on indicator toggles between `front` ↔ `back` | P0 |
| FR-11.5 | Direction stored in label JSON file (per-vehicle, not per-image) | P0 |
| FR-11.6 | Visual distinction: arrow indicating direction (▼ front, ▲ back) | P1 |
| FR-11.7 | Filter by direction in filter panel | P1 |
| FR-11.8 | Bulk set direction for selected/all images (toolbar buttons) | P2 |

### FR-12: Filter Panel

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-12.1 | Collapsible left sidebar panel with tabs (Filters / Directories) | P0 |
| FR-12.2 | Filter by label values: `color`, `brand`, `model`, `label`, `type`, `sub_type` | P0 |
| FR-12.3 | Filter by quality flags | P0 |
| FR-12.4 | Filter by direction (`front`/`back`) | P1 |
| FR-12.5 | Multiple filters combined with AND logic | P0 |
| FR-12.6 | Active filters shown as removable chips in a bar below the header | P0 |
| FR-12.7 | "Clear All Filters" button | P0 |
| FR-12.8 | Real-time filter count (show number of matching images) | P1 |
| FR-12.9 | Search/filter within filter options (search input) | P2 |
| FR-12.10 | Toggle sidebar with keyboard shortcut `\` | P1 |
| FR-12.11 | Filter sections are collapsible (click header to expand/collapse) | P1 |
| FR-12.12 | Each filter option shows count of matching images | P1 |

### FR-13: Directory Browsing (Browse Mode)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-13.1 | "Directories" tab in left sidebar showing tree view | P0 |
| FR-13.2 | Configurable base path restricts navigation scope | P0 |
| FR-13.3 | Single-click to select directory; double-click to expand/collapse | P0 |
| FR-13.4 | Expand/collapse folder nodes with arrow icon | P0 |
| FR-13.5 | Visual folder icons (📁) with indentation for hierarchy | P1 |
| FR-13.6 | Lazy loading of subdirectories (load children on expand) | P1 |
| FR-13.7 | Show image count per directory in tree node | P1 |
| FR-13.8 | "Refresh" button to reload directory tree | P1 |

### FR-14: Dataset Activation & Registry

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-14.1 | "Activate Dataset" button in metadata panel marks directory as active | P0 |
| FR-14.2 | Display mode toggle: Direct (only this folder) or Recursive (include subdirs) | P0 |
| FR-14.3 | Default display mode is "Direct" | P0 |
| FR-14.4 | Grid shows images only after dataset is activated | P0 |
| FR-14.5 | Active directory path shown in header | P0 |
| FR-14.6 | "Deactivate" clears the active dataset | P0 |
| FR-14.7 | `.dataset.json` created at dataset root on activation | P0 |
| FR-14.8 | On activation, register dataset in `datasets_registry.json` | P0 |
| FR-14.9 | Dataset name must be unique — reject duplicates on creation | P0 |
| FR-14.10 | Dataset name in `.dataset.json` and registry kept in sync | P0 |
| FR-14.11 | "Recent Datasets" dropdown in UI for quick switching | P1 |
| FR-14.12 | Remove dataset from registry (unregister) | P2 |

### FR-15: Dataset Metadata Panel

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-15.1 | Collapsible right panel for dataset information | P0 |
| FR-15.2 | **Summary:** Total images and samples by class (`label` field) | P0 |
| FR-15.3 | **Button:** "View Detailed Statistics" opens full statistics modal (FR-18) | P0 |
| FR-15.4 | **Editable:** Dataset name (unique, synced to registry) | P0 |
| FR-15.5 | **Editable:** Description (textarea) | P0 |
| FR-15.6 | **Editable:** Camera View (multi-select: frontal, traseira, panorâmica, closeup, super-panorâmica) | P0 |
| FR-15.7 | **Editable:** Quality (select: poor, fair, good, excellent) | P0 |
| FR-15.8 | **Editable:** Verdict (select: keep ✅, revise 🔄, remove ❌) | P0 |
| FR-15.9 | **Editable:** Cycle (select: Overview, Bounding Box, Type, Color, Brand and Model) | P0 |
| FR-15.10 | **Editable:** Notes (textarea) | P1 |
| FR-15.11 | Auto-save metadata changes to `.dataset.json` and registry | P0 |
| FR-15.12 | Collapsible sections within the panel (Statistics, Metadata, Actions) | P1 |

### FR-16: Trainable Models Configuration

A dataset-level section that defines which ML models can be trained using this dataset. This replaces the old per-image perspective flags.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-16.1 | Section in metadata panel with checkboxes for each model | P0 |
| FR-16.2 | Default models: `Panoramic Day`, `Panoramic Night`, `Superpanoramic Day`, `Superpanoramic Night`, `Close-up Day`, `Close-up Night`, `BMC`, `Plate Localization`, `License Plate Text`, `Container` | P0 |
| FR-16.3 | Multiple models can be selected simultaneously | P0 |
| FR-16.4 | Each selected model has a preprocessing dropdown (`none`, `cropped`) | P0 |
| FR-16.5 | Default preprocessing is `none` | P0 |
| FR-16.6 | `cropped` preprocessing means: crop vehicles using bounding boxes before training | P0 |
| FR-16.7 | User can add new model names via input field | P1 |
| FR-16.8 | User can add new preprocessing options via input field | P1 |
| FR-16.9 | Configuration stored in `.dataset.json` metadata | P0 |
| FR-16.10 | Auto-save on change | P0 |

#### Trainable Models Schema

```json
{
  "trainable_models": [
    {
      "name": "Panoramic Day",
      "enabled": true,
      "preprocessing": "cropped"
    },
    {
      "name": "Close-up Night",
      "enabled": false,
      "preprocessing": "none"
    }
  ],
  "available_preprocessing": ["none", "cropped"]
}
```

### FR-17: Dataset Attributes

Dataset-level attributes describing environmental/quality conditions of the entire dataset. These are **not** per-image flags.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-17.1 | Section in metadata panel with checkboxes for dataset attributes | P0 |
| FR-17.2 | Default attributes: `Excess Light`, `Grainy Image`, `Low Light`, `Raining`, `Normal` | P0 |
| FR-17.3 | Multiple attributes can be selected simultaneously | P0 |
| FR-17.4 | User can add custom attributes via input field | P1 |
| FR-17.5 | User can remove custom attributes | P1 |
| FR-17.6 | Attributes stored in `.dataset.json` metadata | P0 |
| FR-17.7 | Auto-save on change | P0 |

#### Attributes Schema

```json
{
  "attributes": {
    "selected": ["Normal"],
    "available": ["Excess Light", "Grainy Image", "Low Light", "Raining", "Normal"]
  }
}
```

### FR-18: Dataset Statistics (MongoDB)

Comprehensive dataset statistics computed from all label JSON files and stored in a local MongoDB instance.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-18.1 | Local MongoDB instance for storing computed statistics | P0 |
| FR-18.2 | "Compute Statistics" button to trigger on-demand analysis | P0 |
| FR-18.3 | Scan all label JSON files in the dataset (respecting display mode) | P0 |
| FR-18.4 | **Stat:** Total number of objects (vehicles) across all images | P0 |
| FR-18.5 | **Stat:** Total objects by class (`label` field: car, truck, etc.) | P0 |
| FR-18.6 | **Stat:** Mean and variance of bounding box centroids (normalized 0–1: `x_center/img_w`, `y_center/img_h`) | P0 |
| FR-18.7 | **Stat:** Mean and variance of bounding box area (absolute pixels: `w × h`) by class | P0 |
| FR-18.8 | **Stat:** Mean and variance of number of vehicles per image | P0 |
| FR-18.9 | Statistics cached in MongoDB, recomputed on user request | P0 |
| FR-18.10 | Progress indicator during computation | P1 |

#### Statistics MongoDB Schema

```json
{
  "_id": "ObjectId",
  "dataset_path": "/path/to/dataset",
  "dataset_name": "day_v0_panoramic",
  "computed_at": "2026-02-19T12:00:00",
  "total_images": 1234,
  "total_objects": 5678,
  "objects_by_class": {
    "car": 4500,
    "truck": 800,
    "motorcycle": 378
  },
  "centroids": {
    "mean": { "x": 0.52, "y": 0.61 },
    "variance": { "x": 0.04, "y": 0.03 }
  },
  "area_by_class": {
    "car": { "mean": 45000, "variance": 12000 },
    "truck": { "mean": 72000, "variance": 18000 }
  },
  "vehicles_per_image": {
    "mean": 4.6,
    "variance": 2.1
  }
}
```

### FR-19: Detailed Statistics Modal

A rich modal opened from the metadata panel showing comprehensive dataset statistics with visual charts.

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-19.1 | "View Detailed Statistics" button in metadata panel opens modal | P0 |
| FR-19.2 | Summary cards: total images, total objects, objects/image mean | P0 |
| FR-19.3 | **Pie chart:** Object distribution by class (`label`) | P0 |
| FR-19.4 | **Bar chart:** Object count by class | P0 |
| FR-19.5 | **Table:** Per-class stats (count, area mean/variance, centroid mean/variance) | P0 |
| FR-19.6 | **Stats by any label field:** Tabs or dropdown to switch between `label`, `color`, `brand`, `model`, `type`, `sub_type` | P1 |
| FR-19.7 | **Bar chart:** Distribution of vehicles per image | P1 |
| FR-19.8 | "Recompute" button within modal to refresh statistics | P1 |
| FR-19.9 | Close with Escape or close button | P0 |

---

## 4. Data Models

### 4.1 Project JSON Schema (Project Mode)

Stored as `projects/{project_name}.json`:

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
    "visible_labels": ["color", "brand", "model", "type"],
    "default_quality_flag": "review"
  },
  "images": [
    {
      "seq_id": 1,
      "path": "images/xywh/v4/test/000000_ASH4662_1.jpg",
      "json_path": "images/xywh/v4/test/000000_ASH4662_1.json",
      "quality_flags": ["ok"],
      "deleted": false
    }
  ]
}
```

### 4.2 Dataset JSON Schema (Browse Mode)

Stored as `.dataset.json` at the dataset root directory:

```json
{
  "version": "3.0",
  "type": "dataset",
  "name": "day_v0_panoramic",
  "root_path": "/home/pauli/temp/AIFX013_VCR/images/xywh/day_v0",
  "created": "2026-02-19T10:00:00",
  "updated": "2026-02-19T15:30:00",
  "metadata": {
    "description": "Vehicle detection dataset, daytime panoramic views",
    "camera_view": ["frontal", "panorâmica"],
    "quality": "good",
    "verdict": "keep",
    "cycle": "Overview",
    "notes": "First review pass."
  },
  "attributes": {
    "selected": ["Normal"],
    "available": ["Excess Light", "Grainy Image", "Low Light", "Raining", "Normal"]
  },
  "trainable_models": [
    {
      "name": "Panoramic Day",
      "enabled": true,
      "preprocessing": "cropped"
    },
    {
      "name": "Close-up Day",
      "enabled": false,
      "preprocessing": "none"
    }
  ],
  "available_preprocessing": ["none", "cropped"],
  "settings": {
    "display_mode": "direct",
    "skip_delete_confirmation": false,
    "visible_labels": ["color", "brand", "model", "type"],
    "quality_flags": ["bin", "review", "ok", "move"]
  },
  "image_flags": {
    "train/000001_ABC123.jpg": {
      "quality_flags": ["ok"]
    }
  }
}
```

### 4.3 Server-Side Registry Schema

Stored as `datasets_registry.json` alongside `app.py`:

```json
{
  "version": "1.0",
  "datasets": [
    {
      "name": "day_v0_panoramic",
      "path": "/home/pauli/temp/AIFX013_VCR/images/xywh/day_v0",
      "created_at": "2026-02-19T10:00:00",
      "last_accessed": "2026-02-19T15:30:00",
      "cycle": "Overview",
      "image_count": 1234
    }
  ]
}
```

### 4.4 Label JSON Schema (per image)

Each image file (e.g. `image.jpg`) may have a corresponding `image.json`:

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
    "lp_coords": "",
    "direction": "front"
  }
]
```

#### Label Fields

| Field | Type | Description |
|-------|------|-------------|
| `rect` | `[x, y, w, h]` | Bounding box coordinates |
| `color` | string | Vehicle color |
| `brand` | string | Vehicle brand |
| `model` | string | Vehicle model |
| `label` | string | Object class (e.g. "car", "truck") |
| `type` | string | Vehicle type |
| `sub_type` | string | Vehicle sub-type |
| `lp_coords` | string | License plate coordinates |
| `direction` | string | `"front"` or `"back"` (default: `"front"`) |

### 4.5 Dataset Metadata Fields

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `name` | string | — | Display name (unique across registry) |
| `description` | text | — | Brief description of dataset contents |
| `camera_view` | multi-select | frontal, traseira, panorâmica, closeup, super-panorâmica | Camera perspective(s) |
| `quality` | select | poor, fair, good, excellent | Overall dataset quality |
| `verdict` | select | keep, revise, remove | Action decision |
| `cycle` | select | Overview, Bounding Box, Type, Color, Brand and Model | Current review phase |
| `notes` | text | — | Additional observations |

#### Cycle Definitions

| Cycle | Purpose |
|-------|---------|
| **Overview** | General review — remove bad images, assess dataset quality |
| **Bounding Box** | Verify and correct bounding box positions and sizes |
| **Type** | Review and correct vehicle type/sub-type labels |
| **Color** | Review and correct vehicle color labels |
| **Brand and Model** | Review and correct brand and model labels |

---

## 5. API Endpoints

### Project Mode

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create new project |
| GET | `/api/projects/<name>` | Load project |
| GET | `/api/images` | Get paginated images |
| POST | `/api/grid-size` | Update grid size |
| GET | `/api/labels/<seq_id>` | Get labels for image |
| POST | `/api/labels/batch` | Get labels for multiple images |
| POST | `/api/visible-labels` | Update visible labels |
| GET | `/api/image/<seq_id>/full` | Get full-res image |
| DELETE | `/api/images/<seq_id>` | Delete single image |
| POST | `/api/images/delete-bulk` | Delete multiple images |
| POST | `/api/images/<seq_id>/flags` | Set quality flags for image |
| POST | `/api/images/flags-bulk` | Set quality flags for multiple images |
| PUT | `/api/labels/<seq_id>/<obj_idx>/<label>` | Update label value |
| POST | `/api/settings` | Update settings |
| GET | `/api/settings` | Get settings |
| POST | `/api/flags/apply-all` | Apply quality flag to all images |
| POST | `/api/direction/<seq_id>/<vehicle_idx>` | Toggle vehicle direction |
| POST | `/api/direction/apply-all` | Apply direction to all |
| GET | `/api/filter/options` | Get filter options with counts |

### Browse Mode

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/browse/tree` | Get directory tree |
| GET | `/api/browse/children` | Get directory children |
| POST | `/api/browse/activate` | Activate directory as dataset (also registers) |
| GET | `/api/browse/metadata` | Get dataset metadata |
| POST | `/api/browse/metadata` | Update dataset metadata |
| POST | `/api/browse/flag` | Update quality flag |
| POST | `/api/browse/delete` | Delete images |
| GET | `/api/browse/filter-options` | Get filter options |
| GET | `/api/browse/labels/<path>` | Get labels for image |
| POST | `/api/browse/labels` | Save labels for image |
| GET | `/api/browse/image/<path>` | Get full-res image |

### Registry

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/registry/datasets` | List all registered datasets (recent datasets) |
| POST | `/api/registry/datasets` | Register a dataset (with unique name validation) |
| PUT | `/api/registry/datasets/<name>` | Update dataset registry entry |
| DELETE | `/api/registry/datasets/<name>` | Unregister a dataset |

### Statistics (MongoDB)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/stats/compute` | Compute statistics for active dataset (triggers scan) |
| GET | `/api/stats/<dataset_name>` | Get cached statistics from MongoDB |

### Shared

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/browse` | Browse filesystem for directory selection |

---

## 6. Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `W` | Previous page |
| `E` | Next page |
| `1`–`4` | Switch grid size (when not hovering image) |
| `1`–`9` | Set quality flag by number (when hovering/selected) |
| `G` | Open custom grid modal |
| `A` | Select all on current page |
| `D` | Deselect all on page |
| `Space` | Open hovered image (Open Wider) |
| `R` | Delete hovered/selected images |
| `F` | Flag selected/hovered images |
| `Q` | Cycle quality flag |
| `\` | Toggle filter/sidebar panel |
| `,` | Open settings |
| `?` | Show keyboard shortcuts help |
| `Escape` | Close modal / Cancel / Deselect all |
| `←` / `→` | Navigate images in modal |
| `Delete` | Delete selected bounding box (in bbox editor) |

---

## 7. Non-Functional Requirements

### NFR-01: Performance
- Load 36 images in under 2 seconds
- Image thumbnails cached for grid view (in-memory LRU cache)
- Full resolution loaded only for "Open Wider" modal
- Pagination to limit DOM elements
- Statistics computed on-demand (not blocking UI)

### NFR-02: Usability
- Keyboard shortcuts for all common actions
- Viewport-locked layout (no page scroll; panels scroll independently)
- Clear visual feedback for all actions (toast notifications)
- Charts in statistics modal for quick visual understanding

### NFR-03: Reliability
- Auto-save all changes (settings, flags, metadata)
- Error handling with user-friendly notifications
- Atomic JSON file writes
- MongoDB connection resilience (graceful fallback if unavailable)

### NFR-04: Technology Constraints
- Python Flask backend
- HTML/CSS/JavaScript frontend (vanilla, no external JS frameworks)
- PIL/Pillow for image processing & thumbnail generation
- File-based JSON storage for metadata + MongoDB for statistics
- Chart library for statistics visualization (Canvas-based, no heavy dependencies)

### NFR-05: Data Migration Readiness
- All JSON structures designed for easy migration to MongoDB
- Registry as flat list of documents (maps to MongoDB collection)
- Dataset metadata as single document (maps to MongoDB document)
- Image flags as key-value pairs (maps to MongoDB sub-documents)

---

## 8. UI Layout

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ 🖼️ Image Review Tool  [path]  |  Labels: [4 shown ▼]  [2×2][3×3][5×5][6×6][⚙]  [?] ⚙️  │
├─────────────────┬────────────────────────────────────────────────┬───────────────────────┤
│ Filters | Dirs  │            Image Grid (scrollable)             │  DATASET INFO ▶       │
│                 │                                                │                       │
│ ▼ Quality Flags │   ┌─────────┐  ┌─────────┐  ┌─────────┐      │ 📊 Statistics          │
│   ☐ ok     (25) │   │  img1   │  │  img2   │  │  img3   │      │ Total: 1,234 images    │
│   ☐ review (12) │   │ labels  │  │ labels  │  │ labels  │      │ car: 4500 | truck: 800 │
│                 │   └─────────┘  └─────────┘  └─────────┘      │ [📈 View Details]      │
│ ▼ Color         │                                                │                       │
│   ☐ white  (42) │   ┌─────────┐  ┌─────────┐  ┌─────────┐      │ 📝 Metadata            │
│   ☐ black  (38) │   │  img4   │  │  img5   │  │  img6   │      │ Name: [day_v0_pan   ]  │
│                 │   └─────────┘  └─────────┘  └─────────┘      │ Cycle: [Overview ▼]    │
│ ▼ Direction     │                                                │ Quality: [good ▼]      │
│   ☐ front  (80) │                                                │                       │
│   ☐ back   (20) │                                                │ 🤖 Trainable Models    │
│                 │                                                │ ☑ Panoramic Day [crop▼]│
│                 │                                                │ ☐ BMC          [none▼]│
│                 │                                                │ [+ Add Model]          │
│                 │                                                │                       │
│                 │                                                │ 🏷️ Attributes           │
│                 │                                                │ ☑ Normal               │
│                 │                                                │ ☐ Raining              │
│                 │                                                │ [+ Add Attribute]      │
│                 │                                                │                       │
│                 │                                                │ [🔄 Activate Dataset]  │
├─────────────────┴────────────────────────────────────────────────┴───────────────────────┤
│ ← Prev  Page 1 of 5  Next →  |  Total: 500  |  Selected: 2                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large datasets slow performance | High | Pagination, thumbnails, lazy loading |
| Accidental deletions | High | Confirmation setting, skip confirmation off by default |
| JSON corruption on edit | Medium | Write to temp file, then rename |
| Browser memory issues with many images | Medium | Limit loaded images, pagination, cleanup |
| Navigating outside base path | Medium | Strict path validation, configurable base |
| MongoDB unavailable | Medium | Graceful fallback, clear error message |
| Duplicate dataset names | Low | Unique constraint enforced at registration |
| Statistics computation timeout | Medium | Progress indicator, async computation |

---

## 10. Out of Scope

- Image editing (crop, rotate, adjust)
- Multi-user collaboration / authentication
- Version history / undo for edits
- Export to other annotation formats (COCO, YOLO, etc.)
- Integration with ML training pipelines
- Moving individual images between directories
- Drag-and-drop images between folders
- Dataset comparison side-by-side
- Cloud/remote file system support
- Directory operations (create/rename/delete folders)
- Batch move images to different directories
- Per-image perspective flags (replaced by dataset-level Trainable Models)
