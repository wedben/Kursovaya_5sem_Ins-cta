-- Статус «открыт» и привязка карточки из каталога к запросу

ALTER TABLE "ЗапросЭксперту" DROP CONSTRAINT IF EXISTS "ЗапросЭксперту_статус_check";

ALTER TABLE "ЗапросЭксперту"
    ADD CONSTRAINT "ЗапросЭксперту_статус_check"
    CHECK (статус IN (
        'на_модерации', 'открыт', 'ожидает', 'в_работе', 'отвечено',
        'отклонено', 'закрыт', 'удален_модератором'
    ));

-- Старые статусы → «открыт» (кроме закрытых и на модерации)
UPDATE "ЗапросЭксперту"
SET статус = 'открыт'
WHERE статус IN ('ожидает', 'в_работе', 'отвечено');

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ЗапросЭксперту' AND column_name = 'id_карточки'
    ) THEN
        ALTER TABLE "ЗапросЭксперту" ADD COLUMN id_карточки INTEGER;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ЗапросЭксперту' AND column_name = 'тип_карточки'
    ) THEN
        ALTER TABLE "ЗапросЭксперту" ADD COLUMN тип_карточки VARCHAR(20);
    END IF;
END $$;
