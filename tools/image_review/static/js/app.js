/**
 * Image Review Tool - JavaScript
 * Phase 8: Settings Panel
 */

// ============================================
// State
// ============================================

let currentProject = null;
let projectData = null;
let browserCurrentPath = null;

// Browse state (Directory mode - Phase 2.0)
const browseState = {
    isActive: false,          // Whether we're in directory browsing mode
    activePath: null,         // Currently active (loaded) directory
    selectedPath: null,       // Currently selected in tree (not yet activated)
    displayMode: 'direct',    // 'direct' or 'recursive'
    expandedNodes: new Set(), // Expanded directory nodes
    basePath: '/home/pauli/temp/AIFX013_VCR'  // Base path for browsing
};

// Grid state
const gridState = {
    gridSize: 9,           // Current grid size (4, 9, 25, 36)
    currentPage: 1,        // Current page number
    totalPages: 1,         // Calculated from images / gridSize
    totalImages: 0,        // Total non-deleted images
    selectedImages: new Set()  // Set of selected seq_ids
};

// Label visibility state
let visibleLabels = ['color', 'brand', 'model', 'type'];  // Default
let showBoundingBoxes = true;  // Show bounding boxes by default

// Delete state (Phase 5)
const deleteState = {
    skipConfirmation: false,  // Session-level skip confirmation
    pendingDelete: [],        // seq_ids pending deletion
    isDeleting: false         // Lock to prevent concurrent deletes
};

// Flag modal state (Phase 6)
const flagModalState = {
    isOpen: false,
    isBulk: false,
    seqIds: [],
    selectedQualityFlags: new Set(),
    selectedPerspectiveFlags: new Set()
};

// Bounding Box Editor state
const bboxEditorState = {
    isActive: false,           // Edit mode on/off
    originalObjects: [],       // Backup for cancel (deep copy)
    currentObjects: [],        // Working copy (modified during edit)
    selectedIndex: null,       // Currently selected bbox index
    
    // Drag state
    isDragging: false,
    dragType: null,            // 'move' | 'resize-nw' | 'resize-ne' | etc.
    dragStartPos: { x: 0, y: 0 },
    dragStartRect: null,       // { x, y, width, height } in percent
    
    // Draw new rectangle
    isDrawingNew: false,
    drawStart: null,           // { x, y } in percent
    
    // Image dimensions (for coordinate conversion)
    imgWidth: 0,
    imgHeight: 0
};

// Flag configuration
const FLAG_CONFIG = {
    quality: {
        flags: ['bin', 'review', 'ok', 'move'],
        colors: {
            'bin': '#e74c3c',
            'review': '#f39c12',
            'ok': '#27ae60',
            'move': '#3498db'
        }
    },
    perspective: {
        flags: [
            'close-up-day', 'close-up-night',
            'pan-day', 'pan-night',
            'super_pan_day', 'super_pan_night',
            'cropped-day', 'cropped-night'
        ],
        colors: {
            'close-up-day': '#1abc9c',
            'close-up-night': '#16a085',
            'pan-day': '#9b59b6',
            'pan-night': '#8e44ad',
            'super_pan_day': '#e91e63',
            'super_pan_night': '#c2185b',
            'cropped-day': '#00bcd4',
            'cropped-night': '#0097a7'
        }
    }
};

// Cache for loaded labels
const labelCache = new Map();  // seq_id -> label data

// Filter state (Phase 10)
const filterState = {
    isOpen: false,
    options: null,  // Loaded from API
    selected: {
        quality_flags: new Set(),
        perspective_flags: new Set(),
        color: new Set(),
        brand: new Set(),
        model: new Set(),
        type: new Set(),
        sub_type: new Set()
    }
};

// ============================================
// Constants
// ============================================

const DEFAULT_QUALITY_FLAGS = ['bin', 'review', 'ok', 'move'];
const DEFAULT_PERSPECTIVE_FLAGS = [
    'close-up-day', 'close-up-night',
    'pan-day', 'pan-night',
    'super_pan_day', 'super_pan_night',
    'cropped-day', 'cropped-night'
];
const ALL_LABELS = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
const DEFAULT_VISIBLE_LABELS = ['color', 'brand', 'model', 'type'];

// ============================================
// Centralized Flag Access (Single Source of Truth)
// ============================================

// Get available quality flags from project settings or defaults
function getAvailableQualityFlags() {
    return projectData?.settings?.quality_flags || DEFAULT_QUALITY_FLAGS;
}

// Get available perspective flags from project settings or defaults
function getAvailablePerspectiveFlags() {
    return projectData?.settings?.perspective_flags || DEFAULT_PERSPECTIVE_FLAGS;
}

// Get flag color - checks predefined colors, falls back to generated color
function getFlagColor(flag, type = 'quality') {
    // Check predefined colors first
    const predefinedColor = FLAG_CONFIG[type]?.colors?.[flag];
    if (predefinedColor) return predefinedColor;
    
    // Generate consistent color from flag name hash
    return generateColorFromFlag(flag, type);
}

// Generate a consistent color from flag name
function generateColorFromFlag(flag, type) {
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < flag.length; i++) {
        hash = flag.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Base hue on type (quality = warm, perspective = cool)
    const baseHue = type === 'quality' ? 0 : 180;
    const hue = (Math.abs(hash) % 120) + baseHue;
    const saturation = 65 + (Math.abs(hash >> 8) % 20);
    const lightness = 45 + (Math.abs(hash >> 16) % 15);
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Refresh all flag-dependent UI components
function refreshFlagDependentUI() {
    // Refresh filter panel
    loadFilterOptions();
    
    // Refresh flag modal if open
    if (flagModalState.isOpen) {
        renderFlagCheckboxes();
    }
    
    // Refresh default options if startup modal is visible
    const startupModal = document.getElementById('startup');
    if (startupModal && !startupModal.classList.contains('hidden')) {
        populateDefaultOptions();
    }
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', init);

async function init() {
    console.log('🖼️ Image Review Tool - Initializing...');
    setupEventListeners();
    initFilterPanel();
    initDirectoryBrowsing();
    initMetadataPanel();
    
    // Auto-switch to Directories tab on startup
    switchSidebarTab('directories');
    
    console.log('✓ Initialization complete');
}

function setupEventListeners() {
    // Keyboard shortcuts
    document.addEventListener('keydown', handleKeyboard);
    
    // Reposition overlays on window resize
    window.addEventListener('resize', debounce(repositionAllOverlays, 100));
}

function handleKeyboard(e) {
    // Ignore when typing in text inputs (but allow shortcuts for checkboxes and buttons)
    if (e.target.tagName === 'INPUT' && e.target.type !== 'checkbox') {
        // Allow Escape, Tab, and Enter in edit mode
        if (e.key !== 'Escape' && e.key !== 'Tab' && e.key !== 'Enter') return;
    }
    if (e.target.tagName === 'TEXTAREA') {
        if (e.key !== 'Escape' && e.key !== 'Tab' && e.key !== 'Enter') return;
    }
    
    // Global shortcuts (work from anywhere)
    if (e.key === '?') {
        e.preventDefault();
        toggleShortcutsHelp();
        return;
    }
    
    if (e.key === ',') {
        e.preventDefault();
        // Close shortcuts help if open
        const shortcutsModal = document.getElementById('shortcuts-modal');
        if (shortcutsModal && !shortcutsModal.classList.contains('hidden')) {
            closeShortcutsHelp();
        }
        openSettings();
        return;
    }
    
    // Modal-specific shortcuts
    if (modalState && modalState.isOpen) {
        switch (e.key) {
            case 'Escape':
                // If bbox edit mode active, cancel it first
                if (bboxEditorState.isActive) {
                    cancelBboxEdit();
                    return;
                }
                closeImageModal();
                return;
            case 'ArrowLeft':
                e.preventDefault();
                modalPrevImage();
                return;
            case 'ArrowRight':
                e.preventDefault();
                modalNextImage();
                return;
            case 'Delete':
            case 'Backspace':
                // Delete selected bbox if in edit mode
                if (bboxEditorState.isActive && bboxEditorState.selectedIndex !== null) {
                    e.preventDefault();
                    deleteBbox();
                    return;
                }
                break;
        }
        return;  // Don't process other shortcuts when modal open
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        // Shortcuts modal
        const shortcutsModal = document.getElementById('shortcuts-modal');
        if (shortcutsModal && !shortcutsModal.classList.contains('hidden')) {
            closeShortcutsHelp();
            return;
        }
        // Custom grid modal
        const customGridModal = document.getElementById('custom-grid-modal');
        if (customGridModal && !customGridModal.classList.contains('hidden')) {
            closeCustomGridModal();
            return;
        }
        // Settings modal
        if (!document.getElementById('settings-modal').classList.contains('hidden')) {
            closeSettings();
            return;
        }
        // Flag modal
        if (!document.getElementById('flag-modal').classList.contains('hidden')) {
            closeFlagModal();
            return;
        }
        // Delete modal
        if (!document.getElementById('delete-modal').classList.contains('hidden')) {
            closeDeleteModal();
            return;
        }
        if (!document.getElementById('browser-modal').classList.contains('hidden')) {
            closeBrowser();
            return;
        }
        // Deselect all if something is selected
        if (gridState.selectedImages.size > 0) {
            deselectAll();
            return;
        }
        return;
    }
    
    // Only handle grid shortcuts when main app is visible
    if (document.getElementById('main-app').classList.contains('hidden')) {
        return;
    }
    
    // Grid navigation and shortcuts
    switch (e.key) {
        case 'w':
        case 'W':
            e.preventDefault();
            previousPage();
            break;
        case 'e':
        case 'E':
            e.preventDefault();
            nextPage();
            break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9':
            // Check if hovering over image or have selection - set quality flag
            const hoveredForQuality = document.querySelector('.image-card:hover');
            if (hoveredForQuality || gridState.selectedImages.size > 0) {
                e.preventDefault();
                setQualityFlagByNumber(parseInt(e.key));
            } else {
                // No hover/selection: use for grid size (1-4 only)
                const gridSizes = { '1': 4, '2': 9, '3': 25, '4': 36 };
                if (gridSizes[e.key]) {
                    setGridSize(gridSizes[e.key]);
                }
            }
            break;
        case 'a':
        case 'A':
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
            }
            selectAllOnPage();
            break;
        case 'd':
        case 'D':
            deselectAllOnPage();
            break;
        case ' ':  // Space to open hovered image
            e.preventDefault();
            const hoveredCard = document.querySelector('.image-card:hover');
            if (hoveredCard) {
                openWider(parseInt(hoveredCard.dataset.seqId));
            }
            break;
        case 'r':
        case 'R':
            e.preventDefault();
            if (gridState.selectedImages.size > 0) {
                deleteSelectedImages();
            } else {
                // Try to delete hovered image
                const hoveredForDelete = document.querySelector('.image-card:hover');
                if (hoveredForDelete) {
                    deleteImage(parseInt(hoveredForDelete.dataset.seqId));
                }
            }
            break;
        case 'f':
        case 'F':
            e.preventDefault();
            if (gridState.selectedImages.size > 0) {
                openBulkFlagModal();
            } else {
                const hoveredForFlag = document.querySelector('.image-card:hover');
                if (hoveredForFlag) {
                    openFlagModal(parseInt(hoveredForFlag.dataset.seqId));
                }
            }
            break;
        case 'q':
        case 'Q':
            e.preventDefault();
            cycleQualityFlag();
            break;
        case 'p':
        case 'P':
            e.preventDefault();
            openPerspectiveFlagQuick();
            break;
        case '\\':  // Backslash to toggle filter panel
            e.preventDefault();
            toggleFilterPanel();
            break;
        case 'g':
        case 'G':  // 'g' to open custom grid modal
            e.preventDefault();
            openCustomGridModal();
            break;
    }
}

// ============================================
// Populate Default Options
// ============================================

function populateDefaultOptions() {
    // Get available flags from project settings or defaults
    const qualityFlags = getAvailableQualityFlags();
    const perspectiveFlags = getAvailablePerspectiveFlags();
    
    // Populate quality flags radio buttons
    const qualityContainer = document.getElementById('default-quality-flags');
    qualityContainer.innerHTML = qualityFlags.map((flag, i) => `
        <label>
            <input type="radio" name="default-quality" value="${flag}" ${i === 1 ? 'checked' : ''}>
            ${flag}
        </label>
    `).join('');
    
    // Add "None" option for perspective
    const perspectiveContainer = document.getElementById('default-perspective-flags');
    perspectiveContainer.innerHTML = `
        <label>
            <input type="radio" name="default-perspective" value="" checked>
            None
        </label>
    ` + perspectiveFlags.slice(0, 4).map(flag => `
        <label>
            <input type="radio" name="default-perspective" value="${flag}">
            ${flag}
        </label>
    `).join('') + (perspectiveFlags.length > 4 ? `
        <label>
            <input type="radio" name="default-perspective" value="">
            <em>+ more...</em>
        </label>
    ` : '');
    
    // Populate visible labels checkboxes
    const labelsContainer = document.getElementById('visible-labels');
    labelsContainer.innerHTML = ALL_LABELS.map(label => `
        <label>
            <input type="checkbox" name="visible-label" value="${label}" 
                   ${DEFAULT_VISIBLE_LABELS.includes(label) ? 'checked' : ''}>
            ${label}
        </label>
    `).join('');
}

// ============================================
// Load Recent Projects
// ============================================

async function loadRecentProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('recent-projects');
            select.innerHTML = '<option value="">Select a project...</option>';
            
            if (data.data.projects.length === 0) {
                select.innerHTML += '<option value="" disabled>No projects yet</option>';
            } else {
                data.data.projects.forEach(project => {
                    select.innerHTML += `
                        <option value="${project.name}" 
                                data-count="${project.image_count}"
                                data-dir="${project.directory}">
                            ${project.name} (${project.image_count} images)
                        </option>
                    `;
                });
            }
        }
    } catch (error) {
        console.error('Failed to load projects:', error);
        showNotification('Failed to load projects', 'error');
    }
}

function onRecentProjectChange(e) {
    const select = e.target;
    const selected = select.options[select.selectedIndex];
    const infoDiv = document.getElementById('recent-project-info');
    
    if (selected && selected.value) {
        const dir = selected.dataset.dir;
        infoDiv.textContent = `Directory: ${dir}`;
    } else {
        infoDiv.textContent = '';
    }
}

// ============================================
// Directory Browser
// ============================================

function openBrowser() {
    document.getElementById('browser-modal').classList.remove('hidden');
    // Start from home directory
    loadDirectory(getDefaultBrowserPath());
}

function closeBrowser() {
    document.getElementById('browser-modal').classList.add('hidden');
}

function getDefaultBrowserPath() {
    // Use a sensible default path
    return '/home';
}

async function loadDirectory(path) {
    try {
        const response = await fetch('/api/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await response.json();
        
        if (data.success) {
            browserCurrentPath = data.data.current_path;
            renderDirectoryBrowser(data.data);
        } else {
            showNotification(data.error || 'Failed to browse directory', 'error');
        }
    } catch (error) {
        console.error('Failed to browse directory:', error);
        showNotification('Failed to browse directory', 'error');
    }
}

function renderDirectoryBrowser(data) {
    // Update current path display
    document.getElementById('current-path').value = data.current_path;
    
    // Update parent button state
    const parentBtn = document.getElementById('parent-btn');
    parentBtn.disabled = !data.parent;
    parentBtn.onclick = () => data.parent && loadDirectory(data.parent);
    
    // Update info
    const infoDiv = document.getElementById('browser-info');
    if (data.has_images) {
        infoDiv.textContent = `✓ ${data.image_count} images found in this directory`;
        infoDiv.className = 'browser-info has-images';
    } else {
        infoDiv.textContent = 'No images in this directory';
        infoDiv.className = 'browser-info';
    }
    
    // Update select button
    const selectBtn = document.getElementById('select-dir-btn');
    selectBtn.disabled = !data.has_images;
    
    // Render directory list
    const listDiv = document.getElementById('browser-list');
    
    if (data.directories.length === 0) {
        listDiv.innerHTML = '<div class="browser-item"><span class="name" style="color:#666">No subdirectories</span></div>';
    } else {
        listDiv.innerHTML = data.directories.map(dir => `
            <div class="browser-item" onclick="loadDirectory('${dir.path.replace(/'/g, "\\'")}')">
                <span class="icon">📁</span>
                <span class="name">${dir.name}</span>
            </div>
        `).join('');
    }
}

function selectCurrentDirectory() {
    if (browserCurrentPath) {
        document.getElementById('directory-path').value = browserCurrentPath;
        
        // Update info text
        fetch('/api/browse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: browserCurrentPath })
        })
        .then(r => r.json())
        .then(data => {
            const infoDiv = document.getElementById('directory-info');
            if (data.success && data.data.has_images) {
                infoDiv.textContent = `✓ ${data.data.image_count} images found`;
                infoDiv.className = 'info-text success';
            }
        });
        
        closeBrowser();
    }
}

function goToParent() {
    // Will be called from parent button onclick set in renderDirectoryBrowser
}

// ============================================
// Create Project
// ============================================

async function createProject() {
    const name = document.getElementById('project-name').value.trim();
    const directory = document.getElementById('directory-path').value;
    
    // Validation
    if (!name) {
        showNotification('Please enter a project name', 'warning');
        document.getElementById('project-name').focus();
        return;
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(name)) {
        showNotification('Project name can only contain letters, numbers, and underscores', 'warning');
        return;
    }
    
    if (!directory) {
        showNotification('Please select a directory', 'warning');
        return;
    }
    
    // Get selected options
    const defaultQuality = document.querySelector('input[name="default-quality"]:checked')?.value;
    const defaultPerspective = document.querySelector('input[name="default-perspective"]:checked')?.value || null;
    const visibleLabels = Array.from(document.querySelectorAll('input[name="visible-label"]:checked'))
        .map(cb => cb.value);
    
    try {
        showLoadingOverlay('Creating project...');
        
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                directory,
                settings: {
                    default_quality_flag: defaultQuality,
                    default_perspective_flag: defaultPerspective,
                    visible_labels: visibleLabels
                }
            })
        });
        
        const data = await response.json();
        hideLoadingOverlay();
        
        if (data.success) {
            showNotification(`Project created with ${data.data.image_count} images`, 'success');
            currentProject = name;
            projectData = data.data;
            closeStartupModal();
            initializeMainApp(data.data);
        } else {
            showNotification(data.error || 'Failed to create project', 'error');
        }
    } catch (error) {
        hideLoadingOverlay();
        console.error('Failed to create project:', error);
        showNotification('Failed to create project', 'error');
    }
}

