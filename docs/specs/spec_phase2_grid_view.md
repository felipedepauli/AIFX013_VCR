# Phase 2: Grid View Display

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Implement a responsive image grid with configurable layouts (2x2, 3x3, 5x5, 6x6) and pagination. Users can navigate through all project images efficiently.

---

## 1. Prerequisites
- Phase 1 complete (project loaded with image list)
- Project JSON accessible via `project_manager`

---

## 2. Grid Layout Options

| Layout | Images per Page | Use Case |
|--------|-----------------|----------|
| 2×2 | 4 | Detailed review, large images |
| 3×3 | 9 | Default, balanced view |
| 5×5 | 25 | Quick scanning |
| 6×6 | 36 | Mass review, small thumbnails |

---

## 3. State Management

```javascript
// Grid state (client-side)
const gridState = {
    gridSize: 9,           // Current grid size (4, 9, 25, 36)
    currentPage: 1,        // Current page number
    totalPages: 1,         // Calculated from images / gridSize
    totalImages: 0,        // Total non-deleted images
    selectedImages: new Set()  // Set of selected seq_ids
};
```

---

## 4. UI Components

### 4.1 Grid Selector Toolbar

```
┌────────────────────────────────────────────────────────────┐
│  [2×2] [■3×3■] [5×5] [6×6]     Labels: [▼]     ⚙️         │
└────────────────────────────────────────────────────────────┘
```

**HTML:**
```html
<div class="toolbar">
    <div class="grid-selector">
        <button data-size="4" onclick="setGridSize(4)">2×2</button>
        <button data-size="9" class="active" onclick="setGridSize(9)">3×3</button>
        <button data-size="25" onclick="setGridSize(25)">5×5</button>
        <button data-size="36" onclick="setGridSize(36)">6×6</button>
    </div>
    <!-- Other toolbar items -->
</div>
```

**CSS:**
```css
.grid-selector {
    display: flex;
    gap: 4px;
    background: #0f0f23;
    padding: 4px;
    border-radius: 8px;
}

.grid-selector button {
    padding: 8px 16px;
    border: none;
    background: transparent;
    color: #888;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
}

.grid-selector button:hover {
    color: #fff;
    background: #333;
}

.grid-selector button.active {
    background: #4a69bd;
    color: #fff;
}
```

### 4.2 Image Grid Container

```html
<main id="image-grid" class="grid grid-3x3">
    <!-- Image cards populated by JavaScript -->
</main>
```

**CSS Grid Layout:**
```css
.grid {
    display: grid;
    gap: 16px;
    padding: 16px;
    max-width: 1600px;
    margin: 0 auto;
}

.grid-2x2 {
    grid-template-columns: repeat(2, 1fr);
}

.grid-3x3 {
    grid-template-columns: repeat(3, 1fr);
}

.grid-5x5 {
    grid-template-columns: repeat(5, 1fr);
}

.grid-6x6 {
    grid-template-columns: repeat(6, 1fr);
}

/* Responsive adjustments */
@media (max-width: 1200px) {
    .grid-5x5, .grid-6x6 {
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (max-width: 900px) {
    .grid-3x3, .grid-5x5, .grid-6x6 {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### 4.3 Image Card Structure

```html
<div class="image-card" data-seq-id="1">
    <!-- Controls (Phase 4) -->
    <div class="card-controls">
        <input type="checkbox" class="select-checkbox">
        <button class="btn-expand" title="Open Wider">🔍</button>
        <button class="btn-delete" title="Delete">🗑️</button>
        <button class="btn-flag" title="Flag">🏷️</button>
    </div>
    
    <!-- Image container -->
    <div class="image-container">
        <img src="" alt="Image 1" loading="lazy">
        <!-- Label overlay (Phase 3) -->
        <div class="label-overlay">
            <!-- Labels drawn here -->
        </div>
    </div>
    
    <!-- Flags display (Phase 6) -->
    <div class="card-flags">
        <!-- Flags shown here -->
    </div>
