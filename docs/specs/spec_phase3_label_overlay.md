# Phase 3: Label Overlay System

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Display object labels directly on images within the grid. Labels are read from per-image JSON files and rendered at the center of bounding boxes. Users can toggle which labels are visible.

---

## 1. Prerequisites
- Phase 1 complete (project loaded)
- Phase 2 complete (grid rendering works)
- Per-image JSON files exist with label data

---

## 2. Label JSON Structure (Input)

**File:** `{image_name}.json` (same directory as image)

```json
[
  {
    "rect": [1, 580, 562, 563],
    "color": "silver",
    "brand": "honda",
    "model": "city",
    "label": "car",
    "type": "auto",
    "sub_type": "au - sedan compacto",
    "lp_coords": ""
  },
  {
    "rect": [600, 100, 200, 180],
    "color": "white",
    "brand": "toyota",
    "model": "corolla",
    "label": "car",
    "type": "auto",
    "sub_type": "au - sedan compacto",
    "lp_coords": ""
  }
]
```

**Bounding Box Format:**
- `rect`: `[x, y, width, height]` in pixels
- Origin: top-left corner of image
- Coordinates are in original image resolution

---

## 3. Available Labels

| Field | Description | Example |
|-------|-------------|---------|
| `color` | Vehicle color | "silver", "white", "black" |
| `brand` | Vehicle brand | "honda", "toyota", "ford" |
| `model` | Vehicle model | "city", "corolla", "focus" |
| `label` | Object type | "car", "truck", "bus" |
| `type` | Category | "auto", "moto" |
| `sub_type` | Detailed category | "au - sedan compacto" |
| `lp_coords` | License plate coords | "" or coordinates |

**Default Visible:** `color`, `brand`, `model`, `type`

---

## 4. UI Components

### 4.1 Label Toggle Dropdown

```
┌─────────────────────────────────────────────────────────┐
│ Labels: [▼ 4 shown]                                     │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  [✓] color                                              │
│  [✓] brand                                              │
│  [✓] model                                              │
│  [ ] label                                              │
│  [✓] type                                               │
│  [ ] sub_type                                           │
│  [ ] lp_coords                                          │
├─────────────────────────────────────────────────────────┤
│  [Select All]  [Clear All]                              │
└─────────────────────────────────────────────────────────┘
```

**HTML:**
```html
<div class="label-dropdown">
    <button class="dropdown-toggle" onclick="toggleLabelDropdown()">
        Labels: <span id="label-count">4 shown</span> ▼
    </button>
    <div class="dropdown-menu hidden" id="label-menu">
        <label>
            <input type="checkbox" name="visible-label" value="color" checked 
                   onchange="toggleLabel('color', this.checked)">
            color
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="brand" checked
                   onchange="toggleLabel('brand', this.checked)">
            brand
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="model" checked
                   onchange="toggleLabel('model', this.checked)">
            model
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="label"
                   onchange="toggleLabel('label', this.checked)">
            label
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="type" checked
                   onchange="toggleLabel('type', this.checked)">
            type
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="sub_type"
                   onchange="toggleLabel('sub_type', this.checked)">
            sub_type
        </label>
        <label>
            <input type="checkbox" name="visible-label" value="lp_coords"
                   onchange="toggleLabel('lp_coords', this.checked)">
            lp_coords
        </label>
        <div class="dropdown-actions">
            <button onclick="selectAllLabels()">Select All</button>
            <button onclick="clearAllLabels()">Clear All</button>
        </div>
    </div>
</div>
```

**CSS:**
```css
.label-dropdown {
    position: relative;
}

.dropdown-toggle {
    padding: 8px 16px;
    background: #0f0f23;
    border: 1px solid #333;
    border-radius: 6px;
    color: #eee;
    cursor: pointer;
}

.dropdown-menu {
    position: absolute;
    top: 100%;
    left: 0;
    background: #16213e;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 8px;
    min-width: 200px;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.dropdown-menu.hidden {
    display: none;
}

.dropdown-menu label {
    display: block;
    padding: 6px 8px;
    cursor: pointer;
    border-radius: 4px;
}

.dropdown-menu label:hover {
    background: #1a1a2e;
}

.dropdown-actions {
    border-top: 1px solid #333;
    margin-top: 8px;
    padding-top: 8px;
    display: flex;
    gap: 8px;
}

.dropdown-actions button {
    flex: 1;
    padding: 6px;
    font-size: 12px;
}
```

