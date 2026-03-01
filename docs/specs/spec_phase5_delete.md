# Phase 5: Delete Operations

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/css/styles.css`, `static/js/app.js`, `README.md`

---

## Objective
Implement delete functionality for individual and bulk image deletion. Includes confirmation dialog (configurable), file removal, grid reflow, and project JSON update.

---

## 1. Prerequisites
- Phase 1-4 complete
- Selection system working

---

## 2. Delete Behavior Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `skip_delete_confirmation` | `false` | When true, delete immediately without dialog |

---

## 3. UI Components

### 3.1 Delete Confirmation Dialog

```
┌──────────────────────────────────────────────────────┐
│                 ⚠️ Confirm Delete                    │
├──────────────────────────────────────────────────────┤
│                                                      │
│   Are you sure you want to delete this image?        │
│                                                      │
│   📁 000000_ASH4662_1.jpg                            │
│                                                      │
│   ⚠️ This action cannot be undone.                   │
│                                                      │
│   [ ] Don't ask again for this session               │
│                                                      │
│              [Cancel]     [Delete]                   │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3.2 Bulk Delete Confirmation

```
┌──────────────────────────────────────────────────────┐
│              ⚠️ Confirm Bulk Delete                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│   Are you sure you want to delete 5 images?          │
│                                                      │
│   Files to be deleted:                               │
│   • 000000_ASH4662_1.jpg                             │
│   • 000001_ABC1234_2.jpg                             │
│   • 000002_XYZ5678_1.jpg                             │
│   • ... and 2 more                                   │
│                                                      │
│   ⚠️ This action cannot be undone.                   │
│                                                      │
│              [Cancel]     [Delete All]               │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 3.3 HTML Structure

```html
<!-- Delete Confirmation Modal -->
<div id="delete-modal" class="modal hidden">
    <div class="modal-backdrop" onclick="closeDeleteModal()"></div>
    <div class="modal-content delete-modal-content">
        <h2>⚠️ <span id="delete-modal-title">Confirm Delete</span></h2>
        
        <p id="delete-modal-message">Are you sure you want to delete this image?</p>
        
        <div id="delete-file-list" class="file-list">
            <!-- Files listed here -->
        </div>
        
        <p class="warning-text">⚠️ This action cannot be undone.</p>
        
        <label class="dont-ask-checkbox">
            <input type="checkbox" id="delete-dont-ask" 
                   onchange="toggleSkipConfirmation(this.checked)">
            Don't ask again for this session
        </label>
        
        <div class="modal-actions">
            <button class="btn-cancel" onclick="closeDeleteModal()">Cancel</button>
            <button class="btn-delete" id="confirm-delete-btn" onclick="confirmDelete()">
                Delete
            </button>
        </div>
    </div>
</div>
```

### 3.4 CSS

```css
.delete-modal-content {
    max-width: 450px;
    padding: 24px;
}

.delete-modal-content h2 {
    margin-bottom: 16px;
    color: #e74c3c;
}

.file-list {
    background: #0f0f23;
    border-radius: 6px;
    padding: 12px;
    margin: 16px 0;
    max-height: 150px;
    overflow-y: auto;
}

.file-list-item {
    padding: 4px 0;
    font-family: monospace;
    font-size: 13px;
    color: #888;
}

.file-list-more {
    color: #666;
    font-style: italic;
}

.warning-text {
    color: #e74c3c;
    font-size: 14px;
    margin: 12px 0;
}

.dont-ask-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #888;
    font-size: 14px;
    cursor: pointer;
    margin: 16px 0;
}

.modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
}

.btn-cancel {
    padding: 10px 20px;
    background: #333;
    border: 1px solid #444;
    border-radius: 6px;
    color: #eee;
    cursor: pointer;
}

.btn-delete {
    padding: 10px 20px;
    background: #e74c3c;
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
    font-weight: 500;
}

