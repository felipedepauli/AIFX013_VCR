"""
Image Review Tool - Flask Application
Phase 2: Grid View Display
"""

from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
from functools import lru_cache
import json
import os
import re
from datetime import datetime
from PIL import Image
import io
import base64

app = Flask(__name__)

# Configuration
PROJECTS_DIR = Path(__file__).parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_QUALITY_FLAGS = ["bin", "review", "ok", "move"]
DEFAULT_PERSPECTIVE_FLAGS = [
    "close-up-day", "close-up-night",
    "pan-day", "pan-night",
    "super_pan_day", "super_pan_night",
    "cropped-day", "cropped-night"
]
DEFAULT_VISIBLE_LABELS = ["color", "brand", "model", "type"]

# Thumbnail sizes based on grid
THUMBNAIL_SIZES = {4: 400, 9: 300, 25: 200, 36: 150}


def generate_thumbnail(image_path: Path, grid_size: int) -> str:
    """
    Generate base64 thumbnail for grid display.
    Preserves aspect ratio with letterboxing (black padding).
    
    Thumbnail sizes based on grid:
    - 2x2 (4): 400x400
    - 3x3 (9): 300x300
    - 5x5 (25): 200x200
    - 6x6 (36): 150x150
    """
    thumb_size = THUMBNAIL_SIZES.get(grid_size, 300)
    
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Preserve aspect ratio with letterboxing
            width, height = img.size
            aspect = width / height
            
            if aspect > 1:
                # Landscape: fit width, pad top/bottom
                new_width = thumb_size
                new_height = int(thumb_size / aspect)
            else:
                # Portrait or square: fit height, pad left/right
                new_height = thumb_size
                new_width = int(thumb_size * aspect)
            
            # Resize maintaining aspect ratio
            img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Create square canvas with black background
            canvas = Image.new('RGB', (thumb_size, thumb_size), (10, 10, 21))  # Match dark theme
            
            # Paste image centered on canvas
            paste_x = (thumb_size - new_width) // 2
            paste_y = (thumb_size - new_height) // 2
            canvas.paste(img, (paste_x, paste_y))
            
            # Encode to base64
            buffer = io.BytesIO()
            canvas.save(buffer, format='JPEG', quality=85)
            base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/jpeg;base64,{base64_str}"
    
    except Exception as e:
        print(f"Error generating thumbnail for {image_path}: {e}")
        return None


@lru_cache(maxsize=500)
def get_cached_thumbnail(image_path: str, grid_size: int) -> str:
    """Cache thumbnails in memory."""
    return generate_thumbnail(Path(image_path), grid_size)