### 4.2 Label Overlay on Image Card

```html
<div class="image-container">
    <img src="${thumbnail}" alt="${filename}">
    <div class="label-overlay">
        <!-- For each object in image -->
        <div class="object-labels" style="left: 50%; top: 70%;">
            <span class="label-line">silver</span>
            <span class="label-line">honda</span>
            <span class="label-line">city</span>
            <span class="label-line">auto</span>
        </div>
        <!-- Bounding box (optional) -->
        <div class="bbox" style="left: 0.1%; top: 50%; width: 48%; height: 48%;"></div>
    </div>
</div>
```

**CSS:**
```css
.label-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
}

.object-labels {
    position: absolute;
    transform: translate(-50%, -50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    pointer-events: auto;  /* Enable click for editing */
}

.label-line {
    background: rgba(0, 0, 0, 0.75);
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-family: monospace;
    white-space: nowrap;
    cursor: pointer;  /* Clickable for Phase 7 editing */
}

.label-line.null {
    color: #888;
    font-style: italic;
}

.label-line:hover {
    background: rgba(74, 105, 189, 0.9);
}

/* Bounding box */
.bbox {
    position: absolute;
    border: 2px solid rgba(74, 105, 189, 0.7);
    background: rgba(74, 105, 189, 0.1);
    pointer-events: none;
}

/* Different colors for multiple objects */
.object-labels:nth-child(2) .label-line {
    background: rgba(39, 174, 96, 0.85);
}

.object-labels:nth-child(3) .label-line {
    background: rgba(231, 76, 60, 0.85);
}
```

---

## 5. API Endpoints

### 5.1 GET `/api/labels/<seq_id>`

**Purpose:** Get label data for a specific image

**Response:**
```json
{
  "success": true,
  "data": {
    "seq_id": 1,
    "filename": "000000_ASH4662_1.jpg",
    "has_labels": true,
    "objects": [
      {
        "index": 0,
        "rect": [1, 580, 562, 563],
        "rect_percent": {
          "x": 0.1,
          "y": 50.0,
          "width": 48.5,
          "height": 48.6
        },
        "center_percent": {
          "x": 24.35,
          "y": 74.3
        },
        "labels": {
          "color": "silver",
          "brand": "honda",
          "model": "city",
          "label": "car",
          "type": "auto",
          "sub_type": "au - sedan compacto",
          "lp_coords": ""
        }
      }
    ]
  }
}
```

**Backend Logic:**
```python
@app.route('/api/labels/<int:seq_id>')
def get_labels(seq_id: int):
    # Find image entry
    image = next((img for img in project_manager.project_data['images'] 
                  if img['seq_id'] == seq_id), None)
    
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    if not image.get('json_filename'):
        return jsonify({
            'success': True,
            'data': {
                'seq_id': seq_id,
                'filename': image['filename'],
                'has_labels': False,
                'objects': []
            }
        })
    
    # Load JSON file
    json_path = Path(project_manager.project_data['directory']) / image['json_filename']
    
    try:
        with open(json_path, 'r') as f:
            label_data = json.load(f)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read labels: {e}'}), 500
    
    # Get image dimensions for percentage calculation
    img_path = Path(project_manager.project_data['directory']) / image['filename']
    try:
        with Image.open(img_path) as img:
            img_width, img_height = img.size
    except:
        img_width, img_height = 1000, 1000  # Default fallback
    
    # Process objects
    objects = []
    for idx, obj in enumerate(label_data):
        rect = obj.get('rect', [0, 0, 0, 0])
        x, y, w, h = rect
        
        # Calculate percentages
        rect_percent = {
            'x': (x / img_width) * 100,
            'y': (y / img_height) * 100,
            'width': (w / img_width) * 100,
            'height': (h / img_height) * 100
        }
        
        center_percent = {
            'x': ((x + w/2) / img_width) * 100,
            'y': ((y + h/2) / img_height) * 100
        }
        
        objects.append({
            'index': idx,
            'rect': rect,
            'rect_percent': rect_percent,
            'center_percent': center_percent,
            'labels': {
                'color': obj.get('color', None),
                'brand': obj.get('brand', None),
                'model': obj.get('model', None),
                'label': obj.get('label', None),
                'type': obj.get('type', None),
                'sub_type': obj.get('sub_type', None),
                'lp_coords': obj.get('lp_coords', None)
            }
        })
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'filename': image['filename'],
            'has_labels': True,
            'objects': objects
        }
    })
```