.btn-delete:hover {
    background: #c0392b;
}
```

---

## 4. JavaScript Implementation

### 4.1 Delete State

```javascript
// Delete operation state
const deleteState = {
    pendingSeqIds: [],      // Images to be deleted
    skipConfirmation: false  // Session-level skip
};
```

### 4.2 Single Image Delete

```javascript
// Called from card delete button
function deleteImage(seqId) {
    const skipSetting = project?.settings?.skip_delete_confirmation || false;
    
    if (skipSetting || deleteState.skipConfirmation) {
        // Delete immediately
        executeDelete([seqId]);
    } else {
        // Show confirmation
        showDeleteConfirmation([seqId]);
    }
}
```

### 4.3 Bulk Delete

```javascript
// Called from toolbar button
function deleteSelectedImages() {
    const selectedIds = getSelectedIds();
    
    if (selectedIds.length === 0) {
        return;
    }
    
    const skipSetting = project?.settings?.skip_delete_confirmation || false;
    
    if (skipSetting || deleteState.skipConfirmation) {
        executeDelete(selectedIds);
    } else {
        showDeleteConfirmation(selectedIds);
    }
}
```

### 4.4 Confirmation Dialog

```javascript
function showDeleteConfirmation(seqIds) {
    deleteState.pendingSeqIds = seqIds;
    
    const modal = document.getElementById('delete-modal');
    const title = document.getElementById('delete-modal-title');
    const message = document.getElementById('delete-modal-message');
    const fileList = document.getElementById('delete-file-list');
    const confirmBtn = document.getElementById('confirm-delete-btn');
    
    const isBulk = seqIds.length > 1;
    
    title.textContent = isBulk ? 'Confirm Bulk Delete' : 'Confirm Delete';
    message.textContent = isBulk 
        ? `Are you sure you want to delete ${seqIds.length} images?`
        : 'Are you sure you want to delete this image?';
    confirmBtn.textContent = isBulk ? 'Delete All' : 'Delete';
    
    // Build file list
    fileList.innerHTML = '';
    const maxShow = 5;
    
    seqIds.slice(0, maxShow).forEach(seqId => {
        const image = findImageBySeqId(seqId);
        if (image) {
            const item = document.createElement('div');
            item.className = 'file-list-item';
            item.textContent = `📁 ${image.filename}`;
            fileList.appendChild(item);
        }
    });
    
    if (seqIds.length > maxShow) {
        const more = document.createElement('div');
        more.className = 'file-list-item file-list-more';
        more.textContent = `... and ${seqIds.length - maxShow} more`;
        fileList.appendChild(more);
    }
    
    modal.classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('delete-modal').classList.add('hidden');
    deleteState.pendingSeqIds = [];
}

function confirmDelete() {
    const seqIds = deleteState.pendingSeqIds;
    closeDeleteModal();
    executeDelete(seqIds);
}

function toggleSkipConfirmation(skip) {
    deleteState.skipConfirmation = skip;
}
```

### 4.5 Execute Delete

```javascript
async function executeDelete(seqIds) {
    if (seqIds.length === 0) return;
    
    // Show loading state
    showLoadingOverlay('Deleting...');
    
    try {
        const endpoint = seqIds.length === 1 
            ? `/api/delete/${seqIds[0]}`
            : '/api/delete/bulk';
        
        const body = seqIds.length === 1 
            ? {}
            : { seq_ids: seqIds };
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove from UI
            seqIds.forEach(seqId => {
                removeImageFromGrid(seqId);
                selectionState.selected.delete(seqId);
                labelCache.delete(seqId);
            });
            
            // Update counts
            updateSelectedCount();
            updateTotalCount(data.data.remaining_count);
            
            // Load more images if needed
            await refillGridIfNeeded();
            
            showNotification(`Deleted ${seqIds.length} image(s)`);
        } else {
            showNotification(`Failed to delete: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Delete failed:', error);
        showNotification('Delete operation failed', 'error');
    } finally {
        hideLoadingOverlay();
    }
}
```

### 4.6 UI Updates

```javascript
// Remove image card from grid with animation
function removeImageFromGrid(seqId) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    // Animate out
    card.style.transition = 'opacity 0.3s, transform 0.3s';
    card.style.opacity = '0';
    card.style.transform = 'scale(0.8)';
    
    setTimeout(() => {
        card.remove();
    }, 300);
}

// Load more images to fill grid gaps
async function refillGridIfNeeded() {
    const grid = document.getElementById('image-grid');
    const currentCards = grid.querySelectorAll('.image-card').length;
    const expectedCount = gridState.gridSize;
    
    if (currentCards < expectedCount) {
        // Reload current page to get replacement images
        await loadImages();
    }
}

// Update total image count
function updateTotalCount(newCount) {
    gridState.totalImages = newCount;
    gridState.totalPages = Math.ceil(newCount / gridState.gridSize);
    
    document.getElementById('total-images').textContent = newCount;
    document.getElementById('total-pages').textContent = gridState.totalPages;
    
    // If current page is now empty, go back
    if (gridState.currentPage > gridState.totalPages && gridState.totalPages > 0) {
        gridState.currentPage = gridState.totalPages;
        loadImages();
    }
}
```

---

## 5. API Endpoints

### 5.1 POST `/api/delete/<seq_id>`

**Purpose:** Delete single image

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted_seq_id": 1,
    "deleted_filename": "000000_ASH4662_1.jpg",
    "remaining_count": 499
  },
  "message": "Image deleted successfully"
}
```

**Backend Logic:**
```python
@app.route('/api/delete/<int:seq_id>', methods=['POST'])
def delete_image(seq_id: int):
    # Find image
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    directory = Path(project_manager.project_data['directory'])
    
    # Delete image file
    img_path = directory / image['filename']
    if img_path.exists():
        img_path.unlink()
    
    # Delete JSON file if exists
    if image.get('json_filename'):
        json_path = directory / image['json_filename']
        if json_path.exists():
            json_path.unlink()
    
    # Mark as deleted in project JSON (or remove entry)
    image['deleted'] = True
    # OR: project_manager.project_data['images'].remove(image)
    
    project_manager.save_project()
    
    remaining = len([img for img in project_manager.project_data['images'] 
                     if not img.get('deleted', False)])
    
    return jsonify({
        'success': True,
        'data': {
            'deleted_seq_id': seq_id,
            'deleted_filename': image['filename'],
            'remaining_count': remaining
        },
        'message': 'Image deleted successfully'
    })
```

### 5.2 POST `/api/delete/bulk`

**Purpose:** Delete multiple images

**Request Body:**
```json
{
  "seq_ids": [1, 2, 3, 4, 5]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted_count": 5,
    "deleted_filenames": [
      "000000_ASH4662_1.jpg",
      "000001_ABC1234_2.jpg",
      "..."
    ],
    "failed_count": 0,
    "remaining_count": 495
  },
  "message": "5 images deleted successfully"
}
```

**Backend Logic:**
```python
@app.route('/api/delete/bulk', methods=['POST'])
def delete_bulk():
    seq_ids = request.json.get('seq_ids', [])
    
    if not seq_ids:
        return jsonify({'success': False, 'error': 'No images specified'}), 400
    
    directory = Path(project_manager.project_data['directory'])
    
    deleted_filenames = []
    failed_ids = []
    
    for seq_id in seq_ids:
        image = find_image_by_seq_id(seq_id)
        if not image:
            failed_ids.append(seq_id)
            continue
        
        try:
            # Delete files
            img_path = directory / image['filename']
            if img_path.exists():
                img_path.unlink()
            
            if image.get('json_filename'):
                json_path = directory / image['json_filename']
                if json_path.exists():
                    json_path.unlink()
            
            # Mark as deleted
            image['deleted'] = True
            deleted_filenames.append(image['filename'])
            
        except Exception as e:
            failed_ids.append(seq_id)
    
    project_manager.save_project()
    
    remaining = len([img for img in project_manager.project_data['images'] 
                     if not img.get('deleted', False)])
    
    return jsonify({
        'success': True,
        'data': {
            'deleted_count': len(deleted_filenames),
            'deleted_filenames': deleted_filenames,
            'failed_count': len(failed_ids),
            'remaining_count': remaining
        },
        'message': f'{len(deleted_filenames)} images deleted successfully'
    })
