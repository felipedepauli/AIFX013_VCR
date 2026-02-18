# Phase 15: Directory Operations

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Implement directory CRUD operations: create, rename, move, and delete directories. All operations respect the base path restriction and include confirmation dialogs for destructive actions.

---

## 1. Prerequisites
- Phase 12 complete (File System Browser)
- Phase 13 complete (Dataset Activation)
- Phase 14 complete (Dataset Metadata)
- Directory tree fully functional

---

## 2. Core Concepts

### 2.1 Operations

| Operation | Description | Confirmation Required |
|-----------|-------------|----------------------|
| **Create** | New empty directory | No |
| **Rename** | Change directory name | No |
| **Move** | Move to different parent | No |
| **Delete** | Remove directory and contents | Yes (with warning) |

### 2.2 Restrictions

- Cannot operate on base path root
- Cannot move/delete directory containing active dataset
- Cannot move directory outside base path
- Delete requires confirmation dialog

---

## 3. UI Components

### 3.1 Directory Context Menu (Right-Click)

```
┌─────────────────────┐
│ 📁 New Folder       │
│ ─────────────────── │
│ ✏️ Rename           │
│ 📦 Move To...       │
│ ─────────────────── │
│ 🗑️ Delete           │
└─────────────────────┘
```

### 3.2 Action Buttons (Directory Panel)

```html
<div class="directory-actions">
    <button class="dir-action-btn activate-btn" onclick="activateDataset()" disabled>
        <span>⚡</span> Activate
    </button>
    <button class="dir-action-btn" onclick="createNewFolder()">
        <span>📁</span> New
    </button>
    <button class="dir-action-btn" onclick="renameSelectedFolder()" disabled>
        <span>✏️</span> Rename
    </button>
    <button class="dir-action-btn" onclick="moveSelectedFolder()" disabled>
        <span>📦</span> Move
    </button>
    <button class="dir-action-btn delete-btn" onclick="deleteSelectedFolder()" disabled>
        <span>🗑️</span> Delete
    </button>
</div>
```

### 3.3 Create Folder Modal

```html
<div class="modal" id="create-folder-modal">
    <div class="modal-content modal-small">
        <div class="modal-header">
            <h3>Create New Folder</h3>
            <button class="modal-close" onclick="closeModal('create-folder-modal')">×</button>
        </div>
        <div class="modal-body">
            <div class="form-field">
                <label>Parent Directory</label>
                <div class="path-display" id="create-parent-path"></div>
            </div>
            <div class="form-field">
                <label>Folder Name</label>
                <input type="text" id="new-folder-name" placeholder="Enter folder name..." autofocus>
                <div class="field-error" id="create-folder-error"></div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal('create-folder-modal')">Cancel</button>
            <button class="btn-primary" onclick="confirmCreateFolder()">Create</button>
        </div>
    </div>
</div>
```

### 3.4 Rename Folder Modal

```html
<div class="modal" id="rename-folder-modal">
    <div class="modal-content modal-small">
        <div class="modal-header">
            <h3>Rename Folder</h3>
            <button class="modal-close" onclick="closeModal('rename-folder-modal')">×</button>
        </div>
        <div class="modal-body">
            <div class="form-field">
                <label>Current Name</label>
                <div class="path-display" id="rename-current-name"></div>
            </div>
            <div class="form-field">
                <label>New Name</label>
                <input type="text" id="rename-new-name" placeholder="Enter new name..." autofocus>
                <div class="field-error" id="rename-folder-error"></div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal('rename-folder-modal')">Cancel</button>
            <button class="btn-primary" onclick="confirmRenameFolder()">Rename</button>
        </div>
    </div>
</div>
```

### 3.5 Move Folder Modal

