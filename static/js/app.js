function botAction(id, action) {
    const btn = event.target.closest('button');
    if (!btn) return;

    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>';

    fetch(`/bot/${id}/${action}`, { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
                setTimeout(() => location.reload(), 600);
            } else {
                showToast(data.message, 'error');
                btn.disabled = false;
                btn.innerHTML = originalHTML;
            }
        })
        .catch(() => {
            showToast('Connection error', 'error');
            btn.disabled = false;
            btn.innerHTML = originalHTML;
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
                    card.style.transition = 'all 0.2s ease';
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

    const icons = {
        success: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>',
        error: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>',
        info: '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const iconSpan = document.createElement('div');
    iconSpan.className = 'flex items-center gap-2';
    iconSpan.innerHTML = icons[type] || '';
    const msgSpan = document.createElement('span');
    msgSpan.textContent = message;
    iconSpan.appendChild(msgSpan);
    toast.appendChild(iconSpan);
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
            const cpu = document.getElementById('stat-cpu');
            const ram = document.getElementById('stat-ram');
            const disk = document.getElementById('stat-disk');
            const bots = document.getElementById('stat-bots');
            const cpuBar = document.getElementById('cpu-bar');
            const ramBar = document.getElementById('ram-bar');
            const diskBar = document.getElementById('disk-bar');

            if (cpu) cpu.textContent = data.cpu_percent + '%';
            if (ram) ram.textContent = data.memory_used_mb + 'MB';
            if (disk) disk.textContent = data.disk_used_gb + 'GB';
            if (bots) bots.textContent = data.running_bots + '/' + data.total_projects;
            if (cpuBar) cpuBar.style.width = data.cpu_percent + '%';
            if (ramBar) {
                const ramPercent = Math.min(100, (data.memory_used_mb / data.memory_total_mb) * 100);
                ramBar.style.width = ramPercent + '%';
            }
            if (diskBar) {
                const diskPercent = Math.min(100, (data.disk_used_gb / data.disk_total_gb) * 100);
                diskBar.style.width = diskPercent + '%';
            }
        })
        .catch(() => {});
}

if (document.getElementById('stat-cpu')) {
    fetchStats();
    setInterval(fetchStats, 5000);
}
