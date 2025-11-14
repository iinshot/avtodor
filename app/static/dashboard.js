// Загрузка данных дашборда
async function loadDashboardData() {
    try {
        const response = await fetch('/api/dashboard/stats');
        const data = await response.json();

        // Обновляем карточки
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
    // График нарушений
    const violationsCtx = document.getElementById('violationsChart').getContext('2d');
    new Chart(violationsCtx, {
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
    new Chart(pvpCtx, {
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
        const response = await fetch('/violations');
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