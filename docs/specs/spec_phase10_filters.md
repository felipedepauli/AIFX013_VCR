# Phase 10: Filter Panel

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `templates/index.html`

---

## Objective
Add a modern, collapsible left sidebar filter panel to filter images by label values and flags, with real-time updates and active filter chips.

---

## 1. Prerequisites
- Phase 1-9 complete (v1.0)
- All core features working

---

## 2. Design Philosophy

### 2.1 Modern UI Principles
- **Glass morphism**: Subtle transparency with backdrop blur
- **Smooth animations**: 300ms transitions for all interactions
- **Dark theme consistency**: Match existing dark UI
- **Accessibility**: Keyboard navigation, focus states, ARIA labels
- **Responsive**: Panel adapts to available space

### 2.2 Filter UX Patterns
- **Faceted search**: Each filter section shows relevant options
- **Live counts**: Show matching images per option
- **Instant feedback**: No submit button, filters apply immediately
- **Clear affordances**: Easy to understand what's filtered

---

## 3. Filter Panel Structure

### 3.1 Layout Overview

```
┌──────────────────────┐
│ ◀ FILTERS            │  ← Header with collapse button
├──────────────────────┤
│ ┌──────────────────┐ │
│ │ 🔍 Search...     │ │  ← Search within filters
│ └──────────────────┘ │
├──────────────────────┤
│ ▼ Quality Flags      │  ← Collapsible section
│   ☑ ok        (25)   │
│   ☐ review    (12)   │
│   ☐ bin        (5)   │
│   ☐ move       (0)   │
├──────────────────────┤
│ ▶ Perspective Flags  │  ← Collapsed section
├──────────────────────┤
│ ▼ Color              │
│   ☑ white     (42)   │
│   ☐ black     (38)   │
│   ☐ silver    (25)   │
│   ☐ red       (15)   │
│   └ Show 8 more...   │  ← Expandable list
├──────────────────────┤
│ ▶ Brand              │
├──────────────────────┤
│ ▶ Model              │
├──────────────────────┤
│ ▶ Type               │
├──────────────────────┤
│                      │
│ [Clear All Filters]  │  ← Footer action
│                      │
└──────────────────────┘
```

### 3.2 Filter Sections

| Section | Type | Source | Priority |
|---------|------|--------|----------|
| Quality Flags | Checkbox group | Project settings | High |
| Perspective Flags | Checkbox group | Project settings | High |
| Color | Checkbox group | Label JSON values | High |
| Brand | Checkbox group | Label JSON values | Medium |
| Model | Checkbox group | Label JSON values | Medium |
| Type | Checkbox group | Label JSON values | Medium |
| Sub Type | Checkbox group | Label JSON values | Low |

---

## 4. HTML Structure

### 4.1 Filter Panel Container

```html
<!-- Filter Panel (Left Sidebar) -->
<aside id="filter-panel" class="filter-panel">
    <div class="filter-panel-header">
        <button class="filter-toggle-btn" onclick="toggleFilterPanel()" title="Toggle Filters ([)">
            <span class="toggle-icon">◀</span>
        </button>
        <span class="filter-title">FILTERS</span>
        <span class="filter-count" id="filter-match-count">500 images</span>
    </div>
    
    <div class="filter-panel-content">
        <!-- Search Box -->
        <div class="filter-search">
            <input type="text" id="filter-search-input" placeholder="🔍 Search filters..." 
                   oninput="filterSearchOptions(this.value)">
        </div>
        
        <!-- Filter Sections Container -->
        <div class="filter-sections" id="filter-sections">
            <!-- Populated by JavaScript -->
        </div>
        
        <!-- Footer -->
        <div class="filter-panel-footer">
            <button class="btn-clear-filters" onclick="clearAllFilters()" id="clear-filters-btn" disabled>
                Clear All Filters
            </button>
        </div>
    </div>
</aside>
```

### 4.2 Filter Section Template

