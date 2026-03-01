# Phase 13: Dataset Activation System

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Implement dataset activation to make a selected directory the working root. Introduces the `.dataset.json` file format for storing dataset metadata and image flags. Implements Direct vs Recursive display modes for viewing images.

---

## 1. Prerequisites
- Phase 12 complete (File System Browser)
- Directory tree navigation working
- Base path configuration functional

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Dataset Root** | Directory activated as current working dataset |
| **Working Directory** | Current folder within dataset being viewed |
| **Direct Mode** | Show only images in current directory |
| **Recursive Mode** | Show images from current directory and all subdirectories |
| **Display Mode** | Direct (default) or Recursive |
| **.dataset.json** | Metadata file at dataset root |

### 2.2 State Model

```javascript
const datasetState = {
    isActive: false,                          // Is a dataset currently active?
    rootPath: null,                           // Dataset root directory
    workingPath: null,                        // Current working directory
    displayMode: 'direct',                    // 'direct' or 'recursive'
    metadata: null,                           // Loaded .dataset.json content
    images: [],                               // Current image list
    stats: null                               // Class statistics
};
```

---

## 3. Data Model

### 3.1 .dataset.json Schema

```json
{
    "version": "2.0",
    "name": "vehicle_colors_v4",
    "description": "Vehicle color classification dataset - production ready",
    "camera_view": ["frontal", "traseira"],
    "quality": "good",
    "verdict": "keep",
    "cycle": "second",
    "notes": "Reviewed by team on 2025-01-15",
    "created_at": "2025-01-10T14:30:00Z",
    "updated_at": "2025-01-15T09:45:00Z",
    "stats_config": {
        "fields": ["label", "color", "model"]
    },
    "image_flags": {
        "seq_001_v0": {
            "quality_flag": "ok",
            "direction": "front",
            "reviewed_at": "2025-01-15T10:00:00Z"
        },
        "seq_001_v1": {
            "quality_flag": "review",
            "direction": "back",
            "reviewed_at": "2025-01-15T10:01:00Z"
        }
    }
}
```

### 3.2 Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Schema version ("2.0") |
| `name` | string | Dataset display name |
| `description` | string | Free text description |
| `camera_view` | array | Selected camera views |
| `quality` | string | Quality rating |
| `verdict` | string | Dataset verdict |
| `cycle` | string | Review cycle |
| `notes` | string | Free text notes |
| `created_at` | string | ISO timestamp |
| `updated_at` | string | ISO timestamp |
| `stats_config` | object | Statistics configuration |
| `image_flags` | object | Per-image flags keyed by vehicle ID |

---

## 4. UI Components

### 4.1 Dataset Activation Toolbar

```
┌─────────────────────────────────────────────────────────────┐
│ [📁 No Dataset] ▼  | [Direct ⚫] [Recursive ○] | 📁 /path  │
└─────────────────────────────────────────────────────────────┘
```

**With Active Dataset:**
```
┌─────────────────────────────────────────────────────────────┐
│ [📁 vehicle_v4] ▼  | [Direct ⚫] [Recursive ○] | 📁 /train │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Activate Dataset Button (in Directory Panel)

```html
<div class="directory-actions">
    <button class="dir-action-btn activate-btn" onclick="activateDataset()" disabled>
        <span>⚡</span> Activate Dataset
    </button>
    ...
</div>
```

### 4.3 Dataset Selector Dropdown

```html
<div class="dataset-selector">
    <button class="dataset-current" onclick="toggleDatasetDropdown()">
        <span class="dataset-icon">📁</span>
        <span class="dataset-name" id="current-dataset-name">No Dataset</span>
        <span class="dropdown-arrow">▼</span>
    </button>
    <div class="dataset-dropdown hidden" id="dataset-dropdown">
        <div class="dropdown-header">Recent Datasets</div>
        <div class="dropdown-content" id="dataset-dropdown-list">
            <!-- Recent datasets -->
        </div>
        <div class="dropdown-divider"></div>
        <button class="dropdown-action" onclick="deactivateDataset()">
            <span>✕</span> Close Dataset
        </button>
    </div>
</div>
```

### 4.4 Display Mode Toggle

```html
<div class="display-mode-toggle">
    <button class="mode-btn active" data-mode="direct" onclick="setDisplayMode('direct')">
        Direct
    </button>
    <button class="mode-btn" data-mode="recursive" onclick="setDisplayMode('recursive')">
        Recursive
    </button>
