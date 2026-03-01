# Phase 25: Datasets Dashboard Modal & Detail View

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/js/app.js`, `static/css/styles.css`, `templates/index.html`

**PRD Reference:** FR-17.2 (Datasets Dashboard Modal), FR-17.3 (Dataset Detail View)

---

## Objective
Implement the full-screen Datasets Dashboard modal showing all registered datasets as cards with thumbnails, stats, and metadata. Clicking a card opens an inline detail view with editable fields, spatial statistics, and actions (Open, Remove, Refresh).

---

## 1. Prerequisites
- Phase 23 complete (MongoDB Backend)
- Phase 24 complete (Datasets Panel & Registration)

---

## 2. Core Concepts

### 2.1 Modal States

The dashboard modal has two views:

| State | Description |
|-------|-------------|
| **Card Grid** | Default view — shows all datasets as cards in a responsive 2-3 column grid |
| **Detail View** | Expanded view of one dataset — shown when clicking a card |

Navigation: Card Grid → (click card) → Detail View → (click ← Back) → Card Grid

### 2.2 Card Grid Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    📊 Datasets Dashboard                         [✕ Close]  │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐                   │
│  │ vehicle_colors_v4        │  │ night_vehicles_v2        │                   │
│  │ ┌────┐┌────┐┌────┐┌────┐│  │ ┌────┐┌────┐┌────┐┌────┐│                   │
│  │ │ t1 ││ t2 ││ t3 ││ t4 ││  │ │ t1 ││ t2 ││ t3 ││ t4 ││                   │
│  │ └────┘└────┘└────┘└────┘│  │ └────┘└────┘└────┘└────┘│                   │
│  │ /home/.../vehicle_v4     │  │ /home/.../night_v2       │                   │
│  │ Cycle: second  Q: good   │  │ Cycle: first   Q: fair   │                   │
│  │ Model: colornet_v1       │  │ Model: colornet_v2       │                   │
│  │ Total: 1,234 images      │  │ Total: 567 images        │                   │
│  │ [Open]                   │  │ [Open]                   │                   │
│  └─────────────────────────┘  └─────────────────────────┘                   │
│                                                                              │
│  ┌─────────────────────────┐                                                │
│  │ panoramic_day_v1         │                                                │
│  │ ...                      │                                                │
│  └─────────────────────────┘                                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Detail View Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│               📊 Dataset: vehicle_colors_v4              [← Back] [✕ Close] │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │  thumb 1  │ │  thumb 2  │ │  thumb 3  │ │  thumb 4  │                       │
│  │  (1st)    │ │  (25%)    │ │  (75%)    │ │  (last)   │                       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘                       │
│                                                                              │
│  ┌─ Metadata ──────────────────┐  ┌─ Statistics ─────────────────────────┐  │
│  │ Name:    [_______________]  │  │ Total images: 1,234                  │  │
│  │ Path:    /home/...          │  │                                      │  │
│  │ Description: [____________] │  │ Classes:                             │  │
│  │ Camera:  [frontal ▼]       │  │   car: 890  motorcycle: 120          │  │
│  │ Quality: [good ▼]          │  │   truck: 134  bus: 90                │  │
│  │ Verdict: [keep ▼]          │  │                                      │  │
│  │ Cycle:   [second ▼]        │  │ Spatial (bbox):                      │  │
│  │ Model:   [colornet_v1, ▼]  │  │   Position μ: (320.5, 410.2)        │  │
│  │ Notes:   [________________] │  │   Position σ²: (150.3, 180.7)       │  │
│  └─────────────────────────────┘  │   Area μ: 45,230 px²               │  │
│                                    │   Area σ²: 12,500 px²               │  │
│  [Open Dataset]                    │   Computed: 2026-02-25 10:05        │  │
│  [🗑️ Remove from Dashboard]        │   [🔄 Refresh]                      │  │
│                                    └─────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. HTML — Dashboard Modal (index.html)

### 3.1 Modal Skeleton

```html
<!-- Datasets Dashboard Modal -->
<div id="dashboard-modal" class="modal dashboard-modal" style="display: none;">
    <div class="dashboard-modal-content">
        <!-- Header -->
        <div class="dashboard-header">
            <div class="dashboard-header-left">
                <button id="dashboard-back-btn" class="btn btn-icon" 
                        onclick="dashboardGoBack()" style="display: none;"
                        title="Back to list">
                    ← Back
                </button>
                <h2 id="dashboard-title">📊 Datasets Dashboard</h2>
            </div>
            <button class="btn btn-icon modal-close-btn" onclick="closeDashboardModal()">✕</button>
        </div>

        <!-- Card Grid View -->
        <div id="dashboard-card-grid" class="dashboard-card-grid">
            <!-- Cards populated by JS -->
            <div id="dashboard-empty" class="dashboard-empty" style="display: none;">
                <p>No datasets registered yet.</p>
                <p>Activate a dataset and use <strong>[+ Add Current]</strong> in the left panel.</p>
            </div>
        </div>

        <!-- Detail View -->
        <div id="dashboard-detail" class="dashboard-detail" style="display: none;">
            <!-- Thumbnail Strip -->
            <div class="detail-thumbnails">
                <img id="detail-thumb-0" class="detail-thumb" src="" alt="Thumbnail 1">
                <img id="detail-thumb-1" class="detail-thumb" src="" alt="Thumbnail 2">
                <img id="detail-thumb-2" class="detail-thumb" src="" alt="Thumbnail 3">
                <img id="detail-thumb-3" class="detail-thumb" src="" alt="Thumbnail 4">
            </div>

            <!-- Two-column layout -->
            <div class="detail-columns">
                <!-- Left: Metadata (editable) -->
                <div class="detail-metadata">
                    <h3>Metadata</h3>
                    
                    <div class="detail-field">
                        <label>Name</label>
                        <input type="text" id="detail-name" onchange="saveDashboardField('name', this.value)">
                    </div>
                    
                    <div class="detail-field">
                        <label>Path</label>
                        <span id="detail-path" class="detail-readonly"></span>
                        <span id="detail-path-warning" class="path-warning" style="display:none;">⚠️ Path not found</span>
                    </div>
                    
                    <div class="detail-field">
                        <label>Description</label>
                        <textarea id="detail-description" rows="3"
                                  onchange="saveDashboardField('metadata.description', this.value)"></textarea>
                    </div>
                    
                    <div class="detail-field">
                        <label>Camera View</label>
                        <select id="detail-camera-view" multiple
                                onchange="saveDashboardField('metadata.camera_view', getMultiSelectValues(this))">
                            <option value="frontal">Frontal</option>
                            <option value="traseira">Traseira</option>
                            <option value="panorâmica">Panorâmica</option>
                            <option value="closeup">Closeup</option>
                            <option value="super-panorâmica">Super-panorâmica</option>
                        </select>
                    </div>
                    
                    <div class="detail-field">
                        <label>Quality</label>
                        <select id="detail-quality"
                                onchange="saveDashboardField('metadata.quality', this.value)">
                            <option value="">—</option>
                            <option value="poor">Poor</option>
                            <option value="fair">Fair</option>
                            <option value="good">Good</option>
                            <option value="excellent">Excellent</option>
                        </select>
                    </div>
                    
                    <div class="detail-field">
                        <label>Verdict</label>
                        <select id="detail-verdict"
                                onchange="saveDashboardField('metadata.verdict', this.value)">
                            <option value="">—</option>
                            <option value="keep">✅ Keep</option>
                            <option value="revise">🔄 Revise</option>
                            <option value="remove">❌ Remove</option>
                        </select>
                    </div>
                    
                    <div class="detail-field">
                        <label>Cycle</label>
                        <select id="detail-cycle"
                                onchange="saveDashboardField('metadata.cycle', this.value)">
                            <option value="">—</option>
                            <option value="first">First</option>
                            <option value="second">Second</option>
                            <option value="third">Third</option>
                            <option value="fourth">Fourth</option>
                            <option value="fifth">Fifth</option>
                        </select>
                    </div>
                    
                    <div class="detail-field">
                        <label>Model Compatibility</label>
                        <select id="detail-model" multiple
                                onchange="saveDashboardField('metadata.model_compatibility', getMultiSelectValues(this))">
                            <option value="colornet_v1">ColorNet v1</option>
                            <option value="colornet_v2">ColorNet v2</option>
                            <option value="detect_v1">Detection v1</option>
                            <option value="brand_classifier">Brand Classifier</option>
                            <option value="custom">Custom</option>
                        </select>
                    </div>
                    
                    <div class="detail-field">
                        <label>Notes</label>
                        <textarea id="detail-notes" rows="3"
                                  onchange="saveDashboardField('metadata.notes', this.value)"></textarea>
                    </div>
                    
                    <!-- Actions -->
                    <div class="detail-actions">
                        <button class="btn btn-primary" onclick="openDatasetFromDashboard()">
                            Open Dataset
                        </button>
                        <button class="btn btn-danger" onclick="removeDatasetFromDashboard()">
                            🗑️ Remove from Dashboard
                        </button>
                    </div>
                </div>

                <!-- Right: Statistics -->
                <div class="detail-statistics">
                    <h3>Statistics</h3>
                    
                    <div class="stat-group">
                        <div class="stat-row stat-total">
                            <span class="stat-label">Total images</span>
                            <span id="stat-total-images" class="stat-value">—</span>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <h4>Classes</h4>
                        <div class="stat-row">
                            <span class="stat-label">Car</span>
                            <span id="stat-car" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Motorcycle</span>
                            <span id="stat-motorcycle" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Truck</span>
                            <span id="stat-truck" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Bus</span>
                            <span id="stat-bus" class="stat-value">—</span>
                        </div>
                    </div>
                    
                    <div class="stat-group">
                        <h4>Spatial (Bounding Box)</h4>
                        <div class="stat-row">
                            <span class="stat-label">Position μ</span>
                            <span id="stat-pos-mean" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Position σ²</span>
                            <span id="stat-pos-var" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Area μ</span>
                            <span id="stat-area-mean" class="stat-value">—</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Area σ²</span>
                            <span id="stat-area-var" class="stat-value">—</span>
                        </div>
                        <div class="stat-row stat-computed">
                            <span class="stat-label">Computed</span>
                            <span id="stat-computed-at" class="stat-value">—</span>
                        </div>
                    </div>
                    
                    <button class="btn btn-sm btn-secondary" onclick="refreshDatasetStats()">
                        🔄 Refresh Statistics
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## 4. CSS — Dashboard Styling (styles.css)

