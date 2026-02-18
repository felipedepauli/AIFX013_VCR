# Phase 14: Dataset Metadata Panel

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Add a collapsible right panel for viewing and editing dataset metadata. Displays class statistics and allows editing of dataset properties like description, camera view, quality, verdict, cycle, and notes.

---

## 1. Prerequisites
- Phase 12 complete (File System Browser)
- Phase 13 complete (Dataset Activation)
- `.dataset.json` file structure implemented

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Metadata Panel** | Right sidebar showing dataset information |
| **Class Stats** | Distribution of values for configured fields |
| **Stats Config** | Configurable list of fields to show in stats |
| **Dataset Properties** | Editable metadata fields |

### 2.2 Panel Layout

```
┌─────────────────────────────────┐
│ DATASET INFO                  ▶ │
├─────────────────────────────────┤
│                                 │
│ ▼ Statistics                    │
│   label                         │
│     car        ███████░░ 45     │
│     truck      ███░░░░░░ 12     │
│     moto       █░░░░░░░░  3     │
│                                 │
│   color                         │
│     white      █████░░░░ 28     │
│     silver     ████░░░░░ 20     │
│     black      ███░░░░░░ 12     │
│                                 │
│ ▼ Properties                    │
│   Name: vehicle_colors_v4       │
│   Description: [textarea]       │
│   Camera View: [multi-select]   │
│   Quality: [select]             │
│   Verdict: [select]             │
│   Cycle: [select]               │
│   Notes: [textarea]             │
│                                 │
│ ▼ Stats Configuration           │
│   Fields: [multi-select]        │
│                                 │
└─────────────────────────────────┘
```

---

## 3. UI Components

### 3.1 Metadata Panel Structure

```html
<aside id="metadata-panel" class="metadata-panel">
    <div class="metadata-panel-header">
        <button class="panel-collapse-btn" onclick="toggleMetadataPanel()" title="Collapse">
            <span class="toggle-icon" id="meta-panel-toggle-icon">▶</span>
        </button>
        <span class="panel-title">DATASET INFO</span>
    </div>
    
    <div class="metadata-panel-content">
        <!-- Statistics Section -->
        <div class="panel-section stats-section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="section-icon">📊</span>
                <span class="section-title">Statistics</span>
                <span class="section-toggle">▼</span>
            </div>
            <div class="section-content" id="stats-content">
                <!-- Stats injected here -->
            </div>
        </div>
        
        <!-- Properties Section -->
        <div class="panel-section properties-section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="section-icon">📋</span>
                <span class="section-title">Properties</span>
                <span class="section-toggle">▼</span>
            </div>
            <div class="section-content" id="properties-content">
                <!-- Properties form injected here -->
            </div>
        </div>
        
        <!-- Stats Configuration Section -->
        <div class="panel-section config-section">
            <div class="section-header" onclick="toggleSection(this)">
                <span class="section-icon">⚙️</span>
                <span class="section-title">Stats Config</span>
                <span class="section-toggle">▼</span>
            </div>
            <div class="section-content" id="config-content">
                <!-- Config form injected here -->
            </div>
        </div>
    </div>
</aside>
```

### 3.2 Statistics Display

```html
<div class="stats-field">
    <div class="stats-field-name">label</div>
    <div class="stats-items">
        <div class="stats-item">
            <span class="stats-label">car</span>
            <div class="stats-bar-container">
                <div class="stats-bar" style="width: 75%"></div>
            </div>
            <span class="stats-count">45</span>
        </div>
        <!-- More items -->
    </div>
</div>
```

### 3.3 Properties Form

