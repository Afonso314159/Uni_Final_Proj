document.addEventListener('DOMContentLoaded', () => {
 
    // -----------------------------------------------------------------------
    // Generic toggle handler — makes one button active at a time within
    // each .settings-toggle group. Functionality wired up later.
    // -----------------------------------------------------------------------
    document.querySelectorAll('.settings-toggle').forEach(group => {
        group.querySelectorAll('.settings-toggle-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                group.querySelectorAll('.settings-toggle-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    });
 
    // -----------------------------------------------------------------------
    // AI thresholds save — placeholder, functionality comes later
    // -----------------------------------------------------------------------
    document.getElementById('save-ai-thresholds')?.addEventListener('click', () => {
        // TODO: POST values to backend
        console.log('Save AI thresholds — not yet implemented');
    });
 
});
 