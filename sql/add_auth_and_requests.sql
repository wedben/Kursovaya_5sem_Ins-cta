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
        ALTER TABLE "Пользователь" ADD COLUMN роль VARCHAR(50) DEFAULT 'пользователь' CHECK (роль IN ('пользователь', 'админ', 'эксперт'));
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

-- Создаем первого админа (пароль: admin123, нужно будет захешировать)
-- Пароль будет хешироваться в приложении
INSERT INTO "Пользователь" (имя, email, username, пароль, роль) 
VALUES ('Администратор', 'admin@insects.ru', 'admin', 'admin123', 'админ')
ON CONFLICT (username) DO NOTHING;