```html
<form id="metadata-form" class="metadata-form">
    <!-- Name (read-only) -->
    <div class="form-field">
        <label>Name</label>
        <input type="text" name="name" readonly class="readonly">
    </div>
    
    <!-- Description -->
    <div class="form-field">
        <label>Description</label>
        <textarea name="description" rows="3" placeholder="Enter dataset description..."></textarea>
    </div>
    
    <!-- Camera View (multi-select) -->
    <div class="form-field">
        <label>Camera View</label>
        <div class="checkbox-group" id="camera-view-options">
            <label class="checkbox-option">
                <input type="checkbox" name="camera_view" value="frontal"> Frontal
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="camera_view" value="traseira"> Traseira
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="camera_view" value="panorâmica"> Panorâmica
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="camera_view" value="closeup"> Closeup
            </label>
            <label class="checkbox-option">
                <input type="checkbox" name="camera_view" value="super-panorâmica"> Super-panorâmica
            </label>
        </div>
    </div>
    
    <!-- Quality -->
    <div class="form-field">
        <label>Quality</label>
        <select name="quality">
            <option value="">Select...</option>
            <option value="poor">Poor</option>
            <option value="fair">Fair</option>
            <option value="good">Good</option>
            <option value="excellent">Excellent</option>
        </select>
    </div>
    
    <!-- Verdict -->
    <div class="form-field">
        <label>Verdict</label>
        <select name="verdict">
            <option value="">Select...</option>
            <option value="keep">Keep</option>
            <option value="revise">Revise</option>
            <option value="remove">Remove</option>
        </select>
    </div>
    
    <!-- Cycle -->
    <div class="form-field">
        <label>Cycle</label>
        <select name="cycle">
            <option value="">Select...</option>
            <option value="first">First</option>
            <option value="second">Second</option>
            <option value="third">Third</option>
            <option value="fourth">Fourth</option>
            <option value="fifth">Fifth</option>
        </select>
    </div>
    
    <!-- Notes -->
    <div class="form-field">
        <label>Notes</label>
        <textarea name="notes" rows="4" placeholder="Additional notes..."></textarea>
    </div>
    
    <div class="form-actions">
        <button type="button" class="save-btn" onclick="saveMetadata()">
            Save Changes
        </button>
    </div>
</form>
```

### 3.4 Stats Configuration Form

```html
<div class="stats-config-form">
    <label>Fields to show in statistics:</label>
    <div class="checkbox-group" id="stats-fields-options">
        <label class="checkbox-option">
            <input type="checkbox" name="stats_fields" value="label" checked> label
        </label>
        <label class="checkbox-option">
            <input type="checkbox" name="stats_fields" value="color" checked> color
        </label>
        <label class="checkbox-option">
            <input type="checkbox" name="stats_fields" value="model" checked> model
        </label>
        <label class="checkbox-option">
            <input type="checkbox" name="stats_fields" value="quality_flag"> quality_flag
        </label>
        <label class="checkbox-option">
            <input type="checkbox" name="stats_fields" value="direction"> direction
        </label>
    </div>
    <button type="button" class="config-save-btn" onclick="saveStatsConfig()">
        Apply
    </button>
</div>
```

---

## 4. CSS Styling

```css
/* Metadata Panel */
.metadata-panel {
    width: 300px;
    background: #1e1e2e;
    border-left: 1px solid #333;
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
}

.metadata-panel.collapsed {
    width: 0;
    overflow: hidden;
}

.metadata-panel-header {
    padding: 12px 16px;
    background: #252536;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid #333;
}

.metadata-panel-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
}

/* Statistics Display */
.stats-field {
    margin-bottom: 16px;
}

.stats-field-name {
    font-weight: 600;
    color: #4a69bd;
    margin-bottom: 8px;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}

.stats-items {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.stats-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
}

.stats-label {
    width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #ccc;
}

.stats-bar-container {
    flex: 1;
    height: 8px;
    background: #333;
    border-radius: 4px;
    overflow: hidden;
}

.stats-bar {
    height: 100%;
    background: linear-gradient(90deg, #4a69bd, #5a79cd);
    border-radius: 4px;
    transition: width 0.3s ease;
}

.stats-count {
    width: 40px;
    text-align: right;
    color: #888;
    font-size: 11px;
}

/* Metadata Form */
.metadata-form {
    padding: 8px;
}

.form-field {
    margin-bottom: 16px;
}

.form-field label {
    display: block;
    margin-bottom: 6px;
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.form-field input[type="text"],
.form-field textarea,
.form-field select {
    width: 100%;
    padding: 8px 10px;
    background: #252536;
    border: 1px solid #333;
    border-radius: 4px;
    color: #eee;
    font-size: 13px;
    font-family: inherit;
}

.form-field input[type="text"]:focus,
.form-field textarea:focus,
.form-field select:focus {
    border-color: #4a69bd;
    outline: none;
}

.form-field input.readonly {
    background: #1a1a2a;
    color: #888;
    cursor: not-allowed;
}

.form-field textarea {
    resize: vertical;
    min-height: 60px;
}

/* Checkbox Group */
.checkbox-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.checkbox-option {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 13px;
    color: #ccc;
}

.checkbox-option input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #4a69bd;
}

.checkbox-option:hover {
    color: #eee;
}

/* Form Actions */
.form-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #333;
}

.save-btn {
    width: 100%;
    padding: 10px;
    background: #4a69bd;
    border: none;
    border-radius: 4px;
    color: #fff;
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.2s;
}

.save-btn:hover {
    background: #5a79cd;
}

.save-btn:disabled {
    background: #333;
    color: #666;
    cursor: not-allowed;
}

/* Stats Config */
.stats-config-form {
    padding: 8px;
}

.stats-config-form > label {
    display: block;
    margin-bottom: 12px;
    font-size: 12px;
    color: #888;
}

.config-save-btn {
    margin-top: 12px;
    padding: 8px 16px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #eee;
    cursor: pointer;
    font-size: 12px;
}

.config-save-btn:hover {
    background: #444;
}

/* No Dataset Message */
.no-dataset-message {
    text-align: center;
    padding: 40px 20px;
    color: #666;
}

.no-dataset-message .message-icon {
    font-size: 48px;
    margin-bottom: 16px;
}

.no-dataset-message p {
    font-size: 13px;
}
```

