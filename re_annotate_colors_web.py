#!/usr/bin/env python3
"""Web-based re-annotation tool for fixing vehicle color labels.

Interactive web interface to review and correct color labels.
Run with: python re_annotate_colors_web.py
Then open: http://localhost:5000
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, send_file
import base64
from PIL import Image
import io


# Define valid colors and vehicle types (contamination)
VALID_COLORS = [
    "black", "blue", "brown", "gray", "green", 
    "red", "silver", "white", "yellow", "unknown"
]

VEHICLE_TYPES = [
    "bus", "car", "motorcycle", "pickup", "suv", "tow", "truck"
]

app = Flask(__name__)

# Global state
state = {
    'records': [],
    'problematic_indices': [],
    'current_index': 0,
    'show_only_problematic': False,
    'modified_records': set(),
    'deleted_indices': set(),
    'history': [],
    'fixed_count': 0,
    'manifest_path': Path("data/manifests/manifest_ready.jsonl")
}


def load_manifest():
    """Load manifest from file."""
    state['records'] = []
    with open(state['manifest_path'], 'r') as f:
        for line in f:
            state['records'].append(json.loads(line))
    
    state['problematic_indices'] = [
        i for i, r in enumerate(state['records']) 
        if r['label'] in VEHICLE_TYPES
    ]
    state['modified_records'] = set()
    state['deleted_indices'] = set()
    state['history'] = []
    state['fixed_count'] = 0


def get_current_indices():
    """Get list of indices based on filter."""
    if state['show_only_problematic']:
        return [i for i in state['problematic_indices'] if i not in state['deleted_indices']]
    return [i for i in range(len(state['records'])) if i not in state['deleted_indices']]


def get_image_base64(record):
    """Get base64 encoded image for display."""
    crop_path = Path(record.get('crop_path', ''))
    
    if not crop_path.exists():
        # Try image_path with bbox
        img_path = Path(record.get('image_path', ''))
        if img_path.exists():
            img = Image.open(img_path).convert('RGB')
            bbox = record.get('bbox_xyxy', [0, 0, img.width, img.height])
            img = img.crop(bbox)
        else:
            img = Image.new('RGB', (400, 400), color='gray')
    else:
        img = Image.open(crop_path).convert('RGB')
    
    # Resize for display (max 800x800)
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/jpeg;base64,{img_str}"


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Color Re-Annotation Tool</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 30px;
        }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 400px;
            gap: 0;
            min-height: 600px;
        }
        .image-panel {
            background: #fafafa;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px;
            border-right: 1px solid #e0e0e0;
        }
        .image-container {
            max-width: 100%;
            text-align: center;
        }
        .image-container img {
            max-width: 100%;
            max-height: 70vh;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .controls-panel {
            padding: 30px;
            overflow-y: auto;
            max-height: 85vh;
        }
        .stats-box, .info-box, .label-box, .selector-box, .filter-box, .nav-box {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .stats-box h3, .info-box h3, .label-box h3, .selector-box h3, .filter-box h3, .nav-box h3 {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }
        .label-current {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .label-valid { color: #4caf50; }
        .label-invalid { color: #f44336; }
        .label-status {
            font-size: 14px;
            padding: 5px 10px;
            border-radius: 4px;
            display: inline-block;
        }
        .status-valid { background: #e8f5e9; color: #2e7d32; }
        .status-invalid { background: #ffebee; color: #c62828; }
        select, input[type="checkbox"] {
            width: 100%;
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            font-size: 16px;
            margin: 10px 0;
        }
        button {
            width: 100%;
            padding: 12px 20px;
            margin: 5px 0;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #667eea;
            color: white;
        }
        .btn-primary:hover { background: #5568d3; }
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        .btn-secondary:hover { background: #5a6268; }
        .btn-success {
            background: #28a745;
            color: white;
        }
        .btn-success:hover { background: #218838; }
        .btn-danger {
            background: #dc3545;
            color: white;
        }
        .btn-danger:hover { background: #c82333; }
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .btn-nav-group {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 5px;
        }
        .btn-nav {
            padding: 8px;
            font-size: 12px;
        }
        .stat-line {
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 14px;
        }
        .stat-label { color: #666; }
        .stat-value { font-weight: 600; }
        .info-line {
            margin: 5px 0;
            font-size: 13px;
            color: #555;
        }
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s;
        }
        .toast-success { background: #28a745; }
        .toast-error { background: #dc3545; }
        .toast-info { background: #17a2b8; }
        @keyframes slideIn {
            from { transform: translateX(400px); }
            to { transform: translateX(0); }
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 10px 0;
        }
        .checkbox-container input[type="checkbox"] {
            width: auto;
            margin: 0;
        }
        .shortcut-hint {
            font-size: 11px;
            color: #999;
            margin-top: 10px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 Vehicle Color Re-Annotation Tool</h1>
            <p>Review and correct vehicle color labels in your dataset</p>
        </div>
        
        <div class="main-content">
            <div class="image-panel">
                <div class="image-container">
                    <img id="current-image" src="" alt="Vehicle image">
                </div>
            </div>
            
            <div class="controls-panel">
                <div class="stats-box">
                    <h3>📊 Statistics</h3>
                    <div class="stat-line">
                        <span class="stat-label">Total images:</span>
                        <span class="stat-value" id="stat-total">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Problematic:</span>
                        <span class="stat-value" id="stat-problematic">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Fixed:</span>
                        <span class="stat-value" id="stat-fixed">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Unsaved changes:</span>
                        <span class="stat-value" id="stat-modified">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Deleted:</span>
                        <span class="stat-value" id="stat-deleted">0</span>
                    </div>
                </div>
                
                <div class="info-box">
                    <h3>📷 Current Image</h3>
                    <div class="info-line" id="info-id"></div>
                    <div class="info-line" id="info-split"></div>
                    <div class="info-line" id="info-index"></div>
                </div>
                
                <div class="label-box">
                    <h3>🏷️ Current Label</h3>
                    <div class="label-current" id="current-label">-</div>
                    <span class="label-status" id="label-status"></span>
                </div>
                
                <div class="selector-box">
                    <h3>✏️ Change Color To</h3>
                    <select id="color-selector">
                        {% for color in colors %}
                        <option value="{{ color }}">{{ color }}</option>
                        {% endfor %}
                    </select>
                    <div class="btn-group">
                        <button class="btn-primary" onclick="saveChange()">💾 Save</button>
                        <button class="btn-secondary" onclick="undoLast()" id="undo-btn">↶ Undo</button>
                    </div>
                    <button class="btn-danger" onclick="deleteImage()" style="margin-top: 10px;">🗑️ Delete Image</button>
                </div>
                
                <div class="filter-box">
                    <h3>🔍 Filter</h3>
                    <div class="checkbox-container">
                        <input type="checkbox" id="filter-problematic" onchange="toggleFilter()">
                        <label for="filter-problematic">Show only problematic images</label>
                    </div>
                </div>
                
                <div class="nav-box">
                    <h3>🧭 Navigation</h3>
                    <div style="text-align: center; margin: 10px 0; font-weight: 600;" id="nav-position">
                        - / -
                    </div>
                    <div class="btn-nav-group">
                        <button class="btn-secondary btn-nav" onclick="navigate('first')">⏮ First</button>
                        <button class="btn-secondary btn-nav" onclick="navigate('prev')">◀ Prev</button>
                        <button class="btn-secondary btn-nav" onclick="navigate('next')">Next ▶</button>
                        <button class="btn-secondary btn-nav" onclick="navigate('last')">Last ⏭</button>
                    </div>
                    <div class="shortcut-hint">Use ← → keys to navigate</div>
                </div>
                
                <div style="margin-top: 20px;">
                    <button class="btn-success" onclick="saveManifest()">💾 Save All Changes to Manifest</button>
                    <button class="btn-secondary" onclick="reloadManifest()">🔄 Reload Manifest</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentData = null;
        
        // Load initial data
        async function loadData() {
            const response = await fetch('/api/current');
            currentData = await response.json();
            updateUI();
        }
        
        function updateUI() {
            if (!currentData) return;
            
            // Update image
            document.getElementById('current-image').src = currentData.image;
            
            // Update stats
            document.getElementById('stat-total').textContent = currentData.stats.total.toLocaleString();
            document.getElementById('stat-problematic').textContent = 
                `${currentData.stats.problematic.toLocaleString()} (${currentData.stats.problematic_pct}%)`;
            document.getElementById('stat-fixed').textContent = currentData.stats.fixed;
            document.getElementById('stat-modified').textContent = currentData.stats.modified;
            document.getElementById('stat-deleted').textContent = currentData.stats.deleted;
            
            // Update info
            document.getElementById('info-id').textContent = `ID: ${currentData.record.id}`;
            document.getElementById('info-split').textContent = `Split: ${currentData.record.split}`;
            document.getElementById('info-index').textContent = `Index: ${currentData.record.index} / ${currentData.stats.total}`;
            
            // Update label
            const label = currentData.record.label;
            const labelEl = document.getElementById('current-label');
            const statusEl = document.getElementById('label-status');
            
            labelEl.textContent = label;
            
            if (currentData.record.is_problematic) {
                labelEl.className = 'label-current label-invalid';
                statusEl.textContent = '⚠️ VEHICLE TYPE (should be COLOR!)';
                statusEl.className = 'label-status status-invalid';
            } else {
                labelEl.className = 'label-current label-valid';
                statusEl.textContent = '✓ Valid color';
                statusEl.className = 'label-status status-valid';
            }
            
            // Update selector
            document.getElementById('color-selector').value = label;
            
            // Update navigation
            document.getElementById('nav-position').textContent = 
                `${currentData.position.current} / ${currentData.position.total}`;
            
            // Update undo button
            document.getElementById('undo-btn').disabled = currentData.stats.history === 0;
        }
        
        async function saveChange() {
            const newColor = document.getElementById('color-selector').value;
            const response = await fetch('/api/save_change', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_color: newColor })
            });
            const result = await response.json();
            
            if (result.success) {
                showToast(result.message, 'success');
                await loadData();
            } else {
                showToast(result.message, 'error');
            }
        }
        
        async function undoLast() {
            const response = await fetch('/api/undo', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                showToast(result.message, 'info');
                await loadData();
            } else {
                showToast(result.message, 'error');
            }
        }
        
        async function deleteImage() {
            if (!confirm('Delete this image from the dataset?\\n\\nThis will be saved when you click "Save All Changes".')) {
                return;
            }
            
            const response = await fetch('/api/delete_image', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                showToast(result.message, 'success');
                await loadData();
            } else {
                showToast(result.message, 'error');
            }
        }
        
        async function navigate(direction) {
            const response = await fetch('/api/navigate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ direction })
            });
            const result = await response.json();
            
            if (result.success) {
                await loadData();
            }
        }
        
        async function toggleFilter() {
            const checked = document.getElementById('filter-problematic').checked;
            const response = await fetch('/api/toggle_filter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ show_only_problematic: checked })
            });
            const result = await response.json();
            
            if (result.success) {
                showToast(result.message, 'info');
                await loadData();
            } else {
                showToast(result.message, 'error');
            }
        }
        
        async function saveManifest() {
            if (currentData.stats.modified === 0) {
                showToast('No changes to save!', 'info');
                return;
            }
            
            if (!confirm(`Save ${currentData.stats.modified} changes to manifest?\\n\\nA backup will be created.`)) {
                return;
            }
            
            const response = await fetch('/api/save_manifest', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                showToast(result.message, 'success');
                await loadData();
            } else {
                showToast(result.message, 'error');
            }
        }
        
        async function reloadManifest() {
            if (currentData.stats.modified > 0) {
                if (!confirm(`Discard ${currentData.stats.modified} unsaved changes?`)) {
                    return;
                }
            }
            
            const response = await fetch('/api/reload', { method: 'POST' });
            const result = await response.json();
            
            showToast(result.message, 'info');
            await loadData();
        }
        
        function showToast(message, type) {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            setTimeout(() => toast.remove(), 3000);
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'SELECT') return;
            
            if (e.key === 'ArrowLeft') navigate('prev');
            else if (e.key === 'ArrowRight') navigate('next');
            else if (e.key === 'Home') navigate('first');
            else if (e.key === 'End') navigate('last');
            else if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveChange();
            }
            else if (e.ctrlKey && e.key === 'z') {
                e.preventDefault();
                undoLast();
            }
        });
        
        // Load on start
        loadData();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main page."""
    return render_template_string(HTML_TEMPLATE, colors=VALID_COLORS)


