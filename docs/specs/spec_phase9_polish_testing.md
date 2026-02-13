# Phase 9: Polish & Testing

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`, `tests/test_app.py`

---

## Objective
Final polish including keyboard shortcuts, error handling, performance optimization, loading states, notifications, and comprehensive testing.

---

## 1. Prerequisites
- Phase 1-8 complete
- All core features working

---

## 2. Keyboard Shortcuts

### 2.1 Complete Shortcut Map

| Key | Context | Action |
|-----|---------|--------|
| `←` | Grid | Previous page |
| `→` | Grid | Next page |
| `1` | Grid | Set grid 2×2 |
| `2` | Grid | Set grid 3×3 |
| `3` | Grid | Set grid 5×5 |
| `4` | Grid | Set grid 6×6 |
| `A` | Grid | Select all on page |
| `D` | Grid | Deselect all |
| `Delete` | Grid | Delete selected |
| `Backspace` | Grid | Delete selected |
| `F` | Grid | Flag selected/hovered |
| `Q` | Grid | Quick cycle quality flag |
| `P` | Grid | Perspective flag modal |
| `Space` | Grid | Open hovered image wider |
| `,` | Any | Open settings |
| `?` | Any | Show shortcuts help |
| `Escape` | Modal | Close any modal |
| `←` | Image Modal | Previous image |
| `→` | Image Modal | Next image |
| `Enter` | Edit | Save label edit |
| `Escape` | Edit | Cancel label edit |
| `Tab` | Edit | Save and move to next label |

### 2.2 Keyboard Handler Implementation

```javascript
document.addEventListener('keydown', handleKeyboard);

function handleKeyboard(e) {
    // Ignore when typing in input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        // Allow Escape and Tab in edit mode
        if (e.key !== 'Escape' && e.key !== 'Tab' && e.key !== 'Enter') {
            return;
        }
    }
    
    // Help modal shortcut
    if (e.key === '?') {
        e.preventDefault();
        toggleShortcutsHelp();
        return;
    }
    
    // Settings shortcut
    if (e.key === ',') {
        e.preventDefault();
        openSettings();
        return;
    }
    
    // Modal-specific handlers
    if (modalState.isOpen) {
        handleImageModalKeyboard(e);
        return;
    }
    
    if (flagModalState.isOpen || document.querySelector('#settings-modal:not(.hidden)')) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
        return;
    }
    
    // Grid handlers
    handleGridKeyboard(e);
}

function handleGridKeyboard(e) {
    switch (e.key) {
        case 'ArrowLeft':
            e.preventDefault();
            previousPage();
            break;
        case 'ArrowRight':
            e.preventDefault();
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
        case 'a':
        case 'A':
            e.preventDefault();
            selectAll();
            break;
        case 'd':
        case 'D':
            deselectAll();
            break;
        case 'Delete':
        case 'Backspace':
            if (selectionState.selected.size > 0) {
                e.preventDefault();
                deleteSelectedImages();
            }
            break;
        case 'f':
        case 'F':
            handleFlagShortcut();
            break;
        case 'q':
        case 'Q':
            cycleQualityFlag();
            break;
        case 'p':
        case 'P':
            quickPerspectiveFlag();
            break;
        case ' ':
            e.preventDefault();
            openHoveredImage();
            break;
        case 'Escape':
            deselectAll();
            break;
    }
}

