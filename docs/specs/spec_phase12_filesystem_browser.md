# Phase 12: File System Browser

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Replace the project-centric model with a file system browser. The left panel transforms from a filter panel to a directory tree for navigating datasets. Grid remains empty until a dataset is activated (Phase 13).

---

## 1. Prerequisites
- Phase 1-11 complete
- Existing filter panel implementation to reference
- Understanding of current project loading flow

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Base Path** | Root directory restriction (user cannot navigate above this) |
| **Directory Tree** | Hierarchical folder view in left panel |
| **Selected Directory** | Currently highlighted folder (single-click) |
| **Working Directory** | Directory whose contents are shown (after activation) |
| **Dataset Root** | Directory activated as dataset (Phase 13) |

### 2.2 State Model

```javascript
const filesystemState = {
    basePath: '/home/pauli/pdi_datasets',     // Configurable root
    currentPath: '/home/pauli/pdi_datasets',  // Currently viewing
    selectedPath: null,                        // Highlighted in tree
    expandedNodes: new Set(),                  // Expanded folders
    recentDatasets: []                         // Last 10 datasets
};
```

---

## 3. UI Components

### 3.1 Left Panel Transformation

**Before (Filter Panel):**
```
┌────────────────────┐
│ ◀ FILTERS          │
│                    │
│ ▼ Quality Flags    │
│   ☑ ok       (25)  │
│   ☐ review   (12)  │
│                    │
│ ▼ Color            │
│   ☑ white    (42)  │
└────────────────────┘
```

**After (Directory Browser):**
```
┌────────────────────┐
│ ◀ DIRECTORIES      │
│                    │
│ 📁 pdi_datasets    │
│  ├📁 vehicle_v4/   │
│  │  ├📁 train/     │
│  │  ├📁 test/      │
│  │  └📁 valid/     │
│  ├📁 colors_v2/    │
│  └📁 brands_v1/    │
│                    │
│ ─────────────────  │
│ [+ New Folder]     │
│ [🗑️ Delete]        │
│ [📦 Move]          │
└────────────────────┘
```

### 3.2 Directory Tree Node

```html
<div class="dir-node" data-path="/path/to/folder">
    <span class="dir-expand" onclick="toggleExpand(this)">▶</span>
    <span class="dir-icon">📁</span>
    <span class="dir-name" onclick="selectDir(this)" ondblclick="navigateInto(this)">
        folder_name
    </span>
</div>
<div class="dir-children collapsed">
    <!-- Nested nodes -->
</div>
```

### 3.3 Directory Node States

| State | Visual | Behavior |
|-------|--------|----------|
| Default | `📁 folder_name` | Normal folder |
| Selected | `📁 folder_name` (highlighted bg) | Single-clicked |
| Expanded | `▼ 📂 folder_name` | Children visible |
| Collapsed | `▶ 📁 folder_name` | Children hidden |
| Dataset Root | `📁 folder_name` (accent border) | Active dataset (Phase 13) |

---

## 4. CSS Styling

```css
/* Directory Browser Panel */
.directory-panel {
    width: 280px;
    background: #1e1e2e;
    border-right: 1px solid #333;
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
}

.directory-panel.collapsed {
    width: 0;
    overflow: hidden;
}

.directory-panel-header {
    padding: 12px 16px;
    background: #252536;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #333;
}

.directory-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
}

/* Directory Tree */
.dir-tree {
    font-size: 13px;
}

.dir-node {
    display: flex;
    align-items: center;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 4px;
    margin: 1px 0;
}

.dir-node:hover {
    background: rgba(255, 255, 255, 0.05);
}

.dir-node.selected {
    background: rgba(74, 105, 189, 0.3);
    border: 1px solid rgba(74, 105, 189, 0.5);
}

.dir-expand {
    width: 16px;
    text-align: center;
    color: #888;
    font-size: 10px;
    cursor: pointer;
}

.dir-expand:hover {
    color: #fff;
}

.dir-expand.empty {
    visibility: hidden;
}

.dir-icon {
    margin: 0 6px;
    font-size: 14px;
}

.dir-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.dir-children {
    margin-left: 20px;
}

.dir-children.collapsed {
    display: none;
}

/* Directory Actions */
.directory-actions {
    padding: 12px;
    border-top: 1px solid #333;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.dir-action-btn {
    padding: 8px 12px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #eee;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.dir-action-btn:hover {
    background: #444;
}

.dir-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

---

## 5. JavaScript Implementation

### 5.1 State Management

```javascript
// File system state
const filesystemState = {
    basePath: null,
    currentPath: null,
    selectedPath: null,
    expandedNodes: new Set(),
    recentDatasets: [],
    directoryCache: new Map()  // Cache directory listings
};

