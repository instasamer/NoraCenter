/**
 * NoraCenter - Frontend application
 */

const state = {
    page: 1,
    query: '',
    category: '',
    discipline: '',
    region: '',
    activeOnly: true,
};

// --- API ---

async function fetchAPI(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// --- Init ---

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadFilters();
    loadOpportunities();

    // Search
    document.getElementById('searchBtn').addEventListener('click', doSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    });

    // Region select
    document.getElementById('filterRegion').addEventListener('change', doSearch);

    // Active toggle
    document.getElementById('filterActive').addEventListener('change', doSearch);

    // Clear filters
    document.getElementById('clearFilters').addEventListener('click', clearFilters);

    // Mobile filter toggle
    document.getElementById('mobileFilterBtn').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });

    // Modal
    document.getElementById('modalClose').addEventListener('click', closeModal);
    document.getElementById('modalOverlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
});

// --- Stats ---

async function loadStats() {
    try {
        const data = await fetchAPI('/api/stats');
        document.querySelector('#statTotal .stat-item__number').textContent =
            data.total_opportunities.toLocaleString('es-ES');
        document.querySelector('#statActive .stat-item__number').textContent =
            data.active_opportunities.toLocaleString('es-ES');
        document.querySelector('#statSources .stat-item__number').textContent =
            data.sources;
    } catch (e) {
        console.error('Error loading stats:', e);
    }
}

// --- Filters ---

async function loadFilters() {
    try {
        const data = await fetchAPI('/api/filters');
        renderChips('filterCategory', data.categories);
        renderChips('filterDiscipline', data.disciplines);

        const regionSelect = document.getElementById('filterRegion');
        data.regions.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r;
            opt.textContent = r;
            regionSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Error loading filters:', e);
    }
}

function renderChips(containerId, items) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    items.forEach(item => {
        const chip = document.createElement('button');
        chip.className = 'filter-chip';
        chip.textContent = item.label;
        chip.dataset.value = item.value;
        chip.addEventListener('click', () => {
            const wasActive = chip.classList.contains('active');
            // Deselect all in this group
            container.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            if (!wasActive) {
                chip.classList.add('active');
            }
            doSearch();
        });
        container.appendChild(chip);
    });
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    document.getElementById('filterRegion').value = '';
    document.getElementById('filterActive').checked = true;
    doSearch();
}

// --- Search & Load ---

function doSearch() {
    const activeCategory = document.querySelector('#filterCategory .filter-chip.active');
    const activeDiscipline = document.querySelector('#filterDiscipline .filter-chip.active');

    state.query = document.getElementById('searchInput').value.trim();
    state.category = activeCategory ? activeCategory.dataset.value : '';
    state.discipline = activeDiscipline ? activeDiscipline.dataset.value : '';
    state.region = document.getElementById('filterRegion').value;
    state.activeOnly = document.getElementById('filterActive').checked;
    state.page = 1;
    loadOpportunities();

    // Close mobile sidebar
    document.getElementById('sidebar').classList.remove('open');
}

