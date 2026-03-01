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
| v1.1 (Filters) | ✅ Complete | Feb 2026 |
| v1.2 (Vehicle Direction) | ✅ Complete | Feb 2026 |
| v2.0 (Dataset Management) | 🔄 In Progress (93%) | Feb 2026 |
| v2.1 (Datasets Dashboard) | 📋 Planned | Feb 2026 |

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
| FR-01.7 | **BONUS:** Custom NxM grid size with modal | P2 | ✅ |

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
| FR-02.8 | **INVARIANT:** Bounding boxes must always be positioned exactly according to the `rect` coordinates in the JSON, maintaining precise proportional accuracy relative to the image dimensions. This must hold regardless of container resizing, edit panel toggling, window resize, or mode changes (view ↔ edit). The overlay position must be recalculated whenever the image container dimensions change. | P0 | ✅ |

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
| FR-06.8 | Filter view by flag (show only images with specific flag) | P2 | ✅ |
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
| FR-09.6 | **INVARIANT:** The `rect` field in the JSON is the single source of truth for bounding box position and size. Displayed bounding boxes must always reflect the exact `rect` values proportionally scaled to the rendered image size, with no drift or displacement from layout changes. | P0 | ✅ |

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

### FR-11: Filter Panel (v1.1) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-11.1 | Collapsible left sidebar filter panel | P0 | ✅ |
| FR-11.2 | Filter by label values (color, brand, model, type, etc.) | P0 | ✅ |
| FR-11.3 | Filter by quality flags | P0 | ✅ |
| FR-11.4 | Filter by perspective flags | P0 | ✅ |
| FR-11.5 | Multiple filters can be combined (AND logic) | P0 | ✅ |
| FR-11.6 | Active filters shown as removable chips | P0 | ✅ |
| FR-11.7 | "Clear All Filters" button | P0 | ✅ |
| FR-11.8 | Real-time filter count (show matching images) | P1 | ✅ |
| FR-11.9 | Filter state persisted in session | P1 | ✅ |
| FR-11.10 | Search/filter within filter options | P2 | ✅ |
| FR-11.11 | Toggle sidebar visibility with keyboard shortcut | P1 | ✅ |
| FR-11.12 | Toggle "Hide Non-Matching Vehicles" (shortcut `h`) to dim vehicles that don't match active filters (80% black overlay on bounding box), keeping only matching vehicles fully visible. Works in both Grid and Preview modes. | P0 | ❌ |

### FR-12: Vehicle Direction Flag (v1.2) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-12.1 | Binary "direction" flag per vehicle object: `front` or `back` | P0 | ✅ |
| FR-12.2 | Default value is `front` when field is missing | P0 | ✅ |
| FR-12.3 | Display direction indicator on each vehicle bounding box | P0 | ✅ |
| FR-12.4 | Click on indicator toggles between `front` ↔ `back` | P0 | ✅ |
| FR-12.5 | Direction stored in label JSON file (per-vehicle, not per-image) | P0 | ✅ |
| FR-12.6 | Visual distinction: arrow pointing toward camera (front) or away (back) | P1 | ✅ |
| FR-12.7 | Filter by direction in filter panel | P1 | ✅ |
| FR-12.8 | Bulk set direction for selected images (all vehicles) | P2 | ✅ |

### FR-13: File System Browser (v2.0) �

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-13.1 | Collapsible left panel showing directory tree (folders only, no files) | P0 | ✅ |
| FR-13.2 | Configurable base path to restrict navigation scope | P0 | ✅ |
| FR-13.3 | Single-click to select directory, double-click to navigate into | P0 | ✅ |
| FR-13.4 | Expand/collapse folder nodes in tree view | P0 | ✅ |
| FR-13.5 | Visual folder icons with indentation for hierarchy | P1 | ✅ |
| FR-13.6 | Show current path breadcrumb in footer | P1 | ❌ |
| FR-13.7 | "Recent Datasets" dropdown for quick switching | P1 | ❌ |

