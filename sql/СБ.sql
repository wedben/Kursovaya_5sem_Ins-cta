SELECT * FROM ВидНасекомого
select * from Сезонность


-- Все роли могут использовать схему public
GRANT USAGE ON SCHEMA public TO admin, expert, observer;

-- Полный доступ ко всем таблицам
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;

-- Права на последовательности
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;

-- Права на выполнение функций
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO admin;

-- Права на будущие таблицы
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
    GRANT ALL PRIVILEGES ON TABLES TO admin;



-- 1. ЧТЕНИЕ всех таблиц
GRANT SELECT ON ALL TABLES IN SCHEMA public TO expert;

-- 2. ПОЛНЫЙ ДОСТУП к таксономическим таблицам
GRANT INSERT, UPDATE, DELETE ON 
    ВидНасекомого,
    Стрекоза,
    Бабочка,
    ЖукЖесткокрылый,
    Сезонность,
    Изображение,
    Вид_Биотоп,
    Биотоп,
    СтатусТочности
TO expert;

-- 3. ОГРАНИЧЕННЫЙ доступ к наблюдениям (только чтение)
GRANT SELECT ON Наблюдение TO expert;

-- 4. ПРАВА НА ИДЕНТИФИКАЦИИ:
-- 4.1. Чтение всех идентификаций
GRANT SELECT ON Идентификация TO expert;

-- 4.2. Может менять статус точности идентификаций
GRANT UPDATE(id_статуса_точности) ON Идентификация TO expert;

-- 4.3. Может добавлять новые идентификации
GRANT INSERT ON Идентификация TO expert;


-- 5. ПРАВА НА ТАБЛИЦУ НАСЕКОМОЕ (ВидНасекомого):
GRANT SELECT, INSERT, UPDATE, DELETE ON ВидНасекомого, Стрекоза, Бабочка, ЖукЖесткокрылый TO expert;

-- 6. Запрещаем удаление наблюдений и управление пользователями
REVOKE DELETE ON Наблюдение, Идентификация FROM expert;
REVOKE ALL ON Пользователь, Роль FROM expert;
REVOKE UPDATE ON Идентификация FROM expert WHERE column NOT IN ('id_статуса_точности', 'комментарий');

-- 6. Права на последовательности для таксономии
GRANT USAGE, SELECT ON SEQUENCE 
    ВидНасекомого_id_вида_seq,
    Сезонность_id_сезонности_seq
TO expert;

-- 7. Права на функции
GRANT EXECUTE ON FUNCTION 
    а_точность_идентификаций_по_видам,
	а_статистика_групп_простая
TO expert;

GRANT EXECUTE ON PROCEDURE
    пр_добавить_идентификацию,
	пр_удалить_жука
TO expert;


-- 1. ЧТЕНИЕ справочных данных
GRANT SELECT ON 
    ВидНасекомого,
    Стрекоза,
    Бабочка,
    ЖукЖесткокрылый,
    Сезонность,
    Изображение,
    Биотоп,
    Страна,
    Регион,
    МестоНаблюдения,
    СтатусТочности
TO observer;

-- 2. ОГРАНИЧЕННЫЙ просмотр пользователей (только ФИО)
GRANT SELECT(id_пользователя, фамилия, имя, номер_телефона) ON Пользователь TO observer;
GRANT SELECT ON Роль TO observer;

-- 3. Включаем Row Level Security для защиты данных
ALTER TABLE Наблюдение ENABLE ROW LEVEL SECURITY;
ALTER TABLE Идентификация ENABLE ROW LEVEL SECURITY;
ALTER TABLE Пользователь ENABLE ROW LEVEL SECURITY;

-- 4. Политика RLS для таблицы Наблюдение
CREATE POLICY observer_observation_policy ON Наблюдение
    FOR ALL TO observer
    USING (
        -- Для SELECT может видеть все наблюдения
        true
    )
    WITH CHECK (
        -- Для INSERT/UPDATE/DELETE только свои
        id_пользователя = current_setting('app.user_id')::INT
    );

-- 5. Политика RLS для таблицы Идентификация
CREATE POLICY observer_identification_policy ON Идентификация
    FOR ALL TO observer
    USING (
        -- Может видеть все идентификации
        true
    )
    WITH CHECK (
        -- Может добавлять/редактировать только для своих наблюдений
        id_наблюдения IN (
            SELECT id_наблюдения FROM Наблюдение 
            WHERE id_пользователя = current_setting('app.user_id')::INT
        )
    );

-- 6. Политика RLS для таблицы Пользователь
CREATE POLICY observer_user_policy ON Пользователь
    FOR SELECT TO observer
    USING (
        -- Может видеть только себя и публичную информацию других
        id_пользователя = current_setting('app.user_id')::INT
        OR true  -- для публичных полей, но ограничим в GRANT
    );

-- 7. Даем формальные права (реальные права контролируются через RLS)
GRANT SELECT, INSERT, UPDATE ON Наблюдение TO observer;
GRANT SELECT, INSERT, UPDATE ON Идентификация TO observer;

-- 8. Запрещаем удаление
REVOKE DELETE ON Наблюдение, Идентификация FROM observer;

-- 9. Запрещаем доступ к таксономическим таблицам на запись
REVOKE INSERT, UPDATE, DELETE ON 
    ВидНасекомого,
    Стрекоза,
    Бабочка,
    ЖукЖесткокрылый,
    Сезонность,
    Изображение
FROM observer;

-- 10. Права на последовательности для своих наблюдений
GRANT USAGE, SELECT ON SEQUENCE 
    Наблюдение_id_наблюдения_seq,
    Идентификация_id_идентификации_seq
TO observer;

-- 11. Права на ограниченные функции
GRANT EXECUTE ON FUNCTION
    а_виды_в_биотопе,
    а_наблюдения_по_месяцам
TO observer;

SET ROLE postgres

SET ROLE observer;
SET ROLE expert;
SET ROLE admin;

select * from Наблюдение 
where id_пользователя=123456789

select current_user;

select * from а_наблюдения_по_месяцам(2025)

select * from ВидНасекомого
select * from Пользователь
select * from Идентификация