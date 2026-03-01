# Phase 6: Flags System - Quality & Perspective

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Implement a dual-category flag system with Quality Flags (for workflow status) and Perspective Flags (for image characteristics). Flags are stored in the project JSON and displayed on image cards.

---

## 1. Prerequisites
- Phase 1-5 complete
- Project JSON structure supports `quality_flags` and `perspective_flags` arrays per image

---

## 2. Flag Categories

### 2.1 Quality Flags (Workflow Status)

| Flag | Purpose | Color |
|------|---------|-------|
| `bin` | Mark for deletion / discard | Red `#e74c3c` |
| `review` | Needs review / uncertain | Orange `#f39c12` |
| `ok` | Approved / good to use | Green `#27ae60` |
| `move` | Mark for moving to another location | Blue `#3498db` |

### 2.2 Perspective Flags (Image Characteristics)

| Flag | Purpose | Color |
|------|---------|-------|
| `close-up-day` | Close shot, daytime | Teal `#1abc9c` |
| `close-up-night` | Close shot, nighttime | Dark Teal `#16a085` |
| `pan-day` | Panoramic view, daytime | Purple `#9b59b6` |
| `pan-night` | Panoramic view, nighttime | Dark Purple `#8e44ad` |
| `super_pan_day` | Wide panoramic, daytime | Pink `#e91e63` |
| `super_pan_night` | Wide panoramic, nighttime | Dark Pink `#c2185b` |
| `cropped-day` | Cropped image, daytime | Cyan `#00bcd4` |
| `cropped-night` | Cropped image, nighttime | Dark Cyan `#0097a7` |

---

## 3. UI Components

### 3.1 Flag Modal

```
┌──────────────────────────────────────────────────────────────┐
│                        🏷️ Set Flags                          │
│                  Image: 000000_ASH4662_1.jpg                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Quality Flags ─────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  [  ] bin      [●] review    [  ] ok      [  ] move    │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Perspective Flags ─────────────────────────────────────┐ │
│  │                                                         │ │
│  │  [●] close-up-day     [  ] close-up-night              │ │
│  │  [  ] pan-day         [  ] pan-night                   │ │
│  │  [  ] super_pan_day   [  ] super_pan_night             │ │
│  │  [  ] cropped-day     [  ] cropped-night               │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│                         [Cancel]    [Apply]                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Bulk Flag Modal

```
┌──────────────────────────────────────────────────────────────┐
│                     🏷️ Set Flags (Bulk)                      │
│                     Applying to 5 images                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Quality Flags ─────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Mode: ( ) Set  ( ) Add  (●) Remove                    │ │
│  │                                                         │ │
│  │  [  ] bin      [  ] review    [●] ok      [  ] move    │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Perspective Flags ─────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Mode: ( ) Set  (●) Add  ( ) Remove                    │ │
│  │                                                         │ │
│  │  [●] pan-day                                           │ │
│  │                                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│                         [Cancel]    [Apply to All]           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.3 Flag Modal HTML

