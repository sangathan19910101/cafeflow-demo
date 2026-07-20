// CafeFlow Main JavaScript
(function() {
    'use strict';

    // Auto-refresh KDS dashboard every 15 seconds
    const kdsContainer = document.getElementById('kds-dashboard');
    if (kdsContainer) {
        setInterval(function() {
            fetch(window.location.href)
                .then(r => r.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newContent = doc.getElementById('kds-dashboard');
                    if (newContent) {
                        kdsContainer.innerHTML = newContent.innerHTML;
                    }
                })
                .catch(() => {});
        }, 15000);
    }

    // Confirm destructive actions
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Are you sure?')) {
                e.preventDefault();
            }
        });
    });

    // Auto-hide messages after 5 seconds
    document.querySelectorAll('.message, .msg').forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity .5s';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }, 5000);
    });

    // Table position drag on floor layout
    let dragTable = null;
    document.querySelectorAll('.table-cell.draggable').forEach(cell => {
        cell.addEventListener('mousedown', function(e) {
            dragTable = {
                id: this.dataset.tableId,
                x: parseInt(this.dataset.x),
                y: parseInt(this.dataset.y),
                offsetX: e.offsetX,
                offsetY: e.offsetY,
                el: this
            };
        });
    });
    document.addEventListener('mousemove', function(e) {
        if (!dragTable) return;
        // Drag logic
    });
    document.addEventListener('mouseup', function() {
        dragTable = null;
    });

})();
