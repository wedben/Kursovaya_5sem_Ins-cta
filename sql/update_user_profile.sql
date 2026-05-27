-- Дополнительные поля профиля пользователя (как в web_back_lab_1)

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

-- Уникальность email (case-insensitive через индекс)
CREATE UNIQUE INDEX IF NOT EXISTS idx_пользователь_email_lower ON "Пользователь"(LOWER(email));
