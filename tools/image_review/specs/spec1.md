# Spec 1: Cycle-Based Bounding Box Coloring

## Objective
Update the image review tool so that the color of bounding boxes drawn around detected vehicles dynamically adapts based on the active dataset's `cycle` property.

## Requirements from PRD
- **Overview, Bounding Box, and Type cycles**: Use the `label` property to determine bounding box color (e.g., car, truck).
- **Color cycle**: Use the `color` property to determine bounding box color (e.g., silver, black).
- **Brand and Model cycle**: Use the `model` property to determine bounding box color (e.g., city, civic).

## Implementation Details

1. **State Management**:
   - The current cycle is available in the dataset metadata (`appState.datasetMetadata.cycle` in the frontend).
   - The frontend should have access to this `cycle` value when rendering the layout.

2. **Rendering Logic**:
   - Locate the function responsible for drawing bounding boxes (e.g., inside `static/js/app.js` or the appropriate canvas rendering module, maybe `drawLabels`).
   - Create a helper function `getBoundingBoxColorField(cycle)` that returns the name of the relevant JSON field (`'label'`, `'color'`, or `'model'`).
   - Use the value of that field for the specific vehicle object to seed the color generator.

## Verification
1. Load a dataset and set its Cycle to "Overview" in the metadata panel. Verify bounding boxes correspond to object `label`.
2. Change the dataset Cycle to "Color". Verify bounding boxes change to correspond to object `color`.
3. Change the dataset Cycle to "Brand and Model". Verify bounding boxes change to correspond to object `model`.
