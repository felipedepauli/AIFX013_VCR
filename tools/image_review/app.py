"""
Image Review Tool - Flask Application
Phase 2: Grid View Display
"""

from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
from functools import lru_cache, wraps
import json
import os
import re
import hashlib
from datetime import datetime
from PIL import Image
import io
import base64
import numpy as np
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError


def stable_hash(s: str) -> int:
    """Generate a stable hash that is consistent across Python sessions."""
    return int(hashlib.md5(s.encode()).hexdigest(), 16) % (10**9)

app = Flask(__name__)

# Configuration
PROJECTS_DIR = Path(__file__).parent / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

# Default settings
DEFAULT_QUALITY_FLAGS = ["brass", "bronze", "silver", "gold"]

DEFAULT_VISIBLE_LABELS = ["color", "brand", "model", "type"]

# Thumbnail sizes based on grid
THUMBNAIL_SIZES = {4: 400, 9: 300, 25: 200, 36: 150, 35: 150}

# ============== Phase 23: MongoDB Dataset Registry ==============
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = 'image_review_tool'
COLLECTION_NAME = 'datasets'
DATASET_THUMBNAIL_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'static', 'cache', 'thumbnails')
DATASET_THUMBNAIL_SIZE = (200, 200)

mongo_client = None
db = None
datasets_collection = None
mongo_available = False


def init_mongodb():
    """Initialize MongoDB connection. Graceful fallback if unavailable."""
    global mongo_client, db, datasets_collection, mongo_available
    try:
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        mongo_client.admin.command('ping')  # Test connection
        db = mongo_client[DB_NAME]
        datasets_collection = db[COLLECTION_NAME]
        # Create unique index on root_path
        datasets_collection.create_index('root_path', unique=True)
        mongo_available = True
        print(f"[MongoDB] Connected to {MONGODB_URI}/{DB_NAME}")
    except Exception as e:
        mongo_available = False
        print(f"[MongoDB] Not available: {e}. Dashboard features disabled.")


