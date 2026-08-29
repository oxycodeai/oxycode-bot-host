function botAction(id, action) {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = action === 'start' ? 'Starting...' : action === 'stop' ? 'Stopping...' : 'Restarting...';

    fetch(`/bot/${id}/${action}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 800);
            } else {
                showToast(data.message, 'error');
                btn.disabled = false;
                btn.textContent = action.charAt(0).toUpperCase() + action.slice(1);
            }
        })
        .catch(() => {
            showToast('Connection error', 'error');
            btn.disabled = false;
            btn.textContent = action.charAt(0).toUpperCase() + action.slice(1);
        });
}

function deleteBot(id, name) {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;

    fetch(`/bot/${id}/delete`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast('Bot deleted', 'success');
                const card = document.querySelector(`[data-project-id="${id}"]`);
                if (card) {
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.95)';
                    setTimeout(() => card.remove(), 200);
                }
            } else {
                showToast(data.message || 'Delete failed', 'error');
            }
        })
        .catch(() => showToast('Connection error', 'error'));
}

function showToast(message, type) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function fetchStats() {
    fetch('/api/stats')
        .then(r => r.json())
        .then(data => {
            document.getElementById('stat-cpu').textContent = data.cpu_percent + '%';
            document.getElementById('stat-ram').textContent = data.memory_used_mb + 'MB';
            document.getElementById('stat-disk').textContent = data.disk_used_gb + 'GB';
            document.getElementById('stat-bots').textContent = data.running_bots + '/' + data.total_projects;
        })
        .catch(() => {});
}

fetchStats();
setInterval(fetchStats, 5000);