// ============================================
// Open Project
// ============================================

async function openProject() {
    const name = document.getElementById('recent-projects').value;
    
    if (!name) {
        showNotification('Please select a project', 'warning');
        return;
    }
    
    try {
        showLoadingOverlay('Loading project...');
        
        const response = await fetch(`/api/projects/${name}`);
        const data = await response.json();
        hideLoadingOverlay();
        
        if (data.success) {
            showNotification(`Project loaded: ${data.data.image_count} images`, 'success');
            currentProject = name;
            projectData = data.data;
            closeStartupModal();
            initializeMainApp(data.data);
        } else {
            showNotification(data.error || 'Failed to load project', 'error');
        }
    } catch (error) {
        hideLoadingOverlay();
        console.error('Failed to load project:', error);
        showNotification('Failed to load project', 'error');
    }
}

// ============================================
// Main App Initialization
// ============================================

function initializeMainApp(data) {
    console.log('Initializing main app with project:', data.project_name);
    
    // Set project title
    document.getElementById('project-title').textContent = data.project_name;
    
    // Initialize grid size from project settings
    gridState.gridSize = data.settings?.grid_size || 9;
    gridState.currentPage = 1;
    gridState.selectedImages.clear();
    
    // Check for custom grid settings
    const customGrid = data.settings?.custom_grid;
    if (customGrid && customGrid.cols && customGrid.rows) {
        customGridState.isCustom = true;
        customGridState.cols = customGrid.cols;
        customGridState.rows = customGrid.rows;
    } else {
        customGridState.isCustom = false;
    }
    
    // Clear label cache for new project
    labelCache.clear();
    
    // Initialize visible labels from settings (Phase 3)
    initVisibleLabels(data.settings);
    
    // Setup card click handlers for multi-selection (Phase 4)
    setupCardClickHandlers();
    
    // Update grid selector buttons and grid class
    updateGridSelectorUI();
    updateGridClass();
    
    // Load images
    loadImages();
    
    // Load filter options (Phase 10)
    loadFilterOptionsForProject();
    
    console.log('✓ Main app initialized');
}

// ============================================
// Grid Management
// ============================================

// Custom grid state
const customGridState = {
    isCustom: false,
    cols: 4,
    rows: 4
};

function setGridSize(size) {
    // Mark as preset (not custom)
    customGridState.isCustom = false;
    
    if (![4, 9, 25, 36].includes(size)) size = 9;
    
    gridState.gridSize = size;
    gridState.currentPage = 1;  // Reset to page 1
    
    // Update UI
    updateGridSelectorUI();
    updateGridClass();
    
    // Reload images
    loadImages();
    
    // Save preference to server
    saveGridSizeSetting(size);
}

function setCustomGridSize(cols, rows) {
    customGridState.isCustom = true;
    customGridState.cols = cols;
    customGridState.rows = rows;
    
    const totalSize = cols * rows;
    gridState.gridSize = totalSize;
    gridState.currentPage = 1;
    
    // Update UI
    updateGridSelectorUI();
    updateGridClass();
    
    // Reload images
    loadImages();
    
    // Save preference to server
    saveGridSizeSetting(totalSize, cols, rows);
}

function updateGridSelectorUI() {
    // Update preset buttons
    document.querySelectorAll('.grid-selector button[data-size]').forEach(btn => {
        const isActive = !customGridState.isCustom && parseInt(btn.dataset.size) === gridState.gridSize;
        btn.classList.toggle('active', isActive);
    });
    
    // Update custom button
    const customBtn = document.getElementById('custom-grid-btn');
    if (customBtn) {
        customBtn.classList.toggle('active', customGridState.isCustom);
        if (customGridState.isCustom) {
            customBtn.textContent = `${customGridState.cols}×${customGridState.rows}`;
        } else {
            customBtn.textContent = '⚙';
        }
    }
}

function updateGridClass() {
    const grid = document.getElementById('image-grid');
    grid.className = 'grid';
    
    if (customGridState.isCustom) {
        // Use CSS variables for custom grid
        grid.style.setProperty('--custom-cols', customGridState.cols);
        grid.classList.add('grid-custom');
    } else {
        grid.style.removeProperty('--custom-cols');
        const sizeMap = {4: '2x2', 9: '3x3', 25: '5x5', 36: '6x6'};
        grid.classList.add(`grid-${sizeMap[gridState.gridSize]}`);
    }
}

async function saveGridSizeSetting(size, cols = null, rows = null) {
    try {
        const body = { size };
        if (cols !== null && rows !== null) {
            body.custom_cols = cols;
            body.custom_rows = rows;
        }
        await fetch('/api/settings/grid_size', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
    } catch (error) {
        console.error('Failed to save grid size:', error);
    }
}

// ============================================
// Custom Grid Modal
// ============================================

function openCustomGridModal() {
    const modal = document.getElementById('custom-grid-modal');
    modal.classList.remove('hidden');
    
    // Set current values if custom grid is active
    const colsInput = document.getElementById('custom-cols');
    const rowsInput = document.getElementById('custom-rows');
    
    if (customGridState.isCustom) {
        colsInput.value = customGridState.cols;
        rowsInput.value = customGridState.rows;
    } else {
        colsInput.value = 4;
        rowsInput.value = 4;
    }
    
    updateCustomGridPreview();
    
    // Add input listeners for preview
    colsInput.addEventListener('input', updateCustomGridPreview);
    rowsInput.addEventListener('input', updateCustomGridPreview);
    
    // Focus first input
    colsInput.focus();
    colsInput.select();
}

function closeCustomGridModal() {
    const modal = document.getElementById('custom-grid-modal');
    modal.classList.add('hidden');
}

function updateCustomGridPreview() {
    const cols = parseInt(document.getElementById('custom-cols').value) || 1;
    const rows = parseInt(document.getElementById('custom-rows').value) || 1;
    const total = cols * rows;
    
    document.getElementById('custom-grid-total').textContent = total;
}

function applyCustomGrid() {
    let cols = parseInt(document.getElementById('custom-cols').value);
    let rows = parseInt(document.getElementById('custom-rows').value);
    
    // Validate and clamp values
    cols = Math.max(1, Math.min(10, cols || 1));
    rows = Math.max(1, Math.min(10, rows || 1));
    
    setCustomGridSize(cols, rows);
    closeCustomGridModal();
    
    showNotification(`Grid set to ${cols}×${rows} (${cols * rows} images)`, 'success');
}

// ============================================
// Image Loading
// ============================================

async function loadImages() {
    const grid = document.getElementById('image-grid');
    
    // Show skeleton loader instead of text
    showGridSkeleton();
    
    // Cleanup memory on page change
    cleanupMemory();
    
    try {
        // Build URL with filter parameters
        const filterParams = buildFilterParams();
        
        // Add directory parameter if in browse mode
        let directoryParam = '';
        if (browseState.isActive && browseState.activePath) {
            directoryParam = `&directory=${encodeURIComponent(browseState.activePath)}&mode=${browseState.displayMode}`;
        }
        
        const response = await fetch(
            `/api/images?page=${gridState.currentPage}&size=${gridState.gridSize}${filterParams}${directoryParam}`
        );
        const data = await response.json();
        
        if (data.success) {
            if (data.data.images.length === 0) {
                grid.innerHTML = '<div class="empty-state"><p>📁 No images to display</p></div>';
            } else {
                renderGrid(data.data.images);
            }
            updatePagination(data.data.pagination);
        } else {
            grid.innerHTML = `<div class="error">Failed to load images: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading images:', error);
        grid.innerHTML = '<div class="error">Failed to load images. Check console for details.</div>';
    }
}

function renderGrid(images) {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = '';
    
    images.forEach(img => {
        const card = createImageCard(img);
        grid.appendChild(card);
    });
    
    // Load labels after cards are in DOM (Phase 3)
    loadPageLabels(images);
}

function createImageCard(img) {
    const card = document.createElement('div');
    card.className = 'image-card';
    card.dataset.seqId = img.seq_id;
    card.dataset.filename = img.filename;
    card.dataset.imgWidth = img.img_width || 0;
    card.dataset.imgHeight = img.img_height || 0;
    
    // Store full path for browse mode
    if (img.full_path) {
        card.dataset.fullPath = img.full_path;
    }
    
    if (gridState.selectedImages.has(img.seq_id)) {
        card.classList.add('selected');
    }
    
    card.innerHTML = `
        <div class="card-controls">
            <div class="controls-left">
                <label class="select-checkbox-wrapper">
                    <input type="checkbox" class="select-checkbox" 
                           ${gridState.selectedImages.has(img.seq_id) ? 'checked' : ''}
                           onchange="toggleSelect(${img.seq_id}, this.checked)"
                           aria-label="Select image">
                    <span class="checkmark"></span>
                </label>
            </div>
            <div class="controls-right">
                <button class="btn-control btn-expand" onclick="openWider(${img.seq_id})" title="Open Wider (Space)" aria-label="Open image wider">🔍</button>
                <button class="btn-control btn-delete" onclick="deleteImage(${img.seq_id})" title="Delete" aria-label="Delete image">🗑️</button>
                <button class="btn-control btn-flag" onclick="openFlagModal(${img.seq_id})" title="Flag" aria-label="Set flags">🏷️</button>
            </div>
        </div>
        <div class="image-container">
            ${img.thumbnail 
                ? `<img src="${img.thumbnail}" alt="${img.filename}" loading="lazy" onload="positionGridOverlay(${img.seq_id})">`
                : '<div class="no-image">No preview</div>'
            }
            <div class="label-overlay" id="labels-${img.seq_id}">
                <!-- Labels added by Phase 3 -->
            </div>
        </div>
        <div class="card-flags">
            ${renderFlags(img.quality_flags, 'quality')}
            ${renderFlags(img.perspective_flags, 'perspective')}
        </div>
        <div class="selection-overlay"></div>
    `;
    
    return card;
}

function renderFlags(flags, type) {
    if (!flags || flags.length === 0) return '';
    
    const colorClass = type === 'quality' ? 'flag-quality' : 'flag-perspective';
    
    return flags.map(flag => {
        // Add individual flag class for color styling
        const flagClass = `flag-${flag.replace(/_/g, '_')}`;
        return `<span class="flag-pill ${colorClass} ${flagClass}">${flag}</span>`;
    }).join('');
}

// ============================================
// Pagination
// ============================================

function updatePagination(pagination) {
    gridState.totalPages = pagination.total_pages;
    gridState.totalImages = pagination.total_images;
    gridState.currentPage = pagination.current_page;
    
    document.getElementById('current-page').textContent = pagination.current_page;
    document.getElementById('total-pages').textContent = pagination.total_pages;
    document.getElementById('total-images').textContent = pagination.total_images;
    
    // Enable/disable nav buttons
    document.getElementById('btn-prev').disabled = pagination.current_page <= 1;
    document.getElementById('btn-next').disabled = pagination.current_page >= pagination.total_pages;
    
    // Update filter match count (Phase 10)
    updateFilterMatchCount(pagination.total_images);
}

function nextPage() {
    if (gridState.currentPage < gridState.totalPages) {
        gridState.currentPage++;
        loadImages();
    }
}

function previousPage() {
    if (gridState.currentPage > 1) {
        gridState.currentPage--;
        loadImages();
    }
}

// ============================================
// Selection System (Phase 4)
// ============================================

// Selection state
let lastClickedSeqId = null;

function toggleSelect(seqId, isSelected) {
    if (isSelected) {
        gridState.selectedImages.add(seqId);
    } else {
        gridState.selectedImages.delete(seqId);
    }
    
    lastClickedSeqId = seqId;
    
    // Update card visual
    updateCardSelectionUI(seqId, isSelected);
    updateSelectedCount();
}

function updateCardSelectionUI(seqId, isSelected) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    card.classList.toggle('selected', isSelected);
    
    const checkbox = card.querySelector('.select-checkbox');
    if (checkbox) {
        checkbox.checked = isSelected;
    }
}

function selectAllOnPage() {
    const cards = document.querySelectorAll('.image-card');
    let count = 0;
    cards.forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        gridState.selectedImages.add(seqId);
        updateCardSelectionUI(seqId, true);
        count++;
    });
    updateSelectedCount();
    showNotification(`Selected ${count} images on this page`, 'success', 1500);
}

function deselectAllOnPage() {
    const cards = document.querySelectorAll('.image-card');
    let count = 0;
    cards.forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        if (gridState.selectedImages.has(seqId)) {
            gridState.selectedImages.delete(seqId);
            updateCardSelectionUI(seqId, false);
            count++;
        }
    });
    lastClickedSeqId = null;
    updateSelectedCount();
    if (count > 0) {
        showNotification(`Deselected ${count} images`, 'info', 1500);
    }
}

function deselectAll() {
    gridState.selectedImages.forEach(seqId => {
        updateCardSelectionUI(seqId, false);
    });
    gridState.selectedImages.clear();
    lastClickedSeqId = null;
    updateSelectedCount();
}

function selectWithShift(seqId) {
    if (lastClickedSeqId === null) {
        toggleSelect(seqId, true);
        return;
    }
    
    // Get all visible seq_ids in order
    const visibleIds = Array.from(document.querySelectorAll('.image-card'))
        .map(card => parseInt(card.dataset.seqId));
    
    const lastIdx = visibleIds.indexOf(lastClickedSeqId);
    const currentIdx = visibleIds.indexOf(seqId);
    
    if (lastIdx === -1 || currentIdx === -1) {
        toggleSelect(seqId, true);
        return;
    }
    
    // Select range
    const start = Math.min(lastIdx, currentIdx);
    const end = Math.max(lastIdx, currentIdx);
    
    for (let i = start; i <= end; i++) {
        const id = visibleIds[i];
        gridState.selectedImages.add(id);
        updateCardSelectionUI(id, true);
    }
    
    updateSelectedCount();
}

function updateSelectedCount() {
    document.getElementById('selected-count').textContent = gridState.selectedImages.size;
}

// Setup card click handlers for multi-selection
function setupCardClickHandlers() {
    document.getElementById('image-grid').addEventListener('click', (e) => {
        const card = e.target.closest('.image-card');
        if (!card) return;
        
        // Ignore if clicking on controls or checkbox
        if (e.target.closest('.card-controls') || 
            e.target.classList.contains('select-checkbox') ||
            e.target.tagName === 'BUTTON') {
            return;
        }
        
        const seqId = parseInt(card.dataset.seqId);
        
        if (e.shiftKey) {
            // Shift-click: range select
            e.preventDefault();
            selectWithShift(seqId);
        } else if (e.ctrlKey || e.metaKey) {
            // Ctrl/Cmd-click: toggle individual
            e.preventDefault();
            toggleSelect(seqId, !gridState.selectedImages.has(seqId));
        }
    });
}

// ============================================
// Image Modal (Phase 4)
// ============================================

let modalState = {
    isOpen: false,
    currentSeqId: null,
    visibleSeqIds: []
};

async function openWider(seqId) {
    modalState.currentSeqId = seqId;
    modalState.visibleSeqIds = Array.from(document.querySelectorAll('.image-card'))
        .map(card => parseInt(card.dataset.seqId));
    
    await loadModalImage(seqId);
    
    document.getElementById('image-modal').classList.remove('hidden');
    modalState.isOpen = true;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    updateModalNavButtons();
}

async function loadModalImage(seqId) {
    const modalImg = document.getElementById('modal-image');
    const filenameEl = document.getElementById('modal-filename');
    const seqIdEl = document.getElementById('modal-seq-id');
    const labelsEl = document.getElementById('modal-labels');
    
    // Show loading state
    modalImg.src = '';
    modalImg.alt = 'Loading...';
    labelsEl.innerHTML = '';
    filenameEl.textContent = 'Loading...';
    seqIdEl.textContent = '';
    
    try {
        let endpoint;
        
        // Browse mode: use full path from card
        if (browseState.isActive) {
            const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
            if (card && card.dataset.fullPath) {
                // Remove leading slash for URL encoding
                const imagePath = card.dataset.fullPath.replace(/^\//, '');
                endpoint = `/api/browse/image/full/${imagePath}`;
            } else {
                filenameEl.textContent = 'Error: Image path not found';
                return;
            }
        } else {
            // Project mode
            endpoint = `/api/image/${seqId}/full`;
        }
        
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (data.success) {
            // Set up onload to position overlay correctly
            modalImg.onload = function() {
                positionModalOverlay();
            };
            
            modalImg.src = data.data.image;
            modalImg.alt = data.data.filename;
            filenameEl.textContent = data.data.filename;
            seqIdEl.textContent = `#${seqId}`;
            
            // Render labels overlay (will be repositioned after image loads)
            await renderModalLabels(seqId);
            
            // Render edit panel
            await renderEditPanel(seqId);
        } else {
            filenameEl.textContent = 'Error loading image';
        }
    } catch (error) {
        console.error('Failed to load full image:', error);
        filenameEl.textContent = 'Error loading image';
    }
}

// Position modal overlay to match the rendered image dimensions
function positionModalOverlay() {
    const img = document.getElementById('modal-image');
    const overlay = document.getElementById('modal-labels');
    const container = document.querySelector('.modal-image-container');
    
    if (!img || !overlay || !container || !img.naturalWidth) return;
    
    // Get actual rendered image dimensions
    const imgRect = img.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    
    // Calculate offset from container to image
    const offsetLeft = imgRect.left - containerRect.left;
    const offsetTop = imgRect.top - containerRect.top;
    
    // Position and size overlay to match the image exactly
    overlay.style.position = 'absolute';
    overlay.style.left = `${offsetLeft}px`;
    overlay.style.top = `${offsetTop}px`;
    overlay.style.width = `${imgRect.width}px`;
    overlay.style.height = `${imgRect.height}px`;
    overlay.style.right = 'auto';
    overlay.style.bottom = 'auto';
}

// Calculate actual rendered image dimensions within object-fit: contain
function getRenderedImageDimensions(img) {
    const containerWidth = img.clientWidth;
    const containerHeight = img.clientHeight;
    const naturalWidth = img.naturalWidth;
    const naturalHeight = img.naturalHeight;
    
    if (!naturalWidth || !naturalHeight || !containerWidth || !containerHeight) return null;
    
    const containerAspect = containerWidth / containerHeight;
    const imageAspect = naturalWidth / naturalHeight;
    
    let renderedWidth, renderedHeight, offsetX, offsetY;
    
    if (imageAspect > containerAspect) {
        // Image is wider than container - letterbox top/bottom
        renderedWidth = containerWidth;
        renderedHeight = containerWidth / imageAspect;
        offsetX = 0;
        offsetY = (containerHeight - renderedHeight) / 2;
    } else {
        // Image is taller than container - letterbox left/right
        renderedHeight = containerHeight;
        renderedWidth = containerHeight * imageAspect;
        offsetX = (containerWidth - renderedWidth) / 2;
        offsetY = 0;
    }
    
    return { renderedWidth, renderedHeight, offsetX, offsetY };
}

// Position grid card overlay to match the rendered image dimensions
function positionGridOverlay(seqId) {
    // Use requestAnimationFrame to ensure layout is calculated
    requestAnimationFrame(() => {
        const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
        if (!card) {
            return;
        }
        
        const img = card.querySelector('.image-container img');
        const overlay = document.getElementById(`labels-${seqId}`);
        
        if (!img || !overlay) {
            return;
        }
        
        // Get original image dimensions from data attributes
        const origWidth = parseInt(card.dataset.imgWidth) || 0;
        const origHeight = parseInt(card.dataset.imgHeight) || 0;
        
        if (!origWidth || !origHeight) {
            // Fallback: assume thumbnail fills container
            overlay.style.position = 'absolute';
            overlay.style.left = '0';
            overlay.style.top = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            return;
        }
        
        // Container (thumbnail) is square
        const containerSize = img.clientWidth; // Same as clientHeight for square
        
        if (!containerSize) {
            setTimeout(() => positionGridOverlay(seqId), 50);
            return;
        }
        
        // Calculate where the actual image sits within the letterboxed thumbnail
        // This mirrors the Python thumbnail generation logic
        const origAspect = origWidth / origHeight;
        
        let imgWidth, imgHeight, offsetX, offsetY;
        
        if (origAspect > 1) {
            // Landscape: image fills width, letterboxed top/bottom
            imgWidth = containerSize;
            imgHeight = containerSize / origAspect;
            offsetX = 0;
            offsetY = (containerSize - imgHeight) / 2;
        } else {
            // Portrait or square: image fills height, letterboxed left/right
            imgHeight = containerSize;
            imgWidth = containerSize * origAspect;
            offsetX = (containerSize - imgWidth) / 2;
            offsetY = 0;
        }
        
        // Position and size overlay to match the actual image area within letterbox
        overlay.style.position = 'absolute';
        overlay.style.left = `${offsetX}px`;
        overlay.style.top = `${offsetY}px`;
        overlay.style.width = `${imgWidth}px`;
        overlay.style.height = `${imgHeight}px`;
        overlay.style.right = 'auto';
        overlay.style.bottom = 'auto';
    });
}

// Reposition all visible overlays (called on window resize)
function repositionAllOverlays() {
    // Reposition grid card overlays
    document.querySelectorAll('.image-card').forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        positionGridOverlay(seqId);
    });
    
    // Reposition modal overlay if modal is open
    if (modalState.isOpen) {
        positionModalOverlay();
    }
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function renderModalLabels(seqId) {
    const labelData = await loadLabels(seqId);
    const overlay = document.getElementById('modal-labels');
    
    if (!overlay || !labelData || !labelData.has_labels) {
        overlay.innerHTML = '';
        return;
    }
    
    overlay.innerHTML = '';
    
    if (visibleLabels.length === 0 && !showBoundingBoxes) {
        return;
    }
    
    labelData.objects.forEach((obj, idx) => {
        const vehicleColor = getVehicleColor(obj.labels.color);
        const boxBorderColor = vehicleColor ? vehicleColor.border : 'rgba(74, 105, 189, 0.7)';
        
        // Draw bounding box
        if (showBoundingBoxes) {
            const bbox = document.createElement('div');
            bbox.className = 'bbox';
            bbox.style.left = `${obj.rect_percent.x}%`;
            bbox.style.top = `${obj.rect_percent.y}%`;
            bbox.style.width = `${obj.rect_percent.width}%`;
            bbox.style.height = `${obj.rect_percent.height}%`;
            bbox.style.borderColor = boxBorderColor;
            bbox.style.borderWidth = '3px';
            
            // Add direction indicator to bounding box (modal)
            const direction = obj.direction || 'front';
            const dirIndicator = createDirectionIndicator(seqId, idx, direction);
            bbox.appendChild(dirIndicator);
            
            overlay.appendChild(bbox);
        }
        
        if (visibleLabels.length === 0) return;
        
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'object-labels';
        labelsDiv.style.left = `${obj.center_percent.x}%`;
        labelsDiv.style.top = `${obj.center_percent.y}%`;
        
        visibleLabels.forEach(labelName => {
            const value = obj.labels[labelName];
            const labelSpan = document.createElement('span');
            labelSpan.className = 'label-line';
            
            if (value === null || value === undefined || value === '') {
                labelSpan.textContent = 'NULL';
                labelSpan.classList.add('null');
            } else {
                labelSpan.textContent = value;
            }
            
            if (vehicleColor) {
                labelSpan.style.background = vehicleColor.bg;
                labelSpan.style.color = vehicleColor.text;
            }
            
            labelsDiv.appendChild(labelSpan);
        });
        
        overlay.appendChild(labelsDiv);
    });
}

