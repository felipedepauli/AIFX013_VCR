# 👁️ Dataset Visualization with FiftyOne

This guide shows how to visualize and validate your VCR dataset using FiftyOne.

## 🚀 Quick Start

### 1. Install FiftyOne

```bash
pip install fiftyone
```

### 2. Visualize Your Dataset

```bash
# View all detections
python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl

# View only red cars
python visualize_dataset.py \
    --manifest data/manifests/manifest_raw.jsonl \
    --filter-color red

# View processed/split data
python visualize_dataset.py --dataset-dir data/processed/train
```

### 3. Open in Browser

FiftyOne will launch at `http://localhost:5151`

## 🎨 Filtering by Color in FiftyOne UI

### Method 1: Sidebar Filters
1. Open the app
2. In the left sidebar, find **"color"** field
3. Click to expand and see all color values
4. Check/uncheck colors to filter (e.g., select only "red")
5. View updates in real-time

### Method 2: Search Bar
1. Click the search/filter icon (funnel)
2. Create filter: `color.label == "red"`
3. Apply filter

### Method 3: Python API (in script)
```python
# Filter after loading
view = dataset.match(F("color.label") == "red")
session = fo.launch_app(view)
```

## 🔍 Validation Workflow

### Step 1: Overview
```bash
python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl
```

Check:
- ✅ Are all images loading correctly?
- ✅ Is the color distribution balanced?
- ✅ Are there any obvious errors?

### Step 2: Color-by-Color Validation

```bash
# Validate red cars
python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl --filter-color red
```

In the UI:
1. Review each image
2. Press `d` to select/deselect samples
3. Tag incorrect labels: Click "Tags" → Add "incorrect"
4. Export tagged samples for review

### Step 3: Check Rare Colors

Look for underrepresented colors (tail classes):
- gold
- brown  
- orange
- purple

```bash
python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl --filter-color gold
```

### Step 4: Export Problem Cases

In FiftyOne UI:
1. Select problematic samples (press `d` on each)
2. Click "Actions" → "Export"
3. Choose format (e.g., "Export samples")
4. Review and fix annotations

## 📊 Useful FiftyOne Features

### Keyboard Shortcuts
- `d` - Select/deselect sample
- `Space` - Next sample
- `←` `→` - Navigate samples
- `Esc` - Clear selection
- `Ctrl+F` - Focus search bar

### Color Statistics
```python
# In Python console or notebook
import fiftyone as fo

dataset = fo.load_dataset("vcr_dataset")

# Count by color
color_counts = dataset.count_values("color.label")
print(color_counts)

# Get samples with rare colors
rare_colors = ["gold", "brown", "orange"]
rare_view = dataset.match(F("color.label").is_in(rare_colors))
print(f"Rare color samples: {len(rare_view)}")
```

### Tag and Filter
```python
# Tag samples in UI or via Python
# Then filter by tags
tagged_view = dataset.match_tags("incorrect")
fo.launch_app(tagged_view)
```

## 🛠️ Advanced Usage

### Compare Splits
```python
# View train/val/test distributions
python visualize_dataset.py --manifest data/manifests/manifest_ready.jsonl

# In UI: Filter by "split" field
```

### Multi-color Search
```python
# In FiftyOne Python console
from fiftyone import ViewField as F

# Red or blue cars only
view = dataset.match(
    (F("color.label") == "red") | (F("color.label") == "blue")
)
session = fo.launch_app(view)
```

### Export Filtered Dataset
```python
# Select samples in UI, then:
import fiftyone as fo

dataset = fo.load_dataset("vcr_dataset")
selected = dataset.select(selected_ids)  # Get from UI selection

# Export manifest
selected.export(
    export_dir="/path/to/export",
    dataset_type=fo.types.FiftyOneDataset,
)
```

## 📝 Example Validation Script

Create `validate_colors.py`:

```python
#!/usr/bin/env python3
import fiftyone as fo
from fiftyone import ViewField as F

# Load dataset
dataset = fo.load_dataset("vcr_dataset")

# Define expected colors
VALID_COLORS = [
    "black", "white", "silver", "gray", "red", "blue", 
    "green", "yellow", "brown", "gold", "orange", "purple",
    "beige", "pink", "burgundy", "turquoise"
]

# Find invalid colors
invalid = dataset.match(~F("color.label").is_in(VALID_COLORS))
print(f"Found {len(invalid)} samples with invalid colors")

if len(invalid) > 0:
    print("Invalid colors found:")
    invalid_colors = invalid.count_values("color.label")
    for color, count in invalid_colors.items():
        print(f"  {color}: {count}")
    
    # Launch app to review
    session = fo.launch_app(invalid)
    session.wait()
```

## 🐛 Troubleshooting

**Issue**: Images not loading
- Check that image paths in manifest are correct
- Ensure paths are absolute or relative to manifest location

**Issue**: No color field visible
- Verify manifest has "label" field with color values
- Check that records were loaded correctly

**Issue**: Port already in use
```bash
python visualize_dataset.py --manifest data/manifests/manifest_raw.jsonl --port 5152
```

**Issue**: Dataset already exists
```bash
# Delete old dataset
fiftyone datasets delete vcr_dataset

# Or use different name
python visualize_dataset.py --manifest data.jsonl --dataset-name vcr_v2
```

## 📚 Resources

- [FiftyOne Documentation](https://docs.voxel51.com/)
- [FiftyOne Cheat Sheet](https://docs.voxel51.com/cheat_sheets/basics_cheat_sheet.html)
- [Filtering and Querying](https://docs.voxel51.com/user_guide/using_views.html)

---

**Happy validating!** 🎯
