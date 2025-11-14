// Управление фильтрами
document.getElementById('filterBtn').addEventListener('click', function() {
    const filtersSection = document.getElementById('filtersSection');
    filtersSection.style.display = filtersSection.style.display === 'none' ? 'block' : 'none';
});

document.getElementById('applyFilters').addEventListener('click', function() {
    // Применение фильтров
    const filters = {
        transponder: document.getElementById('filterTransponder').value,
        dateFrom: document.getElementById('filterDateFrom').value,
        dateTo: document.getElementById('filterDateTo').value,
        pvp: document.getElementById('filterPVP').value
    };

    // Здесь будет запрос к API с фильтрами
    console.log('Применены фильтры:', filters);
});

document.getElementById('clearFilters').addEventListener('click', function() {
    document.getElementById('filterTransponder').value = '';
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    document.getElementById('filterPVP').value = '';
});

// Загрузка файла
document.getElementById('uploadBtn').addEventListener('click', function() {
    // Создаем input для выбора файла
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.xlsx,.xls';

    input.onchange = async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/transactions/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                alert('Файл успешно загружен!');
                location.reload();
            } else {
                alert('Ошибка при загрузке файла');
            }
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Ошибка при загрузке файла');
        }
    };

    input.click();
});