### 4.1 Modal

```css
/* Dashboard Modal — full screen overlay */
.dashboard-modal .dashboard-modal-content {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: #1e1e1e;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    border-bottom: 1px solid #333;
    flex-shrink: 0;
}

.dashboard-header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.dashboard-header h2 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
}
```

### 4.2 Card Grid

```css
/* Card grid — responsive 2-3 columns */
.dashboard-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 20px;
    padding: 24px;
    overflow-y: auto;
    flex: 1;
}

/* Dataset Card */
.dashboard-card {
    background: #2a2a2a;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 16px;
    cursor: pointer;
    transition: border-color 0.2s, transform 0.1s;
}

.dashboard-card:hover {
    border-color: #42a5f5;
    transform: translateY(-2px);
}

.dashboard-card.path-not-found {
    opacity: 0.6;
    border-color: #f44336;
}

/* Card name */
.card-name {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Card thumbnails row */
.card-thumbnails {
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
}

.card-thumb {
    width: 25%;
    aspect-ratio: 1;
    object-fit: cover;
    border-radius: 4px;
    background: #1a1a1a;
}

/* Card meta info */
.card-meta {
    font-size: 13px;
    color: #aaa;
    display: flex;
    flex-direction: column;
    gap: 3px;
}

.card-meta-row {
    display: flex;
    justify-content: space-between;
}

.card-path {
    font-size: 11px;
    color: #777;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 4px;
}

/* Card actions */
.card-actions {
    margin-top: 12px;
    display: flex;
    gap: 8px;
}

.card-actions .btn {
    font-size: 12px;
    padding: 4px 12px;
}
```