```html
<div class="modal" id="move-folder-modal">
    <div class="modal-content modal-medium">
        <div class="modal-header">
            <h3>Move Folder</h3>
            <button class="modal-close" onclick="closeModal('move-folder-modal')">×</button>
        </div>
        <div class="modal-body">
            <div class="form-field">
                <label>Moving</label>
                <div class="path-display" id="move-source-path"></div>
            </div>
            <div class="form-field">
                <label>Select Destination</label>
                <div class="destination-tree" id="move-destination-tree">
                    <!-- Mini directory tree for selection -->
                </div>
            </div>
            <div class="form-field">
                <label>Destination</label>
                <div class="path-display" id="move-destination-path">Select a folder above</div>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal('move-folder-modal')">Cancel</button>
            <button class="btn-primary" id="move-confirm-btn" onclick="confirmMoveFolder()" disabled>Move</button>
        </div>
    </div>
</div>
```

### 3.6 Delete Confirmation Modal

```html
<div class="modal" id="delete-folder-modal">
    <div class="modal-content modal-small">
        <div class="modal-header modal-header-danger">
            <h3>⚠️ Delete Folder</h3>
            <button class="modal-close" onclick="closeModal('delete-folder-modal')">×</button>
        </div>
        <div class="modal-body">
            <div class="delete-warning">
                <p>Are you sure you want to delete this folder?</p>
                <div class="path-display path-danger" id="delete-folder-path"></div>
            </div>
            <div class="delete-stats" id="delete-stats">
                <p>This will permanently remove:</p>
                <ul>
                    <li><strong id="delete-subfolder-count">0</strong> subfolders</li>
                    <li><strong id="delete-file-count">0</strong> files</li>
                </ul>
            </div>
            <div class="delete-confirm">
                <label class="confirm-checkbox">
                    <input type="checkbox" id="delete-confirm-check" onchange="updateDeleteButton()">
                    I understand this action cannot be undone
                </label>
            </div>
        </div>
        <div class="modal-footer">
            <button class="btn-secondary" onclick="closeModal('delete-folder-modal')">Cancel</button>
            <button class="btn-danger" id="delete-confirm-btn" onclick="confirmDeleteFolder()" disabled>Delete</button>
        </div>
    </div>
</div>
```

---

## 4. CSS Styling