### 5.2 POST `/api/settings/visible_labels`

**Purpose:** Update visible labels setting

**Request Body:**
```json
{
  "visible_labels": ["color", "brand", "model", "type"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Visible labels updated"
}
```

---

## 6. JavaScript Implementation

### 6.1 Label State

```javascript
// Label visibility state
let visibleLabels = ['color', 'brand', 'model', 'type'];  // Default

// Cache for loaded labels
const labelCache = new Map();  // seq_id -> label data
```

### 6.2 Label Toggle Functions

```javascript
function toggleLabelDropdown() {
    const menu = document.getElementById('label-menu');
    menu.classList.toggle('hidden');
}

function toggleLabel(labelName, isVisible) {
    if (isVisible) {
        if (!visibleLabels.includes(labelName)) {
            visibleLabels.push(labelName);
        }
    } else {
        visibleLabels = visibleLabels.filter(l => l !== labelName);
    }
    
    updateLabelCount();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function selectAllLabels() {
    visibleLabels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
    updateLabelCheckboxes();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function clearAllLabels() {
    visibleLabels = [];
    updateLabelCheckboxes();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function updateLabelCount() {
    document.getElementById('label-count').textContent = 
        visibleLabels.length === 0 
            ? 'none' 
            : `${visibleLabels.length} shown`;
}

function updateLabelCheckboxes() {
    document.querySelectorAll('.dropdown-menu input[type="checkbox"]').forEach(cb => {
        cb.checked = visibleLabels.includes(cb.value);
    });
    updateLabelCount();
}

async function saveVisibleLabelsSetting() {
    try {
        await fetch('/api/settings/visible_labels', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ visible_labels: visibleLabels })
        });
    } catch (error) {
        console.error('Failed to save visible labels:', error);
    }
}
```

### 6.3 Label Loading & Rendering

```javascript
// Load labels for a single image
async function loadLabels(seqId) {
    // Check cache first
    if (labelCache.has(seqId)) {
        return labelCache.get(seqId);
    }
    
    try {
        const response = await fetch(`/api/labels/${seqId}`);
        const data = await response.json();
        
        if (data.success) {
            labelCache.set(seqId, data.data);
            return data.data;
        }
    } catch (error) {
        console.error(`Failed to load labels for ${seqId}:`, error);
    }
    
    return null;
}

// Render labels on image card
async function renderLabels(seqId) {
    const labelData = await loadLabels(seqId);
    const overlay = document.getElementById(`labels-${seqId}`);
    
    if (!overlay || !labelData || !labelData.has_labels) {
        return;
    }
    
    overlay.innerHTML = '';
    
    labelData.objects.forEach((obj, idx) => {
        // Create labels container at center of bbox
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'object-labels';
        labelsDiv.style.left = `${obj.center_percent.x}%`;
        labelsDiv.style.top = `${obj.center_percent.y}%`;
        labelsDiv.dataset.objectIndex = idx;
        
        // Add visible labels
        visibleLabels.forEach(labelName => {
            const value = obj.labels[labelName];
            const labelSpan = document.createElement('span');
            labelSpan.className = 'label-line';
            labelSpan.dataset.labelName = labelName;
            labelSpan.dataset.seqId = seqId;
            labelSpan.dataset.objectIndex = idx;
            
            if (value === null || value === undefined || value === '') {
                labelSpan.textContent = 'NULL';
                labelSpan.classList.add('null');
            } else {
                labelSpan.textContent = value;
            }
            
            // Click handler for editing (Phase 7)
            labelSpan.onclick = () => editLabel(seqId, idx, labelName, value);
            
            labelsDiv.appendChild(labelSpan);
        });
        
        overlay.appendChild(labelsDiv);
        
        // Optionally add bounding box
        if (showBoundingBoxes) {
            const bbox = document.createElement('div');
            bbox.className = 'bbox';
            bbox.style.left = `${obj.rect_percent.x}%`;
            bbox.style.top = `${obj.rect_percent.y}%`;
            bbox.style.width = `${obj.rect_percent.width}%`;
            bbox.style.height = `${obj.rect_percent.height}%`;
            overlay.appendChild(bbox);
        }
    });
}

// Refresh labels on all visible cards
function refreshAllLabels() {
    document.querySelectorAll('.image-card').forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        renderLabels(seqId);
    });
}

// Load labels for all images on current page
async function loadPageLabels(images) {
    // Load in parallel
    await Promise.all(images.map(img => renderLabels(img.seq_id)));
}
```