### 4.3 Detail View

```css
/* Detail view */
.dashboard-detail {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
}

/* Thumbnail strip */
.detail-thumbnails {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    justify-content: center;
}

.detail-thumb {
    width: 180px;
    height: 180px;
    object-fit: cover;
    border-radius: 6px;
    background: #1a1a1a;
    border: 1px solid #333;
}

/* Two-column content */
.detail-columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

@media (max-width: 900px) {
    .detail-columns {
        grid-template-columns: 1fr;
    }
}

/* Metadata section */
.detail-metadata h3,
.detail-statistics h3 {
    margin: 0 0 16px 0;
    font-size: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #333;
}

.detail-field {
    margin-bottom: 12px;
}

.detail-field label {
    display: block;
    font-size: 12px;
    color: #888;
    margin-bottom: 4px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.detail-field input,
.detail-field select,
.detail-field textarea {
    width: 100%;
    padding: 6px 8px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #eee;
    font-size: 13px;
}

.detail-field select[multiple] {
    min-height: 80px;
}

.detail-readonly {
    font-size: 13px;
    color: #ccc;
    word-break: break-all;
}

.path-warning {
    color: #f44336;
    font-size: 12px;
}

/* Actions row */
.detail-actions {
    margin-top: 20px;
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

/* Statistics section */
.stat-group {
    margin-bottom: 16px;
}

.stat-group h4 {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #aaa;
}

.stat-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 13px;
}

.stat-row.stat-total {
    font-size: 16px;
    font-weight: 600;
    padding: 8px 0;
}

.stat-label {
    color: #999;
}

.stat-value {
    color: #eee;
    font-variant-numeric: tabular-nums;
}

.stat-computed {
    color: #666;
    font-size: 11px;
    margin-top: 8px;
}

/* Empty state */
.dashboard-empty {
    grid-column: 1 / -1;
    text-align: center;
    padding: 80px 20px;
    color: #666;
}

.dashboard-empty p {
    margin: 8px 0;
    font-size: 15px;
}
```