```css
/* Modal Styles */
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    z-index: 2000;
    align-items: center;
    justify-content: center;
}

.modal.visible {
    display: flex;
}

.modal-content {
    background: #1e1e2e;
    border-radius: 8px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    max-height: 80vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.modal-small {
    width: 400px;
}

.modal-medium {
    width: 500px;
}

.modal-header {
    padding: 16px 20px;
    background: #252536;
    border-bottom: 1px solid #333;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.modal-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 500;
}

.modal-header-danger {
    background: rgba(231, 76, 60, 0.2);
    border-bottom-color: rgba(231, 76, 60, 0.3);
}

.modal-close {
    background: none;
    border: none;
    color: #888;
    font-size: 24px;
    cursor: pointer;
    padding: 0;
    line-height: 1;
}

.modal-close:hover {
    color: #fff;
}

.modal-body {
    padding: 20px;
    overflow-y: auto;
}

.modal-footer {
    padding: 16px 20px;
    background: #252536;
    border-top: 1px solid #333;
    display: flex;
    justify-content: flex-end;
    gap: 12px;
}

/* Buttons */
.btn-primary {
    padding: 8px 16px;
    background: #4a69bd;
    border: none;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
}

.btn-primary:hover:not(:disabled) {
    background: #5a79cd;
}

.btn-primary:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

.btn-secondary {
    padding: 8px 16px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #eee;
    cursor: pointer;
    font-size: 13px;
}

.btn-secondary:hover {
    background: #444;
}

.btn-danger {
    padding: 8px 16px;
    background: #e74c3c;
    border: none;
    border-radius: 4px;
    color: #fff;
    cursor: pointer;
    font-size: 13px;
}

.btn-danger:hover:not(:disabled) {
    background: #c0392b;
}

.btn-danger:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

/* Path Display */
.path-display {
    padding: 8px 12px;
    background: #252536;
    border: 1px solid #333;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: #ccc;
    word-break: break-all;
}

.path-danger {
    border-color: rgba(231, 76, 60, 0.5);
    color: #e74c3c;
}

/* Field Error */
.field-error {
    margin-top: 4px;
    font-size: 12px;
    color: #e74c3c;
    min-height: 18px;
}

/* Delete Warning */
.delete-warning {
    margin-bottom: 16px;
}

.delete-warning p {
    margin: 0 0 12px 0;
    color: #e74c3c;
    font-weight: 500;
}

.delete-stats {
    padding: 12px;
    background: rgba(231, 76, 60, 0.1);
    border-radius: 4px;
    margin-bottom: 16px;
}

.delete-stats p {
    margin: 0 0 8px 0;
    font-size: 13px;
}

.delete-stats ul {
    margin: 0;
    padding-left: 24px;
}

.delete-stats li {
    margin: 4px 0;
    font-size: 13px;
}

/* Confirm Checkbox */
.confirm-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 13px;
}

.confirm-checkbox input {
    width: 16px;
    height: 16px;
    accent-color: #e74c3c;
}

/* Destination Tree */
.destination-tree {
    max-height: 250px;
    overflow-y: auto;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 8px;
    background: #252536;
}

.dest-node {
    padding: 6px 8px;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.dest-node:hover {
    background: rgba(255, 255, 255, 0.05);
}

.dest-node.selected {
    background: rgba(74, 105, 189, 0.3);
}

.dest-node.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Directory Action Buttons */
.directory-actions {
    padding: 12px;
    border-top: 1px solid #333;
    display: grid;
    grid-template-columns: 1fr 1fr;
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
    justify-content: center;
    gap: 6px;
}

.dir-action-btn:hover:not(:disabled) {
    background: #444;
}

.dir-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.dir-action-btn.activate-btn {
    grid-column: 1 / -1;
    background: #4a69bd;
    border-color: #5a79cd;
}

.dir-action-btn.activate-btn:hover:not(:disabled) {
    background: #5a79cd;
}

.dir-action-btn.delete-btn {
    color: #e74c3c;
    border-color: rgba(231, 76, 60, 0.3);
}

.dir-action-btn.delete-btn:hover:not(:disabled) {
    background: rgba(231, 76, 60, 0.2);
}

/* Context Menu */
.context-menu {
    position: fixed;
    background: #2a2a3a;
    border: 1px solid #444;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 3000;
    min-width: 160px;
    padding: 4px 0;
}

.context-menu-item {
    padding: 8px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
}

.context-menu-item:hover {
    background: rgba(255, 255, 255, 0.05);
}

.context-menu-item.danger {
    color: #e74c3c;
}

.context-menu-divider {
    height: 1px;
    background: #444;
    margin: 4px 0;
}
```

---

## 5. JavaScript Implementation

### 5.1 Modal Management

```javascript
function openModal(modalId) {
    document.getElementById(modalId).classList.add('visible');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('visible');
}

// Close modal on backdrop click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('visible');
        }
    });
});
```

### 5.2 Create Folder

```javascript
function createNewFolder() {
    const parentPath = filesystemState.selectedPath || filesystemState.basePath;
    
    document.getElementById('create-parent-path').textContent = parentPath;
    document.getElementById('new-folder-name').value = '';
    document.getElementById('create-folder-error').textContent = '';
    
    openModal('create-folder-modal');
    document.getElementById('new-folder-name').focus();
}

async function confirmCreateFolder() {
    const parentPath = filesystemState.selectedPath || filesystemState.basePath;
    const folderName = document.getElementById('new-folder-name').value.trim();
    
    if (!folderName) {
        document.getElementById('create-folder-error').textContent = 'Folder name is required';
        return;
    }
    
    // Validate folder name (no special characters)
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(folderName)) {
        document.getElementById('create-folder-error').textContent = 'Invalid characters in folder name';
        return;
    }
    
    try {
        const response = await fetch('/api/filesystem/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                parent: parentPath,
                name: folderName
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            document.getElementById('create-folder-error').textContent = result.error;
            return;
        }
        
        closeModal('create-folder-modal');
        
        // Refresh directory tree
        await refreshDirectoryTree();
        
        // Select new folder
        selectDirectory(result.data.path);
        
        showNotification(`Folder created: ${folderName}`, 'success');
    } catch (error) {
        document.getElementById('create-folder-error').textContent = 'Failed to create folder';
    }
}
```

