# Phase 1: Project Setup & Infrastructure

## Objective
Create the foundational Flask application with a project-based architecture. On startup, display a modal for creating/loading projects. Each project has its own JSON file storing settings, flags, and image metadata.

---

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Test Dataset:** `/home/pauli/temp/AIFX013_VCR/images/xywh/v4/test/`

---

## 1. Files to Create

| File | Purpose |
|------|---------|
| `tools/image_review/app.py` | Main Flask application |
| `tools/image_review/templates/index.html` | Single-page HTML template |
| `tools/image_review/static/css/styles.css` | CSS styles |
| `tools/image_review/static/js/app.js` | Client-side JavaScript |
| `tools/image_review/projects/` | Directory for project JSON files |
| `tools/image_review/README.md` | Update with Phase 1 testing info |

---

## 2. Project JSON Schema

**File:** `projects/{project_name}.json`

```json
{
  "version": "1.0",
  "project_name": "vehicle_colors_v4",
  "directory": "/home/pauli/temp/AIFX013_VCR/images/xywh/v4/test",
  "created": "2026-02-12T10:00:00",
  "updated": "2026-02-12T15:30:00",
  "settings": {
    "skip_delete_confirmation": false,
    "quality_flags": ["bin", "review", "ok", "move"],
    "perspective_flags": [
      "close-up-day", "close-up-night",
      "pan-day", "pan-night",
      "super_pan_day", "super_pan_night",
      "cropped-day", "cropped-night"
    ],
    "visible_labels": ["color", "brand", "model", "type"],
    "default_quality_flag": "review",
    "default_perspective_flag": null,
    "grid_size": 9
  },
  "images": []
}
```

### Image Entry Schema
```json
{
  "seq_id": 1,
  "filename": "000000_ASH4662_1.jpg",
  "json_filename": "000000_ASH4662_1.json",
  "quality_flags": ["review"],
  "perspective_flags": [],
  "deleted": false
}
```

---

## 3. Startup Modal UI

### Modal: "Project Setup"

```
┌──────────────────────────────────────────────────────────┐
│                    🖼️ Image Review Tool                  │
│                      Project Setup                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─ Create New Project ─────────────────────────────┐   │
│  │                                                   │   │
│  │  Project Name: [________________________]        │   │
│  │                                                   │   │
│  │  Image Directory:                                 │   │
│  │  [/path/to/images________________] [Browse...]   │   │
│  │                                                   │   │
│  │  Default Quality Flag:                            │   │
│  │  ( ) bin  (•) review  ( ) ok  ( ) move           │   │
│  │                                                   │   │
│  │  Default Perspective Flag:                        │   │
│  │  ( ) None  ( ) close-up-day  ( ) pan-day  ...    │   │
│  │                                                   │   │
│  │  Visible Labels:                                  │   │
│  │  [✓] color  [✓] brand  [✓] model  [ ] label     │   │
│  │  [✓] type   [ ] sub_type  [ ] lp_coords          │   │
│  │                                                   │   │
│  │                         [Create Project]          │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ─── OR ───                                              │
│                                                          │
│  ┌─ Open Recent Project ────────────────────────────┐   │
│  │                                                   │   │
│  │  [▼ Select a project...                    ]     │   │
│  │                                                   │   │
│  │  • vehicle_colors_v4 (500 images)                │   │
│  │  • night_dataset (1200 images)                   │   │
│  │  • cropped_test (89 images)                      │   │
│  │                                                   │   │
│  │                          [Open Project]           │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Flask Application Structure

### 4.1 Imports & Config

```python
from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
import json
import os
from datetime import datetime
from PIL import Image
import io
import base64

app = Flask(__name__)