---

## 5. JavaScript — Dashboard Logic (app.js)

### 5.1 State

```javascript
let dashboardCurrentDatasetId = null;  // ID of dataset in detail view
let dashboardView = 'grid';  // 'grid' or 'detail'
```

### 5.2 Open / Close Modal

```javascript
function openDashboardModal() {
    if (!mongoAvailable) {
        showToast('MongoDB not available', 'warning');
        return;
    }
    
    document.getElementById('dashboard-modal').style.display = 'flex';
    dashboardView = 'grid';
    dashboardCurrentDatasetId = null;
    showDashboardGrid();
    loadDashboardCards();
    
    // Trap Escape key
    document.addEventListener('keydown', dashboardKeyHandler);
}

function closeDashboardModal() {
    document.getElementById('dashboard-modal').style.display = 'none';
    document.removeEventListener('keydown', dashboardKeyHandler);
    dashboardCurrentDatasetId = null;
}

function dashboardKeyHandler(e) {
    if (e.key === 'Escape') {
        if (dashboardView === 'detail') {
            dashboardGoBack();
        } else {
            closeDashboardModal();
        }
        e.stopPropagation();
    }
}
```

### 5.3 Card Grid View

```javascript
async function loadDashboardCards() {
    const grid = document.getElementById('dashboard-card-grid');
    const emptyMsg = document.getElementById('dashboard-empty');
    
    // Show loading
    grid.innerHTML = '<div class="dashboard-loading">Loading datasets...</div>';
    
    try {
        const resp = await fetch('/api/datasets');
        const data = await resp.json();
        const datasets = data.datasets || [];
        
        grid.innerHTML = '';
        
        if (datasets.length === 0) {
            emptyMsg.style.display = 'block';
            grid.appendChild(emptyMsg);
            return;
        }
        
        emptyMsg.style.display = 'none';
        
        datasets.forEach(ds => {
            const card = createDashboardCard(ds);
            grid.appendChild(card);
        });
    } catch (e) {
        grid.innerHTML = `<div class="dashboard-error">Failed to load datasets: ${e.message}</div>`;
    }
}

function createDashboardCard(dataset) {
    const card = document.createElement('div');
    card.className = 'dashboard-card';
    if (!dataset.path_exists) card.classList.add('path-not-found');
    card.dataset.id = dataset.id;
    
    const verdict = dataset.metadata?.verdict || 'none';
    const quality = dataset.metadata?.quality || '—';
    const cycle = dataset.metadata?.cycle || '—';
    const models = (dataset.metadata?.model_compatibility || []).join(', ') || '—';
    const total = dataset.statistics?.total_images || 0;
    
    card.innerHTML = `
        <div class="card-name">
            <span class="dataset-status-dot ${verdict}"></span>
            ${escapeHtml(dataset.name)}
            ${!dataset.path_exists ? '<span class="path-warning">⚠️</span>' : ''}
        </div>
        <div class="card-thumbnails">
            <img class="card-thumb" src="/api/datasets/${dataset.id}/thumbnails/0" 
                 onerror="this.src='data:image/svg+xml,...placeholder...'" alt="">
            <img class="card-thumb" src="/api/datasets/${dataset.id}/thumbnails/1" 
                 onerror="this.src='data:image/svg+xml,...placeholder...'" alt="">
            <img class="card-thumb" src="/api/datasets/${dataset.id}/thumbnails/2" 
                 onerror="this.src='data:image/svg+xml,...placeholder...'" alt="">
            <img class="card-thumb" src="/api/datasets/${dataset.id}/thumbnails/3" 
                 onerror="this.src='data:image/svg+xml,...placeholder...'" alt="">
        </div>
        <div class="card-path">${escapeHtml(dataset.root_path)}</div>
        <div class="card-meta">
            <div class="card-meta-row">
                <span>Cycle: ${cycle}</span>
                <span>Quality: ${quality}</span>
            </div>
            <div class="card-meta-row">
                <span>Model: ${models}</span>
            </div>
            <div class="card-meta-row">
                <span>Total: ${total.toLocaleString()} images</span>
            </div>
        </div>
        <div class="card-actions">
            <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openDatasetFromCard('${dataset.id}')">
                Open
            </button>
        </div>
    `;
    
    // Click card → detail view
    card.addEventListener('click', () => showDashboardDetail(dataset.id));
    
    return card;
}
```