```html
<!-- Filter Section (Quality Flags example) -->
<div class="filter-section" data-section="quality_flags">
    <button class="filter-section-header" onclick="toggleFilterSection('quality_flags')">
        <span class="section-icon">▼</span>
        <span class="section-title">Quality Flags</span>
        <span class="section-active-count" id="quality_flags-active">0</span>
    </button>
    <div class="filter-section-content" id="quality_flags-content">
        <div class="filter-options">
            <label class="filter-option">
                <input type="checkbox" value="ok" onchange="applyFilter('quality_flags', 'ok', this.checked)">
                <span class="option-checkbox"></span>
                <span class="option-label">ok</span>
                <span class="option-count">25</span>
            </label>
            <label class="filter-option">
                <input type="checkbox" value="review" onchange="applyFilter('quality_flags', 'review', this.checked)">
                <span class="option-checkbox"></span>
                <span class="option-label">review</span>
                <span class="option-count">12</span>
            </label>
            <!-- More options... -->
        </div>
        <button class="show-more-btn hidden" onclick="showMoreOptions('quality_flags')">
            Show 5 more...
        </button>
    </div>
</div>
```

### 4.3 Active Filters Bar

```html
<!-- Active Filters Bar (in toolbar area) -->
<div class="active-filters-bar" id="active-filters-bar">
    <div class="active-filters-list" id="active-filters-list">
        <!-- Filter chips injected here -->
    </div>
    <button class="btn-clear-all" onclick="clearAllFilters()" id="clear-all-btn">
        Clear All
    </button>
    <span class="filter-summary" id="filter-summary">42 of 500 images</span>
</div>
```

### 4.4 Filter Chip Template

```html
<!-- Active Filter Chip -->
<span class="filter-chip" data-type="color" data-value="white">
    <span class="chip-label">color:</span>
    <span class="chip-value">white</span>
    <button class="chip-remove" onclick="removeFilter('color', 'white')" aria-label="Remove filter">✕</button>
</span>
```

---

## 5. CSS Styling

### 5.1 Filter Panel Base

```css
/* ============================================
   Filter Panel - Left Sidebar
   ============================================ */

.filter-panel {
    position: fixed;
    left: 0;
    top: 60px;  /* Below header */
    bottom: 60px;  /* Above footer */
    width: 280px;
    background: rgba(22, 33, 62, 0.95);
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    transform: translateX(0);
    transition: transform 0.3s ease, width 0.3s ease;
    z-index: 100;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.filter-panel.collapsed {
    transform: translateX(-240px);
}

.filter-panel.collapsed .filter-panel-content {
    opacity: 0;
    pointer-events: none;
}

.filter-panel.collapsed .filter-toggle-btn .toggle-icon {
    transform: rotate(180deg);
}

/* Main content shifts when panel is open */
.main-content {
    margin-left: 280px;
    transition: margin-left 0.3s ease;
}

.main-content.panel-collapsed {
    margin-left: 40px;
}
```

### 5.2 Panel Header

```css
.filter-panel-header {
    display: flex;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    background: rgba(0, 0, 0, 0.2);
}

.filter-toggle-btn {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    background: rgba(74, 105, 189, 0.2);
    border: 1px solid rgba(74, 105, 189, 0.3);
    color: #4a69bd;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.filter-toggle-btn:hover {
    background: rgba(74, 105, 189, 0.4);
    border-color: #4a69bd;
}

.toggle-icon {
    transition: transform 0.3s ease;
    font-size: 12px;
}

.filter-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.5px;
    color: #888;
    margin-left: 12px;
    flex: 1;
}

.filter-count {
    font-size: 11px;
    color: #4a69bd;
    background: rgba(74, 105, 189, 0.15);
    padding: 4px 8px;
    border-radius: 12px;
}
```

### 5.3 Search Box

```css
.filter-search {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.filter-search input {
    width: 100%;
    padding: 10px 12px;
    background: rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #fff;
    font-size: 13px;
    transition: all 0.2s;
}

.filter-search input:focus {
    outline: none;
    border-color: #4a69bd;
    background: rgba(0, 0, 0, 0.4);
    box-shadow: 0 0 0 3px rgba(74, 105, 189, 0.2);
}

.filter-search input::placeholder {
    color: #666;
}
```

### 5.4 Filter Sections