async function loadOpportunities() {
    const resultsEl = document.getElementById('results');
    resultsEl.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <p>Buscando oportunidades...</p>
        </div>`;

    const params = new URLSearchParams({
        page: state.page,
        per_page: 20,
        active_only: state.activeOnly,
    });

    if (state.query) params.set('q', state.query);
    if (state.category) params.set('category', state.category);
    if (state.discipline) params.set('discipline', state.discipline);
    if (state.region) params.set('region', state.region);

    try {
        const data = await fetchAPI(`/api/opportunities?${params}`);
        renderResults(data);
        renderPagination(data);

        const count = data.total;
        document.getElementById('resultsCount').textContent =
            `${count.toLocaleString('es-ES')} oportunidad${count !== 1 ? 'es' : ''}`;
    } catch (e) {
        resultsEl.innerHTML = `
            <div class="empty-state">
                <div class="empty-state__icon">!</div>
                <h3>Error al cargar</h3>
                <p>No se pudieron cargar las oportunidades. Inténtalo de nuevo más tarde.</p>
            </div>`;
    }
}

// --- Rendering ---

const CATEGORY_LABELS = {
    beca: 'Beca',
    residencia: 'Residencia',
    subvencion: 'Subvención',
    convocatoria: 'Convocatoria',
    empleo: 'Empleo',
    premio: 'Premio',
    formacion: 'Formación',
    exposicion: 'Exposición',
    festival: 'Festival',
    otro: 'Otro',
};

const DISCIPLINE_LABELS = {
    artes_visuales: 'Artes Visuales',
    musica: 'Música',
    teatro: 'Teatro',
    danza: 'Danza',
    cine: 'Cine',
    literatura: 'Literatura',
    fotografia: 'Fotografía',
    diseno: 'Diseño',
    artes_digitales: 'Artes Digitales',
    multidisciplinar: 'Multidisciplinar',
    otro: 'Otro',
};

function formatDate(isoDate) {
    if (!isoDate) return null;
    const d = new Date(isoDate);
    return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });
}

function deadlineInfo(isoDate) {
    if (!isoDate) return { class: '', label: '' };
    const diff = Math.ceil((new Date(isoDate) - new Date()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return { class: 'badge--closed', label: 'Finalizado' };
    if (diff === 0) return { class: 'badge--urgent', label: 'Último día' };
    if (diff === 1) return { class: 'badge--urgent', label: 'Mañana' };
    if (diff < 7) return { class: 'badge--urgent', label: `${diff} días` };
    if (diff < 30) return { class: 'badge--soon', label: `${Math.ceil(diff / 7)} sem.` };
    return { class: 'badge--ok', label: formatDate(isoDate) };
}

function renderResults(data) {
    const el = document.getElementById('results');

    if (!data.results.length) {
        el.innerHTML = `
            <div class="empty-state">
                <div class="empty-state__icon">?</div>
                <h3>No se encontraron oportunidades</h3>
                <p>Prueba con otros filtros o términos de búsqueda.</p>
            </div>`;
        return;
    }

    el.innerHTML = data.results.map(opp => {
        const dl = deadlineInfo(opp.deadline);
        return `
        <article class="opp-card" onclick="openDetail(${opp.id})">
            <div class="opp-card__top">
                <h2 class="opp-card__title">${escapeHtml(opp.title)}</h2>
                ${dl.label ? `<span class="opp-card__badge ${dl.class}">${dl.label}</span>` : ''}
            </div>
            <div class="opp-card__meta">
                ${opp.category ? `<span class="meta-tag meta-tag--category">${CATEGORY_LABELS[opp.category] || opp.category}</span>` : ''}
                ${opp.discipline ? `<span class="meta-tag">${DISCIPLINE_LABELS[opp.discipline] || opp.discipline}</span>` : ''}
                ${opp.region ? `<span class="meta-tag">${escapeHtml(opp.region)}</span>` : ''}
            </div>
            ${opp.description ? `<p class="opp-card__desc">${escapeHtml(opp.description)}</p>` : ''}
            <div class="opp-card__footer">
                <span class="opp-card__source">Fuente: ${escapeHtml(opp.source_name)}</span>
                ${opp.funding_amount ? `<span>${escapeHtml(opp.funding_amount)}</span>` : ''}
            </div>
        </article>`;
    }).join('');
}

function renderPagination(data) {
    const el = document.getElementById('pagination');
    if (data.pages <= 1) {
        el.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button ${data.page <= 1 ? 'disabled' : ''} onclick="goToPage(${data.page - 1})">&#8592;</button>`;

    const start = Math.max(1, data.page - 2);
    const end = Math.min(data.pages, data.page + 2);

    if (start > 1) {
        html += `<button onclick="goToPage(1)">1</button>`;
        if (start > 2) html += `<button disabled>...</button>`;
    }

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === data.page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    if (end < data.pages) {
        if (end < data.pages - 1) html += `<button disabled>...</button>`;
        html += `<button onclick="goToPage(${data.pages})">${data.pages}</button>`;
    }

    html += `<button ${data.page >= data.pages ? 'disabled' : ''} onclick="goToPage(${data.page + 1})">&#8594;</button>`;
    el.innerHTML = html;
}

// --- Detail modal ---

async function openDetail(id) {
    try {
        const opp = await fetchAPI(`/api/opportunities/${id}`);
        if (opp.error) return;

        const dl = deadlineInfo(opp.deadline);

        document.getElementById('modalContent').innerHTML = `
            ${opp.category ? `<span class="modal__category">${CATEGORY_LABELS[opp.category] || opp.category}</span>` : ''}
            <h2 class="modal__title">${escapeHtml(opp.title)}</h2>

            <div class="modal__details">
                ${opp.organization ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Organización</span>
                    <span class="modal__detail-value">${escapeHtml(opp.organization)}</span>
                </div>` : ''}
                ${opp.region || opp.location ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Ubicación</span>
                    <span class="modal__detail-value">${escapeHtml(opp.location || opp.region)}</span>
                </div>` : ''}
                ${opp.deadline ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Plazo</span>
                    <span class="modal__detail-value">${formatDate(opp.deadline)} <span class="opp-card__badge ${dl.class}" style="font-size:0.7rem">${dl.label}</span></span>
                </div>` : ''}
                ${opp.discipline ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Disciplina</span>
                    <span class="modal__detail-value">${DISCIPLINE_LABELS[opp.discipline] || opp.discipline}</span>
                </div>` : ''}
                ${opp.funding_amount ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Dotación</span>
                    <span class="modal__detail-value">${escapeHtml(opp.funding_amount)}</span>
                </div>` : ''}
                ${opp.publication_date ? `
                <div class="modal__detail">
                    <span class="modal__detail-label">Publicado</span>
                    <span class="modal__detail-value">${formatDate(opp.publication_date)}</span>
                </div>` : ''}
            </div>

            ${opp.description ? `<p class="modal__description">${escapeHtml(opp.description)}</p>` : ''}

            <a href="${opp.source_url}" target="_blank" rel="noopener" class="modal__cta">
                Ver convocatoria completa &#8599;
            </a>
        `;

        document.getElementById('modalOverlay').classList.add('open');
        document.body.style.overflow = 'hidden';
    } catch (e) {
        console.error('Error loading detail:', e);
    }
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('open');
    document.body.style.overflow = '';
}

// --- Utils ---

function goToPage(page) {
    state.page = page;
    loadOpportunities();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