### 5.4 Detail View

```javascript
function showDashboardGrid() {
    document.getElementById('dashboard-card-grid').style.display = 'grid';
    document.getElementById('dashboard-detail').style.display = 'none';
    document.getElementById('dashboard-back-btn').style.display = 'none';
    document.getElementById('dashboard-title').textContent = '📊 Datasets Dashboard';
    dashboardView = 'grid';
}

async function showDashboardDetail(datasetId) {
    dashboardCurrentDatasetId = datasetId;
    dashboardView = 'detail';
    
    document.getElementById('dashboard-card-grid').style.display = 'none';
    document.getElementById('dashboard-detail').style.display = 'block';
    document.getElementById('dashboard-back-btn').style.display = 'inline-flex';
    
    try {
        const resp = await fetch(`/api/datasets/${datasetId}`);
        const dataset = await resp.json();
        
        document.getElementById('dashboard-title').textContent = 
            `📊 Dataset: ${dataset.name}`;
        
        // Populate thumbnails
        for (let i = 0; i < 4; i++) {
            const thumb = document.getElementById(`detail-thumb-${i}`);
            thumb.src = `/api/datasets/${datasetId}/thumbnails/${i}`;
            thumb.onerror = function() { this.style.display = 'none'; };
        }
        
        // Populate metadata fields
        document.getElementById('detail-name').value = dataset.name || '';
        document.getElementById('detail-path').textContent = dataset.root_path || '';
        
        const pathExists = dataset.path_exists !== false;
        document.getElementById('detail-path-warning').style.display = 
            pathExists ? 'none' : 'inline';
        
        const meta = dataset.metadata || {};
        document.getElementById('detail-description').value = meta.description || '';
        setSelectValues('detail-camera-view', meta.camera_view || []);
        document.getElementById('detail-quality').value = meta.quality || '';
        document.getElementById('detail-verdict').value = meta.verdict || '';
        document.getElementById('detail-cycle').value = meta.cycle || '';
        setSelectValues('detail-model', meta.model_compatibility || []);
        document.getElementById('detail-notes').value = meta.notes || '';
        
        // Populate statistics
        const stats = dataset.statistics || {};
        document.getElementById('stat-total-images').textContent = 
            (stats.total_images || 0).toLocaleString();
        
        const cc = stats.class_counts || {};
        document.getElementById('stat-car').textContent = (cc.car || 0).toLocaleString();
        document.getElementById('stat-motorcycle').textContent = (cc.motorcycle || 0).toLocaleString();
        document.getElementById('stat-truck').textContent = (cc.truck || 0).toLocaleString();
        document.getElementById('stat-bus').textContent = (cc.bus || 0).toLocaleString();
        
        const sp = stats.spatial || {};
        const pm = sp.position_mean || {};
        const pv = sp.position_variance || {};
        document.getElementById('stat-pos-mean').textContent = 
            pm.x != null ? `(${pm.x.toFixed(1)}, ${pm.y.toFixed(1)})` : '—';
        document.getElementById('stat-pos-var').textContent = 
            pv.x != null ? `(${pv.x.toFixed(1)}, ${pv.y.toFixed(1)})` : '—';
        document.getElementById('stat-area-mean').textContent = 
            sp.area_mean != null ? `${Math.round(sp.area_mean).toLocaleString()} px²` : '—';
        document.getElementById('stat-area-var').textContent = 
            sp.area_variance != null ? `${Math.round(sp.area_variance).toLocaleString()} px²` : '—';
        document.getElementById('stat-computed-at').textContent = 
            stats.computed_at ? new Date(stats.computed_at).toLocaleString() : '—';
        
    } catch (e) {
        showToast('Failed to load dataset details: ' + e.message, 'error');
    }
}

function dashboardGoBack() {
    showDashboardGrid();
    loadDashboardCards();  // Refresh in case edits were made
}
```

