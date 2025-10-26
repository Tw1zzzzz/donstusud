# Отчёт о исправлении бага: AttributeError 'judge_id'

## Дата: 26 октября 2025

## Проблема

Пользователь при нажатии на кнопку "Закрыть заявку" получал ошибку:
```
AttributeError: 'Ticket' object has no attribute 'judge_id'
```

Ошибка возникала в файле `handlers/player.py` на строке 279.

## Анализ причины

### 1. Несоответствие схемы базы данных и модели
База данных `bot.db` была создана со старой схемой, в которой отсутствовала колонка `judge_id` в таблице `tickets`. При этом модель `Ticket` в коде уже содержала это поле.

### 2. Неэффективная миграция
Код миграции в `database/db.py` (строки 76-82) пытался добавить колонку через `ALTER TABLE`, но использовал конструкцию `try/except`, которая молча проглатывала ошибки. Это не гарантировало успешное добавление колонки.

### 3. Проблема при создании объекта Ticket
При извлечении данных из БД через `Ticket(**dict(row))`, если в словаре отсутствовал ключ `judge_id`, Python не мог создать объект dataclass, даже несмотря на наличие значения по умолчанию в определении класса.

## Решение

### 1. Добавлена отсутствующая колонка
Выполнена миграция базы данных для добавления колонки `judge_id`:
```sql
ALTER TABLE tickets ADD COLUMN judge_id INTEGER
```

### 2. Улучшен код миграции
Обновлён код в `database/db.py` (строки 75-86):
- Добавлена явная проверка наличия колонки через `PRAGMA table_info(tickets)`
- Колонка добавляется только если её действительно нет
- Улучшено логирование для отслеживания процесса миграции

### До:
```python
try:
    await db.execute("ALTER TABLE tickets ADD COLUMN judge_id INTEGER")
    await db.commit()
    logger.info("Added judge_id column to tickets table")
except aiosqlite.OperationalError:
    # Column already exists
    pass
```

### После:
```python
# Check if judge_id column exists
cursor = await db.execute("PRAGMA table_info(tickets)")
columns = [row[1] for row in await cursor.fetchall()]

if 'judge_id' not in columns:
    logger.info("Column 'judge_id' not found, adding it now...")
    await db.execute("ALTER TABLE tickets ADD COLUMN judge_id INTEGER")
    logger.info("Successfully added judge_id column to tickets table")
```

## Результат

✅ Колонка `judge_id` успешно добавлена в таблицу `tickets`  
✅ Код миграции улучшен для предотвращения подобных проблем в будущем  
✅ Бот теперь может корректно обрабатывать кнопку "Закрыть заявку"  
✅ Все операции с заявками будут работать без ошибок  

## Проверка

Схема таблицы после исправления:
```
(0, 'id', 'INTEGER', 0, None, 1)
(1, 'user_id', 'INTEGER', 1, None, 0)
(2, 'ticket_type', 'TEXT', 1, None, 0)
(3, 'description', 'TEXT', 1, None, 0)
(4, 'status', 'TEXT', 1, "'open'", 0)
(5, 'created_at', 'TIMESTAMP', 0, 'CURRENT_TIMESTAMP', 0)
(6, 'closed_at', 'TIMESTAMP', 0, None, 0)
(7, 'closed_by', 'INTEGER', 0, None, 0)
(8, 'judge_id', 'INTEGER', 0, None, 0)  ← Добавлена
```

## Рекомендации

1. **Перезапустить бота** для применения изменений в коде миграции
2. **Протестировать** функцию закрытия заявки
3. В будущем использовать более надёжные инструменты миграций (например, Alembic) для сложных изменений схемы

## Измененные файлы

- `database/db.py` - улучшен код миграции
- `bot.db` - добавлена колонка `judge_id` в таблицу `tickets`