```html
<!-- Flag Modal -->
<div id="flag-modal" class="modal hidden">
    <div class="modal-backdrop" onclick="closeFlagModal()"></div>
    <div class="modal-content flag-modal-content">
        <h2>🏷️ <span id="flag-modal-title">Set Flags</span></h2>
        <p id="flag-modal-subtitle" class="subtitle">Image: 000000_ASH4662_1.jpg</p>
        
        <!-- Quality Flags Section -->
        <div class="flag-section">
            <h3>Quality Flags</h3>
            
            <!-- Bulk mode selector (hidden for single) -->
            <div class="bulk-mode-selector hidden" id="quality-bulk-mode">
                <label><input type="radio" name="quality-mode" value="set" checked> Set</label>
                <label><input type="radio" name="quality-mode" value="add"> Add</label>
                <label><input type="radio" name="quality-mode" value="remove"> Remove</label>
            </div>
            
            <div class="flag-grid" id="quality-flags-grid">
                <!-- Generated by JS -->
            </div>
        </div>
        
        <!-- Perspective Flags Section -->
        <div class="flag-section">
            <h3>Perspective Flags</h3>
            
            <!-- Bulk mode selector (hidden for single) -->
            <div class="bulk-mode-selector hidden" id="perspective-bulk-mode">
                <label><input type="radio" name="perspective-mode" value="set" checked> Set</label>
                <label><input type="radio" name="perspective-mode" value="add"> Add</label>
                <label><input type="radio" name="perspective-mode" value="remove"> Remove</label>
            </div>
            
            <div class="flag-grid" id="perspective-flags-grid">
                <!-- Generated by JS -->
            </div>
        </div>
        
        <div class="modal-actions">
            <button class="btn-cancel" onclick="closeFlagModal()">Cancel</button>
            <button class="btn-apply" id="apply-flags-btn" onclick="applyFlags()">Apply</button>
        </div>
    </div>
</div>
```

### 3.4 CSS

```css
.flag-modal-content {
    max-width: 500px;
    padding: 24px;
}

.flag-modal-content h2 {
    margin-bottom: 4px;
}

.subtitle {
    color: #888;
    font-size: 14px;
    margin-bottom: 20px;
}

.flag-section {
    background: #1a1a2e;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.flag-section h3 {
    margin-bottom: 12px;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
}

.flag-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.flag-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: #0f0f23;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.flag-checkbox:hover {
    background: #16213e;
}

.flag-checkbox input {
    width: 18px;
    height: 18px;
    cursor: pointer;
}

.flag-checkbox .flag-label {
    flex: 1;
    font-size: 13px;
}

.flag-checkbox .flag-color {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.flag-checkbox.checked {
    background: rgba(74, 105, 189, 0.2);
    outline: 2px solid #4a69bd;
}

/* Bulk mode selector */
.bulk-mode-selector {
    display: flex;
    gap: 16px;
    margin-bottom: 12px;
    padding: 8px;
    background: #0f0f23;
    border-radius: 6px;
}

.bulk-mode-selector label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    cursor: pointer;
}

/* Flag pills on cards */
.flag-pill {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
    white-space: nowrap;
}

/* Quality flag colors */
.flag-pill.flag-bin { background: #e74c3c; color: white; }
.flag-pill.flag-review { background: #f39c12; color: white; }
.flag-pill.flag-ok { background: #27ae60; color: white; }
.flag-pill.flag-move { background: #3498db; color: white; }

/* Perspective flag colors */
.flag-pill.flag-close-up-day { background: #1abc9c; color: white; }
.flag-pill.flag-close-up-night { background: #16a085; color: white; }
.flag-pill.flag-pan-day { background: #9b59b6; color: white; }
.flag-pill.flag-pan-night { background: #8e44ad; color: white; }
.flag-pill.flag-super_pan_day { background: #e91e63; color: white; }
.flag-pill.flag-super_pan_night { background: #c2185b; color: white; }
.flag-pill.flag-cropped-day { background: #00bcd4; color: white; }
.flag-pill.flag-cropped-night { background: #0097a7; color: white; }
```

---

## 4. JavaScript Implementation

### 4.1 Flag Configuration

```javascript
// Flag definitions
const FLAG_CONFIG = {
    quality: {
        flags: ['bin', 'review', 'ok', 'move'],
        colors: {
            'bin': '#e74c3c',
            'review': '#f39c12',
            'ok': '#27ae60',
            'move': '#3498db'
        }
    },
    perspective: {
        flags: [
            'close-up-day', 'close-up-night',
            'pan-day', 'pan-night',
            'super_pan_day', 'super_pan_night',
            'cropped-day', 'cropped-night'
        ],
        colors: {
            'close-up-day': '#1abc9c',
            'close-up-night': '#16a085',
            'pan-day': '#9b59b6',
            'pan-night': '#8e44ad',
            'super_pan_day': '#e91e63',
            'super_pan_night': '#c2185b',
            'cropped-day': '#00bcd4',
            'cropped-night': '#0097a7'
        }
    }
};
```