function updateModalNavButtons() {
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    document.getElementById('modal-prev-btn').disabled = currentIdx <= 0;
    document.getElementById('modal-next-btn').disabled = currentIdx >= modalState.visibleSeqIds.length - 1;
}

function modalPrevImage() {
    // Check if bbox edit mode is active
    if (bboxEditorState.isActive) {
        if (!confirm('You have unsaved bounding box changes. Discard and continue?')) {
            return;
        }
        exitBboxEditMode();
    }
    
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx > 0) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx - 1];
        loadModalImage(modalState.currentSeqId);
        updateModalNavButtons();
    }
}

function modalNextImage() {
    // Check if bbox edit mode is active
    if (bboxEditorState.isActive) {
        if (!confirm('You have unsaved bounding box changes. Discard and continue?')) {
            return;
        }
        exitBboxEditMode();
    }
    
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx < modalState.visibleSeqIds.length - 1) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx + 1];
        loadModalImage(modalState.currentSeqId);
        updateModalNavButtons();
    }
}

function closeImageModal() {
    // Check if bbox edit mode is active
    if (bboxEditorState.isActive) {
        if (!confirm('You have unsaved bounding box changes. Discard and close?')) {
            return;
        }
        exitBboxEditMode();
    }
    
    document.getElementById('image-modal').classList.add('hidden');
    modalState.isOpen = false;
    document.body.style.overflow = '';
}

// ============================================
// Modal Label Editing
// ============================================

let editPanelState = {
    selectedObjectIndex: 0,
    labelData: null,
    isOpen: true
};

function toggleEditPanel() {
    const panel = document.getElementById('modal-edit-panel');
    editPanelState.isOpen = !editPanelState.isOpen;
    panel.classList.toggle('collapsed', !editPanelState.isOpen);
}

async function renderEditPanel(seqId) {
    const objectSelector = document.getElementById('object-selector');
    const labelEditors = document.getElementById('label-editors');
    const bboxEditBtn = document.querySelector('.btn-edit-bbox');
    
    // Reset bbox editor state when loading new image
    if (bboxEditorState.isActive) {
        exitBboxEditMode();
    }
    
    // Reset bbox editor UI
    const bboxViewMode = document.getElementById('bbox-view-mode');
    const bboxEditMode = document.getElementById('bbox-edit-mode');
    if (bboxViewMode) bboxViewMode.classList.remove('hidden');
    if (bboxEditMode) bboxEditMode.classList.add('hidden');
    
    // Get label data
    const labelData = await loadLabels(seqId);
    editPanelState.labelData = labelData;
    editPanelState.selectedObjectIndex = 0;
    
    if (!labelData || !labelData.has_labels || labelData.objects.length === 0) {
        objectSelector.innerHTML = '';
        labelEditors.innerHTML = '<div class="no-labels-message">📋 No labels available for this image</div>';
        // Still allow adding bboxes even with no existing labels
        if (bboxEditBtn) bboxEditBtn.disabled = false;
        return;
    }
    
    // Enable bbox edit button
    if (bboxEditBtn) bboxEditBtn.disabled = false;
    
    // Render object selector buttons
    objectSelector.innerHTML = labelData.objects.map((obj, idx) => {
        const color = obj.labels.color || 'unknown';
        const type = obj.labels.type || 'vehicle';
        return `<button class="object-btn ${idx === 0 ? 'active' : ''}" 
                        onclick="selectObject(${idx})" 
                        data-index="${idx}">
                    ${type} ${idx + 1} <small>(${color})</small>
                </button>`;
    }).join('');
    
    // Render label editors for first object
    renderLabelEditors(0);
}

function selectObject(index) {
    editPanelState.selectedObjectIndex = index;
    
    // Update button states
    document.querySelectorAll('.object-btn').forEach((btn, idx) => {
        btn.classList.toggle('active', idx === index);
    });
    
    // Re-render editors
    renderLabelEditors(index);
    
    // Highlight the selected object's bbox
    highlightObject(index);
}

function renderLabelEditors(objectIndex) {
    const labelEditors = document.getElementById('label-editors');
    const obj = editPanelState.labelData.objects[objectIndex];
    
    if (!obj) {
        labelEditors.innerHTML = '<div class="no-labels-message">No object data</div>';
        return;
    }
    
    const editableLabels = ['color', 'brand', 'model', 'type', 'sub_type'];
    
    labelEditors.innerHTML = editableLabels.map(labelName => {
        const value = obj.labels[labelName] || '';
        const displayName = labelName.replace('_', ' ');
        return `
            <div class="label-editor-group">
                <label for="edit-${labelName}">${displayName}</label>
                <input type="text" 
                       id="edit-${labelName}" 
                       data-label="${labelName}"
                       data-object-index="${objectIndex}"
                       value="${escapeHtml(value)}"
                       placeholder="Enter ${displayName}..."
                       onchange="saveLabelEdit(this)"
                       onkeydown="handleLabelKeydown(event, this)">
            </div>
        `;
    }).join('');
}

function highlightObject(index) {
    // Remove previous highlights
    document.querySelectorAll('#modal-labels .bbox').forEach(bbox => {
        bbox.classList.remove('highlighted');
    });
    
    // Add highlight to selected object
    const bboxes = document.querySelectorAll('#modal-labels .bbox');
    if (bboxes[index]) {
        bboxes[index].classList.add('highlighted');
    }
}

function handleLabelKeydown(event, input) {
    if (event.key === 'Enter') {
        event.preventDefault();
        saveLabelEdit(input);
    } else if (event.key === 'Tab') {
        // Let default Tab behavior work
    }
}

