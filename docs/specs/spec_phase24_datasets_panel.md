# Phase 24: Datasets Left Panel & Registration

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/js/app.js`, `static/css/styles.css`, `templates/index.html`

**PRD Reference:** FR-17.1 (Left Panel — Datasets Tab), FR-17.4 (Dataset Registration Flow)

---

## Objective
Rename the left panel "Directories" tab to **Datasets**. Add a "Registered Datasets" section at the top listing all datasets from MongoDB. Add **[+ Add Current]** and **[📊 Dashboard]** buttons. Remove the **"Recent"** button from the top-right toolbar. Implement the dataset registration flow.

---

## 1. Prerequisites
- Phase 23 complete (MongoDB Backend & API endpoints)
- Phase 13 complete (Dataset Activation with `.dataset.json`)

---

## 2. Core Concepts

### 2.1 Panel Layout

The left panel currently has two tabs: **Directories** and **Filters**. This phase:
1. Renames "Directories" to **Datasets**
2. Splits the tab content into two sections:
   - **Top:** Registered Datasets (from MongoDB)
   - **Bottom:** Browse Directories (existing file tree)

```
┌─────────────────────────┐
│ [Datasets] [Filters]    │
├─────────────────────────┤
│                         │
│ ▼ Registered (3)        │
│   🟢 vehicle_v4         │
│   🟡 night_v2           │
│   🔴 closeup_v3         │
│                         │
│ [+ Add Current]         │
│ [📊 Dashboard]          │
│                         │
│ ─────────────────────── │
│ ▼ Browse Directories    │
│                         │
│ 📁 pdi_datasets         │
│  ├📁 train/             │
│  ├📁 test/              │
│  └📁 valid/             │
│                         │
│ [🔄 Activate]           │
└─────────────────────────┘
```

### 2.2 Status Indicators

| Indicator | Verdict | CSS Color |
|-----------|---------|-----------|
| 🟢 | keep | `#4caf50` |
| 🟡 | revise | `#ff9800` |
| 🔴 | remove | `#f44336` |
| ⚪ | none / not reviewed | `#9e9e9e` |

---

## 3. HTML Changes (index.html)

### 3.1 Rename Tab

```html
<!-- BEFORE -->
<button class="tab-btn active" data-tab="directories">Directories</button>

<!-- AFTER -->
<button class="tab-btn active" data-tab="datasets">Datasets</button>
```

### 3.2 New Panel Content

```html
<div id="datasets-tab" class="tab-content active">
    <!-- Section 1: Registered Datasets -->
    <div class="panel-section registered-datasets-section">
        <div class="section-header" onclick="toggleSection('registered-datasets')">
            <span class="section-toggle">▼</span>
            <span>Registered (<span id="registered-count">0</span>)</span>
        </div>
        <div id="registered-datasets-list" class="section-body">
            <!-- Populated dynamically by JS -->
            <div class="empty-state" id="no-datasets-msg">
                No datasets registered yet.<br>
                Activate a dataset and click "+ Add Current".
            </div>
        </div>
        <div class="registered-datasets-actions">
            <button id="btn-add-current-dataset" class="btn btn-sm btn-primary" 
                    onclick="addCurrentDataset()" disabled
                    title="Register the currently activated dataset">
                + Add Current
            </button>
            <button id="btn-open-dashboard" class="btn btn-sm btn-secondary"
                    onclick="openDashboardModal()"
                    title="Open Datasets Dashboard">
                📊 Dashboard
            </button>
        </div>
    </div>

    <!-- Separator -->
    <hr class="panel-divider">

    <!-- Section 2: Browse Directories (existing content, moved here) -->
    <div class="panel-section browse-directories-section">
        <div class="section-header" onclick="toggleSection('browse-directories')">
            <span class="section-toggle">▼</span>
            <span>Browse Directories</span>
        </div>
        <div id="browse-directories-content" class="section-body">
            <!-- Existing directory tree content moved here -->
        </div>
    </div>
</div>
```

### 3.3 Remove "Recent" Button

Remove from the top-right toolbar:
```html
<!-- DELETE this element -->
<button id="btn-recent" class="toolbar-btn" title="Recent datasets">
    📋 Recent
</button>
```

---

## 4. CSS Changes (styles.css)

### 4.1 Registered Datasets List