### FR-14: Directory Operations (v2.0) ❌

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-14.1 | Create new directory within current location | P0 | ❌ |
| FR-14.2 | Delete directory (with confirmation, moves to trash or permanent) | P0 | ❌ |
| FR-14.3 | Move directory to different location (drag-drop or modal) | P1 | ❌ |
| FR-14.4 | Rename directory | P1 | ❌ |
| FR-14.5 | Path validation to prevent invalid names | P0 | ❌ |
| FR-14.6 | Confirmation dialog for destructive operations | P0 | ❌ |

### FR-15: Dataset Activation System (v2.0) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-15.1 | "Activate Dataset" button marks directory as active dataset root | P0 | ✅ |
| FR-15.2 | Display mode toggle: Direct (only this folder) or Recursive (include subdirs) | P0 | ✅ |
| FR-15.3 | Default display mode is "Direct" | P0 | ✅ |
| FR-15.4 | Grid shows images only after dataset is activated | P0 | ✅ |
| FR-15.5 | Double-click subdirectory navigates into it (working dir changes, dataset stays) | P0 | ✅ |
| FR-15.6 | Subdirectories inherit parent dataset settings until deactivated | P0 | ✅ |
| FR-15.7 | "Deactivate Dataset" to end current session | P0 | ✅ |
| FR-15.8 | Settings stored in `.dataset.json` at dataset root | P0 | ✅ |
| FR-15.9 | Each dataset has its own metadata, settings, and image flags | P0 | ✅ |

### FR-16: Dataset Metadata Panel (v2.0) ✅

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-16.1 | Collapsible right panel for dataset information | P0 | ✅ |
| FR-16.2 | **Statistics (computed):** Total images (recursive), images per subfolder | P0 | ✅ |
| FR-16.3 | **Statistics:** Samples per class (configurable: label, color, model) | P0 | ✅ |
| FR-16.4 | **Editable:** Name (auto-filled from directory name) | P0 | ✅ |
| FR-16.5 | **Editable:** Description (textarea for dataset content summary) | P0 | ✅ |
| FR-16.6 | **Editable:** Camera View (multi-select: frontal, traseira, panorâmica, closeup, super-panorâmica) | P0 | ✅ |
| FR-16.7 | **Editable:** Quality (select: poor, fair, good, excellent) | P0 | ✅ |
| FR-16.8 | **Editable:** Verdict (select: keep ✅, revise 🔄, remove ❌) | P0 | ✅ |
| FR-16.9 | **Editable:** Cycle (select: first, second, third, fourth, fifth) | P0 | ✅ |
| FR-16.10 | **Editable:** Notes (textarea for additional observations) | P1 | ✅ |
| FR-16.11 | Auto-save metadata changes to `.dataset.json` | P0 | ✅ |
| FR-16.12 | Activate button placed in this panel | P0 | ✅ |

### FR-17: Datasets Dashboard (v2.1) ❌

#### Overview
A centralized datasets registry backed by MongoDB, replacing the "Recents" system. Users register datasets via an "Add" action; registered datasets appear in a left-panel section and can be opened in a full-detail dashboard modal. The left panel tab is renamed from **Directories** to **Datasets**.

#### FR-17.1: Left Panel — Datasets Tab

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-17.1.1 | Rename the left-panel "Directories" tab to **Datasets** | P0 | ❌ |
| FR-17.1.2 | Top section: list of registered datasets (from MongoDB) with name and path | P0 | ❌ |
| FR-17.1.3 | Click on a registered dataset → opens/activates it (same behavior as current browse-mode activation) | P0 | ❌ |
| FR-17.1.4 | **[+ Add Current]** button — registers the currently activated dataset to MongoDB | P0 | ❌ |
| FR-17.1.5 | **[📊 Dashboard]** button — opens the Datasets Dashboard modal | P0 | ❌ |
| FR-17.1.6 | Below the registered datasets: directory tree browser (existing functionality) for navigating and activating new datasets | P0 | ❌ |
| FR-17.1.7 | Remove the **"Recent"** button from the top-right toolbar | P0 | ❌ |
| FR-17.1.8 | Each registered dataset in the list shows a small status indicator (cycle badge) | P1 | ❌ |

