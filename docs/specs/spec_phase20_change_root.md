# Phase 20: Change Root Directory

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `templates/index.html`, `static/js/app.js`

---

## Objective
Allow the user to change the root directory of the "Browse" tab dynamically. Currently, it defaults to a fixed path. The user should be able to enter any absolute path and navigate from there.

---

## 2. UI Changes

### 2.1 Browse Tab (`templates/index.html`)

Add a "Root Path" input section at the top of the "Browse" sidebar tab.

```html
<div class="directory-root-config">
    <input type="text" id="root-path-input" placeholder="Root path..." class="root-input">
    <button class="btn-icon" onclick="changeRootDirectory()" title="Set Root">
        ➡️
    </button>
</div>
```

This should be placed inside `.directory-header` or just below it.

---

## 3. JavaScript Logic (`static/js/app.js`)

### 3.1 `changeRootDirectory()`

1.  Read value from `#root-path-input`.
2.  Validate it's not empty.
3.  Update `browseState.basePath`.
4.  Clear `browseState.expandedNodes`.
5.  Call `loadDirectoryTree()`.

### 3.2 Initialization

- On page load, populate `#root-path-input` with `browseState.basePath`.

---

## 4. Backend (`app.py`)

No changes required. `browse_tree` endpoint already accepts `path` parameter.