# Configuration
PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_QUALITY_FLAGS = ["bin", "review", "ok", "move"]
DEFAULT_PERSPECTIVE_FLAGS = [
    "close-up-day", "close-up-night",
    "pan-day", "pan-night",
    "super_pan_day", "super_pan_night",
    "cropped-day", "cropped-night"
]
DEFAULT_VISIBLE_LABELS = ["color", "brand", "model", "type"]
```

### 4.2 ProjectManager Class

```python
class ProjectManager:
    def __init__(self):
        self.current_project = None
        self.project_data = None
    
    def create_project(self, name: str, directory: str, settings: dict) -> dict:
        """Create a new project and scan directory for images."""
        # Validate directory exists
        # Scan for .jpg/.png files
        # Create matching JSON file entries
        # Save project JSON
        pass
    
    def load_project(self, name: str) -> dict:
        """Load an existing project from JSON."""
        pass
    
    def save_project(self) -> None:
        """Save current project to JSON (auto-save)."""
        pass
    
    def list_projects(self) -> list:
        """List all available projects with metadata."""
        pass
    
    def scan_images(self, directory: str) -> list:
        """Scan directory for image files and their JSON labels."""
        pass
    
    def get_image_count(self) -> int:
        """Return count of non-deleted images."""
        pass

project_manager = ProjectManager()
```

### 4.3 Image Discovery Logic

```python
def scan_images(directory: str) -> list:
    """
    Scan directory for images and create image entries.
    
    Rules:
    1. Find all .jpg, .jpeg, .png files
    2. For each image, check if {name}.json exists
    3. Assign sequential seq_id starting from 1
    4. Apply default flags from settings
    
    Returns: List of image entry dicts
    """
    images = []
    dir_path = Path(directory)
    
    # Supported extensions
    extensions = {'.jpg', '.jpeg', '.png'}
    
    # Get all image files, sorted by name
    image_files = sorted([
        f for f in dir_path.iterdir()
        if f.suffix.lower() in extensions
    ])
    
    for seq_id, img_file in enumerate(image_files, start=1):
        json_file = img_file.with_suffix('.json')
        
        entry = {
            "seq_id": seq_id,
            "filename": img_file.name,
            "json_filename": json_file.name if json_file.exists() else None,
            "quality_flags": [settings["default_quality_flag"]] if settings.get("default_quality_flag") else [],
            "perspective_flags": [settings["default_perspective_flag"]] if settings.get("default_perspective_flag") else [],
            "deleted": False
        }
        images.append(entry)
    
    return images