#### FR-17.2: Datasets Dashboard Modal

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-17.2.1 | Full-screen modal listing all registered datasets as cards | P0 | ❌ |
| FR-17.2.2 | Each card displays: **name**, **path**, **cycle**, **quality**, **model compatibility**, **4 thumbnails** | P0 | ❌ |
| FR-17.2.3 | Each card shows **statistics summary**: total images count | P0 | ❌ |
| FR-17.2.4 | Thumbnails: pick the 1st, 25%-th, 75%-th, and last image from the dataset | P0 | ❌ |
| FR-17.2.5 | Thumbnail images are generated server-side (resized to ~150px) and cached | P1 | ❌ |
| FR-17.2.6 | Click **"Open"** on a card → closes modal and activates that dataset in the main view | P0 | ❌ |
| FR-17.2.7 | Click on a card → expands to **detail view** (inline or sub-modal) | P0 | ❌ |
| FR-17.2.8 | Cards laid out in a responsive grid (2-3 columns depending on viewport) | P1 | ❌ |

#### FR-17.3: Dataset Detail View (inside Dashboard Modal)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-17.3.1 | Show full metadata: name, path, description, camera view, quality, verdict, cycle, notes | P0 | ❌ |
| FR-17.3.2 | Show **statistics**: total images, per-class counts (car, motorcycle, truck, bus) | P0 | ❌ |
| FR-17.3.3 | Show **spatial statistics**: mean and variance of bounding box position (x, y) and area (w×h) | P0 | ❌ |
| FR-17.3.4 | Show **model compatibility**: which model(s) can be trained with this dataset (select field) | P0 | ❌ |
| FR-17.3.5 | Editable fields: name, description, camera view, quality, verdict, cycle, notes, model compatibility | P0 | ❌ |
| FR-17.3.6 | **[🗑️ Remove]** button — unregisters dataset from MongoDB (does NOT delete files) | P0 | ❌ |
| FR-17.3.7 | **[🔄 Refresh Stats]** button — re-scans the dataset directory and updates statistics | P1 | ❌ |
| FR-17.3.8 | **[Open Dataset]** button — closes modal, activates dataset | P0 | ❌ |
| FR-17.3.9 | All edits auto-saved to MongoDB | P0 | ❌ |
| FR-17.3.10 | Show 4 thumbnails in larger size (preview strip) | P1 | ❌ |
| FR-17.3.11 | If dataset path no longer exists on disk, show warning badge "Path not found" | P1 | ❌ |

#### FR-17.4: Dataset Registration Flow

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-17.4.1 | User navigates to a directory and activates a dataset (existing flow) | P0 | ❌ |
| FR-17.4.2 | User clicks **[+ Add Current]** in the Datasets panel or **[+ Add to Dashboard]** in the Dataset Info panel | P0 | ❌ |
| FR-17.4.3 | Server reads `.dataset.json` metadata and inserts record into MongoDB | P0 | ❌ |
| FR-17.4.4 | Server computes initial statistics (total images, per-class, spatial stats) | P0 | ❌ |
| FR-17.4.5 | Server generates 4 thumbnail images from the dataset | P0 | ❌ |
| FR-17.4.6 | Dataset appears immediately in the left panel registered list and in the dashboard modal | P0 | ❌ |
| FR-17.4.7 | Prevent duplicate registration (same `root_path`) — show info toast if already registered | P0 | ❌ |

### FR-18: MongoDB Backend (v2.1) ❌

