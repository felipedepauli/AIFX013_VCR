# Implementation Spec: Directory-Based Navigation

## Guiding Principle

**MINIMAL CHANGES TO EXISTING CODE**

The existing app works. We're adding a new entry point (directory browser) that feeds into the existing image loading pipeline.

---

## Phase 1: Backend Endpoints

### 1.1 Add `/api/browse/tree` Endpoint

**File**: `app.py`
**Location**: After existing `/api/filesystem/tree` (reuse/rename it)

```python
@app.route('/api/browse/tree')
def browse_tree():
    """Get directory tree for browsing."""
    path = request.args.get('path', BASE_PATH)
    depth = int(request.args.get('depth', 2))
    
    # Reuse existing tree-building logic
    # Return: { success: true, data: { name, path, children: [...] } }
```

### 1.2 Add `/api/browse/activate` Endpoint

**File**: `app.py`

```python
@app.route('/api/browse/activate', methods=['POST'])
def activate_directory():
    """Mark directory as active dataset, create .dataset.json if needed."""
    data = request.get_json()
    path = Path(data.get('path'))
    
    if not path.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    dataset_file = path / '.dataset.json'
    if not dataset_file.exists():
        dataset_file.write_text(json.dumps({
            'created_at': datetime.now().isoformat(),
            'image_flags': {}
        }, indent=2))
    
    return jsonify({'success': True, 'path': str(path)})
```

### 1.3 Modify `/api/images` to Accept Directory

**File**: `app.py`
**Change**: Add `directory` parameter as alternative to `project`

```python
@app.route('/api/images')
def get_images():
    # ADD: Check for directory parameter first
    directory = request.args.get('directory')
    if directory:
        return get_images_from_directory(directory, request.args)
    
    # KEEP: Existing project-based logic for backwards compatibility
    project_name = request.args.get('project', ...)
    ...
```

### 1.4 Add Directory Image Loading

**File**: `app.py`

```python
def get_images_from_directory(directory_path, args):
    """Load images from directory (new entry point)."""
    path = Path(directory_path)
    mode = args.get('mode', 'direct')
    page = int(args.get('page', 1))
    per_page = int(args.get('per_page', 50))
    
    # Find images
    if mode == 'recursive':
        image_files = list(path.rglob('*.jpg')) + list(path.rglob('*.png'))
    else:
        image_files = [f for f in path.iterdir() 
                       if f.suffix.lower() in ['.jpg', '.png', '.jpeg']]
    
    # Sort and paginate
    image_files.sort(key=lambda x: x.name)
    total = len(image_files)
    start = (page - 1) * per_page
    page_files = image_files[start:start + per_page]
    
    # Build response - SAME FORMAT as existing /api/images
    images = []
    for img_path in page_files:
        # Read label JSON if exists
        label_path = img_path.with_suffix('.json')
        labels = {}
        if label_path.exists():
            labels = json.loads(label_path.read_text())
        
        # Read flags from .dataset.json
        flags = load_image_flags(path, img_path.stem)
        
        images.append({
            'filename': img_path.name,
            'path': str(img_path),
            'relative_path': str(img_path.relative_to(path)),
            # Include all fields existing code expects
            'labels': labels,
            'quality_flag': flags.get('quality_flag', ''),
            'perspective_flag': flags.get('perspective_flag', ''),
            # ... other fields as needed
        })
    
    return jsonify({
        'success': True,
        'images': images,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })
```

### 1.5 Flag Storage Functions

**File**: `app.py`

```python
def load_image_flags(dataset_path, image_id):
    """Load flags for image from .dataset.json"""
    dataset_file = Path(dataset_path) / '.dataset.json'
    if not dataset_file.exists():
        return {}
    
    data = json.loads(dataset_file.read_text())
    return data.get('image_flags', {}).get(image_id, {})

def save_image_flag(dataset_path, image_id, flag_name, flag_value):
    """Save flag for image to .dataset.json"""
    dataset_file = Path(dataset_path) / '.dataset.json'
    
    if dataset_file.exists():
        data = json.loads(dataset_file.read_text())
    else:
        data = {'created_at': datetime.now().isoformat(), 'image_flags': {}}
    
    if image_id not in data['image_flags']:
        data['image_flags'][image_id] = {}
    
    data['image_flags'][image_id][flag_name] = flag_value
    dataset_file.write_text(json.dumps(data, indent=2))
```

---

## Phase 2: Frontend - Sidebar Tabs

### 2.1 HTML Structure

**File**: `templates/index.html`
**Change**: Wrap filter panel in tab structure