### 5.5 Auto-Save Editable Fields

```javascript
let dashboardSaveTimer = null;

async function saveDashboardField(field, value) {
    if (!dashboardCurrentDatasetId) return;
    
    // Debounce: batch rapid changes
    clearTimeout(dashboardSaveTimer);
    
    dashboardSaveTimer = setTimeout(async () => {
        try {
            // Build update payload
            const payload = {};
            const parts = field.split('.');
            
            if (parts.length === 1) {
                // Top-level field (e.g., 'name')
                payload[field] = value;
            } else {
                // Nested field (e.g., 'metadata.description')
                payload[parts[0]] = payload[parts[0]] || {};
                // Fetch current to merge
                const resp = await fetch(`/api/datasets/${dashboardCurrentDatasetId}`);
                const current = await resp.json();
                payload[parts[0]] = { ...current[parts[0]], [parts[1]]: value };
            }
            
            await fetch(`/api/datasets/${dashboardCurrentDatasetId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            // Also refresh left panel list
            await loadRegisteredDatasets();
        } catch (e) {
            showToast('Failed to save: ' + e.message, 'error');
        }
    }, 500);
}
```

### 5.6 Actions

```javascript
async function openDatasetFromCard(datasetId) {
    // Find dataset from cached list
    const dataset = registeredDatasets.find(d => d.id === datasetId);
    if (!dataset) return;
    
    closeDashboardModal();
    await openRegisteredDataset(dataset);
}

