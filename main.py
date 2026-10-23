        // Загрузка данных с сервера
        async function loadShifts() {
            try {
                const response = await fetch(`${API_URL}/shifts`);
                shiftsDB = await response.json();
                renderCalendarUI(); // Отдельная функция для отрисовки
            } catch (e) {
                console.error("Ошибка загрузки", e);
            }
        }

        function renderCalendar() {
            loadShifts(); // При смене недели или загрузке просто запрашиваем данные заново
        }

        // Отрисовка (бывшая renderCalendar)
        function renderCalendarUI() {
            const dates = getWeekDates(currentWeekOffset);
            const container = document.getElementById('calendar-container');
            container.innerHTML = '';
            
            // ... (оставьте код заголовка недели и перебора дней как было) ...
            // ВАЖНО: внутри цикла, где выводится карточка смены, поменяйте кнопку удаления:
            // const delBtnHtml = canDelete ? `<button class="delete-btn" onclick="deleteShift(${shift.id})">🗑️</button>` : '';
            // Оставьте так же. 
            // ... (код отрисовки карточек) ...
        }

        async function saveShift() {
            if (selectedStart >= selectedEnd) {
                alert("Время окончания должно быть позже начала!");
                return;
            }

            const comment = document.getElementById('input-comment').value;
            const dates = getWeekDates(currentWeekOffset);
            const todayStr = formatDate(new Date());
            const targetDate = dates.find(d => formatDate(d) === todayStr) ? new Date() : dates[0];

            const newShift = {
                master: currentMaster,
                date: formatDate(targetDate),
                start: selectedStart,
                end: selectedEnd,
                comment: comment
            };

            try {
                const response = await fetch(`${API_URL}/shifts`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(newShift)
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    alert(error.detail); // Покажет ошибку пересечения
                } else {
                    closeModal();
                    loadShifts(); // Перезагружаем данные
                }
            } catch (e) {
                alert("Ошибка соединения с сервером");
            }
        }

        async function deleteShift(id) {
            if (confirm("Удалить эту смену?")) {
                try {
                    await fetch(`${API_URL}/shifts/${id}`, { method: 'DELETE' });
                    loadShifts(); // Обновляем данные
                } catch (e) {
                    alert("Ошибка удаления");
                }
            }
        }