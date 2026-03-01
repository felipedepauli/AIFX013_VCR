# Specification: Hide Non-Matching Vehicles (Phase 22)

## Overview
A new feature to help reviewers focus on specific objects when using filters. When filters are active, pressing `h` will dim (apply an 80% black overlay) to all bounding boxes representing vehicles that do NOT match the current filter criteria, leaving only the matching vehicles fully visible.

## Scope
- Applies to **Grid View** (all images on current page)
- Applies to **Preview Modal** ("Open Wider")
- Keyboard shortcut `h` to toggle the feature on/off
- Visual feedback indicating the feature is active

## Functional Requirements

### FR-22.1: Feature Toggle
- Pressing `h` toggles the "Hide Mode" state (ON/OFF).
- If no filters are currently active, pressing `h` should do nothing (or show a brief toast notification: "Activate a filter to use the hide feature").
- The feature automatically turns OFF when all filters are cleared.

### FR-22.2: Visual Overlay
- When Hide Mode is ON, any bounding box (`.bbox`) rendered on screen must be evaluated against the active filters.
- If the object **does not match** the active filters, an overlay with `background-color: rgba(0, 0, 0, 0.8)` (80% black) is applied over its bounding box area.
- If the object **matches**, it remains fully visible (no overlay).
- The overlay needs to visually obscure the vehicle but keep the bounding box border visible.

### FR-22.3: Grid View Implementation
- When rendering grid overlays (`renderLabels`), non-matching objects must be rendered with an extra CSS class (e.g., `dimmed` or `hidden-non-match`).
- This applies to all images currently visible on the grid page.

### FR-22.4: Preview Modal Implementation
- When rendering the modal overlay (`renderModalLabels`), non-matching objects must also receive the extra CSS class.

### FR-22.5: UI Indication
- A visual indicator should show when Hide Mode is active. 
- A toggle button should be added to the Filter Panel header or the main toolbar, allowing mouse users to toggle the feature.
- A keyboard shortcut hint (`[h] Hide filtered`) should be visible.

## Technical Implementation Notes

### State Management
- Add `hideNonMatching: false` to an existing global state object (e.g., `filterState`).
- The keyboard handler (`handleKeyboard`) should intercept `h` and toggle this state.

### CSS Updates
- Add a new CSS rule for the `dimmed` state:
  ```css
  .bbox.dimmed {
      background-color: rgba(0, 0, 0, 0.8) !important;
      border-color: rgba(100, 100, 100, 0.5) !important; /* Optional: dim the border too */
  }
  .bbox.dimmed .object-labels {
      opacity: 0.2; /* Dim the text labels too */
  }
  ```

### JavaScript Updates
- **Filtering Logic**: The current `apply_filters_to_images` logic determines if an *entire image* matches. We need a way to determine if a *specific object* within that image matches.
- A new helper function `doesObjectMatchFilters(obj, filters)` is needed.
- `renderLabels` and `renderModalLabels` will call this helper for each object when `filterState.hideNonMatching` is true.

## Risks & Mitigations
- **Overhead of re-evaluating filters**: Checking every object against filters on every render might be slow. *Mitigation*: The number of objects per image is small, so client-side evaluation is fast enough.
- **State desync**: Hide mode remaining active after filters are cleared. *Mitigation*: Automatically set `hideNonMatching = false` in `clearAllFilters()` or `updateFilters()`.