</div>
```

### 4.5 Visual States

| State | Dataset Selector | Directory Tree |
|-------|------------------|----------------|
| No Dataset | "📁 No Dataset" | Normal folders |
| Dataset Active | "📁 dataset_name" | Root folder highlighted |
| Working Dir | Shows current path | Working folder has indicator |

---

## 5. CSS Styling

```css
/* Dataset Toolbar */
.dataset-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: #252536;
    border-bottom: 1px solid #333;
}

/* Dataset Selector */
.dataset-selector {
    position: relative;
}

.dataset-current {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #eee;
    cursor: pointer;
    min-width: 180px;
}

.dataset-current:hover {
    background: #3a3a4a;
}

.dataset-current.active {
    border-color: #4a69bd;
    background: rgba(74, 105, 189, 0.2);
}

.dataset-name {
    flex: 1;
    text-align: left;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.dataset-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    min-width: 250px;
    background: #2a2a3a;
    border: 1px solid #444;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    z-index: 1000;
}

.dataset-dropdown.hidden {
    display: none;
}

.dropdown-header {
    padding: 8px 12px;
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.dropdown-item {
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
}

.dropdown-item:hover {
    background: rgba(255,255,255,0.05);
}

.dropdown-divider {
    height: 1px;
    background: #444;
    margin: 4px 0;
}

.dropdown-action {
    width: 100%;
    padding: 8px 12px;
    text-align: left;
    background: none;
    border: none;
    color: #ff6b6b;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
}

.dropdown-action:hover {
    background: rgba(255,107,107,0.1);
}

/* Display Mode Toggle */
.display-mode-toggle {
    display: flex;
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid #444;
}

.mode-btn {
    padding: 6px 12px;
    background: #333;
    border: none;
    color: #888;
    cursor: pointer;
    font-size: 12px;
}

.mode-btn:hover {
    background: #3a3a4a;
    color: #ccc;
}

.mode-btn.active {
    background: #4a69bd;
    color: #fff;
}

/* Working Path Display */
.working-path {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #888;
    font-size: 12px;
    max-width: 300px;
    overflow: hidden;
}

.working-path .path-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* Activate Button (in directory panel) */
.activate-btn {
    background: #4a69bd !important;
    border-color: #5a79cd !important;
}

.activate-btn:hover:not(:disabled) {
    background: #5a79cd !important;
}

.activate-btn:disabled {
    background: #333 !important;
    border-color: #444 !important;
}

/* Directory Node - Dataset Root Indicator */
.dir-node.dataset-root {
    border-left: 3px solid #4a69bd;
    padding-left: 5px;
}

.dir-node.working-dir::after {
    content: '◀';
    color: #4a69bd;
    margin-left: 8px;
    font-size: 10px;
}
```

---

## 6. JavaScript Implementation

### 6.1 Dataset Activation

```javascript
async function activateDataset() {
    const selectedPath = filesystemState.selectedPath;
    if (!selectedPath) {
        showNotification('Select a directory first', 'warning');
        return;
    }
    
    try {
        // Load or create .dataset.json
        const response = await fetch(`/api/dataset/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: selectedPath })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        // Update state
        datasetState.isActive = true;
        datasetState.rootPath = selectedPath;
        datasetState.workingPath = selectedPath;
        datasetState.metadata = result.data.metadata;
        
        // Update UI
        updateDatasetUI();
        
        // Add to recent datasets
        addToRecentDatasets(selectedPath, result.data.metadata.name);
        
        // Load images
        await loadDatasetImages();
        
        showNotification(`Dataset activated: ${result.data.metadata.name}`, 'success');
    } catch (error) {
        console.error('Failed to activate dataset:', error);
        showNotification('Failed to activate dataset', 'error');
    }
}

function deactivateDataset() {
    datasetState.isActive = false;
    datasetState.rootPath = null;
    datasetState.workingPath = null;
    datasetState.metadata = null;
    datasetState.images = [];
    datasetState.stats = null;
    
    updateDatasetUI();
    showEmptyGridMessage('Select a directory and click "Activate Dataset" to begin');
    
    showNotification('Dataset closed', 'info');
}
```

### 6.2 Display Mode

```javascript
function setDisplayMode(mode) {
    if (mode !== 'direct' && mode !== 'recursive') {
        return;
    }
    
    datasetState.displayMode = mode;
    
    // Update UI
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    // Reload images with new mode
    if (datasetState.isActive) {
        loadDatasetImages();
    }
}
```

### 6.3 Load Images

```javascript
async function loadDatasetImages() {
    if (!datasetState.isActive) return;
    
    const params = new URLSearchParams({
        root: datasetState.rootPath,
        working: datasetState.workingPath,
        mode: datasetState.displayMode
    });
    
    try {
        showLoadingSpinner();
        
        const response = await fetch(`/api/dataset/images?${params}`);
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        datasetState.images = result.data.images;
        datasetState.stats = result.data.stats;
        
        renderImageGrid();
        updateStatsPanel();
        
    } catch (error) {
        console.error('Failed to load images:', error);
        showNotification('Failed to load images', 'error');
    } finally {
        hideLoadingSpinner();
    }
}
```

### 6.4 Working Directory Navigation

```javascript
function changeWorkingDirectory(path) {
    if (!datasetState.isActive) return;
    
    // Validate path is within dataset root
    if (!path.startsWith(datasetState.rootPath)) {
        showNotification('Cannot navigate outside dataset root', 'warning');
        return;
    }
    
    datasetState.workingPath = path;
    
    // Update tree UI
    updateDirectoryTreeSelection();
    
    // Update toolbar
    updateWorkingPathDisplay();
    
    // Reload images
    loadDatasetImages();
}

function navigateUp() {
    if (!datasetState.isActive) return;
    if (datasetState.workingPath === datasetState.rootPath) {
        showNotification('Already at dataset root', 'info');
        return;
    }
    
    const parentPath = datasetState.workingPath.substring(0, datasetState.workingPath.lastIndexOf('/'));
    changeWorkingDirectory(parentPath);
}
```

### 6.5 UI Updates

```javascript
function updateDatasetUI() {
    // Update dataset selector
    const nameEl = document.getElementById('current-dataset-name');
    const selectorBtn = document.querySelector('.dataset-current');
    
    if (datasetState.isActive) {
        nameEl.textContent = datasetState.metadata.name || 'Unnamed';
        selectorBtn.classList.add('active');
    } else {
        nameEl.textContent = 'No Dataset';
        selectorBtn.classList.remove('active');
    }
    
    // Update activate button
    const activateBtn = document.querySelector('.activate-btn');
    if (activateBtn) {
        activateBtn.disabled = datasetState.isActive || !filesystemState.selectedPath;
    }
    
    // Update directory tree to show dataset root
    updateDirectoryTreeSelection();
    
    // Update working path display
    updateWorkingPathDisplay();
}

function updateWorkingPathDisplay() {
    const pathEl = document.querySelector('.working-path .path-text');
    if (!pathEl) return;
    
    if (datasetState.isActive) {
        // Show relative path from dataset root
        const relativePath = datasetState.workingPath.replace(datasetState.rootPath, '') || '/';
        pathEl.textContent = relativePath;
    } else {
        pathEl.textContent = '';
    }
}

function updateDirectoryTreeSelection() {
    // Clear all special classes
    document.querySelectorAll('.dir-node').forEach(node => {
        node.classList.remove('dataset-root', 'working-dir');
    });
    
    if (!datasetState.isActive) return;
    
    // Mark dataset root
    const rootNode = document.querySelector(`.dir-node[data-path="${datasetState.rootPath}"]`);
    if (rootNode) {
        rootNode.classList.add('dataset-root');
    }
    
    // Mark working directory
    const workingNode = document.querySelector(`.dir-node[data-path="${datasetState.workingPath}"]`);
    if (workingNode) {
        workingNode.classList.add('working-dir');
    }
}

function toggleDatasetDropdown() {
    const dropdown = document.getElementById('dataset-dropdown');
    dropdown.classList.toggle('hidden');
}
```

---

## 7. Backend API

### 7.1 Activate Dataset

```python
@app.route('/api/dataset/activate', methods=['POST'])
def activate_dataset():
    """Activate a directory as dataset."""
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'}), 400
    
    # Load or create .dataset.json
    dataset_file = target / '.dataset.json'
    
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                metadata = json.load(f)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Invalid .dataset.json'}), 400
    else:
        # Create new metadata
        metadata = {
            'version': '2.0',
            'name': target.name,
            'description': '',
            'camera_view': [],
            'quality': '',
            'verdict': '',
            'cycle': '',
            'notes': '',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'stats_config': {
                'fields': ['label', 'color', 'model']
            },
            'image_flags': {}
        }
        
        # Save new metadata
        with open(dataset_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    return jsonify({
        'success': True,
        'data': {
            'path': str(target),
            'metadata': metadata
        }
    })
```

### 7.2 Get Dataset Images

```python
@app.route('/api/dataset/images', methods=['GET'])
def get_dataset_images():
    """Get images from dataset with display mode."""
    root_path = request.args.get('root')
    working_path = request.args.get('working')
    mode = request.args.get('mode', 'direct')  # 'direct' or 'recursive'
    
    if not root_path or not working_path:
        return jsonify({'success': False, 'error': 'Missing path parameters'}), 400
    
    root = Path(root_path)
    working = Path(working_path)
    
    if not working.exists() or not working.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'}), 400
    
    # Validate working is within root
    if not str(working).startswith(str(root)):
        return jsonify({'success': False, 'error': 'Working directory outside dataset root'}), 403
    
    # Find images
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    images = []
    
    if mode == 'direct':
        # Only images in working directory
        for item in working.iterdir():
            if item.is_file() and item.suffix.lower() in image_extensions:
                images.append(build_image_info(item, root))
    else:  # recursive
        # Images in working directory and all subdirectories
        for item in working.rglob('*'):
            if item.is_file() and item.suffix.lower() in image_extensions:
                images.append(build_image_info(item, root))
    
    # Load dataset metadata for flags
    dataset_file = root / '.dataset.json'
    image_flags = {}
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                metadata = json.load(f)
                image_flags = metadata.get('image_flags', {})
        except:
            pass
    
    # Merge flags into images
    for img in images:
        flags = image_flags.get(img['id'], {})
        img['quality_flag'] = flags.get('quality_flag', '')
        img['direction'] = flags.get('direction', '')
    
    # Calculate stats
    stats = calculate_class_stats(images, root)
    
    return jsonify({
        'success': True,
        'data': {
            'images': images,
            'stats': stats,
            'total': len(images),
            'mode': mode
        }
    })

def build_image_info(path, root):
    """Build image info dict."""
    rel_path = path.relative_to(root)
    
    # Try to load label JSON
    label_path = path.with_suffix('.json')
    label_data = {}
    if label_path.exists():
        try:
            with open(label_path) as f:
                label_data = json.load(f)
        except:
            pass
    
    return {
        'id': path.stem,  # filename without extension
        'filename': path.name,
        'path': str(path),
        'relative_path': str(rel_path),
        'label': label_data.get('label', ''),
        'color': label_data.get('color', ''),
        'model': label_data.get('model', ''),
        # Flags loaded separately from .dataset.json
    }

def calculate_class_stats(images, root):
    """Calculate class statistics."""
    # Load stats config
    dataset_file = root / '.dataset.json'
    fields = ['label', 'color', 'model']  # default
    
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                metadata = json.load(f)
                fields = metadata.get('stats_config', {}).get('fields', fields)
        except:
            pass
    
    stats = {}
    for field in fields:
        counts = {}
        for img in images:
            value = img.get(field, '') or 'unknown'
            counts[value] = counts.get(value, 0) + 1
        stats[field] = counts
    
    return stats
```

### 7.3 Update Image Flags

```python
@app.route('/api/dataset/image/<image_id>/flag', methods=['POST'])
def update_image_flag():
    """Update flags for an image."""
    image_id = request.view_args.get('image_id')
    data = request.get_json()
    
    root_path = data.get('dataset_root')
    flag_name = data.get('flag')  # 'quality_flag' or 'direction'
    flag_value = data.get('value')
    
    if not root_path or not flag_name:
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400
    
    root = Path(root_path)
    dataset_file = root / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        if 'image_flags' not in metadata:
            metadata['image_flags'] = {}
        
        if image_id not in metadata['image_flags']:
            metadata['image_flags'][image_id] = {}
        
        metadata['image_flags'][image_id][flag_name] = flag_value
        metadata['image_flags'][image_id]['reviewed_at'] = datetime.utcnow().isoformat() + 'Z'
        metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        with open(dataset_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'success': True,
            'data': {
                'image_id': image_id,
                'flag': flag_name,
                'value': flag_value
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 8. HTML Template Updates

### 8.1 Dataset Toolbar

```html
<!-- Dataset Toolbar (above grid) -->
<div class="dataset-toolbar" id="dataset-toolbar">
    <!-- Dataset Selector -->
    <div class="dataset-selector">
        <button class="dataset-current" onclick="toggleDatasetDropdown()">
            <span class="dataset-icon">📁</span>
            <span class="dataset-name" id="current-dataset-name">No Dataset</span>
            <span class="dropdown-arrow">▼</span>
        </button>
        <div class="dataset-dropdown hidden" id="dataset-dropdown">
            <div class="dropdown-header">Recent Datasets</div>
            <div class="dropdown-content" id="dataset-dropdown-list">
                <!-- Populated dynamically -->
            </div>
            <div class="dropdown-divider"></div>
            <button class="dropdown-action" onclick="deactivateDataset()">
                <span>✕</span> Close Dataset
            </button>
        </div>
    </div>
    
    <!-- Display Mode Toggle -->
    <div class="display-mode-toggle">
        <button class="mode-btn active" data-mode="direct" onclick="setDisplayMode('direct')" title="Show images in current folder only">
            Direct
        </button>
        <button class="mode-btn" data-mode="recursive" onclick="setDisplayMode('recursive')" title="Show images from all subfolders">
            Recursive
        </button>
    </div>
    
    <!-- Working Path Display -->
    <div class="working-path">
        <span class="path-icon">📁</span>
        <span class="path-text" id="working-path-text"></span>
        <button class="path-up-btn" onclick="navigateUp()" title="Go to parent folder">↑</button>
    </div>
    
    <!-- Image Count -->
    <div class="image-count" id="image-count">
        0 images
    </div>
</div>
```

### 8.2 Update Directory Panel Actions

```html
<!-- Add Activate button to directory panel -->
<div class="directory-actions" id="directory-actions">
    <button class="dir-action-btn activate-btn" onclick="activateDataset()" title="Activate as dataset" disabled>
        <span>⚡</span> Activate Dataset
    </button>
    <button class="dir-action-btn" onclick="createNewFolder()" title="Create new folder">
        <span>+</span> New Folder
    </button>
    <button class="dir-action-btn" onclick="deleteSelectedFolder()" title="Delete selected folder" disabled>
        <span>🗑️</span> Delete
    </button>
    <button class="dir-action-btn" onclick="moveSelectedFolder()" title="Move selected folder" disabled>
        <span>📦</span> Move
    </button>
</div>
```

---

## 9. Testing Checklist

### 9.1 Dataset Activation

- [ ] Select folder in tree → click "Activate Dataset" → dataset loads
- [ ] First activation creates `.dataset.json` with default values
- [ ] Subsequent activations load existing `.dataset.json`
- [ ] Dataset name appears in toolbar selector
- [ ] Grid populates with images from directory

### 9.2 Display Modes

- [ ] Default mode is "Direct"
- [ ] Direct mode → shows only images in working directory
- [ ] Recursive mode → shows images from all subdirectories
- [ ] Toggle mode → grid updates immediately
- [ ] Mode persists during navigation

### 9.3 Working Directory Navigation

- [ ] Double-click folder in tree → changes working directory
- [ ] Grid updates to show images from new directory
- [ ] Working path display updates
- [ ] Cannot navigate outside dataset root

### 9.4 Navigate Up

- [ ] Click "↑" button → navigates to parent folder
- [ ] At dataset root → shows notification "Already at root"
- [ ] Grid and path display update

### 9.5 Dataset Selector

- [ ] Click selector → dropdown appears
- [ ] Recent datasets listed in dropdown
- [ ] Click recent → loads that dataset
- [ ] "Close Dataset" → deactivates dataset, shows empty grid

### 9.6 Image Flags

- [ ] Quality flag toggle works → updates `.dataset.json`
- [ ] Direction toggle works → updates `.dataset.json`
- [ ] Flags persist after page refresh
- [ ] Flags appear correctly in grid

### 9.7 Class Statistics

- [ ] Stats panel shows counts for configured fields
- [ ] Default fields: label, color, model
- [ ] Stats update when images loaded

### 9.8 Edge Cases

- [ ] Empty directory → shows "No images in this directory"
- [ ] Directory with no image files → shows appropriate message
- [ ] Permission denied → shows error notification

---

## 10. Files Changed Summary

| File | Changes |
|------|---------|
| `app.py` | Add activate, images, flag endpoints |
| `static/js/app.js` | Add datasetState, activation functions, display mode |
| `static/css/styles.css` | Add dataset toolbar, display mode, working path styles |
| `templates/index.html` | Add dataset toolbar section |

---

## 11. Migration Notes

### 11.1 Flag Storage Change

- **Before:** Flags stored in individual label JSON files
- **After:** Flags stored in `.dataset.json` at dataset root
- **Migration:** Auto-migrate existing flags on first activation (optional)

### 11.2 API Changes

- `/api/project/*` endpoints → `/api/dataset/*` endpoints
- Quality/direction flags now use `/api/dataset/image/<id>/flag`

---

## 12. Implementation Order

1. **Backend API** - Add dataset activation, images, flag endpoints
2. **State Management** - Add datasetState object
3. **Dataset Toolbar** - Add HTML and CSS for toolbar
4. **Activation Logic** - Implement activate/deactivate functions
5. **Display Mode** - Implement direct/recursive toggle
6. **Image Loading** - Connect to new images API
7. **Flag Updates** - Connect to new flag API
8. **Working Directory** - Implement navigation within dataset
9. **Recent Datasets** - Connect to dropdown
10. **Testing** - Manual tests per checklist