// Initialize from localStorage
function initFilesystemState() {
    const saved = localStorage.getItem('filesystem_state');
    if (saved) {
        const data = JSON.parse(saved);
        filesystemState.basePath = data.basePath;
        filesystemState.recentDatasets = data.recentDatasets || [];
        filesystemState.expandedNodes = new Set(data.expandedNodes || []);
    }
}

// Save to localStorage
function saveFilesystemState() {
    localStorage.setItem('filesystem_state', JSON.stringify({
        basePath: filesystemState.basePath,
        recentDatasets: filesystemState.recentDatasets,
        expandedNodes: Array.from(filesystemState.expandedNodes)
    }));
}
```

### 5.2 Directory Tree Rendering

```javascript
async function loadDirectoryTree(path) {
    try {
        const response = await fetch(`/api/filesystem/tree?path=${encodeURIComponent(path)}`);
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        renderDirectoryTree(result.data);
    } catch (error) {
        console.error('Failed to load directory tree:', error);
        showNotification('Failed to load directories', 'error');
    }
}

function renderDirectoryTree(tree) {
    const container = document.getElementById('directory-tree');
    container.innerHTML = '';
    
    function renderNode(node, depth = 0) {
        const div = document.createElement('div');
        div.className = 'dir-node-wrapper';
        div.style.marginLeft = `${depth * 20}px`;
        
        const isExpanded = filesystemState.expandedNodes.has(node.path);
        const isSelected = filesystemState.selectedPath === node.path;
        const hasChildren = node.children && node.children.length > 0;
        
        div.innerHTML = `
            <div class="dir-node ${isSelected ? 'selected' : ''}" data-path="${node.path}">
                <span class="dir-expand ${hasChildren ? '' : 'empty'}" 
                      onclick="toggleDirExpand(event, '${node.path}')">
                    ${hasChildren ? (isExpanded ? '▼' : '▶') : ''}
                </span>
                <span class="dir-icon">${isExpanded ? '📂' : '📁'}</span>
                <span class="dir-name" 
                      onclick="selectDirectory('${node.path}')"
                      ondblclick="navigateIntoDirectory('${node.path}')">
                    ${escapeHtml(node.name)}
                </span>
            </div>
            <div class="dir-children ${isExpanded ? '' : 'collapsed'}">
            </div>
        `;
        
        container.appendChild(div);
        
        // Render children if expanded
        if (isExpanded && node.children) {
            const childContainer = div.querySelector('.dir-children');
            node.children.forEach(child => {
                const childEl = renderNode(child, depth + 1);
                childContainer.appendChild(childEl);
            });
        }
        
        return div;
    }
    
    renderNode(tree);
}
```

### 5.3 Directory Navigation

```javascript
function selectDirectory(path) {
    // Update selection
    document.querySelectorAll('.dir-node.selected').forEach(el => {
        el.classList.remove('selected');
    });
    
    const node = document.querySelector(`.dir-node[data-path="${path}"]`);
    if (node) {
        node.classList.add('selected');
    }
    
    filesystemState.selectedPath = path;
    
    // Update action buttons
    updateDirectoryActionButtons();
}