async function saveLabelEdit(input) {
    const labelName = input.dataset.label;
    const objectIndex = parseInt(input.dataset.objectIndex);
    const newValue = input.value.trim();
    const seqId = modalState.currentSeqId;
    
    // Mark as saving
    input.classList.remove('modified', 'saved');
    input.disabled = true;
    
    try {
        const response = await fetch(`/api/labels/${seqId}/${objectIndex}/${labelName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newValue })
        });
        
        const data = await response.json();
        
        if (data.success) {
            input.classList.add('saved');
            
            // Update local cache
            if (editPanelState.labelData?.objects[objectIndex]) {
                editPanelState.labelData.objects[objectIndex].labels[labelName] = newValue;
            }
            
            // Clear label cache so next load gets fresh data
            labelCache.delete(seqId);
            console.log(`[saveLabelEdit] Cache cleared for seqId=${seqId}`);
            
            // Re-render labels overlay in modal
            await renderModalLabels(seqId);
            console.log(`[saveLabelEdit] Modal labels re-rendered`);
            
            // Re-render labels on grid card (so grid updates immediately)
            const gridOverlay = document.getElementById(`labels-${seqId}`);
            console.log(`[saveLabelEdit] Grid overlay element:`, gridOverlay);
            await renderLabels(seqId);
            console.log(`[saveLabelEdit] Grid labels re-rendered`);
            
            // Update object selector button text
            updateObjectSelectorButton(objectIndex);
            
            // Re-highlight the selected object
            highlightObject(objectIndex);
            
            showNotification(`${labelName} updated`, 'success');
            
            // Remove saved class after animation
            setTimeout(() => input.classList.remove('saved'), 1500);
        } else {
            input.classList.add('modified');
            showNotification(`Failed to save: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Save label error:', error);
        input.classList.add('modified');
        showNotification('Failed to save label', 'error');
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function updateObjectSelectorButton(objectIndex) {
    const btn = document.querySelector(`.object-btn[data-index="${objectIndex}"]`);
    if (btn && editPanelState.labelData?.objects[objectIndex]) {
        const obj = editPanelState.labelData.objects[objectIndex];
        const color = obj.labels.color || 'unknown';
        const type = obj.labels.type || 'vehicle';
        btn.innerHTML = `${type} ${objectIndex + 1} <small>(${color})</small>`;
    }
}

// ============================================
// Bounding Box Editor
// ============================================

/**
 * Enter bbox edit mode
 */
function enterBboxEditMode() {
    // Allow editing even with no existing labels (to add new ones)
    const objects = editPanelState.labelData?.objects || [];
    
    // Deep copy objects for editing
    bboxEditorState.originalObjects = JSON.parse(JSON.stringify(objects));
    bboxEditorState.currentObjects = JSON.parse(JSON.stringify(objects));
    bboxEditorState.isActive = true;
    bboxEditorState.selectedIndex = null;
    
    // Get image dimensions
    const modalImg = document.getElementById('modal-image');
    if (modalImg) {
        bboxEditorState.imgWidth = modalImg.naturalWidth || 1000;
        bboxEditorState.imgHeight = modalImg.naturalHeight || 1000;
    }
    
    // Update UI
    document.getElementById('bbox-view-mode').classList.add('hidden');
    document.getElementById('bbox-edit-mode').classList.remove('hidden');
    document.getElementById('label-editors').classList.add('disabled');
    
    // Set appropriate hint
    if (bboxEditorState.currentObjects.length === 0) {
        document.getElementById('bbox-hint').textContent = 'No boxes yet - use "Add New Object" above';
    } else {
        document.getElementById('bbox-hint').textContent = 'Click a box to select it';
    }
    document.getElementById('bbox-delete-btn').disabled = true;
    
    // Re-render bboxes with handles
    renderBboxesEditable();
    
    // Add event listeners for drag
    const overlay = document.getElementById('modal-labels');
    overlay.classList.add('edit-mode');
    overlay.addEventListener('mousedown', handleBboxMouseDown);
    document.addEventListener('mousemove', handleBboxMouseMove);
    document.addEventListener('mouseup', handleBboxMouseUp);
}

/**
 * Exit bbox edit mode
 */
function exitBboxEditMode() {
    bboxEditorState.isActive = false;
    bboxEditorState.selectedIndex = null;
    bboxEditorState.isDrawingNew = false;
    bboxEditorState.isDragging = false;
    
    // Update UI
    document.getElementById('bbox-view-mode').classList.remove('hidden');
    document.getElementById('bbox-edit-mode').classList.add('hidden');
    document.getElementById('label-editors').classList.remove('disabled');
    
    const container = document.querySelector('.modal-image-container');
    if (container) container.classList.remove('drawing-mode');
    
    // Remove event listeners
    const overlay = document.getElementById('modal-labels');
    overlay.classList.remove('edit-mode');
    overlay.removeEventListener('mousedown', handleBboxMouseDown);
    document.removeEventListener('mousemove', handleBboxMouseMove);
    document.removeEventListener('mouseup', handleBboxMouseUp);
    
    // Re-render normal bboxes
    renderModalLabels(modalState.currentSeqId);
}

/**
 * Render bboxes with editable handles
 */
function renderBboxesEditable() {
    const overlay = document.getElementById('modal-labels');
    if (!overlay) return;
    
    overlay.innerHTML = '';
    
    // Remove draw preview if exists
    const existingPreview = overlay.querySelector('.draw-preview');
    if (existingPreview) existingPreview.remove();
    
    bboxEditorState.currentObjects.forEach((obj, idx) => {
        const rect = obj.rect_percent || {
            x: (obj.rect[0] / bboxEditorState.imgWidth) * 100,
            y: (obj.rect[1] / bboxEditorState.imgHeight) * 100,
            width: (obj.rect[2] / bboxEditorState.imgWidth) * 100,
            height: (obj.rect[3] / bboxEditorState.imgHeight) * 100
        };
        
        // Store working rect_percent
        obj.rect_percent = rect;
        
        const vehicleColor = getVehicleColor(obj.labels?.color);
        const boxBorderColor = vehicleColor ? vehicleColor.border : 'rgba(74, 105, 189, 0.7)';
        
        const bbox = document.createElement('div');
        bbox.className = 'bbox editing';
        bbox.dataset.index = idx;
        
        if (idx === bboxEditorState.selectedIndex) {
            bbox.classList.add('selected');
        }
        
        bbox.style.left = `${rect.x}%`;
        bbox.style.top = `${rect.y}%`;
        bbox.style.width = `${rect.width}%`;
        bbox.style.height = `${rect.height}%`;
        bbox.style.borderColor = boxBorderColor;
        bbox.style.borderWidth = '3px';
        
        // Add resize handles
        const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
        handles.forEach(pos => {
            const handle = document.createElement('div');
            handle.className = `bbox-handle ${pos}`;
            handle.dataset.handle = pos;
            handle.dataset.index = idx;
            bbox.appendChild(handle);
        });
        
        // Add index label
        const indexLabel = document.createElement('span');
        indexLabel.className = 'bbox-index-label';
        indexLabel.textContent = idx + 1;
        indexLabel.style.cssText = 'position:absolute;top:2px;left:2px;background:rgba(0,0,0,0.7);color:#fff;padding:2px 6px;font-size:11px;border-radius:3px;';
        bbox.appendChild(indexLabel);
        
        overlay.appendChild(bbox);
    });
}

/**
 * Handle mouse down on bbox or handle
 */
function handleBboxMouseDown(e) {
    if (!bboxEditorState.isActive) return;
    
    // Prevent browser's default image drag behavior
    e.preventDefault();
    
    const overlay = document.getElementById('modal-labels');
    const rect = overlay.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    // Check if drawing new bbox
    if (bboxEditorState.isDrawingNew) {
        e.stopPropagation();
        bboxEditorState.drawStart = { x, y };
        bboxEditorState.isDragging = true;
        bboxEditorState.dragType = 'draw';
        return;
    }
    
    // Check if clicked on handle
    const handle = e.target.closest('.bbox-handle');
    if (handle) {
        e.stopPropagation();
        const idx = parseInt(handle.dataset.index);
        const pos = handle.dataset.handle;
        
        selectBbox(idx);
        
        bboxEditorState.isDragging = true;
        bboxEditorState.dragType = `resize-${pos}`;
        bboxEditorState.dragStartPos = { x, y };
        bboxEditorState.dragStartRect = { ...bboxEditorState.currentObjects[idx].rect_percent };
        return;
    }
    
    // Check if clicked on bbox body
    const bbox = e.target.closest('.bbox.editing');
    if (bbox) {
        e.stopPropagation();
        const idx = parseInt(bbox.dataset.index);
        
        selectBbox(idx);
        
        bboxEditorState.isDragging = true;
        bboxEditorState.dragType = 'move';
        bboxEditorState.dragStartPos = { x, y };
        bboxEditorState.dragStartRect = { ...bboxEditorState.currentObjects[idx].rect_percent };
        return;
    }
    
    // Clicked on empty area - deselect
    selectBbox(null);
}

/**
 * Handle mouse move for drag operations
 */
function handleBboxMouseMove(e) {
    if (!bboxEditorState.isActive || !bboxEditorState.isDragging) return;
    
    const overlay = document.getElementById('modal-labels');
    const rect = overlay.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    
    // Drawing new bbox
    if (bboxEditorState.dragType === 'draw' && bboxEditorState.drawStart) {
        renderDrawPreview(bboxEditorState.drawStart, { x, y });
        return;
    }
    
    const idx = bboxEditorState.selectedIndex;
    if (idx === null) return;
    
    const startRect = bboxEditorState.dragStartRect;
    const startPos = bboxEditorState.dragStartPos;
    const dx = x - startPos.x;
    const dy = y - startPos.y;
    
    let newRect = { ...startRect };
    
    if (bboxEditorState.dragType === 'move') {
        // Move entire bbox
        newRect.x = Math.max(0, Math.min(100 - startRect.width, startRect.x + dx));
        newRect.y = Math.max(0, Math.min(100 - startRect.height, startRect.y + dy));
    } else if (bboxEditorState.dragType.startsWith('resize-')) {
        const handle = bboxEditorState.dragType.split('-')[1];
        const minSize = 2; // Minimum 2% size
        
        // Resize based on handle position
        if (handle.includes('w')) {
            const newX = Math.max(0, startRect.x + dx);
            const newWidth = startRect.width - (newX - startRect.x);
            if (newWidth >= minSize) {
                newRect.x = newX;
                newRect.width = newWidth;
            }
        }
        if (handle.includes('e')) {
            newRect.width = Math.max(minSize, Math.min(100 - startRect.x, startRect.width + dx));
        }
        if (handle.includes('n')) {
            const newY = Math.max(0, startRect.y + dy);
            const newHeight = startRect.height - (newY - startRect.y);
            if (newHeight >= minSize) {
                newRect.y = newY;
                newRect.height = newHeight;
            }
        }
        if (handle.includes('s')) {
            newRect.height = Math.max(minSize, Math.min(100 - startRect.y, startRect.height + dy));
        }
    }
    
    // Update current object
    bboxEditorState.currentObjects[idx].rect_percent = newRect;
    
    // Update pixel rect
    bboxEditorState.currentObjects[idx].rect = [
        (newRect.x / 100) * bboxEditorState.imgWidth,
        (newRect.y / 100) * bboxEditorState.imgHeight,
        (newRect.width / 100) * bboxEditorState.imgWidth,
        (newRect.height / 100) * bboxEditorState.imgHeight
    ];
    
    // Re-render
    renderBboxesEditable();
}

/**
 * Handle mouse up - end drag
 */
function handleBboxMouseUp(e) {
    if (!bboxEditorState.isActive) return;
    
    // Finish drawing new bbox
    if (bboxEditorState.dragType === 'draw' && bboxEditorState.drawStart) {
        const overlay = document.getElementById('modal-labels');
        const rect = overlay.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        
        finishDrawNewBbox(bboxEditorState.drawStart, { x, y });
    }
    
    bboxEditorState.isDragging = false;
    bboxEditorState.dragType = null;
    bboxEditorState.dragStartPos = null;
    bboxEditorState.dragStartRect = null;
}

/**
 * Render draw preview rectangle
 */
function renderDrawPreview(start, current) {
    const overlay = document.getElementById('modal-labels');
    let preview = overlay.querySelector('.draw-preview');
    
    if (!preview) {
        preview = document.createElement('div');
        preview.className = 'draw-preview';
        overlay.appendChild(preview);
    }
    
    const left = Math.min(start.x, current.x);
    const top = Math.min(start.y, current.y);
    const width = Math.abs(current.x - start.x);
    const height = Math.abs(current.y - start.y);
    
    preview.style.left = `${left}%`;
    preview.style.top = `${top}%`;
    preview.style.width = `${width}%`;
    preview.style.height = `${height}%`;
}

/**
 * Finish drawing new bbox
 */
function finishDrawNewBbox(start, end) {
    const left = Math.min(start.x, end.x);
    const top = Math.min(start.y, end.y);
    const width = Math.abs(end.x - start.x);
    const height = Math.abs(end.y - start.y);
    
    // Minimum size check (at least 2%)
    if (width < 2 || height < 2) {
        showNotification('Rectangle too small, try again', 'warning');
        bboxEditorState.isDrawingNew = false;
        const container = document.querySelector('.modal-image-container');
        if (container) container.classList.remove('drawing-mode');
        document.getElementById('bbox-hint').textContent = 'Click a box to select it';
        
        // Remove preview
        const preview = document.querySelector('.draw-preview');
        if (preview) preview.remove();
        
        renderBboxesEditable();
        return;
    }
    
    // Create new object with empty labels
    const newObj = {
        rect: [
            (left / 100) * bboxEditorState.imgWidth,
            (top / 100) * bboxEditorState.imgHeight,
            (width / 100) * bboxEditorState.imgWidth,
            (height / 100) * bboxEditorState.imgHeight
        ],
        rect_percent: { x: left, y: top, width, height },
        labels: {
            color: '',
            brand: '',
            model: '',
            type: '',
            sub_type: '',
            lp_coords: null
        },
        direction: 'front'
    };
    
    bboxEditorState.currentObjects.push(newObj);
    
    // Exit draw mode
    bboxEditorState.isDrawingNew = false;
    const container = document.querySelector('.modal-image-container');
    if (container) container.classList.remove('drawing-mode');
    document.getElementById('bbox-hint').textContent = 'Click a box to select it';
    
    // Select the new bbox
    selectBbox(bboxEditorState.currentObjects.length - 1);
    
    // Re-render
    renderBboxesEditable();
    
    showNotification(`Added object #${bboxEditorState.currentObjects.length}`, 'success');
}

/**
 * Select a bbox by index
 */
function selectBbox(index) {
    bboxEditorState.selectedIndex = index;
    
    // Update delete button
    document.getElementById('bbox-delete-btn').disabled = (index === null);
    
    // Re-render to show selection
    renderBboxesEditable();
    
    // Sync with object selector if exists
    if (index !== null && editPanelState.labelData?.objects[index]) {
        // Update the edit panel to show this object's labels
        selectObject(index);
    }
}

/**
 * Add new object - creates a default bbox and enters edit mode
 */
function addNewObject() {
    // Get image dimensions
    const modalImg = document.getElementById('modal-image');
    if (modalImg) {
        bboxEditorState.imgWidth = modalImg.naturalWidth || 1000;
        bboxEditorState.imgHeight = modalImg.naturalHeight || 1000;
    }
    
    // Create new object with default centered position (20% of image size)
    const defaultSize = 20;  // 20% of image
    const centerX = 50 - defaultSize / 2;  // Center it
    const centerY = 50 - defaultSize / 2;
    
    const newObj = {
        rect: [
            (centerX / 100) * bboxEditorState.imgWidth,
            (centerY / 100) * bboxEditorState.imgHeight,
            (defaultSize / 100) * bboxEditorState.imgWidth,
            (defaultSize / 100) * bboxEditorState.imgHeight
        ],
        rect_percent: { x: centerX, y: centerY, width: defaultSize, height: defaultSize },
        labels: {
            color: '',
            brand: '',
            model: '',
            type: '',
            sub_type: '',
            lp_coords: null
        },
        direction: 'front'
    };
    
    // If not already in edit mode, enter it
    if (!bboxEditorState.isActive) {
        // Deep copy existing objects for editing
        bboxEditorState.originalObjects = JSON.parse(JSON.stringify(editPanelState.labelData?.objects || []));
        bboxEditorState.currentObjects = JSON.parse(JSON.stringify(editPanelState.labelData?.objects || []));
        bboxEditorState.isActive = true;
        
        // Update UI
        document.getElementById('bbox-view-mode').classList.add('hidden');
        document.getElementById('bbox-edit-mode').classList.remove('hidden');
        document.getElementById('label-editors').classList.add('disabled');
        
        // Add event listeners for drag
        const overlay = document.getElementById('modal-labels');
        overlay.classList.add('edit-mode');
        overlay.addEventListener('mousedown', handleBboxMouseDown);
        document.addEventListener('mousemove', handleBboxMouseMove);
        document.addEventListener('mouseup', handleBboxMouseUp);
    }
    
    // Add new object to current objects
    bboxEditorState.currentObjects.push(newObj);
    
    // Select the new bbox
    bboxEditorState.selectedIndex = bboxEditorState.currentObjects.length - 1;
    document.getElementById('bbox-delete-btn').disabled = false;
    document.getElementById('bbox-hint').textContent = 'Drag to move, use handles to resize';
    
    // Re-render bboxes with handles
    renderBboxesEditable();
    
    showNotification(`Added object #${bboxEditorState.currentObjects.length} - drag to position`, 'success');
}

/**
 * Start adding new bbox (enter draw mode) - kept for backwards compatibility
 */
function startAddBbox() {
    bboxEditorState.isDrawingNew = true;
    bboxEditorState.selectedIndex = null;
    
    document.getElementById('bbox-hint').textContent = 'Click and drag on image to draw rectangle';
    document.getElementById('bbox-delete-btn').disabled = true;
    
    const container = document.querySelector('.modal-image-container');
    if (container) container.classList.add('drawing-mode');
}

/**
 * Delete selected bbox
 */
function deleteBbox() {
    const idx = bboxEditorState.selectedIndex;
    if (idx === null) return;
    
    // Remove from array
    bboxEditorState.currentObjects.splice(idx, 1);
    
    // Deselect
    bboxEditorState.selectedIndex = null;
    document.getElementById('bbox-delete-btn').disabled = true;
    
    // Re-render
    renderBboxesEditable();
    
    showNotification(`Deleted object #${idx + 1}`, 'success');
}

/**
 * Save bbox changes to server
 */
async function saveBboxChanges() {
    const seqId = modalState.currentSeqId;
    
    // Convert objects to save format (pixel coordinates only)
    const objectsToSave = bboxEditorState.currentObjects.map(obj => {
        // Ensure rect is in pixel coordinates
        const rect = obj.rect || [
            (obj.rect_percent.x / 100) * bboxEditorState.imgWidth,
            (obj.rect_percent.y / 100) * bboxEditorState.imgHeight,
            (obj.rect_percent.width / 100) * bboxEditorState.imgWidth,
            (obj.rect_percent.height / 100) * bboxEditorState.imgHeight
        ];
        
        return {
            rect: rect.map(v => Math.round(v)),
            color: obj.labels?.color || '',
            brand: obj.labels?.brand || '',
            model: obj.labels?.model || '',
            type: obj.labels?.type || '',
            sub_type: obj.labels?.sub_type || '',
            label: obj.labels?.label || '',
            lp_coords: obj.labels?.lp_coords || null,
            direction: obj.direction || 'front'
        };
    });
    
    try {
        // Determine endpoint based on mode
        let endpoint;
        let body;
        
        if (browseState.isActive && browseState.activePath) {
            // Browse mode
            const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
            if (!card || !card.dataset.fullPath) {
                throw new Error('Could not find image path');
            }
            endpoint = '/api/browse/labels/save';
            body = {
                image_path: card.dataset.fullPath,
                objects: objectsToSave
            };
        } else {
            // Project mode
            endpoint = `/api/labels/${seqId}/objects`;
            body = { objects: objectsToSave };
        }
        
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear cache
            labelCache.delete(seqId);
            
            // Update editPanelState with new data
            editPanelState.labelData = await loadLabels(seqId);
            
            // Exit edit mode
            exitBboxEditMode();
            
            // Re-render edit panel with updated objects
            await renderEditPanel(seqId);
            
            // Re-render grid overlay
            await renderLabels(seqId);
            
            showNotification('Bounding boxes saved', 'success');
        } else {
            showNotification(`Failed to save: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Save bbox error:', error);
        showNotification('Failed to save bounding boxes', 'error');
    }
}

/**
 * Cancel bbox edit - restore original
 */
function cancelBboxEdit() {
    // Restore original objects
    bboxEditorState.currentObjects = JSON.parse(JSON.stringify(bboxEditorState.originalObjects));
    
    // Exit edit mode
    exitBboxEditMode();
    
    showNotification('Changes discarded', 'info');
}

// ============================================
// Placeholder Functions (Future Phases)
// ============================================

function deleteImage(seqId) {
    showNotification('Delete coming in Phase 5', 'info');
}

function openFlagModal(seqId) {
    showNotification('Flags coming in Phase 6', 'info');
}

// ============================================
// Settings (Placeholder for Phase 8)
// ============================================

function openSettings() {
    showNotification('Settings will be implemented in Phase 8', 'info');
}

// ============================================
// Notifications
// ============================================

function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notifications');
    
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${icons[type] || '●'}</span>
        <span class="notification-message">${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    container.appendChild(notification);
    
    // Auto-remove
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
}

// ============================================
// Utility Functions
// ============================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================
// Label Dropdown Functions
// ============================================

function toggleLabelDropdown() {
    const menu = document.getElementById('label-menu');
    menu.classList.toggle('hidden');
}

function toggleLabel(labelName, isVisible) {
    if (isVisible) {
        if (!visibleLabels.includes(labelName)) {
            visibleLabels.push(labelName);
        }
    } else {
        visibleLabels = visibleLabels.filter(l => l !== labelName);
    }
    
    updateLabelCount();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function selectAllLabels() {
    visibleLabels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
    updateLabelCheckboxes();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function clearAllLabels() {
    visibleLabels = [];
    updateLabelCheckboxes();
    refreshAllLabels();
    saveVisibleLabelsSetting();
}

function toggleBoundingBoxes(show) {
    showBoundingBoxes = show;
    refreshAllLabels();
}

function updateLabelCount() {
    const countEl = document.getElementById('label-count');
    if (countEl) {
        countEl.textContent = visibleLabels.length === 0 
            ? 'none' 
            : `${visibleLabels.length} shown`;
    }
}

function updateLabelCheckboxes() {
    document.querySelectorAll('.dropdown-menu input[type="checkbox"]').forEach(cb => {
        cb.checked = visibleLabels.includes(cb.value);
    });
    updateLabelCount();
}

async function saveVisibleLabelsSetting() {
    try {
        await fetch('/api/settings/visible_labels', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ visible_labels: visibleLabels })
        });
    } catch (error) {
        console.error('Failed to save visible labels:', error);
    }
}

// Initialize visible labels from project settings
function initVisibleLabels(settings) {
    if (settings && settings.visible_labels) {
        visibleLabels = [...settings.visible_labels];
    } else {
        visibleLabels = ['color', 'brand', 'model', 'type'];
    }
    updateLabelCheckboxes();
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const dropdown = document.querySelector('.label-dropdown');
    const menu = document.getElementById('label-menu');
    
    if (dropdown && menu && !dropdown.contains(e.target)) {
        menu.classList.add('hidden');
    }
});

// ============================================
// Label Loading & Rendering
// ============================================

// Vehicle color to CSS color mapping
const vehicleColorMap = {
    'white': { bg: 'rgba(255, 255, 255, 0.9)', text: '#000', border: '#fff' },
    'silver': { bg: 'rgba(192, 192, 192, 0.9)', text: '#000', border: '#c0c0c0' },
    'gray': { bg: 'rgba(128, 128, 128, 0.9)', text: '#fff', border: '#808080' },
    'grey': { bg: 'rgba(128, 128, 128, 0.9)', text: '#fff', border: '#808080' },
    'black': { bg: 'rgba(30, 30, 30, 0.9)', text: '#fff', border: '#333' },
    'red': { bg: 'rgba(220, 53, 69, 0.9)', text: '#fff', border: '#dc3545' },
    'blue': { bg: 'rgba(0, 123, 255, 0.9)', text: '#fff', border: '#007bff' },
    'green': { bg: 'rgba(40, 167, 69, 0.9)', text: '#fff', border: '#28a745' },
    'yellow': { bg: 'rgba(255, 193, 7, 0.9)', text: '#000', border: '#ffc107' },
    'orange': { bg: 'rgba(253, 126, 20, 0.9)', text: '#000', border: '#fd7e14' },
    'brown': { bg: 'rgba(139, 69, 19, 0.9)', text: '#fff', border: '#8b4513' },
    'beige': { bg: 'rgba(245, 245, 220, 0.9)', text: '#000', border: '#f5f5dc' },
    'gold': { bg: 'rgba(255, 215, 0, 0.9)', text: '#000', border: '#ffd700' },
    'pink': { bg: 'rgba(255, 105, 180, 0.9)', text: '#000', border: '#ff69b4' },
    'purple': { bg: 'rgba(128, 0, 128, 0.9)', text: '#fff', border: '#800080' },
    'maroon': { bg: 'rgba(128, 0, 0, 0.9)', text: '#fff', border: '#800000' },
    'navy': { bg: 'rgba(0, 0, 128, 0.9)', text: '#fff', border: '#000080' },
    'cyan': { bg: 'rgba(0, 255, 255, 0.9)', text: '#000', border: '#00ffff' },
    'wine': { bg: 'rgba(114, 47, 55, 0.9)', text: '#fff', border: '#722f37' },
    'champagne': { bg: 'rgba(247, 231, 206, 0.9)', text: '#000', border: '#f7e7ce' },
};

function getVehicleColor(colorName) {
    if (!colorName) return null;
    const key = colorName.toLowerCase().trim();
    return vehicleColorMap[key] || null;
}

// Load labels for a single image
async function loadLabels(seqId) {
    // Check cache first
    if (labelCache.has(seqId)) {
        return labelCache.get(seqId);
    }
    
    try {
        let endpoint;
        
        // Browse mode: use full path from card
        if (browseState.isActive) {
            const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
            if (card && card.dataset.fullPath) {
                // Remove leading slash for URL encoding
                const imagePath = card.dataset.fullPath.replace(/^\//, '');
                endpoint = `/api/browse/labels/${imagePath}`;
            } else {
                return null;
            }
        } else {
            // Project mode
            endpoint = `/api/labels/${seqId}`;
        }
        
        const response = await fetch(endpoint);
        const data = await response.json();
        
        if (data.success) {
            labelCache.set(seqId, data.data);
            return data.data;
        }
    } catch (error) {
        console.error(`Failed to load labels for ${seqId}:`, error);
    }
    
    return null;
}

// Render labels on image card
async function renderLabels(seqId) {
    const labelData = await loadLabels(seqId);
    const overlay = document.getElementById(`labels-${seqId}`);
    
    if (!overlay || !labelData || !labelData.has_labels) {
        return;
    }
    
    overlay.innerHTML = '';
    
    if (visibleLabels.length === 0 && !showBoundingBoxes) {
        return;  // Nothing to show
    }
    
    labelData.objects.forEach((obj, idx) => {
        // Get vehicle color for this object
        const vehicleColor = getVehicleColor(obj.labels.color);
        const boxBorderColor = vehicleColor ? vehicleColor.border : 'rgba(74, 105, 189, 0.7)';
        
        // Draw bounding box first (so labels appear on top)
        if (showBoundingBoxes) {
            const bbox = document.createElement('div');
            bbox.className = 'bbox';
            bbox.style.left = `${obj.rect_percent.x}%`;
            bbox.style.top = `${obj.rect_percent.y}%`;
            bbox.style.width = `${obj.rect_percent.width}%`;
            bbox.style.height = `${obj.rect_percent.height}%`;
            bbox.style.borderColor = boxBorderColor;
            
            // Add direction indicator to bounding box
            const direction = obj.direction || 'front';
            const dirIndicator = createDirectionIndicator(seqId, idx, direction);
            bbox.appendChild(dirIndicator);
            
            overlay.appendChild(bbox);
        }
        
        // Skip labels container if no visible labels
        if (visibleLabels.length === 0) return;
        
        // Create labels container at center of bbox
        const labelsDiv = document.createElement('div');
        labelsDiv.className = 'object-labels';
        labelsDiv.style.left = `${obj.center_percent.x}%`;
        labelsDiv.style.top = `${obj.center_percent.y}%`;
        labelsDiv.dataset.objectIndex = idx;
        
        // Apply vehicle color to labels container
        if (vehicleColor) {
            labelsDiv.style.setProperty('--label-bg', vehicleColor.bg);
            labelsDiv.style.setProperty('--label-text', vehicleColor.text);
        }
        
        // Add visible labels
        visibleLabels.forEach(labelName => {
            const value = obj.labels[labelName];
            const labelSpan = document.createElement('span');
            labelSpan.className = 'label-line';
            labelSpan.dataset.labelName = labelName;
            labelSpan.dataset.seqId = seqId;
            labelSpan.dataset.objectIndex = idx;
            
            if (value === null || value === undefined || value === '') {
                labelSpan.textContent = 'NULL';
                labelSpan.classList.add('null');
            } else {
                labelSpan.textContent = value;
            }
            
            // Apply vehicle color styling
            if (vehicleColor) {
                labelSpan.style.background = vehicleColor.bg;
                labelSpan.style.color = vehicleColor.text;
            }
            
            // Click handler for editing (Phase 7)
            labelSpan.onclick = (e) => {
                e.stopPropagation();
                editLabel(seqId, idx, labelName, value);
            };
            
            labelsDiv.appendChild(labelSpan);
        });
        
        overlay.appendChild(labelsDiv);
    });
    
    // Position overlay after rendering labels
    positionGridOverlay(seqId);
}

// Refresh labels on all visible cards
function refreshAllLabels() {
    document.querySelectorAll('.image-card').forEach(card => {
        const seqId = parseInt(card.dataset.seqId);
        renderLabels(seqId);
    });
    // Reposition all overlays after a brief delay to ensure render is complete
    setTimeout(repositionAllOverlays, 100);
}

// Load labels for all images on current page
async function loadPageLabels(images) {
    // Load in parallel
    await Promise.all(images.map(img => renderLabels(img.seq_id)));
}

// ============================================
// Phase 7: Inline Label Editing
// ============================================

// Edit state
const editState = {
    isEditing: false,
    seqId: null,
    objectIndex: null,
    labelName: null,
    originalValue: null,
    inputElement: null
};

// Start editing a label
function editLabel(seqId, objectIndex, labelName, currentValue) {
    // Cancel any existing edit
    if (editState.isEditing) {
        cancelEdit();
    }
    
    editState.isEditing = true;
    editState.seqId = seqId;
    editState.objectIndex = objectIndex;
    editState.labelName = labelName;
    editState.originalValue = currentValue;
    
    // Find the label element
    const labelSpan = document.querySelector(
        `.label-line[data-seq-id="${seqId}"][data-object-index="${objectIndex}"][data-label-name="${labelName}"]`
    );
    
    if (!labelSpan) return;
    
    // Get styling from the label (for vehicle colors)
    const bgColor = labelSpan.style.background || 'rgba(74, 105, 189, 0.9)';
    const textColor = labelSpan.style.color || '#fff';
    
    // Create input element
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'label-input';
    input.value = currentValue || '';
    input.dataset.seqId = seqId;
    input.dataset.objectIndex = objectIndex;
    input.dataset.labelName = labelName;
    input.style.background = bgColor;
    input.style.color = textColor;
    
    // Event handlers
    input.addEventListener('keydown', handleEditKeydown);
    input.addEventListener('blur', handleEditBlur);
    
    // Replace span with input
    labelSpan.replaceWith(input);
    editState.inputElement = input;
    
    // Focus and select
    input.focus();
    input.select();
}

// Handle keyboard during edit
function handleEditKeydown(e) {
    switch (e.key) {
        case 'Enter':
            e.preventDefault();
            saveEdit();
            break;
        
        case 'Escape':
            e.preventDefault();
            cancelEdit();
            break;
        
        case 'Tab':
            e.preventDefault();
            saveEdit();
            moveToNextLabel(e.shiftKey ? -1 : 1);
            break;
    }
    
    // Stop propagation to prevent triggering grid shortcuts
    e.stopPropagation();
}

// Handle blur (click outside)
function handleEditBlur(e) {
    setTimeout(() => {
        if (editState.isEditing && editState.inputElement === e.target) {
            saveEdit();
        }
    }, 100);
}

// Save the edit
async function saveEdit() {
    if (!editState.isEditing) return;
    
    const { seqId, objectIndex, labelName, originalValue, inputElement } = editState;
    const newValue = inputElement.value.trim();
    
    // Don't save if unchanged
    if (newValue === (originalValue || '')) {
        cancelEdit();
        return;
    }
    
    // Get styling for the saving span
    const bgColor = inputElement.style.background;
    const textColor = inputElement.style.color;
    
    // Create placeholder span while saving
    const savingSpan = document.createElement('span');
    savingSpan.className = 'label-line saving';
    savingSpan.textContent = newValue || 'NULL';
    savingSpan.dataset.seqId = seqId;
    savingSpan.dataset.objectIndex = objectIndex;
    savingSpan.dataset.labelName = labelName;
    savingSpan.style.background = bgColor;
    savingSpan.style.color = textColor;
    
    inputElement.replaceWith(savingSpan);
    
    // Reset edit state
    editState.isEditing = false;
    editState.inputElement = null;
    
    try {
        const response = await fetch(`/api/labels/${seqId}/${objectIndex}/${labelName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ value: newValue || null })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update cache
            if (labelCache.has(seqId)) {
                const cached = labelCache.get(seqId);
                if (cached.objects && cached.objects[objectIndex]) {
                    cached.objects[objectIndex].labels[labelName] = newValue || null;
                }
            }
            
            // Show success
            savingSpan.classList.remove('saving');
            savingSpan.classList.add('saved');
            
            // Make it clickable again
            savingSpan.onclick = (e) => {
                e.stopPropagation();
                editLabel(seqId, objectIndex, labelName, newValue);
            };
            
            if (!newValue) {
                savingSpan.classList.add('null');
            }
            
            setTimeout(() => {
                savingSpan.classList.remove('saved');
            }, 500);
            
        } else {
            throw new Error(data.error || 'Save failed');
        }
        
    } catch (error) {
        console.error('Failed to save label:', error);
        
        // Show error state
        savingSpan.classList.remove('saving');
        savingSpan.classList.add('error');
        savingSpan.textContent = originalValue || 'NULL';
        savingSpan.onclick = (e) => {
            e.stopPropagation();
            editLabel(seqId, objectIndex, labelName, originalValue);
        };
        
        showNotification(`Failed to save: ${error.message}`, 'error');
        
        setTimeout(() => {
            savingSpan.classList.remove('error');
        }, 2000);
    }
    
    // Clear remaining state
    editState.seqId = null;
    editState.objectIndex = null;
    editState.labelName = null;
    editState.originalValue = null;
}

// Cancel the edit
function cancelEdit() {
    if (!editState.isEditing) return;
    
    const { seqId, objectIndex, labelName, originalValue, inputElement } = editState;
    
    // Get styling
    const bgColor = inputElement?.style.background;
    const textColor = inputElement?.style.color;
    
    // Create span with original value
    const span = document.createElement('span');
    span.className = 'label-line';
    span.textContent = originalValue || 'NULL';
    span.dataset.seqId = seqId;
    span.dataset.objectIndex = objectIndex;
    span.dataset.labelName = labelName;
    if (bgColor) span.style.background = bgColor;
    if (textColor) span.style.color = textColor;
    span.onclick = (e) => {
        e.stopPropagation();
        editLabel(seqId, objectIndex, labelName, originalValue);
    };
    
    if (!originalValue) {
        span.classList.add('null');
    }
    
    if (inputElement && inputElement.parentNode) {
        inputElement.replaceWith(span);
    }
    
    // Reset state
    editState.isEditing = false;
    editState.seqId = null;
    editState.objectIndex = null;
    editState.labelName = null;
    editState.originalValue = null;
    editState.inputElement = null;
}

// Move to next/previous label (Tab navigation)
function moveToNextLabel(direction = 1) {
    const { seqId, objectIndex, labelName } = editState;
    
    if (!seqId) return;
    
    // Get list of visible labels
    const labelOrder = visibleLabels;
    const currentIdx = labelOrder.indexOf(labelName);
    
    if (currentIdx === -1) return;
    
    // Find next/prev label
    let nextIdx = currentIdx + direction;
    
    if (nextIdx >= 0 && nextIdx < labelOrder.length) {
        const nextLabel = labelOrder[nextIdx];
        const labelData = labelCache.get(seqId);
        const currentValue = labelData?.objects?.[objectIndex]?.labels?.[nextLabel];
        
        editLabel(seqId, objectIndex, nextLabel, currentValue);
    }
}

// ============================================
// Phase 5: Delete Operations
// ============================================

// Delete selected images (entry point)
function deleteSelectedImages() {
    const selected = Array.from(gridState.selectedImages);
    if (selected.length === 0) {
        showNotification('No images selected', 'warning');
        return;
    }
    deleteImages(selected);
}

// Delete single image (from image card button)
function deleteImage(seqId) {
    deleteImages([seqId]);
}

// Main delete handler
function deleteImages(seqIds) {
    if (deleteState.isDeleting) {
        showNotification('Delete in progress...', 'warning');
        return;
    }
    
    deleteState.pendingDelete = seqIds;
    
    // Skip confirmation if enabled
    if (deleteState.skipConfirmation) {
        executeDelete();
        return;
    }
    
    // Show confirmation dialog
    showDeleteConfirmation(seqIds);
}

// Show delete confirmation modal
function showDeleteConfirmation(seqIds) {
    const modal = document.getElementById('delete-modal');
    const fileList = document.getElementById('delete-file-list');
    const title = document.getElementById('delete-modal-title');
    
    // Update title based on count
    const count = seqIds.length;
    title.textContent = count === 1 
        ? 'Delete Image?' 
        : `Delete ${count} Images?`;
    
    // Build file list
    fileList.innerHTML = '';
    const cards = document.querySelectorAll('.image-card');
    seqIds.forEach(seqId => {
        // Find filename from card data
        const card = Array.from(cards).find(c => parseInt(c.dataset.seqId) === seqId);
        let filename = `Image ${seqId}`;
        if (card) {
            filename = card.dataset.filename || filename;
        }
        
        const li = document.createElement('li');
        li.textContent = filename;
        fileList.appendChild(li);
    });
    
    // Limit displayed files for large selections
    if (seqIds.length > 10) {
        fileList.innerHTML = '';
        seqIds.slice(0, 8).forEach(seqId => {
            const card = Array.from(cards).find(c => parseInt(c.dataset.seqId) === seqId);
            const li = document.createElement('li');
            li.textContent = card?.dataset.filename || `Image ${seqId}`;
            fileList.appendChild(li);
        });
        const moreLi = document.createElement('li');
        moreLi.textContent = `... and ${seqIds.length - 8} more`;
        moreLi.style.fontStyle = 'italic';
        fileList.appendChild(moreLi);
    }
    
    // Reset checkbox
    document.getElementById('delete-dont-ask').checked = false;
    
    // Show modal
    modal.classList.remove('hidden');
}

// Close delete modal
function closeDeleteModal() {
    document.getElementById('delete-modal').classList.add('hidden');
    deleteState.pendingDelete = [];
}

// Handle "Don't ask again" checkbox
function toggleSkipDeleteConfirmation(checked) {
    deleteState.skipConfirmation = checked;
}

// Confirm delete (from modal button)
function confirmDelete() {
    // Hide modal but don't clear pendingDelete yet
    document.getElementById('delete-modal').classList.add('hidden');
    executeDelete();
}

// Execute delete operation
async function executeDelete() {
    const seqIds = deleteState.pendingDelete;
    if (seqIds.length === 0) return;
    
    deleteState.isDeleting = true;
    
    try {
        let response;
        
        if (seqIds.length === 1) {
            // Single delete
            response = await fetch(`/api/delete/${seqIds[0]}`, {
                method: 'POST'
            });
        } else {
            // Bulk delete
            response = await fetch('/api/delete/bulk', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ seq_ids: seqIds })
            });
        }
        
        const result = await response.json();
        
        if (result.success) {
            const count = seqIds.length === 1 ? 1 : result.data.deleted_count;
            showNotification(`Deleted ${count} image${count !== 1 ? 's' : ''}`, 'success');
            
            // Update total count
            updateTotalCount(result.data.remaining_count);
            
            // Clear selection
            seqIds.forEach(id => gridState.selectedImages.delete(id));
            updateSelectedCount();
            
            // Reload current page to refill grid
            await loadImages();
        } else {
            showNotification(`Delete failed: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Delete failed: Network error', 'error');
    } finally {
        deleteState.isDeleting = false;
        deleteState.pendingDelete = [];
    }
}

// Update total image count after deletion
function updateTotalCount(newCount) {
    gridState.totalImages = newCount;
    gridState.totalPages = Math.max(1, Math.ceil(newCount / gridState.gridSize));
    
    document.getElementById('total-images').textContent = newCount;
    document.getElementById('total-pages').textContent = gridState.totalPages;
    
    // If current page is now empty or beyond total, go back
    if (gridState.currentPage > gridState.totalPages && gridState.totalPages > 0) {
        gridState.currentPage = gridState.totalPages;
    }
}

// ============================================
// Phase 6: Flags System
// ============================================

// Open flag modal for single image
function openFlagModal(seqId) {
    // Get current flags from the card data or fetch them
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    flagModalState.isOpen = true;
    flagModalState.isBulk = false;
    flagModalState.seqIds = [seqId];
    
    // Parse current flags from card
    const qualityPills = card.querySelectorAll('.flag-pill.flag-quality');
    const perspectivePills = card.querySelectorAll('.flag-pill.flag-perspective');
    
    flagModalState.selectedQualityFlags = new Set();
    flagModalState.selectedPerspectiveFlags = new Set();
    
    // Get available flags from centralized functions
    const qualityFlags = getAvailableQualityFlags();
    const perspectiveFlags = getAvailablePerspectiveFlags();
    
    qualityPills.forEach(pill => {
        const flag = pill.textContent.trim();
        if (qualityFlags.includes(flag)) {
            flagModalState.selectedQualityFlags.add(flag);
        }
    });
    
    perspectivePills.forEach(pill => {
        const flag = pill.textContent.trim();
        if (perspectiveFlags.includes(flag)) {
            flagModalState.selectedPerspectiveFlags.add(flag);
        }
    });
    
    // Update modal UI
    document.getElementById('flag-modal-title').textContent = 'Set Flags';
    document.getElementById('flag-modal-subtitle').textContent = `Image: ${card.dataset.filename || seqId}`;
    document.getElementById('apply-flags-btn').textContent = 'Apply';
    
    // Hide bulk mode selectors
    document.getElementById('quality-bulk-mode').classList.add('hidden');
    document.getElementById('perspective-bulk-mode').classList.add('hidden');
    
    renderFlagCheckboxes();
    document.getElementById('flag-modal').classList.remove('hidden');
}

// Open flag modal for bulk selection
function openBulkFlagModal() {
    const selectedIds = Array.from(gridState.selectedImages);
    if (selectedIds.length === 0) {
        showNotification('No images selected', 'warning');
        return;
    }
    
    flagModalState.isOpen = true;
    flagModalState.isBulk = true;
    flagModalState.seqIds = selectedIds;
    
    // Clear selections for bulk (user chooses what to apply)
    flagModalState.selectedQualityFlags = new Set();
    flagModalState.selectedPerspectiveFlags = new Set();
    
    // Update modal UI
    document.getElementById('flag-modal-title').textContent = 'Set Flags (Bulk)';
    document.getElementById('flag-modal-subtitle').textContent = `Applying to ${selectedIds.length} images`;
    document.getElementById('apply-flags-btn').textContent = 'Apply to All';
    
    // Show bulk mode selectors
    document.getElementById('quality-bulk-mode').classList.remove('hidden');
    document.getElementById('perspective-bulk-mode').classList.remove('hidden');
    
    renderFlagCheckboxes();
    document.getElementById('flag-modal').classList.remove('hidden');
}

// Close flag modal
function closeFlagModal() {
    document.getElementById('flag-modal').classList.add('hidden');
    flagModalState.isOpen = false;
}

// Render flag checkboxes in modal
function renderFlagCheckboxes() {
    // Quality flags - use centralized function
    const qualityFlags = getAvailableQualityFlags();
    const qualityGrid = document.getElementById('quality-flags-grid');
    qualityGrid.innerHTML = '';
    
    qualityFlags.forEach(flag => {
        const isChecked = flagModalState.selectedQualityFlags.has(flag);
        const color = getFlagColor(flag, 'quality');
        
        qualityGrid.innerHTML += `
            <label class="flag-checkbox ${isChecked ? 'checked' : ''}" data-flag="${flag}">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                       onchange="toggleQualityFlag('${flag}', this.checked)">
                <span class="flag-label">${flag}</span>
                <span class="flag-color" style="background: ${color}"></span>
            </label>
        `;
    });
    
    // Perspective flags - use centralized function
    const perspectiveFlags = getAvailablePerspectiveFlags();
    const perspectiveGrid = document.getElementById('perspective-flags-grid');
    perspectiveGrid.innerHTML = '';
    
    perspectiveFlags.forEach(flag => {
        const isChecked = flagModalState.selectedPerspectiveFlags.has(flag);
        const color = getFlagColor(flag, 'perspective');
        
        perspectiveGrid.innerHTML += `
            <label class="flag-checkbox ${isChecked ? 'checked' : ''}" data-flag="${flag}">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                       onchange="togglePerspectiveFlag('${flag}', this.checked)">
                <span class="flag-label">${flag}</span>
                <span class="flag-color" style="background: ${color}"></span>
            </label>
        `;
    });
}

// Toggle quality flag selection
function toggleQualityFlag(flag, isChecked) {
    if (isChecked) {
        flagModalState.selectedQualityFlags.add(flag);
    } else {
        flagModalState.selectedQualityFlags.delete(flag);
    }
    
    // Update visual
    const checkbox = document.querySelector(`#quality-flags-grid .flag-checkbox[data-flag="${flag}"]`);
    checkbox?.classList.toggle('checked', isChecked);
}

// Toggle perspective flag selection
function togglePerspectiveFlag(flag, isChecked) {
    if (isChecked) {
        flagModalState.selectedPerspectiveFlags.add(flag);
    } else {
        flagModalState.selectedPerspectiveFlags.delete(flag);
    }
    
    // Update visual
    const checkbox = document.querySelector(`#perspective-flags-grid .flag-checkbox[data-flag="${flag}"]`);
    checkbox?.classList.toggle('checked', isChecked);
}

// Apply flags
async function applyFlags() {
    const seqIds = flagModalState.seqIds;
    const qualityFlags = Array.from(flagModalState.selectedQualityFlags);
    const perspectiveFlags = Array.from(flagModalState.selectedPerspectiveFlags);
    
    // Browse mode: save to .dataset.json via different endpoint
    if (browseState.isActive && browseState.activePath) {
        try {
            // Get image filename from card for each seqId
            for (const seqId of seqIds) {
                const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
                if (!card) continue;
                
                const filename = card.dataset.filename;
                const imageId = filename.replace(/\.[^/.]+$/, ''); // Remove extension
                
                // Save quality flag
                const qualityFlag = qualityFlags.length > 0 ? qualityFlags[0] : '';
                await fetch('/api/browse/flag', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directory: browseState.activePath,
                        image_id: imageId,
                        flag_name: 'quality_flag',
                        flag_value: qualityFlag
                    })
                });
                
                // Save perspective flag
                const perspectiveFlag = perspectiveFlags.length > 0 ? perspectiveFlags[0] : '';
                await fetch('/api/browse/flag', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directory: browseState.activePath,
                        image_id: imageId,
                        flag_name: 'perspective_flag',
                        flag_value: perspectiveFlag
                    })
                });
                
                // Update UI
                updateCardFlags(seqId, {
                    quality_flags: qualityFlags,
                    perspective_flags: perspectiveFlags
                });
            }
            
            showNotification(`Flags updated for ${seqIds.length} image(s)`, 'success');
            closeFlagModal();
            return;
        } catch (error) {
            console.error('Failed to apply flags (browse mode):', error);
            showNotification('Failed to apply flags', 'error');
            return;
        }
    }
    
    // Original project mode
    let endpoint, body;
    
    if (flagModalState.isBulk) {
        // Get bulk mode
        const qualityMode = document.querySelector('input[name="quality-mode"]:checked')?.value || 'set';
        const perspectiveMode = document.querySelector('input[name="perspective-mode"]:checked')?.value || 'set';
        
        endpoint = '/api/flags/bulk';
        body = {
            seq_ids: seqIds,
            quality_flags: qualityFlags,
            quality_mode: qualityMode,
            perspective_flags: perspectiveFlags,
            perspective_mode: perspectiveMode
        };
    } else {
        endpoint = `/api/image/${seqIds[0]}/flags`;
        body = {
            quality_flags: qualityFlags,
            perspective_flags: perspectiveFlags
        };
    }
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (flagModalState.isBulk) {
                // Update UI for bulk
                Object.entries(data.data.updated_flags || {}).forEach(([seqId, flags]) => {
                    updateCardFlags(parseInt(seqId), flags);
                });
                showNotification(`Flags updated for ${seqIds.length} image(s)`, 'success');
            } else {
                // Update UI for single
                updateCardFlags(seqIds[0], data.data);
                showNotification('Flags updated', 'success');
            }
            
            closeFlagModal();
        } else {
            showNotification(`Failed to update flags: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to apply flags:', error);
        showNotification('Failed to apply flags', 'error');
    }
}

// Update card flags display
function updateCardFlags(seqId, flags) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    const flagsContainer = card.querySelector('.card-flags');
    if (!flagsContainer) return;
    
    flagsContainer.innerHTML = '';
    
    // Quality flags
    (flags.quality_flags || []).forEach(flag => {
        const pill = document.createElement('span');
        pill.className = `flag-pill flag-quality flag-${flag}`;
        pill.textContent = flag;
        flagsContainer.appendChild(pill);
    });
    
    // Perspective flags
    (flags.perspective_flags || []).forEach(flag => {
        const pill = document.createElement('span');
        // Handle underscores in class names
        const flagClass = flag.replace(/_/g, '_');
        pill.className = `flag-pill flag-perspective flag-${flagClass}`;
        pill.textContent = flag;
        flagsContainer.appendChild(pill);
    });
}

// Quick flag cycle (Q key)
function cycleQualityFlag() {
    // Get hovered card or selected images
    const hoveredCard = document.querySelector('.image-card:hover');
    let seqIds = [];
    
    if (hoveredCard) {
        seqIds = [parseInt(hoveredCard.dataset.seqId)];
    } else if (gridState.selectedImages.size > 0) {
        seqIds = Array.from(gridState.selectedImages);
    } else {
        showNotification('Hover over an image or select images to cycle quality flag', 'info');
        return;
    }
    
    // For single image, cycle the flag
    if (seqIds.length === 1) {
        const seqId = seqIds[0];
        const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
        if (!card) return;
        
        // Get current quality flags
        const currentFlags = [];
        card.querySelectorAll('.flag-pill.flag-quality').forEach(pill => {
            currentFlags.push(pill.textContent.trim());
        });
        
        // Use centralized function to get available flags
        const order = getAvailableQualityFlags();
        let nextFlag;
        
        if (currentFlags.length === 0) {
            nextFlag = order[0];
        } else {
            const lastFlag = currentFlags[currentFlags.length - 1];
            const currentIdx = order.indexOf(lastFlag);
            nextFlag = order[(currentIdx + 1) % order.length];
        }
        
        // Quick apply
        applyQuickFlag(seqId, [nextFlag], null);
        showNotification(`Quality flag: ${nextFlag}`, 'success');
    } else {
        // For multiple images, open bulk flag modal
        openBulkFlagModal();
    }
}

// Set quality flag by number key (1-N)
function setQualityFlagByNumber(number) {
    const qualityFlags = getAvailableQualityFlags();
    const flagIndex = number - 1;  // Convert 1-based to 0-based index
    
    if (flagIndex < 0 || flagIndex >= qualityFlags.length) {
        showNotification(`No quality flag #${number} (only ${qualityFlags.length} available)`, 'warning');
        return;
    }
    
    const targetFlag = qualityFlags[flagIndex];
    
    // Get hovered card or selected images
    const hoveredCard = document.querySelector('.image-card:hover');
    let seqIds = [];
    
    if (hoveredCard) {
        seqIds = [parseInt(hoveredCard.dataset.seqId)];
    } else if (gridState.selectedImages.size > 0) {
        seqIds = Array.from(gridState.selectedImages);
    }
    
    if (seqIds.length === 0) {
        return;
    }
    
    // Apply to all target images
    seqIds.forEach(seqId => {
        applyQuickFlag(seqId, [targetFlag], null);
    });
    
    const count = seqIds.length;
    showNotification(`Set "${targetFlag}" on ${count} image${count > 1 ? 's' : ''}`, 'success');
}

