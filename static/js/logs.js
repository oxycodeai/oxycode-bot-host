const logOutput = document.getElementById('log-output');
const autoScroll = document.getElementById('auto-scroll');
let refreshInterval = null;

function refreshLogs() {
    fetch(`/api/logs/${window.PROJECT_ID}?lines=500`)
        .then(r => r.json())
        .then(data => {
            logOutput.textContent = data.logs || 'No logs yet.';
            if (autoScroll.checked) {
                logOutput.scrollTop = logOutput.scrollHeight;
            }
        })
        .catch(() => {
            logOutput.textContent = 'Failed to load logs.';
        });
}

function clearLogs() {
    if (!confirm('Clear all logs?')) return;
    fetch(`/api/logs/${window.PROJECT_ID}/clear`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                logOutput.textContent = 'Logs cleared.';
            }
        });
}

refreshLogs();
refreshInterval = setInterval(refreshLogs, 3000);

document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        clearInterval(refreshInterval);
    } else {
        refreshLogs();
        refreshInterval = setInterval(refreshLogs, 3000);
    }
});
