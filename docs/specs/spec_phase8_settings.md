# Phase 8: Settings Panel

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Implement a settings panel accessible via gear icon (⚙️) that allows users to configure: delete confirmation, quality flags, perspective flags, visible labels, and view project information.

---

## 1. Prerequisites
- Phase 1-7 complete
- Project JSON structure with settings object

---

## 2. Settings Structure

```json
{
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
  }
}
```

---

## 3. UI Components

### 3.1 Settings Button

```html
<button class="settings-btn" onclick="openSettings()" title="Settings">
    ⚙️
</button>
```

```css
.settings-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #333;
    border: none;
    font-size: 20px;
    cursor: pointer;
    transition: all 0.2s;
}

.settings-btn:hover {
    background: #444;
    transform: rotate(30deg);
}
```

### 3.2 Settings Modal

```
┌──────────────────────────────────────────────────────────────────┐
│  ⚙️ Settings                                           [✕]      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ Project Info ─────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Name: vehicle_colors_v4                                   │  │
│  │  Directory: /home/pauli/.../test                           │  │
│  │  Images: 500 total (12 deleted)                            │  │
│  │  Created: 2026-02-12 10:00                                 │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ General ──────────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  [✓] Skip delete confirmation                              │  │
│  │                                                            │  │
│  │  Default Grid Size:                                        │  │
│  │  ( ) 2×2  (●) 3×3  ( ) 5×5  ( ) 6×6                       │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Visible Labels ───────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  [✓] color    [✓] brand     [✓] model    [ ] label        │  │
│  │  [✓] type     [ ] sub_type  [ ] lp_coords                 │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Quality Flags ────────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Available flags:                                          │  │
│  │  [bin] [review] [ok] [move]  [+ Add]                       │  │
│  │                                                            │  │
│  │  Default: [review ▼]                                       │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─ Perspective Flags ────────────────────────────────────────┐  │
│  │                                                            │  │
│  │  Available flags:                                          │  │
│  │  [close-up-day] [close-up-night] [pan-day] [pan-night]    │  │
│  │  [super_pan_day] [super_pan_night] [cropped-day]          │  │
│  │  [cropped-night]  [+ Add]                                 │  │
│  │                                                            │  │
│  │  Default: [None ▼]                                         │  │
│  │                                                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│                                              [Close]             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.3 HTML Structure

```html
<!-- Settings Modal -->
<div id="settings-modal" class="modal hidden">
    <div class="modal-backdrop" onclick="closeSettings()"></div>
    <div class="modal-content settings-modal-content">
        <div class="modal-header">
            <h2>⚙️ Settings</h2>
            <button class="modal-close" onclick="closeSettings()">✕</button>
        </div>
        
        <!-- Project Info Section -->
        <div class="settings-section">
            <h3>Project Info</h3>
            <div class="project-info">
                <div class="info-row">
                    <span class="info-label">Name:</span>
                    <span id="settings-project-name">vehicle_colors_v4</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Directory:</span>
                    <span id="settings-project-dir" class="dir-path">/home/pauli/.../test</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Images:</span>
                    <span id="settings-image-count">500 total (12 deleted)</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Created:</span>
                    <span id="settings-created-date">2026-02-12 10:00</span>
                </div>
            </div>
        </div>
        
        <!-- General Section -->
        <div class="settings-section">
            <h3>General</h3>
            <label class="setting-checkbox">
                <input type="checkbox" id="setting-skip-confirm" 
                       onchange="updateSetting('skip_delete_confirmation', this.checked)">
                <span>Skip delete confirmation</span>
            </label>
            
            <div class="setting-group">
                <label class="setting-label">Default Grid Size:</label>
                <div class="radio-group">
                    <label>
                        <input type="radio" name="grid-size" value="4" 
                               onchange="updateSetting('grid_size', 4)"> 2×2
                    </label>
                    <label>
                        <input type="radio" name="grid-size" value="9" 
                               onchange="updateSetting('grid_size', 9)"> 3×3
                    </label>
                    <label>
                        <input type="radio" name="grid-size" value="25" 
                               onchange="updateSetting('grid_size', 25)"> 5×5
                    </label>
                    <label>
                        <input type="radio" name="grid-size" value="36" 
                               onchange="updateSetting('grid_size', 36)"> 6×6
                    </label>
                </div>
            </div>
        </div>
        
        <!-- Visible Labels Section -->
        <div class="settings-section">
            <h3>Visible Labels</h3>
            <div class="checkbox-grid" id="visible-labels-settings">
                <!-- Generated by JS -->
            </div>
        </div>
        
        <!-- Quality Flags Section -->
        <div class="settings-section">
            <h3>Quality Flags</h3>
            <div class="flag-manager">
                <div class="flag-tags" id="quality-flags-tags">
                    <!-- Generated by JS -->
                </div>
                <div class="add-flag-row">
                    <input type="text" id="new-quality-flag" placeholder="New flag name">
                    <button onclick="addQualityFlag()">+ Add</button>
                </div>
            </div>
            <div class="setting-group">
                <label class="setting-label">Default for new images:</label>
                <select id="default-quality-flag" onchange="updateSetting('default_quality_flag', this.value)">
                    <option value="">None</option>
                    <!-- Options generated by JS -->
                </select>
            </div>
        </div>
        
        <!-- Perspective Flags Section -->
        <div class="settings-section">
            <h3>Perspective Flags</h3>
            <div class="flag-manager">
                <div class="flag-tags" id="perspective-flags-tags">
                    <!-- Generated by JS -->
                </div>
                <div class="add-flag-row">
                    <input type="text" id="new-perspective-flag" placeholder="New flag name">
                    <button onclick="addPerspectiveFlag()">+ Add</button>
                </div>
            </div>
            <div class="setting-group">
                <label class="setting-label">Default for new images:</label>
                <select id="default-perspective-flag" onchange="updateSetting('default_perspective_flag', this.value)">
                    <option value="">None</option>
                    <!-- Options generated by JS -->
                </select>
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="btn-primary" onclick="closeSettings()">Close</button>
        </div>
    </div>