class ProjectManager:
    """Manages project creation, loading, and saving."""
    
    def __init__(self):
        self.current_project = None
        self.project_data = None
    
    def create_project(self, name: str, directory: str, settings: dict) -> dict:
        """Create a new project and scan directory for images."""
        
        # Validate project name
        if not name or not re.match(r'^[a-zA-Z0-9_]+$', name):
            return {
                "success": False,
                "error": "Project name can only contain letters, numbers, and underscores"
            }
        
        # Check if project already exists
        project_file = PROJECTS_DIR / f"{name}.json"
        if project_file.exists():
            return {
                "success": False,
                "error": "A project with this name already exists"
            }
        
        # Validate directory
        dir_path = Path(directory)
        if not dir_path.exists():
            return {
                "success": False,
                "error": "Directory not found. Please select a valid path"
            }
        
        if not dir_path.is_dir():
            return {
                "success": False,
                "error": "Selected path is not a directory"
            }
        
        # Scan for images
        images = self.scan_images(directory, settings)
        
        if not images:
            return {
                "success": False,
                "error": "No images found in selected directory"
            }
        
        # Build project data
        now = datetime.now().isoformat()
        self.project_data = {
            "version": "1.0",
            "project_name": name,
            "directory": str(directory),
            "created": now,
            "updated": now,
            "settings": {
                "skip_delete_confirmation": False,
                "quality_flags": DEFAULT_QUALITY_FLAGS.copy(),
                "perspective_flags": DEFAULT_PERSPECTIVE_FLAGS.copy(),
                "visible_labels": settings.get("visible_labels", DEFAULT_VISIBLE_LABELS.copy()),
                "default_quality_flag": settings.get("default_quality_flag", "review"),
                "default_perspective_flag": settings.get("default_perspective_flag"),
                "grid_size": 9
            },
            "images": images
        }
        
        self.current_project = name
        self.save_project()
        
        return {
            "success": True,
            "data": {
                "project_name": name,
                "directory": str(directory),
                "image_count": len(images),
                "settings": self.project_data["settings"]
            },
            "message": f"Project created with {len(images)} images"
        }
    
    def load_project(self, name: str) -> dict:
        """Load an existing project from JSON."""
        project_file = PROJECTS_DIR / f"{name}.json"
        
        if not project_file.exists():
            return {
                "success": False,
                "error": "Project not found"
            }
        
        try:
            with open(project_file, 'r') as f:
                self.project_data = json.load(f)
            self.current_project = name
            
            # Calculate stats
            total = len(self.project_data["images"])
            deleted = sum(1 for img in self.project_data["images"] if img.get("deleted", False))
            
            return {
                "success": True,
                "data": {
                    "project_name": self.project_data["project_name"],
                    "directory": self.project_data["directory"],
                    "settings": self.project_data["settings"],
                    "image_count": total - deleted,
                    "stats": {
                        "total": total,
                        "deleted": deleted,
                        "active": total - deleted
                    }
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load project: {str(e)}"
            }
    
    def save_project(self) -> None:
        """Save current project to JSON."""
        if not self.current_project or not self.project_data:
            return
        
        self.project_data["updated"] = datetime.now().isoformat()
        project_file = PROJECTS_DIR / f"{self.current_project}.json"
        
        # Atomic write: write to temp file, then rename
        temp_file = project_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w') as f:
                json.dump(self.project_data, f, indent=2)
            temp_file.rename(project_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def list_projects(self) -> list:
        """List all available projects with metadata."""
        projects = []
        
        for project_file in PROJECTS_DIR.glob("*.json"):
            try:
                with open(project_file, 'r') as f:
                    data = json.load(f)
                
                total = len(data.get("images", []))
                deleted = sum(1 for img in data.get("images", []) if img.get("deleted", False))
                
                projects.append({
                    "name": data["project_name"],
                    "directory": data["directory"],
                    "image_count": total - deleted,
                    "created": data.get("created", ""),
                    "updated": data.get("updated", "")
                })
            except:
                continue  # Skip corrupted files
        
        # Sort by updated date (most recent first)
        projects.sort(key=lambda x: x.get("updated", ""), reverse=True)
        return projects
    
    def scan_images(self, directory: str, settings: dict) -> list:
        """Scan directory for image files and create entries."""
        images = []
        dir_path = Path(directory)
        
        # Supported extensions (case-insensitive)
        extensions = {'.jpg', '.jpeg', '.png'}
        
        # Get all image files, sorted by name
        image_files = sorted([
            f for f in dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        ])
        
        default_quality = settings.get("default_quality_flag")
        default_perspective = settings.get("default_perspective_flag")
        
        for seq_id, img_file in enumerate(image_files, start=1):
            json_file = img_file.with_suffix('.json')
            
            entry = {
                "seq_id": seq_id,
                "filename": img_file.name,
                "json_filename": json_file.name if json_file.exists() else None,
                "quality_flags": [default_quality] if default_quality else [],
                "perspective_flags": [default_perspective] if default_perspective else [],
                "deleted": False
            }
            images.append(entry)
        
        return images
    
    def get_image_count(self) -> int:
        """Return count of non-deleted images."""
        if not self.project_data:
            return 0
        return sum(1 for img in self.project_data["images"] if not img.get("deleted", False))


# Global project manager instance
project_manager = ProjectManager()


# ============== Routes ==============

@app.route('/')
def index():
    """Serve main HTML page."""
    return render_template('index.html')


@app.route('/api/projects', methods=['GET'])
def list_projects():
    """List all available projects."""
    projects = project_manager.list_projects()
    return jsonify({
        "success": True,
        "data": {
            "projects": projects
        }
    })


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project."""
    data = request.json
    
    name = data.get('name', '').strip()
    directory = data.get('directory', '').strip()
    settings = data.get('settings', {})
    
    result = project_manager.create_project(name, directory, settings)
    return jsonify(result)


@app.route('/api/projects/<name>', methods=['GET'])
def load_project(name):
    """Load a specific project."""
    result = project_manager.load_project(name)
    return jsonify(result)


@app.route('/api/browse', methods=['POST'])
def browse_directory():
    """Browse filesystem for directory selection."""
    data = request.json
    path = data.get('path', os.path.expanduser('~'))
    
    try:
        dir_path = Path(path)
        
        if not dir_path.exists():
            return jsonify({
                "success": False,
                "error": "Path does not exist"
            })
        
        if not dir_path.is_dir():
            return jsonify({
                "success": False,
                "error": "Path is not a directory"
            })
        
        # List subdirectories
        directories = []
        try:
            for item in sorted(dir_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    directories.append({
                        "name": item.name,
                        "path": str(item)
                    })
        except PermissionError:
            pass  # Can't read some directories
        
        # Count images in current directory
        extensions = {'.jpg', '.jpeg', '.png'}
        image_count = sum(
            1 for f in dir_path.iterdir()
            if f.is_file() and f.suffix.lower() in extensions
        )
        
        return jsonify({
            "success": True,
            "data": {
                "current_path": str(dir_path),
                "parent": str(dir_path.parent) if dir_path.parent != dir_path else None,
                "directories": directories,
                "has_images": image_count > 0,
                "image_count": image_count
            }
        })
    
    except PermissionError:
        return jsonify({
            "success": False,
            "error": "Permission denied. Check folder permissions"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# ============== Phase 10: Filter Panel ==============

@app.route('/api/filter/options', methods=['GET'])
def get_filter_options():
    """Get available filter options with counts."""
    if not project_manager.project_data:
        return jsonify({"success": False, "error": "No project loaded"})
    
    # Get non-deleted images
    images = [img for img in project_manager.project_data['images'] 
              if not img.get('deleted', False)]
    
    directory = Path(project_manager.project_data['directory'])
    
    # Initialize counters
    quality_flags_count = {}
    perspective_flags_count = {}
    color_count = {}
    brand_count = {}
    model_count = {}
    type_count = {}
    sub_type_count = {}
    
    for img in images:
        # Count quality flags
        for flag in img.get('quality_flags', []):
            quality_flags_count[flag] = quality_flags_count.get(flag, 0) + 1
        
        # Count perspective flags
        for flag in img.get('perspective_flags', []):
            perspective_flags_count[flag] = perspective_flags_count.get(flag, 0) + 1
        
        # Load labels from JSON if available
        if img.get('json_filename'):
            json_path = directory / img['json_filename']
            try:
                with open(json_path, 'r') as f:
                    label_data = json.load(f)
                
                # Process each object's labels
                for obj in label_data:
                    color = obj.get('color')
                    if color:
                        color_count[color] = color_count.get(color, 0) + 1
                    
                    brand = obj.get('brand')
                    if brand:
                        brand_count[brand] = brand_count.get(brand, 0) + 1
                    
                    model = obj.get('model')
                    if model:
                        model_count[model] = model_count.get(model, 0) + 1
                    
                    vtype = obj.get('type')
                    if vtype:
                        type_count[vtype] = type_count.get(vtype, 0) + 1
                    
                    sub_type = obj.get('sub_type')
                    if sub_type:
                        sub_type_count[sub_type] = sub_type_count.get(sub_type, 0) + 1
            except:
                pass  # Skip files that can't be read
    
    # Convert to sorted lists of {value, count}
    def to_option_list(count_dict):
        return sorted([{'value': k, 'count': v} for k, v in count_dict.items()], 
                      key=lambda x: (-x['count'], x['value']))
    
    return jsonify({
        'success': True,
        'data': {
            'quality_flags': to_option_list(quality_flags_count),
            'perspective_flags': to_option_list(perspective_flags_count),
            'color': to_option_list(color_count),
            'brand': to_option_list(brand_count),
            'model': to_option_list(model_count),
            'type': to_option_list(type_count),
            'sub_type': to_option_list(sub_type_count),
            'total_images': len(images)
        }
    })


def apply_filters_to_images(images, filters, directory):
    """Apply filter criteria to image list."""
    if not any(filters.values()):
        return images
    
    filtered = []
    
    for img in images:
        # Check quality flags (OR within, AND with other categories)
        if filters.get('quality_flags'):
            img_flags = set(img.get('quality_flags', []))
            if not img_flags.intersection(set(filters['quality_flags'])):
                continue
        
        # Check perspective flags (OR within, AND with other categories)
        if filters.get('perspective_flags'):
            img_flags = set(img.get('perspective_flags', []))
            if not img_flags.intersection(set(filters['perspective_flags'])):
                continue
        
        # Check label filters - need to load JSON
        label_filters = {k: v for k, v in filters.items() 
                        if k in ('color', 'brand', 'model', 'type', 'sub_type') and v}
        
        if label_filters:
            # Must have JSON file to match label filters
            if not img.get('json_filename'):
                continue
            
            json_path = directory / img['json_filename']
            try:
                with open(json_path, 'r') as f:
                    label_data = json.load(f)
                
                # Check if any object matches all label criteria
                matches = False
                for obj in label_data:
                    obj_matches = True
                    for key, values in label_filters.items():
                        obj_value = obj.get(key)
                        if obj_value not in values:
                            obj_matches = False
                            break
                    if obj_matches:
                        matches = True
                        break
                
                if not matches:
                    continue
            except:
                continue  # Skip if can't read JSON
        
        filtered.append(img)
    
    return filtered


# ============== Phase 2: Grid View ==============

@app.route('/api/images', methods=['GET'])
def get_images():
    """Get paginated list of images for current grid page."""
    if not project_manager.project_data:
        return jsonify({
            "success": False,
            "error": "No project loaded"
        })
    
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 9, type=int)
    
    # Validate size - allow any size from 1 to 100
    size = max(1, min(100, size))
    
    # Get non-deleted images
    images = [img for img in project_manager.project_data['images'] 
              if not img.get('deleted', False)]
    
    # Apply filters if provided
    directory = Path(project_manager.project_data['directory'])
    filters = {
        'quality_flags': request.args.getlist('filter_quality_flags'),
        'perspective_flags': request.args.getlist('filter_perspective_flags'),
        'color': request.args.getlist('filter_color'),
        'brand': request.args.getlist('filter_brand'),
        'model': request.args.getlist('filter_model'),
        'type': request.args.getlist('filter_type'),
        'sub_type': request.args.getlist('filter_sub_type')
    }
    images = apply_filters_to_images(images, filters, directory)
    
    total_images = len(images)
    total_pages = max(1, (total_images + size - 1) // size)
    
    # Clamp page to valid range
    page = max(1, min(page, total_pages))
    
    # Get slice for current page
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_images = images[start_idx:end_idx]
    
    # Generate thumbnails and build response
    directory = Path(project_manager.project_data['directory'])
    result = []
    
    for img in page_images:
        img_path = directory / img['filename']
        
        # Use cached thumbnail
        thumbnail = None
        img_width, img_height = 0, 0
        if img_path.exists():
            thumbnail = get_cached_thumbnail(str(img_path), size)
            # Get original image dimensions for bounding box positioning
            try:
                with Image.open(img_path) as pil_img:
                    img_width, img_height = pil_img.size
            except:
                pass
        
        result.append({
            'seq_id': img['seq_id'],
            'filename': img['filename'],
            'thumbnail': thumbnail,
            'img_width': img_width,
            'img_height': img_height,
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


@app.route('/api/settings/grid_size', methods=['POST'])
def update_grid_size():
    """Update grid size setting."""
    if not project_manager.project_data:
        return jsonify({"success": False, "error": "No project loaded"})
    
    data = request.json
    size = data.get('size', 9)
    custom_cols = data.get('custom_cols')
    custom_rows = data.get('custom_rows')
    
    # Validate size - allow any size from 1 to 100
    size = max(1, min(100, size))
    
    project_manager.project_data['settings']['grid_size'] = size
    
    # Store custom grid dimensions if provided
    if custom_cols and custom_rows:
        project_manager.project_data['settings']['custom_grid'] = {
            'cols': max(1, min(10, custom_cols)),
            'rows': max(1, min(10, custom_rows))
        }
    else:
        # Clear custom grid when using preset
        project_manager.project_data['settings'].pop('custom_grid', None)
    
    project_manager.save_project()
    
    return jsonify({"success": True, "data": {"grid_size": size}})


# ============== Phase 3: Label Overlay ==============

def get_label_data_for_image(seq_id: int) -> dict:
    """Helper function to get label data for a single image."""
    if not project_manager.project_data:
        return None
    
    # Find image entry
    image = next((img for img in project_manager.project_data['images'] 
                  if img['seq_id'] == seq_id), None)
    
    if not image:
        return None
    
    if not image.get('json_filename'):
        return {
            'seq_id': seq_id,
            'filename': image['filename'],
            'has_labels': False,
            'objects': []
        }
    
    # Load JSON file
    json_path = Path(project_manager.project_data['directory']) / image['json_filename']
    
    try:
        with open(json_path, 'r') as f:
            label_data = json.load(f)
    except Exception as e:
        return {
            'seq_id': seq_id,
            'filename': image['filename'],
            'has_labels': False,
            'objects': [],
            'error': str(e)
        }
    
    # Get image dimensions for percentage calculation
    img_path = Path(project_manager.project_data['directory']) / image['filename']
    try:
        with Image.open(img_path) as img:
            img_width, img_height = img.size
    except:
        img_width, img_height = 1000, 1000  # Default fallback
    
    # Process objects
    objects = []
    for idx, obj in enumerate(label_data):
        rect = obj.get('rect', [0, 0, 0, 0])
        x, y, w, h = rect
        
        # Calculate percentages
        rect_percent = {
            'x': (x / img_width) * 100,
            'y': (y / img_height) * 100,
            'width': (w / img_width) * 100,
            'height': (h / img_height) * 100
        }
        
        center_percent = {
            'x': ((x + w/2) / img_width) * 100,
            'y': ((y + h/2) / img_height) * 100
        }
        
        objects.append({
            'index': idx,
            'rect': rect,
            'rect_percent': rect_percent,
            'center_percent': center_percent,
            'labels': {
                'color': obj.get('color', None),
                'brand': obj.get('brand', None),
                'model': obj.get('model', None),
                'label': obj.get('label', None),
                'type': obj.get('type', None),
                'sub_type': obj.get('sub_type', None),
                'lp_coords': obj.get('lp_coords', None)
            }
        })
    
    return {
        'seq_id': seq_id,
        'filename': image['filename'],
        'has_labels': True,
        'objects': objects
    }


@app.route('/api/labels/<int:seq_id>')
def get_labels(seq_id: int):
    """Get label data for a specific image."""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    label_data = get_label_data_for_image(seq_id)
    
    if label_data is None:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    return jsonify({
        'success': True,
        'data': label_data
    })


@app.route('/api/labels/batch', methods=['POST'])
def get_labels_batch():
    """Get label data for multiple images (batch loading)."""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    seq_ids = request.json.get('seq_ids', [])
    
    results = []
    for seq_id in seq_ids[:50]:  # Limit batch size to 50
        label_data = get_label_data_for_image(seq_id)
        if label_data:
            results.append(label_data)
    
    return jsonify({
        'success': True,
        'data': results
    })


@app.route('/api/settings/visible_labels', methods=['POST'])
def update_visible_labels():
    """Update visible labels setting."""
    if not project_manager.project_data:
        return jsonify({"success": False, "error": "No project loaded"})
    
    data = request.json
    visible_labels = data.get('visible_labels', DEFAULT_VISIBLE_LABELS)
    
    project_manager.project_data['settings']['visible_labels'] = visible_labels
    project_manager.save_project()
    
    return jsonify({"success": True, "message": "Visible labels updated"})


# ============== Phase 4: Per-Image Controls ==============

def find_image_by_seq_id(seq_id: int):
    """Helper to find image entry by seq_id."""
    if not project_manager.project_data:
        return None
    return next((img for img in project_manager.project_data['images'] 
                 if img['seq_id'] == seq_id), None)


@app.route('/api/image/<int:seq_id>/full')
def get_full_image(seq_id: int):
    """Get full-resolution image for modal view."""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    img_path = Path(project_manager.project_data['directory']) / image['filename']
    
    if not img_path.exists():
        return jsonify({'success': False, 'error': 'Image file not found'}), 404
    
    try:
        with Image.open(img_path) as img:
            # Convert to RGB
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            width, height = img.size
            
            # Resize if very large (for performance)
            max_dim = 1800
            if max(width, height) > max_dim:
                ratio = max_dim / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                width, height = new_size
            
            # Encode to base64
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=92)
            base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return jsonify({
                'success': True,
                'data': {
                    'seq_id': seq_id,
                    'filename': image['filename'],
                    'image': f"data:image/jpeg;base64,{base64_str}",
                    'width': width,
                    'height': height
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Delete Endpoints ==============

@app.route('/api/delete/<int:seq_id>', methods=['POST'])
def delete_image(seq_id: int):
    """Delete a single image by seq_id"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    # Find image
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    directory = Path(project_manager.project_data['directory'])
    deleted_filename = image['filename']
    
    try:
        # Delete image file
        img_path = directory / image['filename']
        if img_path.exists():
            img_path.unlink()
            print(f"DELETED: {img_path}")
        
        # Delete JSON file if exists
        if image.get('json_filename'):
            json_path = directory / image['json_filename']
            if json_path.exists():
                json_path.unlink()
                print(f"DELETED: {json_path}")
        
        # Mark as deleted in project data
        image['deleted'] = True
        project_manager.save_project()
        
        # Count remaining non-deleted images
        remaining = len([img for img in project_manager.project_data['images'] 
                         if not img.get('deleted', False)])
        
        return jsonify({
            'success': True,
            'data': {
                'deleted_seq_id': seq_id,
                'deleted_filename': deleted_filename,
                'remaining_count': remaining
            },
            'message': 'Image deleted successfully'
        })
    
    except PermissionError as e:
        return jsonify({'success': False, 'error': f'Permission denied: {str(e)}'}), 403
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete/bulk', methods=['POST'])
def delete_bulk():
    """Delete multiple images by seq_ids"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
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
            # Delete image file
            img_path = directory / image['filename']
            if img_path.exists():
                img_path.unlink()
                print(f"DELETED: {img_path}")
            
            # Delete JSON file if exists
            if image.get('json_filename'):
                json_path = directory / image['json_filename']
                if json_path.exists():
                    json_path.unlink()
                    print(f"DELETED: {json_path}")
            
            # Mark as deleted
            image['deleted'] = True
            deleted_filenames.append(image['filename'])
            
        except Exception as e:
            print(f"ERROR deleting {seq_id}: {e}")
            failed_ids.append(seq_id)
    
    project_manager.save_project()
    
    # Count remaining non-deleted images
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


# ============== Flag Endpoints (Phase 6) ==============

@app.route('/api/image/<int:seq_id>/flags', methods=['POST'])
def set_image_flags(seq_id: int):
    """Set flags for a single image"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    data = request.json
    
    if data.get('quality_flags') is not None:
        image['quality_flags'] = data['quality_flags']
    
    if data.get('perspective_flags') is not None:
        image['perspective_flags'] = data['perspective_flags']
    
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'quality_flags': image.get('quality_flags', []),
            'perspective_flags': image.get('perspective_flags', [])
        }
    })


