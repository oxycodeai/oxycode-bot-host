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
            document.getElementById('save-btn').disabled = false;
            document.title = '* ' + document.title;
        }
    });
});

function openFile(filepath) {
    if (hasChanges && !confirm('Unsaved changes. Continue?')) return;

    currentFilePath = filepath;
    document.getElementById('current-file-path').textContent = filepath;
    document.title = filepath + ' - Editor';

    document.querySelectorAll('.file-item').forEach(el => {
        el.classList.toggle('bg-zinc-800', el.dataset.path === filepath);
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
            alert(data.error);
            return;
        }
        editor.setValue(data.content);
        editor.setOption('mode', getMode(filepath));
        editor.clearHistory();
        hasChanges = false;
        document.getElementById('save-btn').disabled = true;
        document.title = filepath + ' - Editor';
    })
    .catch(() => alert('Failed to load file'));
}

function saveFile() {
    if (!currentFilePath || !editor) return;

    const btn = document.getElementById('save-btn');
    btn.disabled = true;
    btn.textContent = 'Saving...';

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
            btn.textContent = 'Saved!';
            setTimeout(() => {
                btn.textContent = 'Save';
                btn.disabled = false;
            }, 1500);
        } else {
            alert(data.error || 'Save failed');
            btn.textContent = 'Save';
            btn.disabled = false;
        }
    })
    .catch(() => {
        alert('Connection error');
        btn.textContent = 'Save';
        btn.disabled = false;
    });
}
