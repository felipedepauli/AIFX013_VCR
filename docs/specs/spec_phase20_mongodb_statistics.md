# Phase 20: Class Statistics (MongoDB Statistics)

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/js/app.js`, `templates/index.html`

---

## Objective
Display specific class statistics for **Car**, **Motorcycle**, **Truck**, and **Bus** in the Metadata Panel. This uses the same data source as the current filter system (iterating over JSON labels).
Note: While the phase is named "MongoDB Statistics", the implementation currently relies on the file-based registry which powers the filters.

---

## 1. Prerequisites
- Phase 19 (Attributes) complete.

---

## 2. Core Concepts

### 2.1 Target Classes
- **car**
- **motorcycle**
- **truck**
- **bus**

### 2.2 Data Source
- The existing `/api/dataset/stats` or a new endpoint that aggregates these specific label counts.
- Currently, `/api/dataset/stats` accepts a `fields` parameter. We can reuse this or add a dedicated section.

---

## 3. UI Components

### 3.1 Class Statistics Section

Add to `templates/index.html` inside the metadata sidebar (before or after existing sections? User said "statistics just for car...", implying a summary).
We will add a new **Class Distribution** section.

```html
<div class="panel-section class-stats-section">
    <div class="section-header" onclick="toggleMetadataSection(this)">
        <span class="section-icon">📊</span>
        <span class="section-title">Class Distribution</span>
        <span class="section-toggle">▼</span>
    </div>
    <div class="section-content" id="class-stats-content">
        <!-- Stats injected here -->
        <div class="stats-item">
            <span class="stats-label">Car</span>
            <div class="stats-bar-container">
                <div class="stats-bar" style="width: 0%"></div>
            </div>
            <span class="stats-count">0</span>
        </div>
        <!-- ... other classes ... -->
    </div>
</div>
```

---

## 4. JavaScript Implementation

Add to `static/js/app.js`:

`loadClassStatistics()`:
1. Fetch stats from `/api/dataset/stats?path=...&fields=label`.
2. Extract counts for `car`, `motorcycle`, `truck`, `bus`.
3. Render the specific UI section.

---

## 5. Backend API (`app.py`)

The existing `/api/dataset/stats` endpoint already aggregates counts for `label`.
We just need to ensure the frontend requests it and filters the display to the specific requested classes.
No backend changes might be needed if the existing stats endpoint is sufficient.
Verification: The existing endpoint iterates all images and counts labels. This is exactly what the user asked for ("same data as filters").
