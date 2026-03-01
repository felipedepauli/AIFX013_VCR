# Phase 26: Dataset Info → MongoDB Sync & Dataset Config

**Version:** v2.2  
**Status:** Planned  
**Dependencies:** Phase 23 (MongoDB), Phase 24 (Datasets Panel), Phase 25 (Dashboard)  
**PRD Reference:** FR-19

---

## 1. Problem Statement

Currently there are two disconnected data stores:

1. **`.dataset.json`** (filesystem) — written by the Dataset Info panel on "Save Changes"
2. **MongoDB `datasets` collection** — written at registration time ("+ Add Current"), then only by Dashboard edits

These diverge immediately after the first edit in either place. The Dashboard shows stale data from registration time, and panel edits never reach MongoDB.

### Current Data Flow (broken)

```
Dataset Info Panel                    Dashboard Detail View
      │ Save                                │ Auto-save
      ▼                                     ▼
  .dataset.json                        MongoDB
  (metadata fields)                    (metadata field)
      ✗ NOT synced ✗                       ✗ NOT synced ✗
```

### Target Data Flow (Phase 26)

```
Dataset Info Panel ──Save──▶ .dataset.json ◀──────┐
      │                           │                │
      │ (if registered)           │                │
      ▼                           │                │
   MongoDB  ◀─ auto-sync ────────┘                │
      │                                            │
      ▼                                            │
Dashboard Detail View ──auto-save──▶ MongoDB──sync─┘
                                        │
                                        ▼
                                   .dataset.json
```

---

## 2. Data Architecture

### 2.1 MongoDB Document (Extended Schema)

```json
{
  "_id": "ObjectId",
  "name": "sat_csg",
  "root_path": "/data/pdi_datasets/data/datasets/sat_csg",
  "registered_at": "2026-02-25T10:00:00Z",
  "updated_at": "2026-02-25T15:30:00Z",
  
  "metadata": {
    "description": "Satellite camera dataset",
    "camera_view": ["frontal", "panorâmica"],
    "quality": "good",
    "verdict": "keep",
    "cycle": "second",
    "notes": "Ready for training.",
    "model_compatibility": ["colornet_v1"],
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
    "total_images": 4968,
    "class_counts": { "car": 3096, "motorcycle": 172, "truck": 1823, "bus": 74 },
    "spatial": {
      "position_mean": { "x": 784.51, "y": 452.46 },
      "position_variance": { "x": 102143.03, "y": 111447.07 },
      "area_mean": 168162.46,
      "area_variance": 37340377597.4
    },
    "computed_at": "2026-02-25T10:05:00"
  },
  
  "thumbnails": {
    "paths": ["<id>_0.jpg", "<id>_1.jpg", "<id>_2.jpg", "<id>_3.jpg"],
    "generated_at": "2026-02-25T10:05:00Z"
  }
}
```

**New fields** (compared to v2.1):
- `config` — operational settings applied when dataset is opened
- `metadata.trainable_models` — model configuration from Dataset Info panel
- `metadata.attributes` — attribute configuration from Dataset Info panel

### 2.2 `.dataset.json` (Unchanged Structure)

```json
{
  "name": "sat_csg",
  "created_at": "2026-02-23T14:57:39.832364",
  "updated_at": "2026-02-25T10:33:51.311246",
  "image_flags": {},
  "stats_config": { "fields": ["label"] },
  "visible_labels": ["color", "brand", "model", "type"],
  "quality_flags": ["brass", "bronze", "silver", "gold"],
  "skip_delete_confirmation": false,
  "description": "",
  "camera_view": [],
  "quality": "",
  "verdict": "",
  "cycle": "",
  "notes": "",
  "trainable_models": [],
  "attributes": []
}
```

The `.dataset.json` structure is NOT changed. It remains backwards compatible. The only difference is that registered datasets now have MongoDB as the authority for metadata and config values.

### 2.3 Field Mapping Table