### 5.3 Rename Folder

```javascript
function renameSelectedFolder() {
    const path = filesystemState.selectedPath;
    if (!path) {
        showNotification('Select a folder first', 'warning');
        return;
    }
    
    // Cannot rename base path
    if (path === filesystemState.basePath) {
        showNotification('Cannot rename root directory', 'warning');
        return;
    }
    
    const currentName = path.split('/').pop();
    
    document.getElementById('rename-current-name').textContent = currentName;
    document.getElementById('rename-new-name').value = currentName;
    document.getElementById('rename-folder-error').textContent = '';
    
    openModal('rename-folder-modal');
    document.getElementById('rename-new-name').select();
}

async function confirmRenameFolder() {
    const path = filesystemState.selectedPath;
    const newName = document.getElementById('rename-new-name').value.trim();
    
    if (!newName) {
        document.getElementById('rename-folder-error').textContent = 'Folder name is required';
        return;
    }
    
    // Validate folder name
    const invalidChars = /[<>:"/\\|?*]/;
    if (invalidChars.test(newName)) {
        document.getElementById('rename-folder-error').textContent = 'Invalid characters in folder name';
        return;
    }
    
    try {
        const response = await fetch('/api/filesystem/rename', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: path,
                new_name: newName
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            document.getElementById('rename-folder-error').textContent = result.error;
            return;
        }
        
        closeModal('rename-folder-modal');
        
        // Update selection to new path
        filesystemState.selectedPath = result.data.new_path;
        
        // Refresh tree
        await refreshDirectoryTree();
        
        // If this was active dataset, update paths
        if (datasetState.rootPath && datasetState.rootPath.includes(path)) {
            datasetState.rootPath = datasetState.rootPath.replace(path, result.data.new_path);
            datasetState.workingPath = datasetState.workingPath.replace(path, result.data.new_path);
        }
        
        showNotification(`Renamed to: ${newName}`, 'success');
    } catch (error) {
        document.getElementById('rename-folder-error').textContent = 'Failed to rename folder';
    }
}
```

### 5.4 Move Folder

