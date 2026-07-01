/* ============================================================
   definicoes.js
   Handles:
     1. Theme toggle  (Claro / Escuro)
     2. AI moderation threshold saving  (admin only)
   ============================================================ */

// ── 1. Theme toggle ──────────────────────────────────────────

const THEME_KEY = 'theme';

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
}

function syncToggleUI(theme) {
    document.querySelectorAll('#theme-toggle .settings-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.value === theme);
    });
}

// Initialise toggle state from localStorage on page load
const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
syncToggleUI(savedTheme);

document.querySelectorAll('#theme-toggle .settings-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const chosen = btn.dataset.value;   // 'light' | 'dark'
        applyTheme(chosen);
        syncToggleUI(chosen);
    });
});


// ── 2. AI threshold saving (superuser only) ──────────────────

const saveBtn = document.getElementById('save-ai-thresholds');

if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        const ideal  = document.querySelector('[name="ideal_threshold"]').value;
        const low    = document.querySelector('[name="low_threshold"]').value;
        const medium = document.querySelector('[name="medium_threshold"]').value;
        const high   = document.querySelector('[name="high_threshold"]').value;
        const aiPrompt = document.querySelector('[name="ai_prompt"]').value;

        const response = await fetch('/com_soc/save_config/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({
                ideal_threshold:  ideal,
                low_threshold:    low,
                medium_threshold: medium,
                high_threshold:   high,
                ai_prompt:        aiPrompt,
            }),
        });

        const data = await response.json();

        if (data.success) {
            showToast('Limiares guardados com sucesso', 'success');
        } else {
            showToast('Erro ao guardar.', 'error');
        }
    });
}


// ── Helpers ──────────────────────────────────────────────────

function getCSRFToken() {
    return document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}

function showToast(message = 'Guardado', variant = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    const iconEl   = toast.querySelector('.toast-icon');
    const msgEl    = toast.querySelector('.toast-message');

    // Reset variant classes
    toast.classList.remove('toast--success', 'toast--error', 'toast--info');
    toast.classList.add(`toast--${variant}`);

    if (iconEl) iconEl.textContent = variant === 'success' ? '✓' : '✕';
    if (msgEl)  msgEl.textContent  = message;

    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2500);
}