```
.dataset.json field        →  MongoDB field              Notes
─────────────────────────     ─────────────────────────  ──────────────
name                       →  name (top-level)           Direct map
description                →  metadata.description       Nesting change
camera_view                →  metadata.camera_view       Nesting change
quality                    →  metadata.quality           Nesting change
verdict                    →  metadata.verdict           Nesting change
cycle                      →  metadata.cycle             Nesting change
notes                      →  metadata.notes             Nesting change
trainable_models           →  metadata.trainable_models  New sync
attributes                 →  metadata.attributes        New sync
stats_config.fields        →  config.stats_fields        Renamed
visible_labels             →  config.visible_labels      New sync
quality_flags              →  config.quality_flags       New sync
skip_delete_confirmation   →  config.skip_delete_confirm New sync
image_flags                →  (not in MongoDB)           Too large, stays local
created_at                 →  registered_at              Different semantics
updated_at                 →  updated_at                 Same
```

### 2.4 Authority Rules

| Scenario | Metadata Source | Config Source | image_flags Source |
|----------|----------------|---------------|--------------------|
| Registered dataset | MongoDB | MongoDB | `.dataset.json` |
| Non-registered dataset | `.dataset.json` | `.dataset.json` | `.dataset.json` |
| MongoDB unavailable | `.dataset.json` (fallback) | `.dataset.json` (fallback) | `.dataset.json` |

---

## 3. Backend Implementation

### 3.1 Helper Functions

#### `_find_registered_dataset(root_path)`

```python
def _find_registered_dataset(root_path: str) -> dict | None:
    """Find a registered dataset by root_path. Returns MongoDB doc or None."""
    if not mongo_available or not datasets_collection:
        return None
    try:
        return datasets_collection.find_one({'root_path': root_path.rstrip('/')})
    except Exception:
        return None
```

**Location:** `app.py`, near existing MongoDB helpers (after `_cleanup_dataset_thumbnails`)

#### `_sync_metadata_to_mongodb(root_path, updates)`

```python
def _sync_metadata_to_mongodb(root_path: str, updates: dict) -> bool:
    """
    Sync metadata/config changes to MongoDB for a registered dataset.
    
    `updates` can contain:
      - Top-level: 'name'
      - Nested under 'metadata': description, camera_view, quality, verdict, 
        cycle, notes, trainable_models, attributes, model_compatibility
      - Nested under 'config': stats_fields, visible_labels, quality_flags,
        skip_delete_confirmation
    
    Returns True if sync succeeded, False if failed or not registered.
    """
    doc = _find_registered_dataset(root_path)
    if not doc:
        return False  # Not registered — nothing to sync
    
    mongo_updates = {'updated_at': datetime.utcnow()}
    
    # Map flat .dataset.json fields to MongoDB nested structure
    METADATA_FIELDS = [
        'description', 'camera_view', 'quality', 'verdict', 
        'cycle', 'notes', 'trainable_models', 'attributes'
    ]
    CONFIG_FIELDS_MAP = {
        'stats_config': 'config.stats_fields',  # special: extract .fields
        'visible_labels': 'config.visible_labels',
        'quality_flags': 'config.quality_flags',
        'skip_delete_confirmation': 'config.skip_delete_confirmation'
    }
    
    if 'name' in updates:
        mongo_updates['name'] = updates['name']
    
    for field in METADATA_FIELDS:
        if field in updates:
            mongo_updates[f'metadata.{field}'] = updates[field]
    
    for json_key, mongo_key in CONFIG_FIELDS_MAP.items():
        if json_key in updates:
            value = updates[json_key]
            if json_key == 'stats_config' and isinstance(value, dict):
                value = value.get('fields', [])
            mongo_updates[mongo_key] = value
    
    try:
        datasets_collection.update_one(
            {'_id': doc['_id']},
            {'$set': mongo_updates}
        )
        return True
    except Exception as e:
        print(f"[MongoDB Sync] Failed to sync {root_path}: {e}")
        return False
```

#### `_sync_to_dataset_json(root_path, mongo_doc)`

```python
def _sync_to_dataset_json(root_path: str, mongo_doc: dict) -> bool:
    """
    Sync MongoDB metadata/config back to .dataset.json.
    Used when Dashboard edits need to be reflected in the filesystem.
    Preserves image_flags and created_at.
    """
    dataset_file = Path(root_path) / '.dataset.json'
    
    try:
        existing = {}
        if dataset_file.exists():
            with open(dataset_file) as f:
                existing = json.load(f)
        
        meta = mongo_doc.get('metadata', {})
        config = mongo_doc.get('config', {})
        
        # Sync metadata fields
        existing['name'] = mongo_doc.get('name', existing.get('name', ''))
        for field in ['description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes']:
            if field in meta:
                existing[field] = meta[field]
        
        if 'trainable_models' in meta:
            existing['trainable_models'] = meta['trainable_models']
        if 'attributes' in meta:
            existing['attributes'] = meta['attributes']
        
        # Sync config fields
        if 'stats_fields' in config:
            existing['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            existing['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            existing['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            existing['skip_delete_confirmation'] = config['skip_delete_confirmation']
        
        existing['updated_at'] = datetime.now().isoformat()
        
        with open(dataset_file, 'w') as f:
            json.dump(existing, f, indent=2)
        
        return True
    except Exception as e:
        print(f"[Sync] Failed to write .dataset.json for {root_path}: {e}")
        return False
```