</div>
```

**CSS:**
```css
.image-card {
    position: relative;
    background: #16213e;
    border-radius: 8px;
    overflow: hidden;
    aspect-ratio: 1;
    transition: transform 0.2s, box-shadow 0.2s;
}

.image-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.image-card.selected {
    outline: 3px solid #4a69bd;
    outline-offset: 2px;
}

.image-container {
    position: relative;
    width: 100%;
    height: 100%;
}

.image-container img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.card-controls {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    padding: 8px;
    display: flex;
    gap: 4px;
    background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent);
    opacity: 0;
    transition: opacity 0.2s;
    z-index: 10;
}

.image-card:hover .card-controls {
    opacity: 1;
}

.card-controls button {
    width: 32px;
    height: 32px;
    padding: 0;
    border-radius: 4px;
    font-size: 16px;
    background: rgba(0, 0, 0, 0.5);
    border: none;
    cursor: pointer;
}

.card-controls button:hover {
    background: rgba(74, 105, 189, 0.8);
}

.select-checkbox {
    width: 20px;
    height: 20px;
    cursor: pointer;
    margin-right: auto;
}

.card-flags {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 4px 8px;
    background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}
```

### 4.4 Pagination Footer

```
┌────────────────────────────────────────────────────────────┐
│  Page 1 of 56  |  Total: 500  |  Selected: 3  | ◀ Prev  Next ▶  │
└────────────────────────────────────────────────────────────┘
```

**HTML:**
```html
<footer class="pagination">
    <span class="page-info">Page <span id="current-page">1</span> of <span id="total-pages">56</span></span>
    <span class="separator">|</span>
    <span class="total-info">Total: <span id="total-images">500</span></span>
    <span class="separator">|</span>
    <span class="selected-info">Selected: <span id="selected-count">0</span></span>
    <div class="nav-buttons">
        <button onclick="previousPage()" id="btn-prev">◀ Prev</button>
        <button onclick="nextPage()" id="btn-next">Next ▶</button>
    </div>
</footer>
```

**CSS:**
```css
.pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 16px;
    background: #16213e;
    border-top: 1px solid #333;
    position: sticky;
    bottom: 0;
}

.pagination .separator {
    color: #555;
}

.nav-buttons {
    display: flex;
    gap: 8px;
    margin-left: auto;
}

.nav-buttons button {
    padding: 8px 16px;
}

.nav-buttons button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
```

---

## 5. API Endpoints

### 5.1 GET `/api/images`

**Purpose:** Get paginated list of images for current grid page

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `size` | int | 9 | Grid size (4, 9, 25, 36) |

**Request Example:**
```
GET /api/images?page=1&size=9
```

**Response:**
```json
{
  "success": true,
  "data": {
    "images": [
      {
        "seq_id": 1,
        "filename": "000000_ASH4662_1.jpg",
        "thumbnail": "data:image/jpeg;base64,/9j/4AAQ...",
        "quality_flags": ["review"],
        "perspective_flags": ["pan-day"],
        "has_labels": true
      },
      // ... more images
    ],
    "pagination": {
      "current_page": 1,
      "total_pages": 56,
      "page_size": 9,
      "total_images": 500
    }
  }
}
```

**Backend Logic:**
```python
@app.route('/api/images')
def get_images():
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 9, type=int)
    
    # Validate size
    if size not in [4, 9, 25, 36]:
        size = 9
    
    # Get non-deleted images
    images = [img for img in project_manager.project_data['images'] 
              if not img.get('deleted', False)]
    
    total_images = len(images)
    total_pages = (total_images + size - 1) // size
    
    # Clamp page to valid range
    page = max(1, min(page, total_pages))
    
    # Get slice for current page
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_images = images[start_idx:end_idx]
    
    # Generate thumbnails and build response
    result = []
    for img in page_images:
        img_path = Path(project_manager.project_data['directory']) / img['filename']
        thumbnail = generate_thumbnail(img_path, size)
        
        result.append({
            'seq_id': img['seq_id'],
            'filename': img['filename'],
            'thumbnail': thumbnail,
            'quality_flags': img.get('quality_flags', []),
            'perspective_flags': img.get('perspective_flags', []),
            'has_labels': img.get('json_filename') is not None
        })
    
    return jsonify({
        'success': True,
        'data': {
            'images': result,
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'page_size': size,
                'total_images': total_images
            }
        }
    })
