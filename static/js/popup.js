(function() {
    const KEY = 'oxycode_popup_seen';
    const popup = document.getElementById('telegram-popup');
    const checkbox = document.getElementById('dont-show-again');
    const closeBtn = document.getElementById('popup-close');
    const joinBtn = document.getElementById('popup-join');

    if (!popup) return;

    if (localStorage.getItem(KEY) === 'true') {
        popup.classList.add('hidden');
        return;
    }

    popup.classList.remove('hidden');

    function dismiss() {
        if (checkbox && checkbox.checked) {
            localStorage.setItem(KEY, 'true');
        }
        popup.classList.add('hidden');
    }

    if (closeBtn) closeBtn.addEventListener('click', dismiss);
    if (joinBtn) {
        joinBtn.addEventListener('click', function() {
            if (checkbox && checkbox.checked) {
                localStorage.setItem(KEY, 'true');
            }
        });
    }

    popup.addEventListener('click', function(e) {
        if (e.target === popup) dismiss();
    });
})();