def requires_mongodb(f):
    """Decorator: returns 503 if MongoDB is not available."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not mongo_available:
            return jsonify({
                'error': 'MongoDB not available',
                'message': 'Dashboard features require MongoDB. Start mongod and restart the app.'
            }), 503
        return f(*args, **kwargs)
    return decorated


def _compute_dataset_statistics(root_path):
    """Scan all JSON label files and compute comprehensive dataset statistics.
    
    Returns normalized centroids and proportional areas (relative to image size).
    """
    root = Path(root_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    total_images = 0
    total_vehicles = 0
    class_counts = {'car': 0, 'motorcycle': 0, 'truck': 0, 'bus': 0}
    centroids_x = []  # normalized [0,1]
    centroids_y = []  # normalized [0,1]
    norm_areas = []   # proportion of image area [0,1]
    area_by_class = {}  # {class_name: [list of norm areas]}
    vehicles_per_image = []  # count of vehicles in each image

    for img_path in root.rglob('*'):
        if img_path.suffix.lower() not in image_extensions:
            continue
        total_images += 1

        json_path = img_path.with_suffix('.json')
        if not json_path.exists():
            vehicles_per_image.append(0)
            continue

        # Get image dimensions for normalization
        try:
            with Image.open(img_path) as img:
                img_w, img_h = img.size
        except Exception:
            img_w, img_h = 0, 0

        if img_w == 0 or img_h == 0:
            vehicles_per_image.append(0)
            continue

        try:
            with open(json_path, 'r') as f:
                objects = json.load(f)
            if not isinstance(objects, list):
                objects = [objects]

            img_vehicle_count = 0
            for obj in objects:
                label = obj.get('label', '').lower()
                if label in class_counts:
                    class_counts[label] += 1
                    total_vehicles += 1
                    img_vehicle_count += 1

                rect = obj.get('rect')
                if rect and len(rect) == 4:
                    x, y, w, h = rect
                    # Normalized centroid
                    cx = (x + w / 2) / img_w
                    cy = (y + h / 2) / img_h
                    centroids_x.append(cx)
                    centroids_y.append(cy)
                    # Proportional area (bbox area / image area)
                    prop_area = (w * h) / (img_w * img_h)
                    norm_areas.append(prop_area)
                    # Track area per class
                    if label in class_counts:
                        area_by_class.setdefault(label, []).append(prop_area)
            vehicles_per_image.append(img_vehicle_count)
        except (json.JSONDecodeError, KeyError, TypeError):
            vehicles_per_image.append(0)
            continue

    spatial = {}
    if centroids_x:
        spatial = {
            'centroid_mean': {
                'x': round(float(np.mean(centroids_x)), 4),
                'y': round(float(np.mean(centroids_y)), 4)
            },
            'centroid_variance': {
                'x': round(float(np.var(centroids_x)), 6),
                'y': round(float(np.var(centroids_y)), 6)
            },
            'norm_area_mean': round(float(np.mean(norm_areas)), 6),
            'norm_area_variance': round(float(np.var(norm_areas)), 6),
        }

    # Compute per-class area stats
    class_area_stats = {}
    for cls, areas in area_by_class.items():
        arr = np.array(areas)
        class_area_stats[cls] = {
            'mean': round(float(np.mean(arr)), 6),
            'variance': round(float(np.var(arr)), 6),
        }

    # Compute vehicles-per-image stats
    vpi_stats = {}
    if vehicles_per_image:
        vpi_arr = np.array(vehicles_per_image)
        vpi_stats = {
            'mean': round(float(np.mean(vpi_arr)), 4),
            'variance': round(float(np.var(vpi_arr)), 4),
        }

    return {
        'total_images': total_images,
        'total_vehicles': total_vehicles,
        'class_counts': class_counts,
        'class_area_stats': class_area_stats,
        'vehicles_per_image': vpi_stats,
        'spatial': spatial,
        'computed_at': datetime.utcnow().isoformat()
    }



def _generate_dataset_thumbnails(root_path, dataset_id):
    """Generate 4 representative thumbnails: 1st, 25%, 75%, last."""
    root = Path(root_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    all_images = sorted([
        p for p in root.rglob('*')
        if p.suffix.lower() in image_extensions
    ])

    if not all_images:
        return []

    n = len(all_images)
    indices = [0, n // 4, (3 * n) // 4, n - 1]
    indices = list(dict.fromkeys(indices))  # Remove duplicates for small datasets

    os.makedirs(DATASET_THUMBNAIL_CACHE_DIR, exist_ok=True)

    thumbnail_paths = []
    for i, idx in enumerate(indices):
        img_path = all_images[idx]
        thumb_filename = f"{dataset_id}_{i}.jpg"
        thumb_path = os.path.join(DATASET_THUMBNAIL_CACHE_DIR, thumb_filename)

        try:
            with Image.open(img_path) as img:
                img.thumbnail(DATASET_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                img = img.convert('RGB')
                img.save(thumb_path, 'JPEG', quality=85)
            thumbnail_paths.append(thumb_filename)
        except Exception as e:
            print(f"[Thumbnails] Failed to generate {thumb_filename}: {e}")

    return thumbnail_paths


def _cleanup_dataset_thumbnails(dataset_id):
    """Delete cached thumbnails for a dataset."""
    for i in range(4):
        thumb_path = os.path.join(DATASET_THUMBNAIL_CACHE_DIR, f"{dataset_id}_{i}.jpg")
        if os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except OSError:
                pass


# ============== Phase 26: Dataset Sync Helpers ==============

def _find_registered_dataset(root_path):
    """Find a registered dataset by root_path. Returns MongoDB doc or None."""
    if not mongo_available or datasets_collection is None:
        return None
    try:
        return datasets_collection.find_one({'root_path': root_path.rstrip('/')})
    except Exception:
        return None


def _sync_metadata_to_mongodb(root_path, updates):
    """
    Sync metadata/config changes to MongoDB for a registered dataset.
    Returns True if sync succeeded, False if failed or not registered.
    """
    doc = _find_registered_dataset(root_path)
    if not doc:
        return False

    mongo_updates = {'updated_at': datetime.utcnow()}

    METADATA_FIELDS = [
        'description', 'camera_view', 'quality',
        'cycle', 'notes', 'trainable_models', 'attributes'
    ]

    if 'name' in updates:
        mongo_updates['name'] = updates['name']

    for field in METADATA_FIELDS:
        if field in updates:
            mongo_updates[f'metadata.{field}'] = updates[field]

    try:
        datasets_collection.update_one(
            {'_id': doc['_id']},
            {'$set': mongo_updates}
        )
        return True
    except Exception as e:
        print(f"[MongoDB Sync] Failed to sync {root_path}: {e}")
        return False


def _sync_config_to_mongodb(root_path, config_updates):
    """
    Sync config fields to MongoDB for a registered dataset.
    Returns True if sync succeeded, False if failed or not registered.
    """
    doc = _find_registered_dataset(root_path)
    if not doc:
        return False

    mongo_updates = {'updated_at': datetime.utcnow()}
    for key in ['stats_fields', 'visible_labels', 'quality_flags', 'skip_delete_confirmation']:
        if key in config_updates:
            mongo_updates[f'config.{key}'] = config_updates[key]

    try:
        datasets_collection.update_one(
            {'_id': doc['_id']},
            {'$set': mongo_updates}
        )
        return True
    except Exception as e:
        print(f"[MongoDB Sync] Config sync failed for {root_path}: {e}")
        return False


def _sync_to_dataset_json(root_path, mongo_doc):
    """
    Sync MongoDB metadata/config back to .dataset.json.
    Preserves image_flags and created_at.
    """
    dataset_file = Path(root_path) / '.dataset.json'
    try:
        existing = {}
        if dataset_file.exists():
            with open(dataset_file) as f:
                existing = json.load(f)

        meta = mongo_doc.get('metadata', {})
        config = mongo_doc.get('config', {})

        # Sync metadata fields
        existing['name'] = mongo_doc.get('name', existing.get('name', ''))
        for field in ['description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes']:
            if field in meta:
                existing[field] = meta[field]
        if 'trainable_models' in meta:
            existing['trainable_models'] = meta['trainable_models']
        if 'attributes' in meta:
            existing['attributes'] = meta['attributes']

        # Sync config fields
        if 'stats_fields' in config:
            existing['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            existing['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            existing['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            existing['skip_delete_confirmation'] = config['skip_delete_confirmation']

        existing['updated_at'] = datetime.now().isoformat()

        with open(dataset_file, 'w') as f:
            json.dump(existing, f, indent=2)
        return True
    except Exception as e:
        print(f"[Sync] Failed to write .dataset.json for {root_path}: {e}")
        return False


def serialize_dataset(doc):
    """Convert MongoDB document to JSON-safe dict."""
    if doc is None:
        return None
    doc = dict(doc)  # Don't mutate the original
    doc['id'] = str(doc.pop('_id'))
    for field in ('registered_at', 'updated_at'):
        if field in doc and doc[field] and hasattr(doc[field], 'isoformat'):
            doc[field] = doc[field].isoformat()
    # Handle nested datetime in statistics
    stats = doc.get('statistics', {})
    if stats.get('computed_at') and hasattr(stats['computed_at'], 'isoformat'):
        stats['computed_at'] = stats['computed_at'].isoformat()
    thumbs = doc.get('thumbnails', {})
    if thumbs.get('generated_at') and hasattr(thumbs['generated_at'], 'isoformat'):
        thumbs['generated_at'] = thumbs['generated_at'].isoformat()
    doc['path_exists'] = os.path.isdir(doc.get('root_path', ''))
    return doc


def serialize_dataset_summary(doc):
    """Lightweight serialization for list view — includes full statistics."""
    stats = doc.get('statistics', {})
    # Serialize computed_at datetime if present
    computed_at = stats.get('computed_at')
    if computed_at and hasattr(computed_at, 'isoformat'):
        computed_at = computed_at.isoformat()
    return {
        'id': str(doc['_id']),
        'name': doc.get('name', ''),
        'root_path': doc.get('root_path', ''),
        'metadata': {
            'description': doc.get('metadata', {}).get('description', ''),
            'quality': doc.get('metadata', {}).get('quality', ''),
            'cycle': doc.get('metadata', {}).get('cycle', ''),
            'trainable_models': doc.get('metadata', {}).get('trainable_models', []),
        },
        'statistics': {
            'total_images': stats.get('total_images', 0),
            'total_vehicles': stats.get('total_vehicles', 0),
            'class_counts': stats.get('class_counts', {}),
            'class_area_stats': stats.get('class_area_stats', {}),
            'vehicles_per_image': stats.get('vehicles_per_image', {}),
            'spatial': stats.get('spatial', {}),
            'computed_at': computed_at,
        },
        'registered_at': doc.get('registered_at').isoformat() if doc.get('registered_at') and hasattr(doc.get('registered_at'), 'isoformat') else str(doc.get('registered_at', '')),
        'path_exists': os.path.isdir(doc.get('root_path', ''))
    }


# ============== Phase 12: Dataset Registry (file-based, legacy) ==============
REGISTRY_FILE = Path(__file__).parent / 'datasets_registry.json'

def load_registry() -> dict:
    """Load the datasets registry from JSON file."""
    if REGISTRY_FILE.exists():
        try:
            with open(REGISTRY_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'version': '1.0', 'datasets': []}

def save_registry(registry: dict):
    """Save the datasets registry atomically."""
    tmp_file = REGISTRY_FILE.with_suffix('.tmp')
    with open(tmp_file, 'w') as f:
        json.dump(registry, f, indent=2)
    tmp_file.replace(REGISTRY_FILE)

def register_dataset(name: str, path: str, cycle: str = 'Overview', image_count: int = 0) -> dict:
    """Register a dataset in the registry. Returns error dict if name is taken."""
    registry = load_registry()
    
    # Check uniqueness
    for ds in registry['datasets']:
        if ds['name'] == name:
            if ds['path'] == path:
                # Same dataset, just update access time
                ds['last_accessed'] = datetime.now().isoformat()
                ds['cycle'] = cycle
                ds['image_count'] = image_count
                save_registry(registry)
                return {'success': True, 'data': ds}
            else:
                return {'success': False, 'error': f'Dataset name "{name}" is already taken by another directory'}
    
    # New entry
    entry = {
        'name': name,
        'path': path,
        'created_at': datetime.now().isoformat(),
        'last_accessed': datetime.now().isoformat(),
        'cycle': cycle,
        'image_count': image_count
    }
    registry['datasets'].append(entry)
    save_registry(registry)
    return {'success': True, 'data': entry}

def unregister_dataset(name: str) -> dict:
    """Remove a dataset from the registry."""
    registry = load_registry()
    original_len = len(registry['datasets'])
    registry['datasets'] = [ds for ds in registry['datasets'] if ds['name'] != name]
    if len(registry['datasets']) == original_len:
        return {'success': False, 'error': f'Dataset "{name}" not found in registry'}
    save_registry(registry)
    return {'success': True}

def update_registry_entry(old_name: str, updates: dict) -> dict:
    """Update a registry entry. Validates name uniqueness if name is changing."""
    registry = load_registry()
    target = None
    for ds in registry['datasets']:
        if ds['name'] == old_name:
            target = ds
            break
    
    if not target:
        return {'success': False, 'error': f'Dataset "{old_name}" not found in registry'}
    
    # If renaming, check uniqueness
    new_name = updates.get('name', old_name)
    if new_name != old_name:
        for ds in registry['datasets']:
            if ds['name'] == new_name:
                return {'success': False, 'error': f'Dataset name "{new_name}" is already taken'}
    
    # Apply updates
    allowed_fields = ['name', 'cycle', 'image_count', 'last_accessed']
    for field in allowed_fields:
        if field in updates:
            target[field] = updates[field]
    
    save_registry(registry)
    return {'success': True, 'data': target}


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
                "visible_labels": settings.get("visible_labels", DEFAULT_VISIBLE_LABELS.copy()),
                "default_quality_flag": settings.get("default_quality_flag", "review"),
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

        
        for seq_id, img_file in enumerate(image_files, start=1):
            json_file = img_file.with_suffix('.json')
            
            entry = {
                "seq_id": seq_id,
                "filename": img_file.name,
                "json_filename": json_file.name if json_file.exists() else None,
                "quality_flags": [default_quality] if default_quality else [],
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

# Default flags (used when no project settings exist)
DEFAULT_QUALITY_FLAGS = ['brass', 'bronze', 'silver', 'gold']
DEFAULT_PERSPECTIVE_FLAGS = [
    'close-up-day', 'close-up-night',
    'pan-day', 'pan-night',
    'super_pan_day', 'super_pan_night',
    'cropped-day', 'cropped-night'
]

@app.route('/api/filter/options', methods=['GET'])
def get_filter_options():
    """Get available filter options with counts."""
    if not project_manager.project_data:
        return jsonify({"success": False, "error": "No project loaded"})
    
    # Get non-deleted images
    images = [img for img in project_manager.project_data['images'] 
              if not img.get('deleted', False)]
    
    directory = Path(project_manager.project_data['directory'])
    settings = project_manager.project_data.get('settings', {})
    
    # Get available flags from settings (or defaults)
    available_quality = settings.get('quality_flags', DEFAULT_QUALITY_FLAGS)
    
    # Initialize counters with all available flags (count=0)
    quality_flags_count = {flag: 0 for flag in available_quality}
    color_count = {}
    brand_count = {}
    model_count = {}
    label_count = {}  # The 'label' field
    type_count = {}
    sub_type_count = {}
    direction_count = {'front': 0, 'back': 0}  # Vehicle direction
    
    for img in images:
        # Count quality flags (including any legacy flags not in settings)
        for flag in img.get('quality_flags', []):
            quality_flags_count[flag] = quality_flags_count.get(flag, 0) + 1
        

        
        # Load labels from JSON if available
        if img.get('json_filename'):
            json_path = directory / img['json_filename']
            try:
                with open(json_path, 'r') as f:
                    label_data = json.load(f)
                
                # Process each object's labels
                for obj in label_data:
                    color = obj.get('color')
                    color_key = color if color else 'NULL'
                    color_count[color_key] = color_count.get(color_key, 0) + 1
                    
                    brand = obj.get('brand')
                    brand_key = brand if brand else 'NULL'
                    brand_count[brand_key] = brand_count.get(brand_key, 0) + 1
                    
                    model = obj.get('model')
                    model_key = model if model else 'NULL'
                    model_count[model_key] = model_count.get(model_key, 0) + 1
                    
                    label = obj.get('label')
                    label_key = label if label else 'NULL'
                    label_count[label_key] = label_count.get(label_key, 0) + 1
                    
                    vtype = obj.get('type')
                    vtype_key = vtype if vtype else 'NULL'
                    type_count[vtype_key] = type_count.get(vtype_key, 0) + 1
                    
                    sub_type = obj.get('sub_type')
                    sub_type_key = sub_type if sub_type else 'NULL'
                    sub_type_count[sub_type_key] = sub_type_count.get(sub_type_key, 0) + 1
                    
                    # Count direction (default to 'front' if missing)
                    direction = obj.get('direction', 'front')
                    direction_count[direction] = direction_count.get(direction, 0) + 1
            except:
                pass  # Skip files that can't be read
    
    # Convert to sorted lists of {value, count}
    # For flags: sort by defined order first (from settings), then by count for extras
    def to_flag_option_list(count_dict, defined_order):
        result = []
        # First add flags in defined order
        for flag in defined_order:
            if flag in count_dict:
                result.append({'value': flag, 'count': count_dict[flag]})
        # Then add any extra flags (legacy) sorted by count
        extras = [(k, v) for k, v in count_dict.items() if k not in defined_order]
        extras.sort(key=lambda x: (-x[1], x[0]))
        for k, v in extras:
            result.append({'value': k, 'count': v})
        return result
    
    def to_option_list(count_dict):
        return sorted([{'value': k, 'count': v} for k, v in count_dict.items()], 
                      key=lambda x: (-x['count'], x['value']))
    
    return jsonify({
        'success': True,
        'data': {
            'quality_flags': to_flag_option_list(quality_flags_count, available_quality),

            'direction': to_option_list(direction_count),
            'color': to_option_list(color_count),
            'brand': to_option_list(brand_count),
            'model': to_option_list(model_count),
            'label': to_option_list(label_count),
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
        

        
        # Check label filters (including direction) - need to load JSON
        label_filters = {k: v for k, v in filters.items() 
                        if k in ('color', 'brand', 'model', 'label', 'type', 'sub_type', 'direction') and v}
        
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
                        if key == 'direction':
                            # Direction defaults to 'front' if missing
                            obj_value = obj.get(key, 'front')
                        else:
                            obj_value = obj.get(key)
                        # Map None/empty to 'NULL' for filter matching
                        if not obj_value:
                            obj_value = 'NULL'
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
    
    # Check for directory mode (Phase 2.0)
    directory = request.args.get('directory')
    if directory:
        return get_images_from_directory(directory, request.args)
    
    # Original project-based mode
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

        'direction': request.args.getlist('filter_direction'),
        'color': request.args.getlist('filter_color'),
        'brand': request.args.getlist('filter_brand'),
        'model': request.args.getlist('filter_model'),
        'label': request.args.getlist('filter_label'),
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
    
    # Labels to skip (non-vehicle annotations)
    SKIP_LABELS = {'char', 'plate'}

    # Process objects
    objects = []
    for idx, obj in enumerate(label_data):
        # Skip non-vehicle objects (e.g. char, plate)
        if obj.get('label', '').lower() in SKIP_LABELS:
            continue

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
            'direction': obj.get('direction', 'front'),  # Default to 'front'
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
            
            orig_width, orig_height = img.size
            width, height = orig_width, orig_height
            
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
                    'height': height,
                    'orig_width': orig_width,
                    'orig_height': orig_height
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
    

    
    project_manager.save_project()
    
    return jsonify({
        'success': True,
        'data': {
            'seq_id': seq_id,
            'quality_flags': image.get('quality_flags', []),

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
        

        
        updated_flags[seq_id] = {
            'quality_flags': image.get('quality_flags', []),

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
        'quality_flags': ['brass', 'bronze', 'silver', 'gold'],
        'visible_labels': ['color', 'brand', 'model', 'type'],
        'default_quality_flag': None,
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
    flag_type = data.get('type')  # 'quality' only
    flag_value = data.get('flag')
    
    if flag_type != 'quality':
        return jsonify({'success': False, 'error': 'Invalid flag type'}), 400
    
    if not flag_value:
        return jsonify({'success': False, 'error': 'No flag specified'}), 400
    
    flag_key = 'quality_flags'
    
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


# ============== Vehicle Direction (Phase 11) ==============

@app.route('/api/vehicle/<int:seq_id>/<int:vehicle_idx>/direction', methods=['POST'])
def toggle_vehicle_direction(seq_id: int, vehicle_idx: int):
    """Toggle direction flag for a specific vehicle in an image."""
    data = request.get_json()
    new_direction = data.get('direction')
    directory_path = data.get('directory')  # For browse mode
    
    if new_direction not in ('front', 'back'):
        return jsonify({'success': False, 'error': "Invalid direction. Must be 'front' or 'back'"}), 400
    
    # Determine which mode we're in (project vs directory browse)
    if directory_path:
        # Directory browse mode - search recursively
        directory = Path(directory_path)
        image = find_image_in_directory_by_seq(directory, seq_id)
        if image:
            # Get directory from found image path
            directory = Path(image['path']).parent
    elif project_manager.project_data:
        # Project mode
        directory = Path(project_manager.project_data['directory'])
        image = find_image_by_seq_id(seq_id)
    else:
        return jsonify({'success': False, 'error': 'No project loaded and no directory specified'}), 400
    
    if not image:
        return jsonify({'success': False, 'error': 'Image not found'}), 404
    
    if not image.get('json_filename'):
        return jsonify({'success': False, 'error': 'No label file for this image'}), 404
    
    # Load label JSON
    json_path = directory / image['json_filename']
    
    if not json_path.exists():
        return jsonify({'success': False, 'error': 'Label file not found'}), 404
    
    try:
        with open(json_path, 'r') as f:
            labels = json.load(f)
        
        if vehicle_idx < 0 or vehicle_idx >= len(labels):
            return jsonify({'success': False, 'error': 'Vehicle index out of range'}), 400
        
        old_direction = labels[vehicle_idx].get('direction', 'front')
        
        # Update direction
        labels[vehicle_idx]['direction'] = new_direction
        
        # Save back to file (atomic write)
        temp_path = json_path.with_suffix('.json.tmp')
        with open(temp_path, 'w') as f:
            json.dump(labels, f, indent=2)
        temp_path.replace(json_path)
        
        print(f"DIRECTION: {image['filename']} vehicle[{vehicle_idx}]: {old_direction} -> {new_direction}")
        
        return jsonify({
            'success': True,
            'direction': new_direction,
            'message': f'Direction set to {new_direction}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def find_image_in_directory_by_seq(directory: Path, seq_id: int) -> dict:
    """Find image in a directory by sequence ID (stable hash of path).
    Searches recursively since images may be in subdirectories.
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    # Search recursively
    for f in directory.rglob('*'):
        if f.is_file() and f.suffix.lower() in image_extensions:
            computed_hash = stable_hash(str(f))
            if computed_hash == seq_id:
                return {
                    'filename': f.name,
                    'path': str(f),
                    'json_filename': f.with_suffix('.json').name if f.with_suffix('.json').exists() else None
                }
    return None