// Quick apply flag (without modal)
async function applyQuickFlag(seqId, qualityFlags, perspectiveFlags) {
    try {
        // Check if browse mode is active
        if (browseState.isActive && browseState.activePath) {
            // Browse mode: use browse flag endpoint
            const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
            if (!card) return;
            
            // Get image filename from card
            const filename = card.dataset.filename;
            const imageId = filename.replace(/\.[^/.]+$/, '');  // Remove extension
            
            // Apply quality flag
            if (qualityFlags !== null && qualityFlags.length > 0) {
                await fetch('/api/browse/flag', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directory: browseState.activePath,
                        image_id: imageId,
                        flag_name: 'quality_flag',
                        flag_value: qualityFlags[0]  // Take first flag
                    })
                });
            }
            
            // Apply perspective flag
            if (perspectiveFlags !== null && perspectiveFlags.length > 0) {
                await fetch('/api/browse/flag', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        directory: browseState.activePath,
                        image_id: imageId,
                        flag_name: 'perspective_flag',
                        flag_value: perspectiveFlags[0]  // Take first flag
                    })
                });
            }
            
            // Update card display
            updateCardFlagsBrowse(seqId, qualityFlags, perspectiveFlags);
        } else {
            // Project mode: use project flags endpoint
            const body = {};
            if (qualityFlags !== null) body.quality_flags = qualityFlags;
            if (perspectiveFlags !== null) body.perspective_flags = perspectiveFlags;
            
            const response = await fetch(`/api/image/${seqId}/flags`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            
            const data = await response.json();
            
            if (data.success) {
                updateCardFlags(seqId, data.data);
            }
        }
    } catch (error) {
        console.error('Quick flag failed:', error);
    }
}

