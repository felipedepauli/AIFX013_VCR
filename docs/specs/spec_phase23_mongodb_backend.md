# Phase 23: MongoDB Backend & Dataset Registry

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `requirements.txt`

**PRD Reference:** FR-18 (MongoDB Backend v2.1)

---

## Objective
Set up server-side MongoDB integration for a persistent dataset registry. The database is accessed exclusively by the Flask server — no direct client access. This phase establishes the data layer that Phases 24 and 25 build upon.

---

## 1. Prerequisites
- Phase 13 complete (Dataset Activation with `.dataset.json`)
- Phase 14 complete (Dataset Metadata Panel)
- MongoDB installed and running locally (`mongod`)
- `pymongo` package available

---

## 2. Core Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Dataset Registry** | MongoDB collection storing metadata about registered datasets |
| **Registration** | Adding a dataset's metadata to MongoDB (does NOT copy files) |
| **Unregistration** | Removing a dataset record from MongoDB (does NOT delete files) |
| **root_path** | Absolute path to the dataset directory on disk (unique key) |

### 2.2 Architecture

```
Browser ──HTTP──▶ Flask (app.py) ──pymongo──▶ MongoDB (localhost:27017)
                                                 │
                                                 └─ DB: image_review_tool
                                                      └─ Collection: datasets
```

The client never talks to MongoDB directly. All CRUD goes through Flask API endpoints.

---

## 3. MongoDB Setup

### 3.1 Connection Management

```python
# app.py — top-level initialization
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017')
DB_NAME = 'image_review_tool'
COLLECTION_NAME = 'datasets'

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
    except ConnectionFailure as e:
        mongo_available = False
        print(f"[MongoDB] Not available: {e}. Dashboard features disabled.")
```

### 3.2 Graceful Fallback

When MongoDB is unavailable:
- The app starts normally — all existing features work
- Dashboard-related API endpoints return `503 Service Unavailable` with JSON message
- The frontend shows a warning banner: "MongoDB not available — Dashboard features disabled"
- The "Add Current" and "Dashboard" buttons in the left panel are grayed out

### 3.3 Decorator for MongoDB Endpoints

```python
from functools import wraps

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
```

---

## 4. Document Schema

### 4.1 `datasets` Collection

```json
{
  "_id": "ObjectId (auto-generated)",
  "name": "string — display name",
  "root_path": "string — absolute path to dataset dir (unique index)",
  "registered_at": "datetime — when added to registry",
  "updated_at": "datetime — last metadata edit",
  "metadata": {
    "description": "string",
    "camera_view": ["string array — frontal, traseira, etc."],
    "quality": "string — poor|fair|good|excellent",
    "verdict": "string — keep|revise|remove",
    "cycle": "string — first|second|third|fourth|fifth",
    "notes": "string",
    "model_compatibility": ["string array — colornet_v1, detect_v1, etc."]
  },
  "statistics": {
    "total_images": "int",
    "class_counts": {
      "car": "int",
      "motorcycle": "int",
      "truck": "int",
      "bus": "int"
    },
    "spatial": {
      "position_mean": { "x": "float", "y": "float" },
      "position_variance": { "x": "float", "y": "float" },
      "area_mean": "float",
      "area_variance": "float"
    },
    "computed_at": "datetime"
  },
  "thumbnails": {
    "paths": ["string array — 4 relative paths to cached thumbnails"],
    "generated_at": "datetime"
  }
}
```

### 4.2 Index

```python
datasets_collection.create_index('root_path', unique=True)
```

---

## 5. API Endpoints

### 5.1 List All Datasets

```
GET /api/datasets
```

**Response 200:**
```json
{
  "datasets": [
    {
      "id": "65a1b2c3d4e5f6...",
      "name": "vehicle_colors_v4",
      "root_path": "/home/pauli/pdi_datasets/vehicle_colors_v4",
      "metadata": { "quality": "good", "cycle": "second", "verdict": "keep",
                     "model_compatibility": ["colornet_v1"] },
      "statistics": { "total_images": 1234 },
      "registered_at": "2026-02-25T10:00:00",
      "path_exists": true
    }
  ],
  "count": 1
}
```

**Notes:**
- Returns a summary (not full statistics/thumbnails) for list performance
- `path_exists` is computed on-the-fly via `os.path.isdir(root_path)`

### 5.2 Register Dataset

```
POST /api/datasets
Content-Type: application/json

{
  "root_path": "/home/pauli/pdi_datasets/vehicle_colors_v4"
}
```

**Server logic:**
1. Check `root_path` exists on disk → 400 if not
2. Check not already registered (unique index) → 409 if duplicate
3. Read `.dataset.json` from `root_path` if it exists → populate metadata
4. Compute statistics (call `_compute_dataset_statistics(root_path)`)
5. Generate 4 thumbnails (call `_generate_dataset_thumbnails(root_path)`)
6. Insert document into MongoDB
7. Return the created document

