document.addEventListener('DOMContentLoaded', () => {

    // Mark all unread as read after a short delay so the user sees the highlights first
    const unread = document.querySelectorAll('.notif-item--unread');
    if (unread.length > 0) {
        fetch('/com_soc/notifications/mark-read/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrf() }
        });
    }
    // -----------------------------------------------------------------------
    // Delete individual
    // -----------------------------------------------------------------------
    document.querySelectorAll('.notif-delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            const item = document.querySelector(`.notif-item[data-id="${id}"]`);

            item.classList.add('notif-item--removing');
            setTimeout(() => {
                fetch(`/com_soc/notifications/delete/${id}/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrf() }
                })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        item.remove();
                        updateCount();
                    }
                });
            }, 200);
        });
    });

    // -----------------------------------------------------------------------
    // Delete all
    // -----------------------------------------------------------------------
    document.getElementById('delete-all-btn')?.addEventListener('click', () => {
        const items = document.querySelectorAll('.notif-item');
        items.forEach(item => item.classList.add('notif-item--removing'));

        setTimeout(() => {
            fetch('/com_soc/notifications/delete-all/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('notif-list')?.remove();
                    document.getElementById('delete-all-btn')?.closest('.notif-header').querySelector('.notif-header-left .notif-count')?.remove();
                    document.getElementById('delete-all-btn')?.remove();
                    showEmpty();
                }
            });
        }, 220);
    });

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    function updateCount() {
        const remaining = document.querySelectorAll('.notif-item').length;
        const countEl = document.querySelector('.notif-count');
        if (remaining === 0) {
            document.getElementById('notif-list')?.remove();
            document.getElementById('delete-all-btn')?.remove();
            if (countEl) countEl.remove();
            showEmpty();
        } else if (countEl) {
            countEl.textContent = remaining;
        }
    }

    function showEmpty() {
        if (document.getElementById('notif-empty')) return;
        const empty = document.createElement('div');
        empty.id = 'notif-empty';
        empty.className = 'notif-empty';
        empty.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
            </svg>
            <p>Não tens notificações.</p>
        `;
        document.querySelector('.notif-page').appendChild(empty);
    }

    function getCsrf() {
        return document.cookie.split('; ')
            .find(r => r.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }
});