```

### 5.2 GET `/api/thumbnail/<seq_id>`

**Purpose:** Get thumbnail for specific image (fallback if not in batch)

**Response:** Base64 encoded JPEG image

---

## 6. Thumbnail Generation

```python
def generate_thumbnail(image_path: Path, grid_size: int) -> str:
    """
    Generate base64 thumbnail for grid display.
    
    Thumbnail sizes based on grid:
    - 2x2 (4): 400x400
    - 3x3 (9): 300x300
    - 5x5 (25): 200x200
    - 6x6 (36): 150x150
    """
    sizes = {4: 400, 9: 300, 25: 200, 36: 150}
    thumb_size = sizes.get(grid_size, 300)
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Create square thumbnail (crop to center)
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) // 2
            top = (height - min_dim) // 2
            img = img.crop((left, top, left + min_dim, top + min_dim))
            
            # Resize
            img.thumbnail((thumb_size, thumb_size), Image.LANCZOS)
            
            # Encode to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/jpeg;base64,{base64_str}"
    
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None
```

---

## 7. JavaScript Implementation

### 7.1 Grid Functions

```javascript
// Set grid size and reload
function setGridSize(size) {
    gridState.gridSize = size;
    gridState.currentPage = 1;  // Reset to page 1
    
    // Update UI
    document.querySelectorAll('.grid-selector button').forEach(btn => {
        btn.classList.toggle('active', parseInt(btn.dataset.size) === size);
    });
    
    // Update grid class
    const grid = document.getElementById('image-grid');
    grid.className = 'grid';
    grid.classList.add(`grid-${Math.sqrt(size)}x${Math.sqrt(size)}`);
    
    // Reload images
    loadImages();
    
    // Save preference to project
    saveGridSizeSetting(size);
}

// Navigate pages
function nextPage() {
    if (gridState.currentPage < gridState.totalPages) {
        gridState.currentPage++;
        loadImages();
    }
}

function previousPage() {
    if (gridState.currentPage > 1) {
        gridState.currentPage--;
        loadImages();
    }
}

// Load images for current page
async function loadImages() {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = '<div class="loading">Loading images...</div>';
    
    try {
        const response = await fetch(
            `/api/images?page=${gridState.currentPage}&size=${gridState.gridSize}`
        );
        const data = await response.json();
        
        if (data.success) {
            renderGrid(data.data.images);
            updatePagination(data.data.pagination);
        } else {
            grid.innerHTML = '<div class="error">Failed to load images</div>';
        }
    } catch (error) {
        console.error('Error loading images:', error);
        grid.innerHTML = '<div class="error">Failed to load images</div>';
    }
}

// Render image cards
function renderGrid(images) {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = '';
    
    images.forEach(img => {
        const card = createImageCard(img);
        grid.appendChild(card);
    });
}

// Create single image card
function createImageCard(img) {
    const card = document.createElement('div');
    card.className = 'image-card';
    card.dataset.seqId = img.seq_id;
    
    if (gridState.selectedImages.has(img.seq_id)) {
        card.classList.add('selected');
    }
    
    card.innerHTML = `
        <div class="card-controls">
            <input type="checkbox" class="select-checkbox" 
                   ${gridState.selectedImages.has(img.seq_id) ? 'checked' : ''}
                   onchange="toggleSelect(${img.seq_id}, this.checked)">
            <button class="btn-expand" onclick="openWider(${img.seq_id})" title="Open Wider">🔍</button>
            <button class="btn-delete" onclick="deleteImage(${img.seq_id})" title="Delete">🗑️</button>
            <button class="btn-flag" onclick="openFlagModal(${img.seq_id})" title="Flag">🏷️</button>
        </div>
        <div class="image-container">
            ${img.thumbnail 
                ? `<img src="${img.thumbnail}" alt="${img.filename}" loading="lazy">`
                : '<div class="no-image">No preview</div>'
            }
            <div class="label-overlay" id="labels-${img.seq_id}">
                <!-- Labels added by Phase 3 -->
            </div>
        </div>
        <div class="card-flags">
            ${renderFlags(img.quality_flags, 'quality')}
            ${renderFlags(img.perspective_flags, 'perspective')}
        </div>
    `;
    
    return card;
}