```css
.filter-sections {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
}

.filter-section {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.filter-section-header {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: transparent;
    border: none;
    color: #fff;
    cursor: pointer;
    transition: background 0.2s;
    text-align: left;
}

.filter-section-header:hover {
    background: rgba(255, 255, 255, 0.05);
}

.section-icon {
    width: 20px;
    font-size: 10px;
    color: #888;
    transition: transform 0.3s ease;
}

.filter-section.collapsed .section-icon {
    transform: rotate(-90deg);
}

.section-title {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
}

.section-active-count {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #4a69bd;
    color: #fff;
    font-size: 11px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transform: scale(0.8);
    transition: all 0.2s;
}

.section-active-count.visible {
    opacity: 1;
    transform: scale(1);
}

.filter-section-content {
    max-height: 300px;
    overflow: hidden;
    transition: max-height 0.3s ease;
}

.filter-section.collapsed .filter-section-content {
    max-height: 0;
}

.filter-options {
    padding: 4px 8px 12px 8px;
}
```

### 5.5 Filter Options

```css
.filter-option {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    margin: 2px 0;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
}

.filter-option:hover {
    background: rgba(255, 255, 255, 0.05);
}

.filter-option input[type="checkbox"] {
    display: none;
}

.option-checkbox {
    width: 18px;
    height: 18px;
    border: 2px solid #444;
    border-radius: 4px;
    margin-right: 10px;
    position: relative;
    transition: all 0.2s;
}

.filter-option input:checked + .option-checkbox {
    background: #4a69bd;
    border-color: #4a69bd;
}

.filter-option input:checked + .option-checkbox::after {
    content: '✓';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #fff;
    font-size: 12px;
    font-weight: bold;
}

.option-label {
    flex: 1;
    font-size: 13px;
    color: #ccc;
}

.filter-option input:checked ~ .option-label {
    color: #fff;
    font-weight: 500;
}

.option-count {
    font-size: 12px;
    color: #666;
    min-width: 30px;
    text-align: right;
}

.filter-option input:checked ~ .option-count {
    color: #4a69bd;
}

/* Zero count styling */
.filter-option.zero-count {
    opacity: 0.4;
}

.filter-option.zero-count:hover {
    opacity: 0.6;
}

.show-more-btn {
    width: calc(100% - 24px);
    margin: 4px 12px 8px;
    padding: 8px;
    background: rgba(74, 105, 189, 0.1);
    border: 1px dashed rgba(74, 105, 189, 0.3);
    border-radius: 6px;
    color: #4a69bd;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}

.show-more-btn:hover {
    background: rgba(74, 105, 189, 0.2);
    border-style: solid;
}
```

### 5.6 Active Filters Bar

```css
.active-filters-bar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 16px;
    background: rgba(74, 105, 189, 0.1);
    border-bottom: 1px solid rgba(74, 105, 189, 0.2);
    min-height: 44px;
    flex-wrap: wrap;
}

.active-filters-bar.hidden {
    display: none;
}

.active-filters-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    flex: 1;
}

.filter-chip {
    display: inline-flex;
    align-items: center;
    background: rgba(74, 105, 189, 0.2);
    border: 1px solid rgba(74, 105, 189, 0.4);
    border-radius: 16px;
    padding: 4px 8px 4px 12px;
    font-size: 12px;
    animation: chipIn 0.2s ease;
}

@keyframes chipIn {
    from {
        opacity: 0;
        transform: scale(0.8);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

.chip-label {
    color: #888;
    margin-right: 4px;
}

.chip-value {
    color: #fff;
    font-weight: 500;
}

.chip-remove {
    width: 18px;
    height: 18px;
    margin-left: 6px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #888;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    transition: all 0.2s;
}

.chip-remove:hover {
    background: rgba(231, 76, 60, 0.3);
    color: #e74c3c;
}

.btn-clear-all {
    padding: 6px 12px;
    background: transparent;
    border: 1px solid rgba(231, 76, 60, 0.4);
    border-radius: 6px;
    color: #e74c3c;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}

.btn-clear-all:hover {
    background: rgba(231, 76, 60, 0.1);
}

.filter-summary {
    color: #4a69bd;
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
}
```

### 5.7 Panel Footer

```css
.filter-panel-footer {
    padding: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-clear-filters {
    width: 100%;
    padding: 12px;
    background: transparent;
    border: 1px solid rgba(231, 76, 60, 0.4);
    border-radius: 8px;
    color: #e74c3c;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-clear-filters:hover:not(:disabled) {
    background: rgba(231, 76, 60, 0.1);
    border-color: #e74c3c;
}

.btn-clear-filters:disabled {
    opacity: 0.4;
    cursor: not-allowed;
}
```