@app.route('/api/flags/bulk', methods=['POST'])
def set_bulk_flags():
    """Apply flags to multiple images with mode (set/add/remove)"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    data = request.json
    seq_ids = data.get('seq_ids', [])
    
    quality_flags = data.get('quality_flags', [])
    quality_mode = data.get('quality_mode', 'set')
    
    perspective_flags = data.get('perspective_flags', [])
    perspective_mode = data.get('perspective_mode', 'set')
    
    updated_flags = {}
    
    for seq_id in seq_ids:
        image = find_image_by_seq_id(seq_id)
        if not image:
            continue
        
        # Apply quality flags
        if quality_flags:
            current_quality = set(image.get('quality_flags', []))
            
            if quality_mode == 'set':
                image['quality_flags'] = quality_flags
            elif quality_mode == 'add':
                image['quality_flags'] = list(current_quality.union(quality_flags))
            elif quality_mode == 'remove':
                image['quality_flags'] = list(current_quality - set(quality_flags))
        
        # Apply perspective flags
        if perspective_flags:
            current_perspective = set(image.get('perspective_flags', []))
            
            if perspective_mode == 'set':
                image['perspective_flags'] = perspective_flags
            elif perspective_mode == 'add':
                image['perspective_flags'] = list(current_perspective.union(perspective_flags))
            elif perspective_mode == 'remove':
                image['perspective_flags'] = list(current_perspective - set(perspective_flags))
        
        updated_flags[seq_id] = {
            'quality_flags': image.get('quality_flags', []),
            'perspective_flags': image.get('perspective_flags', [])
        }
    
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'data': {
            'updated_count': len(updated_flags),
            'updated_flags': updated_flags
        }
    })


# ============== Label Editing (Phase 7) ==============

@app.route('/api/labels/<int:seq_id>/<int:object_index>/<label_name>', methods=['PUT'])
def update_label(seq_id: int, object_index: int, label_name: str):
    """Update a single label value in the image's JSON file"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    # Validate label name
    valid_labels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords']
    if label_name not in valid_labels:
        return jsonify({'success': False, 'error': f'Invalid label name: {label_name}'}), 400
    
    # Find image
    image = find_image_by_seq_id(seq_id)
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    if not image.get('json_filename'):
        return jsonify({'success': False, 'error': 'No JSON file for this image'}), 404
    
    json_path = Path(project_manager.project_data['directory']) / image['json_filename']
    
    # Read current JSON
    try:
        with open(json_path, 'r') as f:
            label_data = json.load(f)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read JSON: {e}'}), 500
    
    # Validate object index
    if object_index < 0 or object_index >= len(label_data):
        return jsonify({'success': False, 'error': f'Invalid object index: {object_index}'}), 400
    
    # Get new value
    new_value = request.json.get('value')
    old_value = label_data[object_index].get(label_name)
    
    # Update
    label_data[object_index][label_name] = new_value if new_value else ''
    
    # Write back (atomic)
    temp_path = json_path.with_suffix('.json.tmp')
    try:
        with open(temp_path, 'w') as f:
            json.dump(label_data, f, indent=2)
        
        temp_path.replace(json_path)
        print(f"LABEL UPDATE: {image['filename']} [{object_index}].{label_name}: {old_value} -> {new_value}")
        
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'success': False, 'error': f'Failed to write JSON: {e}'}), 500
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'object_index': object_index,
            'label_name': label_name,
            'old_value': old_value,
            'new_value': new_value
        }
    })