@app.route('/api/current')
def api_current():
    """Get current image data."""
    if not state['records']:
        return jsonify({'error': 'No records loaded'}), 400
    
    idx = state['current_index']
    record = state['records'][idx]
    
    indices = get_current_indices()
    try:
        pos = indices.index(idx) + 1
    except ValueError:
        pos = 0
    
    return jsonify({
        'image': get_image_base64(record),
        'record': {
            'id': record['id'],
            'label': record['label'],
            'split': record.get('split', 'N/A'),
            'index': idx + 1,
            'is_problematic': record['label'] in VEHICLE_TYPES
        },
        'stats': {
            'total': len(state['records']),
            'problematic': len(state['problematic_indices']),
            'problematic_pct': round(100 * len(state['problematic_indices']) / len(state['records']), 1),
            'fixed': state['fixed_count'],
            'modified': len(state['modified_records']),
            'deleted': len(state['deleted_indices']),
            'history': len(state['history'])
        },
        'position': {
            'current': pos,
            'total': len(indices)
        }
    })


@app.route('/api/save_change', methods=['POST'])
def api_save_change():
    """Save color change."""
    data = request.json
    new_color = data.get('new_color')
    
    if not new_color or new_color not in VALID_COLORS:
        return jsonify({'success': False, 'message': 'Invalid color'}), 400
    
    idx = state['current_index']
    record = state['records'][idx]
    old_label = record['label']
    
    if new_color == old_label:
        return jsonify({'success': False, 'message': 'Selected color is the same as current!'}), 400
    
    # Save to history
    state['history'].append({
        'index': idx,
        'old_label': old_label,
        'old_label_idx': record['label_idx'],
        'new_label': new_color
    })
    
    # Update record
    record['label'] = new_color
    record['label_idx'] = VALID_COLORS.index(new_color)
    
    # Track modification
    state['modified_records'].add(idx)
    
    # Update fixed count
    if old_label in VEHICLE_TYPES and new_color in VALID_COLORS:
        state['fixed_count'] += 1
        if idx in state['problematic_indices']:
            state['problematic_indices'].remove(idx)
    
    # Auto-navigate to next
    indices = get_current_indices()
    try:
        pos = indices.index(idx)
        if pos < len(indices) - 1:
            state['current_index'] = indices[pos + 1]
    except ValueError:
        pass
    
    return jsonify({
        'success': True,
        'message': f'Changed: {old_label} → {new_color}'
    })


