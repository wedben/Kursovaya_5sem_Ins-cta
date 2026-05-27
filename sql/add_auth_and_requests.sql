-- Расширение таблицы Пользователь для аутентификации
-- Добавляем поля для пароля и роли, если их еще нет

-- Проверяем и добавляем поле пароля
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'Пользователь' AND column_name = 'пароль'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN пароль VARCHAR(255);
    END IF;
END $$;

-- Проверяем и добавляем поле роли
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'Пользователь' AND column_name = 'роль'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN роль VARCHAR(50) DEFAULT 'пользователь' CHECK (роль IN ('пользователь', 'эксперт', 'модератор'));
    END IF;
END $$;

-- Проверяем и добавляем поле username (логин)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'Пользователь' AND column_name = 'username'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN username VARCHAR(255) UNIQUE;
    END IF;
END $$;

-- Обновляем существующие записи, если нужно
UPDATE "Пользователь" SET роль = 'пользователь' WHERE роль IS NULL;

-- Таблица для запросов к эксперту
CREATE TABLE IF NOT EXISTS "ЗапросЭксперту" (
    id_запроса SERIAL PRIMARY KEY,
    id_пользователя INTEGER NOT NULL,
    описание_насекомого TEXT NOT NULL,
    место_наблюдения TEXT,
    дата_наблюдения DATE,
    дополнительные_данные TEXT,
    статус VARCHAR(50) DEFAULT 'ожидает' CHECK (статус IN ('ожидает', 'в_работе', 'отвечено', 'отклонено')),
    дата_создания TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    дата_ответа TIMESTAMP,
    ответ_эксперта TEXT,
    id_вида_насекомого INTEGER, -- Если эксперт определил вид
    изображение_ответа TEXT, -- URL изображения от эксперта
    id_эксперта INTEGER, -- Кто ответил
    FOREIGN KEY (id_пользователя) REFERENCES "Пользователь"(id_пользователя) ON DELETE CASCADE,
    FOREIGN KEY (id_вида_насекомого) REFERENCES "ВидНасекомого"(id_вида) ON DELETE SET NULL,
    FOREIGN KEY (id_эксперта) REFERENCES "Пользователь"(id_пользователя) ON DELETE SET NULL
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_запрос_пользователь ON "ЗапросЭксперту"(id_пользователя);
CREATE INDEX IF NOT EXISTS idx_запрос_статус ON "ЗапросЭксперту"(статус);
CREATE INDEX IF NOT EXISTS idx_запрос_дата ON "ЗапросЭксперту"(дата_создания);
CREATE INDEX IF NOT EXISTS idx_пользователь_username ON "Пользователь"(username);
CREATE INDEX IF NOT EXISTS idx_пользователь_email ON "Пользователь"(email);

-- Профиль пользователя (как в web_back_lab_1)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'фамилия'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN фамилия VARCHAR(31);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'пол'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN пол VARCHAR(10) CHECK (пол IN ('male', 'female'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'возраст'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN возраст VARCHAR(10) CHECK (возраст IN ('18plus', 'under18'));
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'тема'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN тема VARCHAR(10) DEFAULT 'light' CHECK (тема IN ('light', 'dark'));
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_пользователь_email_lower ON "Пользователь"(LOWER(email));

-- Примечание: роль 'админ' удалена. Для начальной настройки используйте модератора или эксперта.

