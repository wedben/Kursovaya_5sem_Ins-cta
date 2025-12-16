-- SQL скрипт для создания таблиц в PostgreSQL

-- Таблица для стрекоз
CREATE TABLE IF NOT EXISTS dragonflies (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_lat VARCHAR(255),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    color TEXT,
    habitat TEXT,
    season TEXT,
    description TEXT,
    image_url TEXT
);

-- Таблица для жуков
CREATE TABLE IF NOT EXISTS beetles (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_lat VARCHAR(255),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    color TEXT,
    habitat TEXT,
    season TEXT,
    description TEXT,
    image_url TEXT
);

-- Таблица для бабочек
CREATE TABLE IF NOT EXISTS butterflies (
    id SERIAL PRIMARY KEY,
    name_ru VARCHAR(255) NOT NULL,
    name_lat VARCHAR(255),
    size_min NUMERIC(10, 2),
    size_max NUMERIC(10, 2),
    color TEXT,
    habitat TEXT,
    season TEXT,
    description TEXT,
    image_url TEXT
);

-- Создание индексов для ускорения поиска
CREATE INDEX IF NOT EXISTS idx_dragonflies_color ON dragonflies(color);
CREATE INDEX IF NOT EXISTS idx_dragonflies_habitat ON dragonflies(habitat);
CREATE INDEX IF NOT EXISTS idx_dragonflies_season ON dragonflies(season);

CREATE INDEX IF NOT EXISTS idx_beetles_color ON beetles(color);
CREATE INDEX IF NOT EXISTS idx_beetles_habitat ON beetles(habitat);
CREATE INDEX IF NOT EXISTS idx_beetles_season ON beetles(season);

CREATE INDEX IF NOT EXISTS idx_butterflies_color ON butterflies(color);
CREATE INDEX IF NOT EXISTS idx_butterflies_habitat ON butterflies(habitat);
CREATE INDEX IF NOT EXISTS idx_butterflies_season ON butterflies(season);

-- ============================================
-- Дополнительные таблицы для системы наблюдений
-- ============================================

-- Таблица Пользователь (базовая структура, дополните при необходимости)
CREATE TABLE IF NOT EXISTS "Пользователь" (
    id_пользователя SERIAL PRIMARY KEY,
    имя VARCHAR(255),
    email VARCHAR(255),
    дата_регистрации DATE DEFAULT CURRENT_DATE
);

-- Таблица МестоНаблюдения (базовая структура, дополните при необходимости)
CREATE TABLE IF NOT EXISTS "МестоНаблюдения" (
    id_места SERIAL PRIMARY KEY,
    название VARCHAR(255) NOT NULL,
    описание TEXT,
    координаты POINT,
    регион VARCHAR(255)
);

-- Таблица ВидНасекомого (базовая структура, дополните при необходимости)
-- Эта таблица может объединять все виды или ссылаться на dragonflies/beetles/butterflies
CREATE TABLE IF NOT EXISTS "ВидНасекомого" (
    id_вида SERIAL PRIMARY KEY,
    название_русское VARCHAR(255) NOT NULL,
    название_латинское VARCHAR(255),
    тип_насекомого VARCHAR(50) CHECK (тип_насекомого IN ('стрекоза', 'жук', 'бабочка')),
    размер_мин NUMERIC(10, 2),
    размер_макс NUMERIC(10, 2),
    цвет TEXT,
    описание TEXT,
    изображение TEXT
);

-- Таблица Биотоп (базовая структура, дополните при необходимости)
CREATE TABLE IF NOT EXISTS "Биотоп" (
    id_биотоп SERIAL PRIMARY KEY,
    название VARCHAR(255) NOT NULL UNIQUE,
    описание TEXT
);

-- Таблица СтатусТочности
CREATE TABLE IF NOT EXISTS "СтатусТочности" (
    id_статуса_точности SERIAL PRIMARY KEY,
    значение VARCHAR(50) NOT NULL UNIQUE
);

-- Таблица Наблюдение
CREATE TABLE IF NOT EXISTS "Наблюдение" (
    id_наблюдения SERIAL PRIMARY KEY,
    id_пользователя INTEGER NOT NULL,
    id_места INTEGER NOT NULL,
    дата DATE NOT NULL,
    месяц INTEGER NOT NULL CHECK (месяц >= 1 AND месяц <= 12),
    часть_дня VARCHAR(20) CHECK (часть_дня IN ('утро', 'день', 'вечер', 'ночь')),
    FOREIGN KEY (id_пользователя) REFERENCES "Пользователь"(id_пользователя) ON DELETE CASCADE,
    FOREIGN KEY (id_места) REFERENCES "МестоНаблюдения"(id_места) ON DELETE RESTRICT,
    UNIQUE(id_пользователя, id_места, дата, часть_дня)
);

-- Таблица Идентификация
CREATE TABLE IF NOT EXISTS "Идентификация" (
    id_идентификации SERIAL PRIMARY KEY,
    id_наблюдения INTEGER NOT NULL,
    id_вида INTEGER NOT NULL,
    дата DATE NOT NULL DEFAULT CURRENT_DATE,
    id_статуса_точности INTEGER NOT NULL,
    FOREIGN KEY (id_наблюдения) REFERENCES "Наблюдение"(id_наблюдения) ON DELETE CASCADE,
    FOREIGN KEY (id_вида) REFERENCES "ВидНасекомого"(id_вида) ON DELETE RESTRICT,
    FOREIGN KEY (id_статуса_точности) REFERENCES "СтатусТочности"(id_статуса_точности) ON DELETE RESTRICT,
    UNIQUE(id_наблюдения, id_вида)
);

-- Таблица связи многие-ко-многим ВидНасекомого_Биотоп
CREATE TABLE IF NOT EXISTS "ВидНасекомого_Биотоп" (
    id_вида INTEGER NOT NULL,
    id_биотоп INTEGER NOT NULL,
    вероятность DECIMAL(3,2) CHECK (вероятность >= 0 AND вероятность <= 1),
    PRIMARY KEY (id_вида, id_биотоп),
    FOREIGN KEY (id_вида) REFERENCES "ВидНасекомого"(id_вида) ON DELETE CASCADE,
    FOREIGN KEY (id_биотоп) REFERENCES "Биотоп"(id_биотоп) ON DELETE CASCADE
);

-- Индексы для новых таблиц
CREATE INDEX IF NOT EXISTS idx_наблюдение_пользователь ON "Наблюдение"(id_пользователя);
CREATE INDEX IF NOT EXISTS idx_наблюдение_место ON "Наблюдение"(id_места);
CREATE INDEX IF NOT EXISTS idx_наблюдение_дата ON "Наблюдение"(дата);
CREATE INDEX IF NOT EXISTS idx_идентификация_наблюдение ON "Идентификация"(id_наблюдения);
CREATE INDEX IF NOT EXISTS idx_идентификация_вид ON "Идентификация"(id_вида);
CREATE INDEX IF NOT EXISTS idx_вид_биотоп_вид ON "ВидНасекомого_Биотоп"(id_вида);
CREATE INDEX IF NOT EXISTS idx_вид_биотоп_биотоп ON "ВидНасекомого_Биотоп"(id_биотоп);

