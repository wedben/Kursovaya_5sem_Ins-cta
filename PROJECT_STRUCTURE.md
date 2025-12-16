# Структура проекта

## 📁 Описание структуры директорий

```
kursach/
├── app.py                    # Основное Flask приложение
├── config.py                 # Конфигурация подключения к БД
├── database.py               # Модуль для работы с базой данных
├── requirements.txt          # Зависимости Python
├── README.md                 # Основная документация
├── .env                      # Переменные окружения (не в git)
│
├── sql/                      # SQL скрипты
│   ├── create_tables.sql     # Создание таблиц
│   ├── Процедуры.sql         # Хранимые процедуры
│   ├── процедуры_с_операциями_над_данными.sql
│   ├── представления.sql     # Представления (views)
│   ├── триггеры-2.sql        # Триггеры
│   └── СБ.sql                # Права доступа
│
├── scripts/                  # Скрипты для настройки и работы с БД
│   ├── setup_db.py           # Полная настройка базы данных
│   ├── init_db.py            # Инициализация тестовых данных
│   ├── init_additional_tables.py  # Инициализация дополнительных таблиц
│   ├── import_excel_data.py  # Импорт данных из Excel
│   ├── run_sql.py            # Выполнение SQL файлов
│   ├── run_all_sql.sh        # Выполнение всех SQL скриптов
│   └── test_search.py        # Тестирование поиска
│
├── data/                     # Исходные данные
│   ├── стрекозы.xlsx         # Данные о стрекозах
│   ├── жужжелицы.xlsx        # Данные о жуках
│   └── Бабочки.xlsx          # Данные о бабочках
│
├── docs/                     # Документация
│   ├── INSTALL.md            # Инструкция по установке
│   ├── QUICK_SETUP.md        # Быстрая настройка
│   ├── SETUP_DB.md           # Настройка базы данных
│   └── КП_Отчёт.docx         # Отчет по курсовой работе
│
├── static/                   # Статические файлы
│   ├── css/
│   │   └── style.css         # Стили приложения
│   ├── js/
│   │   └── app.js            # Vue.js приложение
│   └── images/
│       └── dragon.png        # Иконка стрекозы
│
└── templates/                 # HTML шаблоны
    └── index.html            # Главная страница
```

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка базы данных
```bash
python scripts/setup_db.py
```

### 3. Импорт данных из Excel
```bash
python scripts/import_excel_data.py
```

### 4. Запуск приложения
```bash
python app.py
```

## 📝 Использование скриптов

### Настройка базы данных
```bash
python scripts/setup_db.py
```

### Импорт данных
```bash
python scripts/import_excel_data.py
```

### Выполнение SQL скриптов
```bash
# Один файл
python scripts/run_sql.py sql/create_tables.sql

# Все скрипты
./scripts/run_all_sql.sh
```

### Тестирование
```bash
python scripts/test_search.py
```

## 📂 Назначение папок

- **sql/** - Все SQL скрипты для создания структуры БД
- **scripts/** - Вспомогательные скрипты для настройки и работы
- **data/** - Исходные Excel файлы с данными
- **docs/** - Документация проекта
- **static/** - Статические файлы (CSS, JS, изображения)
- **templates/** - HTML шаблоны Flask

