/* ==========================================
   Account Page JavaScript
   ========================================== */

document.addEventListener('DOMContentLoaded', function () {
    initAvatarUpload();
    initUsernameEdit();
    initPasswordModal();
});

/* ==========================================
   Avatar Upload
   ========================================== */
function initAvatarUpload() {
    const fileInput = document.getElementById('avatar-file-input');
    const avatarImg = document.getElementById('avatar-img');
    const avatarInitials = document.getElementById('avatar-initials');
    if (!fileInput) return;

    fileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;

        // Validate: image only, max 5 MB
        if (!file.type.startsWith('image/')) {
            showToast('Apenas imagens são permitidas.', 'error');
            return;
        }
        if (file.size > 5 * 1024 * 1024) {
            showToast('A imagem não pode exceder 5 MB.', 'error');
            return;
        }

        // Optimistic preview
        const reader = new FileReader();
        reader.onload = e => {
            avatarImg.src = e.target.result;
            avatarImg.style.display = 'block';
            if (avatarInitials) avatarInitials.style.display = 'none';
        };
        reader.readAsDataURL(file);

        // Upload via AJAX
        const fd = new FormData();
        fd.append('profile_picture', file);
        fd.append('csrfmiddlewaretoken', getCsrf());

        fetch('/conta/atualizar-avatar/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast('Foto de perfil atualizada!', 'success');
            } else {
                showToast(data.error || 'Erro ao atualizar foto.', 'error');
                // Revert preview if upload failed
                if (!avatarImg.dataset.originalSrc) {
                    avatarImg.style.display = 'none';
                    if (avatarInitials) avatarInitials.style.display = '';
                } else {
                    avatarImg.src = avatarImg.dataset.originalSrc;
                }
            }
        })
        .catch(() => showToast('Erro de ligação. Tenta novamente.', 'error'));
    });

    // Store original src so we can revert on error
    if (avatarImg && avatarImg.src && !avatarImg.src.endsWith('/')) {
        avatarImg.dataset.originalSrc = avatarImg.src;
    }
}

/* ==========================================
   Username Inline Edit
   ========================================== */
function initUsernameEdit() {
    const editBtn    = document.getElementById('username-edit-btn');
    const cancelBtn  = document.getElementById('username-cancel-btn');
    const saveBtn    = document.getElementById('username-save-btn');
    const viewRow    = document.getElementById('username-view-row');
    const editRow    = document.getElementById('username-edit-row');
    const input      = document.getElementById('username-input');
    const display    = document.getElementById('username-display');
    const sidebarDisplay = document.getElementById('display-username');
    const feedback   = document.getElementById('username-feedback');

    if (!editBtn) return;

    function openEdit() {
        viewRow.style.display = 'none';
        editRow.style.display = 'block';
        input.value = display.textContent.trim();
        input.focus();
        input.select();
        clearFeedback();
    }

    function closeEdit() {
        viewRow.style.display = '';
        editRow.style.display = 'none';
        clearFeedback();
    }

    function clearFeedback() {
        feedback.textContent = '';
        feedback.className = 'field-feedback';
        input.classList.remove('input-error');
    }

    editBtn.addEventListener('click', openEdit);
    cancelBtn.addEventListener('click', closeEdit);

    // Enter to save, Escape to cancel
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter')  { e.preventDefault(); saveUsername(); }
        if (e.key === 'Escape') { closeEdit(); }
    });

    saveBtn.addEventListener('click', saveUsername);

    function saveUsername() {
        const newVal = input.value.trim();
        clearFeedback();

        if (!newVal) {
            setFeedback('O nome de utilizador não pode estar vazio.', 'error');
            return;
        }
        if (newVal.length < 3) {
            setFeedback('Mínimo 3 caracteres.', 'error');
            return;
        }
        if (newVal === display.textContent.trim()) {
            closeEdit();
            return;
        }
        if (!/^[\w.@+-]+$/.test(newVal)) {
            setFeedback('Apenas letras, números e os caracteres @ . + - _ são permitidos.', 'error');
            return;
        }

        saveBtn.disabled = true;
        saveBtn.textContent = 'A guardar…';

        const fd = new FormData();
        fd.append('username', newVal);
        fd.append('csrfmiddlewaretoken', getCsrf());

        fetch('/conta/atualizar-username/', {
            method: 'POST',
            body: fd,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                display.textContent = newVal;
                if (sidebarDisplay) sidebarDisplay.textContent = newVal;
                closeEdit();
                showToast('Nome de utilizador atualizado!', 'success');
            } else {
                setFeedback(data.error || 'Erro ao guardar.', 'error');
            }
        })
        .catch(() => setFeedback('Erro de ligação. Tenta novamente.', 'error'))
        .finally(() => {
            saveBtn.disabled = false;
            saveBtn.textContent = 'Guardar';
        });
    }

    function setFeedback(msg, type) {
        feedback.textContent = msg;
        feedback.className = 'field-feedback ' + type;
        if (type === 'error') input.classList.add('input-error');
    }
}

/* ==========================================
   Password Modal
   ========================================== */