---

## 5. JavaScript Implementation

### 5.1 Panel Toggle

```javascript
function toggleMetadataPanel() {
    const panel = document.getElementById('metadata-panel');
    const icon = document.getElementById('meta-panel-toggle-icon');
    
    panel.classList.toggle('collapsed');
    icon.textContent = panel.classList.contains('collapsed') ? '◀' : '▶';
    
    // Save state
    localStorage.setItem('metadata_panel_collapsed', panel.classList.contains('collapsed'));
}

function initMetadataPanel() {
    const collapsed = localStorage.getItem('metadata_panel_collapsed') === 'true';
    const panel = document.getElementById('metadata-panel');
    const icon = document.getElementById('meta-panel-toggle-icon');
    
    if (collapsed) {
        panel.classList.add('collapsed');
        icon.textContent = '◀';
    }
}
```

### 5.2 Statistics Rendering

```javascript
function renderStatistics(stats) {
    const container = document.getElementById('stats-content');
    
    if (!stats || Object.keys(stats).length === 0) {
        container.innerHTML = '<div class="no-stats">No statistics available</div>';
        return;
    }
    
    let html = '';
    
    for (const [field, counts] of Object.entries(stats)) {
        const total = Object.values(counts).reduce((a, b) => a + b, 0);
        const maxCount = Math.max(...Object.values(counts));
        
        // Sort by count descending
        const sortedEntries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        
        html += `
            <div class="stats-field">
                <div class="stats-field-name">${escapeHtml(field)}</div>
                <div class="stats-items">
        `;
        
        for (const [value, count] of sortedEntries) {
            const percentage = (count / maxCount) * 100;
            html += `
                <div class="stats-item">
                    <span class="stats-label" title="${escapeHtml(value)}">${escapeHtml(value)}</span>
                    <div class="stats-bar-container">
                        <div class="stats-bar" style="width: ${percentage}%"></div>
                    </div>
                    <span class="stats-count">${count}</span>
                </div>
            `;
        }
        
        html += '</div></div>';
    }
    
    container.innerHTML = html;
}

function updateStatsPanel() {
    if (!datasetState.isActive) {
        renderNoDatasetMessage();
        return;
    }
    
    renderStatistics(datasetState.stats);
}
```

### 5.3 Properties Form

