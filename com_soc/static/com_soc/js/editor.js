function initEditorPage() {
    const deleteModal = document.getElementById('delete-modal');
    if (!deleteModal) return;

    let pendingDeleteId = null;

    // Accept
    document.querySelectorAll('.editor-btn--accept').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;
            fetch(`/com_soc/noticia/${id}/aceitar/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) window.location.reload();
            });
        });
    });

    //edit
    document.querySelectorAll('.editor-btn--edit').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;

            fetch(`/com_soc/noticia/${id}/json/`)
                .then(r => r.json())
                .then(data => {
                    const form = document.getElementById('news-create-form');
                    const modal = document.getElementById('add-news-modal');
                    

                    // Reset first so we start clean
                    // Call resetForm from dashboard.js — it's in the same scope
                    // so we need a small workaround — see below

                    // Populate title and body
                    document.getElementById('news-create-titulo').value = data.titulo;
                    document.getElementById('news-create-corpo').value = data.corpo_texto;

                    // Populate categories
                    const chips = document.querySelectorAll('.news-chip');
                    const catInputs = ['nc-cat-1', 'nc-cat-2', 'nc-cat-3']
                        .map(id => document.getElementById(id));
                    const cats = [data.categoria_1, data.categoria_2, data.categoria_3].filter(Boolean);
                    window.setEditCategories(cats);

                    chips.forEach(chip => {
                        const isSelected = cats.includes(chip.dataset.value);
                        chip.classList.toggle('selected', isSelected);
                        chip.classList.toggle('disabled', !isSelected && cats.length >= 3);
                    });
                    catInputs.forEach((input, i) => {
                        if (input) input.value = cats[i] || '';
                    });

                    // Populate acesso toggle
                    document.querySelectorAll('.news-access-btn').forEach(b => {
                        b.classList.toggle('active', b.dataset.value === data.acesso);
                    });
                    const acesoInput = document.getElementById('nc-acesso');
                    if (acesoInput) acesoInput.value = data.acesso;

                    // Images — show existing ones as previews
                    const previewsContainer = document.getElementById('news-create-previews');
                    previewsContainer.innerHTML = '';
                    if (data.imagens && data.imagens.length > 0) {
                        data.imagens.forEach(img => {
                            const wrap = document.createElement('div');
                            wrap.className = 'news-preview-item';
                            const image = document.createElement('img');
                            image.src = img.url;
                            image.alt = 'imagem';
                            wrap.appendChild(image);
                            previewsContainer.appendChild(wrap);
                        });
                    }

                    // Change form action to edit endpoint
                    form.action = `/com_soc/noticia/${id}/editar/`;

                    openModal(modal);
                });
        });
    });

    // Delete — open modal
    document.querySelectorAll('.editor-btn--delete').forEach(btn => {
        btn.addEventListener('click', () => {
            pendingDeleteId = btn.dataset.id;
            openModal(deleteModal);
        });
    });

    // Delete — confirm
    document.getElementById('delete-confirm-btn').addEventListener('click', () => {
        if (!pendingDeleteId) return;
        fetch(`/com_soc/noticia/${pendingDeleteId}/eliminar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrf(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                closeModal(deleteModal);
                document.querySelector(`.editor-row[data-id="${pendingDeleteId}"]`)?.remove();
                pendingDeleteId = null;
            }
        });
    });

    function getCsrf() {
        return document.cookie.split('; ')
            .find(r => r.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }
}