@app.route('/api/undo', methods=['POST'])
def api_undo():
    """Undo last change."""
    if not state['history']:
        return jsonify({'success': False, 'message': 'Nothing to undo'}), 400
    
    last_change = state['history'].pop()
    idx = last_change['index']
    
    # Restore
    state['records'][idx]['label'] = last_change['old_label']
    state['records'][idx]['label_idx'] = last_change['old_label_idx']
    
    # Update counts
    if last_change['old_label'] in VEHICLE_TYPES:
        state['fixed_count'] -= 1
        if idx not in state['problematic_indices']:
            state['problematic_indices'].append(idx)
            state['problematic_indices'].sort()
    
    state['current_index'] = idx
    
    return jsonify({
        'success': True,
        'message': f'Undone change at index {idx + 1}'
    })


@app.route('/api/delete_image', methods=['POST'])
def api_delete_image():
    """Delete current image from dataset."""
    idx = state['current_index']
    
    if idx in state['deleted_indices']:
        return jsonify({'success': False, 'message': 'Image already deleted'}), 400
    
    # Mark as deleted
    state['deleted_indices'].add(idx)
    state['modified_records'].add(idx)
    
    # Update problematic count
    if idx in state['problematic_indices']:
        state['problematic_indices'].remove(idx)
    
    # Navigate to next available image
    indices = get_current_indices()
    if indices:
        # Find next index after current
        next_indices = [i for i in indices if i > idx]
        if next_indices:
            state['current_index'] = next_indices[0]
        else:
            # No next, go to first
            state['current_index'] = indices[0]
    
    return jsonify({
        'success': True,
        'message': f'Image deleted (will be removed when manifest is saved)'
    })