### 4.2 Flag Modal State

```javascript
// Flag modal state
const flagModalState = {
    isOpen: false,
    isBulk: false,
    seqIds: [],
    originalQualityFlags: [],
    originalPerspectiveFlags: [],
    selectedQualityFlags: new Set(),
    selectedPerspectiveFlags: new Set()
};
```

### 4.3 Open Flag Modal

```javascript
// Open for single image
function openFlagModal(seqId) {
    const image = findImageBySeqId(seqId);
    if (!image) return;
    
    flagModalState.isOpen = true;
    flagModalState.isBulk = false;
    flagModalState.seqIds = [seqId];
    
    // Load current flags
    flagModalState.selectedQualityFlags = new Set(image.quality_flags || []);
    flagModalState.selectedPerspectiveFlags = new Set(image.perspective_flags || []);
    
    // Update UI
    document.getElementById('flag-modal-title').textContent = 'Set Flags';
    document.getElementById('flag-modal-subtitle').textContent = `Image: ${image.filename}`;
    document.getElementById('apply-flags-btn').textContent = 'Apply';
    
    // Hide bulk mode selectors
    document.getElementById('quality-bulk-mode').classList.add('hidden');
    document.getElementById('perspective-bulk-mode').classList.add('hidden');
    
    renderFlagCheckboxes();
    document.getElementById('flag-modal').classList.remove('hidden');
}

// Open for bulk
function openBulkFlagModal() {
    const selectedIds = getSelectedIds();
    if (selectedIds.length === 0) return;
    
    flagModalState.isOpen = true;
    flagModalState.isBulk = true;
    flagModalState.seqIds = selectedIds;
    
    // Clear selections for bulk (user chooses what to apply)
    flagModalState.selectedQualityFlags = new Set();
    flagModalState.selectedPerspectiveFlags = new Set();
    
    // Update UI
    document.getElementById('flag-modal-title').textContent = 'Set Flags (Bulk)';
    document.getElementById('flag-modal-subtitle').textContent = `Applying to ${selectedIds.length} images`;
    document.getElementById('apply-flags-btn').textContent = 'Apply to All';
    
    // Show bulk mode selectors
    document.getElementById('quality-bulk-mode').classList.remove('hidden');
    document.getElementById('perspective-bulk-mode').classList.remove('hidden');
    
    renderFlagCheckboxes();
    document.getElementById('flag-modal').classList.remove('hidden');
}

function closeFlagModal() {
    document.getElementById('flag-modal').classList.add('hidden');
    flagModalState.isOpen = false;
}
```

### 4.4 Render Flag Checkboxes

```javascript
function renderFlagCheckboxes() {
    // Quality flags
    const qualityGrid = document.getElementById('quality-flags-grid');
    qualityGrid.innerHTML = '';
    
    FLAG_CONFIG.quality.flags.forEach(flag => {
        const isChecked = flagModalState.selectedQualityFlags.has(flag);
        const color = FLAG_CONFIG.quality.colors[flag];
        
        qualityGrid.innerHTML += `
            <label class="flag-checkbox ${isChecked ? 'checked' : ''}" data-flag="${flag}">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                       onchange="toggleQualityFlag('${flag}', this.checked)">
                <span class="flag-label">${flag}</span>
                <span class="flag-color" style="background: ${color}"></span>
            </label>
        `;
    });
    
    // Perspective flags
    const perspectiveGrid = document.getElementById('perspective-flags-grid');
    perspectiveGrid.innerHTML = '';
    
    FLAG_CONFIG.perspective.flags.forEach(flag => {
        const isChecked = flagModalState.selectedPerspectiveFlags.has(flag);
        const color = FLAG_CONFIG.perspective.colors[flag];
        
        perspectiveGrid.innerHTML += `
            <label class="flag-checkbox ${isChecked ? 'checked' : ''}" data-flag="${flag}">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                       onchange="togglePerspectiveFlag('${flag}', this.checked)">
                <span class="flag-label">${flag}</span>
                <span class="flag-color" style="background: ${color}"></span>
            </label>
        `;
    });
}

function toggleQualityFlag(flag, isChecked) {
    if (isChecked) {
        flagModalState.selectedQualityFlags.add(flag);
    } else {
        flagModalState.selectedQualityFlags.delete(flag);
    }
    
    // Update visual
    const checkbox = document.querySelector(`#quality-flags-grid .flag-checkbox[data-flag="${flag}"]`);
    checkbox?.classList.toggle('checked', isChecked);
}

