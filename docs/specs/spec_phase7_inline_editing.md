# Phase 7: Inline Label Editing

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Enable direct editing of label values on image overlays. Clicking a label makes it editable, changes are saved to the per-image JSON file immediately.

---

## 1. Prerequisites
- Phase 1-6 complete
- Label overlay rendering working (Phase 3)
- Per-image JSON files accessible

---

## 2. Edit Flow

```
1. User clicks on label text (e.g., "silver")
2. Label transforms to input field
3. User types new value (e.g., "gray")
4. User presses Enter or clicks outside
5. Value saved to JSON file
6. UI updates to show new value
```

---

## 3. UI Components

### 3.1 Normal Label State

```html
<span class="label-line" 
      data-seq-id="1" 
      data-object-index="0" 
      data-label-name="color"
      onclick="editLabel(1, 0, 'color', 'silver')">
    silver
</span>
```

### 3.2 Edit Mode State

```html
<input class="label-input" 
       type="text" 
       value="silver"
       data-seq-id="1"
       data-object-index="0"
       data-label-name="color"
       autofocus>
```

### 3.3 CSS Styles

```css
/* Normal label - clickable */
.label-line {
    background: rgba(0, 0, 0, 0.75);
    color: #fff;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-family: monospace;
    white-space: nowrap;
    cursor: pointer;
    min-width: 40px;
    text-align: center;
    transition: all 0.15s;
}

.label-line:hover {
    background: rgba(74, 105, 189, 0.9);
    transform: scale(1.05);
}

.label-line.null {
    color: #888;
    font-style: italic;
}

/* Edit mode input */
.label-input {
    background: rgba(74, 105, 189, 0.9);
    color: #fff;
    border: 2px solid #fff;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 11px;
    font-family: monospace;
    min-width: 60px;
    max-width: 120px;
    text-align: center;
    outline: none;
}

.label-input:focus {
    box-shadow: 0 0 0 3px rgba(74, 105, 189, 0.4);
}

/* Saving indicator */
.label-line.saving {
    opacity: 0.7;
    pointer-events: none;
}

.label-line.saving::after {
    content: '...';
    animation: dots 1s infinite;
}

@keyframes dots {
    0%, 20% { content: '.'; }
    40% { content: '..'; }
    60%, 100% { content: '...'; }
}

/* Success flash */
.label-line.saved {
    animation: flash-green 0.5s ease;
}

@keyframes flash-green {
    0% { background: rgba(39, 174, 96, 0.9); }
    100% { background: rgba(0, 0, 0, 0.75); }
}

/* Error state */
.label-line.error {
    background: rgba(231, 76, 60, 0.9);
}
```

---

## 4. JavaScript Implementation

### 4.1 Edit State

```javascript
// Current edit state
const editState = {
    isEditing: false,
    seqId: null,
    objectIndex: null,
    labelName: null,
    originalValue: null,
    inputElement: null
};
```

### 4.2 Start Editing

```javascript
function editLabel(seqId, objectIndex, labelName, currentValue) {
    // Prevent if already editing
    if (editState.isEditing) {
        cancelEdit();
    }
    
    editState.isEditing = true;
    editState.seqId = seqId;
    editState.objectIndex = objectIndex;
    editState.labelName = labelName;
    editState.originalValue = currentValue;
    
    // Find the label element
    const labelSpan = document.querySelector(
        `.label-line[data-seq-id="${seqId}"][data-object-index="${objectIndex}"][data-label-name="${labelName}"]`
    );
    
    if (!labelSpan) return;
    
    // Create input element
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'label-input';
    input.value = currentValue || '';
    input.dataset.seqId = seqId;
    input.dataset.objectIndex = objectIndex;
    input.dataset.labelName = labelName;
    
    // Event handlers
    input.addEventListener('keydown', handleEditKeydown);
    input.addEventListener('blur', handleEditBlur);
    
    // Replace span with input
    labelSpan.replaceWith(input);
    editState.inputElement = input;
    
    // Focus and select
    input.focus();
    input.select();
}
```

### 4.3 Keyboard Handling

```javascript
function handleEditKeydown(e) {
    switch (e.key) {
        case 'Enter':
            e.preventDefault();
            saveEdit();
            break;
        
        case 'Escape':
            e.preventDefault();
            cancelEdit();
            break;
        
        case 'Tab':
            e.preventDefault();
            saveEdit();
            // Optionally move to next label
            moveToNextLabel(e.shiftKey ? -1 : 1);
            break;
    }
}
```

### 4.4 Blur Handling

```javascript
function handleEditBlur(e) {
    // Small delay to allow click on other elements
    setTimeout(() => {
        if (editState.isEditing && editState.inputElement === e.target) {
            saveEdit();
        }
    }, 100);
}
```

### 4.5 Save Edit