---

## 6. JavaScript Implementation

### 6.1 Filter State

```javascript
// Filter state
const filterState = {
    isOpen: true,
    activeFilters: {
        quality_flags: [],
        perspective_flags: [],
        color: [],
        brand: [],
        model: [],
        type: [],
        sub_type: []
    },
    filterOptions: {},  // Populated from API
    expandedSections: ['quality_flags', 'color'],
    searchQuery: ''
};

// Count of images matching current filters
let filteredImageCount = 0;
let totalImageCount = 0;
```

### 6.2 Initialize Filter Panel

```javascript
async function initFilterPanel() {
    // Load filter options from API
    await loadFilterOptions();
    
    // Render filter sections
    renderFilterSections();
    
    // Restore panel state from session
    restoreFilterPanelState();
    
    // Add keyboard shortcut
    document.addEventListener('keydown', handleFilterShortcuts);
}

async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filter/options');
        const data = await response.json();
        
        if (data.success) {
            filterState.filterOptions = data.data;
            totalImageCount = data.data.total_count;
        }
    } catch (error) {
        console.error('Failed to load filter options:', error);
    }
}
```

### 6.3 Render Filter Sections

```javascript
function renderFilterSections() {
    const container = document.getElementById('filter-sections');
    container.innerHTML = '';
    
    const sections = [
        { key: 'quality_flags', title: 'Quality Flags', icon: '🏷️' },
        { key: 'perspective_flags', title: 'Perspective Flags', icon: '📐' },
        { key: 'color', title: 'Color', icon: '🎨' },
        { key: 'brand', title: 'Brand', icon: '🏢' },
        { key: 'model', title: 'Model', icon: '🚗' },
        { key: 'type', title: 'Type', icon: '📦' },
        { key: 'sub_type', title: 'Sub Type', icon: '📑' }
    ];
    
    sections.forEach(section => {
        const options = filterState.filterOptions[section.key] || [];
        if (options.length === 0) return;
        
        const sectionEl = createFilterSection(section, options);
        container.appendChild(sectionEl);
    });
}

function createFilterSection(section, options) {
    const isExpanded = filterState.expandedSections.includes(section.key);
    const activeCount = filterState.activeFilters[section.key].length;
    
    const div = document.createElement('div');
    div.className = `filter-section ${isExpanded ? '' : 'collapsed'}`;
    div.dataset.section = section.key;
    
    // Show first 5 options, rest hidden
    const visibleOptions = options.slice(0, 5);
    const hiddenOptions = options.slice(5);
    
    div.innerHTML = `
        <button class="filter-section-header" onclick="toggleFilterSection('${section.key}')">
            <span class="section-icon">▼</span>
            <span class="section-title">${section.title}</span>
            <span class="section-active-count ${activeCount > 0 ? 'visible' : ''}">${activeCount}</span>
        </button>
        <div class="filter-section-content">
            <div class="filter-options">
                ${visibleOptions.map(opt => createFilterOption(section.key, opt)).join('')}
            </div>
            <div class="filter-options-hidden hidden" id="${section.key}-hidden">
                ${hiddenOptions.map(opt => createFilterOption(section.key, opt)).join('')}
            </div>
            ${hiddenOptions.length > 0 ? `
                <button class="show-more-btn" onclick="showMoreOptions('${section.key}')">
                    Show ${hiddenOptions.length} more...
                </button>
            ` : ''}
        </div>
    `;
    
    return div;
}

function createFilterOption(sectionKey, option) {
    const isChecked = filterState.activeFilters[sectionKey].includes(option.value);
    const zeroClass = option.count === 0 ? 'zero-count' : '';
    
    return `
        <label class="filter-option ${zeroClass}">
            <input type="checkbox" 
                   value="${option.value}" 
                   ${isChecked ? 'checked' : ''}
                   onchange="applyFilter('${sectionKey}', '${option.value}', this.checked)">
            <span class="option-checkbox"></span>
            <span class="option-label">${option.value}</span>
            <span class="option-count">${option.count}</span>
        </label>
    `;
}
```

### 6.4 Filter Actions

