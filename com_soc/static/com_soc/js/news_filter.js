/* ==========================================
   News Filter — shared by home.html & subscriber.html
   Save to: com_soc/static/com_soc/js/news_filter.js
   ========================================== */
 
document.addEventListener('DOMContentLoaded', function () {
 
    const form     = document.getElementById('news-filter-form');
    if (!form) return;
 
    const qInput   = document.getElementById('filter-q');
 
    // If the search box already has a value (restored by Django after reload),
    // refocus it and move the cursor to the end so the user can keep typing.
    if (qInput && qInput.value) {
        qInput.focus();
        const len = qInput.value.length;
        qInput.setSelectionRange(len, len);
    }
    const dateFrom = document.getElementById('filter-date-from');
    const dateTo   = document.getElementById('filter-date-to');
    const dateClear= document.getElementById('filter-date-clear');
    const clearAll = document.getElementById('filter-clear-all');
    const chips    = document.querySelectorAll('.news-filter-chip');
    const catInputs= [
        document.getElementById('filter-cat-1'),
        document.getElementById('filter-cat-2'),
        document.getElementById('filter-cat-3'),
    ];
 
    // Subscriber only — toggle is outside the form so we use a hidden input inside it
    const toggleRow       = document.getElementById('filter-toggle-row');
    const toggleHidden    = document.getElementById('filter-include-public-val');
 
    // ------------------------------------------------
    // Track selected categories from initial page load
    // ------------------------------------------------
    let selectedCats = [];
    chips.forEach(chip => {
        if (chip.classList.contains('active')) {
            selectedCats.push(chip.dataset.value);
        }
    });
 
    // ------------------------------------------------
    // Auto-submit with debounce for text input
    // ------------------------------------------------
    let debounceTimer;
    if (qInput) {
        qInput.addEventListener('input', function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(submitForm, 400);
        });
    }
 
    if (dateFrom) dateFrom.addEventListener('change', submitForm);
    if (dateTo)   dateTo.addEventListener('change',   submitForm);
 
    // ------------------------------------------------
    // Date clear button visibility + action
    // ------------------------------------------------
    function updateDateClear() {
        if (!dateClear) return;
        const hasDate = (dateFrom && dateFrom.value) || (dateTo && dateTo.value);
        dateClear.classList.toggle('visible', !!hasDate);
    }
 
    if (dateClear) {
        dateClear.addEventListener('click', function () {
            if (dateFrom) dateFrom.value = '';
            if (dateTo)   dateTo.value   = '';
            updateDateClear();
            submitForm();
        });
    }
 
    if (dateFrom) dateFrom.addEventListener('change', updateDateClear);
    if (dateTo)   dateTo.addEventListener('change',   updateDateClear);
 
    // ------------------------------------------------
    // Category chips
    // ------------------------------------------------
    chips.forEach(chip => {
        chip.addEventListener('click', function () {
            const val = this.dataset.value;
 
            if (this.classList.contains('active')) {
                selectedCats = selectedCats.filter(v => v !== val);
                this.classList.remove('active');
            } else {
                if (selectedCats.length >= 3) return;
                selectedCats.push(val);
                this.classList.add('active');
            }
 
            chips.forEach(c => {
                if (!c.classList.contains('active')) {
                    c.classList.toggle('disabled', selectedCats.length >= 3);
                }
            });
 
            catInputs.forEach((input, i) => {
                if (input) input.value = selectedCats[i] || '';
            });
 
            submitForm();
        });
    });
 
    // ------------------------------------------------
    // Include public toggle (subscriber page only)
    // The toggle div sits in the sidebar outside the form.
    // We sync its state to a hidden input inside the form.
    // ------------------------------------------------
    if (toggleRow && toggleHidden) {
        toggleRow.addEventListener('click', function () {
            const isActive = toggleRow.classList.contains('checked');
            toggleRow.classList.toggle('checked', !isActive);
            toggleHidden.value = isActive ? '' : '1';
            submitForm();
        });
    }
 
    // ------------------------------------------------
    // Clear all filters
    // ------------------------------------------------
    if (clearAll) {
        clearAll.addEventListener('click', function () {
            if (qInput)   qInput.value   = '';
            if (dateFrom) dateFrom.value = '';
            if (dateTo)   dateTo.value   = '';
 
            selectedCats = [];
            chips.forEach(c => c.classList.remove('active', 'disabled'));
            catInputs.forEach(i => { if (i) i.value = ''; });
 
            if (toggleRow)    toggleRow.classList.remove('checked');
            if (toggleHidden) toggleHidden.value = '';
 
            updateDateClear();
            submitForm();
        });
    }
 
    // ------------------------------------------------
    // Submit — always resets to page 1
    // ------------------------------------------------
    function submitForm() {
        const existingPage = form.querySelector('input[name="page"]');
        if (existingPage) existingPage.remove();
        form.submit();
    }
 
});
 