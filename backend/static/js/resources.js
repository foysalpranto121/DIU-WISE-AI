/* ============================================
   RESOURCE LIBRARY — Interactive Logic
   ============================================ */
document.addEventListener('DOMContentLoaded', () => {
    // --- Tab Switching ---
    const tabs = document.querySelectorAll('.resource-tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;

            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.dataset.tab === targetTab) {
                    content.classList.add('active');
                }
            });

            // Update search results for new tab
            filterResources();
        });
    });

    // --- Category Chip Filtering ---
    const categoryChips = document.querySelectorAll('.category-chip');
    categoryChips.forEach(chip => {
        chip.addEventListener('click', () => {
            categoryChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            filterResources();
        });
    });

    // --- Search ---
    const searchInput = document.getElementById('resource-search-input');
    const searchCount = document.getElementById('search-results-count');
    let searchTimeout;

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(filterResources, 250);
        });
    }

    function filterResources() {
        const query = (searchInput ? searchInput.value : '').toLowerCase().trim();
        const activeCategory = document.querySelector('.category-chip.active');
        const category = activeCategory ? activeCategory.dataset.category : 'all';
        const activeTab = document.querySelector('.resource-tab.active');
        const tab = activeTab ? activeTab.dataset.tab : 'all';

        let totalVisible = 0;

        // Get all resource cards across all tab panels
        const allCards = document.querySelectorAll('.resource-card[data-searchable]');

        allCards.forEach(card => {
            const cardTab = card.dataset.type;
            const cardCategory = card.dataset.category;
            const cardTitle = (card.dataset.title || '').toLowerCase();
            const cardSummary = (card.dataset.summary || '').toLowerCase();

            let matchesTab = (tab === 'all') || (cardTab === tab);
            let matchesCategory = (category === 'all') || (cardCategory === category);
            let matchesSearch = !query || cardTitle.includes(query) || cardSummary.includes(query) || cardCategory.toLowerCase().includes(query);

            if (matchesTab && matchesCategory && matchesSearch) {
                card.style.display = '';
                totalVisible++;
            } else {
                card.style.display = 'none';
            }
        });

        // Show/hide featured sections based on visible featured cards
        document.querySelectorAll('.featured-section').forEach(section => {
            const visibleFeatured = section.querySelectorAll('.resource-card[data-searchable]:not([style*="display: none"])');
            section.style.display = visibleFeatured.length > 0 ? '' : 'none';
        });

        // Show/hide empty states
        tabContents.forEach(content => {
            const visibleCards = content.querySelectorAll('.resource-card[data-searchable]:not([style*="display: none"])');
            const emptyState = content.querySelector('.empty-state');
            if (emptyState) {
                emptyState.style.display = visibleCards.length === 0 ? 'flex' : 'none';
            }
        });

        // Update count
        if (searchCount) {
            if (query || category !== 'all') {
                searchCount.textContent = `${totalVisible} found`;
                searchCount.style.display = '';
            } else {
                searchCount.style.display = 'none';
            }
        }
    }

    // --- Modal System ---
    const modalOverlay = document.getElementById('resource-modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalMeta = document.getElementById('modal-meta');
    const modalBody = document.getElementById('modal-body');
    const modalCloseBtn = document.getElementById('modal-close-btn');

    // Open modal on card click
    document.querySelectorAll('.resource-card[data-searchable]').forEach(card => {
        card.addEventListener('click', (e) => {
            // Don't open modal if clicking an external link
            if (e.target.closest('a[href]')) return;

            const resourceId = card.dataset.id;
            const type = card.dataset.type;
            openResourceModal(resourceId, type, card);
        });
    });

    function openResourceModal(resourceId, type, card) {
        const title = card.dataset.title;
        const author = card.dataset.author || '';
        const readTime = card.dataset.readtime || '';
        const duration = card.dataset.duration || '';
        const date = card.dataset.date || '';
        const category = card.dataset.category || '';

        // Set title
        modalTitle.textContent = title;

        // Build meta info
        let metaHTML = '';
        if (author) metaHTML += `<span class="modal-meta-item">✍️ ${author}</span>`;
        if (readTime) metaHTML += `<span class="modal-meta-item">⏱️ ${readTime}</span>`;
        if (duration) metaHTML += `<span class="modal-meta-item">🎬 ${duration}</span>`;
        if (date) metaHTML += `<span class="modal-meta-item">📅 ${formatDate(date)}</span>`;
        if (category) metaHTML += `<span class="modal-meta-item card-category">${category}</span>`;
        modalMeta.innerHTML = metaHTML;

        // Build body content
        const contentEl = card.querySelector('.resource-full-content');
        const youtubeId = card.dataset.youtube;

        let bodyHTML = '';

        if (youtubeId && (type === 'video' || type === 'speech')) {
            bodyHTML += `
                <div class="video-embed-wrapper">
                    <iframe 
                        src="https://www.youtube.com/embed/${youtubeId}?autoplay=1&rel=0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen
                        title="${title}">
                    </iframe>
                </div>`;
        }

        if (contentEl) {
            bodyHTML += `<div class="document-content">${contentEl.innerHTML}</div>`;
        }

        modalBody.innerHTML = bodyHTML;

        // Show modal
        modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modalOverlay.classList.remove('active');
        document.body.style.overflow = '';
        // Stop any playing videos
        const iframes = modalBody.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            iframe.src = '';
        });
    }

    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', closeModal);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) closeModal();
        });
    }

    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // --- Utility ---
    function formatDate(dateStr) {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        } catch {
            return dateStr;
        }
    }

    // --- Initialize ---
    filterResources();
});