**Response 201:**
```json
{
  "id": "65a1b2c3d4e5f6...",
  "name": "vehicle_colors_v4",
  "root_path": "/home/pauli/pdi_datasets/vehicle_colors_v4",
  "message": "Dataset registered successfully"
}
```

**Response 409 (duplicate):**
```json
{
  "error": "duplicate",
  "message": "Dataset already registered",
  "existing_id": "65a1b2c3d4e5f6..."
}
```

### 5.3 Get Dataset Detail

```
GET /api/datasets/<id>
```

**Response 200:** Full document including all statistics and thumbnail paths.

### 5.4 Update Dataset

```
PUT /api/datasets/<id>
Content-Type: application/json

{
  "metadata": {
    "description": "Updated description",
    "quality": "excellent",
    "model_compatibility": ["colornet_v1", "colornet_v2"]
  }
}
```

**Notes:**
- Only `metadata.*` and `name` fields are editable via this endpoint
- `root_path`, `statistics`, `thumbnails` are NOT editable (use refresh endpoint)
- Updates `updated_at` timestamp

### 5.5 Delete (Unregister) Dataset

```
DELETE /api/datasets/<id>
```

**Server logic:**
1. Delete thumbnail files from cache
2. Remove document from MongoDB
3. Return 200

**Response 200:**
```json
{
  "message": "Dataset unregistered",
  "id": "65a1b2c3d4e5f6..."
}
```

### 5.6 Refresh Statistics

```
POST /api/datasets/<id>/refresh
```

**Server logic:**
1. Verify `root_path` still exists → 404 if gone
2. Re-compute statistics
3. Re-generate thumbnails
4. Update document in MongoDB
5. Return updated statistics

### 5.7 Serve Thumbnail

```
GET /api/datasets/<id>/thumbnails/<index>
```

- `index`: 0–3
- Returns JPEG image (Content-Type: image/jpeg)
- 404 if thumbnail not cached

### 5.8 Check MongoDB Status

```
GET /api/datasets/status
```

**Response 200:**
```json
{
  "mongodb_available": true,
  "database": "image_review_tool",
  "dataset_count": 5
}
```

---

## 6. Statistics Computation

### 6.1 `_compute_dataset_statistics(root_path)`

```python
import numpy as np
from pathlib import Path

def _compute_dataset_statistics(root_path):
    """Scan all JSON label files and compute dataset statistics."""
    root = Path(root_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    
    total_images = 0
    class_counts = {'car': 0, 'motorcycle': 0, 'truck': 0, 'bus': 0}
    positions_x = []
    positions_y = []
    areas = []
    
    # Walk recursively through all subdirectories
    for img_path in root.rglob('*'):
        if img_path.suffix.lower() not in image_extensions:
            continue
        total_images += 1
        
        # Look for corresponding JSON
        json_path = img_path.with_suffix('.json')
        if not json_path.exists():
            continue
        
        try:
            with open(json_path, 'r') as f:
                objects = json.load(f)
            if not isinstance(objects, list):
                objects = [objects]
            
            for obj in objects:
                # Class counts
                label = obj.get('label', '').lower()
                if label in class_counts:
                    class_counts[label] += 1
                
                # Spatial stats from rect [x, y, w, h]
                rect = obj.get('rect')
                if rect and len(rect) == 4:
                    x, y, w, h = rect
                    positions_x.append(x + w / 2)  # center x
                    positions_y.append(y + h / 2)  # center y
                    areas.append(w * h)
        except (json.JSONDecodeError, KeyError):
            continue
    
    # Compute spatial statistics
    spatial = {}
    if positions_x:
        spatial = {
            'position_mean': {
                'x': round(float(np.mean(positions_x)), 2),
                'y': round(float(np.mean(positions_y)), 2)
            },
            'position_variance': {
                'x': round(float(np.var(positions_x)), 2),
                'y': round(float(np.var(positions_y)), 2)
            },
            'area_mean': round(float(np.mean(areas)), 2),
            'area_variance': round(float(np.var(areas)), 2)
        }
    
    return {
        'total_images': total_images,
        'class_counts': class_counts,
        'spatial': spatial,
        'computed_at': datetime.utcnow().isoformat()
    }
```

### 6.2 Performance Considerations
- For datasets with 5,000+ images, statistics computation may take several seconds
- The endpoint returns immediately if statistics are cached; use `POST .../refresh` to re-compute
- Consider running computation in a background thread for very large datasets (future improvement)

---

## 7. Thumbnail Generation

### 7.1 `_generate_dataset_thumbnails(root_path, dataset_id)`

