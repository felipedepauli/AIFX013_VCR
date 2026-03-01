# Phase 18: Trainable Models Configuration

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Add a "Trainable Models" configuration section to the Dataset Metadata Panel. This allows users to define which ML models can be trained on the current dataset and specifies preprocessing steps (e.g., cropping) for each model. This replaces the deprecated "Perspective Flags" system.

---

## 1. Prerequisites
- Phase 17 (Cycles & Perspective Removal) complete
- Phase 14 (Metadata Panel) infrastructure verified

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Trainable Model** | An ML model configuration (name + enabled status + preprocessing) |
| **Preprocessing** | Transformation applied to images before training (e.g., `cropped`, `none`) |
| **Model Config** | The JSON structure storing these settings in `.dataset.json` |

### 2.2 Panel Layout

```
┌─────────────────────────────────┐
│ DATASET INFO                  ▶ │
│ ...                             │
│ ▼ Trainable Models              │
│   ☑ Panoramic Day    [cropped▼] │
│   ☐ Close-up Day     [none   ▼] │
│   ☐ BMC              [none   ▼] │
│                                 │
│   [+ Add Model]                 │
│                                 │
└─────────────────────────────────┘
```

---

## 3. UI Components

### 3.1 Trainable Models Section

Add to `templates/index.html` inside the metadata sidebar (after Stats Config):

```html
<div class="panel-section models-section">
    <div class="section-header" onclick="toggleSection(this)">
        <span class="section-icon">🤖</span>
        <span class="section-title">Trainable Models</span>
        <span class="section-toggle">▼</span>
    </div>
    <div class="section-content" id="models-content">
        <!-- Models list injected here -->
        <div id="trainable-models-list"></div>
        
        <!-- Add Model Form -->
        <div class="add-model-form">
            <input type="text" id="new-model-name" placeholder="New model name...">
            <button class="add-btn" onclick="addTrainableModel()">+</button>
        </div>
    </div>
</div>
```

### 3.2 Model Item Template

DOM structure for each model item:

```html
<div class="model-item">
    <label class="checkbox-option">
        <input type="checkbox" onchange="toggleModel('Panoramic Day', this.checked)" checked>
        <span class="model-name">Panoramic Day</span>
    </label>
    <select class="preprocessing-select" onchange="updatePreprocessing('Panoramic Day', this.value)">
        <option value="none">none</option>
        <option value="cropped" selected>cropped</option>
    </select>
</div>
```

---

## 4. CSS Styling

Add to `static/css/styles.css`:

```css
/* Trainable Models Section */
.model-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
    padding: 4px 6px;
    background: #252536;
    border-radius: 4px;
}

.model-item:hover {
    background: #2a2a3e;
}

.model-name {
    font-size: 13px;
    color: #eee;
    margin-left: 8px;
}

.preprocessing-select {
    width: 80px;
    padding: 2px 4px;
    font-size: 11px;
    background: #1a1a2a;
    border: 1px solid #444;
    color: #ccc;
    border-radius: 3px;
}

.add-model-form {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #333;
}

.add-model-form input {
    flex: 1;
    padding: 6px;
    background: #1a1a2a;
    border: 1px solid #444;
    color: #eee;
    font-size: 12px;
    border-radius: 3px;
}

.add-btn {
    width: 28px;
    height: 28px;
    background: #4a69bd;
    border: none;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.add-btn:hover {
    background: #5a79cd;
}
```

---

## 5. JavaScript Implementation

Add to `static/js/app.js`:

### 5.1 Constants

```javascript
const DEFAULT_TRAINABLE_MODELS = [
    'Panoramic Day', 'Panoramic Night',
    'Superpanoramic Day', 'Superpanoramic Night', 
    'Close-up Day', 'Close-up Night',
    'BMC', 'Plate Localization',
    'License Plate Text', 'Container'
];

const DEFAULT_PREPROCESSING = ['none', 'cropped'];
```

### 5.2 Rendering Logic

`renderTrainableModels()` will populate the list. It should:
1. Load `trainable_models` from `datasetState.metadata`.
2. Merge with `DEFAULT_TRAINABLE_MODELS` to ensure all defaults are shown (unchecked if not in metadata).
3. Render the HTML list.

### 5.3 State Management

`updateTrainableModel(name, enabled, preprocessing)`:
1. Update local state `datasetState.metadata.trainable_models`.
2. Call `saveTrainableModels()` to persist to backend.
3. Re-render UI.

`saveTrainableModels(models)`:
1. Send `PUT` request to `/api/dataset/metadata` with `metadata: { trainable_models: models }`.

---

## 6. Backend API (`app.py`)

Ensure `update_dataset_metadata` allows the `trainable_models` field in the `allowed_fields` list.
