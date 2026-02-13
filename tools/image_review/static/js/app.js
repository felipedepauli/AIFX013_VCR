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
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', init);

async function init() {
    console.log('🖼️ Image Review Tool - Initializing...');
    populateDefaultOptions();
    await loadRecentProjects();
    setupEventListeners();
    initFilterPanel();
    console.log('✓ Initialization complete');
}

function setupEventListeners() {
    // Project name validation
    document.getElementById('project-name').addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^a-zA-Z0-9_]/g, '');
    });
    
    // Recent project selection info
    document.getElementById('recent-projects').addEventListener('change', onRecentProjectChange);
    
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
            setGridSize(4);
            break;
        case '2':
            setGridSize(9);
            break;
        case '3':
            setGridSize(25);
            break;
        case '4':
            setGridSize(36);
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
    // Populate quality flags radio buttons
    const qualityContainer = document.getElementById('default-quality-flags');
    qualityContainer.innerHTML = DEFAULT_QUALITY_FLAGS.map((flag, i) => `
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
    ` + DEFAULT_PERSPECTIVE_FLAGS.slice(0, 4).map(flag => `
        <label>
            <input type="radio" name="default-perspective" value="${flag}">
            ${flag}
        </label>
    `).join('') + `
        <label>
            <input type="radio" name="default-perspective" value="">
            <em>+ more...</em>
        </label>
    `;
    
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

function closeStartupModal() {
    document.getElementById('startup-modal').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
}

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
        const response = await fetch(
            `/api/images?page=${gridState.currentPage}&size=${gridState.gridSize}${filterParams}`
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
        const response = await fetch(`/api/image/${seqId}/full`);
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
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx > 0) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx - 1];
        loadModalImage(modalState.currentSeqId);
        updateModalNavButtons();
    }
}

function modalNextImage() {
    const currentIdx = modalState.visibleSeqIds.indexOf(modalState.currentSeqId);
    if (currentIdx < modalState.visibleSeqIds.length - 1) {
        modalState.currentSeqId = modalState.visibleSeqIds[currentIdx + 1];
        loadModalImage(modalState.currentSeqId);
        updateModalNavButtons();
    }
}

function closeImageModal() {
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
    
    // Get label data
    const labelData = await loadLabels(seqId);
    editPanelState.labelData = labelData;
    editPanelState.selectedObjectIndex = 0;
    
    if (!labelData || !labelData.has_labels || labelData.objects.length === 0) {
        objectSelector.innerHTML = '';
        labelEditors.innerHTML = '<div class="no-labels-message">📋 No labels available for this image</div>';
        return;
    }
    
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
        const response = await fetch(`/api/labels/${seqId}`);
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
    
    qualityPills.forEach(pill => {
        const flag = pill.textContent.trim();
        if (FLAG_CONFIG.quality.flags.includes(flag)) {
            flagModalState.selectedQualityFlags.add(flag);
        }
    });
    
    perspectivePills.forEach(pill => {
        const flag = pill.textContent.trim();
        if (FLAG_CONFIG.perspective.flags.includes(flag)) {
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
    // Quality flags
    const qualityGrid = document.getElementById('quality-flags-grid');
    qualityGrid.innerHTML = '';
    
    FLAG_CONFIG.quality.flags.forEach(flag => {
        const isChecked = flagModalState.selectedQualityFlags.has(flag);
        const color = FLAG_CONFIG.quality.colors[flag];
        
        qualityGrid.innerHTML += `
            <label class="flag-checkbox ${isChecked ? 'checked' : ''}" data-flag="${flag}">
                <input type="checkbox" ${isChecked ? 'checked' : ''} 
                       onchange="toggleQualityFlag('${flag}', this.checked)">
                <span class="flag-label">${flag}</span>
                <span class="flag-color" style="background: ${color}"></span>
            </label>
        `;
    });
    
    // Perspective flags
    const perspectiveGrid = document.getElementById('perspective-flags-grid');
    perspectiveGrid.innerHTML = '';
    
    FLAG_CONFIG.perspective.flags.forEach(flag => {
        const isChecked = flagModalState.selectedPerspectiveFlags.has(flag);
        const color = FLAG_CONFIG.perspective.colors[flag];
        
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
        
        const order = FLAG_CONFIG.quality.flags;
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

// Quick apply flag (without modal)
async function applyQuickFlag(seqId, qualityFlags, perspectiveFlags) {
    try {
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
    } catch (error) {
        console.error('Quick flag failed:', error);
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
    const flags = projectData?.settings?.quality_flags || FLAG_CONFIG.quality.flags;
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag">
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
    const flags = projectData?.settings?.perspective_flags || FLAG_CONFIG.perspective.flags;
    
    container.innerHTML = flags.map(flag => `
        <span class="flag-tag">
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
    
    const flags = projectData?.settings?.quality_flags || [...FLAG_CONFIG.quality.flags];
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('quality_flags', flags);
    
    input.value = '';
    renderQualityFlagsSettings();
    
    // Update flag modal if open
    if (flagModalState.isOpen) {
        renderFlagCheckboxes();
    }
}

// Remove quality flag
function removeQualityFlag(flag) {
    const flags = projectData?.settings?.quality_flags || [...FLAG_CONFIG.quality.flags];
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('quality_flags', newFlags);
    
    // Clear default if removed
    if (projectData?.settings?.default_quality_flag === flag) {
        updateSetting('default_quality_flag', null);
    }
    
    renderQualityFlagsSettings();
}

// Add perspective flag
function addPerspectiveFlag() {
    const input = document.getElementById('new-perspective-flag');
    const flagName = input.value.trim().toLowerCase().replace(/\s+/g, '_');
    
    if (!flagName) return;
    
    const flags = projectData?.settings?.perspective_flags || [...FLAG_CONFIG.perspective.flags];
    if (flags.includes(flagName)) {
        showNotification('Flag already exists', 'warning');
        return;
    }
    
    flags.push(flagName);
    updateSetting('perspective_flags', flags);
    
    input.value = '';
    renderPerspectiveFlagsSettings();
}

// Remove perspective flag
function removePerspectiveFlag(flag) {
    const flags = projectData?.settings?.perspective_flags || [...FLAG_CONFIG.perspective.flags];
    const newFlags = flags.filter(f => f !== flag);
    
    updateSetting('perspective_flags', newFlags);
    
    if (projectData?.settings?.default_perspective_flag === flag) {
        updateSetting('default_perspective_flag', null);
    }
    
    renderPerspectiveFlagsSettings();
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
    const mainContent = document.querySelector('.main-content');
    const toggleBtn = document.getElementById('filter-toggle-btn');
    
    if (!panel) return;
    
    filterState.isOpen = !filterState.isOpen;
    panel.classList.toggle('collapsed', !filterState.isOpen);
    
    if (mainContent) {
        mainContent.classList.toggle('panel-collapsed', !filterState.isOpen);
    }
    
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