</div>
```

### 3.4 CSS

```css
.settings-modal-content {
    max-width: 550px;
    max-height: 90vh;
    overflow-y: auto;
    padding: 0;
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    border-bottom: 1px solid #333;
    position: sticky;
    top: 0;
    background: #16213e;
    z-index: 10;
}

.modal-header h2 {
    margin: 0;
}

.settings-section {
    padding: 20px 24px;
    border-bottom: 1px solid #333;
}

.settings-section:last-of-type {
    border-bottom: none;
}

.settings-section h3 {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 16px;
}

/* Project Info */
.project-info {
    background: #0f0f23;
    border-radius: 8px;
    padding: 12px 16px;
}

.info-row {
    display: flex;
    padding: 6px 0;
}

.info-label {
    color: #888;
    width: 80px;
    flex-shrink: 0;
}

.dir-path {
    font-family: monospace;
    font-size: 12px;
    color: #666;
    word-break: break-all;
}

/* Setting Checkbox */
.setting-checkbox {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
    padding: 8px 0;
}

.setting-checkbox input {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

/* Setting Group */
.setting-group {
    margin-top: 16px;
}

.setting-label {
    display: block;
    margin-bottom: 8px;
    color: #888;
    font-size: 14px;
}

.radio-group {
    display: flex;
    gap: 16px;
}

.radio-group label {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
}

/* Checkbox Grid for Labels */
.checkbox-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.checkbox-grid label {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 8px;
    background: #0f0f23;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.checkbox-grid label:hover {
    background: #1a1a2e;
}

/* Flag Manager */
.flag-manager {
    background: #0f0f23;
    border-radius: 8px;
    padding: 12px;
}

.flag-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.flag-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #333;
    padding: 4px 8px 4px 12px;
    border-radius: 16px;
    font-size: 13px;
}

.flag-tag .remove-flag {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: transparent;
    border: none;
    color: #888;
    font-size: 14px;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
}

.flag-tag .remove-flag:hover {
    background: #e74c3c;
    color: white;
}

.add-flag-row {
    display: flex;
    gap: 8px;
}

.add-flag-row input {
    flex: 1;
    padding: 6px 10px;
    border: 1px solid #333;
    border-radius: 4px;
    background: #16213e;
    color: #eee;
    font-size: 13px;
}

.add-flag-row button {
    padding: 6px 12px;
    font-size: 13px;
}

/* Modal Actions */
.settings-modal-content .modal-actions {
    padding: 16px 24px;
    border-top: 1px solid #333;
    position: sticky;
    bottom: 0;
    background: #16213e;
}