```python
from PIL import Image

THUMBNAIL_CACHE_DIR = os.path.join(os.path.dirname(__file__), 'static', 'cache', 'thumbnails')
THUMBNAIL_SIZE = (200, 200)

def _generate_dataset_thumbnails(root_path, dataset_id):
    """Generate 4 representative thumbnails: 1st, 25%, 75%, last."""
    root = Path(root_path)
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    
    # Collect and sort all images
    all_images = sorted([
        p for p in root.rglob('*')
        if p.suffix.lower() in image_extensions
    ])
    
    if not all_images:
        return []
    
    # Pick: 1st, 25%, 75%, last
    n = len(all_images)
    indices = [0, n // 4, (3 * n) // 4, n - 1]
    # Remove duplicates for small datasets
    indices = list(dict.fromkeys(indices))
    
    # Ensure cache directory exists
    os.makedirs(THUMBNAIL_CACHE_DIR, exist_ok=True)
    
    thumbnail_paths = []
    for i, idx in enumerate(indices):
        img_path = all_images[idx]
        thumb_filename = f"{dataset_id}_{i}.jpg"
        thumb_path = os.path.join(THUMBNAIL_CACHE_DIR, thumb_filename)
        
        try:
            with Image.open(img_path) as img:
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                img = img.convert('RGB')
                img.save(thumb_path, 'JPEG', quality=85)
            thumbnail_paths.append(thumb_filename)
        except Exception as e:
            print(f"[Thumbnails] Failed to generate {thumb_filename}: {e}")
    
    return thumbnail_paths
```

### 7.2 Thumbnail Storage
- Cached at: `tools/image_review/static/cache/thumbnails/{dataset_id}_{0-3}.jpg`
- Served via: `GET /api/datasets/<id>/thumbnails/<index>`
- Regenerated on `POST /api/datasets/<id>/refresh`
- Deleted when dataset is unregistered

---

## 8. Serialization Helpers

### 8.1 MongoDB Document → JSON

```python
from bson import ObjectId

def serialize_dataset(doc):
    """Convert MongoDB document to JSON-safe dict."""
    if doc is None:
        return None
    doc['id'] = str(doc.pop('_id'))
    # Convert datetime objects to ISO strings
    for field in ('registered_at', 'updated_at'):
        if field in doc and doc[field]:
            doc[field] = doc[field].isoformat()
    return doc

def serialize_dataset_summary(doc):
    """Lightweight serialization for list view."""
    return {
        'id': str(doc['_id']),
        'name': doc.get('name', ''),
        'root_path': doc.get('root_path', ''),
        'metadata': {
            'quality': doc.get('metadata', {}).get('quality', ''),
            'cycle': doc.get('metadata', {}).get('cycle', ''),
            'verdict': doc.get('metadata', {}).get('verdict', ''),
            'model_compatibility': doc.get('metadata', {}).get('model_compatibility', [])
        },
        'statistics': {
            'total_images': doc.get('statistics', {}).get('total_images', 0)
        },
        'registered_at': doc.get('registered_at', '').isoformat() if doc.get('registered_at') else '',
        'path_exists': os.path.isdir(doc.get('root_path', ''))
    }
```

---

## 9. Dependencies

### 9.1 requirements.txt additions

```
pymongo>=4.6.0
```

### 9.2 System requirements
- MongoDB 6.0+ running locally (or accessible via `MONGODB_URI`)
- `numpy` (already in project dependencies for statistics computation)

---

## 10. Testing Checklist

### 10.1 MongoDB Connection
- [ ] App starts with MongoDB running → connected message in console
- [ ] App starts without MongoDB → fallback message, app works normally
- [ ] `GET /api/datasets/status` returns `mongodb_available: true/false`

### 10.2 Register Dataset
- [ ] `POST /api/datasets` with valid `root_path` → 201 with document
- [ ] `POST /api/datasets` with same path again → 409 duplicate
- [ ] `POST /api/datasets` with non-existent path → 400 error
- [ ] Verify statistics computed (total_images > 0, class_counts populated)
- [ ] Verify 4 thumbnails generated in cache directory

### 10.3 List, Get, Update, Delete
- [ ] `GET /api/datasets` → returns list with summaries
- [ ] `GET /api/datasets/<id>` → returns full document
- [ ] `PUT /api/datasets/<id>` with metadata changes → updated
- [ ] `DELETE /api/datasets/<id>` → removed from DB, thumbnails cleaned

### 10.4 Refresh
- [ ] `POST /api/datasets/<id>/refresh` → statistics recomputed
- [ ] Refresh on deleted path → 404 with "path not found"

### 10.5 Thumbnails
- [ ] `GET /api/datasets/<id>/thumbnails/0` → returns JPEG image
- [ ] `GET /api/datasets/<id>/thumbnails/5` → 404