function navigateIntoDirectory(path) {
    // Expand the node if not already
    if (!filesystemState.expandedNodes.has(path)) {
        toggleDirExpand(null, path);
    }
    
    // If dataset is active, this changes working directory (Phase 13)
    if (datasetState.isActive) {
        changeWorkingDirectory(path);
    }
}

function toggleDirExpand(event, path) {
    if (event) event.stopPropagation();
    
    if (filesystemState.expandedNodes.has(path)) {
        filesystemState.expandedNodes.delete(path);
    } else {
        filesystemState.expandedNodes.add(path);
        // Load children if not cached
        loadDirectoryChildren(path);
    }
    
    saveFilesystemState();
    refreshDirectoryTree();
}

async function loadDirectoryChildren(path) {
    if (filesystemState.directoryCache.has(path)) {
        return filesystemState.directoryCache.get(path);
    }
    
    try {
        const response = await fetch(`/api/filesystem/browse?path=${encodeURIComponent(path)}`);
        const result = await response.json();
        
        if (result.success) {
            filesystemState.directoryCache.set(path, result.data.directories);
            return result.data.directories;
        }
    } catch (error) {
        console.error('Failed to load directory:', error);
    }
    
    return [];
}
```

### 5.4 Recent Datasets

```javascript
function addToRecentDatasets(path, name) {
    // Remove if already exists
    filesystemState.recentDatasets = filesystemState.recentDatasets.filter(d => d.path !== path);
    
    // Add to beginning
    filesystemState.recentDatasets.unshift({ path, name, timestamp: Date.now() });
    
    // Keep only last 10
    filesystemState.recentDatasets = filesystemState.recentDatasets.slice(0, 10);
    
    saveFilesystemState();
    renderRecentDatasets();
}