```

---

## 6. Keyboard Shortcut

```javascript
// Add to keyboard handler
case 'Delete':
case 'Backspace':
    if (selectionState.selected.size > 0) {
        deleteSelectedImages();
    }
    break;
```

---

## 7. Acceptance Criteria

| ID | Criterion | Test |
|----|-----------|------|
| AC-5.1 | Single delete shows confirmation | Click 🗑️, verify dialog appears |
| AC-5.2 | Bulk delete shows count | Select 5, delete, verify "5 images" in dialog |
| AC-5.3 | Confirmation dialog has Cancel | Click Cancel, nothing deleted |
| AC-5.4 | Skip confirmation setting works | Enable setting, delete without dialog |
| AC-5.5 | Session skip checkbox works | Check "Don't ask again", next delete is immediate |
| AC-5.6 | Image file deleted from disk | Verify file no longer exists |
| AC-5.7 | JSON file deleted with image | Verify .json file also removed |
| AC-5.8 | Image card removed from grid | Deleted image disappears |
| AC-5.9 | Grid refills after delete | Delete on full page, verify new image loads |
| AC-5.10 | Total count updates | Delete 1, total decrements by 1 |
| AC-5.11 | Selection cleared after delete | Delete selected, selection becomes empty |
| AC-5.12 | Delete key triggers delete | Select image, press Delete key |

---

## 8. Error Handling

| Error | Handling |
|-------|----------|
| File not found | Mark as deleted anyway (was already gone) |
| Permission denied | Show error notification, don't mark deleted |
| Disk full | N/A (delete frees space) |
| Partial bulk failure | Report how many succeeded vs failed |

---

## 9. Safety Measures

1. **Confirm by default** - Skip requires explicit setting change
2. **Show file names** - User sees exactly what will be deleted
3. **No actual "move to trash"** - Direct deletion (clear expectation)
4. **Session-only skip** - "Don't ask again" resets on page reload
5. **Log all deletions** - Server logs deleted filenames

```python
# Server-side logging
import logging

logger = logging.getLogger('image_review')

def log_deletion(filename):
    logger.info(f"DELETED: {filename}")
```
