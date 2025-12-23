// Идентификаторы элементов DOM
let tableId = "violationsTable";
let prevBtnId = "prevBtnViolation";
let nextBtnId = "nextBtnViolation";
let showingTextId = "showingText";
let apiUrl = "/violations/info";
let refreshBtnId = "refreshBtn";
let filterTriggerId = "sourceFilter";

// Состояние пагинации и фильтров
let currentPage = 1;
const pageSize = 50;
let totalItems = 0;
let currentFilters = {};

// Загружает статистику транзакций для дашборда
async function loadDashboardDataViolations() {
    try {
        const response = await fetch('/violations/stats');
        const data = await response.json();

        document.getElementById('monthViolations').textContent = data.month_violations;
        document.getElementById('todayViolations').textContent = data.today_violations;
        document.getElementById('totalViolations').textContent = data.total_violations;
        document.getElementById('monthPaidViolations').textContent = '₽ ' + data.sum_violations.toLocaleString();

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Форматирует дату в читаемый формат
function formatDateTime(dateString) {
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('ru-RU') + ' ' + date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch {
        return dateString;
    }
}

// Показывает/скрывает индикатор загрузки
function showLoading(show) {
    const loading = document.getElementById("loadingIndicator");
    const table = document.getElementById(tableId);
    if (loading) loading.style.display = show ? 'block' : 'none';
    if (table) table.style.opacity = show ? '0.5' : '1';
}

// Отображает сообщение об ошибке в таблице
function showError(message) {
    const tbody = document.getElementById(tableId);
    if (!tbody) return;
    tbody.innerHTML = `
        <tr>
            <td colspan="20" class="text-center py-4 text-danger">
                <i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>
                ${message}
            </td>
        </tr>
    `;
}

// Обновляет состояние кнопок пагинации
function updatePagination() {
    const prevBtn = document.getElementById(prevBtnId);
    const nextBtn = document.getElementById(nextBtnId);

    console.log('prevBtn found:', prevBtn); // 🔥 ДЕБАГ
    console.log('nextBtn found:', nextBtn); //

    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage * pageSize >= totalItems;
}

// Обновляет текст с информацией о показываемых записях
function updateShowingText() {
    const elem = document.getElementById(showingTextId);
    if (!elem) return;
    const start = totalItems === 0 ? 0 : ((currentPage - 1) * pageSize) + 1;
    const end = Math.min(currentPage * pageSize, totalItems);
    elem.textContent = `Показано ${start}-${end} из ${totalItems.toLocaleString()}`;
}

// Рендерит строки таблицы транзакций
function renderTable(items, formatDate) {
    const tbody = document.getElementById(tableId);
    if (!items.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">Нет данных</td></tr>`;
        return;
    }
    tbody.innerHTML = items.map(t => `
        <tr>
            <td>${formatDate(t.occurred_at)}</td>
            <td><span class="badge bg-primary">${t.PVP_code || "—"}</span></td>
            <td><code>${t.transponder || "—"}</code></td>
            <td>${t.base_tariff ? t.base_tariff.toLocaleString() + " ₽" : "—"}</td>
            <td>${t.discount ? `<span class="badge bg-success">${t.discount}%</span>` : "—"}</td>
            <td>${t.paid ? t.paid.toLocaleString() + " ₽" : "—"}</td>
        </tr>
    `).join('');
}

function initDateFilters() {
    const dateFromInput = document.getElementById("filterDateFrom");
    const dateToInput = document.getElementById("filterDateTo");

    if (dateFromInput) {
        dateFromInput.addEventListener("change", () => {
            // Если выбрана дата "от", но нет даты "до" - применяем фильтр
            if (dateFromInput.value && !dateToInput.value) {
                applyFilters();
            }
        });
    }

    if (dateToInput) {
        dateToInput.addEventListener("change", applyFilters);
    }
}

async function loadTransponders() {
    try {
        const response = await fetch("/transactions/transponders");
        if (!response.ok) throw new Error(response.status);
        const data = await response.json();

        const select = document.getElementById("filterTransponder");
        if (!select) return;

        select.innerHTML = `<option value="">Все транспондеры</option>` +
            data.items.map(t => `<option value="${t}">${t}</option>`).join('');

        // Слушатель изменения транспондера
        select.addEventListener("change", () => {
            applyFilters();
        });

    } catch (err) {
        console.error("Ошибка загрузки транспондеров:", err);
    }
}

// collectFilters() берёт текущее значение select
function collectFilters() {
    return {
        transponder: document.getElementById("filterTransponder")?.value || "",
        date_from: document.getElementById("filterDateFrom")?.value || "",
        date_to: document.getElementById("filterDateTo")?.value || ""
    };
}

// Загружает данные транзакций с сервера
async function loadData(page = 1){
    currentPage = page;
    showLoading(true);

    try {
        const params = new URLSearchParams({
            page: currentPage,
            page_size: pageSize,
            ...currentFilters
        });

        const response = await fetch(`${apiUrl}?${params.toString()}`);
        if (!response.ok) throw new Error(response.status);

        const data = await response.json();
        totalItems = data.total || 0;

        renderTable(data.items || [], formatDateTime);
        updatePagination();
        updateShowingText();
    } catch (err) {
        showError(`Ошибка загрузки данных: ${err.message}`);
    } finally {
        showLoading(false);
    }
}

// Применяет фильтры и перезагружает данные
function applyFilters() {
    currentFilters = collectFilters();
    loadData(1);
}

// Инициализирует страницу транзакций
function init() {
    if (!document.getElementById(tableId)) return;

    loadData();

    const refreshBtn = document.getElementById(refreshBtnId);
    if (refreshBtn) refreshBtn.addEventListener("click", () => loadData(1));

    const filterTrigger = document.getElementById(filterTriggerId);
    if (filterTrigger) filterTrigger.addEventListener("change", applyFilters);

    const prevBtn = document.getElementById(prevBtnId);
    const nextBtn = document.getElementById(nextBtnId);

    if (prevBtn) prevBtn.addEventListener("click", () => {
        if (currentPage > 1) loadData(currentPage - 1);
    });

    if (nextBtn) nextBtn.addEventListener("click", () => {
        if (currentPage * pageSize < totalItems) loadData(currentPage + 1);
    });
    initDateFilters();
}

window.applyFilters = applyFilters;

// Инициализация после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    init();
    loadDashboardDataViolations();
    loadTransponders();
});