#### Overview
Server-side MongoDB integration for persistent dataset registry. The database is accessed exclusively by the Flask server — no direct client access.

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-18.1 | MongoDB connection managed by Flask server (pymongo) | P0 | ❌ |
| FR-18.2 | Database name: `image_review_tool` | P0 | ❌ |
| FR-18.3 | Collection: `datasets` — stores all registered dataset records | P0 | ❌ |
| FR-18.4 | Connection string configurable via environment variable `MONGODB_URI` (default: `mongodb://localhost:27017`) | P0 | ❌ |
| FR-18.5 | Graceful fallback if MongoDB is unavailable — show warning, disable dashboard features | P1 | ❌ |
| FR-18.6 | API: `GET /api/datasets` — list all registered datasets | P0 | ❌ |
| FR-18.7 | API: `POST /api/datasets` — register a new dataset (compute stats + thumbnails) | P0 | ❌ |
| FR-18.8 | API: `GET /api/datasets/<id>` — get full dataset detail | P0 | ❌ |
| FR-18.9 | API: `PUT /api/datasets/<id>` — update dataset metadata/fields | P0 | ❌ |
| FR-18.10 | API: `DELETE /api/datasets/<id>` — unregister dataset (files untouched) | P0 | ❌ |
| FR-18.11 | API: `POST /api/datasets/<id>/refresh` — re-scan and update statistics | P0 | ❌ |
| FR-18.12 | API: `GET /api/datasets/<id>/thumbnails/<index>` — serve cached thumbnail (0-3) | P0 | ❌ |
| FR-18.13 | Unique index on `root_path` to prevent duplicates | P0 | ❌ |

### FR-19: Dataset Info → MongoDB Sync (v2.2) ❌

#### Overview
When a dataset is registered in MongoDB, all metadata changes from the Dataset Info panel (right sidebar) must sync to the MongoDB document on save. This eliminates the dual-source-of-truth problem where `.dataset.json` and MongoDB diverge after registration. Additionally, "Stats Config" is expanded into "Dataset Config" — a section that stores all dataset-level operational settings and applies them automatically when the dataset is opened.

#### FR-19.1: Metadata Sync on Save

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19.1.1 | "Save Changes" in Dataset Info panel syncs metadata to MongoDB if dataset is registered | P0 | ❌ |
| FR-19.1.2 | Synced fields: name, description, camera_view, quality, verdict, cycle, notes | P0 | ❌ |
| FR-19.1.3 | Trainable Models changes (toggle/add/remove) sync to MongoDB | P0 | ❌ |
| FR-19.1.4 | Attributes changes (toggle/add/remove) sync to MongoDB | P0 | ❌ |
| FR-19.1.5 | If MongoDB write fails, show warning but don't block (`.dataset.json` is still saved) | P1 | ❌ |
| FR-19.1.6 | Non-registered datasets: save only to `.dataset.json` (backwards compatible) | P0 | ❌ |
| FR-19.1.7 | Sync indicator in panel header: "✓ Synced" (green) or "Local only" (grey) | P1 | ❌ |

#### FR-19.2: Dataset Config (replaces Stats Config)

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19.2.1 | Rename "Stats Config" section to **"Dataset Config"** (icon: ⚙️) | P0 | ❌ |
| FR-19.2.2 | Retain existing stats fields checkboxes (label, color, model, quality_flag, direction) | P0 | ❌ |
| FR-19.2.3 | Add **Visible Labels** checkboxes: color, brand, model, label, type, sub_type, lp_coords | P0 | ❌ |
| FR-19.2.4 | Add **Quality Flags** list: editable list of quality flag names (add/remove) | P0 | ❌ |
| FR-19.2.5 | "Apply" button saves all config to `.dataset.json` AND MongoDB (if registered) | P0 | ❌ |
| FR-19.2.6 | Config stored in MongoDB under `config` field (not inside `metadata`) | P0 | ❌ |

#### FR-19.3: Apply Config on Dataset Open

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19.3.1 | On activation: if dataset is registered, load metadata + config from MongoDB | P0 | ❌ |
| FR-19.3.2 | Apply `config.visible_labels` → update grid label overlay | P0 | ❌ |
| FR-19.3.3 | Apply `config.quality_flags` → update quality flag options | P0 | ❌ |
| FR-19.3.4 | Apply `config.stats_fields` → load statistics with correct fields | P0 | ❌ |
| FR-19.3.5 | Merge strategy: MongoDB for metadata/config, `.dataset.json` for `image_flags` | P0 | ❌ |
| FR-19.3.6 | Non-registered datasets: load everything from `.dataset.json` (unchanged) | P0 | ❌ |