```html
<!-- sidebar -->
<div class="sidebar" id="filter-panel">
    <!-- Tab Headers -->
    <div class="sidebar-tabs">
        <button class="sidebar-tab active" data-tab="filters">Filters</button>
        <button class="sidebar-tab" data-tab="directories">Directories</button>
    </div>
    
    <!-- Tab Content: Filters (EXISTING - just wrap in div) -->
    <div class="sidebar-tab-content active" id="tab-filters">
        <!-- ALL EXISTING FILTER PANEL HTML UNCHANGED -->
        <div class="filter-section">
            ...
        </div>
    </div>
    
    <!-- Tab Content: Directories (NEW) -->
    <div class="sidebar-tab-content" id="tab-directories">
        <div class="directory-browser">
            <div class="directory-tree" id="directory-tree">
                <!-- Tree populated by JS -->
            </div>
            <div class="directory-actions">
                <button id="btn-activate" class="btn-primary" disabled>
                    Activate
                </button>
            </div>
        </div>
    </div>
</div>
```

### 2.2 CSS for Tabs

**File**: `static/css/styles.css`

```css
/* Sidebar Tabs */
.sidebar-tabs {
    display: flex;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
}

.sidebar-tab {
    flex: 1;
    padding: 10px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-weight: 500;
    color: var(--text-muted);
    border-bottom: 2px solid transparent;
}

.sidebar-tab.active {
    color: var(--primary-color);
    border-bottom-color: var(--primary-color);
}

.sidebar-tab-content {
    display: none;
    padding: 10px;
    overflow-y: auto;
    height: calc(100% - 50px);
}

.sidebar-tab-content.active {
    display: block;
}

/* Directory Tree */
.directory-tree {
    font-size: 13px;
}

.dir-node {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 4px;
}

.dir-node:hover {
    background: var(--bg-hover);
}

.dir-node.selected {
    background: var(--primary-color-light);
}

.dir-expand {
    width: 16px;
    text-align: center;
    color: var(--text-muted);
}

.dir-name {
    margin-left: 4px;
}

.directory-actions {
    padding: 10px;
    border-top: 1px solid var(--border-color);
}
```

---

## Phase 3: Frontend - Directory Browser Logic

### 3.1 State Management

**File**: `static/js/app.js`
**Location**: Near top with other state variables

```javascript
// ADD: Browse state (alongside existing state variables)
let browseState = {
    activePath: null,       // Currently active directory
    selectedPath: null,     // Currently selected in tree (not yet activated)
    displayMode: 'direct',  // 'direct' or 'recursive'
    expandedNodes: new Set(),
    basePath: '/home/pauli/temp/AIFX013_VCR'  // Configurable
};
```

### 3.2 Tab Switching

**File**: `static/js/app.js`

```javascript
function initSidebarTabs() {
    document.querySelectorAll('.sidebar-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs and contents
            document.querySelectorAll('.sidebar-tab').forEach(t => 
                t.classList.remove('active'));
            document.querySelectorAll('.sidebar-tab-content').forEach(c => 
                c.classList.remove('active'));
            
            // Add active to clicked tab and corresponding content
            tab.classList.add('active');
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        });
    });
}
```

### 3.3 Directory Tree

**File**: `static/js/app.js`

```javascript
async function loadDirectoryTree() {
    const container = document.getElementById('directory-tree');
    container.innerHTML = '<div class="loading">Loading...</div>';
    
    try {
        const response = await fetch(
            `/api/browse/tree?path=${encodeURIComponent(browseState.basePath)}&depth=2`
        );
        const result = await response.json();
        
        if (result.success) {
            container.innerHTML = '';
            renderTreeNode(result.data, container, 0);
        }
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load</div>';
    }
}

function renderTreeNode(node, container, depth) {
    const div = document.createElement('div');
    div.className = 'dir-node';
    div.style.paddingLeft = `${depth * 16}px`;
    div.dataset.path = node.path;
    
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = browseState.expandedNodes.has(node.path);
    
    div.innerHTML = `
        <span class="dir-expand">${hasChildren ? (isExpanded ? '▼' : '▶') : ''}</span>
        <span class="dir-icon">${isExpanded ? '📂' : '📁'}</span>
        <span class="dir-name">${node.name}</span>
    `;
    
    // Click to select
    div.addEventListener('click', (e) => {
        if (e.target.classList.contains('dir-expand')) {
            toggleTreeNode(node.path);
        } else {
            selectDirectory(node.path);
        }
    });
    
    // Double-click to expand
    div.addEventListener('dblclick', () => {
        toggleTreeNode(node.path);
    });
    
    container.appendChild(div);
    
    // Render children if expanded
    if (hasChildren && isExpanded) {
        node.children.forEach(child => {
            renderTreeNode(child, container, depth + 1);
        });
    }
}

function selectDirectory(path) {
    // Update selection
    document.querySelectorAll('.dir-node').forEach(n => 
        n.classList.remove('selected'));
    document.querySelector(`.dir-node[data-path="${CSS.escape(path)}"]`)
        ?.classList.add('selected');
    
    browseState.selectedPath = path;
    
    // Enable activate button
    document.getElementById('btn-activate').disabled = false;
}

async function toggleTreeNode(path) {
    if (browseState.expandedNodes.has(path)) {
        browseState.expandedNodes.delete(path);
    } else {
        browseState.expandedNodes.add(path);
    }
    await loadDirectoryTree();
}
```

