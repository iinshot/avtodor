async function loadDashboardData() {
    try {
        const response = await fetch('/dashboard/stats');
        const data = await response.json();

        document.getElementById('balanceAmount').textContent = '₽' + data.balance.toLocaleString();
        document.getElementById('transactionsCount').textContent = data.today_transactions;
        document.getElementById('violationsCount').textContent = data.today_violations;
        document.getElementById('pvpCount').textContent = data.active_pvp;

        // Обновляем статус баланса
        const balanceStatus = document.getElementById('balanceStatus');
        if (data.balance < 40000) {
            balanceStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Низкий баланс!';
            balanceStatus.className = 'card-text text-warning';
        } else {
            balanceStatus.innerHTML = '<i class="fas fa-check-circle"></i> Норма';
            balanceStatus.className = 'card-text text-light';
        }

        // Загружаем графики
        loadCharts();
        loadRecentViolations();

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

// Загрузка графиков
function loadCharts() {
    // Уничтожаем предыдущие графики, если они существуют
    if (window.violationsChart) {
        window.violationsChart.destroy();
    }
    if (window.pvpChart) {
        window.pvpChart.destroy();
    }

    // График нарушений
    const violationsCtx = document.getElementById('violationsChart').getContext('2d');
    window.violationsChart = new Chart(violationsCtx, {
        type: 'line',
        data: {
            labels: ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
            datasets: [{
                label: 'Нарушения',
                data: [12, 19, 3, 5, 2, 3, 7],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            }
        }
    });

    // График ПВП
    const pvpCtx = document.getElementById('pvpChart').getContext('2d');
    window.pvpChart = new Chart(pvpCtx, {
        type: 'doughnut',
        data: {
            labels: ['ПВП 1223', 'ПВП 1184', 'ПВП 1046', 'ПВП 636'],
            datasets: [{
                data: [30, 25, 20, 25],
                backgroundColor: [
                    'rgb(255, 99, 132)',
                    'rgb(54, 162, 235)',
                    'rgb(255, 205, 86)',
                    'rgb(75, 192, 192)'
                ]
            }]
        }
    });
}

// Загрузка последних нарушений
async function loadRecentViolations() {
    try {
        const response = await fetch('/violations');  // Изменили URL
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const violations = await response.json();

        const tbody = document.querySelector('#recentViolations tbody');
        tbody.innerHTML = '';

        violations.forEach(violation => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${violation.transponder}</td>
                <td><span class="badge bg-danger">${violation.PVP_code}</span></td>
                <td>${new Date(violation.occurred_at).toLocaleDateString()}</td>
                <td><strong>₽${violation.base_tariff}</strong></td>
                <td><span class="badge bg-warning">Нарушение</span></td>
            `;
            tbody.appendChild(row);
        });

    } catch (error) {
        console.error('Ошибка загрузки нарушений:', error);
    }
}

// Обновление по кнопке
document.getElementById('refreshBtn').addEventListener('click', loadDashboardData);

// Автозагрузка при старте
document.addEventListener('DOMContentLoaded', loadDashboardData);

async function checkAuthStatus() {
    const authStatus = document.getElementById('authStatus');
    const scrapeBtn = document.getElementById('scrapeBtn');

    authStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Проверка авторизации...';

    try {
        const response = await fetch('/check-avtodor-auth');
        const data = await response.json();

        let statusText = '';
        if (data.valid) {
            statusText = '<span class="text-success"><i class="fas fa-check-circle"></i> Сессия активна</span>';
        }
        else {
            statusText = '<span class="text-danger"><i class="fas fa-times-circle"></i> Ошибка авторизации</span>';
            scrapeBtn.disabled = true;
        }

        authStatus.innerHTML = statusText;

    } catch (error) {
        authStatus.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> Ошибка проверки</span>';
        scrapeBtn.disabled = true;
    }
}

// Запуск парсера Avtodor
async function scrapeAvtodor() {
    const scrapeBtn = document.getElementById('scrapeBtn');
    const resultDiv = document.getElementById('scraperResult');
    const messageDiv = document.getElementById('scraperMessage');
    const lastUpdateStatus = document.getElementById('lastUpdateStatus');

    // Сохраняем оригинальный текст кнопки
    const originalHtml = scrapeBtn.innerHTML;

    scrapeBtn.disabled = true;
    scrapeBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Получение данных...';

    try {
        const response = await fetch('/transactions/scrape-avtodor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (data.success) {
            messageDiv.innerHTML = `
                <strong>✅ ${data.message}</strong><br>
                <small>Получено поездок: ${data.scraped_count}, сохранено: ${data.saved_count}</small>
            `;
            resultDiv.style.display = 'block';

            // Обновляем статус последнего обновления
            const now = new Date();
            lastUpdateStatus.innerHTML = `Последнее обновление: ${now.toLocaleTimeString()}`;

            // Показываем уведомление
            showNotification(`Данные успешно получены! Добавлено ${data.saved_count} новых транзакций`, 'success');

            // Обновляем статистику дашборда
            setTimeout(loadDashboardData, 1000);

        } else {
            messageDiv.innerHTML = `<strong>❌ Ошибка: ${data.message}</strong>`;
            resultDiv.style.display = 'block';
            showNotification(`Ошибка при получении данных: ${data.message}`, 'error');
        }
    } catch (error) {
        messageDiv.innerHTML = `<strong>❌ Ошибка: ${error.message}</strong>`;
        resultDiv.style.display = 'block';
        showNotification(`Ошибка сети: ${error.message}`, 'error');
    } finally {
        scrapeBtn.disabled = false;
        scrapeBtn.innerHTML = originalHtml;
    }
}

// Скрытие результата парсинга
function hideScraperResult() {
    const resultDiv = document.getElementById('scraperResult');
    resultDiv.style.display = 'none';
}

// Переход к транзакциям
function viewTransactions() {
    window.location.href = '/transactions';
}

// Функция для отображения уведомлений
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Добавляем на страницу
    document.body.appendChild(notification);

    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Автопроверка статуса при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    // Проверяем статус авторизации с небольшой задержкой
    setTimeout(checkAuthStatus, 1000);
});