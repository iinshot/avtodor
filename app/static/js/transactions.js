let currentPage = 1;
const pageSize = 50;
let totalItems = 0;
let currentFilters = {};

function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return dateString;
    }
}

// Управление индикатором загрузки
function showLoading(show) {
    const loading = document.getElementById('loadingIndicator');
    const table = document.getElementById('transactionsTable');

    if (loading && table) {
        if (show) {
            loading.style.display = 'block';
            table.style.opacity = '0.5';
        } else {
            loading.style.display = 'none';
            table.style.opacity = '1';
        }
    }
}

// Показать ошибку
function showError(message) {
    const tbody = document.getElementById('transactionsTable');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4 text-danger">
                    <i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>
                    ${message}
                </td>
            </tr>
        `;
    }
}

// Загрузка статистики
async function loadStats() {
    try {
        const response = await fetch('/transactions/stats');
        const stats = await response.json();

        // Безопасное обновление элементов
        const elements = {
            'totalTransactions': stats.total?.toLocaleString() || '0',
            'todayTransactions': stats.today?.toLocaleString() || '0',
            'todayTotalPaid': (stats.today_total_paid || 0).toLocaleString() + ' ₽'
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        });

    } catch (error) {
        console.error('Ошибка загрузки статистики:', error);
    }
}

// Отображение транзакций в таблице
function displayTransactions(transactions) {
    const tbody = document.getElementById('transactionsTable');
    if (!tbody) return;

    if (!transactions || transactions.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="fas fa-inbox fa-2x mb-2"></i><br>
                    Нет данных для отображения
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = transactions.map(transaction => `
        <tr>
            <td>
                <div class="fw-bold">${formatDateTime(transaction.occurred_at)}</div>
            </td>
            <td>
                <span class="badge bg-primary">${transaction.PVP_code || "—"}</span>
            </td>
            <td>
                <code class="text-dark">${transaction.transponder || '—'}</code>
            </td>
            <td>
                ${transaction.base_tariff ? `
                    <span class="fw-bold">${transaction.base_tariff.toLocaleString()} ₽</span>
                ` : '<span class="text-muted">—</span>'}
            </td>
            <td>
                ${transaction.discount ? `
                    <span class="badge bg-success">${transaction.discount}%</span>
                ` : '<span class="text-muted">—</span>'}
            </td>
            <td>
                ${transaction.paid ? `
                    <span class="fw-bold text-success">${transaction.paid.toLocaleString()} ₽</span>
                ` : '<span class="text-muted">—</span>'}
            </td>
        </tr>
    `).join('');
}

// Обновление пагинации
function updatePagination(data) {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage * pageSize >= totalItems;
}

// Обновление текста
function updateShowingText(data) {
    const showingElement = document.getElementById('showingText');
    if (showingElement) {
        const start = ((currentPage - 1) * pageSize) + 1;
        const end = Math.min(currentPage * pageSize, totalItems);
        const text = `Показано ${start}-${end} из ${totalItems.toLocaleString()}`;
        showingElement.textContent = text;
    }
}

// Загрузка транзакций
async function loadTransactions(page = 1) {
    currentPage = page;

    showLoading(true);

    try {
        const params = new URLSearchParams({
            page: currentPage.toString(),
            page_size: pageSize.toString(),
            ...currentFilters
        });

        const response = await fetch(`/transactions/info?${params.toString()}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        totalItems = data.total || 0;
        displayTransactions(data.items || []);
        updatePagination(data);
        updateShowingText(data);

    } catch (error) {
        console.error('Ошибка загрузки транзакций:', error);
        showError('Ошибка загрузки данных: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Применение фильтров
function applyFilters() {
    currentFilters = {};

    const sourceFilter = document.getElementById('sourceFilter');
    const transponderFilter = document.getElementById('transponderFilter');
    const dateFromFilter = document.getElementById('dateFromFilter');
    const dateToFilter = document.getElementById('dateToFilter');

    if (sourceFilter && sourceFilter.value) currentFilters.source = sourceFilter.value;
    if (transponderFilter && transponderFilter.value) currentFilters.transponder = transponderFilter.value;
    if (dateFromFilter && dateFromFilter.value) currentFilters.date_from = dateFromFilter.value;
    if (dateToFilter && dateToFilter.value) currentFilters.date_to = dateToFilter.value;

    loadTransactions(1);
}

// Навигация по страницам
function prevPage() {
    if (currentPage > 1) {
        loadTransactions(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage * pageSize < totalItems) {
        loadTransactions(currentPage + 1);
    }
}

// Инициализация при загрузке страницы
function initTransactionsPage() {
    if (document.getElementById('transactionsTable')) {
        console.log('Инициализация страницы транзакций...');
        loadTransactions();
        loadStats();

        const dateToFilter = document.getElementById('dateToFilter');
        if (dateToFilter) {
            const today = new Date().toISOString().split('T')[0];
            dateToFilter.value = today;
        }

        const dateFromFilter = document.getElementById('dateFromFilter');
        if (dateFromFilter) {
            const weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            dateFromFilter.value = weekAgo.toISOString().split('T')[0];
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {

    const refreshBtn = document.getElementById("refreshBtn");
    const sourceFilter = document.getElementById("sourceFilter");

    if (!refreshBtn || !sourceFilter) return;

    refreshBtn.addEventListener("click", () => loadTransactions(1));
    sourceFilter.addEventListener("change", applyFilters);

    initTransactionsPage();
});
