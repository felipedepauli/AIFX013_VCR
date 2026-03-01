# Phase 4: Per-Image Controls

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Add interactive controls to each image card: selection checkbox, expand button (open wider), delete button, and flag button. Implement selection system for batch operations.

---

## 1. Prerequisites
- Phase 1-3 complete
- Grid displaying images with labels

---

## 2. Control Buttons

| Button | Icon | Position | Action |
|--------|------|----------|--------|
| Select | ☐ / ☑ | Top-left | Toggle image selection |
| Expand | 🔍 | Top-right area | Open full-size modal |
| Delete | 🗑️ | Top-right area | Delete image (Phase 5) |
| Flag | 🏷️ | Top-right area | Open flag modal (Phase 6) |

---

## 3. UI Components

### 3.1 Card Controls Layout

```
┌─────────────────────────────────────────┐
│ [☐]                    [🔍] [🗑️] [🏷️] │  ← Controls bar
│                                         │
│                                         │
│              [Image]                    │
│                                         │
│           ┌─────────┐                   │
│           │ silver  │                   │
│           │ honda   │                   │
│           └─────────┘                   │
│                                         │
│ [review] [pan-day]                      │  ← Flags bar
└─────────────────────────────────────────┘
```

### 3.2 HTML Structure

```html
<div class="image-card" data-seq-id="1">
    <!-- Controls Bar (appears on hover) -->
    <div class="card-controls">
        <div class="controls-left">
            <label class="select-checkbox-wrapper">
                <input type="checkbox" class="select-checkbox"
                       onchange="toggleSelect(1, this.checked)">
                <span class="checkmark"></span>
            </label>
        </div>
        <div class="controls-right">
            <button class="btn-control btn-expand" 
                    onclick="openWider(1)" title="Open Wider (Space)">
                🔍
            </button>
            <button class="btn-control btn-delete" 
                    onclick="deleteImage(1)" title="Delete (Del)">
                🗑️
            </button>
            <button class="btn-control btn-flag" 
                    onclick="openFlagModal(1)" title="Flag (F)">
                🏷️
            </button>
        </div>
    </div>
    
    <!-- Image Container -->
    <div class="image-container">
        <img src="..." alt="...">
        <div class="label-overlay">...</div>
    </div>
    
    <!-- Flags Bar -->
    <div class="card-flags">
        <span class="flag-pill flag-quality">review</span>
        <span class="flag-pill flag-perspective">pan-day</span>
    </div>
    
    <!-- Selection overlay (visual indicator) -->
    <div class="selection-overlay"></div>
</div>
```

### 3.3 CSS Styles

```css
/* Card Controls Bar */
.card-controls {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    padding: 8px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    background: linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 100%);
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 20;
}

.image-card:hover .card-controls {
    opacity: 1;
}

/* Keep controls visible when selected */
.image-card.selected .card-controls {
    opacity: 1;
}

.controls-left, .controls-right {
    display: flex;
    gap: 4px;
}

/* Custom Checkbox */
.select-checkbox-wrapper {
    display: flex;
    align-items: center;
    cursor: pointer;
}

.select-checkbox {
    position: absolute;
    opacity: 0;
    cursor: pointer;
    height: 0;
    width: 0;
}

.checkmark {
    width: 22px;
    height: 22px;
    background: rgba(255, 255, 255, 0.2);
    border: 2px solid rgba(255, 255, 255, 0.6);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.checkmark::after {
    content: '✓';
    color: white;
    font-size: 14px;
    display: none;
}

.select-checkbox:checked ~ .checkmark {
    background: #4a69bd;
    border-color: #4a69bd;
}

.select-checkbox:checked ~ .checkmark::after {
    display: block;
}

.checkmark:hover {
    background: rgba(74, 105, 189, 0.5);
    border-color: #4a69bd;
}

/* Control Buttons */
.btn-control {
    width: 32px;
    height: 32px;
    padding: 0;
    border: none;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.5);
    color: white;
    font-size: 16px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.btn-control:hover {
    transform: scale(1.1);
}

.btn-expand:hover {
    background: rgba(74, 105, 189, 0.8);
}

.btn-delete:hover {
    background: rgba(231, 76, 60, 0.8);
}

.btn-flag:hover {
    background: rgba(39, 174, 96, 0.8);
}

/* Selected State */
.image-card.selected {
    outline: 3px solid #4a69bd;
    outline-offset: -3px;
}

.selection-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(74, 105, 189, 0.15);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.2s;
}

.image-card.selected .selection-overlay {
    opacity: 1;
}

/* Flags Bar */
.card-flags {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 6px 8px;
    background: linear-gradient(to top, rgba(0,0,0,0.7) 0%, transparent 100%);
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    min-height: 30px;
}

.flag-pill {
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: 500;
}

.flag-quality {
    background: #3498db;
    color: white;
}

.flag-perspective {
    background: #27ae60;
    color: white;
}
```