```javascript
async function saveEdit() {
    if (!editState.isEditing) return;
    
    const { seqId, objectIndex, labelName, originalValue, inputElement } = editState;
    const newValue = inputElement.value.trim();
    
    // Don't save if unchanged
    if (newValue === originalValue) {
        cancelEdit();
        return;
    }
    
    // Create placeholder span while saving
    const savingSpan = document.createElement('span');
    savingSpan.className = 'label-line saving';
    savingSpan.textContent = newValue || 'NULL';
    savingSpan.dataset.seqId = seqId;
    savingSpan.dataset.objectIndex = objectIndex;
    savingSpan.dataset.labelName = labelName;
    
    inputElement.replaceWith(savingSpan);
    
    // Reset edit state
    editState.isEditing = false;
    editState.inputElement = null;
    
    try {
        const response = await fetch(`/api/labels/${seqId}/${objectIndex}/${labelName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newValue || null })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update cache
            if (labelCache.has(seqId)) {
                const cached = labelCache.get(seqId);
                if (cached.objects[objectIndex]) {
                    cached.objects[objectIndex].labels[labelName] = newValue || null;
                }
            }
            
            // Show success
            savingSpan.classList.remove('saving');
            savingSpan.classList.add('saved');
            
            // Make it clickable again
            savingSpan.onclick = () => editLabel(seqId, objectIndex, labelName, newValue);
            
            if (!newValue) {
                savingSpan.classList.add('null');
            }
            
            setTimeout(() => {
                savingSpan.classList.remove('saved');
            }, 500);
            
        } else {
            throw new Error(data.error || 'Save failed');
        }
        
    } catch (error) {
        console.error('Failed to save label:', error);
        
        // Show error state
        savingSpan.classList.remove('saving');
        savingSpan.classList.add('error');
        savingSpan.textContent = originalValue || 'NULL';
        savingSpan.onclick = () => editLabel(seqId, objectIndex, labelName, originalValue);
        
        showNotification(`Failed to save: ${error.message}`, 'error');
        
        setTimeout(() => {
            savingSpan.classList.remove('error');
        }, 2000);
    }
}
```

### 4.6 Cancel Edit

```javascript
function cancelEdit() {
    if (!editState.isEditing) return;
    
    const { seqId, objectIndex, labelName, originalValue, inputElement } = editState;
    
    // Create span with original value
    const span = document.createElement('span');
    span.className = 'label-line';
    span.textContent = originalValue || 'NULL';
    span.dataset.seqId = seqId;
    span.dataset.objectIndex = objectIndex;
    span.dataset.labelName = labelName;
    span.onclick = () => editLabel(seqId, objectIndex, labelName, originalValue);
    
    if (!originalValue) {
        span.classList.add('null');
    }
    
    if (inputElement && inputElement.parentNode) {
        inputElement.replaceWith(span);
    }
    
    // Reset state
    editState.isEditing = false;
    editState.seqId = null;
    editState.objectIndex = null;
    editState.labelName = null;
    editState.originalValue = null;
    editState.inputElement = null;
}
```

### 4.7 Tab Navigation (Optional)

```javascript
function moveToNextLabel(direction = 1) {
    const { seqId, objectIndex, labelName } = editState;
    
    // Get list of visible labels
    const labelOrder = visibleLabels;
    const currentIdx = labelOrder.indexOf(labelName);
    
    if (currentIdx === -1) return;
    
    // Find next/prev label
    let nextIdx = currentIdx + direction;
    
    if (nextIdx >= 0 && nextIdx < labelOrder.length) {
        // Same object, next label
        const nextLabel = labelOrder[nextIdx];
        const labelData = labelCache.get(seqId);
        const currentValue = labelData?.objects[objectIndex]?.labels[nextLabel];
        
        editLabel(seqId, objectIndex, nextLabel, currentValue);
    }
}
```

---

## 5. API Endpoint

### 5.1 PUT `/api/labels/<seq_id>/<object_index>/<label_name>`

**Purpose:** Update a single label value in the image's JSON file

**Request Body:**
```json
{
  "value": "gray"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "seq_id": 1,
    "object_index": 0,
    "label_name": "color",
    "old_value": "silver",
    "new_value": "gray"
  }
}
```

### 5.2 Backend Implementation

```python
@app.route('/api/labels/<int:seq_id>/<int:object_index>/<label_name>', methods=['PUT'])
def update_label(seq_id: int, object_index: int, label_name: str):
    # Validate label name
    valid_labels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords']
    if label_name not in valid_labels:
        return jsonify({'success': False, 'error': f'Invalid label name: {label_name}'}), 400
    
    # Find image
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    if not image.get('json_filename'):
        return jsonify({'success': False, 'error': 'No JSON file for this image'}), 404
    
    json_path = Path(project_manager.project_data['directory']) / image['json_filename']
    
    # Read current JSON
    try:
        with open(json_path, 'r') as f:
            label_data = json.load(f)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read JSON: {e}'}), 500
    
    # Validate object index
    if object_index < 0 or object_index >= len(label_data):
        return jsonify({'success': False, 'error': f'Invalid object index: {object_index}'}), 400
    
    # Get new value
    new_value = request.json.get('value')
    old_value = label_data[object_index].get(label_name)
    
    # Update
    label_data[object_index][label_name] = new_value if new_value else ''
    
    # Write back (atomic)
    temp_path = json_path.with_suffix('.json.tmp')
    try:
        with open(temp_path, 'w') as f:
            json.dump(label_data, f, indent=2)
        
        temp_path.replace(json_path)
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'success': False, 'error': f'Failed to write JSON: {e}'}), 500
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'object_index': object_index,
            'label_name': label_name,
            'old_value': old_value,
            'new_value': new_value
        }
    })