function initPasswordModal() {
    const modal        = document.getElementById('password-modal');
    const submitBtn    = document.getElementById('pw-submit-btn');
    const currentInput = document.getElementById('pw-current');
    const newInput     = document.getElementById('pw-new');
    const confirmInput = document.getElementById('pw-confirm');
    const errorEl      = document.getElementById('pw-error');
    const successEl    = document.getElementById('pw-success');
    const formState    = document.getElementById('pw-form-state');
    const strengthFill = document.getElementById('pw-strength-fill');
    const strengthLabel= document.getElementById('pw-strength-label');
    const matchHint    = document.getElementById('pw-match-hint');

    if (!modal) return;

    // Password visibility toggles
    document.querySelectorAll('.pw-toggle').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;
            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';
            // Swap eye icon slightly
            this.style.color = isHidden ? 'var(--primary)' : '';
        });
    });

    // Strength checker
    if (newInput) {
        newInput.addEventListener('input', function () {
            checkStrength(this.value);
            checkMatch();
        });
    }

    if (confirmInput) {
        confirmInput.addEventListener('input', checkMatch);
    }

    function checkStrength(val) {
        const rules = {
            length: val.length >= 8,
            upper:  /[A-Z]/.test(val),
            number: /[0-9]/.test(val),
        };

        // Update requirement items
        Object.entries(rules).forEach(([rule, met]) => {
            const el = document.querySelector(`[data-rule="${rule}"]`);
            if (el) el.classList.toggle('met', met);
        });

        const score = Object.values(rules).filter(Boolean).length;
        const levels = [
            { label: '',          color: '',                     width: '0%'   },
            { label: 'Fraca',     color: 'var(--error-text)',    width: '33%'  },
            { label: 'Razoável',  color: '#d97706',              width: '66%'  },
            { label: 'Forte',     color: 'var(--success-text)',  width: '100%' },
        ];
        const lvl = val.length === 0 ? levels[0] : levels[score] || levels[1];
        strengthFill.style.width           = lvl.width;
        strengthFill.style.backgroundColor = lvl.color;
        strengthLabel.textContent          = lvl.label;
        strengthLabel.style.color          = lvl.color;
    }

    function checkMatch() {
        const nv = newInput.value;
        const cv = confirmInput.value;
        if (!cv) { matchHint.textContent = ''; matchHint.className = 'pw-match-hint'; return; }
        if (nv === cv) {
            matchHint.textContent = '✓ As palavras-passe coincidem';
            matchHint.className   = 'pw-match-hint match';
        } else {
            matchHint.textContent = '✗ As palavras-passe não coincidem';
            matchHint.className   = 'pw-match-hint no-match';
        }
    }

    // Reset modal state when it opens
    modal.addEventListener('transitionend', function () {
        if (!modal.classList.contains('active')) resetPasswordForm();
    });

    function resetPasswordForm() {
        if (currentInput)  currentInput.value  = '';
        if (newInput)      newInput.value       = '';
        if (confirmInput)  confirmInput.value   = '';
        if (errorEl)       { errorEl.style.display = 'none'; errorEl.textContent = ''; }
        if (successEl)     successEl.style.display  = 'none';
        if (formState)     formState.style.display  = '';
        if (strengthFill)  { strengthFill.style.width = '0%'; strengthFill.style.backgroundColor = ''; }
        if (strengthLabel) { strengthLabel.textContent = ''; }
        if (matchHint)     { matchHint.textContent = ''; matchHint.className = 'pw-match-hint'; }
        document.querySelectorAll('.req-item').forEach(el => el.classList.remove('met'));
        document.querySelectorAll('.pw-input').forEach(el => el.classList.remove('input-error'));
        document.querySelectorAll('.pw-toggle').forEach(btn => {
            const input = document.getElementById(btn.dataset.target);
            if (input) input.type = 'password';
            btn.style.color = '';
        });
    }

    // Submit
    if (submitBtn) {
        submitBtn.addEventListener('click', function () {
            errorEl.style.display = 'none';
            errorEl.textContent = '';
            document.querySelectorAll('.pw-input').forEach(el => el.classList.remove('input-error'));

            const current = currentInput.value;
            const newPw   = newInput.value;
            const confirm = confirmInput.value;

            if (!current) {
                showPwError('Insere a tua palavra-passe atual.', currentInput); return;
            }
            if (newPw.length < 8) {
                showPwError('A nova palavra-passe deve ter pelo menos 8 caracteres.', newInput); return;
            }
            if (!/[A-Z]/.test(newPw)) {
                showPwError('A nova palavra-passe deve ter pelo menos uma letra maiúscula.', newInput); return;
            }
            if (!/[0-9]/.test(newPw)) {
                showPwError('A nova palavra-passe deve conter pelo menos um número.', newInput); return;
            }
            if (newPw !== confirm) {
                showPwError('As palavras-passe não coincidem.', confirmInput); return;
            }

            submitBtn.disabled = true;
            submitBtn.textContent = 'A alterar…';

            const fd = new FormData();
            fd.append('current_password', current);
            fd.append('new_password', newPw);
            fd.append('csrfmiddlewaretoken', getCsrf());

            fetch('/conta/alterar-password/', {
                method: 'POST',
                body: fd,
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    formState.style.display = 'none';
                    successEl.style.display = 'block';
                    // Auto-close after 2.5 s
                    setTimeout(() => {
                        const overlay = document.getElementById('password-modal');
                        if (overlay) {
                            overlay.classList.remove('active');
                            document.body.style.overflow = '';
                        }
                    }, 2500);
                } else {
                    showPwError(data.error || 'Erro ao alterar a palavra-passe.');
                }
            })
            .catch(() => showPwError('Erro de ligação. Tenta novamente.'))
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Alterar Palavra-passe';
            });
        });
    }

    function showPwError(msg, inputEl) {
        errorEl.textContent = msg;
        errorEl.style.display = 'block';
        if (inputEl) inputEl.classList.add('input-error');
    }
}

/* ==========================================
   Toast Notifications
   ========================================== */
function showToast(message, type = 'success') {
    // Remove existing toast if any
    const existing = document.querySelector('.account-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `account-toast account-toast--${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger enter animation
    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('account-toast--visible'));
    });

    setTimeout(() => {
        toast.classList.remove('account-toast--visible');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }, 3000);
}

/* ==========================================
   Utility: get CSRF token
   ========================================== */
function getCsrf() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.trim().split('=')[1] : '';
}