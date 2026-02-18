# Phase 11: Vehicle Direction Flag

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`

---

## Objective
Add a per-vehicle binary direction flag (`front`/`back`) to indicate whether a vehicle is coming toward the camera or going away. This flag enables efficient annotation of vehicle direction without opening a separate modal.

---

## 1. Prerequisites
- Phase 1-10 complete
- Label JSON files exist for images
- Bounding boxes are rendered on images

---

## 2. Data Model

### 2.1 Direction Field

| Field | Type | Values | Default |
|-------|------|--------|---------|
| `direction` | string | `"front"`, `"back"` | `"front"` |

### 2.2 Label JSON Update

**Before:**
```json
[
  {
    "rect": [100, 200, 300, 400],
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

**After:**
```json
[
  {
    "rect": [100, 200, 300, 400],
    "color": "white",
    "brand": "toyota",
    "model": "corolla",
    "label": "car",
    "type": "auto",
    "sub_type": "au - sedan compacto",
    "lp_coords": "",
    "direction": "front"
  }
]
```

### 2.3 Behavior When Missing

- If `direction` field is not present, treat as `"front"` (default)
- On first toggle, add the field to the JSON with value `"back"`
- Never remove the field once added

---

## 3. UI Components

### 3.1 Direction Indicator (Grid View)

```
┌────────────────────────────────────┐
│ [☐] [🔍] [🗑️] [🏷️]                 │
│                                    │
│    ┌──────────────────────────┐    │
│    │                    [⬆️]  │    │  ← Direction indicator (top-right)
│    │       🚗                 │    │
│    │      white               │    │
│    │      toyota              │    │
│    │                          │    │
│    └──────────────────────────┘    │
│                                    │
│ [ok] [pan-day]                     │
└────────────────────────────────────┘
```

### 3.2 Direction Indicator Visual

| Direction | Icon | Tooltip | Meaning |
|-----------|------|---------|---------|
| `front` | ⬆️ or ▲ | "Front (coming)" | Vehicle facing camera |
| `back` | ⬇️ or ▼ | "Back (going)" | Vehicle facing away |

Alternative icons (if emoji not suitable):
- Front: `↑`, `◄►`, `[F]`, `→◎`
- Back: `↓`, `►◄`, `[B]`, `◎←`

### 3.3 Position and Styling

```css
.direction-indicator {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 24px;
    height: 24px;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
    z-index: 10;
}

.direction-indicator:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
}

.direction-indicator.front {
    color: #4CAF50;  /* Green for front */
}

.direction-indicator.back {
    color: #FF9800;  /* Orange for back */
}
```

### 3.4 Direction Indicator HTML (per vehicle)

```html
<div class="vehicle-bbox" data-vehicle-idx="0">
    <div class="direction-indicator front" 
         onclick="toggleDirection(event, 'image_id', 0)"
         title="Front (coming) - Click to toggle">
        ⬆️
    </div>
    <!-- Bounding box rectangle -->
    <!-- Labels -->
</div>
```

---

## 4. Toggle Interaction

### 4.1 Click Behavior

1. User clicks on direction indicator
2. Toggle value: `front` → `back` or `back` → `front`
3. Update visual immediately (optimistic UI)
4. Send API request to save
5. Show brief visual feedback (flash/pulse)
6. If save fails, revert visual and show error notification

### 4.2 Toggle Animation

```css
@keyframes direction-toggle {
    0% { transform: scale(1); }
    50% { transform: scale(1.3); }
    100% { transform: scale(1); }
}

.direction-indicator.toggling {
    animation: direction-toggle 0.3s ease-out;
}
```

### 4.3 JavaScript Toggle Function

```javascript
async function toggleDirection(event, imageId, vehicleIdx) {
    event.stopPropagation();  // Don't trigger parent click handlers
    
    const indicator = event.target.closest('.direction-indicator');
    const currentDirection = indicator.classList.contains('front') ? 'front' : 'back';
    const newDirection = currentDirection === 'front' ? 'back' : 'front';
    
    // Optimistic UI update
    indicator.classList.remove(currentDirection);
    indicator.classList.add(newDirection);
    indicator.innerHTML = newDirection === 'front' ? '⬆️' : '⬇️';
    indicator.title = newDirection === 'front' ? 'Front (coming) - Click to toggle' : 'Back (going) - Click to toggle';
    
    // Animation
    indicator.classList.add('toggling');
    setTimeout(() => indicator.classList.remove('toggling'), 300);
    
    try {
        const response = await fetch(`/api/vehicle/${imageId}/${vehicleIdx}/direction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ direction: newDirection })
        });
        
        if (!response.ok) throw new Error('Failed to save');
        
        showNotification(`Direction set to ${newDirection}`, 'success');
    } catch (error) {
        // Revert on failure
        indicator.classList.remove(newDirection);
        indicator.classList.add(currentDirection);
        indicator.innerHTML = currentDirection === 'front' ? '⬆️' : '⬇️';
        showNotification('Failed to update direction', 'error');
    }
}
```

---

## 5. Backend API

### 5.1 Toggle Direction Endpoint

```python
@app.route('/api/vehicle/<image_id>/<int:vehicle_idx>/direction', methods=['POST'])
def toggle_vehicle_direction(image_id, vehicle_idx):
    """Toggle direction flag for a specific vehicle in an image."""
    if not project_manager.project_data:
        return jsonify({"success": False, "error": "No project loaded"})
    
    data = request.get_json()
    new_direction = data.get('direction')
    
    if new_direction not in ('front', 'back'):
        return jsonify({"success": False, "error": "Invalid direction. Must be 'front' or 'back'"})
    
    # Find the image
    image = find_image_by_id(image_id)
    if not image:
        return jsonify({"success": False, "error": "Image not found"})
    
    # Load label JSON
    directory = Path(project_manager.project_data['directory'])
    json_path = directory / image.get('json_filename')
    
    if not json_path.exists():
        return jsonify({"success": False, "error": "Label file not found"})
    
    try:
        with open(json_path, 'r') as f:
            labels = json.load(f)
        
        if vehicle_idx < 0 or vehicle_idx >= len(labels):
            return jsonify({"success": False, "error": "Vehicle index out of range"})
        
        # Update direction
        labels[vehicle_idx]['direction'] = new_direction
        
        # Save back to file
        with open(json_path, 'w') as f:
            json.dump(labels, f, indent=2)
        
        return jsonify({
            "success": True,
            "direction": new_direction,
            "message": f"Direction set to {new_direction}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
```

### 5.2 Include Direction in Label Data

Update `get_labels` or wherever label data is returned:

```python
def get_vehicle_direction(vehicle_obj):
    """Get direction with default fallback."""
    return vehicle_obj.get('direction', 'front')
```

---

## 6. Filter Integration

### 6.1 Add Direction to Filter Options

Update `/api/filter/options` to include direction counts:

```python
# In get_filter_options()
direction_count = {'front': 0, 'back': 0}

for json_path in json_files:
    with open(json_path, 'r') as f:
        labels = json.load(f)
    for obj in labels:
        direction = obj.get('direction', 'front')
        direction_count[direction] = direction_count.get(direction, 0) + 1

# Include in response
return jsonify({
    'quality_flags': ...,
    'perspective_flags': ...,
    'color': ...,
    'direction': [
        {'value': 'front', 'count': direction_count['front']},
        {'value': 'back', 'count': direction_count['back']}
    ],
    ...
})
```

### 6.2 Add Direction Section to Filter Panel

```javascript
const sections = [
    { key: 'quality_flags', title: 'Quality Flags', icon: '🏷️' },
    { key: 'perspective_flags', title: 'Perspective', icon: '📐' },
    { key: 'direction', title: 'Direction', icon: '↕️' },  // Add this
    { key: 'color', title: 'Color', icon: '🎨' },
    // ... rest
];
```

### 6.3 Update Filter Application

```python
# In apply_filters_to_images()
if filters.get('direction'):
    # Must check if ANY vehicle in the image matches the direction filter
    json_path = directory / img['json_filename']
    with open(json_path, 'r') as f:
        labels = json.load(f)
    
    has_matching_direction = any(
        obj.get('direction', 'front') in filters['direction']
        for obj in labels
    )
    
    if not has_matching_direction:
        continue  # Skip this image
```

---

## 7. Modal View (Open Wider)

### 7.1 Direction in Modal

Same indicator behavior in the modal view:

```javascript
function renderModalVehicle(vehicle, idx, imageId) {
    const direction = vehicle.direction || 'front';
    
    return `
        <div class="modal-vehicle-bbox" data-idx="${idx}">
            <div class="direction-indicator ${direction}"
                 onclick="toggleDirection(event, '${imageId}', ${idx})"
                 title="${direction === 'front' ? 'Front (coming)' : 'Back (going)'} - Click to toggle">
                ${direction === 'front' ? '⬆️' : '⬇️'}
            </div>
            <!-- rest of vehicle rendering -->
        </div>
    `;
}
```

### 7.2 Larger Clickable Area in Modal

```css
.modal-content .direction-indicator {
    width: 32px;
    height: 32px;
    font-size: 18px;
}
```

---

## 8. Display States

### 8.1 State Summary

| State | Icon | Color | Background |
|-------|------|-------|------------|
| Front (default) | ⬆️ | Green `#4CAF50` | Dark `rgba(0,0,0,0.7)` |
| Back | ⬇️ | Orange `#FF9800` | Dark `rgba(0,0,0,0.7)` |
| Saving | ⏳ | Gray | Dark |
| Error | ⚠️ | Red | Dark |

### 8.2 Loading State

While saving, show a brief loading indicator:

```javascript
indicator.innerHTML = '⏳';
indicator.style.pointerEvents = 'none';

// After save completes
indicator.innerHTML = newDirection === 'front' ? '⬆️' : '⬇️';
indicator.style.pointerEvents = 'auto';
```

---

## 9. Keyboard Shortcut (Optional)

| Shortcut | Action |
|----------|--------|
| `V` | Toggle direction of hovered vehicle |

```javascript
document.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === 'v' && hoveredVehicle) {
        toggleDirection(
            { stopPropagation: () => {}, target: hoveredVehicle.indicator },
            hoveredVehicle.imageId,
            hoveredVehicle.vehicleIdx
        );
    }
});
```

---

## 10. Testing Checklist

### 10.1 Unit Tests

```python
# tests/test_app.py

def test_toggle_direction_front_to_back():
    """Test toggling direction from front to back."""
    response = client.post('/api/vehicle/image001/0/direction',
                          json={'direction': 'back'})
    assert response.json['success'] == True
    assert response.json['direction'] == 'back'

def test_toggle_direction_back_to_front():
    """Test toggling direction from back to front."""
    response = client.post('/api/vehicle/image001/0/direction',
                          json={'direction': 'front'})
    assert response.json['success'] == True
    assert response.json['direction'] == 'front'

def test_invalid_direction():
    """Test invalid direction value."""
    response = client.post('/api/vehicle/image001/0/direction',
                          json={'direction': 'left'})
    assert response.json['success'] == False

def test_default_direction():
    """Test that missing direction defaults to front."""
    # Load label that doesn't have direction field
    response = client.get('/api/labels/image_without_direction')
    for vehicle in response.json['vehicles']:
        assert vehicle.get('direction', 'front') == 'front'

def test_filter_by_direction():
    """Test filtering images by vehicle direction."""
    response = client.get('/api/images?filter_direction=back')
    # All returned images should have at least one vehicle with direction=back
```

### 10.2 Manual Tests

- [ ] Direction indicator appears on each vehicle bounding box
- [ ] Default shows ⬆️ (front) for vehicles without direction field
- [ ] Click toggles from ⬆️ to ⬇️ and vice versa
- [ ] JSON file is updated after toggle
- [ ] Multiple vehicles in same image can have different directions
- [ ] Direction shows correctly in modal view
- [ ] Toggle works in modal view
- [ ] Filter panel shows Direction section
- [ ] Filter by direction works correctly
- [ ] Page refresh preserves direction state

---

## 11. Implementation Order

1. **Backend API** - Add `/api/vehicle/.../direction` endpoint
2. **Data Reading** - Include direction in label data response
3. **Grid View UI** - Add direction indicator to bounding boxes
4. **Toggle Logic** - Implement click-to-toggle with API call
5. **Modal View** - Add direction indicator to modal
6. **Filter API** - Add direction to filter options
7. **Filter UI** - Add Direction section to filter panel
8. **Filter Logic** - Apply direction filter to images
9. **Testing** - Unit and manual tests
10. **Polish** - Animation, error handling, keyboard shortcut

---

## 12. Files Changed Summary

| File | Changes |
|------|---------|
| `app.py` | Add direction toggle endpoint, update filter options, update filter logic |
| `static/js/app.js` | Add `toggleDirection()`, update vehicle rendering, update filter sections |
| `static/css/styles.css` | Add `.direction-indicator` styles |
| `templates/index.html` | No changes needed |

---

## 13. Rollback Plan

If issues arise:
1. Revert code changes
2. Direction field in JSON files can remain (harmless)
3. Missing direction defaults to 'front' (no data migration needed)

The feature is additive and backward-compatible.