```javascript
function renderPropertiesForm() {
    const container = document.getElementById('properties-content');
    
    if (!datasetState.isActive || !datasetState.metadata) {
        container.innerHTML = '<div class="no-dataset">Activate a dataset to edit properties</div>';
        return;
    }
    
    const meta = datasetState.metadata;
    
    // Populate form fields
    document.querySelector('input[name="name"]').value = meta.name || '';
    document.querySelector('textarea[name="description"]').value = meta.description || '';
    document.querySelector('select[name="quality"]').value = meta.quality || '';
    document.querySelector('select[name="verdict"]').value = meta.verdict || '';
    document.querySelector('select[name="cycle"]').value = meta.cycle || '';
    document.querySelector('textarea[name="notes"]').value = meta.notes || '';
    
    // Set camera view checkboxes
    const cameraViews = meta.camera_view || [];
    document.querySelectorAll('input[name="camera_view"]').forEach(checkbox => {
        checkbox.checked = cameraViews.includes(checkbox.value);
    });
}

async function saveMetadata() {
    if (!datasetState.isActive) {
        showNotification('No dataset active', 'warning');
        return;
    }
    
    const form = document.getElementById('metadata-form');
    const formData = new FormData(form);
    
    // Build metadata object
    const updates = {
        description: formData.get('description'),
        quality: formData.get('quality'),
        verdict: formData.get('verdict'),
        cycle: formData.get('cycle'),
        notes: formData.get('notes'),
        camera_view: formData.getAll('camera_view')
    };
    
    try {
        const response = await fetch('/api/dataset/metadata', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: datasetState.rootPath,
                metadata: updates
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        // Update local state
        Object.assign(datasetState.metadata, updates);
        datasetState.metadata.updated_at = result.data.updated_at;
        
        showNotification('Metadata saved', 'success');
    } catch (error) {
        console.error('Failed to save metadata:', error);
        showNotification('Failed to save metadata', 'error');
    }
}
```

### 5.4 Stats Configuration

```javascript
function renderStatsConfig() {
    const container = document.getElementById('config-content');
    
    if (!datasetState.isActive || !datasetState.metadata) {
        container.innerHTML = '<div class="no-dataset">Activate a dataset to configure stats</div>';
        return;
    }
    
    const currentFields = datasetState.metadata.stats_config?.fields || ['label', 'color', 'model'];
    
    // Set checkboxes
    document.querySelectorAll('input[name="stats_fields"]').forEach(checkbox => {
        checkbox.checked = currentFields.includes(checkbox.value);
    });
}

async function saveStatsConfig() {
    if (!datasetState.isActive) {
        showNotification('No dataset active', 'warning');
        return;
    }
    
    const checkboxes = document.querySelectorAll('input[name="stats_fields"]:checked');
    const fields = Array.from(checkboxes).map(cb => cb.value);
    
    if (fields.length === 0) {
        showNotification('Select at least one field', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/dataset/stats-config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: datasetState.rootPath,
                fields: fields
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error, 'error');
            return;
        }
        
        // Update local state
        datasetState.metadata.stats_config = { fields };
        
        // Reload stats with new fields
        await loadDatasetImages();
        
        showNotification('Stats configuration updated', 'success');
    } catch (error) {
        console.error('Failed to save stats config:', error);
        showNotification('Failed to save configuration', 'error');
    }
}
```

### 5.5 No Dataset Message

```javascript
function renderNoDatasetMessage() {
    const statsContainer = document.getElementById('stats-content');
    const propsContainer = document.getElementById('properties-content');
    const configContainer = document.getElementById('config-content');
    
    const message = `
        <div class="no-dataset-message">
            <div class="message-icon">📁</div>
            <p>Activate a dataset to view information</p>
        </div>
    `;
    
    statsContainer.innerHTML = message;
    propsContainer.innerHTML = message;
    configContainer.innerHTML = message;
}
```

### 5.6 Update on Dataset Change

```javascript
// Call these when dataset is activated/deactivated
function updateMetadataPanel() {
    if (!datasetState.isActive) {
        renderNoDatasetMessage();
        return;
    }
    
    renderStatistics(datasetState.stats);
    renderPropertiesForm();
    renderStatsConfig();
}

// Add to activateDataset() and deactivateDataset()
// After: updateDatasetUI();
// Add: updateMetadataPanel();
```

---

## 6. Backend API

### 6.1 Update Metadata

