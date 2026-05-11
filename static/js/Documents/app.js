// Dark Mode Toggle
const themeBtn = document.getElementById('theme-btn');
const html = document.documentElement;

// Check for saved theme preference or default to light mode
const savedTheme = localStorage.getItem('theme') || 'light';
if (savedTheme === 'dark') {
    html.classList.add('dark-mode');
    themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
}

themeBtn.addEventListener('click', () => {
    html.classList.toggle('dark-mode');
    const isNowDark = html.classList.contains('dark-mode');
    localStorage.setItem('theme', isNowDark ? 'dark' : 'light');
    themeBtn.innerHTML = isNowDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
});

// UI Elements
const dirPathInput = document.getElementById('dir-path');
const browseBtn = document.getElementById('browse-btn');
const selectedInfo = document.getElementById('selected-info');
const selectedPath = document.getElementById('selected-path');
const fileCount = document.getElementById('file-count');
const fileSelectionSection = document.getElementById('file-selection-section');
const fileList = document.getElementById('file-list');
const selectAllBtn = document.getElementById('select-all-btn');
const deselectAllBtn = document.getElementById('deselect-all-btn');
const selectedFileCountLabel = document.getElementById('selected-file-count');
const skipDuplicates = document.getElementById('skip-duplicates');
const cleanupEmpty = document.getElementById('cleanup-empty');
const organizeBtn = document.getElementById('organize-btn');
const restoreBtn = document.getElementById('restore-btn');
const settingsBtn = document.getElementById('settings-btn');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');
const statusLabel = document.getElementById('status');
const logContainer = document.getElementById('log-container');
const clearLogBtn = document.getElementById('clear-log-btn');
const copyLogBtn = document.getElementById('copy-log-btn');
const toast = document.getElementById('toast');
const categoriesModal = document.getElementById('categories-modal');
const categoriesGrid = document.getElementById('categories-grid');
const saveCategoriesBtn = document.getElementById('save-categories-btn');
const modalCloseButtons = document.querySelectorAll('.modal-close');
const browseModal = document.getElementById('browse-modal');
const browseCurrentPath = document.getElementById('browse-current-path');
const browseList = document.getElementById('browse-list');
const browseSelectBtn = document.getElementById('browse-select-btn');
const browseCancelBtn = document.getElementById('browse-cancel-btn');
const browseCloseBtn = document.getElementById('browse-close-btn');

let selectedDirectory = null;
let selectedFiles = [];
let currentBrowsePath = '';
let pollInterval = null;

// Toast Notification
function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = `toast ${type}`;
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}

// Directory Selection
browseBtn.addEventListener('click', openBrowseModal);

dirPathInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        const path = dirPathInput.value.trim();
        if (path) {
            selectDirectory(path);
        }
    }
});

browseCloseBtn.addEventListener('click', closeBrowseModal);
browseCancelBtn.addEventListener('click', closeBrowseModal);

function openBrowseModal() {
    browseModal.classList.remove('hidden');
    currentBrowsePath = '';
    loadBrowseDirectory('');
}

function closeBrowseModal() {
    browseModal.classList.add('hidden');
}

