-- Роли, модерация, чат по запросам эксперту

-- 1) Расширяем роли (добавляем модератора)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'роль'
    ) THEN
        -- Снимаем старый CHECK (имя может отличаться, поэтому добавляем новый через NOT VALID и затем VALIDATE)
        BEGIN
            ALTER TABLE "Пользователь" DROP CONSTRAINT IF EXISTS "Пользователь_роль_check";
        EXCEPTION WHEN OTHERS THEN
            -- ignore
        END;

        ALTER TABLE "Пользователь"
            ADD CONSTRAINT "Пользователь_роль_check"
            CHECK (роль IN ('пользователь', 'эксперт', 'модератор', 'админ'));
    END IF;
END $$;

-- 2) Поля для блокировок и предупреждений
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'blocked_until'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN blocked_until TIMESTAMP;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'warnings_count'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN warnings_count INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- 2b) Бессрочная блокировка (админ)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'Пользователь' AND column_name = 'blocked_permanent'
    ) THEN
        ALTER TABLE "Пользователь" ADD COLUMN blocked_permanent BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- 3) Статусы запросов: добавляем "на_модерации", "закрыт", "удален_модератором"
DO $$
BEGIN
    ALTER TABLE "ЗапросЭксперту" DROP CONSTRAINT IF EXISTS "ЗапросЭксперту_статус_check";
EXCEPTION WHEN OTHERS THEN
    -- ignore
END $$;

ALTER TABLE "ЗапросЭксперту"
    ADD CONSTRAINT "ЗапросЭксперту_статус_check"
    CHECK (статус IN ('на_модерации', 'ожидает', 'в_работе', 'отвечено', 'отклонено', 'закрыт', 'удален_модератором'));

-- 4) Метаданные модерации/закрытия
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ЗапросЭксперту' AND column_name = 'id_модератора'
    ) THEN
        ALTER TABLE "ЗапросЭксперту" ADD COLUMN id_модератора INTEGER;
        ALTER TABLE "ЗапросЭксперту"
            ADD CONSTRAINT fk_запрос_модератор FOREIGN KEY (id_модератора)
            REFERENCES "Пользователь"(id_пользователя) ON DELETE SET NULL;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ЗапросЭксперту' AND column_name = 'причина_удаления'
    ) THEN
        ALTER TABLE "ЗапросЭксперту" ADD COLUMN причина_удаления TEXT;
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ЗапросЭксперту' AND column_name = 'дата_закрытия'
    ) THEN
        ALTER TABLE "ЗапросЭксперту" ADD COLUMN дата_закрытия TIMESTAMP;
    END IF;
END $$;

-- 5) Таблица сообщений (чат) по запросу
CREATE TABLE IF NOT EXISTS "СообщениеЗапроса" (
    id_сообщения SERIAL PRIMARY KEY,
    id_запроса INTEGER NOT NULL,
    id_отправителя INTEGER NOT NULL,
    текст TEXT NOT NULL,
    дата_создания TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_запроса) REFERENCES "ЗапросЭксперту"(id_запроса) ON DELETE CASCADE,
    FOREIGN KEY (id_отправителя) REFERENCES "Пользователь"(id_пользователя) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_сообщение_запроса_request ON "СообщениеЗапроса"(id_запроса, дата_создания);

-- 6) Лог модерации (для отчётности)
CREATE TABLE IF NOT EXISTS "МодерацияЛог" (
    id_события SERIAL PRIMARY KEY,
    id_модератора INTEGER NOT NULL,
    id_пользователя INTEGER,
    id_запроса INTEGER,
    действие VARCHAR(50) NOT NULL CHECK (действие IN ('approve_request', 'delete_request', 'warn_user', 'block_user', 'set_role')),
    детали TEXT,
    дата_создания TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_модератора) REFERENCES "Пользователь"(id_пользователя) ON DELETE CASCADE,
    FOREIGN KEY (id_пользователя) REFERENCES "Пользователь"(id_пользователя) ON DELETE SET NULL,
    FOREIGN KEY (id_запроса) REFERENCES "ЗапросЭксперту"(id_запроса) ON DELETE SET NULL
);