```javascript
let moveState = {
    sourcePath: null,
    destinationPath: null
};

function moveSelectedFolder() {
    const path = filesystemState.selectedPath;
    if (!path) {
        showNotification('Select a folder first', 'warning');
        return;
    }
    
    // Cannot move base path
    if (path === filesystemState.basePath) {
        showNotification('Cannot move root directory', 'warning');
        return;
    }
    
    moveState.sourcePath = path;
    moveState.destinationPath = null;
    
    document.getElementById('move-source-path').textContent = path;
    document.getElementById('move-destination-path').textContent = 'Select a folder above';
    document.getElementById('move-confirm-btn').disabled = true;
    
    // Render destination tree
    renderMoveDestinationTree();
    
    openModal('move-folder-modal');
}

async function renderMoveDestinationTree() {
    const container = document.getElementById('move-destination-tree');
    
    try {
        const response = await fetch(`/api/filesystem/tree?path=${encodeURIComponent(filesystemState.basePath)}&depth=3`);
        const result = await response.json();
        
        if (!result.success) {
            container.innerHTML = '<div class="error">Failed to load directories</div>';
            return;
        }
        
        container.innerHTML = '';
        renderDestinationNode(result.data, container, 0);
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load directories</div>';
    }
}

function renderDestinationNode(node, container, depth) {
    const div = document.createElement('div');
    div.style.paddingLeft = `${depth * 16}px`;
    
    // Cannot move to self, parent, or descendant
    const isDisabled = node.path === moveState.sourcePath || 
                       moveState.sourcePath.startsWith(node.path + '/') ||
                       node.path.startsWith(moveState.sourcePath + '/');
    
    const isSelected = node.path === moveState.destinationPath;
    
    div.innerHTML = `
        <div class="dest-node ${isDisabled ? 'disabled' : ''} ${isSelected ? 'selected' : ''}"
             data-path="${node.path}"
             onclick="${isDisabled ? '' : `selectMoveDestination('${node.path}')`}">
            <span>📁</span>
            <span>${escapeHtml(node.name)}</span>
        </div>
    `;
    
    container.appendChild(div);
    
    if (node.children) {
        node.children.forEach(child => {
            renderDestinationNode(child, container, depth + 1);
        });
    }
}

function selectMoveDestination(path) {
    moveState.destinationPath = path;
    
    // Update UI
    document.querySelectorAll('.dest-node').forEach(el => {
        el.classList.remove('selected');
    });
    document.querySelector(`.dest-node[data-path="${path}"]`)?.classList.add('selected');
    
    document.getElementById('move-destination-path').textContent = path;
    document.getElementById('move-confirm-btn').disabled = false;
}

async function confirmMoveFolder() {
    if (!moveState.sourcePath || !moveState.destinationPath) {
        return;
    }
    
    try {
        const response = await fetch('/api/filesystem/move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source: moveState.sourcePath,
                destination: moveState.destinationPath
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        closeModal('move-folder-modal');
        
        // Update selection to new path
        filesystemState.selectedPath = result.data.new_path;
        
        // Refresh tree
        await refreshDirectoryTree();
        
        // If this was active dataset, update paths
        if (datasetState.rootPath && datasetState.rootPath.includes(moveState.sourcePath)) {
            datasetState.rootPath = datasetState.rootPath.replace(moveState.sourcePath, result.data.new_path);
            datasetState.workingPath = datasetState.workingPath?.replace(moveState.sourcePath, result.data.new_path);
        }
        
        showNotification('Folder moved successfully', 'success');
    } catch (error) {
        showNotification('Failed to move folder', 'error');
    }
}
```

### 5.5 Delete Folder

```javascript
let deleteState = {
    path: null,
    stats: null
};

async function deleteSelectedFolder() {
    const path = filesystemState.selectedPath;
    if (!path) {
        showNotification('Select a folder first', 'warning');
        return;
    }
    
    // Cannot delete base path
    if (path === filesystemState.basePath) {
        showNotification('Cannot delete root directory', 'warning');
        return;
    }
    
    // Cannot delete active dataset
    if (datasetState.isActive && datasetState.rootPath.startsWith(path)) {
        showNotification('Cannot delete active dataset. Deactivate first.', 'warning');
        return;
    }
    
    // Get folder stats
    try {
        const response = await fetch(`/api/filesystem/stats?path=${encodeURIComponent(path)}`);
        const result = await response.json();
        
        if (result.success) {
            deleteState.stats = result.data;
        } else {
            deleteState.stats = { subfolders: 0, files: 0 };
        }
    } catch {
        deleteState.stats = { subfolders: 0, files: 0 };
    }
    
    deleteState.path = path;
    
    // Update modal
    document.getElementById('delete-folder-path').textContent = path;
    document.getElementById('delete-subfolder-count').textContent = deleteState.stats.subfolders;
    document.getElementById('delete-file-count').textContent = deleteState.stats.files;
    document.getElementById('delete-confirm-check').checked = false;
    document.getElementById('delete-confirm-btn').disabled = true;
    
    openModal('delete-folder-modal');
}

function updateDeleteButton() {
    const checked = document.getElementById('delete-confirm-check').checked;
    document.getElementById('delete-confirm-btn').disabled = !checked;
}

async function confirmDeleteFolder() {
    if (!deleteState.path) return;
    
    try {
        const response = await fetch('/api/filesystem/delete', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: deleteState.path })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        closeModal('delete-folder-modal');
        
        // Clear selection
        filesystemState.selectedPath = null;
        
        // Refresh tree
        await refreshDirectoryTree();
        
        updateDirectoryActionButtons();
        
        showNotification('Folder deleted', 'success');
    } catch (error) {
        showNotification('Failed to delete folder', 'error');
    }
}
```