### 3.4 Activate Directory

**File**: `static/js/app.js`

```javascript
async function activateDirectory() {
    const path = browseState.selectedPath;
    if (!path) return;
    
    try {
        // Call activate endpoint
        await fetch('/api/browse/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        
        // Set active path
        browseState.activePath = path;
        
        // Update toolbar display
        updateToolbarPath();
        
        // LOAD IMAGES USING EXISTING FUNCTION
        // Just need to make loadImages() use browseState.activePath
        loadImages(1);
        
    } catch (error) {
        showNotification('Failed to activate directory', 'error');
    }
}
```

---

## Phase 4: Integration with Existing loadImages()

### 4.1 Modify loadImages()

**File**: `static/js/app.js`
**Change**: Add directory mode check at START of function

```javascript
async function loadImages(page = 1) {
    // ADD THIS AT THE START:
    if (browseState.activePath) {
        // Directory mode
        const params = new URLSearchParams({
            directory: browseState.activePath,
            mode: browseState.displayMode,
            page: page,
            per_page: getImagesPerPage()
        });
        
        // Apply existing filters
        addFilterParams(params);  // Extract filter logic to reusable function
        
        const response = await fetch(`/api/images?${params}`);
        const data = await response.json();
        
        // EXISTING RENDERING CODE - unchanged
        renderImageGrid(data.images);
        updatePagination(data);
        return;
    }
    
    // KEEP: Existing project-based loading for backwards compatibility
    ...
}
```

### 4.2 Toolbar Update

**File**: `templates/index.html`
**Change**: Replace project dropdown

```html
<!-- OLD: Project dropdown -->
<!-- <select id="project-select">...</select> -->

<!-- NEW: Directory path display -->
<div class="toolbar-directory">
    <span class="directory-path" id="current-path">No directory selected</span>
    <select id="display-mode" class="mode-select">
        <option value="direct">Direct</option>
        <option value="recursive">Recursive</option>
    </select>
    <button id="btn-refresh" class="btn-icon" title="Refresh">⟳</button>
</div>
```

### 4.3 Mode Toggle Handler

**File**: `static/js/app.js`

```javascript
function initModeToggle() {
    document.getElementById('display-mode').addEventListener('change', (e) => {
        browseState.displayMode = e.target.value;
        if (browseState.activePath) {
            loadImages(1);  // Reload with new mode
        }
    });
}

function updateToolbarPath() {
    const pathEl = document.getElementById('current-path');
    if (browseState.activePath) {
        pathEl.textContent = browseState.activePath;
    } else {
        pathEl.textContent = 'No directory selected';
    }
}
```

---

## Phase 5: Flag Storage Integration

### 5.1 Modify Flag Save

**File**: `static/js/app.js`
**Change**: Update flag save to use directory endpoint when in directory mode

```javascript
async function saveFlag(imageId, flagName, flagValue) {
    if (browseState.activePath) {
        // Directory mode - save to .dataset.json
        await fetch('/api/browse/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                directory: browseState.activePath,
                image_id: imageId,
                flag_name: flagName,
                flag_value: flagValue
            })
        });
    } else {
        // KEEP: Existing project-based flag save
        ...
    }
}
```

---

## Checklist

### Backend
- [ ] Add `/api/browse/tree` endpoint
- [ ] Add `/api/browse/activate` endpoint
- [ ] Modify `/api/images` to accept `directory` param
- [ ] Add `.dataset.json` flag storage functions
- [ ] Add `/api/browse/flag` endpoint

### Frontend HTML
- [ ] Add sidebar tabs structure
- [ ] Wrap existing filters in tab content div
- [ ] Add directories tab content
- [ ] Update toolbar (path display, mode toggle)

### Frontend CSS
- [ ] Tab header styles
- [ ] Tab content styles
- [ ] Directory tree styles
- [ ] Toolbar directory styles

### Frontend JS
- [ ] Add `browseState` object
- [ ] Tab switching logic
- [ ] Directory tree rendering
- [ ] Activate directory function
- [ ] Modify `loadImages()` start
- [ ] Mode toggle handler
- [ ] Update flag save functions
- [ ] Initialize on page load

### Testing
- [ ] Directory browsing works
- [ ] Activate creates .dataset.json
- [ ] Images load into existing grid
- [ ] Labels render correctly
- [ ] Flags save to .dataset.json
- [ ] Filters work
- [ ] Keyboard shortcuts work
- [ ] Pagination works
- [ ] Recursive mode works