#### FR-19.4: MongoDB Schema Extension

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-19.4.1 | Add `config` field: `stats_fields`, `visible_labels`, `quality_flags`, `skip_delete_confirmation` | P0 | ❌ |
| FR-19.4.2 | Add `trainable_models` array to `metadata` field | P0 | ❌ |
| FR-19.4.3 | Add `attributes` array to `metadata` field | P0 | ❌ |
| FR-19.4.4 | Registration reads full metadata + config from `.dataset.json` into MongoDB | P0 | ❌ |
| FR-19.4.5 | Lazy migration: on first access after upgrade, missing fields filled from `.dataset.json` | P1 | ❌ |

---

## Data Models (v2.2)

### MongoDB `datasets` Collection Schema

```json
{
  "_id": "ObjectId",
  "name": "vehicle_colors_v4",
  "root_path": "/home/pauli/pdi_datasets/vehicle_colors_v4",
  "registered_at": "2026-02-25T10:00:00",
  "updated_at": "2026-02-25T15:30:00",
  "metadata": {
    "description": "Vehicle color classification dataset",
    "camera_view": ["frontal", "panorâmica"],
    "quality": "good",
    "verdict": "keep",
    "cycle": "second",
    "notes": "Ready for training.",
    "model_compatibility": ["colornet_v1", "colornet_v2"],
    "trainable_models": [
      { "name": "Panoramic Day", "enabled": true, "preprocessing": "none" },
      { "name": "BMC", "enabled": false, "preprocessing": "cropped" }
    ],
    "attributes": [
      { "name": "Normal", "enabled": true },
      { "name": "Low Light", "enabled": false }
    ]
  },
  "config": {
    "stats_fields": ["label", "color", "model"],
    "visible_labels": ["color", "brand", "model", "type"],
    "quality_flags": ["brass", "bronze", "silver", "gold"],
    "skip_delete_confirmation": false
  },
  "statistics": {
    "total_images": 1234,
    "class_counts": {
      "car": 890,
      "motorcycle": 120,
      "truck": 134,
      "bus": 90
    },
    "spatial": {
      "position_mean": { "x": 320.5, "y": 410.2 },
      "position_variance": { "x": 150.3, "y": 180.7 },
      "area_mean": 45230.0,
      "area_variance": 12500.0
    },
    "computed_at": "2026-02-25T10:05:00"
  },
  "thumbnails": {
    "paths": ["<id>_0.jpg", "<id>_1.jpg", "<id>_2.jpg", "<id>_3.jpg"],
    "generated_at": "2026-02-25T10:05:00"
  }
}
```

### `.dataset.json` Schema (Filesystem)

```json
{
  "name": "vehicle_colors_v4",
  "created_at": "2026-02-25T10:00:00",
  "updated_at": "2026-02-25T15:30:00",
  "image_flags": { "img001.jpg": { "quality_flag": "gold" } },
  "description": "",
  "camera_view": [],
  "quality": "good",
  "verdict": "keep",
  "cycle": "second",
  "notes": "",
  "trainable_models": [],
  "attributes": [],
  "stats_config": { "fields": ["label", "color", "model"] },
  "visible_labels": ["color", "brand", "model", "type"],
  "quality_flags": ["brass", "bronze", "silver", "gold"],
  "skip_delete_confirmation": false
}
```

### Data Ownership Map

```
Field                   .dataset.json    MongoDB         Authority (registered)
──────────────────────  ─────────────    ──────────────  ──────────────────────
name                    ✓                ✓ (top-level)   MongoDB
description             ✓                ✓ (metadata)    MongoDB
camera_view             ✓                ✓ (metadata)    MongoDB
quality                 ✓                ✓ (metadata)    MongoDB
verdict                 ✓                ✓ (metadata)    MongoDB
cycle                   ✓                ✓ (metadata)    MongoDB
notes                   ✓                ✓ (metadata)    MongoDB
trainable_models        ✓                ✓ (metadata)    MongoDB
attributes              ✓                ✓ (metadata)    MongoDB
model_compatibility     —                ✓ (metadata)    MongoDB
stats_fields            ✓ (stats_config) ✓ (config)      MongoDB
visible_labels          ✓                ✓ (config)      MongoDB
quality_flags           ✓                ✓ (config)      MongoDB
skip_delete_confirm     ✓                ✓ (config)      MongoDB
image_flags             ✓                —               .dataset.json (always)
statistics              —                ✓               MongoDB (computed)
thumbnails              —                ✓               MongoDB (generated)
```