```javascript
function applyFilter(category, value, isActive) {
    if (isActive) {
        if (!filterState.activeFilters[category].includes(value)) {
            filterState.activeFilters[category].push(value);
        }
    } else {
        filterState.activeFilters[category] = filterState.activeFilters[category]
            .filter(v => v !== value);
    }
    
    // Update UI
    updateActiveFiltersBar();
    updateSectionActiveCounts();
    
    // Save state
    saveFilterState();
    
    // Reload images with filters
    gridState.currentPage = 1;
    loadImages();
}

function removeFilter(category, value) {
    filterState.activeFilters[category] = filterState.activeFilters[category]
        .filter(v => v !== value);
    
    // Uncheck the checkbox
    const checkbox = document.querySelector(
        `.filter-section[data-section="${category}"] input[value="${value}"]`
    );
    if (checkbox) checkbox.checked = false;
    
    updateActiveFiltersBar();
    updateSectionActiveCounts();
    saveFilterState();
    
    gridState.currentPage = 1;
    loadImages();
}

function clearAllFilters() {
    Object.keys(filterState.activeFilters).forEach(key => {
        filterState.activeFilters[key] = [];
    });
    
    // Uncheck all checkboxes
    document.querySelectorAll('.filter-option input:checked').forEach(cb => {
        cb.checked = false;
    });
    
    updateActiveFiltersBar();
    updateSectionActiveCounts();
    saveFilterState();
    
    gridState.currentPage = 1;
    loadImages();
}
```

### 6.5 Active Filters Bar

```javascript
function updateActiveFiltersBar() {
    const container = document.getElementById('active-filters-list');
    const bar = document.getElementById('active-filters-bar');
    const clearBtn = document.getElementById('clear-all-btn');
    
    let chips = [];
    
    Object.entries(filterState.activeFilters).forEach(([category, values]) => {
        values.forEach(value => {
            chips.push(createFilterChip(category, value));
        });
    });
    
    container.innerHTML = chips.join('');
    
    // Show/hide bar
    if (chips.length > 0) {
        bar.classList.remove('hidden');
        clearBtn.disabled = false;
        document.getElementById('clear-filters-btn').disabled = false;
    } else {
        bar.classList.add('hidden');
        clearBtn.disabled = true;
        document.getElementById('clear-filters-btn').disabled = true;
    }
}

function createFilterChip(category, value) {
    const labels = {
        quality_flags: 'flag',
        perspective_flags: 'view',
        color: 'color',
        brand: 'brand',
        model: 'model',
        type: 'type',
        sub_type: 'sub'
    };
    
    return `
        <span class="filter-chip" data-type="${category}" data-value="${value}">
            <span class="chip-label">${labels[category] || category}:</span>
            <span class="chip-value">${value}</span>
            <button class="chip-remove" onclick="removeFilter('${category}', '${value}')" 
                    aria-label="Remove ${value} filter">✕</button>
        </span>
    `;
}
```

### 6.6 Panel Toggle & Shortcuts

```javascript
function toggleFilterPanel() {
    const panel = document.getElementById('filter-panel');
    const mainContent = document.getElementById('main-app');
    
    filterState.isOpen = !filterState.isOpen;
    
    if (filterState.isOpen) {
        panel.classList.remove('collapsed');
        mainContent.classList.remove('panel-collapsed');
    } else {
        panel.classList.add('collapsed');
        mainContent.classList.add('panel-collapsed');
    }
    
    saveFilterState();
}

function handleFilterShortcuts(e) {
    // '[' key toggles filter panel
    if (e.key === '[' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        toggleFilterPanel();
    }
}
```

### 6.7 Search Within Filters

```javascript
function filterSearchOptions(query) {
    filterState.searchQuery = query.toLowerCase();
    
    document.querySelectorAll('.filter-option').forEach(option => {
        const label = option.querySelector('.option-label').textContent.toLowerCase();
        const matches = label.includes(filterState.searchQuery);
        option.style.display = matches || !query ? '' : 'none';
    });
    
    // Show/hide sections based on visible options
    document.querySelectorAll('.filter-section').forEach(section => {
        const visibleOptions = section.querySelectorAll('.filter-option:not([style*="display: none"])');
        section.style.display = visibleOptions.length > 0 || !query ? '' : 'none';
    });
}
```

---

## 7. API Endpoints

### 7.1 Get Filter Options