```

---

## 6. Edit in Modal (Open Wider)

### 6.1 Modal Labels Also Editable

```javascript
// When rendering labels in modal, same click handler
async function renderModalLabels(seqId) {
    const labelData = await loadLabels(seqId);
    const overlay = document.getElementById('modal-labels');
    
    if (!overlay || !labelData || !labelData.has_labels) {
        overlay.innerHTML = '';
        return;
    }
    
    overlay.innerHTML = '';
    
    labelData.objects.forEach((obj, idx) => {
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'object-labels modal-object-labels';
        labelsDiv.style.left = `${obj.center_percent.x}%`;
        labelsDiv.style.top = `${obj.center_percent.y}%`;
        
        visibleLabels.forEach(labelName => {
            const value = obj.labels[labelName];
            const labelSpan = document.createElement('span');
            labelSpan.className = 'label-line modal-label';
            labelSpan.textContent = value || 'NULL';
            labelSpan.dataset.seqId = seqId;
            labelSpan.dataset.objectIndex = idx;
            labelSpan.dataset.labelName = labelName;
            
            if (!value) labelSpan.classList.add('null');
            
            // Same edit handler
            labelSpan.onclick = () => editLabel(seqId, idx, labelName, value);
            
            labelsDiv.appendChild(labelSpan);
        });
        
        overlay.appendChild(labelsDiv);
    });
}
```

### 6.2 Modal Label Styles

```css
.modal-object-labels {
    font-size: 14px;
}

.modal-object-labels .label-line {
    font-size: 14px;
    padding: 4px 12px;
}

.modal-object-labels .label-input {
    font-size: 14px;
    padding: 4px 10px;
    min-width: 80px;
    max-width: 200px;
}
```

---

## 7. Validation (Optional Enhancement)

### 7.1 Known Values Autocomplete

```javascript
// Color options for validation/suggest
const KNOWN_COLORS = [
    'black', 'blue', 'brown', 'gray', 'green', 
    'red', 'silver', 'white', 'yellow', 'unknown'
];

function createEditInput(seqId, objectIndex, labelName, currentValue) {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'label-input';
    input.value = currentValue || '';
    
    // Add datalist for color field
    if (labelName === 'color') {
        const datalistId = `color-options-${seqId}`;
        input.setAttribute('list', datalistId);
        
        if (!document.getElementById(datalistId)) {
            const datalist = document.createElement('datalist');
            datalist.id = datalistId;
            KNOWN_COLORS.forEach(color => {
                const option = document.createElement('option');
                option.value = color;
                datalist.appendChild(option);
            });
            document.body.appendChild(datalist);
        }
    }
    
    return input;
}
```

---

## 8. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-7.1 | Click label enters edit mode | Click "silver", input appears |
| AC-7.2 | Input shows current value | Input has "silver" as value |
| AC-7.3 | Enter key saves edit | Type "gray", press Enter, saved |
| AC-7.4 | Escape key cancels edit | Type, press Escape, original restored |
| AC-7.5 | Click outside saves edit | Type value, click elsewhere, saved |
| AC-7.6 | JSON file updated | Check .json file has new value |
| AC-7.7 | Other fields preserved | Change color, verify brand unchanged |
| AC-7.8 | Visual feedback on save | See brief green flash |
| AC-7.9 | Error shown on failure | Simulate error, see red state |
| AC-7.10 | NULL shown for empty value | Clear value, shows "NULL" |
| AC-7.11 | Edit works in modal | Open wider, edit label, saves |
| AC-7.12 | Cache updated after edit | Edit, close modal, reopen shows new value |

---

## 9. Edge Cases

| Case | Handling |
|------|----------|
| Empty value | Save as empty string, display as "NULL" |
| Very long value | Allow input, may overflow display |
| Special characters | Allow and escape properly in JSON |
| Concurrent edits | Last write wins |
| JSON file deleted | Show error, don't crash |
| Network timeout | Show error, keep original value |

---

## 10. Performance Notes

1. **Direct write** - No buffering, immediate save
2. **Atomic write** - Write to temp, then rename
3. **Cache update** - Update in-memory cache after successful save
4. **No undo** - Changes are permanent (could add undo stack later)
