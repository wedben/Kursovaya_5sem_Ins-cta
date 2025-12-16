# Инструкция по установке и настройке

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Настройка подключения к PostgreSQL

1. Создайте файл `.env` в корне проекта (скопируйте из `.env.example`):
```bash
cp .env.example .env
```

2. Отредактируйте `.env` и укажите параметры вашей базы данных:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insects_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
```

## Шаг 3: Создание базы данных

Если база данных еще не создана, создайте её:
```bash
createdb -U postgres insects_db
```

## Шаг 4: Создание таблиц

Выполните SQL скрипт для создания таблиц:

**Вариант 1: Используя Python скрипт**
```bash
python run_sql.py create_tables.sql
```

**Вариант 2: Напрямую через psql**
```bash
psql -U postgres -d insects_db -f create_tables.sql
```

## Шаг 5: (Опционально) Добавление примеров данных

Если хотите добавить тестовые данные:
```bash
python init_db.py
```

## Шаг 6: Запуск приложения

```bash
python app.py
```

Приложение будет доступно по адресу: http://localhost:5000

## Если у вас уже есть база данных с данными

Если у вас уже есть готовая база данных PostgreSQL с таблицами и данными:

1. Убедитесь, что структура таблиц соответствует схеме в `create_tables.sql`
2. Настройте `.env` файл с параметрами подключения к вашей базе
3. Запустите приложение - оно должно работать с вашими данными

## Проверка подключения

Для проверки подключения к базе данных можно использовать:

```python
from database import Database

db = Database()
results = db.get_all_insects('dragonfly')
print(f"Найдено стрекоз: {len(results)}")
```

