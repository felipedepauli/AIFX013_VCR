# Image Review Tool

**Status:** Phase 4 Complete ✓  
**Current Phase:** Per-Image Controls

## Quick Start

```bash
cd tools/image_review
pip install -r requirements.txt
python app.py
# Open: http://localhost:5000
```

## Testing Phase 4

### Test 4.1: Control Buttons
- [ ] Hover over image → controls appear (checkbox, 🔍, 🗑️, 🏷️)
- [ ] Checkbox on left, buttons on right
- [ ] Controls stay visible when image is selected

### Test 4.2: Selection
- [ ] Click checkbox → image gets selection highlight (blue tint)
- [ ] Selected count updates in footer
- [ ] Ctrl+click to toggle individual images
- [ ] Shift+click to select range between last clicked and current

### Test 4.3: Selection Shortcuts
- [ ] Press `A` → select all images on current page
- [ ] Press `D` → deselect all images
- [ ] Press `Escape` → deselect all images
- [ ] Toolbar "☑ All" / "☐ None" buttons work

### Test 4.4: Open Wider Modal
- [ ] Click 🔍 button → full-size image modal opens
- [ ] Modal shows larger image with labels
- [ ] Filename and seq_id shown at bottom
- [ ] Press `Escape` → modal closes
- [ ] Arrow keys ←/→ navigate between images in modal
- [ ] ◀/▶ buttons navigate between images
- [ ] Hover over image inside grid, press `Space` → opens modal

### Test 4.5: Bounding Boxes in Modal
- [ ] Bounding boxes visible in modal (if enabled)
- [ ] Labels use vehicle colors in modal

## Current Features
- ✅ Project setup and management
- ✅ Image grid (2×2, 3×3, 5×5, 6×6)
- ✅ Thumbnail generation with caching
- ✅ Pagination with page navigation
- ✅ Keyboard shortcuts
- ✅ Label overlays with vehicle colors
- ✅ Bounding box display
- ✅ Per-image controls (select, expand, delete, flag buttons)
- ✅ Multi-selection (checkbox, Ctrl+click, Shift+click)
- ✅ Open Wider modal with full-size image
- ✅ Modal navigation (arrows)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← | Previous page (or prev image in modal) |
| → | Next page (or next image in modal) |
| 1 | 2×2 grid |
| 2 | 3×3 grid |
| 3 | 5×5 grid |
| 4 | 6×6 grid |
| A | Select all |
| D | Deselect all |
| Escape | Close modal / Deselect all |
| Space | Open hovered image in modal |

## Known Limitations
- Delete button shows notification (Phase 5)
- Flag button shows notification (Phase 6)
- Settings panel not implemented (Phase 8)

## Next Phase

**Phase 5: Delete Operations** will add:
- Single image deletion
- Bulk deletion of selected images
- Confirmation dialog
- Soft delete (mark deleted, not remove file)
