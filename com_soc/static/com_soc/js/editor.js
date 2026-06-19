function initEditorPage() {
    const deleteModal = document.getElementById('delete-modal');
    const aiEvalModal = document.getElementById('ai-eval-modal');
    if (!deleteModal) return;

    let pendingDeleteId = null;

    // -----------------------------------------------------------------------
    // Accept
    // -----------------------------------------------------------------------
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

    // -----------------------------------------------------------------------
    // Edit
    // -----------------------------------------------------------------------
    document.querySelectorAll('.editor-btn--edit').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.dataset.id;

            fetch(`/com_soc/noticia/${id}/json/`)
                .then(r => r.json())
                .then(data => {
                    const form = document.getElementById('news-create-form');
                    const modal = document.getElementById('add-news-modal');

                    document.getElementById('news-create-titulo').value = data.titulo;
                    document.getElementById('news-create-corpo').value = data.corpo_texto;

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

                    document.querySelectorAll('.news-access-btn').forEach(b => {
                        b.classList.toggle('active', b.dataset.value === data.acesso);
                    });
                    const acesoInput = document.getElementById('nc-acesso');
                    if (acesoInput) acesoInput.value = data.acesso;

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

                    form.action = `/com_soc/noticia/${id}/editar/`;
                    openModal(modal);
                });
        });
    });

    // -----------------------------------------------------------------------
    // Delete — open modal
    // -----------------------------------------------------------------------
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

    // -----------------------------------------------------------------------
    // AI Evaluation badge — open detail modal
    // -----------------------------------------------------------------------
    document.querySelectorAll('.ai-risk-badge').forEach(badge => {
        badge.addEventListener('click', () => {
            let evaluation;
            try {
                evaluation = JSON.parse(badge.dataset.evaluation);
            } catch {
                return;
            }

            const content = document.getElementById('ai-eval-content');
            const riskLevel = evaluation.risk_level || 'unknown';

            const scoreBar = (label, score) => `
                <div class="ai-eval-score-row">
                    <div class="ai-eval-score-header">
                        <span class="ai-eval-score-label">${label}</span>
                        <span class="ai-eval-score-value">${score}<span class="ai-eval-score-max">/100</span></span>
                    </div>
                    <div class="ai-eval-bar">
                        <div class="ai-eval-bar-fill" style="width: ${score}%; --bar-score: ${score};"></div>
                    </div>
                </div>`;

            const reasons = (evaluation.reasons || [])
                .map(r => `<li>${r}</li>`)
                .join('');

            content.innerHTML = `
                <div class="ai-eval-risk-header">
                    <span class="ai-risk-badge risk-${riskLevel} ai-risk-badge--lg">
                        ${riskLevel.toUpperCase()}
                    </span>
                </div>

                <div class="ai-eval-scores">
                    ${scoreBar('Probabilidade de Fake', evaluation.fake_score ?? '—')}
                    ${scoreBar('Conteúdo Abusivo', evaluation.abusive_score ?? '—')}
                </div>

                ${reasons ? `
                <div class="ai-eval-section">
                    <h3 class="ai-eval-section-title">Sinais Detetados</h3>
                    <ul class="ai-eval-reasons">${reasons}</ul>
                </div>` : ''}

                ${evaluation.recommendation ? `
                <div class="ai-eval-section">
                    <h3 class="ai-eval-section-title">Recomendação</h3>
                    <p class="ai-eval-recommendation">${evaluation.recommendation}</p>
                </div>` : ''}
            `;

            openModal(aiEvalModal);
        });
    });

    // -----------------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------------
    function getCsrf() {
        return document.cookie.split('; ')
            .find(r => r.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }
}