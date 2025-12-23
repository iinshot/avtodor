let tableId = "transactionsTable";
let prevBtnId = "prevBtnTransaction";
let nextBtnId = "nextBtnTransaction";
let showingTextId = "showingText";
let apiUrl = "/transactions/info";
let refreshBtnId = "refreshBtn";
let filterTriggerId = "sourceFilter";
let currentPage = 1;
const pageSize = 50;
let totalItems = 0;
let currentFilters = {};
let scrapeFrom = null;
let scrapeTo = null;
let isScraping = false;

// Загружает статистику транзакций
async function loadDashboardDataTransactions() {
    try {
        const response = await fetch('/transactions/stats');
        const data = await response.json();

        document.getElementById('monthTransactions').textContent = data.month_transactions;
        document.getElementById('todayTransactions').textContent = data.today_transactions;
        document.getElementById('totalTransactions').textContent = data.total_transactions;
        document.getElementById('monthPaidTransactions').textContent = '₽ ' + data.sum_transactions.toLocaleString();

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Отвечает за прогресс бар и количество записей
async function updateProgress() {
    const progressBar = document.getElementById("scrapeProgress");
    const countLabel = document.getElementById("scrapeCount");

    try {
        const res = await fetch("/transactions/progress");
        const data = await res.json();
        const target = data.progress || 0;
        const current = parseFloat(progressBar.style.width) || 0;
        const newWidth = current + (target - current) * 0.15;
        progressBar.style.width = newWidth + "%";

        if (countLabel) {
            countLabel.textContent = `Получено записей: ${data.items_count}`;
        }

        if (isScraping && newWidth < 100) {
            setTimeout(updateProgress, 300);
        }

        if (target === 100) {
            progressBar.style.width = "100%";
        }

    } catch (err) {
        console.error("Ошибка прогресса:", err);
    }
}

// Форматирует дату в читаемый формат
function formatDateTime(dateString){
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
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage * pageSize >= totalItems;
}

// Обновляет текст с информацией о показываемых записях
function updateShowingText(){
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
    const dateFromInput = document.getElementById("dateFromFilter");
    const dateToInput = document.getElementById("dateToFilter");

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
        date_from: document.getElementById("dateFromFilter")?.value || "",
        date_to: document.getElementById("dateToFilter")?.value || ""
    };
}

// Загружает данные транзакций с сервера
async function loadData(page = 1) {
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

function toggleDateRangeForm() {
    const form = document.getElementById('dateRangeForm');
    const button = document.getElementById('showDateRangeBtn');

    // Проверяем текущее состояние через computed style
    const computedStyle = window.getComputedStyle(form);
    const isVisible = computedStyle.display !== 'none';

    if (isVisible) {
        // Скрываем форму с !important
        form.style.cssText = 'display: none !important';
        button.innerHTML = 'За выбранный период';
    } else {
        // Показываем форму с !important
        form.style.cssText = 'display: flex !important';
        button.innerHTML = 'Скрыть выбор периода';
    }
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

async function scrapeRange(){
    const fromInput = document.getElementById("customDateFrom");
    const toInput = document.getElementById("customDateTo");

    scrapeFrom = fromInput.value;
    scrapeTo = toInput.value;

    try {
        isScraping = true;

        const progressBar = document.getElementById("scrapeProgress");
        progressBar.style.width = "0%";

        const res = await fetch(`/transactions/scrape-range?date_from=${scrapeFrom}&date_to=${scrapeTo}`, {
            method: "POST"
        });

        if (!res.ok) throw new Error("Ошибка запуска");
        updateProgress();

    } catch (err) {
        console.error("Ошибка скрапинга:", err);
        alert("Ошибка: " + err.message);
    }
};

function formatDate(date) {
    return date.toISOString().split("T")[0];
}

function scrapeDay() {
    const today = new Date();
    const from = formatDate(today);
    const to = formatDate(today);

    document.getElementById("customDateFrom").value = from;
    document.getElementById("customDateTo").value = to;

    scrapeRange();
}

function scrapeWeek() {
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);

    document.getElementById("customDateFrom").value = formatDate(weekAgo);
    document.getElementById("customDateTo").value = formatDate(today);

    scrapeRange();
}

function scrapeMonth() {
    const today = new Date();
    const monthAgo = new Date();
    monthAgo.setMonth(today.getMonth() - 1);

    document.getElementById("customDateFrom").value = formatDate(monthAgo);
    document.getElementById("customDateTo").value = formatDate(today);

    scrapeRange();
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    try {
        isScraping = true;
        const progressBar = document.getElementById("scrapeProgress");
        progressBar.style.width = "0%";
        updateProgress();

        const response = await fetch('/transactions/import', {
            method: 'POST',
            body: formData
        })
        if (!response.ok) {
            const text = await response.text();
            console.error("Server error:", response.status, text);
            throw new Error(`Ошибка загрузки файла: ${response.status}`);
        }

        const data = await response.json();

        if (data.saved !== undefined) {
            loadData(1);
            loadDashboardDataTransactions();
        }

        isScraping = false;
    } catch(err) {
        console.error('Ошибка:', err)
    }
}

function scrapeFile(fileType = null) {
    const input = document.createElement('input');
    input.type = 'file';

    if (fileType) {
        input.accept = fileType === 'csv' ? '.csv' :
                      fileType === 'xlsx' ? '.xlsx,.xls' :
                      '.pdf';
    }

    input.onchange = function(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (fileType) {
            const ext = file.name.split('.').pop().toLowerCase();
            const validExts = fileType === 'xlsx' ? ['xlsx', 'xls'] : [fileType];

            if (!validExts.includes(ext)) {
                alert(`Выберите ${fileType.toUpperCase()} файл`);
                return;
            }
        }

        uploadFile(file);
    };

    input.click();
}

window.scrapeFile = scrapeFile;
window.scrapeDay = scrapeDay;
window.scrapeWeek = scrapeWeek;
window.scrapeMonth = scrapeMonth;
window.scrapeRange = scrapeRange;
window.applyFilters = applyFilters;
window.toggleDateRangeForm = toggleDateRangeForm;

// Инициализация после загрузки DOM
document.addEventListener("DOMContentLoaded", () => {
    init();
    loadDashboardDataTransactions();
    loadTransponders();
});