```python
@app.route('/api/filter/options', methods=['GET'])
def get_filter_options():
    """Get all filterable options with counts"""
    if not current_project:
        return jsonify({'success': False, 'error': 'No project loaded'})
    
    options = {
        'quality_flags': [],
        'perspective_flags': [],
        'color': {},
        'brand': {},
        'model': {},
        'type': {},
        'sub_type': {}
    }
    
    # Count quality flags
    for flag in FLAG_CONFIG['quality']:
        count = sum(1 for img in current_project['images'] 
                    if flag in img.get('quality_flags', []))
        options['quality_flags'].append({'value': flag, 'count': count})
    
    # Count perspective flags
    for flag in FLAG_CONFIG['perspective']:
        count = sum(1 for img in current_project['images'] 
                    if flag in img.get('perspective_flags', []))
        options['perspective_flags'].append({'value': flag, 'count': count})
    
    # Count label values
    for img in current_project['images']:
        labels = img.get('labels', {})
        for field in ['color', 'brand', 'model', 'type', 'sub_type']:
            value = labels.get(field)
            if value and value != 'NULL':
                options[field][value] = options[field].get(value, 0) + 1
    
    # Convert dicts to sorted arrays
    for field in ['color', 'brand', 'model', 'type', 'sub_type']:
        sorted_opts = sorted(options[field].items(), key=lambda x: -x[1])
        options[field] = [{'value': k, 'count': v} for k, v in sorted_opts]
    
    return jsonify({
        'success': True,
        'data': {
            **options,
            'total_count': len(current_project['images'])
        }
    })
```

### 7.2 Modified Images Endpoint

```python
@app.route('/api/images', methods=['GET'])
def get_images():
    """Get paginated images with optional filters"""
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 9))
    
    # Parse filters
    filters = {}
    for key in ['quality_flags', 'perspective_flags', 'color', 'brand', 'model', 'type', 'sub_type']:
        values = request.args.getlist(f'filter_{key}')
        if values:
            filters[key] = values
    
    # Filter images
    images = current_project['images']
    
    if filters:
        filtered = []
        for img in images:
            match = True
            
            # Check flag filters
            if 'quality_flags' in filters:
                if not any(f in img.get('quality_flags', []) for f in filters['quality_flags']):
                    match = False
            
            if 'perspective_flags' in filters:
                if not any(f in img.get('perspective_flags', []) for f in filters['perspective_flags']):
                    match = False
            
            # Check label filters
            labels = img.get('labels', {})
            for field in ['color', 'brand', 'model', 'type', 'sub_type']:
                if field in filters:
                    if labels.get(field) not in filters[field]:
                        match = False
            
            if match:
                filtered.append(img)
        
        images = filtered
    
    # Paginate
    total = len(images)
    total_pages = (total + size - 1) // size
    start = (page - 1) * size
    end = start + size
    page_images = images[start:end]
    
    return jsonify({
        'success': True,
        'data': {
            'images': [prepare_image_data(img) for img in page_images],
            'pagination': {
                'page': page,
                'size': size,
                'total': total,
                'total_pages': total_pages,
                'total_unfiltered': len(current_project['images'])
            }
        }
    })
```

---

## 8. Integration with Existing Code

### 8.1 Modified loadImages Function