# ============== Settings (Phase 8) ==============

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Save all settings to project JSON"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    new_settings = request.json
    
    # Validate and update only known keys
    valid_keys = [
        'skip_delete_confirmation',
        'quality_flags',
        'perspective_flags', 
        'visible_labels',
        'default_quality_flag',
        'default_perspective_flag',
        'grid_size'
    ]
    
    # Initialize settings if not exists
    if 'settings' not in project_manager.project_data:
        project_manager.project_data['settings'] = {}
    
    for key in new_settings:
        if key in valid_keys:
            project_manager.project_data['settings'][key] = new_settings[key]
    
    project_manager.project_data['updated'] = datetime.now().isoformat()
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'message': 'Settings saved'
    })


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current project settings"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    settings = project_manager.project_data.get('settings', {})
    
    # Apply defaults
    defaults = {
        'skip_delete_confirmation': False,
        'quality_flags': ['bin', 'review', 'ok', 'move'],
        'perspective_flags': [
            'close-up-day', 'close-up-night',
            'pan-day', 'pan-night',
            'super_pan_day', 'super_pan_night',
            'cropped-day', 'cropped-night'
        ],
        'visible_labels': ['color', 'brand', 'model', 'type'],
        'default_quality_flag': None,
        'default_perspective_flag': None,
        'grid_size': 9
    }
    
    for key, value in defaults.items():
        if key not in settings:
            settings[key] = value
    
    return jsonify({
        'success': True,
        'data': settings
    })