function togglePerspectiveFlag(flag, isChecked) {
    if (isChecked) {
        flagModalState.selectedPerspectiveFlags.add(flag);
    } else {
        flagModalState.selectedPerspectiveFlags.delete(flag);
    }
    
    // Update visual
    const checkbox = document.querySelector(`#perspective-flags-grid .flag-checkbox[data-flag="${flag}"]`);
    checkbox?.classList.toggle('checked', isChecked);
}
```

### 4.5 Apply Flags

```javascript
async function applyFlags() {
    const seqIds = flagModalState.seqIds;
    const qualityFlags = Array.from(flagModalState.selectedQualityFlags);
    const perspectiveFlags = Array.from(flagModalState.selectedPerspectiveFlags);
    
    let endpoint, body;
    
    if (flagModalState.isBulk) {
        // Get bulk mode
        const qualityMode = document.querySelector('input[name="quality-mode"]:checked')?.value || 'set';
        const perspectiveMode = document.querySelector('input[name="perspective-mode"]:checked')?.value || 'set';
        
        endpoint = '/api/flags/bulk';
        body = {
            seq_ids: seqIds,
            quality_flags: qualityFlags,
            quality_mode: qualityMode,
            perspective_flags: perspectiveFlags,
            perspective_mode: perspectiveMode
        };
    } else {
        endpoint = `/api/image/${seqIds[0]}/flags`;
        body = {
            quality_flags: qualityFlags,
            perspective_flags: perspectiveFlags
        };
    }
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI for affected cards
            seqIds.forEach(seqId => {
                updateCardFlags(seqId, data.data.updated_flags?.[seqId] || {
                    quality_flags: qualityFlags,
                    perspective_flags: perspectiveFlags
                });
            });
            
            closeFlagModal();
            showNotification(`Flags updated for ${seqIds.length} image(s)`);
        } else {
            showNotification(`Failed to update flags: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to apply flags:', error);
        showNotification('Failed to apply flags', 'error');
    }
}
```

### 4.6 Update Card Flags Display

```javascript
function updateCardFlags(seqId, flags) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    const flagsContainer = card.querySelector('.card-flags');
    if (!flagsContainer) return;
    
    flagsContainer.innerHTML = '';
    
    // Quality flags
    (flags.quality_flags || []).forEach(flag => {
        const pill = document.createElement('span');
        pill.className = `flag-pill flag-${flag}`;
        pill.textContent = flag;
        flagsContainer.appendChild(pill);
    });
    
    // Perspective flags
    (flags.perspective_flags || []).forEach(flag => {
        const pill = document.createElement('span');
        pill.className = `flag-pill flag-${flag.replace(/_/g, '-')}`;
        pill.textContent = flag;
        flagsContainer.appendChild(pill);
    });
}
```

### 4.7 Quick Flag Keyboard Shortcuts

```javascript
// Q key: Cycle quality flag on hovered/selected image
function cycleQualityFlag() {
    const hoveredCard = document.querySelector('.image-card:hover');
    const seqId = hoveredCard 
        ? parseInt(hoveredCard.dataset.seqId)
        : (selectionState.selected.size === 1 
            ? Array.from(selectionState.selected)[0] 
            : null);
    
    if (!seqId) return;
    
    const image = findImageBySeqId(seqId);
    if (!image) return;
    
    const currentFlags = image.quality_flags || [];
    const order = ['bin', 'review', 'ok', 'move'];
    
    let nextFlag;
    if (currentFlags.length === 0) {
        nextFlag = order[0];
    } else {
        const lastFlag = currentFlags[currentFlags.length - 1];
        const currentIdx = order.indexOf(lastFlag);
        nextFlag = order[(currentIdx + 1) % order.length];
    }
    
    // Quick apply single flag
    applyQuickFlag(seqId, 'quality', [nextFlag]);
}

// P key: Open perspective flag modal
function quickPerspectiveFlag() {
    const hoveredCard = document.querySelector('.image-card:hover');
    const seqId = hoveredCard 
        ? parseInt(hoveredCard.dataset.seqId)
        : null;
    
    if (seqId) {
        openFlagModal(seqId);
    } else if (selectionState.selected.size > 0) {
        openBulkFlagModal();
    }
}

async function applyQuickFlag(seqId, type, flags) {
    try {
        const body = type === 'quality' 
            ? { quality_flags: flags, perspective_flags: null }
            : { quality_flags: null, perspective_flags: flags };
        
        const response = await fetch(`/api/image/${seqId}/flags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateCardFlags(seqId, data.data);
        }
    } catch (error) {
        console.error('Quick flag failed:', error);
    }
}
```

---

## 5. API Endpoints

### 5.1 POST `/api/image/<seq_id>/flags`

**Purpose:** Set flags for single image

**Request Body:**
```json
{
  "quality_flags": ["ok"],
  "perspective_flags": ["pan-day"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "seq_id": 1,
    "quality_flags": ["ok"],
    "perspective_flags": ["pan-day"]
  }
}
```

### 5.2 POST `/api/flags/bulk`

**Purpose:** Apply flags to multiple images with mode

**Request Body:**
```json
{
  "seq_ids": [1, 2, 3, 4, 5],
  "quality_flags": ["ok"],
  "quality_mode": "set",
  "perspective_flags": ["pan-day"],
  "perspective_mode": "add"
}
```

**Modes:**
- `set`: Replace existing flags with new ones
- `add`: Add new flags to existing
- `remove`: Remove specified flags

**Response:**
```json
{
  "success": true,
  "data": {
    "updated_count": 5,
    "updated_flags": {
      "1": {"quality_flags": ["ok"], "perspective_flags": ["close-up-day", "pan-day"]},
      "2": {"quality_flags": ["ok"], "perspective_flags": ["pan-day"]}
    }
  }
}
```

### 5.3 Backend Logic

```python
@app.route('/api/image/<int:seq_id>/flags', methods=['POST'])
def set_image_flags(seq_id: int):
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    data = request.json
    
    if data.get('quality_flags') is not None:
        image['quality_flags'] = data['quality_flags']
    
    if data.get('perspective_flags') is not None:
        image['perspective_flags'] = data['perspective_flags']
    
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'quality_flags': image.get('quality_flags', []),
            'perspective_flags': image.get('perspective_flags', [])
        }
    })