```

---

## 5. API Endpoints

### 5.1 GET `/`
**Purpose:** Serve main HTML page with startup modal

**Response:** HTML page

---

### 5.2 GET `/api/projects`
**Purpose:** List all available projects

**Response:**
```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "name": "vehicle_colors_v4",
        "directory": "/home/pauli/.../test",
        "image_count": 500,
        "created": "2026-02-12T10:00:00",
        "updated": "2026-02-12T15:30:00"
      }
    ]
  }
}
```

---

### 5.3 POST `/api/projects`
**Purpose:** Create a new project

**Request Body:**
```json
{
  "name": "my_project",
  "directory": "/path/to/images",
  "settings": {
    "default_quality_flag": "review",
    "default_perspective_flag": null,
    "visible_labels": ["color", "brand", "model", "type"]
  }
}
```

**Validation:**
- `name`: Required, alphanumeric + underscore, max 50 chars
- `directory`: Required, must exist and contain images
- Project name must not already exist

**Response (success):**
```json
{
  "success": true,
  "data": {
    "project_name": "my_project",
    "image_count": 500
  },
  "message": "Project created with 500 images"
}
```

**Response (error):**
```json
{
  "success": false,
  "error": "Directory does not exist",
  "message": "Please select a valid directory"
}
```

---

### 5.4 GET `/api/projects/<name>`
**Purpose:** Load a specific project

**Response:**
```json
{
  "success": true,
  "data": {
    "project_name": "vehicle_colors_v4",
    "directory": "/path/to/images",
    "settings": { ... },
    "image_count": 500,
    "stats": {
      "total": 500,
      "flagged_ok": 123,
      "flagged_review": 377,
      "deleted": 0
    }
  }
}
```

---

### 5.5 POST `/api/browse`
**Purpose:** Browse filesystem for directory selection

**Request Body:**
```json
{
  "path": "/home/pauli/temp"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "current_path": "/home/pauli/temp",
    "parent": "/home/pauli",
    "directories": [
      {"name": "AIFX013_VCR", "path": "/home/pauli/temp/AIFX013_VCR"},
      {"name": "other_folder", "path": "/home/pauli/temp/other_folder"}
    ],
    "has_images": false,
    "image_count": 0
  }
}
```

---

## 6. HTML Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image Review Tool</title>
    <style>
        /* CSS goes here - see Section 7 */
    </style>
</head>
<body>
    <!-- Startup Modal (visible on load) -->
    <div id="startup-modal" class="modal">
        <div class="modal-content">
            <h1>🖼️ Image Review Tool</h1>
            <h2>Project Setup</h2>
            
            <!-- Create New Project Section -->
            <div class="section">
                <h3>Create New Project</h3>
                <div class="form-group">
                    <label>Project Name:</label>
                    <input type="text" id="project-name" placeholder="my_project">
                </div>
                <div class="form-group">
                    <label>Image Directory:</label>
                    <div class="input-with-button">
                        <input type="text" id="directory-path" readonly>
                        <button onclick="browseDirectory()">Browse...</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>Default Quality Flag:</label>
                    <div class="radio-group" id="default-quality-flags">
                        <!-- Populated by JS -->
                    </div>
                </div>
                <div class="form-group">
                    <label>Default Perspective Flag:</label>
                    <div class="radio-group" id="default-perspective-flags">
                        <!-- Populated by JS -->
                    </div>
                </div>
                <div class="form-group">
                    <label>Visible Labels:</label>
                    <div class="checkbox-group" id="visible-labels">
                        <!-- Populated by JS -->
                    </div>
                </div>
                <button class="primary" onclick="createProject()">Create Project</button>
            </div>
            
            <div class="divider">OR</div>
            
            <!-- Open Recent Section -->
            <div class="section">
                <h3>Open Recent Project</h3>
                <select id="recent-projects">
                    <option value="">Select a project...</option>
                </select>
                <button onclick="openProject()">Open Project</button>
            </div>
        </div>
    </div>
    
    <!-- Main Application (hidden until project loaded) -->
    <div id="main-app" class="hidden">
        <!-- Header -->
        <header>
            <h1>🖼️ Image Review Tool - <span id="project-title"></span></h1>
            <div class="toolbar">
                <!-- Grid size buttons -->
                <!-- Settings button -->
            </div>
        </header>
        
        <!-- Image Grid -->
        <main id="image-grid">
            <!-- Images populated by JS -->
        </main>
        
        <!-- Footer -->
        <footer>
            <!-- Pagination -->
        </footer>
    </div>
    
    <!-- Directory Browser Modal -->
    <div id="browser-modal" class="modal hidden">
        <!-- Directory browser content -->
    </div>
    
    <script>
        /* JavaScript goes here - see Section 8 */
    </script>
</body>
</html>
```

---

## 7. CSS Specifications

```css
/* Reset and Base */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e;
    color: #eee;
    min-height: 100vh;
}

/* Modal Styles */
.modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal.hidden {
    display: none;
}

.modal-content {
    background: #16213e;
    border-radius: 12px;
    padding: 32px;
    max-width: 600px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
}

.modal-content h1 {
    text-align: center;
    margin-bottom: 8px;
}

.modal-content h2 {
    text-align: center;
    color: #888;
    font-weight: normal;
    margin-bottom: 24px;
}

/* Form Elements */
.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
}

input[type="text"], select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #333;
    border-radius: 6px;
    background: #0f0f23;
    color: #eee;
    font-size: 14px;
}

.input-with-button {
    display: flex;
    gap: 8px;
}

.input-with-button input {
    flex: 1;
}

/* Buttons */
button {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    background: #333;
    color: #eee;
    transition: background 0.2s;
}

button:hover {
    background: #444;
}

button.primary {
    background: #4a69bd;
    width: 100%;
    margin-top: 16px;
}

button.primary:hover {
    background: #5a79cd;
}

/* Radio and Checkbox Groups */
.radio-group, .checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.radio-group label, .checkbox-group label {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    font-weight: normal;
}

/* Divider */
.divider {
    text-align: center;
    margin: 24px 0;
    color: #666;
    position: relative;
}

.divider::before, .divider::after {
    content: '';
    position: absolute;
    top: 50%;
    width: 40%;
    height: 1px;
    background: #333;
}

.divider::before { left: 0; }
.divider::after { right: 0; }

/* Section */
.section {
    background: #1a1a2e;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.section h3 {
    margin-bottom: 16px;
    font-size: 16px;
}

/* Hidden utility */
.hidden {
    display: none !important;
}
```