---

## 4. Selection System

### 4.1 State Management

```javascript
// Selection state
const selectionState = {
    selected: new Set(),  // Set of seq_ids
    lastClicked: null     // For shift-click range selection
};

// Get selected count
function getSelectedCount() {
    return selectionState.selected.size;
}

// Get selected seq_ids as array
function getSelectedIds() {
    return Array.from(selectionState.selected);
}
```

### 4.2 Selection Functions

```javascript
// Toggle single image selection
function toggleSelect(seqId, isSelected) {
    if (isSelected) {
        selectionState.selected.add(seqId);
    } else {
        selectionState.selected.delete(seqId);
    }
    
    selectionState.lastClicked = seqId;
    
    updateCardSelectionUI(seqId, isSelected);
    updateSelectedCount();
    updateBulkActionsVisibility();
}

// Select with shift-click (range selection)
function selectWithShift(seqId) {
    if (selectionState.lastClicked === null) {
        toggleSelect(seqId, true);
        return;
    }
    
    // Get all visible seq_ids in order
    const visibleIds = Array.from(document.querySelectorAll('.image-card'))
        .map(card => parseInt(card.dataset.seqId));
    
    const lastIdx = visibleIds.indexOf(selectionState.lastClicked);
    const currentIdx = visibleIds.indexOf(seqId);
    
    if (lastIdx === -1 || currentIdx === -1) {
        toggleSelect(seqId, true);
        return;
    }
    
    // Select range
    const start = Math.min(lastIdx, currentIdx);
    const end = Math.max(lastIdx, currentIdx);
    
    for (let i = start; i <= end; i++) {
        const id = visibleIds[i];
        selectionState.selected.add(id);
        updateCardSelectionUI(id, true);
    }
    
    updateSelectedCount();
    updateBulkActionsVisibility();
}

// Update card UI for selection state
function updateCardSelectionUI(seqId, isSelected) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    card.classList.toggle('selected', isSelected);
    
    const checkbox = card.querySelector('.select-checkbox');
    if (checkbox) {
        checkbox.checked = isSelected;
    }
}

// Select all on current page
function selectAll() {
    document.querySelectorAll('.image-card').forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        selectionState.selected.add(seqId);
        updateCardSelectionUI(seqId, true);
    });
    
    updateSelectedCount();
    updateBulkActionsVisibility();
}

// Deselect all
function deselectAll() {
    selectionState.selected.forEach(seqId => {
        updateCardSelectionUI(seqId, false);
    });
    
    selectionState.selected.clear();
    selectionState.lastClicked = null;
    
    updateSelectedCount();
    updateBulkActionsVisibility();
}

// Update selected count display
function updateSelectedCount() {
    const countEl = document.getElementById('selected-count');
    if (countEl) {
        countEl.textContent = selectionState.selected.size;
    }
}

// Show/hide bulk action buttons based on selection
function updateBulkActionsVisibility() {
    const hasSelection = selectionState.selected.size > 0;
    
    document.querySelectorAll('.bulk-action-btn').forEach(btn => {
        btn.disabled = !hasSelection;
        btn.style.opacity = hasSelection ? '1' : '0.5';
    });
}
```

### 4.3 Card Click Handlers

```javascript
// Add click handler to image cards
function setupCardClickHandlers() {
    document.getElementById('image-grid').addEventListener('click', (e) => {
        const card = e.target.closest('.image-card');
        if (!card) return;
        
        // Ignore if clicking on controls
        if (e.target.closest('.card-controls') || 
            e.target.closest('.btn-control')) {
            return;
        }
        
        const seqId = parseInt(card.dataset.seqId);
        
        if (e.shiftKey) {
            // Shift-click: range select
            selectWithShift(seqId);
        } else if (e.ctrlKey || e.metaKey) {
            // Ctrl/Cmd-click: toggle individual
            toggleSelect(seqId, !selectionState.selected.has(seqId));
        } else {
            // Regular click on image: could open wider or do nothing
            // (depends on preference)
        }
    });
}
```

---

## 5. Open Wider Modal

### 5.1 Modal Structure