async function loadBrowseDirectory(path) {
    try {
        const response = await fetch('/api/browser', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await response.json();
        if (!data.success) {
            showToast(data.error, 'error');
            return;
        }
        currentBrowsePath = data.relative_path || '';
        browseCurrentPath.textContent = currentBrowsePath || '/';

        if (!data.entries.length) {
            browseList.innerHTML = `
                <div class="browse-entry empty">
                    <i class="fas fa-folder-open"></i>
                    <span>No subfolders found.</span>
                </div>
            `;
            return;
        }

        browseList.innerHTML = '';
        data.entries.forEach(entry => {
            const row = document.createElement('button');
            row.className = 'browse-entry';
            row.type = 'button';
            row.dataset.path = entry.path;
            row.innerHTML = `
                <span><i class="fas fa-folder"></i> ${escapeHtml(entry.name)}</span>
                <span class="browse-entry-badge">Folder</span>
            `;
            row.addEventListener('click', () => {
                loadBrowseDirectory(entry.path);
            });
            browseList.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading browser directory:', error);
        showToast('Failed to load folder list', 'error');
    }
}

browseSelectBtn.addEventListener('click', () => {
    const path = currentBrowsePath || '.';
    dirPathInput.value = path === '.' ? '' : path;
    closeBrowseModal();
    selectDirectory(path);
});

async function selectDirectory(path) {
    try {
        const response = await fetch('/api/select-directory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        
        const data = await response.json();
        
        if (data.success) {
            selectedDirectory = data.path;
            selectedPath.textContent = data.path;
            fileCount.textContent = data.file_count;
            selectedInfo.classList.remove('hidden');
            fileSelectionSection.classList.remove('hidden');
            renderFileList(data.files);
            organizeBtn.disabled = false;
            showToast(`Selected directory with ${data.file_count} files`, 'success');
        } else {
            selectedDirectory = null;
            selectedInfo.classList.add('hidden');
            fileSelectionSection.classList.add('hidden');
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to select directory', 'error');
    }
}

function renderFileList(files) {
    selectedFiles = [];
    selectedFileCountLabel.textContent = '0 selected';

    if (!files || files.length === 0) {
        fileList.innerHTML = `
            <div class="file-entry empty">
                <i class="fas fa-inbox"></i>
                <span>No files found in this directory.</span>
            </div>
        `;
        return;
    }

    fileList.innerHTML = '';
    files.forEach(file => {
        const entry = document.createElement('label');
        entry.className = 'file-entry';
        entry.innerHTML = `
            <input type="checkbox" data-filename="${escapeHtml(file.name)}">
            <div class="file-meta">
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-detail">${file.type || 'File'} · ${formatBytes(file.size)}</span>
            </div>
        `;

        const checkbox = entry.querySelector('input[type="checkbox"]');
        checkbox.addEventListener('change', (event) => {
            const name = event.target.dataset.filename;
            if (event.target.checked) {
                selectedFiles.push(name);
            } else {
                selectedFiles = selectedFiles.filter(item => item !== name);
            }
            updateSelectedFileCount();
        });

        fileList.appendChild(entry);
    });
}

function updateSelectedFileCount() {
    const count = selectedFiles.length;
    selectedFileCountLabel.textContent = `${count} selected`;
}

function formatBytes(bytes) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = Number(bytes);
    let unit = units.shift();
    while (size >= 1024 && units.length) {
        size /= 1024;
        unit = units.shift();
    }
    return `${size.toFixed(1)} ${unit}`;
}

selectAllBtn.addEventListener('click', () => {
    const checkboxes = fileList.querySelectorAll('input[type="checkbox"]');
    selectedFiles = [];
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        selectedFiles.push(checkbox.dataset.filename);
    });
    updateSelectedFileCount();
});

deselectAllBtn.addEventListener('click', () => {
    const checkboxes = fileList.querySelectorAll('input[type="checkbox"]');
    selectedFiles = [];
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedFileCount();
});

// Organization
organizeBtn.addEventListener('click', async () => {
    if (!selectedDirectory) {
        showToast('Please select a directory first', 'error');
        return;
    }
    
    organizeBtn.disabled = true;
    restoreBtn.disabled = true;
    logContainer.innerHTML = '';
    
    try {
        const response = await fetch('/api/organize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                path: selectedDirectory,
                skip_duplicates: skipDuplicates.checked,
                selected_files: selectedFiles
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateStatus('organizing');
            startPolling();
            showToast('Organization started...', 'info');
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to start organization', 'error');
    }
});

// Restore
restoreBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to restore files to their original locations?')) {
        return;
    }
    
    organizeBtn.disabled = true;
    restoreBtn.disabled = true;
    logContainer.innerHTML = '';
    
    try {
        const response = await fetch('/api/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cleanup_empty: cleanupEmpty.checked
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateStatus('organizing');
            startPolling();
            showToast('Restore started...', 'info');
        } else {
            showToast(data.error, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to start restore', 'error');
    }
});

// Polling for Updates
function startPolling() {
    pollInterval = setInterval(updateLogs, 500);
}

async function updateLogs() {
    try {
        const response = await fetch('/api/logs');
        const data = await response.json();
        
        if (data.logs.length > logContainer.querySelectorAll('.log-entry:not(.empty)').length) {
            renderLogs(data.logs);
        }
        
        // Update progress
        if (data.total > 0) {
            const percentage = Math.round((data.progress / data.total) * 100);
            progressBar.querySelector('.progress-fill').style.width = percentage + '%';
            progressText.textContent = percentage + '%';
        }
        
        if (!data.organizing) {
            clearInterval(pollInterval);
            organizeBtn.disabled = false;
            restoreBtn.disabled = false;
            updateStatus('ready');
            showToast('Operation complete!', 'success');
        }
    } catch (error) {
        console.error('Error updating logs:', error);
    }
}

function renderLogs(logs) {
    logContainer.innerHTML = '';
    logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        
        // Determine log type
        if (log.includes('✅') || log.includes('Restored')) {
            entry.classList.add('success');
        } else if (log.includes('❌') || log.includes('Error')) {
            entry.classList.add('error');
        } else if (log.includes('⚠️') || log.includes('Warning')) {
            entry.classList.add('warning');
        } else if (log.includes('✨') || log.includes('complete')) {
            entry.classList.add('success');
        } else {
            entry.classList.add('info');
        }
        
        entry.title = log;
        entry.innerHTML = `<span>${escapeHtml(log)}</span>`;
        logContainer.appendChild(entry);
    });
    
    logContainer.scrollTop = logContainer.scrollHeight;
}