```css
/* Registered datasets list */
.registered-datasets-section {
    padding: 8px;
}

.registered-datasets-list {
    max-height: 200px;
    overflow-y: auto;
}

.registered-dataset-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.15s;
    font-size: 13px;
}

.registered-dataset-item:hover {
    background-color: rgba(255, 255, 255, 0.08);
}

.registered-dataset-item.active {
    background-color: rgba(66, 165, 245, 0.15);
    border-left: 3px solid #42a5f5;
}

/* Status dot */
.dataset-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dataset-status-dot.keep { background-color: #4caf50; }
.dataset-status-dot.revise { background-color: #ff9800; }
.dataset-status-dot.remove { background-color: #f44336; }
.dataset-status-dot.none { background-color: #9e9e9e; }

/* Dataset info in list */
.dataset-item-info {
    flex: 1;
    min-width: 0;
    overflow: hidden;
}

.dataset-item-name {
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dataset-item-path {
    font-size: 11px;
    color: #888;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Action buttons */
.registered-datasets-actions {
    display: flex;
    gap: 6px;
    padding: 8px;
}

.registered-datasets-actions .btn {
    flex: 1;
    font-size: 12px;
    padding: 5px 8px;
}

/* Panel divider */
.panel-divider {
    margin: 4px 8px;
    border: none;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Disabled state for MongoDB unavailable */
.btn.mongo-disabled {
    opacity: 0.4;
    cursor: not-allowed;
    pointer-events: none;
}
```

---

## 5. JavaScript Changes (app.js)

### 5.1 State

```javascript
// Add to global state
let registeredDatasets = [];
let mongoAvailable = false;
```

### 5.2 Initialize on App Load

```javascript
async function initDatasetsPanel() {
    // Check MongoDB status
    try {
        const resp = await fetch('/api/datasets/status');
        const data = await resp.json();
        mongoAvailable = data.mongodb_available;
    } catch (e) {
        mongoAvailable = false;
    }

    if (!mongoAvailable) {
        document.getElementById('btn-add-current-dataset').classList.add('mongo-disabled');
        document.getElementById('btn-open-dashboard').classList.add('mongo-disabled');
        document.getElementById('no-datasets-msg').textContent = 
            'MongoDB not available. Start mongod and restart.';
        return;
    }

    await loadRegisteredDatasets();
}
```

### 5.3 Load Registered Datasets

```javascript
async function loadRegisteredDatasets() {
    if (!mongoAvailable) return;

    try {
        const resp = await fetch('/api/datasets');
        const data = await resp.json();
        registeredDatasets = data.datasets || [];
        renderRegisteredDatasets();
    } catch (e) {
        console.error('Failed to load datasets:', e);
    }
}

function renderRegisteredDatasets() {
    const list = document.getElementById('registered-datasets-list');
    const countEl = document.getElementById('registered-count');
    const emptyMsg = document.getElementById('no-datasets-msg');

    countEl.textContent = registeredDatasets.length;

    if (registeredDatasets.length === 0) {
        emptyMsg.style.display = 'block';
        // Clear any previous items
        list.querySelectorAll('.registered-dataset-item').forEach(el => el.remove());
        return;
    }

    emptyMsg.style.display = 'none';

    // Clear and re-render
    list.querySelectorAll('.registered-dataset-item').forEach(el => el.remove());

    registeredDatasets.forEach(ds => {
        const verdict = ds.metadata?.verdict || 'none';
        const totalImages = ds.statistics?.total_images || 0;

        const item = document.createElement('div');
        item.className = 'registered-dataset-item';
        item.dataset.id = ds.id;
        item.dataset.rootPath = ds.root_path;

        // Highlight if this is the currently active dataset
        if (browseState?.datasetRoot === ds.root_path) {
            item.classList.add('active');
        }

        item.innerHTML = `
            <span class="dataset-status-dot ${verdict}"></span>
            <div class="dataset-item-info">
                <div class="dataset-item-name">${escapeHtml(ds.name)}</div>
                <div class="dataset-item-path" title="${escapeHtml(ds.root_path)}">
                    ${escapeHtml(ds.root_path)}
                </div>
            </div>
            <span class="dataset-item-count">${totalImages}</span>
        `;

        // Click to open/activate
        item.addEventListener('click', () => openRegisteredDataset(ds));

        // Check if path exists
        if (!ds.path_exists) {
            item.classList.add('path-not-found');
            item.title = 'Path not found on disk';
        }

        list.appendChild(item);
    });
}
```

### 5.4 Open Registered Dataset

```javascript
async function openRegisteredDataset(dataset) {
    if (!dataset.path_exists) {
        showToast('Dataset path not found: ' + dataset.root_path, 'error');
        return;
    }

    // Navigate to the dataset root in the directory tree
    // Then activate it (reuses existing browse-mode activation logic)
    await navigateToDirectory(dataset.root_path);
    await activateDataset(dataset.root_path);

    // Highlight the active item
    renderRegisteredDatasets();
}
```

### 5.5 Add Current Dataset

```javascript
async function addCurrentDataset() {
    if (!mongoAvailable) {
        showToast('MongoDB not available', 'warning');
        return;
    }

    if (!browseState?.datasetRoot) {
        showToast('No dataset is currently activated. Activate one first.', 'warning');
        return;
    }

    const rootPath = browseState.datasetRoot;

    try {
        const resp = await fetch('/api/datasets', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ root_path: rootPath })
        });

        if (resp.status === 409) {
            const data = await resp.json();
            showToast('Dataset already registered', 'info');
            return;
        }

        if (!resp.ok) {
            const data = await resp.json();
            showToast(data.message || 'Failed to register dataset', 'error');
            return;
        }

        showToast('Dataset registered successfully!', 'success');
        await loadRegisteredDatasets();
    } catch (e) {
        showToast('Error registering dataset: ' + e.message, 'error');
    }
}
```

