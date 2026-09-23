// A long example opens at its first lines, so it doesn't bury the prose
// around it. Diagrams are text blocks and always show whole.
document.addEventListener('DOMContentLoaded', () => {
    const selector = 'div[class^="highlight-"]:not(.highlight-text) > .highlight > pre';
    for (const pre of document.querySelectorAll(selector)) {
        const lines = pre.textContent.split('\n').length - 1;
        if (lines <= 30)
            continue;
        const block = pre.parentElement;
        const button = document.createElement('button');
        button.className = 'expand';
        button.textContent = `Show all ${lines} lines`;
        button.addEventListener('click', () => {
            block.classList.remove('collapsed');
            button.remove();
        });
        block.classList.add('collapsed');
        block.append(button);
    }
});