@app.route('/api/navigate', methods=['POST'])
def api_navigate():
    """Navigate between images."""
    data = request.json
    direction = data.get('direction')
    
    indices = get_current_indices()
    if not indices:
        return jsonify({'success': False}), 400
    
    try:
        pos = indices.index(state['current_index'])
    except ValueError:
        pos = 0
    
    if direction == 'first':
        state['current_index'] = indices[0]
    elif direction == 'last':
        state['current_index'] = indices[-1]
    elif direction == 'prev' and pos > 0:
        state['current_index'] = indices[pos - 1]
    elif direction == 'next' and pos < len(indices) - 1:
        state['current_index'] = indices[pos + 1]
    
    return jsonify({'success': True})


@app.route('/api/toggle_filter', methods=['POST'])
def api_toggle_filter():
    """Toggle filter."""
    data = request.json
    state['show_only_problematic'] = data.get('show_only_problematic', False)
    
    if state['show_only_problematic']:
        if not state['problematic_indices']:
            state['show_only_problematic'] = False
            return jsonify({
                'success': False,
                'message': 'No problematic images found!'
            })
        state['current_index'] = state['problematic_indices'][0]
        return jsonify({
            'success': True,
            'message': f'Showing {len(state["problematic_indices"])} problematic images'
        })
    else:
        state['current_index'] = 0
        return jsonify({
            'success': True,
            'message': 'Showing all images'
        })