```html
<!-- Full-size Image Modal -->
<div id="image-modal" class="modal hidden">
    <div class="modal-backdrop" onclick="closeImageModal()"></div>
    <div class="modal-content image-modal-content">
        <button class="modal-close" onclick="closeImageModal()">✕</button>
        <div class="modal-nav">
            <button class="nav-btn" onclick="modalPrevImage()">◀</button>
            <button class="nav-btn" onclick="modalNextImage()">▶</button>
        </div>
        <div class="modal-image-container">
            <img id="modal-image" src="" alt="">
            <div id="modal-labels" class="label-overlay">
                <!-- Labels rendered here -->
            </div>
        </div>
        <div class="modal-info">
            <span id="modal-filename"></span>
            <span id="modal-seq-id"></span>
        </div>
    </div>
</div>
```

### 5.2 Modal CSS

```css
.image-modal-content {
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    background: #16213e;
    border-radius: 12px;
    overflow: hidden;
}

.modal-close {
    position: absolute;
    top: 16px;
    right: 16px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    z-index: 10;
}

.modal-close:hover {
    background: rgba(231, 76, 60, 0.8);
}

.modal-nav {
    position: absolute;
    top: 50%;
    left: 0;
    right: 0;
    transform: translateY(-50%);
    display: flex;
    justify-content: space-between;
    padding: 0 16px;
    pointer-events: none;
    z-index: 10;
}

.nav-btn {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: rgba(0, 0, 0, 0.5);
    border: none;
    color: white;
    font-size: 24px;
    cursor: pointer;
    pointer-events: auto;
    transition: all 0.2s;
}

.nav-btn:hover {
    background: rgba(74, 105, 189, 0.8);
    transform: scale(1.1);
}

.modal-image-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-image-container img {
    max-width: 90vw;
    max-height: 80vh;
    object-fit: contain;
}

.modal-info {
    padding: 12px 16px;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: space-between;
    color: #888;
    font-size: 14px;
}
```

### 5.3 Modal JavaScript

```javascript
// Modal state
let modalState = {
    isOpen: false,
    currentSeqId: null,
    visibleSeqIds: []  // All seq_ids from current page
};

// Open image in modal
async function openWider(seqId) {
    modalState.currentSeqId = seqId;
    modalState.visibleSeqIds = Array.from(document.querySelectorAll('.image-card'))
        .map(card => parseInt(card.dataset.seqId));
    
    await loadModalImage(seqId);
    
    document.getElementById('image-modal').classList.remove('hidden');
    modalState.isOpen = true;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

// Load full-size image
async function loadModalImage(seqId) {
    const modalImg = document.getElementById('modal-image');
    const filenameEl = document.getElementById('modal-filename');
    const seqIdEl = document.getElementById('modal-seq-id');
    
    // Show loading state
    modalImg.src = '';
    modalImg.alt = 'Loading...';
    
    try {
        const response = await fetch(`/api/image/${seqId}/full`);
        const data = await response.json();
        
        if (data.success) {
            modalImg.src = data.data.image;
            modalImg.alt = data.data.filename;
            filenameEl.textContent = data.data.filename;
            seqIdEl.textContent = `#${seqId}`;
            
            // Render labels
            await renderModalLabels(seqId);
        }
    } catch (error) {
        console.error('Failed to load full image:', error);
    }
}

// Navigate in modal
function modalPrevImage() {
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx > 0) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx - 1];
        loadModalImage(modalState.currentSeqId);
    }
}

function modalNextImage() {
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx < modalState.visibleSeqIds.length - 1) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx + 1];
        loadModalImage(modalState.currentSeqId);
    }
}

// Close modal
function closeImageModal() {
    document.getElementById('image-modal').classList.add('hidden');
    modalState.isOpen = false;
    document.body.style.overflow = '';
}

