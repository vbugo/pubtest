const dbCount = 10;
const tableBody = document.getElementById('db-table');

// Хранилище локального состояния планирования для каждой строки
// "none" - обычный режим, "ready" - время выбрано, "active" - задача запланирована
const schedState = {};
for (let i = 1; i <= dbCount; i++) {
    schedState[i] = { phase: "none", targetTime: "" };
}

// 1. Инициализация таблицы при старте страницы в строгом порядке колонок
for (let i = 1; i <= dbCount; i++) {
    const tr = document.createElement('tr');
    tr.id = `row-${i}`;
    tr.innerHTML = `
        <td class="col-pc"><strong id="name-${i}">Загрузка...</strong> <span id="ip-${i}" style="color: #666; font-size: 11px;"></span></td>
        <td class="col-dump"><span id="dump-${i}"></span></td>
        <td class="col-script"><span id="script-${i}"></span></td>
        <td class="col-list"><select id="select-${i}"><option value="">Select file...</option></select></td>
        <td class="col-sched"><input type="datetime-local" id="sched-${i}"></td>
        <td class="col-exec"><button id="btn-${i}" class="btn-deploy" disabled>развернуть</button></td>
        <td class="col-status"><span id="task-${i}"></span></td>
    `;
    tableBody.appendChild(tr);

    const select = document.getElementById(`select-${i}`);
    const schedInput = document.getElementById(`sched-${i}`);
    const btn = document.getElementById(`btn-${i}`);

    // Функция динамического перерасчета состояния кнопки до отправки на бэкенд
    function updateLocalButtonMode() {
        if (schedState[i].phase === "active") return; // Если уже запланировано, логику не трогаем

        if (select.value === '') {
            btn.disabled = true;
            btn.textContent = "развернуть";
            btn.className = "btn-deploy";
        } else if (schedInput.value !== '') {
            btn.disabled = false;
            btn.textContent = "по расписанию";
            btn.className = "btn-sched";
            schedState[i].phase = "ready";
            schedState[i].targetTime = schedInput.value;
        } else {
            btn.disabled = false;
            btn.textContent = "развернуть";
            btn.className = "btn-deploy";
            schedState[i].phase = "none";
            schedState[i].targetTime = "";
        }
    }

    select.addEventListener('change', updateLocalButtonMode);
    schedInput.addEventListener('input', updateLocalButtonMode);

    btn.addEventListener('click', function() {
        // Режим ОТМЕНЫ установленной задачи
        if (schedState[i].phase === "active") {
            console.log(`[БД ${i}] Отмена отложенного запуска...`);
            schedState[i].phase = "none";
            schedState[i].targetTime = "";
            schedInput.value = "";
            schedInput.disabled = false;
            select.disabled = false;
            updateLocalButtonMode();
            return;
        }

        const file = select.value;
        if (!file) return;

        // Режим АКТИВАЦИИ отложенного запуска
        if (schedState[i].phase === "ready") {
            console.log(`[БД ${i}] Планирование задачи на ${schedState[i].targetTime}`);
            schedState[i].phase = "active";
            btn.textContent = "отменить";
            btn.className = "btn-cancel";
            schedInput.disabled = true;
            select.disabled = true;
            return;
        }

        // Режим МГНОВЕННОГО запуска db_renew
        schedState[i].phase = "none";
        btn.disabled = true;
        
        // Мгновенный сброс списка в "Select file..." при старте задачи
        select.value = ""; 

        fetch(`/api/run/${i}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: file })
        })
        .then(res => res.json())
        .then(data => console.log(`БД${i} запуск:`, data))
        .catch(err => console.error('Ошибка запуска:', err));
    });
}

function updateState() {
    fetch('/api/state')
        .then(res => res.json())
        .then(data => {
            for (let i = 1; i <= dbCount; i++) {
                const node = data[i.toString()];

                const trRow = document.getElementById(`row-${i}`);
                const nameStrong = document.getElementById(`name-${i}`);
                const ipSpan = document.getElementById(`ip-${i}`);
                const select = document.getElementById(`select-${i}`);
                const dumpSpan = document.getElementById(`dump-${i}`);
                const scriptSpan = document.getElementById(`script-${i}`);
                const taskSpan = document.getElementById(`task-${i}`);
                const schedInput = document.getElementById(`sched-${i}`);
                const btn = document.getElementById(`btn-${i}`);

                const stateMetric = node && node.metrics ? node.metrics['STATE'] : null;
                const isBusy = (stateMetric === '1');

                // 1. Обработка ОФФЛАЙН состояния (если задача не активна прямо сейчас)
                if ((!node || node.status === 'offline') && !isBusy && schedState[i].phase !== "active") {
                    if (trRow) trRow.className = 'status-offline';
                    if (node && node.name) {
                        nameStrong.textContent = `${node.name} (нет связи)`;
                    } else {
                        nameStrong.textContent = `pc${i} (нет связи)`;
                    }
                    dumpSpan.textContent = '';
                    scriptSpan.textContent = '';
                    taskSpan.textContent = '';
                    btn.disabled = true;
                    continue;
                }

                // Логика для доступного узла (online)
                if (node && node.name) { nameStrong.textContent = node.name; }
                if (node) { ipSpan.textContent = `(${node.ip})`; }

                // 2. Обработка фиолетовой строки ОТЛОЖЕННОГО запуска
                if (schedState[i].phase === "active") {
                    if (trRow) trRow.className = 'status-scheduled';
                    dumpSpan.textContent = '';
                    scriptSpan.textContent = '';
                    // Форматируем вывод времени в статус
                    const rawTime = schedState[i].targetTime.replace('T', ' ');
                    taskSpan.textContent = `Планировано на ${rawTime}`;
                    
                    // Блокируем обновление списка файлов, чтобы не сбить выбор
                    if (node && node.files && !select.disabled) {
                        select.disabled = true;
                    }
                    continue; 
                }

                // 3. Обработка ЖЕЛТОЙ строки активного наката (STATE=1)
                if (isBusy) {
                    if (trRow) trRow.className = 'status-busy';
                    dumpSpan.textContent = '';
                    scriptSpan.textContent = '';
                    schedInput.disabled = true;
                    select.disabled = true;
                    btn.disabled = true;
                    if (taskSpan) {
                        taskSpan.textContent = node.metrics['TASK_STATUS'] || '';
                    }
                } else {
                    // 4. Обработка ЗЕЛЕНОЙ штатной строки (STATE=0)
                    if (stateMetric === '0') {
                        if (trRow) trRow.className = 'status-online';
                    } else {
                        if (trRow) trRow.className = 'status-unknown';
                    }

                    // Разблокируем элементы управления после окончания работы
                    if (schedInput.disabled && schedState[i].phase !== "active") {
                        schedInput.disabled = false;
                        select.disabled = false;
                        schedInput.value = ""; // Очищаем отработанное время
                    }

                    if (node && node.metrics) {
                        dumpSpan.textContent = node.metrics['CURRENT_DUMP'] || '';
                        scriptSpan.textContent = node.metrics['CURRENT_SCRIPT'] || '';
                        taskSpan.textContent = node.metrics['TASK_STATUS'] || '';
                    } else {
                        dumpSpan.textContent = '';
                        scriptSpan.textContent = '';
                        taskSpan.textContent = '';
                    }
                }

                // Обновление выпадающего списка файлов (только если строка не занята и не запланирована)
                if (node && node.files && schedState[i].phase !== "active" && !isBusy) {
                    const currentVal = select.value;
                    const existingOptions = Array.from(select.options).map(o => o.value).filter(v => v !== "").join(",");
                    const newOptions = node.files.join(",");
                    if (existingOptions === newOptions) {
                        if (currentVal === '') btn.disabled = true;
                        continue;
                    }

                    select.innerHTML = '<option value="">Select file...</option>';
                    node.files.forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f; opt.textContent = f;
                        select.appendChild(opt);
                    });
                    if (node.files.includes(currentVal)) {
                        select.value = currentVal;
                    }
                }
            }
        })
        .catch(err => console.error('Ошибка опроса состояния:', err));
}

updateState();
setInterval(updateState, 2000);