---

## 8. JavaScript Specifications

```javascript
// State
let currentProject = null;
let selectedDirectory = null;

// Constants
const DEFAULT_QUALITY_FLAGS = ['bin', 'review', 'ok', 'move'];
const DEFAULT_PERSPECTIVE_FLAGS = [
    'close-up-day', 'close-up-night',
    'pan-day', 'pan-night',
    'super_pan_day', 'super_pan_night',
    'cropped-day', 'cropped-night'
];
const ALL_LABELS = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
const DEFAULT_VISIBLE_LABELS = ['color', 'brand', 'model', 'type'];

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);

async function init() {
    populateDefaultOptions();
    await loadRecentProjects();
}

function populateDefaultOptions() {
    // Populate quality flags radio buttons
    const qualityContainer = document.getElementById('default-quality-flags');
    qualityContainer.innerHTML = DEFAULT_QUALITY_FLAGS.map((flag, i) => `
        <label>
            <input type="radio" name="default-quality" value="${flag}" ${i === 1 ? 'checked' : ''}>
            ${flag}
        </label>
    `).join('');
    
    // Add "None" option for perspective
    const perspectiveContainer = document.getElementById('default-perspective-flags');
    perspectiveContainer.innerHTML = `
        <label>
            <input type="radio" name="default-perspective" value="" checked>
            None
        </label>
    ` + DEFAULT_PERSPECTIVE_FLAGS.map(flag => `
        <label>
            <input type="radio" name="default-perspective" value="${flag}">
            ${flag}
        </label>
    `).join('');
    
    // Populate visible labels checkboxes
    const labelsContainer = document.getElementById('visible-labels');
    labelsContainer.innerHTML = ALL_LABELS.map(label => `
        <label>
            <input type="checkbox" name="visible-label" value="${label}" 
                   ${DEFAULT_VISIBLE_LABELS.includes(label) ? 'checked' : ''}>
            ${label}
        </label>
    `).join('');
}

async function loadRecentProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('recent-projects');
            select.innerHTML = '<option value="">Select a project...</option>';
            
            data.data.projects.forEach(project => {
                select.innerHTML += `
                    <option value="${project.name}">
                        ${project.name} (${project.image_count} images)
                    </option>
                `;
            });
        }
    } catch (error) {
        console.error('Failed to load projects:', error);
    }
}

async function browseDirectory() {
    // Open directory browser modal
    document.getElementById('browser-modal').classList.remove('hidden');
    await loadDirectory('/home');  // Start from home
}

async function loadDirectory(path) {
    try {
        const response = await fetch('/api/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await response.json();
        
        if (data.success) {
            // Update browser modal with directory contents
            renderDirectoryBrowser(data.data);
        }
    } catch (error) {
        console.error('Failed to browse directory:', error);
    }
}

function selectDirectory(path) {
    selectedDirectory = path;
    document.getElementById('directory-path').value = path;
    document.getElementById('browser-modal').classList.add('hidden');
}

async function createProject() {
    const name = document.getElementById('project-name').value.trim();
    const directory = document.getElementById('directory-path').value;
    
    // Validation
    if (!name) {
        alert('Please enter a project name');
        return;
    }
    if (!directory) {
        alert('Please select a directory');
        return;
    }
    
    // Get selected options
    const defaultQuality = document.querySelector('input[name="default-quality"]:checked')?.value;
    const defaultPerspective = document.querySelector('input[name="default-perspective"]:checked')?.value || null;
    const visibleLabels = Array.from(document.querySelectorAll('input[name="visible-label"]:checked'))
        .map(cb => cb.value);
    
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                directory,
                settings: {
                    default_quality_flag: defaultQuality,
                    default_perspective_flag: defaultPerspective,
                    visible_labels: visibleLabels
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentProject = name;
            closeStartupModal();
            initializeMainApp(data.data);
        } else {
            alert(data.error || 'Failed to create project');
        }
    } catch (error) {
        console.error('Failed to create project:', error);
        alert('Failed to create project');
    }
}

async function openProject() {
    const name = document.getElementById('recent-projects').value;
    
    if (!name) {
        alert('Please select a project');
        return;
    }
    
    try {
        const response = await fetch(`/api/projects/${name}`);
        const data = await response.json();
        
        if (data.success) {
            currentProject = name;
            closeStartupModal();
            initializeMainApp(data.data);
        } else {
            alert(data.error || 'Failed to load project');
        }
    } catch (error) {
        console.error('Failed to load project:', error);
        alert('Failed to load project');
    }
}

function closeStartupModal() {
    document.getElementById('startup-modal').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
}

function initializeMainApp(projectData) {
    // Set project title
    document.getElementById('project-title').textContent = projectData.project_name;
    
    // Initialize grid view (Phase 2)
    // ...
}
```