@app.route('/api/flags/bulk', methods=['POST'])
def set_bulk_flags():
    data = request.json
    seq_ids = data.get('seq_ids', [])
    
    quality_flags = data.get('quality_flags', [])
    quality_mode = data.get('quality_mode', 'set')
    
    perspective_flags = data.get('perspective_flags', [])
    perspective_mode = data.get('perspective_mode', 'set')
    
    updated_flags = {}
    
    for seq_id in seq_ids:
        image = find_image_by_seq_id(seq_id)
        if not image:
            continue
        
        # Apply quality flags
        if quality_flags:
            current_quality = set(image.get('quality_flags', []))
            
            if quality_mode == 'set':
                image['quality_flags'] = quality_flags
            elif quality_mode == 'add':
                image['quality_flags'] = list(current_quality.union(quality_flags))
            elif quality_mode == 'remove':
                image['quality_flags'] = list(current_quality - set(quality_flags))
        
        # Apply perspective flags
        if perspective_flags:
            current_perspective = set(image.get('perspective_flags', []))
            
            if perspective_mode == 'set':
                image['perspective_flags'] = perspective_flags
            elif perspective_mode == 'add':
                image['perspective_flags'] = list(current_perspective.union(perspective_flags))
            elif perspective_mode == 'remove':
                image['perspective_flags'] = list(current_perspective - set(perspective_flags))
        
        updated_flags[seq_id] = {
            'quality_flags': image.get('quality_flags', []),
            'perspective_flags': image.get('perspective_flags', [])
        }
    
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'data': {
            'updated_count': len(updated_flags),
            'updated_flags': updated_flags
        }
    })