```python
@app.route('/api/dataset/metadata', methods=['PUT'])
def update_dataset_metadata():
    """Update dataset metadata."""
    data = request.get_json()
    path = data.get('path')
    updates = data.get('metadata', {})
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        # Update allowed fields
        allowed_fields = ['description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes']
        for field in allowed_fields:
            if field in updates:
                metadata[field] = updates[field]
        
        metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        with open(dataset_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'success': True,
            'data': {
                'updated_at': metadata['updated_at']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.2 Update Stats Configuration

```python
@app.route('/api/dataset/stats-config', methods=['PUT'])
def update_stats_config():
    """Update dataset stats configuration."""
    data = request.get_json()
    path = data.get('path')
    fields = data.get('fields', [])
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    if not fields:
        return jsonify({'success': False, 'error': 'At least one field required'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        metadata['stats_config'] = {'fields': fields}
        metadata['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        with open(dataset_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({
            'success': True,
            'data': {
                'fields': fields,
                'updated_at': metadata['updated_at']
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.3 Get Metadata

```python
@app.route('/api/dataset/metadata', methods=['GET'])
def get_dataset_metadata():
    """Get dataset metadata."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        return jsonify({
            'success': True,
            'data': metadata
        })
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid dataset file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 7. HTML Template Updates

The main template already includes the form from section 3.1-3.4. Update [templates/index.html](templates/index.html) to add the metadata panel structure.

---

## 8. Testing Checklist

### 8.1 Panel Display

- [ ] Metadata panel visible on right side
- [ ] Panel can be collapsed/expanded
- [ ] Collapse state persists across refresh

### 8.2 Statistics Section

- [ ] Stats show when dataset active
- [ ] Shows configured fields only
- [ ] Bar widths proportional to counts
- [ ] Sorted by count descending
- [ ] Empty message when no dataset

### 8.3 Properties Form

- [ ] Name field shows dataset name (read-only)
- [ ] Description textarea editable
- [ ] Camera view checkboxes work (multi-select)
- [ ] Quality dropdown shows 4 options
- [ ] Verdict dropdown shows 3 options
- [ ] Cycle dropdown shows 5 options
- [ ] Notes textarea editable

### 8.4 Save Metadata

- [ ] Click "Save Changes" → saves to `.dataset.json`
- [ ] Success notification appears
- [ ] Reload page → values persist
- [ ] Check `.dataset.json` file contains updates

### 8.5 Stats Configuration

- [ ] Shows current field selection
- [ ] Can select/deselect fields
- [ ] Must have at least one selected
- [ ] Click "Apply" → stats refresh
- [ ] New fields appear in stats
- [ ] Configuration persists in `.dataset.json`

### 8.6 No Dataset State

- [ ] All sections show "Activate dataset" message
- [ ] Form inputs disabled or hidden
- [ ] Save buttons disabled

### 8.7 Integration

- [ ] Activate new dataset → panel populates
- [ ] Change dataset → panel updates
- [ ] Deactivate → panel shows no-dataset message

---

## 9. Files Changed Summary

| File | Changes |
|------|---------|
| `app.py` | Add metadata GET/PUT, stats-config PUT endpoints |
| `static/js/app.js` | Add panel toggle, stats render, properties form, save functions |
| `static/css/styles.css` | Add metadata panel, stats display, form styles |
| `templates/index.html` | Add metadata panel HTML structure |

---

## 10. Metadata Field Reference

| Field | Type | Control | Options |
|-------|------|---------|---------|
| name | string | text (readonly) | Auto from folder |
| description | string | textarea | Free text |
| camera_view | array | checkboxes | frontal, traseira, panorâmica, closeup, super-panorâmica |
| quality | string | select | poor, fair, good, excellent |
| verdict | string | select | keep, revise, remove |
| cycle | string | select | first, second, third, fourth, fifth |
| notes | string | textarea | Free text |

---

## 11. Implementation Order

1. **HTML Structure** - Add metadata panel to template
2. **CSS Styling** - Add all panel styles
3. **Panel Toggle** - Implement collapse/expand with persistence
4. **Statistics Rendering** - Implement stats display from datasetState
5. **Properties Form** - Implement form rendering
6. **Save Metadata** - Connect to backend API
7. **Stats Config** - Implement configuration UI and save
8. **Backend API** - Add metadata and stats-config endpoints
9. **Integration** - Connect to dataset activation flow
10. **Testing** - Manual tests per checklist