async function openDatasetFromDashboard() {
    if (!dashboardCurrentDatasetId) return;
    const dataset = registeredDatasets.find(d => d.id === dashboardCurrentDatasetId);
    if (!dataset) return;
    
    closeDashboardModal();
    await openRegisteredDataset(dataset);
}

async function removeDatasetFromDashboard() {
    if (!dashboardCurrentDatasetId) return;
    
    const confirmed = confirm(
        'Remove this dataset from the Dashboard?\n' +
        'This only unregisters it — no files will be deleted.'
    );
    if (!confirmed) return;
    
    try {
        await fetch(`/api/datasets/${dashboardCurrentDatasetId}`, {
            method: 'DELETE'
        });
        
        showToast('Dataset removed from Dashboard', 'success');
        dashboardGoBack();
        await loadRegisteredDatasets();
    } catch (e) {
        showToast('Failed to remove: ' + e.message, 'error');
    }
}

async function refreshDatasetStats() {
    if (!dashboardCurrentDatasetId) return;
    
    showToast('Refreshing statistics...', 'info');
    
    try {
        const resp = await fetch(`/api/datasets/${dashboardCurrentDatasetId}/refresh`, {
            method: 'POST'
        });
        
        if (!resp.ok) {
            const data = await resp.json();
            showToast(data.message || 'Refresh failed', 'error');
            return;
        }
        
        showToast('Statistics refreshed!', 'success');
        // Reload detail view
        await showDashboardDetail(dashboardCurrentDatasetId);
        await loadRegisteredDatasets();
    } catch (e) {
        showToast('Refresh failed: ' + e.message, 'error');
    }
}
```

### 5.7 Utility Helpers

```javascript
function setSelectValues(selectId, values) {
    const select = document.getElementById(selectId);
    if (!select) return;
    Array.from(select.options).forEach(opt => {
        opt.selected = values.includes(opt.value);
    });
}

function getMultiSelectValues(select) {
    return Array.from(select.selectedOptions).map(o => o.value);
}
```

---

## 6. Keyboard Shortcuts

| Shortcut | Context | Action |
|----------|---------|--------|
| `Escape` | Detail view | Back to card grid |
| `Escape` | Card grid | Close modal |

---

## 7. Testing Checklist

### 7.1 Dashboard Modal
- [ ] Click "📊 Dashboard" button → modal opens full-screen
- [ ] Escape closes modal
- [ ] ✕ button closes modal
- [ ] Shows "No datasets registered" when empty

### 7.2 Card Grid
- [ ] Registered datasets appear as cards
- [ ] Each card shows: name, 4 thumbnails, path, cycle, quality, model, total images
- [ ] Status dot color matches verdict (green/yellow/red/grey)
- [ ] Cards with missing paths show warning + reduced opacity
- [ ] "Open" button activates dataset and closes modal
- [ ] Clicking card body opens detail view

### 7.3 Detail View
- [ ] Shows 4 larger thumbnails at top
- [ ] All metadata fields populated from database
- [ ] Path shows read-only with warning if not found
- [ ] Edit name → auto-saves
- [ ] Edit description → auto-saves
- [ ] Change quality dropdown → auto-saves
- [ ] Change verdict → auto-saves
- [ ] Change cycle → auto-saves
- [ ] Select model compatibility → auto-saves
- [ ] Edit notes → auto-saves

### 7.4 Statistics
- [ ] Total images shown
- [ ] Class counts shown (car, motorcycle, truck, bus)
- [ ] Spatial stats shown (position mean/variance, area mean/variance)
- [ ] "Computed at" timestamp shown
- [ ] "🔄 Refresh Statistics" button re-computes and updates display

### 7.5 Actions
- [ ] "Open Dataset" → activates dataset, closes modal
- [ ] "🗑️ Remove from Dashboard" → confirmation → removes from list
- [ ] "← Back" returns to card grid
- [ ] After removal, card grid refreshed (card gone)

### 7.6 Responsive
- [ ] At ≥1200px viewport: 3 cards per row
- [ ] At ~800px viewport: 2 cards per row
- [ ] Detail view columns stack on narrow viewport