// Update card flags display for browse mode
function updateCardFlagsBrowse(seqId, qualityFlags, perspectiveFlags) {
    const card = document.querySelector(`.image-card[data-seq-id="${seqId}"]`);
    if (!card) return;
    
    const flagsContainer = card.querySelector('.card-flags');
    if (!flagsContainer) return;
    
    // Clear existing flags
    flagsContainer.innerHTML = '';
    
    // Add quality flags
    if (qualityFlags && qualityFlags.length > 0) {
        qualityFlags.forEach(flag => {
            const color = FLAG_CONFIG.quality.colors[flag] || '#3498db';
            flagsContainer.innerHTML += `<span class="flag-pill flag-quality" style="background:${color}">${flag}</span>`;
        });
    }
    
    // Add perspective flags
    if (perspectiveFlags && perspectiveFlags.length > 0) {
        perspectiveFlags.forEach(flag => {
            const color = FLAG_CONFIG.perspective.colors[flag] || '#27ae60';
            flagsContainer.innerHTML += `<span class="flag-pill flag-perspective" style="background:${color}">${flag}</span>`;
        });
    }
}

// ============================================
// Shortcuts Help Modal
// ============================================

function toggleShortcutsHelp() {
    const modal = document.getElementById('shortcuts-modal');
    if (!modal) return;
    
    if (modal.classList.contains('hidden')) {
        openShortcutsHelp();
    } else {
        closeShortcutsHelp();
    }
}

function openShortcutsHelp() {
    document.getElementById('shortcuts-modal').classList.remove('hidden');
}

function closeShortcutsHelp() {
    document.getElementById('shortcuts-modal').classList.add('hidden');
}

// Quick perspective flag (P key)
function openPerspectiveFlagQuick() {
    // Get hovered card or selected cards
    if (gridState.selectedImages.size > 0) {
        openBulkFlagModal();
    } else {
        const hoveredCard = document.querySelector('.image-card:hover');
        if (hoveredCard) {
            openFlagModal(parseInt(hoveredCard.dataset.seqId));
        }
    }
}

// ============================================
// Loading Overlay
// ============================================

function showLoadingOverlay(text = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.querySelector('.loading-text').textContent = text;
        overlay.classList.remove('hidden');
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

// Skeleton loader for grid
function showGridSkeleton() {
    const grid = document.getElementById('image-grid');
    const count = gridState.gridSize;
    
    grid.innerHTML = Array(count).fill('').map(() => `
        <div class="skeleton-card">
            <div class="skeleton-image"></div>
        </div>
    `).join('');
}

// ============================================
// Global Error Handlers
// ============================================

window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    showNotification('An unexpected error occurred', 'error');
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    // Don't show notification for every network error - let specific handlers do it
});

// ============================================
// Memory Cleanup
// ============================================

function cleanupMemory() {
    // Keep labelCache from growing too large
    if (labelCache.size > 200) {
        const keysToDelete = Array.from(labelCache.keys()).slice(0, 100);
        keysToDelete.forEach(k => labelCache.delete(k));
    }
}

// ============================================
// Phase 8: Settings Panel
// ============================================

// Open settings modal
function openSettings() {
    populateSettingsModal();
    document.getElementById('settings-modal').classList.remove('hidden');
}

// Close settings modal
function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

// Populate settings modal with current values
function populateSettingsModal() {
    if (!projectData) return;
    
    const settings = projectData.settings || {};
    
    // Project info
    document.getElementById('settings-project-name').textContent = projectData.project_name || '-';
    document.getElementById('settings-project-dir').textContent = truncatePath(projectData.directory || '-');
    
    const totalImages = projectData.images?.length || 0;
    const deletedImages = projectData.images?.filter(img => img.deleted).length || 0;
    document.getElementById('settings-image-count').textContent = 
        `${totalImages - deletedImages} total (${deletedImages} deleted)`;
    
    document.getElementById('settings-created-date').textContent = 
        formatDate(projectData.created);
    
    // General settings
    document.getElementById('setting-skip-confirm').checked = settings.skip_delete_confirmation || false;
    
    document.querySelectorAll('input[name="setting-grid-size"]').forEach(radio => {
        radio.checked = parseInt(radio.value) === (settings.grid_size || 9);
    });
    
    // Visible labels
    renderVisibleLabelsSettings();
    
    // Quality flags
    renderQualityFlagsSettings();
    
    // Perspective flags
    renderPerspectiveFlagsSettings();
}

// Truncate long paths
function truncatePath(path, maxLength = 45) {
    if (!path || path.length <= maxLength) return path;
    
    const parts = path.split('/');
    const filename = parts.pop();
    
    if (filename.length >= maxLength - 3) {
        return '...' + filename.slice(-(maxLength - 3));
    }
    
    let result = filename;
    for (let i = parts.length - 1; i >= 0; i--) {
        const test = parts[i] + '/' + result;
        if (test.length > maxLength - 4) break;
        result = test;
    }
    
    return '.../' + result;
}

// Format date for display
function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Render visible labels checkboxes
function renderVisibleLabelsSettings() {
    const container = document.getElementById('visible-labels-settings');
    const allLabels = ['color', 'brand', 'model', 'label', 'type', 'sub_type', 'lp_coords'];
    const visible = projectData?.settings?.visible_labels || visibleLabels;
    
    container.innerHTML = allLabels.map(label => `
        <label>
            <input type="checkbox" 
                   ${visible.includes(label) ? 'checked' : ''}
                   onchange="toggleVisibleLabelSetting('${label}', this.checked)">
            ${label}
        </label>
    `).join('');
}

// Toggle visible label in settings
function toggleVisibleLabelSetting(label, isVisible) {
    let visible = projectData?.settings?.visible_labels || [...visibleLabels];
    
    if (isVisible && !visible.includes(label)) {
        visible.push(label);
    } else if (!isVisible) {
        visible = visible.filter(l => l !== label);
    }
    
    updateSetting('visible_labels', visible);
    
    // Update main app
    visibleLabels = visible;
    updateLabelCheckboxes();
    refreshAllLabels();
}