### 5.6 Enable/Disable "Add Current" Button

```javascript
// Call this whenever dataset activation state changes
function updateAddCurrentButton() {
    const btn = document.getElementById('btn-add-current-dataset');
    if (!btn) return;

    const hasActiveDataset = !!browseState?.datasetRoot;
    btn.disabled = !hasActiveDataset || !mongoAvailable;

    if (!mongoAvailable) {
        btn.title = 'MongoDB not available';
    } else if (!hasActiveDataset) {
        btn.title = 'Activate a dataset first';
    } else {
        btn.title = `Register "${browseState.datasetRoot}" to Dashboard`;
    }
}
```

---

## 6. Registration Flow (Server Side)

### 6.1 `POST /api/datasets` Implementation

```python
@app.route('/api/datasets', methods=['POST'])
@requires_mongodb
def register_dataset():
    data = request.get_json()
    root_path = data.get('root_path', '').rstrip('/')
    
    # Validate
    if not root_path or not os.path.isdir(root_path):
        return jsonify({'error': 'Invalid path', 'message': 'Directory does not exist'}), 400
    
    # Check duplicate
    existing = datasets_collection.find_one({'root_path': root_path})
    if existing:
        return jsonify({
            'error': 'duplicate',
            'message': 'Dataset already registered',
            'existing_id': str(existing['_id'])
        }), 409
    
    # Read .dataset.json for metadata
    dataset_json_path = os.path.join(root_path, '.dataset.json')
    metadata = {
        'description': '',
        'camera_view': [],
        'quality': '',
        'verdict': '',
        'cycle': '',
        'notes': '',
        'model_compatibility': []
    }
    name = os.path.basename(root_path)
    
    if os.path.exists(dataset_json_path):
        try:
            with open(dataset_json_path, 'r') as f:
                ds_data = json.load(f)
            name = ds_data.get('name', name)
            ds_meta = ds_data.get('metadata', {})
            for key in metadata:
                if key in ds_meta:
                    metadata[key] = ds_meta[key]
        except Exception:
            pass
    
    # Compute statistics
    statistics = _compute_dataset_statistics(root_path)
    
    # Generate unique ID first (for thumbnail naming)
    from bson import ObjectId
    doc_id = ObjectId()
    
    # Generate thumbnails
    thumbnail_paths = _generate_dataset_thumbnails(root_path, str(doc_id))
    
    # Insert
    now = datetime.utcnow()
    document = {
        '_id': doc_id,
        'name': name,
        'root_path': root_path,
        'registered_at': now,
        'updated_at': now,
        'metadata': metadata,
        'statistics': statistics,
        'thumbnails': {
            'paths': thumbnail_paths,
            'generated_at': now
        }
    }
    
    datasets_collection.insert_one(document)
    
    return jsonify({
        'id': str(doc_id),
        'name': name,
        'root_path': root_path,
        'message': 'Dataset registered successfully'
    }), 201
```

---

## 7. Integration Points

### 7.1 On Dataset Activate/Deactivate
- Call `updateAddCurrentButton()` after `activateDataset()` and `deactivateDataset()`
- Call `renderRegisteredDatasets()` to update active highlight

### 7.2 On App Startup
- Call `initDatasetsPanel()` in the main initialization flow
- Load registered datasets before rendering the panel

### 7.3 Remove "Recent" Logic
- Remove `loadRecentDatasets()` function and related code
- Remove "Recent" button click handler
- Remove recent datasets dropdown/modal
- Clean up `recentDatasets` state variable if present

---

## 8. Testing Checklist

### 8.1 Tab Rename
- [ ] Left panel tab now reads "Datasets" instead of "Directories"
- [ ] Tab switching still works between Datasets ↔ Filters

### 8.2 Registered Datasets Section
- [ ] Shows "No datasets registered yet" when empty
- [ ] After registering, shows dataset with name, path, status dot
- [ ] Click on registered dataset → activates it
- [ ] Currently active dataset shows highlighted
- [ ] Path-not-found datasets show warning indicator

### 8.3 Add Current Button
- [ ] Disabled when no dataset is activated
- [ ] Disabled when MongoDB is unavailable
- [ ] Enabled after activating a dataset
- [ ] Click → registers dataset, shows in list
- [ ] Click again → "already registered" toast

### 8.4 Dashboard Button
- [ ] Click → opens dashboard modal (implemented in Phase 25)
- [ ] Disabled/grayed when MongoDB unavailable

### 8.5 Recent Button Removed
- [ ] "Recent" button no longer in top-right toolbar
- [ ] No JS errors from removed Recent functionality

### 8.6 MongoDB Unavailable
- [ ] Both buttons grayed out
- [ ] Empty state message updated
- [ ] No console errors, app works normally for other features