### 6.4 Integration with Grid Loading

```javascript
// Modified renderGrid from Phase 2
function renderGrid(images) {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = '';
    
    images.forEach(img => {
        const card = createImageCard(img);
        grid.appendChild(card);
    });
    
    // Load labels after cards are in DOM
    loadPageLabels(images);
}
```

---

## 7. Performance Optimizations

### 7.1 Batch Label Loading

```javascript
// Load labels for multiple images in one request
async function loadLabelsForPage(seqIds) {
    const uncached = seqIds.filter(id => !labelCache.has(id));
    
    if (uncached.length === 0) return;
    
    try {
        const response = await fetch('/api/labels/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ seq_ids: uncached })
        });
        const data = await response.json();
        
        if (data.success) {
            data.data.forEach(labelData => {
                labelCache.set(labelData.seq_id, labelData);
            });
        }
    } catch (error) {
        console.error('Failed to batch load labels:', error);
    }
}
```

### 7.2 API: Batch Label Endpoint

```python
@app.route('/api/labels/batch', methods=['POST'])
def get_labels_batch():
    seq_ids = request.json.get('seq_ids', [])
    
    results = []
    for seq_id in seq_ids[:50]:  # Limit batch size
        # Reuse single label logic
        label_data = get_label_data_for_image(seq_id)
        if label_data:
            results.append(label_data)
    
    return jsonify({
        'success': True,
        'data': results
    })
```

---

## 8. Coordinate System

### 8.1 Coordinate Transformation

**Original Image → Thumbnail:**
```
Original: 1160 x 1160 pixels
Thumbnail: 300 x 300 pixels (displayed)

Rect in original: [1, 580, 562, 563]
- x=1, y=580, width=562, height=563

As percentage of original:
- x% = 1/1160 * 100 = 0.086%
- y% = 580/1160 * 100 = 50.0%
- width% = 562/1160 * 100 = 48.4%
- height% = 563/1160 * 100 = 48.5%

Center point:
- cx% = (1 + 562/2) / 1160 * 100 = 24.3%
- cy% = (580 + 563/2) / 1160 * 100 = 74.3%
```

### 8.2 CSS Positioning

```css
/* Position at center of bounding box */
.object-labels {
    position: absolute;
    left: 24.3%;   /* center x */
    top: 74.3%;    /* center y */
    transform: translate(-50%, -50%);  /* Center the element */
}
```

---

## 9. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-3.1 | Labels displayed at center of bounding box | Verify position matches bbox center |
| AC-3.2 | Multiple labels stacked vertically | Image with 4 labels shows all stacked |
| AC-3.3 | Label dropdown shows all 7 label types | Click dropdown, verify all present |
| AC-3.4 | Toggling label updates display immediately | Uncheck "brand", verify removed from all cards |
| AC-3.5 | NULL displayed for missing label values | Image without brand shows "NULL" |
| AC-3.6 | Multiple objects have different colors | Image with 2 objects has colored labels |
| AC-3.7 | Label visibility saved to project | Change labels, reload, same visible |
| AC-3.8 | Images without JSON show no labels | Verify no overlay content |
| AC-3.9 | Labels scale with thumbnail size | Change grid 2x2→6x6, labels still visible |
| AC-3.10 | "Select All" shows all 7 labels | Click, verify all checked and displayed |

---

## 10. Edge Cases

| Case | Handling |
|------|----------|
| No JSON file for image | Show no labels (graceful) |
| Empty JSON array `[]` | Show no labels |
| Missing field in object | Show "NULL" for that label |
| Very long label text | Truncate with ellipsis or allow wrap |
| Bbox outside image bounds | Clamp to visible area |
| Many objects (>5) | Show all, may overlap |

---

## 11. Styling Variations

### 11.1 Compact Mode (for 6x6 grid)
```css
.grid-6x6 .label-line {
    font-size: 9px;
    padding: 1px 4px;
}

.grid-6x6 .object-labels {
    gap: 1px;
}
```

### 11.2 Show Object Index
```javascript
// Optional: Show object number
const indexBadge = document.createElement('span');
indexBadge.className = 'object-index';
indexBadge.textContent = `#${idx + 1}`;
labelsDiv.prepend(indexBadge);
```

```css
.object-index {
    background: rgba(74, 105, 189, 0.9);
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    margin-bottom: 2px;
}
```