function handleImageModalKeyboard(e) {
    switch (e.key) {
        case 'Escape':
            closeImageModal();
            break;
        case 'ArrowLeft':
            e.preventDefault();
            modalPrevImage();
            break;
        case 'ArrowRight':
            e.preventDefault();
            modalNextImage();
            break;
    }
}
```

### 2.3 Shortcuts Help Modal

```html
<div id="shortcuts-modal" class="modal hidden">
    <div class="modal-backdrop" onclick="closeShortcutsHelp()"></div>
    <div class="modal-content shortcuts-modal-content">
        <h2>⌨️ Keyboard Shortcuts</h2>
        
        <div class="shortcuts-section">
            <h3>Navigation</h3>
            <div class="shortcut-row"><kbd>←</kbd><span>Previous page</span></div>
            <div class="shortcut-row"><kbd>→</kbd><span>Next page</span></div>
            <div class="shortcut-row"><kbd>1-4</kbd><span>Change grid size</span></div>
        </div>
        
        <div class="shortcuts-section">
            <h3>Selection</h3>
            <div class="shortcut-row"><kbd>A</kbd><span>Select all on page</span></div>
            <div class="shortcut-row"><kbd>D</kbd><span>Deselect all</span></div>
            <div class="shortcut-row"><kbd>Space</kbd><span>Open hovered image</span></div>
        </div>
        
        <div class="shortcuts-section">
            <h3>Actions</h3>
            <div class="shortcut-row"><kbd>Delete</kbd><span>Delete selected</span></div>
            <div class="shortcut-row"><kbd>F</kbd><span>Flag selected</span></div>
            <div class="shortcut-row"><kbd>Q</kbd><span>Quick quality flag cycle</span></div>
            <div class="shortcut-row"><kbd>P</kbd><span>Perspective flags</span></div>
        </div>
        
        <div class="shortcuts-section">
            <h3>General</h3>
            <div class="shortcut-row"><kbd>,</kbd><span>Open settings</span></div>
            <div class="shortcut-row"><kbd>?</kbd><span>Show this help</span></div>
            <div class="shortcut-row"><kbd>Esc</kbd><span>Close modal / Deselect</span></div>
        </div>
        
        <button class="btn-primary" onclick="closeShortcutsHelp()">Got it</button>
    </div>
</div>
```

```css
.shortcuts-modal-content {
    max-width: 400px;
    padding: 24px;
}

.shortcuts-section {
    margin-bottom: 24px;
}

.shortcuts-section h3 {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 8px;
}

.shortcut-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 0;
}

.shortcut-row kbd {
    background: #333;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    font-family: monospace;
    min-width: 40px;
    text-align: center;
}

.shortcut-row span {
    color: #888;
    font-size: 14px;
}
```

---

## 3. Notification System

### 3.1 Notification HTML

```html
<div id="notifications" class="notifications-container">
    <!-- Notifications injected here -->
</div>
```

### 3.2 CSS

```css
.notifications-container {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 2000;
    display: flex;
    flex-direction: column-reverse;
    gap: 8px;
    max-width: 400px;
}

.notification {
    padding: 12px 16px;
    border-radius: 8px;
    background: #16213e;
    border: 1px solid #333;
    display: flex;
    align-items: center;
    gap: 10px;
    animation: slideIn 0.3s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.notification.success {
    border-color: #27ae60;
    background: rgba(39, 174, 96, 0.1);
}

.notification.error {
    border-color: #e74c3c;
    background: rgba(231, 76, 60, 0.1);
}

.notification.warning {
    border-color: #f39c12;
    background: rgba(243, 156, 18, 0.1);
}

.notification-icon {
    font-size: 18px;
}

.notification-message {
    flex: 1;
    font-size: 14px;
}

.notification-close {
    background: transparent;
    border: none;
    color: #888;
    cursor: pointer;
    padding: 4px;
}

.notification.fade-out {
    animation: fadeOut 0.3s ease forwards;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes fadeOut {
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}
```

### 3.3 JavaScript

```javascript
function showNotification(message, type = 'success', duration = 3000) {
    const container = document.getElementById('notifications');
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠'
    };
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${icons[type] || '●'}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}
```

---

## 4. Loading States

### 4.1 Full-Page Loader

```html
<div id="loading-overlay" class="loading-overlay hidden">
    <div class="loading-spinner"></div>
    <div class="loading-text">Loading...</div>
</div>
```

```css
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 3000;
}

.loading-overlay.hidden {
    display: none;
}

.loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid #333;
    border-top-color: #4a69bd;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-text {
    margin-top: 16px;
    color: #888;
    font-size: 14px;
}
```

```javascript
function showLoadingOverlay(text = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    overlay.querySelector('.loading-text').textContent = text;
    overlay.classList.remove('hidden');
}

