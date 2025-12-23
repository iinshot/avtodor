async function loadDashboardData() {
    try {
        const response = await fetch('/stats');
        const data = await response.json();

        document.getElementById('transactionsCountMonth').textContent = data.month_transactions;
        document.getElementById('transactionsCountDay').textContent = data.today_transactions;
        document.getElementById('violationsCountDay').textContent = data.today_violations;
        document.getElementById('violationsCountMonth').textContent = data.month_violations;

    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
}

async function loadDashboardBalance() {
    try {
        const response_balance = await fetch('/balance');
        const data_balance = await response_balance.json();
        document.getElementById('balanceScore').textContent = '₽ ' + data_balance.balance.toLocaleString();

    } catch (error) {
        console.error('Ошибка загрузки баланса:', error);
    }
}

async function checkAuthStatus() {
    const authStatus = document.getElementById('authStatus');

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
        }

        authStatus.innerHTML = statusText;

    } catch (error) {
        authStatus.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> Ошибка проверки</span>';
    }
}

async function checkBalanceStatus() {
    const balanceStatus = document.getElementById('balanceStatus');

    balanceStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Проверка баланса...';

    try {
        const response = await fetch('/balance');
        const data = await response.json();

        let statusText = '';
        if (data.valid) {
            statusText = '<span class="text-success"><i class="fas fa-check-circle"></i> Баланс получен</span>';
        }
        else {
            statusText = '<span class="text-danger"><i class="fas fa-times-circle"></i> Ошибка при получении баланса</span>';
        }

        balanceStatus.innerHTML = statusText;

    } catch (error) {
        balanceStatus.innerHTML = '<span class="text-danger"><i class="fas fa-times-circle"></i> Ошибка проверки</span>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    loadDashboardBalance();
    checkAuthStatus();
    checkBalanceStatus();
});