@app.route('/api/flags/apply-to-all', methods=['POST'])
def apply_flag_to_all():
    """Apply a flag to all non-deleted images, removing existing flags of that type"""
    if not project_manager.project_data:
        return jsonify({'success': False, 'error': 'No project loaded'}), 400
    
    data = request.json
    flag_type = data.get('type')  # 'quality' or 'perspective'
    flag_value = data.get('flag')
    
    if flag_type not in ['quality', 'perspective']:
        return jsonify({'success': False, 'error': 'Invalid flag type'}), 400
    
    if not flag_value:
        return jsonify({'success': False, 'error': 'No flag specified'}), 400
    
    flag_key = 'quality_flags' if flag_type == 'quality' else 'perspective_flags'
    
    updated_count = 0
    for image in project_manager.project_data.get('images', []):
        if image.get('deleted', False):
            continue
        
        # Replace all flags of this type with just the new one
        image[flag_key] = [flag_value]
        updated_count += 1
    
    project_manager.save_project()
    
    print(f"APPLIED FLAG: {flag_type}={flag_value} to {updated_count} images")
    
    return jsonify({
        'success': True,
        'data': {
            'updated_count': updated_count,
            'flag_type': flag_type,
            'flag_value': flag_value
        },
        'message': f'Applied {flag_value} to {updated_count} images'
    })


# ============== Main ==============

if __name__ == '__main__':
    print("=" * 50)
    print("🖼️  Image Review Tool - Phase 8")
    print("=" * 50)
    print(f"Projects directory: {PROJECTS_DIR.absolute()}")
    print("Starting server at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