### 3.2 Modified Endpoints

#### `PUT /api/dataset/metadata` (modified)

**Current behavior:** Writes to `.dataset.json` only.  
**New behavior:** Writes to `.dataset.json` AND syncs to MongoDB if registered.

```python
@app.route('/api/dataset/metadata', methods=['PUT'])
def update_dataset_metadata():
    data = request.get_json()
    path = data.get('path')
    updates = data.get('metadata', {})
    
    # ... existing validation ...
    
    # ... existing .dataset.json write logic (unchanged) ...
    
    # NEW: Sync to MongoDB if registered
    synced = _sync_metadata_to_mongodb(path, updates)
    
    return jsonify({
        'success': True,
        'data': {
            'updated_at': metadata['updated_at'],
            'synced_to_mongodb': synced  # NEW: tells frontend if sync happened
        }
    })
```

**Key change:** Add `synced_to_mongodb` to response so frontend can update indicator.

#### `PUT /api/dataset/config` (new, replaces `PUT /api/dataset/stats-config`)

```python
@app.route('/api/dataset/config', methods=['PUT'])
def update_dataset_config():
    """Update dataset configuration (stats fields, visible labels, quality flags)."""
    data = request.get_json()
    path = data.get('path')
    config = data.get('config', {})
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            dataset_data = json.load(f)
        
        # Apply config fields to .dataset.json
        if 'stats_fields' in config:
            dataset_data['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            dataset_data['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            dataset_data['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            dataset_data['skip_delete_confirmation'] = config['skip_delete_confirmation']
        
        dataset_data['updated_at'] = datetime.now().isoformat()
        
        with open(dataset_file, 'w') as f:
            json.dump(dataset_data, f, indent=2)
        
        # Sync to MongoDB
        synced = False
        if mongo_available:
            doc = _find_registered_dataset(path)
            if doc:
                mongo_config = {}
                for key in ['stats_fields', 'visible_labels', 'quality_flags', 
                           'skip_delete_confirmation']:
                    if key in config:
                        mongo_config[f'config.{key}'] = config[key]
                mongo_config['updated_at'] = datetime.utcnow()
                try:
                    datasets_collection.update_one(
                        {'_id': doc['_id']}, {'$set': mongo_config}
                    )
                    synced = True
                except Exception as e:
                    print(f"[MongoDB] Config sync failed: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'config': config,
                'updated_at': dataset_data['updated_at'],
                'synced_to_mongodb': synced
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

**Note:** Keep `PUT /api/dataset/stats-config` as a deprecated alias that redirects internally, to avoid breaking anything.

#### `POST /api/browse/activate` (modified)

**Current behavior:** Reads from `.dataset.json`, registers in JSON registry.  
**New behavior:** If registered in MongoDB, loads metadata + config from MongoDB (authority), merges with `.dataset.json` for `image_flags`.

```python
@app.route('/api/browse/activate', methods=['POST'])
def activate_directory():
    data = request.get_json()
    path = data.get('path')
    settings = data.get('settings', {})
    
    # ... existing validation ...
    
    dataset_file = target / '.dataset.json'
    
    # Load .dataset.json (always needed for image_flags)
    if dataset_file.exists():
        with open(dataset_file) as f:
            dataset_data = json.load(f)
    else:
        dataset_data = {}
    
    # ... existing defaults and settings merge ...
    
    # NEW: Check MongoDB for registered dataset
    mongo_doc = _find_registered_dataset(str(target))
    is_registered = mongo_doc is not None
    
    if is_registered:
        # MongoDB is authority for metadata and config
        meta = mongo_doc.get('metadata', {})
        config = mongo_doc.get('config', {})
        
        # Override .dataset.json metadata with MongoDB values
        dataset_data['name'] = mongo_doc.get('name', dataset_data.get('name', target.name))
        for field in ['description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes']:
            if field in meta:
                dataset_data[field] = meta[field]
        if 'trainable_models' in meta:
            dataset_data['trainable_models'] = meta['trainable_models']
        if 'attributes' in meta:
            dataset_data['attributes'] = meta['attributes']
        
        # Override config
        if 'stats_fields' in config:
            dataset_data['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            dataset_data['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            dataset_data['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            dataset_data['skip_delete_confirmation'] = config['skip_delete_confirmation']
    
    # ... existing registration + save logic ...
    
    return jsonify({
        'success': True,
        'data': {
            'path': str(target),
            'image_count': image_count,
            'settings': dataset_data,
            'is_registered': is_registered  # NEW: frontend uses for sync indicator
        }
    })
```

#### `PUT /api/datasets/<id>` (modified — Dashboard edits)

**Current behavior:** Updates MongoDB only.  
**New behavior:** Updates MongoDB AND syncs back to `.dataset.json`.

```python
@app.route('/api/datasets/<dataset_id>', methods=['PUT'])
@requires_mongodb
def update_dataset(dataset_id):
    # ... existing validation and MongoDB update ...
    
    # NEW: Sync changes back to .dataset.json
    updated_doc = datasets_collection.find_one({'_id': oid})
    if updated_doc:
        _sync_to_dataset_json(updated_doc['root_path'], updated_doc)
    
    return jsonify(serialize_dataset(updated_doc))
```

#### `POST /api/datasets` (modified — Registration)

**Current behavior:** Reads limited metadata from `.dataset.json`.  
**New behavior:** Reads full metadata + config from `.dataset.json`.

The registration endpoint currently reads:
```python
metadata = {
    'description': '', 'camera_view': [], 'quality': '', 
    'verdict': '', 'cycle': '', 'notes': '', 'model_compatibility': []
}
```

**Extended to include:**
```python
metadata = {
    'description': '', 'camera_view': [], 'quality': '', 'verdict': '',
    'cycle': '', 'notes': '', 'model_compatibility': [],
    'trainable_models': [], 'attributes': []
}
config = {
    'stats_fields': ['label', 'color', 'model'],
    'visible_labels': ['color', 'brand', 'model', 'type'],
    'quality_flags': ['brass', 'bronze', 'silver', 'gold'],
    'skip_delete_confirmation': False
}

if os.path.exists(dataset_json_path):
    with open(dataset_json_path, 'r') as f:
        ds_data = json.load(f)
    
    # Read metadata
    for key in ['description', 'camera_view', 'quality', 'verdict', 
                'cycle', 'notes', 'trainable_models', 'attributes']:
        if key in ds_data:
            metadata[key] = ds_data[key]
    
    # Read config
    if 'stats_config' in ds_data:
        config['stats_fields'] = ds_data['stats_config'].get('fields', config['stats_fields'])
    for key in ['visible_labels', 'quality_flags', 'skip_delete_confirmation']:
        if key in ds_data:
            config[key] = ds_data[key]

# Include config in document
document = {
    ...,
    'metadata': metadata,
    'config': config,
    ...
}
```

### 3.3 Deprecated Endpoint

```python
@app.route('/api/dataset/stats-config', methods=['PUT'])
def update_stats_config():
    """DEPRECATED: Use PUT /api/dataset/config instead. Kept for backwards compat."""
    data = request.get_json()
    # Convert old format to new format
    new_data = {
        'path': data.get('path'),
        'config': {'stats_fields': data.get('fields', [])}
    }
    # Delegate to new endpoint logic
    ...
```

---

## 4. Frontend Implementation

### 4.1 Sync Indicator

Add a small status badge to the metadata panel header:

**HTML** (in `index.html`, metadata panel header):
```html
<span class="panel-title">DATASET INFO</span>
<span id="sync-indicator" class="sync-indicator" style="display:none;">
    <span class="sync-dot"></span>
    <span class="sync-text"></span>
</span>
```

**CSS:**
```css
.sync-indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    margin-left: 8px;
}
.sync-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
}
.sync-indicator.synced .sync-dot { background: #4caf50; }
.sync-indicator.synced .sync-text { color: #4caf50; }
.sync-indicator.local .sync-dot { background: #888; }
.sync-indicator.local .sync-text { color: #888; }
.sync-indicator.failed .sync-dot { background: #f59e0b; }
.sync-indicator.failed .sync-text { color: #f59e0b; }
```

**JS:**
```javascript
// State variable
let datasetIsRegistered = false;

function updateSyncIndicator(status) {
    // status: 'synced' | 'local' | 'failed'
    const el = document.getElementById('sync-indicator');
    if (!el) return;
    el.style.display = 'inline-flex';
    el.className = `sync-indicator ${status}`;
    const textEl = el.querySelector('.sync-text');
    if (status === 'synced') textEl.textContent = '✓ Synced';
    else if (status === 'local') textEl.textContent = 'Local only';
    else if (status === 'failed') textEl.textContent = '⚠ Sync failed';
}
```

### 4.2 Modified `activateDirectory()`

After activation response, check `is_registered`:

```javascript
// In activateDirectory(), after setting browseState:
if (result.data.is_registered !== undefined) {
    datasetIsRegistered = result.data.is_registered;
    updateSyncIndicator(datasetIsRegistered ? 'synced' : 'local');
}
```

### 4.3 Modified `saveDatasetMetadata()`

After saving, check `synced_to_mongodb` in response:

```javascript
async function saveDatasetMetadata() {
    // ... existing form collection ...
    
    const result = await response.json();
    
    if (result.success) {
        Object.assign(browseState.metadata || {}, updates);
        
        // Update sync indicator based on response
        if (result.data?.synced_to_mongodb) {
            showNotification('Metadata saved & synced to DB', 'success');
            updateSyncIndicator('synced');
        } else if (datasetIsRegistered) {
            showNotification('Metadata saved (sync failed)', 'warning');
            updateSyncIndicator('failed');
        } else {
            showNotification('Metadata saved', 'success');
            updateSyncIndicator('local');
        }
    }
}
```

### 4.4 Rename Stats Config → Dataset Config

**HTML changes:**
```html
<!-- OLD -->
<span class="section-title">Stats Config</span>

<!-- NEW -->
<span class="section-title">Dataset Config</span>
```

Add new fields to the section:

```html
<div class="section-content" id="config-content">
    <div class="dataset-config-form">
        <!-- Stats Fields (existing) -->
        <label class="config-group-label">Statistics Fields:</label>
        <div class="checkbox-group" id="stats-fields-options">
            <!-- existing checkboxes unchanged -->
        </div>
        
        <!-- Visible Labels (NEW) -->
        <label class="config-group-label">Visible Labels:</label>
        <div class="checkbox-group" id="visible-labels-options">
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="color" checked> color
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="brand" checked> brand
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="model" checked> model
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="label"> label
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="type" checked> type
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="sub_type"> sub_type
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="visible_labels" value="lp_coords"> lp_coords
            </label>
        </div>
        
        <!-- Quality Flags (NEW) -->
        <label class="config-group-label">Quality Flags:</label>
        <div id="quality-flags-list" class="quality-flags-list">
            <!-- populated dynamically -->
        </div>
        <div class="add-flag-form">
            <input type="text" id="new-quality-flag" placeholder="New flag name...">
            <button class="add-btn" onclick="addQualityFlag()">+</button>
        </div>
        
        <button type="button" class="config-save-btn" onclick="saveDatasetConfig()">
            Apply
        </button>
    </div>
</div>
```

### 4.5 Modified `saveDatasetConfig()` (was `saveStatsConfig()`)

```javascript
async function saveDatasetConfig() {
    if (!browseState.isActive || !browseState.activePath) {
        showNotification('No dataset active', 'warning');
        return;
    }
    
    // Collect all config values
    const statsFields = Array.from(
        document.querySelectorAll('input[name="stats_fields"]:checked')
    ).map(cb => cb.value);
    
    const visibleLabels = Array.from(
        document.querySelectorAll('input[name="visible_labels"]:checked')
    ).map(cb => cb.value);
    
    const qualityFlags = Array.from(
        document.querySelectorAll('#quality-flags-list .flag-item')
    ).map(el => el.dataset.value);
    
    if (statsFields.length === 0) {
        showNotification('Select at least one statistics field', 'warning');
        return;
    }
    
    const config = {
        stats_fields: statsFields,
        visible_labels: visibleLabels,
        quality_flags: qualityFlags
    };
    
    try {
        const response = await fetch('/api/dataset/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: browseState.activePath,
                config: config
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Apply config locally
            visibleLabels_state = config.visible_labels;  // update app state
            if (config.quality_flags) {
                projectData.settings.quality_flags = config.quality_flags;
            }
            
            // Reload stats with new fields
            loadDatasetStats(config.stats_fields);
            
            // Re-render grid to apply visible labels
            loadImages();
            
            // Update sync indicator
            if (result.data?.synced_to_mongodb) {
                updateSyncIndicator('synced');
            }
            
            showNotification('Dataset config applied', 'success');
        }
    } catch (error) {
        console.error('Failed to save config:', error);
        showNotification('Failed to save configuration', 'error');
    }
}
```

### 4.6 Quality Flags Management

```javascript
function renderQualityFlags() {
    const container = document.getElementById('quality-flags-list');
    if (!container) return;
    
    const flags = getAvailableQualityFlags();
    
    container.innerHTML = flags.map(flag => `
        <div class="flag-item" data-value="${escapeHtml(flag)}">
            <span class="flag-name">${escapeHtml(flag)}</span>
            <button class="remove-flag" onclick="removeQualityFlag('${escapeHtml(flag)}')">×</button>
        </div>
    `).join('');
}

function addQualityFlag() {
    const input = document.getElementById('new-quality-flag');
    if (!input) return;
    const name = input.value.trim();
    if (!name) return;
    
    const flags = getAvailableQualityFlags();
    if (!flags.includes(name)) {
        flags.push(name);
        if (!projectData) projectData = { settings: {} };
        if (!projectData.settings) projectData.settings = {};
        projectData.settings.quality_flags = flags;
        renderQualityFlags();
    }
    input.value = '';
}

function removeQualityFlag(name) {
    let flags = getAvailableQualityFlags().filter(f => f !== name);
    if (!projectData) projectData = { settings: {} };
    if (!projectData.settings) projectData.settings = {};
    projectData.settings.quality_flags = flags;
    renderQualityFlags();
}
```

### 4.7 Populate Config on Load

In `populateMetadataForm()`, add config population:

```javascript
function populateMetadataForm(metadata) {
    // ... existing code ...
    
    // Populate visible labels checkboxes (NEW)
    const visLabels = metadata.visible_labels || DEFAULT_VISIBLE_LABELS;
    document.querySelectorAll('input[name="visible_labels"]').forEach(cb => {
        cb.checked = visLabels.includes(cb.value);
    });
    
    // Populate quality flags list (NEW)
    if (metadata.quality_flags) {
        if (!projectData) projectData = { settings: {} };
        if (!projectData.settings) projectData.settings = {};
        projectData.settings.quality_flags = metadata.quality_flags;
    }
    renderQualityFlags();
}
```

---

## 5. Sync Scenarios

### 5.1 Save in Dataset Info Panel (registered dataset)

```
User clicks "Save Changes"
    → PUT /api/dataset/metadata { path, metadata: {...} }
        → Backend:
            1. Write to .dataset.json ← always
            2. _sync_metadata_to_mongodb(path, updates) ← if registered
        → Response: { success: true, synced_to_mongodb: true }
    → Frontend: show "Metadata saved & synced" + green indicator
```

### 5.2 Save in Dataset Info Panel (non-registered dataset)

```
User clicks "Save Changes"
    → PUT /api/dataset/metadata { path, metadata: {...} }
        → Backend:
            1. Write to .dataset.json ← always
            2. _find_registered_dataset(path) → null, skip sync
        → Response: { success: true, synced_to_mongodb: false }
    → Frontend: show "Metadata saved" + grey "Local only" indicator
```

### 5.3 Edit in Dashboard (registered dataset)

```
User changes field in Dashboard detail
    → PUT /api/datasets/<id> { metadata: { verdict: "keep" } }
        → Backend:
            1. Update MongoDB document ← always
            2. _sync_to_dataset_json(root_path, updated_doc) ← NEW
        → Response: { ...updated doc }
```

### 5.4 Toggle Trainable Model (registered dataset)

```
User toggles model checkbox
    → updateTrainableModel() → saveTrainableModels()
        → PUT /api/dataset/metadata { path, metadata: { trainable_models: [...] } }
            → Backend: write .dataset.json + sync to MongoDB
```

### 5.5 Apply Dataset Config

```
User clicks "Apply" in Dataset Config
    → saveDatasetConfig()
        → PUT /api/dataset/config { path, config: { stats_fields, visible_labels, quality_flags } }
            → Backend: write .dataset.json + sync to MongoDB
        → Frontend: apply visibleLabels, qualityFlags, reload stats
```

### 5.6 Open Registered Dataset

```
User activates directory
    → POST /api/browse/activate { path, settings }
        → Backend:
            1. Load .dataset.json (for image_flags)
            2. _find_registered_dataset(path)
            3. If registered: override metadata + config from MongoDB
            4. Save merged data to .dataset.json
        → Response: { settings: merged_data, is_registered: true }
    → Frontend:
        1. Apply visibleLabels from config
        2. Apply qualityFlags from config
        3. Set sync indicator to "synced"
        4. populateMetadataForm() with MongoDB values
```

---

## 6. Migration Strategy

### 6.1 Existing Registered Datasets (no `config` or `trainable_models`)

When a registered dataset is opened and its MongoDB doc lacks the new fields:

1. **`config` missing:** Use defaults from `.dataset.json` if available, else hardcoded defaults
2. **`metadata.trainable_models` missing:** Use `[]` (empty), will be populated on next save
3. **`metadata.attributes` missing:** Use `[]` (empty)

The lazy migration happens in `POST /api/browse/activate`:
```python
if is_registered and 'config' not in mongo_doc:
    # First access after v2.2 upgrade — populate from .dataset.json
    initial_config = {
        'stats_fields': dataset_data.get('stats_config', {}).get('fields', ['label', 'color', 'model']),
        'visible_labels': dataset_data.get('visible_labels', ['color', 'brand', 'model', 'type']),
        'quality_flags': dataset_data.get('quality_flags', ['brass', 'bronze', 'silver', 'gold']),
        'skip_delete_confirmation': dataset_data.get('skip_delete_confirmation', False)
    }
    datasets_collection.update_one(
        {'_id': mongo_doc['_id']},
        {'$set': {'config': initial_config}}
    )
```

### 6.2 No Breaking Changes

- `.dataset.json` format is unchanged
- Old `PUT /api/dataset/stats-config` still works (deprecated, delegates to new endpoint)
- Non-registered datasets work exactly as before
- MongoDB documents without `config` field gracefully use defaults

---

## 7. Error Handling

| Scenario | Behavior |
|----------|----------|
| MongoDB down during save | `.dataset.json` saved, sync skipped, warning shown |
| MongoDB down during activation | Fall back to `.dataset.json` entirely |
| `.dataset.json` corrupted | Return error, don't touch MongoDB |
| MongoDB doc missing `config` | Lazy migrate from `.dataset.json` or use defaults |
| Concurrent edit (panel + dashboard) | Last write wins (both update `updated_at`) |
| Registration of old-format dataset | New fields populated from `.dataset.json` at registration time |

---

## 8. Files Modified

| File | Changes |
|------|---------|
| `app.py` | Add `_find_registered_dataset()`, `_sync_metadata_to_mongodb()`, `_sync_to_dataset_json()`. Modify `update_dataset_metadata()`, `activate_directory()`, `update_dataset()`, `register_dataset_mongo()`. New `update_dataset_config()`. Deprecate `update_stats_config()`. |
| `index.html` | Rename "Stats Config" → "Dataset Config". Add visible_labels checkboxes, quality_flags list, sync indicator. |
| `app.js` | Add `datasetIsRegistered` state, `updateSyncIndicator()`. Modify `saveDatasetMetadata()`, `activateDirectory()`, `populateMetadataForm()`. New `saveDatasetConfig()` (replace `saveStatsConfig()`), `renderQualityFlags()`, `addQualityFlag()`, `removeQualityFlag()`. |
| `styles.css` | Sync indicator styles, quality flags list styles, config group label styles. |

---

## 9. Estimated Scope

| Sub-phase | Effort | Description |
|-----------|--------|-------------|
| 26.1 Schema + Helpers | Small | 3 helper functions + schema extension |
| 26.2 Metadata Sync | Medium | Modify 2 endpoints, add sync calls |
| 26.3 Dataset Config UI | Medium | HTML/CSS/JS for config section |
| 26.4 Apply on Open | Medium | Modify activation flow, frontend config apply |
| 26.5 Sync Indicator | Small | HTML + CSS + JS state management |
| 26.6 Dashboard Sync-back | Small | Modify dashboard PUT to write .dataset.json |
