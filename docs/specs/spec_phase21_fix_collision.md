# Phase 21: Fix Activation Name Collision

## Location

**Tool Directory:** `/home/pauli/temp/AIFX013_VCR/tools/image_review/`

**Files to Modify:** `app.py`, `static/js/app.js`

---

## Objective
Resolve the issue where a user cannot activate a directory if its default name (the folder name) is already registered by a different path. The system should prompt the user for a unique name.

---

## 2. Backward Compatibility
- The existing activation flow should remain unchanged for non-conflicting names.
- The `custom_name` parameter is optional.

---

## 3. Backend Changes (`app.py`)

### 3.1 `activate_directory` Endpoint

Accept `custom_name` in the JSON body.

```python
data = request.get_json()
custom_name = data.get('custom_name')

# ...

# When setting defaults:
dataset_name = custom_name if custom_name else target.name
dataset_data.setdefault('name', dataset_name)
```

And ensuring `register_dataset` uses this name.

---

## 4. Frontend Changes (`static/js/app.js`)

### 4.1 `activateDirectory`

- Catch 409 (Conflict) error response.
- Check if error message indicates name collision.
- Use `prompt("Name '...' is taken. Enter a unique name for this dataset:")`.
- If user enters a name, retry the activation request including `custom_name`.

```javascript
if (response.status === 409) {
    const newName = prompt(result.error + "\n\nPlease enter a unique name for this dataset:");
    if (newName) {
        // Retry with custom_name
        activateDirectoryWithCustomName(path, newName);
    }
    return;
}
```