### 5.6 Action Button State

```javascript
function updateDirectoryActionButtons() {
    const selected = filesystemState.selectedPath;
    const isBasePath = selected === filesystemState.basePath;
    const isActiveDataset = datasetState.isActive && datasetState.rootPath?.startsWith(selected);
    
    // Activate button - enabled when folder selected and no dataset active
    const activateBtn = document.querySelector('.activate-btn');
    if (activateBtn) {
        activateBtn.disabled = !selected || datasetState.isActive;
    }
    
    // Rename button - enabled when folder selected (not base path)
    const renameBtn = document.querySelector('[onclick="renameSelectedFolder()"]');
    if (renameBtn) {
        renameBtn.disabled = !selected || isBasePath;
    }
    
    // Move button - enabled when folder selected (not base path)
    const moveBtn = document.querySelector('[onclick="moveSelectedFolder()"]');
    if (moveBtn) {
        moveBtn.disabled = !selected || isBasePath;
    }
    
    // Delete button - enabled when folder selected (not base path, not active dataset)
    const deleteBtn = document.querySelector('.delete-btn');
    if (deleteBtn) {
        deleteBtn.disabled = !selected || isBasePath || isActiveDataset;
    }
}
```

### 5.7 Context Menu

```javascript
let contextMenuTarget = null;

function showContextMenu(event, path) {
    event.preventDefault();
    event.stopPropagation();
    
    contextMenuTarget = path;
    
    const menu = document.getElementById('dir-context-menu');
    const isBasePath = path === filesystemState.basePath;
    const isActiveDataset = datasetState.isActive && datasetState.rootPath?.startsWith(path);
    
    // Position menu
    menu.style.left = `${event.clientX}px`;
    menu.style.top = `${event.clientY}px`;
    
    // Enable/disable items
    menu.querySelector('[data-action="rename"]').classList.toggle('disabled', isBasePath);
    menu.querySelector('[data-action="move"]').classList.toggle('disabled', isBasePath);
    menu.querySelector('[data-action="delete"]').classList.toggle('disabled', isBasePath || isActiveDataset);
    
    menu.style.display = 'block';
}

function hideContextMenu() {
    document.getElementById('dir-context-menu').style.display = 'none';
}

function handleContextAction(action) {
    hideContextMenu();
    
    // Select the target first
    selectDirectory(contextMenuTarget);
    
    switch (action) {
        case 'new':
            createNewFolder();
            break;
        case 'rename':
            renameSelectedFolder();
            break;
        case 'move':
            moveSelectedFolder();
            break;
        case 'delete':
            deleteSelectedFolder();
            break;
    }
}

// Hide context menu on click elsewhere
document.addEventListener('click', hideContextMenu);
```

---

## 6. Backend API

### 6.1 Create Directory