@app.route('/api/save_manifest', methods=['POST'])
def api_save_manifest():
    """Save manifest to disk."""
    if not state['modified_records']:
        return jsonify({'success': False, 'message': 'No changes to save'}), 400
    
    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = state['manifest_path'].parent / f"{state['manifest_path'].stem}_backup_{timestamp}.jsonl"
    shutil.copy(state['manifest_path'], backup_path)
    
    # Count for message
    modified_count = len(state['modified_records'])
    fixed_count = state['fixed_count']
    deleted_count = len(state['deleted_indices'])
    
    # Write (excluding deleted records)
    with open(state['manifest_path'], 'w') as f:
        for i, record in enumerate(state['records']):
            if i not in state['deleted_indices']:
                f.write(json.dumps(record) + '\n')
    
    # Update class_to_idx.json
    class_mapping_path = Path("data/processed/class_to_idx.json")
    new_mapping = {color: idx for idx, color in enumerate(sorted(VALID_COLORS))}
    with open(class_mapping_path, 'w') as f:
        json.dump(new_mapping, f, indent=2)
    
    # Reload manifest to update indices
    load_manifest()
    state['current_index'] = 0
    
    return jsonify({
        'success': True,
        'message': f'Saved {modified_count} changes! Fixed {fixed_count} problematic. Deleted {deleted_count} images. Backup: {backup_path.name}'
    })


@app.route('/api/reload', methods=['POST'])
def api_reload():
    """Reload manifest from disk."""
    load_manifest()
    state['current_index'] = 0
    return jsonify({
        'success': True,
        'message': 'Manifest reloaded (all unsaved changes discarded)'
    })


def main():
    """Main entry point."""
    print("🎨 Vehicle Color Re-Annotation Tool (Web Version)")
    print("=" * 60)
    
    if not state['manifest_path'].exists():
        print(f"Error: Manifest not found at {state['manifest_path']}")
        return 1
    
    print(f"Loading manifest: {state['manifest_path']}")
    load_manifest()
    
    print(f"\n✓ Loaded {len(state['records']):,} images")
    print(f"✓ Found {len(state['problematic_indices']):,} problematic images")
    
    print("\n" + "=" * 60)
    print("Starting web server...")
    print("\n🌐 Open in your browser: http://localhost:5000")
    print("\n⌨️  Keyboard Shortcuts:")
    print("   ← / →        : Previous / Next image")
    print("   Home / End   : First / Last image")
    print("   Ctrl+S       : Save current change")
    print("   Ctrl+Z       : Undo last change")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
    
    return 0


if __name__ == "__main__":
    exit(main())