---

## 9. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-1.1 | Startup modal appears on page load | Open app, verify modal visible |
| AC-1.2 | Can browse filesystem for directories | Click Browse, navigate folders |
| AC-1.3 | Can create new project with valid inputs | Enter name, select dir, click Create |
| AC-1.4 | Project JSON created in `projects/` folder | Check file exists with correct schema |
| AC-1.5 | Images scanned and added to project JSON | Verify image_count matches actual files |
| AC-1.6 | Default flags applied to all images | Check image entries have default flags |
| AC-1.7 | Recent projects appear in dropdown | Create project, reload, verify in list |
| AC-1.8 | Can load existing project | Select from dropdown, click Open |
| AC-1.9 | Main app hidden until project loaded | Verify #main-app has .hidden class |
| AC-1.10 | Error shown for invalid project name | Enter special chars, verify error |
| AC-1.11 | Error shown for invalid/empty directory | Select non-existent path, verify error |

---

## 10. Error Handling

| Error | Cause | User Message |
|-------|-------|--------------|
| `INVALID_NAME` | Name contains invalid characters | "Project name can only contain letters, numbers, and underscores" |
| `NAME_EXISTS` | Project with name already exists | "A project with this name already exists" |
| `DIR_NOT_FOUND` | Directory doesn't exist | "Directory not found. Please select a valid path" |
| `NO_IMAGES` | Directory contains no images | "No images found in selected directory" |
| `PERMISSION_DENIED` | Can't read directory | "Permission denied. Check folder permissions" |

---

## 11. Implementation Notes

1. **Atomic JSON writes**: Write to temp file, then rename
2. **Directory validation**: Check path exists AND is directory
3. **Image extensions**: Support `.jpg`, `.jpeg`, `.png` (case-insensitive)
4. **Sequential IDs**: Start from 1, increment per image
5. **JSON label files**: Optional - image works without JSON, just shows "NULL" for labels
6. **Auto-save**: Save project JSON on every change (debounce 500ms)
7. **Browser modal**: Show only directories, not files

---

## 12. Dependencies

```python
# requirements.txt additions
flask>=2.0.0
Pillow>=9.0.0
```

---

## 13. Test Cases

### Unit Tests
```python
def test_project_manager_create():
    """Test creating a new project."""
    pm = ProjectManager()
    result = pm.create_project("test_project", "/valid/path", {})
    assert result["success"] == True
    assert Path("projects/test_project.json").exists()

def test_project_manager_invalid_name():
    """Test that invalid names are rejected."""
    pm = ProjectManager()
    result = pm.create_project("test project!", "/valid/path", {})
    assert result["success"] == False
    assert "invalid" in result["error"].lower()

def test_scan_images():
    """Test image scanning."""
    images = scan_images("/path/with/3/images")
    assert len(images) == 3
    assert images[0]["seq_id"] == 1
    assert images[2]["seq_id"] == 3
```

### Integration Tests
1. Create project → Verify JSON file created
2. Load project → Verify data matches saved JSON
3. Browse directory → Verify correct folders shown
4. Create project with defaults → Verify flags applied to images