function hideLoadingOverlay() {
    document.getElementById('loading-overlay').classList.add('hidden');
}
```

### 4.2 Grid Skeleton Loader

```javascript
function showGridSkeleton() {
    const grid = document.getElementById('image-grid');
    const count = gridState.gridSize;
    
    grid.innerHTML = Array(count).fill('').map(() => `
        <div class="skeleton-card">
            <div class="skeleton-image"></div>
        </div>
    `).join('');
}
```

```css
.skeleton-card {
    background: #16213e;
    border-radius: 8px;
    aspect-ratio: 1;
    overflow: hidden;
}

.skeleton-image {
    width: 100%;
    height: 100%;
    background: linear-gradient(
        90deg,
        #1a1a2e 0%,
        #2a2a4e 50%,
        #1a1a2e 100%
    );
    background-size: 200% 100%;
    animation: skeleton-shimmer 1.5s infinite;
}

@keyframes skeleton-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
```

---

## 5. Error Handling

### 5.1 Global Error Handler

```javascript
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    showNotification('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    showNotification('Network error occurred', 'error');
});
```

### 5.2 API Error Handling

```javascript
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Unknown error');
        }
        
        return data;
        
    } catch (error) {
        console.error(`API call failed: ${url}`, error);
        throw error;
    }
}
```

### 5.3 Retry Logic

```javascript
async function apiCallWithRetry(url, options = {}, retries = 3) {
    let lastError;
    
    for (let i = 0; i < retries; i++) {
        try {
            return await apiCall(url, options);
        } catch (error) {
            lastError = error;
            
            if (i < retries - 1) {
                // Wait before retry (exponential backoff)
                await new Promise(r => setTimeout(r, Math.pow(2, i) * 500));
            }
        }
    }
    
    throw lastError;
}
```

---

## 6. Performance Optimizations

### 6.1 Thumbnail Cache

```python
# Server-side caching
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_thumbnail(image_path: str, size: int) -> str:
    return generate_thumbnail(Path(image_path), size)

# Clear cache when needed
def clear_thumbnail_cache():
    get_cached_thumbnail.cache_clear()
```

### 6.2 Debounced Search/Filter

```javascript
const debouncedSearch = debounce((query) => {
    // Implement search
}, 300);
```

### 6.3 Virtual Scrolling (Future Enhancement)

For very large datasets (10,000+ images), consider implementing virtual scrolling:

```javascript
// Placeholder for future enhancement
// Use library like virtual-scroller or implement custom
```

### 6.4 Memory Cleanup

```javascript
// Clear caches when switching pages
function cleanupMemory() {
    // Keep only recent pages in label cache
    if (labelCache.size > 200) {
        const keysToDelete = Array.from(labelCache.keys()).slice(0, 100);
        keysToDelete.forEach(k => labelCache.delete(k));
    }
}

// Call on page change
function loadImages() {
    cleanupMemory();
    // ... rest of loading
}
```

---

## 7. Accessibility

### 7.1 ARIA Labels

```html
<button class="btn-delete" aria-label="Delete image" title="Delete">🗑️</button>
<button class="btn-flag" aria-label="Flag image" title="Flag">🏷️</button>
```

### 7.2 Focus Management

```javascript
// Focus first card after page load
function focusFirstCard() {
    const firstCard = document.querySelector('.image-card');
    if (firstCard) {
        firstCard.setAttribute('tabindex', '0');
        firstCard.focus();
    }
}

// Arrow key navigation between cards
function handleCardNavigation(e) {
    if (!['ArrowUp', 'ArrowDown'].includes(e.key)) return;
    
    const cards = Array.from(document.querySelectorAll('.image-card'));
    const currentIndex = cards.findIndex(c => c === document.activeElement);
    
    if (currentIndex === -1) return;
    
    const cols = Math.sqrt(gridState.gridSize);
    let nextIndex;
    
    if (e.key === 'ArrowUp') {
        nextIndex = currentIndex - cols;
    } else {
        nextIndex = currentIndex + cols;
    }
    
    if (nextIndex >= 0 && nextIndex < cards.length) {
        e.preventDefault();
        cards[nextIndex].focus();
    }
}
```

---

## 8. Testing Checklist

### 8.1 Unit Tests

```python
# test_image_review.py

def test_create_project():
    """Test project creation."""
    pass

def test_load_project():
    """Test loading existing project."""
    pass

def test_delete_image():
    """Test single image deletion."""
    pass

def test_bulk_delete():
    """Test bulk deletion."""
    pass