function renderRecentDatasets() {
    const container = document.getElementById('recent-datasets');
    if (!container) return;
    
    if (filesystemState.recentDatasets.length === 0) {
        container.innerHTML = '<div class="no-recent">No recent datasets</div>';
        return;
    }
    
    container.innerHTML = filesystemState.recentDatasets.map(ds => `
        <div class="recent-dataset" onclick="openRecentDataset('${ds.path}')">
            <span class="recent-icon">📁</span>
            <span class="recent-name">${escapeHtml(ds.name)}</span>
            <span class="recent-path">${escapeHtml(ds.path)}</span>
        </div>
    `).join('');
}
```

---

## 6. Backend API

### 6.1 Browse Directory

```python
@app.route('/api/filesystem/browse', methods=['GET'])
def browse_directory():
    """Get contents of a directory (subdirectories only)."""
    path = request.args.get('path', '')
    
    # Validate path is within base path
    base_path = get_base_path()
    if not is_path_within_base(path, base_path):
        return jsonify({'success': False, 'error': 'Path outside allowed directory'}), 403
    
    target = Path(path)
    if not target.exists():
        return jsonify({'success': False, 'error': 'Directory not found'}), 404
    
    if not target.is_dir():
        return jsonify({'success': False, 'error': 'Not a directory'}), 400
    
    # Get subdirectories only
    directories = []
    try:
        for item in sorted(target.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                directories.append({
                    'name': item.name,
                    'path': str(item),
                    'has_children': any(p.is_dir() for p in item.iterdir() if not p.name.startswith('.'))
                })
    except PermissionError:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    
    return jsonify({
        'success': True,
        'data': {
            'path': str(target),
            'name': target.name,
            'directories': directories
        }
    })
```

### 6.2 Get Directory Tree

```python
@app.route('/api/filesystem/tree', methods=['GET'])
def get_directory_tree():
    """Get full directory tree from path (limited depth)."""
    path = request.args.get('path', '')
    max_depth = request.args.get('depth', 2, type=int)
    
    base_path = get_base_path()
    if not is_path_within_base(path, base_path):
        return jsonify({'success': False, 'error': 'Path outside allowed directory'}), 403
    
    target = Path(path) if path else Path(base_path)
    
    def build_tree(dir_path, depth=0):
        if depth > max_depth:
            return None
        
        try:
            children = []
            for item in sorted(dir_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    child_tree = build_tree(item, depth + 1) if depth < max_depth else None
                    children.append({
                        'name': item.name,
                        'path': str(item),
                        'children': child_tree.get('children', []) if child_tree else [],
                        'has_children': any(p.is_dir() for p in item.iterdir() if not p.name.startswith('.'))
                    })
            
            return {
                'name': dir_path.name or str(dir_path),
                'path': str(dir_path),
                'children': children
            }
        except PermissionError:
            return {'name': dir_path.name, 'path': str(dir_path), 'children': [], 'error': 'Permission denied'}
    
    tree = build_tree(target)
    
    return jsonify({
        'success': True,
        'data': tree
    })
```

### 6.3 Base Path Configuration

```python
# Global configuration
APP_CONFIG = {
    'base_path': None  # Set on startup or via API
}

def get_base_path():
    """Get configured base path."""
    return APP_CONFIG.get('base_path') or str(Path.home())

def is_path_within_base(path, base_path):
    """Check if path is within base path."""
    try:
        path = Path(path).resolve()
        base = Path(base_path).resolve()
        return str(path).startswith(str(base))
    except:
        return False

@app.route('/api/config/base_path', methods=['GET'])
def get_base_path_config():
    """Get current base path."""
    return jsonify({
        'success': True,
        'data': {'base_path': get_base_path()}
    })

@app.route('/api/config/base_path', methods=['POST'])
def set_base_path_config():
    """Set base path."""
    data = request.get_json()
    path = data.get('base_path')
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'}), 400
    
    APP_CONFIG['base_path'] = str(target.resolve())
    
    return jsonify({
        'success': True,
        'data': {'base_path': APP_CONFIG['base_path']}
    })
```

### 6.4 Recent Datasets

```python
@app.route('/api/recent_datasets', methods=['GET'])
def get_recent_datasets():
    """Get list of recent datasets (from localStorage via frontend)."""
    # Note: Recent datasets are stored in browser localStorage
    # This endpoint is for server-side tracking if needed
    return jsonify({
        'success': True,
        'data': {'recent': []}  # Placeholder - managed by frontend
    })
```

---

## 7. HTML Template Updates

### 7.1 Replace Filter Panel with Directory Panel

```html
<!-- Directory Browser Panel (Left Sidebar) -->
<aside id="directory-panel" class="directory-panel">
    <div class="directory-panel-header">
        <button class="panel-collapse-btn" onclick="toggleDirectoryPanel()" title="Collapse">
            <span class="toggle-icon" id="dir-panel-toggle-icon">◀</span>
        </button>
        <span class="panel-title">DIRECTORIES</span>
    </div>
    
    <div class="directory-panel-content">
        <!-- Recent Datasets Section -->
        <div class="panel-section recent-section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="section-icon">🕐</span>
                <span class="section-title">Recent Datasets</span>
                <span class="section-toggle">▼</span>
            </div>
            <div class="section-content" id="recent-datasets">
                <!-- Recent datasets injected here -->
            </div>
        </div>
        
        <!-- Directory Tree Section -->
        <div class="panel-section tree-section">
            <div class="section-header">
                <span class="section-icon">📂</span>
                <span class="section-title">Browse</span>
            </div>
            <div class="section-content" id="directory-tree">
                <!-- Directory tree injected here -->
            </div>
        </div>
    </div>
    
    <!-- Directory Actions -->
    <div class="directory-actions" id="directory-actions">
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
</aside>
```

---

## 8. Initialization Flow

### 8.1 App Startup

```javascript
async function initApp() {
    // 1. Load filesystem state from localStorage
    initFilesystemState();
    
    // 2. Check if base path is configured
    if (!filesystemState.basePath) {
        // Show base path configuration modal
        openBasePathModal();
        return;
    }
    
    // 3. Load directory tree from base path
    await loadDirectoryTree(filesystemState.basePath);
    
    // 4. Render recent datasets
    renderRecentDatasets();
    
    // 5. Grid stays empty until dataset activated
    showEmptyGridMessage('Select a directory and click "Activate Dataset" to begin');
}

function showEmptyGridMessage(message) {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = `
        <div class="empty-grid-message">
            <span class="empty-icon">📁</span>
            <p>${message}</p>
        </div>
    `;
}
```

### 8.2 Base Path Modal

```javascript
function openBasePathModal() {
    const modal = document.getElementById('base-path-modal');
    modal.classList.remove('hidden');
}

async function setBasePath() {
    const input = document.getElementById('base-path-input');
    const path = input.value.trim();
    
    if (!path) {
        showNotification('Please enter a path', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/config/base_path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ base_path: path })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        filesystemState.basePath = result.data.base_path;
        saveFilesystemState();
        
        closeBasePathModal();
        await loadDirectoryTree(filesystemState.basePath);
        
        showNotification('Base path configured', 'success');
    } catch (error) {
        showNotification('Failed to set base path', 'error');
    }
}
```

---

## 9. Testing Checklist

### 9.1 Directory Tree Display

- [ ] Launch app → left panel shows directory browser (not filters)
- [ ] Base path modal appears if not configured
- [ ] Set base path → tree loads from that directory
- [ ] Only directories shown (no files)
- [ ] Hidden folders (starting with .) are excluded

### 9.2 Tree Navigation

- [ ] Click expand arrow (▶) → folder expands, shows children
- [ ] Click again → folder collapses
- [ ] Single-click folder name → folder is selected (highlighted)
- [ ] Double-click folder → expands and navigates into

### 9.3 Selection State

- [ ] Only one folder can be selected at a time
- [ ] Selection persists when expanding/collapsing other folders
- [ ] Selected folder has visual highlight

### 9.4 Action Buttons

- [ ] "New Folder" button always enabled
- [ ] "Delete" and "Move" buttons disabled until folder selected
- [ ] After selecting folder → buttons become enabled

### 9.5 Recent Datasets

- [ ] Recent datasets section shows "No recent datasets" initially
- [ ] (After Phase 13) Activated datasets appear in recent list
- [ ] Click recent dataset → loads that directory

### 9.6 Panel Collapse

- [ ] Click collapse button (◀) → panel collapses
- [ ] Click again → panel expands
- [ ] State persists across page refresh

### 9.7 Grid State

- [ ] Grid shows empty message until dataset activated
- [ ] Message instructs: "Select directory and click Activate"

---

## 10. Files Changed Summary

| File | Changes |
|------|---------|
| `app.py` | Add filesystem browse/tree endpoints, base path config |
| `static/js/app.js` | Add filesystemState, tree rendering, navigation functions |
| `static/css/styles.css` | Add directory panel styles, tree node styles |
| `templates/index.html` | Replace filter panel with directory panel |

---

## 11. Migration Notes

### 11.1 Backward Compatibility

- Filter panel functionality will be preserved but moved (can be accessed via toolbar)
- Existing project JSON files remain valid
- New `.dataset.json` format introduced in Phase 13

### 11.2 Breaking Changes

- Left panel changes from filters to directories
- App no longer shows images on startup
- Project loading removed (replaced by dataset activation in Phase 13)

---

## 12. Implementation Order

1. **Backend API** - Add filesystem endpoints
2. **State Management** - Add filesystemState, localStorage persistence
3. **HTML Update** - Replace filter panel with directory panel
4. **CSS Styling** - Add directory tree styles
5. **Tree Rendering** - Implement directory tree display
6. **Navigation** - Add select/expand/collapse logic
7. **Base Path** - Add configuration modal and validation
8. **Recent Datasets** - Add recent list (populated in Phase 13)
9. **Action Buttons** - Wire up buttons (functionality in Phase 15)
10. **Testing** - Manual tests per checklist