```

---

## 6. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `F` | Open flag modal for hovered/selected image(s) |
| `Q` | Cycle quality flag (bin → review → ok → move) |
| `P` | Open perspective flag modal |

```javascript
// Add to keyboard handler
case 'f':
case 'F':
    if (selectionState.selected.size > 0) {
        openBulkFlagModal();
    } else {
        const hovered = document.querySelector('.image-card:hover');
        if (hovered) {
            openFlagModal(parseInt(hovered.dataset.seqId));
        }
    }
    break;

case 'q':
case 'Q':
    cycleQualityFlag();
    break;

case 'p':
case 'P':
    quickPerspectiveFlag();
    break;
```

---

## 7. Default Flags Behavior

When an image has no flags set, apply defaults from project settings:

```javascript
// When loading images, apply defaults if no flags
function applyDefaultFlags(image) {
    const settings = project.settings;
    
    if (!image.quality_flags || image.quality_flags.length === 0) {
        if (settings.default_quality_flag) {
            image.quality_flags = [settings.default_quality_flag];
        }
    }
    
    if (!image.perspective_flags || image.perspective_flags.length === 0) {
        if (settings.default_perspective_flag) {
            image.perspective_flags = [settings.default_perspective_flag];
        }
    }
    
    return image;
}
```

---

## 8. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-6.1 | Flag button opens modal | Click 🏷️, verify modal opens |
| AC-6.2 | Modal shows Quality and Perspective sections | Verify both sections present |
| AC-6.3 | Current flags pre-selected | Image with "ok" flag, verify "ok" checked |
| AC-6.4 | Can select multiple flags per category | Check bin and review, both selected |
| AC-6.5 | Apply saves to project JSON | Apply flags, check JSON file updated |
| AC-6.6 | Flags display on card | Set flags, verify pills appear on card |
| AC-6.7 | Quality flags have correct colors | "ok" is green, "bin" is red |
| AC-6.8 | Bulk flag affects all selected | Select 5, bulk flag, all 5 updated |
| AC-6.9 | Bulk mode "Add" adds to existing | Image has "review", add "ok", now has both |
| AC-6.10 | Bulk mode "Remove" removes specified | Image has "ok", remove "ok", now empty |
| AC-6.11 | Q key cycles quality flag | Press Q, flag cycles |
| AC-6.12 | F key opens flag modal | Press F with selection, modal opens |

---

## 9. Integration with Filter (Future)

Prepared for future filtering by flag:

```javascript
// Filter state (Phase 9 enhancement)
const filterState = {
    qualityFilter: null,    // null = show all, or specific flag
    perspectiveFilter: null
};

function filterByQualityFlag(flag) {
    filterState.qualityFilter = flag;
    loadImages();  // API would filter server-side
}
```