@app.route('/api/direction/apply-to-all', methods=['POST'])
def apply_direction_to_all():
    """Apply direction to all vehicles in all images (or selected images)."""
    data = request.get_json()
    new_direction = data.get('direction')
    seq_ids = data.get('seq_ids')  # Optional: specific images to update
    browse_path = data.get('path')
    browse_mode = data.get('mode', 'direct')
    
    if new_direction not in ('front', 'back'):
        return jsonify({'success': False, 'error': "Invalid direction. Must be 'front' or 'back'"}), 400
        
    images = []
    directory = None
    
    if browse_path:
        # Browse Mode
        directory = Path(browse_path)
        if not directory.exists() or not directory.is_dir():
             return jsonify({'success': False, 'error': 'Invalid directory path'}), 400
             
        # Need to find all json files
        json_files = []
        if browse_mode == 'recursive':
            json_files = list(directory.rglob('*.json'))
        else:
            json_files = list(directory.glob('*.json'))
            
        # Ignore dataset registry and settings
        json_files = [f for f in json_files if not f.name.startswith('.dataset') and not f.name.startswith('.project')]
        
        for jf in json_files:
            try:
                # Reconstruct seq_id just like in browse mode image loading
                img_path = jf.with_suffix('.jpg')
                if not img_path.exists():
                    img_path = jf.with_suffix('.png')
                if img_path.exists():
                    this_seq_id = stable_hash(str(img_path))
                    images.append({
                        'filename': img_path.name,
                        'json_filename': str(jf.relative_to(directory)), # Relative to directory for processing
                        'seq_id': this_seq_id,
                        'deleted': False # Assuming not deleted if browsing
                    })
            except Exception as e:
                pass
    else:
        # Project Mode
        if not project_manager.project_data:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400
        directory = Path(project_manager.project_data['directory'])
        images = project_manager.project_data['images']
    
    # Get images to process
    if seq_ids:
        images_to_process = [img for img in images 
                  if img['seq_id'] in seq_ids and not img.get('deleted', False)]
    else:
        images_to_process = [img for img in images 
                  if not img.get('deleted', False)]
    
    updated_images = 0
    updated_vehicles = 0
    
    for image in images_to_process:
        if not image.get('json_filename'):
            continue
        
        json_path = directory / image['json_filename']
        if not json_path.exists():
            continue
        
        try:
            with open(json_path, 'r') as f:
                labels = json.load(f)
            
            # Update direction for all vehicles in this image
            changed = False
            for vehicle in labels:
                if vehicle.get('direction', 'front') != new_direction:
                    vehicle['direction'] = new_direction
                    changed = True
                    updated_vehicles += 1
            
            if changed:
                # Save back to file (atomic write)
                temp_path = json_path.with_suffix('.json.tmp')
                with open(temp_path, 'w') as f:
                    json.dump(labels, f, indent=2)
                temp_path.replace(json_path)
                updated_images += 1
        except Exception as e:
            print(f"Error updating {image['filename']}: {e}")
            continue
    
    print(f"BULK DIRECTION: Set {new_direction} for {updated_vehicles} vehicles in {updated_images} images")
    
    return jsonify({
        'success': True,
        'data': {
            'direction': new_direction,
            'updated_images': updated_images,
            'updated_vehicles': updated_vehicles
        },
        'message': f'Set {new_direction} for {updated_vehicles} vehicles in {updated_images} images'
    })