```python
@app.route('/api/filesystem/create', methods=['POST'])
def create_directory():
    """Create a new directory."""
    data = request.get_json()
    parent = data.get('parent')
    name = data.get('name')
    
    if not parent or not name:
        return jsonify({'success': False, 'error': 'Parent and name required'}), 400
    
    base_path = get_base_path()
    if not is_path_within_base(parent, base_path):
        return jsonify({'success': False, 'error': 'Parent outside allowed directory'}), 403
    
    # Validate name
    if not name or '/' in name or '\\' in name:
        return jsonify({'success': False, 'error': 'Invalid folder name'}), 400
    
    parent_path = Path(parent)
    new_path = parent_path / name
    
    if new_path.exists():
        return jsonify({'success': False, 'error': 'Folder already exists'}), 400
    
    try:
        new_path.mkdir(parents=False)
        return jsonify({
            'success': True,
            'data': {
                'path': str(new_path),
                'name': name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.2 Rename Directory

```python
@app.route('/api/filesystem/rename', methods=['POST'])
def rename_directory():
    """Rename a directory."""
    data = request.get_json()
    path = data.get('path')
    new_name = data.get('new_name')
    
    if not path or not new_name:
        return jsonify({'success': False, 'error': 'Path and new_name required'}), 400
    
    base_path = get_base_path()
    if not is_path_within_base(path, base_path):
        return jsonify({'success': False, 'error': 'Path outside allowed directory'}), 403
    
    # Cannot rename base path
    if str(Path(path).resolve()) == str(Path(base_path).resolve()):
        return jsonify({'success': False, 'error': 'Cannot rename root directory'}), 403
    
    old_path = Path(path)
    if not old_path.exists():
        return jsonify({'success': False, 'error': 'Directory not found'}), 404
    
    new_path = old_path.parent / new_name
    
    if new_path.exists():
        return jsonify({'success': False, 'error': 'A folder with that name already exists'}), 400
    
    try:
        old_path.rename(new_path)
        return jsonify({
            'success': True,
            'data': {
                'old_path': str(old_path),
                'new_path': str(new_path),
                'name': new_name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.3 Move Directory

```python
@app.route('/api/filesystem/move', methods=['POST'])
def move_directory():
    """Move a directory to a new parent."""
    data = request.get_json()
    source = data.get('source')
    destination = data.get('destination')
    
    if not source or not destination:
        return jsonify({'success': False, 'error': 'Source and destination required'}), 400
    
    base_path = get_base_path()
    if not is_path_within_base(source, base_path) or not is_path_within_base(destination, base_path):
        return jsonify({'success': False, 'error': 'Path outside allowed directory'}), 403
    
    source_path = Path(source)
    dest_path = Path(destination)
    
    if not source_path.exists():
        return jsonify({'success': False, 'error': 'Source not found'}), 404
    
    if not dest_path.exists() or not dest_path.is_dir():
        return jsonify({'success': False, 'error': 'Invalid destination'}), 400
    
    # Cannot move into itself or its children
    if str(dest_path).startswith(str(source_path)):
        return jsonify({'success': False, 'error': 'Cannot move folder into itself'}), 400
    
    new_path = dest_path / source_path.name
    
    if new_path.exists():
        return jsonify({'success': False, 'error': 'Folder with same name exists at destination'}), 400
    
    try:
        import shutil
        shutil.move(str(source_path), str(new_path))
        return jsonify({
            'success': True,
            'data': {
                'old_path': str(source_path),
                'new_path': str(new_path)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.4 Delete Directory

```python
@app.route('/api/filesystem/delete', methods=['DELETE'])
def delete_directory():
    """Delete a directory and its contents."""
    data = request.get_json()
    path = data.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path required'}), 400
    
    base_path = get_base_path()
    if not is_path_within_base(path, base_path):
        return jsonify({'success': False, 'error': 'Path outside allowed directory'}), 403
    
    # Cannot delete base path
    if str(Path(path).resolve()) == str(Path(base_path).resolve()):
        return jsonify({'success': False, 'error': 'Cannot delete root directory'}), 403
    
    target = Path(path)
    if not target.exists():
        return jsonify({'success': False, 'error': 'Directory not found'}), 404
    
    try:
        import shutil
        shutil.rmtree(target)
        return jsonify({
            'success': True,
            'data': {'deleted': str(target)}
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.5 Directory Stats

```python
@app.route('/api/filesystem/stats', methods=['GET'])
def get_directory_stats():
    """Get statistics for a directory."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path required'}), 400
    
    target = Path(path)
    if not target.exists():
        return jsonify({'success': False, 'error': 'Directory not found'}), 404
    
    subfolders = 0
    files = 0
    
    try:
        for item in target.rglob('*'):
            if item.is_dir():
                subfolders += 1
            else:
                files += 1
        
        return jsonify({
            'success': True,
            'data': {
                'subfolders': subfolders,
                'files': files
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 7. HTML Template Updates

### 7.1 Context Menu

```html
<!-- Directory Context Menu -->
<div class="context-menu" id="dir-context-menu" style="display: none;">
    <div class="context-menu-item" data-action="new" onclick="handleContextAction('new')">
        <span>📁</span> New Folder
    </div>
    <div class="context-menu-divider"></div>
    <div class="context-menu-item" data-action="rename" onclick="handleContextAction('rename')">
        <span>✏️</span> Rename
    </div>
    <div class="context-menu-item" data-action="move" onclick="handleContextAction('move')">
        <span>📦</span> Move To...
    </div>
    <div class="context-menu-divider"></div>
    <div class="context-menu-item danger" data-action="delete" onclick="handleContextAction('delete')">
        <span>🗑️</span> Delete
    </div>
</div>
```

### 7.2 Modals (Add to body)

Add all modal HTML from section 3.3-3.6 to the body of index.html.

---

## 8. Testing Checklist

### 8.1 Create Folder

- [ ] Click "New" button → modal opens
- [ ] Modal shows parent path
- [ ] Enter name → click Create → folder created
- [ ] Empty name → shows error
- [ ] Invalid characters → shows error
- [ ] Duplicate name → shows error
- [ ] New folder appears in tree
- [ ] New folder becomes selected

### 8.2 Rename Folder

- [ ] Select folder → click "Rename" → modal opens
- [ ] Current name pre-filled
- [ ] Change name → click Rename → folder renamed
- [ ] Tree updates with new name
- [ ] Cannot rename base path (button disabled)
- [ ] Duplicate name → shows error

### 8.3 Move Folder

- [ ] Select folder → click "Move" → modal opens
- [ ] Source path displayed
- [ ] Destination tree shows all folders
- [ ] Cannot select source folder as destination
- [ ] Cannot select descendant as destination
- [ ] Select valid destination → Enable Move button
- [ ] Click Move → folder moved
- [ ] Tree updates correctly
- [ ] Cannot move base path

### 8.4 Delete Folder

- [ ] Select folder → click "Delete" → confirmation modal opens
- [ ] Shows folder path
- [ ] Shows subfolder and file counts
- [ ] Checkbox unchecked → Delete button disabled
- [ ] Check checkbox → Delete button enabled
- [ ] Click Delete → folder deleted
- [ ] Tree updates (folder removed)
- [ ] Cannot delete base path
- [ ] Cannot delete folder containing active dataset

### 8.5 Context Menu

- [ ] Right-click folder → context menu appears
- [ ] Menu positioned at click location
- [ ] Click elsewhere → menu closes
- [ ] Click item → executes action
- [ ] Appropriate items disabled for base path

### 8.6 Action Button States

- [ ] No selection → all buttons disabled (except New)
- [ ] Select folder → Rename, Move, Delete enabled
- [ ] Select base path → only New enabled
- [ ] Active dataset folder → Delete disabled

### 8.7 Dataset Integration

- [ ] Move/rename active dataset folder → paths update correctly
- [ ] Delete parent of working dir → handled gracefully

---

## 9. Files Changed Summary

| File | Changes |
|------|---------|
| `app.py` | Add create, rename, move, delete, stats endpoints |
| `static/js/app.js` | Add modal management, CRUD functions, context menu |
| `static/css/styles.css` | Add modal, context menu, button state styles |
| `templates/index.html` | Add modals, context menu HTML |

---

## 10. Security Considerations

- All operations validate paths are within base path
- Delete requires explicit confirmation
- Cannot delete active dataset directory
- Invalid characters rejected in names
- Duplicate names handled gracefully

---

## 11. Implementation Order

1. **Backend API** - Create all filesystem endpoints
2. **Modal CSS** - Add all modal styling
3. **Modal HTML** - Add modal templates
4. **Modal JS** - Implement modal management
5. **Create Folder** - Implement create flow
6. **Rename Folder** - Implement rename flow
7. **Move Folder** - Implement move flow with destination tree
8. **Delete Folder** - Implement delete with confirmation
9. **Context Menu** - Add right-click menu
10. **Button States** - Implement state management
11. **Testing** - Manual tests per checklist