def test_update_flags():
    """Test flag updates."""
    pass

def test_update_label():
    """Test label editing."""
    pass

def test_settings_save():
    """Test settings persistence."""
    pass
```

### 8.2 Integration Test Scenarios

| Test | Steps | Expected |
|------|-------|----------|
| Project Create | Enter name, select dir, click Create | Project JSON created, images scanned |
| Project Load | Select existing project, click Open | Project loaded, images displayed |
| Grid Navigation | Click Next/Prev, press arrows | Correct page shown |
| Grid Size Change | Click 6×6 button | 36 images displayed |
| Image Selection | Click checkbox, shift-click | Correct images selected |
| Single Delete | Click delete, confirm | Image removed from grid and disk |
| Bulk Delete | Select 5, delete all | All 5 removed |
| Flag Single | Click flag, set "ok" | Card shows "ok" pill |
| Flag Bulk | Select 5, bulk flag "ok" | All 5 have "ok" pill |
| Edit Label | Click label, type, Enter | Label updated in JSON |
| Settings Change | Open settings, change value | Setting persisted |
| Keyboard Shortcuts | Test all shortcuts | Correct actions triggered |

### 8.3 Edge Case Tests

| Test | Scenario | Expected |
|------|----------|----------|
| Empty Project | Create project in empty dir | "No images found" message |
| Large Dataset | 10,000+ images | Performance acceptable (<5s load) |
| Missing JSON | Image without label file | "NULL" labels shown |
| Corrupt JSON | Invalid JSON file | Error handled gracefully |
| Network Error | API call fails | Error notification shown |
| Concurrent Edit | Two tabs editing same label | Last write wins |
| Browser Refresh | Refresh mid-operation | State restored correctly |

### 8.4 Browser Compatibility

| Browser | Minimum Version | Test |
|---------|-----------------|------|
| Chrome | 90+ | ✓ Full support |
| Firefox | 85+ | ✓ Full support |
| Safari | 14+ | ✓ Full support |
| Edge | 90+ | ✓ Full support |

---

## 9. Final File Structure

```
image_review_tool.py
├── Flask app
├── ProjectManager class
├── API routes
│   ├── /api/projects
│   ├── /api/images
│   ├── /api/image/<id>
│   ├── /api/labels/<id>
│   ├── /api/delete
│   ├── /api/flags
│   └── /api/settings
└── Template embedding

templates/
└── (inline in Python or separate index.html)

projects/
├── vehicle_colors_v4.json
├── night_dataset.json
└── ...

docs/
├── PRD_IMAGE_REVIEW_TOOL.md
├── DEV_PLAN_IMAGE_REVIEW_TOOL.md
└── specs/
    ├── spec_phase1_project_setup.md
    ├── spec_phase2_grid_view.md
    ├── spec_phase3_label_overlay.md
    ├── spec_phase4_per_image_controls.md
    ├── spec_phase5_delete.md
    ├── spec_phase6_flags.md
    ├── spec_phase7_inline_editing.md
    ├── spec_phase8_settings.md
    └── spec_phase9_polish_testing.md
```

---

## 10. Launch Checklist

- [ ] All phases implemented
- [ ] All acceptance criteria pass
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Error handling complete
- [ ] Keyboard shortcuts working
- [ ] Notifications working
- [ ] Settings persist correctly
- [ ] Delete confirmation works
- [ ] Flags save correctly
- [ ] Label editing saves to JSON
- [ ] Project JSON auto-saves
- [ ] Multiple projects supported
- [ ] Documentation complete

---

## 11. Known Limitations (v1.0)

1. **No undo** - Deletions and edits are permanent
2. **Single user** - No concurrent access handling
3. **Local only** - No cloud storage support
4. **No image editing** - View and label only
5. **No export** - Manual JSON access required

---

## 12. Future Enhancements

1. **Filter by flag** - Show only "review" images
2. **Search** - Find images by filename or label
3. **Undo stack** - Revert recent actions
4. **Export** - CSV/JSON export of annotations
5. **Statistics** - Dashboard with flag counts
6. **Presets** - Save common flag combinations
7. **Batch label edit** - Change label for all selected
8. **Dark/light theme** - Theme toggle
