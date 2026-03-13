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

async function loadFilters() {
    try {
        const data = await fetchAPI('/api/filters');
        populateSelect('filterCategory', data.categories, 'Todas las categorías');
        populateSelect('filterDiscipline', data.disciplines, 'Todas las disciplinas');

        const regionSelect = document.getElementById('filterRegion');
        regionSelect.innerHTML = '<option value="">Toda España</option>';
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

function populateSelect(id, items, defaultLabel) {
    const select = document.getElementById(id);
    select.innerHTML = `<option value="">${defaultLabel}</option>`;
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.value;
        opt.textContent = item.label;
        select.appendChild(opt);
    });
}

async function loadOpportunities() {
    const resultsEl = document.getElementById('results');
    resultsEl.innerHTML = '<div class="loading">Buscando oportunidades...</div>';

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
        document.getElementById('statsTotal').textContent =
            `${data.total} oportunidad${data.total !== 1 ? 'es' : ''} encontrada${data.total !== 1 ? 's' : ''}`;
    } catch (e) {
        resultsEl.innerHTML = '<div class="empty-state"><h3>Error al cargar</h3><p>Inténtalo de nuevo más tarde.</p></div>';
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

function formatDate(isoDate) {
    if (!isoDate) return null;
    const d = new Date(isoDate);
    return d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
}

function deadlineClass(isoDate) {
    if (!isoDate) return '';
    const diff = (new Date(isoDate) - new Date()) / (1000 * 60 * 60 * 24);
    if (diff < 7) return 'deadline--urgent';
    if (diff < 30) return 'deadline--soon';
    return 'deadline--ok';
}

function deadlineLabel(isoDate) {
    if (!isoDate) return '';
    const diff = Math.ceil((new Date(isoDate) - new Date()) / (1000 * 60 * 60 * 24));
    if (diff < 0) return 'Finalizado';
    if (diff === 0) return 'Último día';
    if (diff === 1) return 'Mañana';
    if (diff < 7) return `${diff} días`;
    if (diff < 30) return `${Math.ceil(diff / 7)} semanas`;
    return formatDate(isoDate);
}

function renderResults(data) {
    const el = document.getElementById('results');

    if (!data.results.length) {
        el.innerHTML = `
            <div class="empty-state">
                <h3>No se encontraron oportunidades</h3>
                <p>Prueba con otros filtros o términos de búsqueda.</p>
            </div>`;
        return;
    }

    el.innerHTML = data.results.map(opp => `
        <article class="opp-card">
            <div class="opp-card__header">
                <h2 class="opp-card__title">
                    <a href="${opp.source_url}" target="_blank" rel="noopener">${escapeHtml(opp.title)}</a>
                </h2>
                ${opp.deadline ? `<span class="opp-card__deadline ${deadlineClass(opp.deadline)}">${deadlineLabel(opp.deadline)}</span>` : ''}
            </div>
            <div class="opp-card__meta">
                ${opp.category ? `<span class="opp-card__tag">${CATEGORY_LABELS[opp.category] || opp.category}</span>` : ''}
                ${opp.region ? `<span>${opp.region}</span>` : ''}
                ${opp.organization ? `<span>${escapeHtml(opp.organization)}</span>` : ''}
                ${opp.funding_amount ? `<span>${escapeHtml(opp.funding_amount)}</span>` : ''}
            </div>
            ${opp.description ? `<p class="opp-card__description">${escapeHtml(opp.description.substring(0, 200))}${opp.description.length > 200 ? '...' : ''}</p>` : ''}
            <p class="opp-card__source">Fuente: ${escapeHtml(opp.source_name)}</p>
        </article>
    `).join('');
}

function renderPagination(data) {
    const el = document.getElementById('pagination');
    if (data.pages <= 1) {
        el.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button ${data.page <= 1 ? 'disabled' : ''} onclick="goToPage(${data.page - 1})">Anterior</button>`;

    const start = Math.max(1, data.page - 2);
    const end = Math.min(data.pages, data.page + 2);

    for (let i = start; i <= end; i++) {
        html += `<button class="${i === data.page ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }

    html += `<button ${data.page >= data.pages ? 'disabled' : ''} onclick="goToPage(${data.page + 1})">Siguiente</button>`;
    el.innerHTML = html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- Actions ---

function goToPage(page) {
    state.page = page;
    loadOpportunities();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function doSearch() {
    state.query = document.getElementById('searchInput').value.trim();
    state.category = document.getElementById('filterCategory').value;
    state.discipline = document.getElementById('filterDiscipline').value;
    state.region = document.getElementById('filterRegion').value;
    state.activeOnly = document.getElementById('filterActive').checked;
    state.page = 1;
    loadOpportunities();
}

// --- Init ---

document.addEventListener('DOMContentLoaded', () => {
    loadFilters();
    loadOpportunities();

    document.getElementById('searchBtn').addEventListener('click', doSearch);
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    });

    // Auto-search on filter change
    ['filterCategory', 'filterDiscipline', 'filterRegion', 'filterActive'].forEach(id => {
        document.getElementById(id).addEventListener('change', doSearch);
    });
});
