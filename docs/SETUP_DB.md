# Инструкция по настройке базы данных

## Шаг 1: Установка PostgreSQL

Если PostgreSQL еще не установлен:

### macOS (через Homebrew):
```bash
brew install postgresql@14
brew services start postgresql@14
```

### Или скачайте с официального сайта:
https://www.postgresql.org/download/

## Шаг 2: Настройка файла .env

1. Откройте файл `.env` в корне проекта
2. Заполните параметры подключения:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=insects_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль
```

**Важно:** Если у вас нет пароля для пользователя postgres, оставьте `DB_PASSWORD=` пустым или установите пароль:

```bash
# Установка пароля для пользователя postgres
psql -U postgres
ALTER USER postgres PASSWORD 'ваш_пароль';
\q
```

## Шаг 3: Автоматическая настройка базы данных

Запустите скрипт настройки:

```bash
python3 setup_db.py
```

Этот скрипт:
- ✅ Проверит подключение к PostgreSQL
- ✅ Создаст базу данных `insects_db` (если её нет)
- ✅ Создаст все таблицы из `create_tables.sql`
- ✅ Добавит тестовые данные (стрекозы, жуки, бабочки)

## Шаг 4: Ручная настройка (альтернатива)

Если автоматическая настройка не работает, выполните вручную:

### 3.1. Создание базы данных:
```bash
createdb -U postgres insects_db
```

### 3.2. Создание таблиц:
```bash
# Вариант 1: через Python скрипт
python3 run_sql.py create_tables.sql

# Вариант 2: через psql
psql -U postgres -d insects_db -f create_tables.sql
```

### 3.3. Добавление тестовых данных:
```bash
python3 init_db.py
python3 init_additional_tables.py
```

## Шаг 5: Проверка подключения

Проверьте, что всё работает:

```bash
python3 -c "from database import Database; db = Database(); print('✅ Подключение успешно!')"
```

## Шаг 6: Запуск приложения

```bash
python3 app.py
```

Приложение будет доступно по адресу: http://localhost:5001

## Устранение проблем

### Ошибка "psql: command not found"
- Установите PostgreSQL (см. Шаг 1)
- Добавьте PostgreSQL в PATH:
  ```bash
  export PATH="/usr/local/opt/postgresql@14/bin:$PATH"
  ```

### Ошибка подключения "password authentication failed"
- Проверьте пароль в файле `.env`
- Или создайте нового пользователя:
  ```bash
  createuser -U postgres -P ваш_пользователь
  ```

### Ошибка "database does not exist"
- Убедитесь, что база данных создана:
  ```bash
  createdb -U postgres insects_db
  ```

### Ошибка "permission denied"
- Убедитесь, что пользователь имеет права на создание баз данных
- Или выполните команды от имени пользователя postgres

## Если у вас уже есть база данных с данными

1. Убедитесь, что структура таблиц соответствует схеме в `create_tables.sql`
2. Настройте `.env` файл с параметрами подключения к вашей базе
3. Запустите приложение - оно должно работать с вашими данными

