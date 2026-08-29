let editor = null;
let currentFilePath = window.CURRENT_FILE;
let hasChanges = false;

const MODE_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.ts': 'text/typescript',
    '.json': { name: 'javascript', json: true },
    '.html': 'htmlmixed',
    '.htm': 'htmlmixed',
    '.css': 'css',
    '.yml': 'yaml',
    '.yaml': 'yaml',
    '.md': 'markdown',
    '.sh': 'shell',
    '.bash': 'shell',
    '.env': 'properties',
    '.cfg': 'properties',
    '.ini': 'properties',
    '.toml': 'python',
    '.txt': 'text/plain'
};

function getMode(filename) {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return MODE_MAP[ext] || 'text/plain';
}

document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('editor');
    if (!textarea) return;

    editor = CodeMirror.fromTextArea(textarea, {
        theme: 'material-darker',
        lineNumbers: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        indentUnit: 4,
        tabSize: 4,
        indentWithTabs: false,
        lineWrapping: false,
        viewportMargin: Infinity,
        extraKeys: {
            'Ctrl-S': function() { saveFile(); },
            'Cmd-S': function() { saveFile(); }
        }
    });

    if (currentFilePath) {
        editor.setOption('mode', getMode(currentFilePath));
    }

    editor.on('change', function() {
        if (!hasChanges) {
            hasChanges = true;
            const btn = document.getElementById('save-btn');
            if (btn) btn.disabled = false;
            document.title = '* ' + document.title;
        }
    });
});

function openFile(filepath) {
    if (hasChanges && !confirm('Unsaved changes. Continue?')) return;

    currentFilePath = filepath;
    const pathEl = document.getElementById('current-file-path');
    if (pathEl) pathEl.textContent = filepath;
    document.title = filepath + ' - Editor';

    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.toggle('bg-white/[0.06]', el.dataset.path === filepath);
        el.classList.toggle('text-zinc-100', el.dataset.path === filepath);
    });

    fetch('/api/editor/read', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: window.PROJECT_ID, filepath: filepath })
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }
        editor.setValue(data.content);
        editor.setOption('mode', getMode(filepath));
        editor.clearHistory();
        hasChanges = false;
        const btn = document.getElementById('save-btn');
        if (btn) btn.disabled = true;
        document.title = filepath + ' - Editor';
    })
    .catch(() => showToast('Failed to load file', 'error'));
}

function saveFile() {
    if (!currentFilePath || !editor) return;

    const btn = document.getElementById('save-btn');
    const originalHTML = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>';
    }

    fetch('/api/editor/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            project_id: window.PROJECT_ID,
            filepath: currentFilePath,
            content: editor.getValue()
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            hasChanges = false;
            document.title = currentFilePath + ' - Editor';
            showToast('File saved', 'success');
            if (btn) {
                btn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Saved';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.disabled = false;
                }, 1500);
            }
        } else {
            showToast(data.error || 'Save failed', 'error');
            if (btn) {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            }
        }
    })
    .catch(() => {
        showToast('Connection error', 'error');
        if (btn) {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    });
}

function createNewFile() {
    const filename = prompt('Enter filename (e.g., bot.py, config.json):');
    if (!filename) return;

    if (!/^[a-zA-Z0-9._-]+$/.test(filename)) {
        showToast('Invalid filename', 'error');
        return;
    }

    fetch('/api/editor/create-file', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_id: window.PROJECT_ID, filename: filename })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            showToast('File created', 'success');
            openFile(data.filepath);
            setTimeout(() => location.reload(), 500);
        } else {
            showToast(data.error || 'Failed to create file', 'error');
        }
    })
    .catch(() => showToast('Connection error', 'error'));
}

function showToast(message, type) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const icons = {
        success: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const iconDiv = document.createElement('div');
    iconDiv.className = 'flex items-center gap-2';
    iconDiv.innerHTML = icons[type] || '';
    const msgSpan = document.createElement('span');
    msgSpan.textContent = message;
    iconDiv.appendChild(msgSpan);
    toast.appendChild(iconDiv);
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
