# Phase 19: Dataset Attributes

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Add a "Dataset Attributes" section to the Dataset Metadata Panel. This allows users to tag the dataset with global attributes such as environmental conditions or image quality characteristics.

---

## 1. Prerequisites
- Phase 18 (Trainable Models) complete
- Metadata Panel infrastructure active

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Attribute** | A boolean flag describing the dataset (e.g., "Raining", "Low Light") |
| **Attribute Config** | The JSON structure storing these flags in `.dataset.json` |

### 2.2 Default Attributes
- Excess Light
- Grainy Image
- Low Light
- Raining
- Normal

### 2.3 Panel Layout

```
┌─────────────────────────────────┐
│ ...                             │
│ ▼ Dataset Attributes            │
│   ☑ Excess Light                │
│   ☐ Grainy Image                │
│   ☐ Low Light                   │
│   ☐ Raining                     │
│   ☑ Normal                      │
│                                 │
│   [+ Add Attribute]             │
│                                 │
└─────────────────────────────────┘
```

---

## 3. UI Components

### 3.1 Attributes Section

Add to `templates/index.html` inside the metadata sidebar (after Trainable Models):

```html
<div class="panel-section attributes-section">
    <div class="section-header" onclick="toggleMetadataSection(this)">
        <span class="section-icon">🏷️</span>
        <span class="section-title">Attributes</span>
        <span class="section-toggle">▼</span>
    </div>
    <div class="section-content" id="attributes-content">
        <!-- Attributes list injected here -->
        <div id="dataset-attributes-list"></div>
        
        <!-- Add Attribute Form -->
        <div class="add-attribute-form">
            <input type="text" id="new-attribute-name" placeholder="New attribute...">
            <button class="add-btn" onclick="addDatasetAttribute()">+</button>
        </div>
    </div>
</div>
```

---

## 4. CSS Styling

Reuse styles from `model-item` where possible or create similar `attribute-item`.

```css
/* Attributes Section */
.attribute-item {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
    padding: 6px 8px;
    background: #252536;
    border-radius: 4px;
    cursor: pointer;
}

.attribute-item:hover {
    background: #2a2a3e;
}

.attribute-item.enabled {
    border-left: 2px solid #4a69bd;
}

.attribute-name {
    font-size: 13px;
    color: #eee;
    margin-left: 8px;
    flex: 1;
}

.remove-attribute {
    padding: 2px 6px;
    background: none;
    border: none;
    color: #666;
    cursor: pointer;
    font-size: 14px;
    display: none;
}

.attribute-item:hover .remove-attribute {
    display: block;
}

.remove-attribute:hover {
    color: #e74c3c;
}

.add-attribute-form {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #333;
}

.add-attribute-form input {
    flex: 1;
    padding: 6px;
    background: #1a1a2a;
    border: 1px solid #444;
    color: #eee;
    font-size: 12px;
    border-radius: 3px;
}
```

---

## 5. JavaScript Implementation

Add to `static/js/app.js`:

### 5.1 Constants

```javascript
const DEFAULT_ATTRIBUTES = [
    'Excess Light',
    'Grainy Image', 
    'Low Light',
    'Raining',
    'Normal'
];
```

### 5.2 Rendering Logic

`renderDatasetAttributes()`:
1. Load `attributes` from `datasetState.metadata`.
2. Merge with `DEFAULT_ATTRIBUTES`.
3. Render list.

### 5.3 State Management

`updateDatasetAttribute(name, enabled)`:
1. Update local state.
2. Save to backend.

`addDatasetAttribute()`:
1. Add new custom attribute.

`saveDatasetAttributes(attributes)`:
1. Send `PUT` request to `/api/dataset/metadata` with `metadata: { attributes: attributes }`.
   note: `attributes` in JSON can be a list of strings (only enabled ones) or objects. Using objects `{name, enabled}` is consistent with models, but simple list of enabled strings might be easier. 
   **Decision**: Use list of objects `{name: "Raining", enabled: true}` to maintain consistency with Trainable Models and allow custom attributes to persist even if disabled (if we want that). However, for simple tags, a list of strings in `.dataset.json` like `"attributes": ["Raining", "Normal"]` is standard. 
   **Refined Decision**: To support "custom" attributes that haven't been selected yet, we need to know they exist. So we'll stick to the object pattern:
   `"attributes": [{"name": "MyCustom", "enabled": true}, ...]`

---

## 6. Backend API (`app.py`)

Ensure `update_dataset_metadata` allows the `attributes` field.