.btn-primary {
    width: 100%;
    padding: 12px;
    background: #4a69bd;
    border: none;
    border-radius: 6px;
    color: white;
    font-size: 14px;
    cursor: pointer;
}

.btn-primary:hover {
    background: #5a79cd;
}
```

---

## 4. JavaScript Implementation

### 4.1 Open/Close Settings

```javascript
function openSettings() {
    populateSettingsModal();
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}
```

### 4.2 Populate Settings Modal

```javascript
function populateSettingsModal() {
    const settings = project.settings;
    const projectData = project;
    
    // Project info
    document.getElementById('settings-project-name').textContent = projectData.project_name;
    document.getElementById('settings-project-dir').textContent = truncatePath(projectData.directory);
    
    const totalImages = projectData.images.length;
    const deletedImages = projectData.images.filter(img => img.deleted).length;
    document.getElementById('settings-image-count').textContent = 
        `${totalImages - deletedImages} total (${deletedImages} deleted)`;
    
    document.getElementById('settings-created-date').textContent = 
        formatDate(projectData.created);
    
    // General settings
    document.getElementById('setting-skip-confirm').checked = settings.skip_delete_confirmation;
    
    document.querySelectorAll('input[name="grid-size"]').forEach(radio => {
        radio.checked = parseInt(radio.value) === settings.grid_size;
    });
    
    // Visible labels
    renderVisibleLabelsSettings();
    
    // Quality flags
    renderQualityFlagsSettings();
    
    // Perspective flags
    renderPerspectiveFlagsSettings();
}

function truncatePath(path, maxLength = 40) {
    if (path.length <= maxLength) return path;
    
    const parts = path.split('/');
    const filename = parts.pop();
    
    if (filename.length >= maxLength - 3) {
        return '...' + filename.slice(-(maxLength - 3));
    }
    
    let result = filename;
    for (let i = parts.length - 1; i >= 0; i--) {
        const test = parts[i] + '/' + result;
        if (test.length > maxLength - 3) break;
        result = test;
    }
    
    return '.../' + result;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}
```

### 4.3 Render Visible Labels Settings

```javascript
function renderVisibleLabelsSettings() {
    const container = document.getElementById('visible-labels-settings');
    const allLabels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
    const visible = project.settings.visible_labels || [];
    
    container.innerHTML = allLabels.map(label => `
        <label>
            <input type="checkbox" 
                   ${visible.includes(label) ? 'checked' : ''}
                   onchange="toggleVisibleLabel('${label}', this.checked)">
            ${label}
        </label>
    `).join('');
}

function toggleVisibleLabel(label, isVisible) {
    let visible = project.settings.visible_labels || [];
    
    if (isVisible && !visible.includes(label)) {
        visible.push(label);
    } else if (!isVisible) {
        visible = visible.filter(l => l !== label);
    }
    
    updateSetting('visible_labels', visible);
    
    // Update main toolbar dropdown
    visibleLabels = visible;
    updateLabelCheckboxes();
    refreshAllLabels();
}
```

### 4.4 Render Flag Settings

```javascript
function renderQualityFlagsSettings() {
    const container = document.getElementById('quality-flags-tags');
    const flags = project.settings.quality_flags || [];
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag">
            ${flag}
            <button class="remove-flag" onclick="removeQualityFlag('${flag}')" title="Remove">✕</button>
        </span>
    `).join('');
    
    // Update default dropdown
    const select = document.getElementById('default-quality-flag');
    select.innerHTML = '<option value="">None</option>' + 
        flags.map(flag => `
            <option value="${flag}" ${project.settings.default_quality_flag === flag ? 'selected' : ''}>
                ${flag}
            </option>
        `).join('');
}

function renderPerspectiveFlagsSettings() {
    const container = document.getElementById('perspective-flags-tags');
    const flags = project.settings.perspective_flags || [];
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag">
            ${flag}
            <button class="remove-flag" onclick="removePerspectiveFlag('${flag}')" title="Remove">✕</button>
        </span>
    `).join('');
    
    // Update default dropdown
    const select = document.getElementById('default-perspective-flag');
    select.innerHTML = '<option value="">None</option>' + 
        flags.map(flag => `
            <option value="${flag}" ${project.settings.default_perspective_flag === flag ? 'selected' : ''}>
                ${flag}
            </option>
        `).join('');
}
```

### 4.5 Add/Remove Flags

```javascript
function addQualityFlag() {
    const input = document.getElementById('new-quality-flag');
    const flagName = input.value.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!flagName) return;
    
    const flags = project.settings.quality_flags || [];
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('quality_flags', flags);
    
    input.value = '';
    renderQualityFlagsSettings();
    
    // Update flag modal if open
    if (flagModalState.isOpen) {
        renderFlagCheckboxes();
    }
}