// Render quality flags settings
function renderQualityFlagsSettings() {
    const container = document.getElementById('quality-flags-tags');
    const flags = getAvailableQualityFlags();
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag" style="background: ${getFlagColor(flag, 'quality')}">
            ${flag}
            <button class="remove-flag" onclick="removeQualityFlag('${flag}')" title="Remove">✕</button>
        </span>
    `).join('');
    
    // Update default dropdown
    const select = document.getElementById('default-quality-flag');
    const defaultFlag = projectData?.settings?.default_quality_flag || '';
    select.innerHTML = '<option value="">None</option>' + 
        flags.map(flag => `
            <option value="${flag}" ${defaultFlag === flag ? 'selected' : ''}>
                ${flag}
            </option>
        `).join('');
}

// Render perspective flags settings
function renderPerspectiveFlagsSettings() {
    const container = document.getElementById('perspective-flags-tags');
    const flags = getAvailablePerspectiveFlags();
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag" style="background: ${getFlagColor(flag, 'perspective')}">
            ${flag}
            <button class="remove-flag" onclick="removePerspectiveFlag('${flag}')" title="Remove">✕</button>
        </span>
    `).join('');
    
    // Update default dropdown
    const select = document.getElementById('default-perspective-flag');
    const defaultFlag = projectData?.settings?.default_perspective_flag || '';
    select.innerHTML = '<option value="">None</option>' + 
        flags.map(flag => `
            <option value="${flag}" ${defaultFlag === flag ? 'selected' : ''}>
                ${flag}
            </option>
        `).join('');
}

// Add quality flag
function addQualityFlag() {
    const input = document.getElementById('new-quality-flag');
    const flagName = input.value.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!flagName) return;
    
    const flags = getAvailableQualityFlags().slice(); // Copy array
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('quality_flags', flags);
    
    input.value = '';
    renderQualityFlagsSettings();
    
    // Refresh all flag-dependent UI
    refreshFlagDependentUI();
}

// Remove quality flag
function removeQualityFlag(flag) {
    const flags = getAvailableQualityFlags().slice(); // Copy array
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('quality_flags', newFlags);
    
    // Clear default if removed
    if (projectData?.settings?.default_quality_flag === flag) {
        updateSetting('default_quality_flag', null);
    }
    
    renderQualityFlagsSettings();
    
    // Refresh all flag-dependent UI
    refreshFlagDependentUI();
}

// Add perspective flag
function addPerspectiveFlag() {
    const input = document.getElementById('new-perspective-flag');
    const flagName = input.value.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!flagName) return;
    
    const flags = getAvailablePerspectiveFlags().slice(); // Copy array
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('perspective_flags', flags);
    
    input.value = '';
    renderPerspectiveFlagsSettings();
    
    // Refresh all flag-dependent UI
    refreshFlagDependentUI();
}

// Remove perspective flag
function removePerspectiveFlag(flag) {
    const flags = getAvailablePerspectiveFlags().slice(); // Copy array
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('perspective_flags', newFlags);
    
    if (projectData?.settings?.default_perspective_flag === flag) {
        updateSetting('default_perspective_flag', null);
    }
    
    renderPerspectiveFlagsSettings();
    
    // Refresh all flag-dependent UI
    refreshFlagDependentUI();
}

// Update a single setting
async function updateSetting(key, value) {
    // Update local state
    if (!projectData.settings) {
        projectData.settings = {};
    }
    projectData.settings[key] = value;
    
    // Apply skip_delete_confirmation to deleteState
    if (key === 'skip_delete_confirmation') {
        deleteState.skipConfirmation = value;
    }
    
    // Apply grid_size
    if (key === 'grid_size') {
        setGridSize(value);
    }
    
    // Debounced save to server
    debouncedSaveSettings();
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Debounced settings save
const debouncedSaveSettings = debounce(async () => {
    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData.settings)
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showNotification('Failed to save settings', 'error');
        }
    } catch (error) {
        console.error('Failed to save settings:', error);
        showNotification('Failed to save settings', 'error');
    }
}, 500);

// Handle default flag change with confirmation
async function onDefaultFlagChange(type, newValue) {
    const settingKey = type === 'quality' ? 'default_quality_flag' : 'default_perspective_flag';
    const flagType = type === 'quality' ? 'quality_flags' : 'perspective_flags';
    const displayType = type === 'quality' ? 'Quality' : 'Perspective';
    
    // Update the setting
    updateSetting(settingKey, newValue || null);
    
    // If a value is selected (not "None"), ask to apply to all
    if (newValue) {
        const totalImages = projectData.images?.filter(img => !img.deleted).length || 0;
        
        const confirmed = confirm(
            `Apply "${newValue}" as the ${displayType} flag to ALL ${totalImages} images?\n\n` +
            `This will REMOVE all existing ${displayType.toLowerCase()} flags and set only "${newValue}" on every image.\n\n` +
            `This action cannot be undone.`
        );
        
        if (confirmed) {
            await applyDefaultFlagToAll(type, newValue);
        }
    }
}