### Model Compatibility Field

| Value | Description |
|-------|-------------|
| `colornet_v1` | ColorNet v1 — vehicle color classifier |
| `colornet_v2` | ColorNet v2 — multi-task color + type |
| `detect_v1` | Detection model v1 — vehicle detection |
| `brand_classifier` | Brand/model classifier |
| `custom` | Custom / user-defined model |

> **Note:** Model compatibility is a free-form multi-select. Users can type custom model names or pick from known values.

---

## User Interface Mockup (v2.1 — Datasets Dashboard Modal)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         📊 Datasets Dashboard                              [✕ Close] │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐      │
│  │ 🖼️ vehicle_colors_v4                │  │ 🖼️ night_vehicles_v2                │      │
│  │                                    │  │                                    │      │
│  │  ┌──────┐┌──────┐┌──────┐┌──────┐ │  │  ┌──────┐┌──────┐┌──────┐┌──────┐ │      │
│  │  │ img1 ││ img2 ││ img3 ││ img4 │ │  │  │ img1 ││ img2 ││ img3 ││ img4 │ │      │
│  │  └──────┘└──────┘└──────┘└──────┘ │  │  └──────┘└──────┘└──────┘└──────┘ │      │
│  │                                    │  │                                    │      │
│  │  Path: /home/.../vehicle_colors_v4 │  │  Path: /home/.../night_vehicles_v2 │      │
│  │  Cycle: second  Quality: good      │  │  Cycle: first   Quality: fair      │      │
│  │  Model: colornet_v1                │  │  Model: colornet_v2                │      │
│  │  Total: 1,234 images               │  │  Total: 567 images                 │      │
│  │                                    │  │                                    │      │
│  │  [Open]                            │  │  [Open]                            │      │
│  └────────────────────────────────────┘  └────────────────────────────────────┘      │
│                                                                                      │
│  ┌────────────────────────────────────┐  ┌────────────────────────────────────┐      │
│  │ 🖼️ panoramic_day_v1                 │  │ 🖼️ closeup_test_v3                  │      │
│  │  ...                               │  │  ...                               │      │
│  └────────────────────────────────────┘  └────────────────────────────────────┘      │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Datasets Dashboard — Detail View (expanded card)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    📊 Dataset: vehicle_colors_v4                    [← Back] [✕ Close]│
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │              │ │              │ │              │ │              │                │
│  │   thumb 1    │ │   thumb 2    │ │   thumb 3    │ │   thumb 4    │                │
│  │   (1st)      │ │   (25%)      │ │   (75%)      │ │   (last)     │                │
│  │              │ │              │ │              │ │              │                │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                                      │
│  ┌─ Metadata ─────────────────────────┐  ┌─ Statistics ───────────────────────────┐  │
│  │ Name:    [vehicle_colors_v4     ]  │  │ Total images: 1,234                    │  │
│  │ Path:    /home/.../vehicle_v4      │  │                                        │  │
│  │ Description:                       │  │ Classes:                               │  │
│  │ [Vehicle color dataset w/ day... ] │  │   car: 890   motorcycle: 120           │  │
│  │ Camera:  [frontal ▼] [panorâmica]  │  │   truck: 134   bus: 90                 │  │
│  │ Quality: [good ▼]                  │  │                                        │  │
│  │ Verdict: [keep ▼]                  │  │ Spatial (bbox):                        │  │
│  │ Cycle:   [second ▼]               │  │   Position μ: (320.5, 410.2)           │  │
│  │ Model:   [colornet_v1 ▼]          │  │   Position σ²: (150.3, 180.7)          │  │
│  │ Notes:                             │  │   Area μ: 45,230 px²                   │  │
│  │ [Ready for training. Cleanup... ]  │  │   Area σ²: 12,500 px²                 │  │
│  └────────────────────────────────────┘  │                                        │  │
│                                          │   Computed: 2026-02-25 10:05           │  │
│  [Open Dataset]  [🔄 Refresh Stats]      │   [🔄 Refresh]                         │  │
│  [🗑️ Remove from Dashboard]              └────────────────────────────────────────┘  │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Left Panel — Datasets Tab (v2.1)