// Render flag pills
function renderFlags(flags, type) {
    if (!flags || flags.length === 0) return '';
    
    const colorClass = type === 'quality' ? 'flag-quality' : 'flag-perspective';
    
    return flags.map(flag => 
        `<span class="flag-pill ${colorClass}">${flag}</span>`
    ).join('');
}

// Update pagination display
function updatePagination(pagination) {
    gridState.totalPages = pagination.total_pages;
    gridState.totalImages = pagination.total_images;
    
    document.getElementById('current-page').textContent = pagination.current_page;
    document.getElementById('total-pages').textContent = pagination.total_pages;
    document.getElementById('total-images').textContent = pagination.total_images;
    
    // Enable/disable nav buttons
    document.getElementById('btn-prev').disabled = pagination.current_page <= 1;
    document.getElementById('btn-next').disabled = pagination.current_page >= pagination.total_pages;
}

// Update selected count
function updateSelectedCount() {
    document.getElementById('selected-count').textContent = gridState.selectedImages.size;
}
```

### 7.2 Keyboard Shortcuts

```javascript
document.addEventListener('keydown', (e) => {
    // Ignore if typing in input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
    
    switch (e.key) {
        case 'ArrowLeft':
            previousPage();
            break;
        case 'ArrowRight':
            nextPage();
            break;
        case '1':
            setGridSize(4);
            break;
        case '2':
            setGridSize(9);
            break;
        case '3':
            setGridSize(25);
            break;
        case '4':
            setGridSize(36);
            break;
    }
});
```

---

## 8. Performance Optimization

### 8.1 Thumbnail Caching

```python
# Server-side cache
from functools import lru_cache

@lru_cache(maxsize=500)
def get_cached_thumbnail(image_path: str, size: int) -> str:
    """Cache thumbnails in memory."""
    return generate_thumbnail(Path(image_path), size)
```

### 8.2 Lazy Loading

```html
<!-- Use native lazy loading -->
<img src="${thumbnail}" alt="${filename}" loading="lazy">
```

### 8.3 Debounced Resize

```javascript
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Adjust grid if needed
    }, 250);
});
```

---

## 9. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-2.1 | Grid displays correct number of images per layout | Select 2x2, verify 4 images shown |
| AC-2.2 | Grid layout changes when selector clicked | Click 6x6, verify grid columns change |
| AC-2.3 | Pagination shows correct page count | 500 images ÷ 9 = 56 pages |
| AC-2.4 | Next/Prev buttons navigate correctly | Click Next, page increments |
| AC-2.5 | Nav buttons disabled at boundaries | Page 1: Prev disabled; Last page: Next disabled |
| AC-2.6 | Thumbnails load for all images | Verify no broken images |
| AC-2.7 | Keyboard 1-4 changes grid size | Press 2, verify 3x3 layout |
| AC-2.8 | Arrow keys navigate pages | Press →, page increments |
| AC-2.9 | Deleted images not shown | Delete image, verify not in grid |
| AC-2.10 | Grid size preference saved | Change size, reload, same size |

---

## 10. Error States

| State | Display |
|-------|---------|
| Loading | Spinner or "Loading images..." text |
| Empty project | "No images in this project" |
| All deleted | "All images have been deleted" |
| Network error | "Failed to load images. Click to retry." |
| Invalid thumbnail | Placeholder with file icon |

---

## 11. CSS Variables for Theming

```css
:root {
    --grid-gap: 16px;
    --card-radius: 8px;
    --card-bg: #16213e;
    --card-hover-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    --selected-outline: #4a69bd;
    --control-bg: rgba(0, 0, 0, 0.5);
    --flag-quality-bg: #3498db;
    --flag-perspective-bg: #27ae60;
}
```