// Apply default flag to all images
async function applyDefaultFlagToAll(type, flag) {
    try {
        showNotification(`Applying "${flag}" to all images...`, 'info');
        
        const response = await fetch('/api/flags/apply-to-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: type,
                flag: flag
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Applied "${flag}" to ${data.data.updated_count} images`, 'success');
            
            // Reload current page to reflect changes
            await loadImages();
        } else {
            showNotification(`Failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Failed to apply flag to all:', error);
        showNotification('Failed to apply flag to all images', 'error');
    }
}

// ============================================
// Phase 11: Vehicle Direction Flag
// ============================================

/**
 * Toggle the direction (front/back) of a vehicle
 * @param {Event} event - Click event
 * @param {number} seqId - Image sequence ID
 * @param {number} vehicleIdx - Vehicle index within the image
 */
async function toggleDirection(event, seqId, vehicleIdx) {
    event.stopPropagation();
    event.preventDefault();
    
    const indicator = event.target.closest('.direction-indicator');
    if (!indicator || indicator.classList.contains('saving')) return;
    
    const currentDirection = indicator.classList.contains('front') ? 'front' : 'back';
    const newDirection = currentDirection === 'front' ? 'back' : 'front';
    
    // Optimistic UI update
    indicator.classList.remove(currentDirection);
    indicator.classList.add(newDirection, 'toggling');
    indicator.innerHTML = newDirection === 'front' ? '▼' : '▲';
    indicator.title = newDirection === 'front' ? 'Front (coming) - Click to toggle' : 'Back (going) - Click to toggle';
    
    // Remove animation class after animation completes
    setTimeout(() => indicator.classList.remove('toggling'), 300);
    
    // Mark as saving
    indicator.classList.add('saving');
    
    try {
        // Build request body - include directory in browse mode
        const body = { direction: newDirection };
        if (browseState.isActive && browseState.activePath) {
            body.directory = browseState.activePath;
        }
        
        const response = await fetch(`/api/vehicle/${seqId}/${vehicleIdx}/direction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to save');
        }
        
        // Update label cache
        if (labelCache.has(seqId)) {
            const cached = labelCache.get(seqId);
            if (cached.objects && cached.objects[vehicleIdx]) {
                cached.objects[vehicleIdx].direction = newDirection;
            }
        }
        
        showNotification(`Direction: ${newDirection}`, 'success');
    } catch (error) {
        // Revert on failure
        indicator.classList.remove(newDirection);
        indicator.classList.add(currentDirection);
        indicator.innerHTML = currentDirection === 'front' ? '▼' : '▲';
        indicator.title = currentDirection === 'front' ? 'Front (coming) - Click to toggle' : 'Back (going) - Click to toggle';
        showNotification('Failed to update direction', 'error');
        console.error('Direction toggle error:', error);
    } finally {
        indicator.classList.remove('saving');
    }
}

/**
 * Create a direction indicator element
 * @param {number} seqId - Image sequence ID
 * @param {number} vehicleIdx - Vehicle index
 * @param {string} direction - Current direction ('front' or 'back')
 * @returns {HTMLElement} Direction indicator element
 */
function createDirectionIndicator(seqId, vehicleIdx, direction) {
    const indicator = document.createElement('div');
    indicator.className = `direction-indicator ${direction}`;
    indicator.innerHTML = direction === 'front' ? '▼' : '▲';
    indicator.title = direction === 'front' ? 'Front (coming) - Click to toggle' : 'Back (going) - Click to toggle';
    indicator.addEventListener('click', (e) => toggleDirection(e, seqId, vehicleIdx));
    return indicator;
}

/**
 * Set direction for all vehicles (in selected images or all images)
 * @param {string} direction - 'front' or 'back'
 */
async function setAllDirection(direction) {
    if (direction !== 'front' && direction !== 'back') {
        showNotification('Invalid direction', 'error');
        return;
    }
    
    // Check if there are selected images
    const selectedIds = Array.from(gridState.selectedImages);
    const hasSelection = selectedIds.length > 0;
    
    // Confirm action
    const targetDesc = hasSelection 
        ? `${selectedIds.length} selected image(s)` 
        : 'ALL images';
    
    const confirmed = confirm(
        `Set all vehicles to "${direction}" in ${targetDesc}?\n\n` +
        `This will update the direction flag for every vehicle.`
    );
    
    if (!confirmed) return;
    
    try {
        showNotification(`Setting direction to ${direction}...`, 'info');
        
        const response = await fetch('/api/direction/apply-to-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                direction: direction,
                seq_ids: hasSelection ? selectedIds : null
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to apply direction');
        }
        
        // Clear label cache to force refresh
        labelCache.clear();
        
        // Refresh displayed images
        refreshAllLabels();
        
        showNotification(result.message, 'success');
    } catch (error) {
        console.error('Failed to set direction:', error);
        showNotification('Failed to set direction', 'error');
    }
}

// ============================================
// Phase 10: Filter Panel
// ============================================

function initFilterPanel() {
    // Set up filter toggle button
    const toggleBtn = document.getElementById('filter-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleFilterPanel);
    }
    
    // Panel collapse button inside the panel
    const collapseBtn = document.querySelector('.filter-collapse-btn');
    if (collapseBtn) {
        // Already has onclick in HTML
    }
    
    // Set initial state - panel starts open
    const panel = document.getElementById('filter-panel');
    if (panel && !panel.classList.contains('collapsed')) {
        filterState.isOpen = true;
    }
    
    console.log('✓ Filter panel initialized');
}

// Load filter options when project is loaded
async function loadFilterOptionsForProject() {
    await loadFilterOptions();
    // Count is updated inside loadFilterOptions from API response
}

function toggleFilterPanel() {
    const panel = document.getElementById('filter-panel');
    const toggleBtn = document.getElementById('filter-toggle-btn');
    
    if (!panel) return;
    
    filterState.isOpen = !filterState.isOpen;
    panel.classList.toggle('collapsed', !filterState.isOpen);
    
    if (toggleBtn) {
        toggleBtn.classList.toggle('active', filterState.isOpen);
        toggleBtn.title = filterState.isOpen ? 'Hide Filters' : 'Show Filters';
    }
    
    // Load filter options on first open
    if (filterState.isOpen && !filterState.options) {
        loadFilterOptions();
    }
}

async function loadFilterOptions() {
    try {
        const response = await fetch('/api/filter/options');
        const data = await response.json();
        
        if (data.success) {
            filterState.options = data.data;
            renderFilterSections();
            updateFilterMatchCount(data.data.total_images);
        } else {
            console.error('Failed to load filter options:', data.error);
        }
    } catch (error) {
        console.error('Error loading filter options:', error);
    }
}

function updateFilterMatchCount(count) {
    const countEl = document.getElementById('filter-match-count');
    if (countEl) {
        countEl.textContent = `${count || 0} images`;
    }
    
    // Update clear button disabled state
    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) {
        const hasActiveFilters = Object.values(filterState.selected).some(set => set.size > 0);
        clearBtn.disabled = !hasActiveFilters;
    }
}

// Escape string for safe use in HTML attributes that contain JS strings
function escapeForJsString(str) {
    return String(str)
        .replace(/\\/g, '\\\\')  // Backslash first
        .replace(/'/g, "\\'")    // Single quotes for JS strings
        .replace(/"/g, '&quot;') // Double quotes for HTML attributes
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

// Escape for display in HTML (text content)
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function renderFilterSections() {
    const container = document.getElementById('filter-sections');
    if (!container || !filterState.options) return;
    
    container.innerHTML = '';
    
    const sections = [
        { key: 'quality_flags', title: 'Quality Flags', icon: '🏷️' },
        { key: 'perspective_flags', title: 'Perspective', icon: '📐' },
        { key: 'direction', title: 'Direction', icon: '↕️' },
        { key: 'label', title: 'Label', icon: '🏷️' },
        { key: 'color', title: 'Color', icon: '🎨' },
        { key: 'brand', title: 'Brand', icon: '🏢' },
        { key: 'model', title: 'Model', icon: '🚗' },
        { key: 'type', title: 'Type', icon: '📋' },
        { key: 'sub_type', title: 'Sub-Type', icon: '📝' }
    ];
    
    sections.forEach(section => {
        const options = filterState.options[section.key] || [];
        if (options.length === 0) return;
        
        const sectionEl = document.createElement('div');
        sectionEl.className = 'filter-section';
        sectionEl.dataset.filterKey = section.key;
        
        const selectedCount = filterState.selected[section.key]?.size || 0;
        
        sectionEl.innerHTML = `
            <div class="filter-section-header" onclick="toggleFilterSection(this)">
                <span class="section-icon">${section.icon}</span>
                <span class="section-title">${section.title}</span>
                ${selectedCount > 0 ? `<span class="section-count">${selectedCount}</span>` : ''}
                <span class="section-chevron">▼</span>
            </div>
            <div class="filter-section-content">
                ${options.map(opt => {
                    const jsEscaped = escapeForJsString(opt.value);
                    const htmlEscaped = escapeHtml(opt.value);
                    return `
                    <label class="filter-option" data-value="${htmlEscaped}">
                        <input type="checkbox" class="option-checkbox"
                               ${filterState.selected[section.key]?.has(opt.value) ? 'checked' : ''}
                               onchange="handleFilterChange('${section.key}', '${jsEscaped}', this.checked)">
                        <span class="option-label">${htmlEscaped}</span>
                        <span class="option-count">${opt.count}</span>
                    </label>
                    `;
                }).join('')}
            </div>
        `;
        
        container.appendChild(sectionEl);
    });
}

function toggleFilterSection(header) {
    const section = header.closest('.filter-section');
    if (section) {
        section.classList.toggle('collapsed');
    }
}

function handleFilterChange(category, value, isChecked) {
    if (!filterState.selected[category]) {
        filterState.selected[category] = new Set();
    }
    
    if (isChecked) {
        filterState.selected[category].add(value);
    } else {
        filterState.selected[category].delete(value);
    }
    
    updateActiveFiltersBar();
    updateSectionCounts();
    
    // Update clear button state
    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) {
        const hasActiveFilters = Object.values(filterState.selected).some(set => set.size > 0);
        clearBtn.disabled = !hasActiveFilters;
    }
    
    // Reset to page 1 and reload
    gridState.currentPage = 1;
    loadImages();
}

function updateSectionCounts() {
    document.querySelectorAll('.filter-section').forEach(section => {
        const key = section.dataset.filterKey;
        const count = filterState.selected[key]?.size || 0;
        const header = section.querySelector('.filter-section-header');
        
        // Remove existing count badge
        const existingBadge = header.querySelector('.section-count');
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Add new count badge if > 0
        if (count > 0) {
            const chevron = header.querySelector('.section-chevron');
            const badge = document.createElement('span');
            badge.className = 'section-count';
            badge.textContent = count;
            chevron.before(badge);
        }
    });
}

function updateActiveFiltersBar() {
    const bar = document.querySelector('.active-filters-bar');
    const countEl = document.getElementById('active-filter-count');
    const chipsContainer = document.querySelector('.filter-chips');
    
    if (!bar || !chipsContainer) return;
    
    // Collect all active filters
    const allFilters = [];
    for (const [category, values] of Object.entries(filterState.selected)) {
        for (const value of values) {
            allFilters.push({ category, value });
        }
    }
    
    // Update count
    if (countEl) {
        countEl.textContent = allFilters.length;
    }
    
    // Show/hide bar
    bar.classList.toggle('hidden', allFilters.length === 0);
    
    // Render chips
    chipsContainer.innerHTML = allFilters.map(f => {
        const jsEscaped = escapeForJsString(f.value);
        const htmlEscaped = escapeHtml(f.value);
        return `
        <span class="filter-chip" data-category="${f.category}" data-value="${htmlEscaped}">
            ${htmlEscaped}
            <button class="chip-remove" onclick="removeFilter('${f.category}', '${jsEscaped}')" title="Remove filter">×</button>
        </span>
        `;
    }).join('');
}

function removeFilter(category, value) {
    if (filterState.selected[category]) {
        filterState.selected[category].delete(value);
    }
    
    // Update checkbox if visible - need to use escaped value for attribute selector
    const escapedValue = escapeHtml(value);
    const checkbox = document.querySelector(
        `.filter-section[data-filter-key="${category}"] .filter-option[data-value="${escapedValue}"] input`
    );
    if (checkbox) {
        checkbox.checked = false;
    }
    
    // Update clear button state
    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) {
        const hasActiveFilters = Object.values(filterState.selected).some(set => set.size > 0);
        clearBtn.disabled = !hasActiveFilters;
    }
    
    updateActiveFiltersBar();
    updateSectionCounts();
    
    gridState.currentPage = 1;
    loadImages();
}

function clearAllFilters() {
    // Clear all selected filters
    for (const category of Object.keys(filterState.selected)) {
        filterState.selected[category].clear();
    }
    
    // Uncheck all checkboxes
    document.querySelectorAll('.filter-section input[type="checkbox"]').forEach(cb => {
        cb.checked = false;
    });
    
    // Disable clear button
    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) {
        clearBtn.disabled = true;
    }
    
    updateActiveFiltersBar();
    updateSectionCounts();
    
    gridState.currentPage = 1;
    loadImages();
    
    showNotification('All filters cleared', 'info');
}

function buildFilterParams() {
    const params = [];
    
    for (const [category, values] of Object.entries(filterState.selected)) {
        for (const value of values) {
            params.push(`filter_${category}=${encodeURIComponent(value)}`);
        }
    }
    
    return params.length > 0 ? '&' + params.join('&') : '';
}

function filterSearchOptions(query) {
    const searchTerm = (query || '').toLowerCase().trim();
    
    document.querySelectorAll('.filter-option').forEach(option => {
        const label = option.querySelector('.option-label');
        if (label) {
            const text = label.textContent.toLowerCase();
            option.style.display = text.includes(searchTerm) ? '' : 'none';
        }
    });
    
    // Hide empty sections
    document.querySelectorAll('.filter-section').forEach(section => {
        const visibleOptions = section.querySelectorAll('.filter-option:not([style*="display: none"])');
        section.style.display = visibleOptions.length > 0 ? '' : 'none';
    });
}

// Debounce helper for filter search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Refresh filter options (call after flag changes)
async function refreshFilterOptions() {
    if (filterState.options) {
        await loadFilterOptions();
    }
}

// ============================================
// Directory Browsing (Phase 2.0)
// ============================================

/**
 * Switch between sidebar tabs (Filters / Directories)
 */
function switchSidebarTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.sidebar-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    // Update tab content
    document.querySelectorAll('.sidebar-tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });
    
    // Load directory tree if switching to directories tab for first time
    if (tabName === 'directories') {
        const tree = document.getElementById('directory-tree');
        if (tree && !tree.hasChildNodes()) {
            loadDirectoryTree();
        }
    }
}

/**
 * Load directory tree from base path
 */
async function loadDirectoryTree() {
    const container = document.getElementById('directory-tree');
    if (!container) return;
    
    container.innerHTML = '<div class="dir-loading">Loading...</div>';
    
    try {
        // Pass expanded paths to backend so it returns deeper levels
        const expandedPaths = Array.from(browseState.expandedNodes).join(',');
        const response = await fetch(
            `/api/browse/tree?path=${encodeURIComponent(browseState.basePath)}&depth=2&expanded=${encodeURIComponent(expandedPaths)}`
        );
        const result = await response.json();
        
        if (result.success) {
            container.innerHTML = '';
            renderDirectoryNode(result.data, container, 0);
        } else {
            container.innerHTML = `<div class="dir-loading">Error: ${result.error}</div>`;
        }
    } catch (error) {
        console.error('Failed to load directory tree:', error);
        container.innerHTML = '<div class="dir-loading">Failed to load</div>';
    }
}

/**
 * Render a directory node and its children
 */
function renderDirectoryNode(node, container, depth) {
    // has_children from backend indicates if subdirs exist, children array may be empty until expanded
    const hasChildren = node.has_children || (node.children && node.children.length > 0);
    const isExpanded = browseState.expandedNodes.has(node.path) || depth < 1;
    const isSelected = browseState.selectedPath === node.path;
    
    const div = document.createElement('div');
    div.className = 'dir-node' + (isSelected ? ' selected' : '');
    div.style.paddingLeft = `${12 + depth * 16}px`;
    div.dataset.path = node.path;
    
    // Expand arrow
    const arrow = document.createElement('span');
    arrow.className = 'dir-expand';
    arrow.textContent = hasChildren ? (isExpanded ? '▼' : '▶') : '';
    arrow.onclick = (e) => {
        e.stopPropagation();
        if (hasChildren) {
            toggleDirectoryNode(node.path);
        }
    };
    div.appendChild(arrow);
    
    // Folder icon
    const icon = document.createElement('span');
    icon.className = 'dir-icon';
    icon.textContent = isExpanded && hasChildren ? '📂' : '📁';
    div.appendChild(icon);
    
    // Name
    const name = document.createElement('span');
    name.className = 'dir-name';
    name.textContent = node.name;
    div.appendChild(name);
    
    // Click to select
    div.onclick = () => selectDirectoryNode(node.path);
    
    // Double click to expand and select
    div.ondblclick = () => {
        if (hasChildren) {
            browseState.expandedNodes.add(node.path);
        }
        selectDirectoryNode(node.path);
        activateDirectory();
    };
    
    container.appendChild(div);
    
    // Render children if expanded
    if (hasChildren && isExpanded) {
        const childContainer = document.createElement('div');
        childContainer.className = 'dir-children';
        node.children.forEach(child => {
            renderDirectoryNode(child, childContainer, depth + 1);
        });
        container.appendChild(childContainer);
    }
}

/**
 * Toggle expand/collapse of a directory node
 */
async function toggleDirectoryNode(path) {
    if (browseState.expandedNodes.has(path)) {
        browseState.expandedNodes.delete(path);
    } else {
        browseState.expandedNodes.add(path);
        // Load children if needed
        await loadDirectoryChildren(path);
    }
    // Re-render tree
    loadDirectoryTree();
}

/**
 * Load children of a directory (lazy loading)
 * Now just triggers a tree reload - the expanded paths are sent to backend
 */
async function loadDirectoryChildren(path) {
    // Children are now loaded via tree endpoint with expanded paths
    // This function is kept for compatibility but doesn't need to do anything
    // The tree reload in toggleDirectoryNode will include the expanded path
}

/**
 * Select a directory node
 */
function selectDirectoryNode(path) {
    browseState.selectedPath = path;
    
    // Update visual selection
    document.querySelectorAll('.dir-node').forEach(node => {
        node.classList.toggle('selected', node.dataset.path === path);
    });
    
    // Enable activate button
    const activateBtn = document.getElementById('btn-activate');
    if (activateBtn) {
        activateBtn.disabled = false;
    }
}

/**
 * Activate selected directory as dataset
 */
async function activateDirectory() {
    const path = browseState.selectedPath;
    if (!path) {
        showNotification('Please select a directory first', 'warning');
        return;
    }
    
    try {
        // Collect current app settings to save to dataset
        const currentSettings = {
            visible_labels: visibleLabels,
            quality_flags: getAvailableQualityFlags(),
            perspective_flags: getAvailablePerspectiveFlags(),
            skip_delete_confirmation: projectData?.settings?.skip_delete_confirmation || false
        };
        
        // Call activate endpoint with settings
        const response = await fetch('/api/browse/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path, settings: currentSettings })
        });
        const result = await response.json();
        
        if (!result.success) {
            showNotification(result.error || 'Failed to activate', 'error');
            return;
        }
        
        // Set as active
        browseState.isActive = true;
        browseState.activePath = path;
        
        // Load settings from dataset (if they exist)
        if (result.data.settings) {
            const ds = result.data.settings;
            if (ds.visible_labels) visibleLabels = ds.visible_labels;
            if (ds.quality_flags) {
                // Store quality flags from dataset
                if (!projectData) projectData = { settings: {} };
                if (!projectData.settings) projectData.settings = {};
                projectData.settings.quality_flags = ds.quality_flags;
            }
            if (ds.perspective_flags) {
                if (!projectData) projectData = { settings: {} };
                if (!projectData.settings) projectData.settings = {};
                projectData.settings.perspective_flags = ds.perspective_flags;
            }
            browseState.metadata = ds;
        }
        
        // Update UI
        updateDirectoryInfo();
        
        // Clear project title (we're in directory mode now)
        currentProject = null;
        document.getElementById('project-title').textContent = '';
        
        // Load filter options for this directory
        await loadBrowseFilterOptions();
        
        // Load images using existing function
        loadImages();
        
        // Update metadata panel
        updateMetadataPanel();
        
        showNotification(`Loaded ${result.data.image_count} images from directory`, 'success');
        
    } catch (error) {
        console.error('Failed to activate directory:', error);
        showNotification('Failed to activate directory', 'error');
    }
}

/**
 * Update directory info in header
 */
function updateDirectoryInfo() {
    const infoDiv = document.getElementById('directory-info');
    const pathSpan = document.getElementById('active-directory-path');
    const projectTitle = document.getElementById('project-title');
    
    if (browseState.isActive && browseState.activePath) {
        // Show directory info, hide project title
        if (infoDiv) infoDiv.classList.remove('hidden');
        if (projectTitle) projectTitle.style.display = 'none';
        
        // Show shortened path
        if (pathSpan) {
            const shortPath = browseState.activePath.split('/').slice(-2).join('/');
            pathSpan.textContent = shortPath;
            pathSpan.title = browseState.activePath;
        }
    } else {
        // Hide directory info, show project title
        if (infoDiv) infoDiv.classList.add('hidden');
        if (projectTitle) projectTitle.style.display = '';
    }
}

/**
 * Change browse mode (direct/recursive)
 */
function changeBrowseMode(mode) {
    browseState.displayMode = mode;
    if (browseState.isActive) {
        loadImages();
        loadBrowseFilterOptions();
    }
}

/**
 * Load filter options for current browse directory
 */
async function loadBrowseFilterOptions() {
    if (!browseState.activePath) return;
    
    try {
        const response = await fetch(
            `/api/browse/filter-options?directory=${encodeURIComponent(browseState.activePath)}&mode=${browseState.displayMode}`
        );
        const result = await response.json();
        
        if (result.success) {
            filterState.options = result.data;
            renderFilterSections();
        }
    } catch (error) {
        console.error('Failed to load browse filter options:', error);
    }
}

/**
 * Refresh directory tree
 */
function refreshDirectoryTree() {
    browseState.expandedNodes.clear();
    loadDirectoryTree();
}

/**
 * Go to parent directory
 */
function goToParentDirectory() {
    if (!browseState.selectedPath) return;
    
    const parts = browseState.selectedPath.split('/');
    if (parts.length > 1) {
        parts.pop();
        const parentPath = parts.join('/') || '/';
        selectDirectoryNode(parentPath);
        browseState.expandedNodes.add(parentPath);
        loadDirectoryTree();
    }
}

/**
 * Initialize directory browsing on startup
 */
function initDirectoryBrowsing() {
    // Load tree when directories tab is clicked
    const dirTab = document.querySelector('.sidebar-tab[data-tab="directories"]');
    if (dirTab) {
        // Pre-load tree on startup
        setTimeout(() => {
            loadDirectoryTree();
        }, 500);
    }
}

// ============================================
// METADATA PANEL FUNCTIONS
// ============================================

/**
 * Toggle metadata panel collapse state
 */
function toggleMetadataPanel() {
    const panel = document.getElementById('metadata-panel');
    const icon = document.getElementById('meta-panel-toggle-icon');
    
    if (!panel) return;
    
    panel.classList.toggle('collapsed');
    const isCollapsed = panel.classList.contains('collapsed');
    icon.textContent = isCollapsed ? '◀' : '▶';
    
    // Save state to localStorage
    localStorage.setItem('metadata_panel_collapsed', isCollapsed);
}

/**
 * Initialize metadata panel state from localStorage
 */
function initMetadataPanel() {
    const collapsed = localStorage.getItem('metadata_panel_collapsed');
    const panel = document.getElementById('metadata-panel');
    const icon = document.getElementById('meta-panel-toggle-icon');
    
    if (!panel) return;
    
    // Default to collapsed
    if (collapsed === null || collapsed === 'true') {
        panel.classList.add('collapsed');
        if (icon) icon.textContent = '◀';
    } else {
        panel.classList.remove('collapsed');
        if (icon) icon.textContent = '▶';
    }
}

/**
 * Toggle a section within the metadata panel
 */
function toggleMetadataSection(headerElement) {
    const section = headerElement.closest('.panel-section');
    if (section) {
        section.classList.toggle('collapsed');
    }
}

/**
 * Render statistics for the active dataset
 */
function renderStatistics(stats) {
    const container = document.getElementById('stats-content');
    if (!container) return;
    
    if (!stats || Object.keys(stats).length === 0) {
        container.innerHTML = '<div class="no-stats">No statistics available</div>';
        return;
    }
    
    let html = '';
    
    for (const [field, counts] of Object.entries(stats)) {
        const total = Object.values(counts).reduce((a, b) => a + b, 0);
        const maxCount = Math.max(...Object.values(counts));
        
        // Sort by count descending
        const sortedEntries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
        
        html += `
            <div class="stats-field">
                <div class="stats-field-name">${escapeHtml(field)}</div>
                <div class="stats-items">
        `;
        
        for (const [value, count] of sortedEntries) {
            const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
            html += `
                <div class="stats-item">
                    <span class="stats-label" title="${escapeHtml(value)}">${escapeHtml(value)}</span>
                    <div class="stats-bar-container">
                        <div class="stats-bar" style="width: ${percentage}%"></div>
                    </div>
                    <span class="stats-count">${count}</span>
                </div>
            `;
        }
        
        html += '</div></div>';
    }
    
    container.innerHTML = html;
}

/**
 * Update metadata panel when dataset changes
 */
function updateMetadataPanel() {
    if (!browseState.isActive) {
        renderNoDatasetMessage();
        return;
    }
    
    // Load and display metadata
    loadDatasetMetadata();
}

/**
 * Show "no dataset" message in all sections
 */
function renderNoDatasetMessage() {
    const statsContainer = document.getElementById('stats-content');
    const propsContainer = document.getElementById('properties-content');
    const configContainer = document.getElementById('config-content');
    
    const message = `
        <div class="no-dataset-message">
            <div class="message-icon">📁</div>
            <p>Activate a dataset to view information</p>
        </div>
    `;
    
    if (statsContainer) statsContainer.innerHTML = message;
    // Keep the form in properties but disable it
    if (propsContainer) {
        const form = propsContainer.querySelector('.metadata-form');
        if (form) {
            form.querySelectorAll('input, textarea, select').forEach(el => {
                el.value = '';
                el.disabled = true;
            });
            form.querySelectorAll('input[type="checkbox"]').forEach(el => {
                el.checked = false;
                el.disabled = true;
            });
        }
    }
}

/**
 * Load metadata for active dataset from backend
 */
async function loadDatasetMetadata() {
    if (!browseState.isActive || !browseState.activePath) {
        renderNoDatasetMessage();
        return;
    }
    
    try {
        const response = await fetch(`/api/dataset/metadata?path=${encodeURIComponent(browseState.activePath)}`);
        const result = await response.json();
        
        if (result.success) {
            browseState.metadata = result.data;
            populateMetadataForm(result.data);
            
            // Load stats if configured
            if (result.data.stats_config?.fields) {
                loadDatasetStats(result.data.stats_config.fields);
            } else {
                // Use default fields
                loadDatasetStats(['label', 'color', 'model']);
            }
        } else {
            console.error('Failed to load metadata:', result.error);
        }
    } catch (error) {
        console.error('Failed to load metadata:', error);
    }
}

/**
 * Populate the metadata form with dataset values
 */
function populateMetadataForm(metadata) {
    const form = document.getElementById('metadata-form');
    if (!form) return;
    
    // Enable all fields
    form.querySelectorAll('input, textarea, select').forEach(el => {
        el.disabled = false;
    });
    form.querySelectorAll('input[type="checkbox"]').forEach(el => {
        el.disabled = false;
    });
    
    // Set name (read-only)
    const nameInput = form.querySelector('input[name="name"]');
    if (nameInput) {
        nameInput.value = metadata.name || browseState.activePath.split('/').pop() || '';
    }
    
    // Set text fields
    const description = form.querySelector('textarea[name="description"]');
    if (description) description.value = metadata.description || '';
    
    const notes = form.querySelector('textarea[name="notes"]');
    if (notes) notes.value = metadata.notes || '';
    
    // Set select fields
    const quality = form.querySelector('select[name="quality"]');
    if (quality) quality.value = metadata.quality || '';
    
    const verdict = form.querySelector('select[name="verdict"]');
    if (verdict) verdict.value = metadata.verdict || '';
    
    const cycle = form.querySelector('select[name="cycle"]');
    if (cycle) cycle.value = metadata.cycle || '';
    
    // Set camera view checkboxes
    const cameraViews = metadata.camera_view || [];
    form.querySelectorAll('input[name="camera_view"]').forEach(checkbox => {
        checkbox.checked = cameraViews.includes(checkbox.value);
    });
    
    // Update stats config checkboxes
    const statsFields = metadata.stats_config?.fields || ['label', 'color', 'model'];
    document.querySelectorAll('input[name="stats_fields"]').forEach(checkbox => {
        checkbox.checked = statsFields.includes(checkbox.value);
    });
}

/**
 * Save dataset metadata to backend
 */
async function saveDatasetMetadata() {
    if (!browseState.isActive || !browseState.activePath) {
        showNotification('No dataset active', 'warning');
        return;
    }
    
    const form = document.getElementById('metadata-form');
    if (!form) return;
    
    // Collect form values
    const updates = {
        description: form.querySelector('textarea[name="description"]').value,
        quality: form.querySelector('select[name="quality"]').value,
        verdict: form.querySelector('select[name="verdict"]').value,
        cycle: form.querySelector('select[name="cycle"]').value,
        notes: form.querySelector('textarea[name="notes"]').value,
        camera_view: Array.from(form.querySelectorAll('input[name="camera_view"]:checked')).map(cb => cb.value)
    };
    
    try {
        const response = await fetch('/api/dataset/metadata', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: browseState.activePath,
                metadata: updates
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update local state
            Object.assign(browseState.metadata || {}, updates);
            showNotification('Metadata saved', 'success');
        } else {
            showNotification(result.error || 'Failed to save', 'error');
        }
    } catch (error) {
        console.error('Failed to save metadata:', error);
        showNotification('Failed to save metadata', 'error');
    }
}

/**
 * Save stats configuration
 */
async function saveStatsConfig() {
    if (!browseState.isActive || !browseState.activePath) {
        showNotification('No dataset active', 'warning');
        return;
    }
    
    const checkboxes = document.querySelectorAll('input[name="stats_fields"]:checked');
    const fields = Array.from(checkboxes).map(cb => cb.value);
    
    if (fields.length === 0) {
        showNotification('Select at least one field', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/dataset/stats-config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: browseState.activePath,
                fields: fields
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update local state
            if (!browseState.metadata) browseState.metadata = {};
            browseState.metadata.stats_config = { fields };
            
            // Reload stats with new fields
            loadDatasetStats(fields);
            
            showNotification('Stats configuration updated', 'success');
        } else {
            showNotification(result.error || 'Failed to save', 'error');
        }
    } catch (error) {
        console.error('Failed to save stats config:', error);
        showNotification('Failed to save configuration', 'error');
    }
}

/**
 * Load dataset statistics based on configured fields
 */
async function loadDatasetStats(fields) {
    if (!browseState.isActive || !browseState.activePath) {
        return;
    }
    
    try {
        const response = await fetch(`/api/dataset/stats?path=${encodeURIComponent(browseState.activePath)}&fields=${encodeURIComponent(fields.join(','))}`);
        const result = await response.json();
        
        if (result.success) {
            renderStatistics(result.data);
        } else {
            console.error('Failed to load stats:', result.error);
            renderStatistics({});
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
        renderStatistics({});
    }
}