```
┌─────────────────────┐
│ DATASETS             │
│                     │
│ ▼ Registered (3)    │
│   🟢 vehicle_v4     │
│   🟡 night_v2       │
│   🔴 closeup_v3     │
│                     │
│ [+ Add Current]     │
│ [📊 Dashboard]      │
│                     │
│ ─────────────────── │
│ ▼ Browse Directories│
│                     │
│ 📁 pdi_datasets     │
│  ├📁 train/         │
│  ├📁 test/          │
│  └📁 valid/         │
│                     │
│ [🔄 Activate]       │
└─────────────────────┘
```

#### Status Indicators (Registered Datasets)

| Indicator | Meaning |
|-----------|---------|
| 🟢 Green | verdict = keep |
| 🟡 Yellow | verdict = revise |
| 🔴 Red | verdict = remove |
| ⚪ Grey | Not reviewed / no verdict |

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
- MongoDB (pymongo) for datasets registry — server-side only
- MongoDB connection configurable via `MONGODB_URI` env var

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
    "lp_coords": "",
    "direction": "front"
  }
]
```

#### Direction Field (v1.2)

| Value | Meaning | Visual |
|-------|---------|--------|
| `front` | Vehicle facing camera (coming toward) | ▼ Arrow toward viewer |
| `back` | Vehicle facing away (going away) | ▲ Arrow away from viewer |

**Note:** If `direction` field is missing, default is `front`.

### Dataset JSON Schema (v2.0)

Stored as `.dataset.json` at the dataset root directory:

```json
{
  "version": "2.0",
  "type": "dataset",
  "name": "vehicle_colors_v4",
  "root_path": "/home/pauli/pdi_datasets/vehicle_colors_v4",
  "created": "2026-02-13T10:00:00",
  "updated": "2026-02-13T15:30:00",
  "metadata": {
    "description": "Vehicle color classification dataset with day/night, multiple camera views",
    "camera_view": ["frontal", "panorâmica"],
    "quality": "good",
    "verdict": "keep",
    "cycle": "second",
    "notes": "Ready for training. Cleanup complete."
  },
  "settings": {
    "display_mode": "direct",
    "class_stats_fields": ["label", "color", "model"],
    "skip_delete_confirmation": false,
    "visible_labels": ["color", "brand", "model", "type"],
    "quality_flags": ["bin", "review", "ok", "move"],
    "perspective_flags": ["close-up-day", "close-up-night", "pan-day", "pan-night", "super_pan_day", "super_pan_night", "cropped-day", "cropped-night"],
    "default_quality_flag": "review",
    "default_perspective_flag": null
  },
  "image_flags": {
    "train/000001_ABC123.jpg": {
      "quality_flags": ["ok"],
      "perspective_flags": ["pan-day"]
    },
    "test/000002_XYZ789.jpg": {
      "quality_flags": ["review"],
      "perspective_flags": ["close-up-day"]
    }
  }
}
```

#### Dataset Metadata Fields (v2.0)

| Field | Type | Options | Description |
|-------|------|---------|-------------|
| `name` | string | - | Display name (auto-filled from directory) |
| `description` | text | - | Brief description of dataset contents |
| `camera_view` | multi-select | frontal, traseira, panorâmica, closeup, super-panorâmica | Camera perspective(s) |
| `quality` | select | poor, fair, good, excellent | Overall dataset quality |
| `verdict` | select | keep, revise, remove | Action decision |
| `cycle` | select | first, second, third, fourth, fifth | Review iteration |
| `notes` | text | - | Additional observations |

---

## User Interface Mockup (v2.0)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ 🖼️ Dataset Review Tool                [2x2] [3x3] [5x5] [6x6]  [?] ⚙️               │
├─────────────────┬────────────────────────────────────────────┬───────────────────────┤
│ ◀ DIRECTORIES   │                                            │ DATASET INFO ▶       │
│                 │   ┌─────────┐  ┌─────────┐  ┌─────────┐   │                       │
│ 📁 pdi_datasets │   │  img1   │  │  img2   │  │  img3   │   │ 📊 Statistics         │
│  ├📁 train/     │   │  ▼      │  │  ▼      │  │  ▲      │   │ ─────────────────     │
│  │  ├📁 car/    │   └─────────┘  └─────────┘  └─────────┘   │ Total: 1,234 images   │
│  │  └📁 truck/  │                                            │   train: 800          │
│  ├📁 test/      │   ┌─────────┐  ┌─────────┐  ┌─────────┐   │   test: 234           │
│  └📁 valid/     │   │  img4   │  │  img5   │  │  img6   │   │   valid: 200          │
│                 │   └─────────┘  └─────────┘  └─────────┘   │                       │
│ ─────────────── │                                            │ Classes (label):      │
│ [+ New Folder]  │                                            │   car: 890            │
│ [🗑️ Delete]     │                                            │   truck: 234          │
│ [📦 Move]       │                                            │   moto: 110           │
│                 │                                            │                       │
│                 │                                            │ 📝 Metadata           │
│                 │                                            │ ─────────────────     │
│                 │                                            │ Name: [vehicle_v4  ]  │
│                 │                                            │ Description:          │
│                 │                                            │ [_________________ ]  │
│                 │                                            │ Camera: [frontal ▼]   │
│                 │                                            │ Quality: [good ▼]     │
│                 │                                            │ Verdict: [keep ▼]     │
│                 │                                            │ Cycle: [second ▼]     │
│                 │                                            │ Notes:                │
│                 │                                            │ [_________________ ]  │
│                 │                                            │                       │
│                 │                                            │ [🔄 Activate Dataset] │
├─────────────────┴────────────────────────────────────────────┴───────────────────────┤
│ Dataset: /pdi_datasets/vehicle_v4  |  Viewing: /train  |  Mode: [Direct ▼]  | 800 img│
└──────────────────────────────────────────────────────────────────────────────────────┘
```