function removeQualityFlag(flag) {
    const flags = project.settings.quality_flags || [];
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('quality_flags', newFlags);
    
    // Clear default if removed
    if (project.settings.default_quality_flag === flag) {
        updateSetting('default_quality_flag', null);
    }
    
    renderQualityFlagsSettings();
}

function addPerspectiveFlag() {
    const input = document.getElementById('new-perspective-flag');
    const flagName = input.value.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!flagName) return;
    
    const flags = project.settings.perspective_flags || [];
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('perspective_flags', flags);
    
    input.value = '';
    renderPerspectiveFlagsSettings();
}

function removePerspectiveFlag(flag) {
    const flags = project.settings.perspective_flags || [];
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('perspective_flags', newFlags);
    
    if (project.settings.default_perspective_flag === flag) {
        updateSetting('default_perspective_flag', null);
    }
    
    renderPerspectiveFlagsSettings();
}
```

### 4.6 Update Setting

```javascript
async function updateSetting(key, value) {
    // Update local state
    project.settings[key] = value;
    
    // Debounced save to server
    debouncedSaveSettings();
}

const debouncedSaveSettings = debounce(async () => {
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(project.settings)
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showNotification('Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        showNotification('Failed to save settings', 'error');
    }
}, 500);

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

---

## 5. API Endpoint

### 5.1 POST `/api/settings`

**Purpose:** Save all settings to project JSON

**Request Body:**
```json
{
  "skip_delete_confirmation": true,
  "quality_flags": ["bin", "review", "ok", "move"],
  "perspective_flags": ["close-up-day", "pan-day"],
  "visible_labels": ["color", "brand", "type"],
  "default_quality_flag": "review",
  "default_perspective_flag": null,
  "grid_size": 9
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings saved"
}
```

### 5.2 Backend

```python
@app.route('/api/settings', methods=['POST'])
def update_settings():
    new_settings = request.json
    
    # Validate
    valid_keys = [
        'skip_delete_confirmation',
        'quality_flags',
        'perspective_flags', 
        'visible_labels',
        'default_quality_flag',
        'default_perspective_flag',
        'grid_size'
    ]
    
    for key in new_settings:
        if key in valid_keys:
            project_manager.project_data['settings'][key] = new_settings[key]
    
    project_manager.project_data['updated'] = datetime.now().isoformat()
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'message': 'Settings saved'
    })
```

---

## 6. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-8.1 | Settings button opens modal | Click ⚙️, verify modal opens |
| AC-8.2 | Project info displayed | Verify name, directory, counts shown |
| AC-8.3 | Skip confirmation toggle works | Toggle, verify delete behavior changes |
| AC-8.4 | Grid size radio saves | Select 5×5, reload, verify saved |
| AC-8.5 | Visible labels checkboxes work | Uncheck "brand", verify hidden in grid |
| AC-8.6 | Can add quality flag | Type name, click Add, flag appears |
| AC-8.7 | Can remove quality flag | Click ✕, flag removed |
| AC-8.8 | Default quality flag dropdown works | Select "ok", verify new images get "ok" |
| AC-8.9 | Can add perspective flag | Type name, click Add, flag appears |
| AC-8.10 | Can remove perspective flag | Click ✕, flag removed |
| AC-8.11 | Settings saved to JSON | Change setting, check project JSON updated |
| AC-8.12 | Settings loaded on project open | Reload page, verify settings restored |

---

## 7. Keyboard Shortcut

```javascript
// Add to keyboard handler
case ',':  // Common settings shortcut
    openSettings();
    break;
```

---

## 8. Header with Project Name

```html
<header>
    <h1>
        🖼️ Image Review Tool - 
        <span id="project-title">vehicle_colors_v4</span>
    </h1>
    <!-- ... toolbar ... -->
</header>
```

```css
header h1 {
    font-size: 18px;
    font-weight: 500;
}

#project-title {
    color: #4a69bd;
}
```
