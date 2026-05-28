-- Уведомления пользователей (предупреждения, отклонение запроса, ответ эксперта)

CREATE TABLE IF NOT EXISTS "УведомлениеПользователя" (
    id_уведомления SERIAL PRIMARY KEY,
    id_пользователя INTEGER NOT NULL,
    id_запроса INTEGER,
    тип VARCHAR(50) NOT NULL CHECK (тип IN (
        'moderator_warning',
        'request_rejected',
        'expert_response'
    )),
    заголовок TEXT NOT NULL,
    текст TEXT NOT NULL,
    прочитано BOOLEAN NOT NULL DEFAULT FALSE,
    дата_создания TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_пользователя) REFERENCES "Пользователь"(id_пользователя) ON DELETE CASCADE,
    FOREIGN KEY (id_запроса) REFERENCES "ЗапросЭксперту"(id_запроса) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_уведомления_user
    ON "УведомлениеПользователя"(id_пользователя, прочитано, дата_создания DESC);