---

## User Interface Mockup (v1.x)

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
| `h` | Toggle "Hide Non-Matching Vehicles" when filters are active |

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
| Directory operations fail mid-way (v2.0) | High | Atomic operations, rollback on failure |
| Accidental directory deletion (v2.0) | High | Move to trash first, confirmation dialog |
| Navigating outside base path (v2.0) | Medium | Strict path validation, configurable base |
| MongoDB unavailable (v2.1) | Medium | Graceful fallback — app works without dashboard, show warning |
| Dataset path moved/deleted after registration (v2.1) | Low | "Path not found" badge, option to re-link or remove |
| Large dataset statistics computation slow (v2.1) | Medium | Async computation, cached results, manual refresh |

---

## Success Metrics

- Review 500+ images per session without performance degradation
- Complete batch operations (delete/flag) in under 1 second
- Zero data loss from accidental operations
- User satisfaction: reduce review time by 50% vs single-image tools
- (v2.0) Dataset analysis: review and categorize 10+ datasets per session
- (v2.0) Quick dataset switching via recent datasets list
- (v2.1) Register and open datasets in under 3 clicks
- (v2.1) Dashboard overview of all datasets at a glance
- (v2.1) Statistics computation completes in under 10 seconds for 5K-image datasets

---

## Out of Scope (v1.x)

- Image editing (crop, rotate, adjust)
- Multi-user collaboration
- Version history/undo for JSON edits
- Export to other annotation formats
- Integration with ML training pipelines
- Moving individual images between directories

---

## Out of Scope (v2.0)

- Drag-and-drop images between folders
- Dataset comparison side-by-side
- Automatic dataset quality scoring
- Cloud/remote file system support

---

## Out of Scope (v2.1)

- Multi-user access to MongoDB (single-user local instance)
- Dataset versioning / history tracking
- Automatic model training trigger from dashboard
- Dataset merge / split operations
- Remote MongoDB hosting / authentication