// Render labels in modal
async function renderModalLabels(seqId) {
    const labelData = await loadLabels(seqId);
    const overlay = document.getElementById('modal-labels');
    
    if (!overlay || !labelData || !labelData.has_labels) {
        overlay.innerHTML = '';
        return;
    }
    
    // Similar to grid labels but larger font
    overlay.innerHTML = '';
    
    labelData.objects.forEach((obj, idx) => {
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'object-labels modal-labels';
        labelsDiv.style.left = `${obj.center_percent.x}%`;
        labelsDiv.style.top = `${obj.center_percent.y}%`;
        
        visibleLabels.forEach(labelName => {
            const value = obj.labels[labelName];
            const labelSpan = document.createElement('span');
            labelSpan.className = 'label-line';
            labelSpan.textContent = value || 'NULL';
            if (!value) labelSpan.classList.add('null');
            
            labelsDiv.appendChild(labelSpan);
        });
        
        overlay.appendChild(labelsDiv);
    });
}
```

---

## 6. API Endpoints

### 6.1 GET `/api/image/<seq_id>/full`

**Purpose:** Get full-resolution image

**Response:**
```json
{
  "success": true,
  "data": {
    "seq_id": 1,
    "filename": "000000_ASH4662_1.jpg",
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "width": 1160,
    "height": 1160
  }
}
```

**Backend:**
```python
@app.route('/api/image/<int:seq_id>/full')
def get_full_image(seq_id: int):
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    img_path = Path(project_manager.project_data['directory']) / image['filename']
    
    try:
        with Image.open(img_path) as img:
            # Convert to RGB
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            width, height = img.size
            
            # Resize if very large (optional, for performance)
            max_dim = 2000
            if max(width, height) > max_dim:
                ratio = max_dim / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                width, height = new_size
            
            # Encode
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=90)
            base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'data': {
                    'seq_id': seq_id,
                    'filename': image['filename'],
                    'image': f"data:image/jpeg;base64,{base64_str}",
                    'width': width,
                    'height': height
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

---

## 7. Keyboard Shortcuts

```javascript
// Add to existing keyboard handler
document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    // Modal-specific shortcuts
    if (modalState.isOpen) {
        switch (e.key) {
            case 'Escape':
                closeImageModal();
                break;
            case 'ArrowLeft':
                modalPrevImage();
                e.preventDefault();
                break;
            case 'ArrowRight':
                modalNextImage();
                e.preventDefault();
                break;
        }
        return;  // Don't process other shortcuts when modal open
    }
    
    // Grid shortcuts
    switch (e.key) {
        case 'a':
        case 'A':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                selectAll();
            } else {
                selectAll();
            }
            break;
        case 'd':
        case 'D':
            deselectAll();
            break;
        case 'Escape':
            deselectAll();
            break;
        case ' ':  // Space to open hovered image
            e.preventDefault();
            const hoveredCard = document.querySelector('.image-card:hover');
            if (hoveredCard) {
                openWider(parseInt(hoveredCard.dataset.seqId));
            }
            break;
    }
});
```

---

## 8. Toolbar Bulk Actions

### 8.1 Toolbar HTML

```html
<div class="toolbar">
    <div class="grid-selector">
        <!-- Grid size buttons -->
    </div>
    
    <div class="label-dropdown">
        <!-- Label toggles -->
    </div>
    
    <div class="bulk-actions">
        <button class="bulk-action-btn" onclick="deleteSelectedImages()" disabled>
            🗑️ Delete Selected (<span class="selected-count-inline">0</span>)
        </button>
        <button class="bulk-action-btn" onclick="openBulkFlagModal()" disabled>
            🏷️ Flag Selected
        </button>
    </div>
    
    <button class="settings-btn" onclick="openSettings()">⚙️</button>
</div>
```

### 8.2 CSS

```css
.bulk-actions {
    display: flex;
    gap: 8px;
    margin-left: auto;
}

.bulk-action-btn {
    padding: 8px 16px;
    background: #333;
    border: 1px solid #444;
    border-radius: 6px;
    color: #eee;
    cursor: pointer;
    transition: all 0.2s;
}

.bulk-action-btn:hover:not(:disabled) {
    background: #444;
    border-color: #555;
}

.bulk-action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

---

## 9. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-4.1 | Controls appear on hover | Hover card, verify controls visible |
| AC-4.2 | Checkbox toggles selection | Click checkbox, verify selected state |
| AC-4.3 | Selected card has visual indicator | Select card, verify outline/overlay |
| AC-4.4 | Shift-click selects range | Select card 1, shift-click card 5, verify 1-5 selected |
| AC-4.5 | Ctrl-click toggles individual | Ctrl-click selected card, verify deselected |
| AC-4.6 | Select All selects current page | Press A, verify all cards selected |
| AC-4.7 | Deselect All clears selection | Press D, verify all deselected |
| AC-4.8 | Selected count updates in footer | Select 3 images, verify "Selected: 3" |
| AC-4.9 | Open Wider shows modal | Click 🔍, verify modal opens |
| AC-4.10 | Modal shows full-size image | Verify image larger than thumbnail |
| AC-4.11 | Modal navigation works | Click ◀/▶, image changes |
| AC-4.12 | Escape closes modal | Press Escape, modal closes |
| AC-4.13 | Bulk buttons enabled when selection exists | Select image, buttons become enabled |

---

## 10. Edge Cases

| Case | Handling |
|------|----------|
| No selection | Bulk action buttons disabled |
| All page selected, navigate | Selection preserved (if in-memory) or cleared |
| Delete while modal open | Close modal, remove from grid |
| Very large image in modal | Resize to max viewport size |
| Selection across page change | Clear or preserve (configurable) |