function updateStatus(status) {
    statusLabel.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusLabel.className = 'stat-value status-' + status;
}

// Log Controls
clearLogBtn.addEventListener('click', () => {
    logContainer.innerHTML = '<div class="log-entry empty"><i class="fas fa-inbox"></i><span>Logs cleared</span></div>';
});

copyLogBtn.addEventListener('click', () => {
    const text = Array.from(logContainer.querySelectorAll('.log-entry')).map(e => e.textContent).join('\n');
    navigator.clipboard.writeText(text).then(() => {
        showToast('Logs copied to clipboard', 'success');
    });
});

// Settings Modal
settingsBtn.addEventListener('click', loadCategories);

async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        categoriesGrid.innerHTML = '';
        
        Object.entries(categories).forEach(([name, props]) => {
            const card = document.createElement('div');
            card.className = 'category-card';
            card.innerHTML = `
                <div class="category-name">${name}</div>
                <div class="category-field">
                    <label>Keywords</label>
                    <textarea name="keywords" placeholder="comma-separated">${props.keywords.join(', ')}</textarea>
                </div>
                <div class="category-field">
                    <label>Extensions</label>
                    <textarea name="extensions" placeholder="comma-separated">${props.extensions.join(', ')}</textarea>
                </div>
                <div class="category-field">
                    <label>MIME Types</label>
                    <textarea name="mime_types" placeholder="comma-separated">${props.mime_types.join(', ')}</textarea>
                </div>
            `;
            categoriesGrid.appendChild(card);
        });
        
        categoriesModal.classList.remove('hidden');
    } catch (error) {
        console.error('Error loading categories:', error);
        showToast('Failed to load categories', 'error');
    }
}

// Modal Close
modalCloseButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        categoriesModal.classList.add('hidden');
    });
});

categoriesModal.addEventListener('click', (e) => {
    if (e.target === categoriesModal) {
        categoriesModal.classList.add('hidden');
    }
});

// Save Categories
saveCategoriesBtn.addEventListener('click', async () => {
    const updated = {};
    
    document.querySelectorAll('.category-card').forEach((card, idx) => {
        const name = card.querySelector('.category-name').textContent;
        const keywords = card.querySelector('[name="keywords"]').value.split(',').map(k => k.trim()).filter(Boolean);
        const extensions = card.querySelector('[name="extensions"]').value.split(',').map(e => e.trim()).filter(Boolean);
        const mime_types = card.querySelector('[name="mime_types"]').value.split(',').map(m => m.trim()).filter(Boolean);
        
        updated[name] = { keywords, extensions, mime_types };
    });
    
    try {
        const response = await fetch('/api/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updated)
        });
        
        if (response.ok) {
            showToast('Categories updated successfully', 'success');
            categoriesModal.classList.add('hidden');
        } else {
            showToast('Failed to update categories', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Failed to update categories', 'error');
    }
});

// Utility Functions
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Initialize
window.addEventListener('load', () => {
    // Check if restore log exists
    fetch('/api/logs').then(r => r.json()).then(data => {
        restoreBtn.disabled = !data.can_restore;
    });
});