# ============== Directory Browsing Routes (Phase 2.0) ==============

# Base path for directory browsing - can be configured
BROWSE_BASE_PATH = Path('/home/pauli/temp/AIFX013_VCR')


def build_directory_tree(path: Path, depth: int = 2, current_depth: int = 0, expanded_paths: set = None) -> dict:
    """Build directory tree structure recursively.
    
    Args:
        path: Directory path to scan
        depth: Base depth to scan
        current_depth: Current recursion depth
        expanded_paths: Set of paths that should be expanded regardless of depth
    """
    if expanded_paths is None:
        expanded_paths = set()
        
    result = {
        'name': path.name or str(path),
        'path': str(path),
        'has_children': False,
        'children': []
    }
    
    try:
        subdirs = sorted([d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')])
        result['has_children'] = len(subdirs) > 0
        
        # Check if this path is in expanded paths OR within base depth
        path_str = str(path)
        should_expand = current_depth < depth or path_str in expanded_paths
        
        # Also expand if any child path is in expanded_paths
        if not should_expand:
            for exp_path in expanded_paths:
                if exp_path.startswith(path_str + '/'):
                    should_expand = True
                    break
        
        if should_expand and subdirs:
            result['children'] = [
                build_directory_tree(d, depth, current_depth + 1, expanded_paths) 
                for d in subdirs
            ]
    except PermissionError:
        pass
    
    return result


@app.route('/api/browse/tree')
def browse_tree():
    """Get directory tree for browsing."""
    path = request.args.get('path', str(BROWSE_BASE_PATH))
    depth = request.args.get('depth', 2, type=int)
    expanded = request.args.get('expanded', '')  # Comma-separated list of expanded paths
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    # Parse expanded paths
    expanded_paths = set(expanded.split(',')) if expanded else set()
    
    tree = build_directory_tree(target, depth, expanded_paths=expanded_paths)
    
    return jsonify({
        'success': True,
        'data': tree
    })


@app.route('/api/browse/children')
def browse_children():
    """Get immediate children of a directory."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'Path required'})
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    try:
        subdirs = sorted([
            {'name': d.name, 'path': str(d), 'has_children': any(d.iterdir())}
            for d in target.iterdir() 
            if d.is_dir() and not d.name.startswith('.')
        ], key=lambda x: x['name'])
    except PermissionError:
        subdirs = []
    
    return jsonify({
        'success': True,
        'data': {
            'path': str(target),
            'directories': subdirs
        }
    })


@app.route('/api/browse/activate', methods=['POST'])
def activate_directory():
    """Mark directory as active dataset, create .dataset.json if needed."""
    data = request.get_json()
    path = data.get('path')
    settings = data.get('settings', {})  # Optional settings to save to dataset
    
    if not path:
        return jsonify({'success': False, 'error': 'Path required'})
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    dataset_file = target / '.dataset.json'
    
    # Load existing or create new
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                dataset_data = json.load(f)
        except:
            dataset_data = {}
    else:
        dataset_data = {}
    
    # If custom_name is provided from frontend, prioritize it over target.name
    # But only if it differs from current stored name, or if we are registering newly
    custom_name = data.get('custom_name')
    if custom_name:
        dataset_data['name'] = custom_name
        
    # Set defaults if not present
    dataset_data.setdefault('name', target.name)
    dataset_data.setdefault('created_at', datetime.now().isoformat())
    dataset_data['updated_at'] = datetime.now().isoformat()
    dataset_data.setdefault('image_flags', {})
    dataset_data.setdefault('stats_config', {'fields': ['label', 'color', 'model']})
    
    # Merge in settings if provided (only for NEW datasets without existing config)
    # Phase 26: Check MongoDB for registered dataset — MongoDB is authority
    mongo_doc = _find_registered_dataset(str(target))
    is_registered = mongo_doc is not None
    
    if is_registered:
        # Override metadata from MongoDB (authority for registered datasets)
        meta = mongo_doc.get('metadata', {})
        config = mongo_doc.get('config', {})
        
        dataset_data['name'] = mongo_doc.get('name', dataset_data.get('name', target.name))
        for field in ['description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes']:
            if field in meta:
                dataset_data[field] = meta[field]
        if 'trainable_models' in meta:
            dataset_data['trainable_models'] = meta['trainable_models']
        if 'attributes' in meta:
            dataset_data['attributes'] = meta['attributes']
        
        # Override config from MongoDB
        if 'stats_fields' in config:
            dataset_data['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            dataset_data['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            dataset_data['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            dataset_data['skip_delete_confirmation'] = config['skip_delete_confirmation']
        
        # Lazy migration: if MongoDB doc has no config field, populate from .dataset.json
        if 'config' not in mongo_doc:
            initial_config = {
                'stats_fields': dataset_data.get('stats_config', {}).get('fields', ['label', 'color', 'model']),
                'visible_labels': dataset_data.get('visible_labels', ['color', 'brand', 'model', 'type']),
                'quality_flags': dataset_data.get('quality_flags', ['brass', 'bronze', 'silver', 'gold']),
                'skip_delete_confirmation': dataset_data.get('skip_delete_confirmation', False)
            }
            try:
                datasets_collection.update_one(
                    {'_id': mongo_doc['_id']},
                    {'$set': {'config': initial_config}}
                )
                print(f"[MongoDB] Lazy-migrated config for {target}")
            except Exception as e:
                print(f"[MongoDB] Lazy migration failed: {e}")
    elif settings:
        # Non-registered: merge settings from frontend (original behavior)
        allowed_settings = ['visible_labels', 'quality_flags',
                           'skip_delete_confirmation', 'default_quality_flag']
        for key in allowed_settings:
            if key in settings:
                dataset_data[key] = settings[key]
    
    # Optional backend check before writing to dataset_data
    # Phase 12: Register in datasets registry
    # We do registration BEFORE saving dataset_file, so if it fails, we don't save the customized name
    dataset_name = dataset_data.get('name', target.name)
    cycle = dataset_data.get('cycle', 'Overview')
    
    # Count images
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    image_count = sum(1 for f in target.iterdir() 
                     if f.is_file() and f.suffix.lower() in image_extensions)
                     
    reg_result = register_dataset(dataset_name, str(target), cycle, image_count)
    if not reg_result['success']:
        return jsonify(reg_result), 409
        
    # Save dataset file fully now that registration succeeded
    with open(dataset_file, 'w') as f:
        json.dump(dataset_data, f, indent=2)
    
    return jsonify({
        'success': True,
        'data': {
            'path': str(target),
            'image_count': image_count,
            'settings': dataset_data,
            'is_registered': is_registered
        }
    })


@app.route('/api/dataset/metadata', methods=['GET'])
def get_dataset_metadata():
    """Get dataset metadata."""
    path = request.args.get('path')
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        # Ensure name is set
        if 'name' not in metadata:
            metadata['name'] = target.name
        
        return jsonify({
            'success': True,
            'data': metadata
        })
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'Invalid dataset file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dataset/metadata', methods=['PUT'])
def update_dataset_metadata():
    """Update dataset metadata and optionally config in a single call."""
    data = request.get_json()
    path = data.get('path')
    updates = data.get('metadata', {})
    config = data.get('config')  # Optional: stats_fields, visible_labels, quality_flags
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            metadata = json.load(f)
        
        old_name = metadata.get('name', target.name)
        
        # Update allowed metadata fields
        allowed_fields = [
            'name', 'description', 'camera_view', 'quality',
            'cycle', 'notes', 'trainable_models', 'available_preprocessing',
            'attributes'
        ]
        for field in allowed_fields:
            if field in updates:
                metadata[field] = updates[field]

        # Update config fields (stored at top-level in .dataset.json)
        config_synced = False
        if config:
            if 'stats_fields' in config:
                metadata['stats_config'] = {'fields': config['stats_fields']}
            if 'visible_labels' in config:
                metadata['visible_labels'] = config['visible_labels']
            if 'quality_flags' in config:
                metadata['quality_flags'] = config['quality_flags']
            if 'skip_delete_confirmation' in config:
                metadata['skip_delete_confirmation'] = config['skip_delete_confirmation']
        
        metadata['updated_at'] = datetime.now().isoformat()
        
        # Phase 12: Sync name/cycle changes to registry
        new_name = metadata.get('name', old_name)
        registry_updates = {'last_accessed': metadata['updated_at']}
        if 'name' in updates:
            registry_updates['name'] = updates['name']
        if 'cycle' in updates:
            registry_updates['cycle'] = updates['cycle']
        
        reg_result = update_registry_entry(old_name, registry_updates)
        if not reg_result['success']:
            return jsonify(reg_result), 409
        
        with open(dataset_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Phase 26: Sync metadata + config to MongoDB if registered
        synced = _sync_metadata_to_mongodb(path, updates)
        if config:
            config_synced = _sync_config_to_mongodb(path, config)
        
        return jsonify({
            'success': True,
            'data': {
                'updated_at': metadata['updated_at'],
                'synced_to_mongodb': synced or config_synced
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dataset/stats-config', methods=['PUT'])
def update_stats_config():
    """DEPRECATED: Use PUT /api/dataset/config instead. Kept for backwards compat."""
    data = request.get_json()
    # Convert old format to new config format
    new_data = {
        'path': data.get('path'),
        'config': {'stats_fields': data.get('fields', [])}
    }
    # Forward to new config handler
    with app.test_request_context(
        '/api/dataset/config', method='PUT',
        json=new_data, content_type='application/json'
    ):
        return update_dataset_config()


@app.route('/api/dataset/config', methods=['PUT'])
def update_dataset_config():
    """Update dataset configuration (stats fields, visible labels, quality flags)."""
    data = request.get_json()
    path = data.get('path')
    config = data.get('config', {})
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    dataset_file = target / '.dataset.json'
    
    if not dataset_file.exists():
        return jsonify({'success': False, 'error': 'Dataset not found'}), 404
    
    try:
        with open(dataset_file) as f:
            dataset_data = json.load(f)
        
        # Apply config fields to .dataset.json
        if 'stats_fields' in config:
            dataset_data['stats_config'] = {'fields': config['stats_fields']}
        if 'visible_labels' in config:
            dataset_data['visible_labels'] = config['visible_labels']
        if 'quality_flags' in config:
            dataset_data['quality_flags'] = config['quality_flags']
        if 'skip_delete_confirmation' in config:
            dataset_data['skip_delete_confirmation'] = config['skip_delete_confirmation']
        
        dataset_data['updated_at'] = datetime.now().isoformat()
        
        with open(dataset_file, 'w') as f:
            json.dump(dataset_data, f, indent=2)
        
        # Phase 26: Sync to MongoDB if registered
        synced = _sync_config_to_mongodb(path, config)
        
        return jsonify({
            'success': True,
            'data': {
                'config': config,
                'updated_at': dataset_data['updated_at'],
                'synced_to_mongodb': synced
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/dataset/stats', methods=['GET'])
def get_dataset_stats():
    """Get statistics for a dataset based on configured fields.
    
    Returns total_images count and per-field value distributions.
    Handles both bare JSON arrays and {objects: [...]} formats.
    """
    path = request.args.get('path')
    fields_param = request.args.get('fields', 'label,color,model')
    
    if not path:
        return jsonify({'success': False, 'error': 'No path provided'}), 400
    
    target = Path(path)
    if not target.exists() or not target.is_dir():
        return jsonify({'success': False, 'error': 'Invalid directory'}), 404
    
    fields = [f.strip() for f in fields_param.split(',') if f.strip()]
    
    # Find all images and their labels
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    stats = {field: {} for field in fields}
    total_images = 0
    
    try:
        for img_file in target.rglob('*'):
            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                total_images += 1
                # Look for associated JSON label file
                label_file = img_file.with_suffix('.json')
                if label_file.exists():
                    try:
                        with open(label_file) as f:
                            label_data = json.load(f)
                        
                        # Handle bare arrays (common format) and dict formats
                        if isinstance(label_data, list):
                            objects = label_data
                        else:
                            objects = label_data.get('objects', label_data.get('annotations', []))
                        
                        for obj in objects:
                            if not isinstance(obj, dict):
                                continue
                            for field in fields:
                                value = obj.get(field)
                                if value is not None:
                                    value_str = str(value)
                                    stats[field][value_str] = stats[field].get(value_str, 0) + 1
                        
                        # Also check top-level fields (only if dict)
                        if isinstance(label_data, dict):
                            for field in fields:
                                if field in label_data and field not in ['objects', 'annotations']:
                                    value = label_data[field]
                                    if value is not None:
                                        value_str = str(value)
                                        stats[field][value_str] = stats[field].get(value_str, 0) + 1
                    except:
                        pass
        
        # Also include image flags in stats
        dataset_file = target / '.dataset.json'
        if dataset_file.exists():
            try:
                with open(dataset_file) as f:
                    dataset_data = json.load(f)
                image_flags = dataset_data.get('image_flags', {})
                
                for img_name, flags in image_flags.items():
                    for field in fields:
                        if field in flags:
                            value = flags[field]
                            if value is not None:
                                value_str = str(value)
                                stats[field][value_str] = stats[field].get(value_str, 0) + 1
            except:
                pass
        
        # Remove empty fields
        stats = {k: v for k, v in stats.items() if v}
        
        return jsonify({
            'success': True,
            'data': stats,
            'total_images': total_images
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def get_images_from_directory(directory_path: str, args) -> dict:
    """Load images from directory (directory browsing mode)."""
    path = Path(directory_path)
    mode = args.get('mode', 'direct')
    page = args.get('page', 1, type=int)
    size = args.get('size', 9, type=int)
    
    # Validate size
    size = max(1, min(100, size))
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    # Find images based on mode
    if mode == 'recursive':
        image_files = []
        for ext in image_extensions:
            image_files.extend(path.rglob(f'*{ext}'))
            image_files.extend(path.rglob(f'*{ext.upper()}'))
    else:
        image_files = [f for f in path.iterdir() 
                      if f.is_file() and f.suffix.lower() in image_extensions]
    
    # Sort by filename
    image_files = sorted(set(image_files), key=lambda x: x.name)
    
    # Load dataset flags
    dataset_file = path / '.dataset.json'
    image_flags = {}
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                dataset_data = json.load(f)
                image_flags = dataset_data.get('image_flags', {})
        except:
            pass
    
    # Apply filters if provided
    filters = {
        'quality_flags': args.getlist('filter_quality_flags'),

        'direction': args.getlist('filter_direction'),
        'color': args.getlist('filter_color'),
        'brand': args.getlist('filter_brand'),
        'model': args.getlist('filter_model'),
        'label': args.getlist('filter_label'),
        'type': args.getlist('filter_type'),
        'sub_type': args.getlist('filter_sub_type')
    }
    
    # Build image list with filtering
    filtered_images = []
    for img_path in image_files:
        img_id = img_path.stem
        flags = image_flags.get(img_id, {})
        
        # Build image dict for filtering
        img_data = {
            'filename': img_path.name,
            'path': str(img_path),
            'quality_flags': [flags.get('quality_flag')] if flags.get('quality_flag') else [],

        }
        
        # Load labels from JSON for filtering
        label_path = img_path.with_suffix('.json')
        labels = None
        if label_path.exists():
            try:
                with open(label_path) as f:
                    labels = json.load(f)
                    if isinstance(labels, list) and len(labels) > 0:
                        # Use first item for filtering
                        first = labels[0]
                        img_data['color'] = first.get('color') or 'NULL'
                        img_data['brand'] = first.get('brand') or 'NULL'
                        img_data['model'] = first.get('model') or 'NULL'
                        img_data['type'] = first.get('type') or 'NULL'
                        img_data['sub_type'] = first.get('sub_type') or 'NULL'
                        img_data['label'] = first.get('label') or 'NULL'
                        img_data['direction'] = first.get('direction') or 'front'
            except:
                pass
        
        # Apply filters
        if should_include_image(img_data, filters):
            filtered_images.append((img_path, img_data, flags))
    
    total_images = len(filtered_images)
    total_pages = max(1, (total_images + size - 1) // size)
    
    # Clamp page to valid range
    page = max(1, min(page, total_pages))
    
    # Get slice for current page
    start_idx = (page - 1) * size
    end_idx = start_idx + size
    page_images = filtered_images[start_idx:end_idx]
    
    # Build response (same format as project mode)
    result = []
    for img_path, img_data, flags in page_images:
        thumbnail = None
        img_width, img_height = 0, 0
        
        if img_path.exists():
            thumbnail = get_cached_thumbnail(str(img_path), size)
            try:
                with Image.open(img_path) as pil_img:
                    img_width, img_height = pil_img.size
            except:
                pass
        
        # Check for label file
        label_path = img_path.with_suffix('.json')
        
        result.append({
            'seq_id': stable_hash(str(img_path)),  # Generate stable ID from path
            'filename': img_path.name,
            'full_path': str(img_path),
            'thumbnail': thumbnail,
            'img_width': img_width,
            'img_height': img_height,
            'quality_flags': [flags.get('quality_flag')] if flags.get('quality_flag') else [],

            'has_labels': label_path.exists()
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


def should_include_image(img_data: dict, filters: dict) -> bool:
    """Check if image should be included based on filters."""
    # Check quality flags filter
    if filters['quality_flags']:
        img_flags = img_data.get('quality_flags', [])
        if not any(f in img_flags for f in filters['quality_flags']):
            return False
    

    
    # Check label-based filters
    for field in ['direction', 'color', 'brand', 'model', 'label', 'type', 'sub_type']:
        if filters.get(field):
            value = img_data.get(field, 'NULL')
            # Map empty values to 'NULL' for filter matching
            if not value:
                value = 'NULL'
            if value not in filters[field]:
                return False
    
    return True


@app.route('/api/browse/flag', methods=['POST'])
def update_browse_flag():
    """Update flag for an image in browse mode."""
    data = request.get_json()
    
    directory = data.get('directory')
    image_id = data.get('image_id')  # filename stem
    flag_name = data.get('flag_name')
    flag_value = data.get('flag_value')
    
    if not all([directory, image_id, flag_name]):
        return jsonify({'success': False, 'error': 'Missing parameters'})
    
    path = Path(directory)
    dataset_file = path / '.dataset.json'
    
    # Load or create dataset file
    if dataset_file.exists():
        with open(dataset_file) as f:
            dataset_data = json.load(f)
    else:
        dataset_data = {
            'created_at': datetime.now().isoformat(),
            'image_flags': {}
        }
    
    # Update flag
    if image_id not in dataset_data['image_flags']:
        dataset_data['image_flags'][image_id] = {}
    
    if flag_value:
        dataset_data['image_flags'][image_id][flag_name] = flag_value
    else:
        # Remove flag if value is empty
        dataset_data['image_flags'][image_id].pop(flag_name, None)
    
    dataset_data['updated_at'] = datetime.now().isoformat()
    
    # Save atomically
    temp_file = dataset_file.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(dataset_data, f, indent=2)
    temp_file.rename(dataset_file)
    
    return jsonify({'success': True})


@app.route('/api/browse/delete', methods=['POST'])
def browse_delete():
    """Delete images in browse mode (directory browsing)."""
    data = request.get_json()
    
    directory = data.get('directory')
    filenames = data.get('filenames', [])  # list of image filenames
    
    if not directory or not filenames:
        return jsonify({'success': False, 'error': 'Missing directory or filenames'}), 400
    
    path = Path(directory)
    if not path.is_dir():
        return jsonify({'success': False, 'error': 'Directory not found'}), 404
    
    deleted_filenames = []
    failed = []
    
    for filename in filenames:
        try:
            # Find the image file (may be in subdirectory for recursive mode)
            img_path = path / filename
            if not img_path.exists():
                # Try searching recursively
                matches = list(path.rglob(filename))
                img_path = matches[0] if matches else None
            
            if not img_path or not img_path.exists():
                failed.append({'filename': filename, 'error': 'File not found'})
                continue
            
            # Delete image file
            img_path.unlink()
            print(f"BROWSE DELETE: {img_path}")
            
            # Delete associated JSON file if it exists
            json_path = img_path.with_suffix('.json')
            if json_path.exists():
                json_path.unlink()
                print(f"BROWSE DELETE: {json_path}")
            
            deleted_filenames.append(filename)
            
        except PermissionError as e:
            failed.append({'filename': filename, 'error': f'Permission denied: {e}'})
        except Exception as e:
            failed.append({'filename': filename, 'error': str(e)})
    
    # Update .dataset.json to mark deleted images
    dataset_file = path / '.dataset.json'
    if dataset_file.exists() and deleted_filenames:
        try:
            with open(dataset_file) as f:
                dataset_data = json.load(f)
            
            # Remove flags for deleted images
            image_flags = dataset_data.get('image_flags', {})
            for filename in deleted_filenames:
                stem = Path(filename).stem
                image_flags.pop(stem, None)
            
            dataset_data['image_flags'] = image_flags
            dataset_data['updated_at'] = datetime.now().isoformat()
            
            temp_file = dataset_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(dataset_data, f, indent=2)
            temp_file.rename(dataset_file)
        except Exception as e:
            print(f"Warning: Could not update .dataset.json: {e}")
    
    # Count remaining images in directory
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    remaining = len([f for f in path.iterdir() 
                     if f.is_file() and f.suffix.lower() in image_extensions])
    
    return jsonify({
        'success': True,
        'data': {
            'deleted_count': len(deleted_filenames),
            'deleted_filenames': deleted_filenames,
            'failed_count': len(failed),
            'failed': failed,
            'remaining_count': remaining
        },
        'message': f'{len(deleted_filenames)} image(s) deleted successfully'
    })


@app.route('/api/browse/filter-options')
def get_browse_filter_options():
    """Get filter options for current directory with counts (same format as project mode)."""
    directory = request.args.get('directory')
    mode = request.args.get('mode', 'direct')
    
    if not directory:
        return jsonify({'success': False, 'error': 'Directory required'})
    
    path = Path(directory)
    if not path.exists():
        return jsonify({'success': False, 'error': 'Invalid directory'})
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    # Find images
    if mode == 'recursive':
        image_files = []
        for ext in image_extensions:
            image_files.extend(path.rglob(f'*{ext}'))
    else:
        image_files = [f for f in path.iterdir() 
                      if f.is_file() and f.suffix.lower() in image_extensions]
    
    # Load dataset flags
    dataset_file = path / '.dataset.json'
    image_flags = {}
    if dataset_file.exists():
        try:
            with open(dataset_file) as f:
                image_flags = json.load(f).get('image_flags', {})
        except:
            pass
    
    # Initialize counters
    quality_flags_count = {}

    direction_count = {'front': 0, 'back': 0}
    color_count = {}
    brand_count = {}
    model_count = {}
    label_count = {}
    type_count = {}
    sub_type_count = {}
    
    for img_path in image_files:
        img_id = img_path.stem
        
        # Get flags from dataset.json
        flags = image_flags.get(img_id, {})
        if flags.get('quality_flag'):
            qf = flags['quality_flag']
            quality_flags_count[qf] = quality_flags_count.get(qf, 0) + 1

        
        # Get labels from JSON
        label_path = img_path.with_suffix('.json')
        if label_path.exists():
            try:
                with open(label_path) as f:
                    labels = json.load(f)
                    if isinstance(labels, list):
                        for item in labels:
                            # Direction
                            direction = str(item.get('direction', 'front'))
                            direction_count[direction] = direction_count.get(direction, 0) + 1
                            
                            # Color
                            color = item.get('color')
                            color_key = str(color) if color else 'NULL'
                            color_count[color_key] = color_count.get(color_key, 0) + 1
                            
                            # Brand
                            brand = item.get('brand')
                            brand_key = str(brand) if brand else 'NULL'
                            brand_count[brand_key] = brand_count.get(brand_key, 0) + 1
                            
                            # Model
                            model = item.get('model')
                            model_key = str(model) if model else 'NULL'
                            model_count[model_key] = model_count.get(model_key, 0) + 1
                            
                            # Label
                            label = item.get('label')
                            label_key = str(label) if label else 'NULL'
                            label_count[label_key] = label_count.get(label_key, 0) + 1
                            
                            # Type
                            vtype = item.get('type')
                            vtype_key = str(vtype) if vtype else 'NULL'
                            type_count[vtype_key] = type_count.get(vtype_key, 0) + 1
                            
                            # Sub-type
                            sub_type = item.get('sub_type')
                            sub_type_key = str(sub_type) if sub_type else 'NULL'
                            sub_type_count[sub_type_key] = sub_type_count.get(sub_type_key, 0) + 1
            except:
                pass
    
    # Convert to sorted lists of {value, count} - same format as project mode
    def to_option_list(count_dict):
        return sorted([{'value': k, 'count': v} for k, v in count_dict.items()], 
                      key=lambda x: (-x['count'], str(x['value'])))
    
    return jsonify({
        'success': True,
        'data': {
            'quality_flags': to_option_list(quality_flags_count),

            'direction': to_option_list(direction_count),
            'color': to_option_list(color_count),
            'brand': to_option_list(brand_count),
            'model': to_option_list(model_count),
            'label': to_option_list(label_count),
            'type': to_option_list(type_count),
            'sub_type': to_option_list(sub_type_count),
            'total_images': len(image_files)
        }
    })


@app.route('/api/browse/labels/<path:image_path>')
def get_browse_labels(image_path):
    """Get labels for an image in browse mode."""
    img_path = Path('/' + image_path)  # Restore absolute path
    label_path = img_path.with_suffix('.json')
    
    if not label_path.exists():
        return jsonify({
            'success': True,
            'data': {
                'filename': img_path.name,
                'has_labels': False,
                'objects': []
            }
        })
    
    try:
        with open(label_path) as f:
            label_data = json.load(f)
        
        if not isinstance(label_data, list):
            label_data = [label_data]
        
        # Get image dimensions for percentage calculation
        try:
            with Image.open(img_path) as img:
                img_width, img_height = img.size
        except:
            img_width, img_height = 1000, 1000  # Default fallback
        
        # Labels to skip (non-vehicle annotations)
        SKIP_LABELS = {'char', 'plate'}

        # Process objects (same format as get_label_data_for_image)
        objects = []
        for idx, obj in enumerate(label_data):
            # Skip non-vehicle objects (e.g. char, plate)
            if obj.get('label', '').lower() in SKIP_LABELS:
                continue

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
                'direction': obj.get('direction', 'front'),
                'labels': {
                    'color': obj.get('color'),
                    'brand': obj.get('brand'),
                    'model': obj.get('model'),
                    'label': obj.get('label'),
                    'type': obj.get('type'),
                    'sub_type': obj.get('sub_type'),
                    'lp_coords': obj.get('lp_coords')
                }
            })
        
        return jsonify({
            'success': True,
            'data': {
                'filename': img_path.name,
                'has_labels': True,
                'objects': objects
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/browse/labels/save', methods=['PUT'])
def save_browse_labels():
    """Save all objects/bboxes for an image in browse mode."""
    data = request.get_json()
    image_path = data.get('image_path')
    objects = data.get('objects', [])
    
    if not image_path:
        return jsonify({'success': False, 'error': 'Missing image_path'}), 400
    
    img_path = Path(image_path)
    label_path = img_path.with_suffix('.json')
    
    # Validate image exists
    if not img_path.exists():
        return jsonify({'success': False, 'error': f'Image not found: {image_path}'}), 404
    
    # Convert objects to storage format
    label_data = []
    for obj in objects:
        # Handle both nested labels format (from frontend editPanelState)
        # and flat format (from bbox editor saveBboxChanges)
        labels = obj.get('labels', {})
        if labels:
            # Nested format: { rect, labels: { color, brand, ... }, direction }
            label_obj = {
                'rect': obj.get('rect', [0, 0, 0, 0]),
                'color': labels.get('color', ''),
                'brand': labels.get('brand', ''),
                'model': labels.get('model', ''),
                'type': labels.get('type', ''),
                'sub_type': labels.get('sub_type', ''),
                'label': labels.get('label', ''),
                'lp_coords': labels.get('lp_coords'),
                'direction': obj.get('direction', 'front')
            }
        else:
            # Flat format: { rect, color, brand, ..., direction }
            label_obj = {
                'rect': obj.get('rect', [0, 0, 0, 0]),
                'color': obj.get('color', ''),
                'brand': obj.get('brand', ''),
                'model': obj.get('model', ''),
                'type': obj.get('type', ''),
                'sub_type': obj.get('sub_type', ''),
                'label': obj.get('label', ''),
                'lp_coords': obj.get('lp_coords'),
                'direction': obj.get('direction', 'front')
            }
        label_data.append(label_obj)
    
    # Write atomically
    try:
        temp_path = label_path.with_suffix('.json.tmp')
        with open(temp_path, 'w') as f:
            json.dump(label_data, f, indent=2)
        temp_path.rename(label_path)
        
        print(f"LABELS SAVED: {label_path} ({len(label_data)} objects)")
        
        return jsonify({
            'success': True,
            'data': {
                'objects_count': len(label_data),
                'path': str(label_path)
            }
        })
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Main ==============

@app.route('/api/browse/image/full/<path:image_path>')
def get_browse_full_image(image_path):
    """Get full-resolution image for browse mode."""
    img_path = Path('/' + image_path)  # Restore absolute path
    
    if not img_path.exists():
        return jsonify({'success': False, 'error': 'Image file not found'}), 404
    
    try:
        with Image.open(img_path) as img:
            # Convert to RGB
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            orig_width, orig_height = img.size
            width, height = orig_width, orig_height
            
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
                    'seq_id': stable_hash(str(img_path)),
                    'filename': img_path.name,
                    'image': f"data:image/jpeg;base64,{base64_str}",
                    'width': width,
                    'height': height,
                    'orig_width': orig_width,
                    'orig_height': orig_height,
                    'full_path': str(img_path)
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Phase 12: Registry API Endpoints ==============

@app.route('/api/registry/datasets', methods=['GET'])
def get_registry_datasets():
    """List all registered datasets, sorted by last_accessed descending."""
    registry = load_registry()
    datasets = sorted(registry['datasets'], 
                     key=lambda d: d.get('last_accessed', ''), reverse=True)
    return jsonify({'success': True, 'data': datasets})


@app.route('/api/registry/datasets/<name>', methods=['PUT'])
def update_registry_dataset(name):
    """Update a registry entry (name, cycle, etc)."""
    data = request.get_json()
    result = update_registry_entry(name, data)
    if not result['success']:
        return jsonify(result), 409
    return jsonify(result)


@app.route('/api/registry/datasets/<name>', methods=['DELETE'])
def delete_registry_dataset(name):
    """Unregister a dataset from the registry."""
    result = unregister_dataset(name)
    if not result['success']:
        return jsonify(result), 404
    return jsonify(result)


# ============== Phase 23: MongoDB Dataset API Endpoints ==============

@app.route('/api/datasets/status', methods=['GET'])
def get_datasets_status():
    """Check MongoDB connection status."""
    result = {
        'mongodb_available': mongo_available,
        'database': DB_NAME,
        'dataset_count': 0
    }
    if mongo_available:
        try:
            result['dataset_count'] = datasets_collection.count_documents({})
        except Exception:
            pass
    return jsonify(result)


@app.route('/api/datasets', methods=['GET'])
@requires_mongodb
def list_datasets():
    """List all registered datasets (summary view)."""
    try:
        docs = datasets_collection.find().sort('registered_at', -1)
        datasets_list = [serialize_dataset_summary(doc) for doc in docs]
        return jsonify({'datasets': datasets_list, 'count': len(datasets_list)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/datasets', methods=['POST'])
@requires_mongodb
def register_dataset_mongo():
    """Register a new dataset in MongoDB."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    root_path = data.get('root_path', '').rstrip('/')

    if not root_path or not os.path.isdir(root_path):
        return jsonify({'error': 'Invalid path', 'message': 'Directory does not exist'}), 400

    # Check duplicate
    existing = datasets_collection.find_one({'root_path': root_path})
    if existing:
        return jsonify({
            'error': 'duplicate',
            'message': 'Dataset already registered',
            'existing_id': str(existing['_id'])
        }), 409

    # Read .dataset.json for metadata + config
    dataset_json_path = os.path.join(root_path, '.dataset.json')
    metadata = {
        'description': '',
        'camera_view': [],
        'quality': '',
        'verdict': '',
        'cycle': '',
        'notes': '',
        'model_compatibility': [],
        'trainable_models': [],
        'attributes': []
    }
    config = {
        'stats_fields': ['label', 'color', 'model'],
        'visible_labels': ['color', 'brand', 'model', 'type'],
        'quality_flags': ['brass', 'bronze', 'silver', 'gold'],
        'skip_delete_confirmation': False
    }
    name = os.path.basename(root_path)

    if os.path.exists(dataset_json_path):
        try:
            with open(dataset_json_path, 'r') as f:
                ds_data = json.load(f)
            name = ds_data.get('name', name)
            # Read metadata fields (stored at top level in .dataset.json)
            for key in ['description', 'camera_view', 'quality',
                        'cycle', 'notes', 'trainable_models', 'attributes']:
                if key in ds_data:
                    metadata[key] = ds_data[key]
            # Also check nested metadata (legacy format from older registrations)
            ds_meta = ds_data.get('metadata', {})
            for key in ['model_compatibility']:
                if key in ds_meta:
                    metadata[key] = ds_meta[key]
            # Read config fields
            if 'stats_config' in ds_data:
                config['stats_fields'] = ds_data['stats_config'].get('fields', config['stats_fields'])
            for key in ['visible_labels', 'quality_flags', 'skip_delete_confirmation']:
                if key in ds_data:
                    config[key] = ds_data[key]
        except Exception:
            pass

    # Compute statistics
    print(f"[MongoDB] Computing statistics for {root_path}...")
    statistics = _compute_dataset_statistics(root_path)
    print(f"[MongoDB] Found {statistics['total_images']} images, classes: {statistics['class_counts']}")

    # Generate unique ID first (for thumbnail naming)
    doc_id = ObjectId()

    # Generate thumbnails
    print(f"[MongoDB] Generating thumbnails...")
    thumbnail_paths = _generate_dataset_thumbnails(root_path, str(doc_id))
    print(f"[MongoDB] Generated {len(thumbnail_paths)} thumbnails")

    # Insert
    now = datetime.utcnow()
    document = {
        '_id': doc_id,
        'name': name,
        'root_path': root_path,
        'registered_at': now,
        'updated_at': now,
        'metadata': metadata,
        'config': config,
        'statistics': statistics,
        'thumbnails': {
            'paths': thumbnail_paths,
            'generated_at': now
        }
    }

    try:
        datasets_collection.insert_one(document)
    except DuplicateKeyError:
        _cleanup_dataset_thumbnails(str(doc_id))
        existing = datasets_collection.find_one({'root_path': root_path})
        return jsonify({
            'error': 'duplicate',
            'message': 'Dataset already registered (race condition)',
            'existing_id': str(existing['_id']) if existing else ''
        }), 409

    return jsonify({
        'id': str(doc_id),
        'name': name,
        'root_path': root_path,
        'message': 'Dataset registered successfully'
    }), 201


@app.route('/api/datasets/<dataset_id>', methods=['GET'])
@requires_mongodb
def get_dataset_detail(dataset_id):
    """Get full dataset detail."""
    try:
        doc = datasets_collection.find_one({'_id': ObjectId(dataset_id)})
    except Exception:
        return jsonify({'error': 'Invalid dataset ID'}), 400

    if not doc:
        return jsonify({'error': 'Dataset not found'}), 404

    return jsonify(serialize_dataset(doc))


@app.route('/api/datasets/<dataset_id>', methods=['PUT'])
@requires_mongodb
def update_dataset_mongo(dataset_id):
    """Update dataset metadata/name."""
    try:
        oid = ObjectId(dataset_id)
    except Exception:
        return jsonify({'error': 'Invalid dataset ID'}), 400

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON body'}), 400

    # Only allow updating name and metadata
    update_fields = {'updated_at': datetime.utcnow()}
    if 'name' in data:
        new_name = data['name'].strip()
        if new_name:
            # Check name uniqueness (exclude self)
            existing = datasets_collection.find_one({'name': new_name, '_id': {'$ne': oid}})
            if existing:
                return jsonify({'error': f'Dataset name "{new_name}" is already taken'}), 409
            update_fields['name'] = new_name
    if 'metadata' in data:
        # Merge with existing metadata rather than replacing
        doc = datasets_collection.find_one({'_id': oid})
        if not doc:
            return jsonify({'error': 'Dataset not found'}), 404
        existing_meta = doc.get('metadata', {})
        existing_meta.update(data['metadata'])
        update_fields['metadata'] = existing_meta

    result = datasets_collection.update_one({'_id': oid}, {'$set': update_fields})
    if result.matched_count == 0:
        return jsonify({'error': 'Dataset not found'}), 404

    # Phase 26: Sync changes back to .dataset.json
    updated_doc = datasets_collection.find_one({'_id': oid})
    if updated_doc:
        _sync_to_dataset_json(updated_doc['root_path'], updated_doc)

    return jsonify({'message': 'Dataset updated', 'id': dataset_id})


@app.route('/api/datasets/<dataset_id>', methods=['DELETE'])
@requires_mongodb
def delete_dataset_mongo(dataset_id):
    """Unregister a dataset (files untouched)."""
    try:
        oid = ObjectId(dataset_id)
    except Exception:
        return jsonify({'error': 'Invalid dataset ID'}), 400

    doc = datasets_collection.find_one({'_id': oid})
    if not doc:
        return jsonify({'error': 'Dataset not found'}), 404

    # Clean up thumbnails
    _cleanup_dataset_thumbnails(dataset_id)

    # Remove from file-based registry (legacy)
    dataset_name = doc.get('name', '')
    if dataset_name:
        unregister_dataset(dataset_name)

    # Remove from MongoDB
    datasets_collection.delete_one({'_id': oid})

    return jsonify({'message': 'Dataset unregistered', 'id': dataset_id})


@app.route('/api/datasets/<dataset_id>/refresh', methods=['POST'])
@requires_mongodb
def refresh_dataset_stats(dataset_id):
    """Re-scan dataset and update statistics + thumbnails."""
    try:
        oid = ObjectId(dataset_id)
    except Exception:
        return jsonify({'error': 'Invalid dataset ID'}), 400

    doc = datasets_collection.find_one({'_id': oid})
    if not doc:
        return jsonify({'error': 'Dataset not found'}), 404

    root_path = doc['root_path']
    if not os.path.isdir(root_path):
        return jsonify({'error': 'Path not found', 'message': f'Directory no longer exists: {root_path}'}), 404

    # Re-compute statistics
    print(f"[MongoDB] Refreshing statistics for {root_path}...")
    statistics = _compute_dataset_statistics(root_path)

    # Re-generate thumbnails
    _cleanup_dataset_thumbnails(dataset_id)
    thumbnail_paths = _generate_dataset_thumbnails(root_path, dataset_id)

    now = datetime.utcnow()
    datasets_collection.update_one({'_id': oid}, {'$set': {
        'statistics': statistics,
        'thumbnails': {'paths': thumbnail_paths, 'generated_at': now},
        'updated_at': now
    }})

    # Also re-read .dataset.json metadata in case it changed
    dataset_json_path = os.path.join(root_path, '.dataset.json')
    if os.path.exists(dataset_json_path):
        try:
            with open(dataset_json_path, 'r') as f:
                ds_data = json.load(f)
            ds_meta = ds_data.get('metadata', {})
            existing_meta = doc.get('metadata', {})
            for key in ('description', 'camera_view', 'quality', 'verdict', 'cycle', 'notes'):
                if key in ds_meta:
                    existing_meta[key] = ds_meta[key]
            datasets_collection.update_one({'_id': oid}, {'$set': {
                'name': ds_data.get('name', doc.get('name', '')),
                'metadata': existing_meta
            }})
        except Exception:
            pass

    # Return updated document
    updated_doc = datasets_collection.find_one({'_id': oid})
    return jsonify(serialize_dataset(updated_doc))


@app.route('/api/datasets/<dataset_id>/thumbnails/<int:index>')
def serve_dataset_thumbnail(dataset_id, index):
    """Serve a cached dataset thumbnail."""
    if index < 0 or index > 3:
        return jsonify({'error': 'Invalid thumbnail index (0-3)'}), 404

    thumb_path = os.path.join(DATASET_THUMBNAIL_CACHE_DIR, f"{dataset_id}_{index}.jpg")
    if not os.path.exists(thumb_path):
        return jsonify({'error': 'Thumbnail not found'}), 404

    return send_file(thumb_path, mimetype='image/jpeg')


if __name__ == '__main__':
    # Initialize MongoDB connection
    init_mongodb()

    print("=" * 50)
    print("🖼️  Image Review Tool")
    print("=" * 50)
    print(f"Projects directory: {PROJECTS_DIR.absolute()}")
    print(f"Registry file: {REGISTRY_FILE.absolute()}")
    print(f"MongoDB: {'✅ Connected' if mongo_available else '❌ Not available'}")
    print("Starting server at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