```javascript
async function loadImages() {
    const grid = document.getElementById('image-grid');
    showGridSkeleton();
    cleanupMemory();
    
    try {
        // Build filter query string
        const filterParams = buildFilterParams();
        const url = `/api/images?page=${gridState.currentPage}&size=${gridState.gridSize}${filterParams}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            if (data.data.images.length === 0) {
                grid.innerHTML = `
                    <div class="empty-state">
                        <p>📁 No images match your filters</p>
                        <button onclick="clearAllFilters()">Clear Filters</button>
                    </div>
                `;
            } else {
                renderGrid(data.data.images);
            }
            updatePagination(data.data.pagination);
            updateFilterSummary(data.data.pagination);
        } else {
            grid.innerHTML = `<div class="error">Failed to load images: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading images:', error);
        grid.innerHTML = '<div class="error">Failed to load images</div>';
    }
}

function buildFilterParams() {
    let params = '';
    
    Object.entries(filterState.activeFilters).forEach(([category, values]) => {
        values.forEach(value => {
            params += `&filter_${category}=${encodeURIComponent(value)}`;
        });
    });
    
    return params;
}

function updateFilterSummary(pagination) {
    const summary = document.getElementById('filter-summary');
    const matchCount = document.getElementById('filter-match-count');
    
    if (pagination.total !== pagination.total_unfiltered) {
        summary.textContent = `${pagination.total} of ${pagination.total_unfiltered} images`;
        matchCount.textContent = `${pagination.total} images`;
    } else {
        summary.textContent = `${pagination.total} images`;
        matchCount.textContent = `${pagination.total} images`;
    }
}
```

---

## 9. Acceptance Criteria

### 9.1 Filter Panel
- [ ] Panel slides in from left with smooth animation
- [ ] Toggle button (◀) collapses/expands panel
- [ ] `[` key toggles panel
- [ ] Panel state persists in session

### 9.2 Filter Functions
- [ ] Quality flags filterable
- [ ] Perspective flags filterable
- [ ] Color values filterable
- [ ] Brand values filterable
- [ ] Multiple filters combine with AND logic
- [ ] Filter counts update when filters applied

### 9.3 Active Filters
- [ ] Active filters shown as chips
- [ ] Click ✕ removes individual filter
- [ ] "Clear All" removes all filters
- [ ] Summary shows "X of Y images"

### 9.4 Performance
- [ ] Filters apply within 200ms
- [ ] Panel animations are smooth (60fps)
- [ ] Works with 1000+ images

---

## 10. Testing Checklist

### Manual Tests

```markdown
### Test 10.1: Filter Panel Toggle
- [ ] Click filter toggle button (◀) → panel slides in
- [ ] Click again → panel slides out
- [ ] Press `[` key → panel toggles
- [ ] Refresh page → panel state restored

### Test 10.2: Filter by Quality Flag
- [ ] Check "ok" in Quality Flags
- [ ] Verify only images with "ok" flag shown
- [ ] Verify filter chip appears: [flag: ok ✕]
- [ ] Verify count updates in footer

### Test 10.3: Filter by Multiple Flags
- [ ] Check "ok" and "review"
- [ ] Verify images with EITHER flag shown (OR within category)
- [ ] Check perspective flag too
- [ ] Verify images must match both categories (AND between categories)

### Test 10.4: Filter by Label Value
- [ ] Expand "Color" section
- [ ] Check "white"
- [ ] Verify only images with color=white shown
- [ ] Verify chip: [color: white ✕]

### Test 10.5: Remove Individual Filter
- [ ] Apply multiple filters
- [ ] Click ✕ on one chip
- [ ] Verify that filter removed, others remain
- [ ] Verify grid updates

### Test 10.6: Clear All Filters
- [ ] Apply 3+ filters
- [ ] Click "Clear All Filters"
- [ ] Verify all filters removed
- [ ] Verify all checkboxes unchecked
- [ ] Verify full image list restored

### Test 10.7: Search Options
- [ ] Type "whi" in search box
- [ ] Verify only matching options visible (white, etc.)
- [ ] Clear search → all options visible again

### Test 10.8: Pagination with Filters
- [ ] Apply filter that shows 15 images
- [ ] Verify pagination shows correct page count
- [ ] Navigate pages → verify correct images

### Test 10.9: Empty Results
- [ ] Apply filters that match 0 images
- [ ] Verify "No images match your filters" message
- [ ] Verify "Clear Filters" button in empty state
```

---

## 11. Implementation Order

1. **HTML Structure** - Add filter panel, active filters bar
2. **CSS Styling** - Complete styling with animations
3. **API Endpoints** - `/api/filter/options`, modify `/api/images`
4. **JavaScript Core** - Filter state, render functions
5. **Filter Actions** - Apply, remove, clear filters
6. **Integration** - Connect to loadImages, pagination
7. **Polish** - Search, animations, keyboard shortcuts
8. **Testing** - All test scenarios

---

## 12. Files to Modify

| File | Changes |
|------|---------|
| `templates/index.html` | Add filter panel HTML, active filters bar |
| `static/css/styles.css` | Add ~200 lines of filter styling |
| `static/js/app.js` | Add filter state, functions ~300 lines |
| `app.py` | Add filter options endpoint, modify images endpoint |
| `README.md` | Update with Phase 10 testing guide |
