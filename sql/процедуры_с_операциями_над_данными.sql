-- 1. Добавление нового вида насекомого
CREATE OR REPLACE PROCEDURE пр_добавить_вид_процедура(
    IN p_научное_название VARCHAR,
    IN p_русское_название VARCHAR,
    IN p_семейство VARCHAR,
    IN p_род_или_подотряд VARCHAR,
    IN p_первый_месяц INT,
    IN p_последний_месяц INT,
    OUT p_id_вида INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_сезонности INT;
    v_название_периода VARCHAR;
BEGIN
    -- 1. Проверка входных параметров
    IF p_первый_месяц < 1 OR p_первый_месяц > 12 THEN
        RAISE EXCEPTION 'Первый месяц должен быть от 1 до 12, получено: %', p_первый_месяц;
    END IF;
    
    IF p_последний_месяц < 1 OR p_последний_месяц > 12 THEN
        RAISE EXCEPTION 'Последний месяц должен быть от 1 до 12, получено: %', p_последний_месяц;
    END IF;
    
    IF p_первый_месяц > p_последний_месяц THEN
        RAISE EXCEPTION 'Первый месяц (%) не может быть больше последнего месяца (%)', 
                       p_первый_месяц, p_последний_месяц;
    END IF;
    
    IF p_научное_название IS NULL OR p_научное_название = '' THEN
        RAISE EXCEPTION 'Научное название обязательно';
    END IF;
    
    IF p_русское_название IS NULL OR p_русское_название = '' THEN
        RAISE EXCEPTION 'Русское название обязательно';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM ВидНасекомого 
        WHERE научное_название = p_научное_название
           OR русское_название = p_русское_название
    ) THEN
        RAISE EXCEPTION 'Вид с таким названием уже существует';
    END IF;
    
    v_название_периода := 
        CASE 
            WHEN p_первый_месяц BETWEEN 3 AND 5 AND p_последний_месяц BETWEEN 3 AND 5 THEN 'Весенний'
            WHEN p_первый_месяц BETWEEN 6 AND 8 AND p_последний_месяц BETWEEN 6 AND 8 THEN 'Летний'
            WHEN p_первый_месяц BETWEEN 9 AND 11 AND p_последний_месяц BETWEEN 9 AND 11 THEN 'Осенний'
            WHEN (p_первый_месяц = 12 OR p_первый_месяц <= 2) AND 
                 (p_последний_месяц = 12 OR p_последний_месяц <= 2) THEN 'Зимний'
            WHEN p_первый_месяц = 1 AND p_последний_месяц = 12 THEN 'Круглогодичный'
            ELSE 'Смешанный'
        END;
    
    INSERT INTO Сезонность (первый_месяц, последний_месяц, название_периода)
    VALUES (p_первый_месяц, p_последний_месяц, v_название_периода)
    ON CONFLICT (первый_месяц, последний_месяц) 
    DO UPDATE SET название_периода = EXCLUDED.название_периода
    RETURNING id_сезонности INTO v_id_сезонности;
    
    -- 5. Вставляем вид насекомого
    INSERT INTO ВидНасекомого (
        научное_название, 
        русское_название, 
        семейство, 
        род_или_подотряд, 
        id_сезонности
    ) VALUES (
        p_научное_название,
        p_русское_название,
        p_семейство,
        p_род_или_подотряд,
        v_id_сезонности
    )
    RETURNING id_вида INTO p_id_вида;

    RAISE NOTICE 'Вид "%" успешно добавлен. ID: %', p_русское_название, p_id_вида;
END;
$$;

select * from ВидНасекомого

DO $$
DECLARE
    v_id_вида INT;
BEGIN
    -- Вызов процедуры
    CALL пр_добавить_вид_процедура(
        p_научное_название := 'Aeshna',
        p_русское_название := 'Стрекоза синяя',
        p_семейство := 'Aeshnidae',
        p_род_или_подотряд := 'Aeshna',
        p_первый_месяц := 5,  -- май
        p_последний_месяц := 9,  -- сентябрь
        p_id_вида := v_id_вида  -- OUT параметр
    );
    
    -- Выводим результат
    RAISE NOTICE 'Добавлен вид с ID: %', v_id_вида;
END $$;

-- 2. Обновление статуса точности идентификации (процедура)
CREATE OR REPLACE PROCEDURE пр_обновить_статус_идентификации(
    IN p_id_идентификации INT,
    IN p_новый_статус INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    rows_affected INT;
BEGIN
    UPDATE Идентификация
    SET id_статуса_точности = p_новый_статус
    WHERE id_идентификации = p_id_идентификации;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;

    IF rows_affected > 0 THEN
        RAISE NOTICE 'Статус идентификации % успешно обновлён до %', 
                     p_id_идентификации, p_новый_статус;
    ELSE
        RAISE NOTICE 'Запись с id_идентификации = % не найдена', 
                     p_id_идентификации;
    END IF;
END;
$$;

select * from Идентификация

DO $$
BEGIN
    CALL пр_обновить_статус_идентификации(12, 2);
END $$;


-- 3. Удаление Одного из ЖукаЖестокрылого
CREATE OR REPLACE PROCEDURE пр_удалить_жука(
    p_id_жука INT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_id_вида INT;
    v_название_жука VARCHAR;
    v_количество_идентификаций INT;
    v_количество_изображений INT;
    v_количество_биотопов INT;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM ЖукЖесткокрылый WHERE id_вида = p_id_жука) THEN
        RAISE EXCEPTION 'Жук жесткокрылый с ID % не существует', p_id_жука;
    END IF;
    
    SELECT 
        j.id_вида,
        v.русское_название,
        (SELECT COUNT(*) FROM Идентификация WHERE id_вида = j.id_вида),
        (SELECT COUNT(*) FROM Изображение WHERE id_вида = j.id_вида),
        (SELECT COUNT(*) FROM Вид_Биотоп WHERE id_вида = j.id_вида)
    INTO 
        v_id_вида,
        v_название_жука,
        v_количество_идентификаций,
        v_количество_изображений,
        v_количество_биотопов
    FROM ЖукЖесткокрылый j
    JOIN ВидНасекомого v ON v.id_вида = j.id_вида
    WHERE j.id_вида = p_id_жука;
    
    RAISE NOTICE 'Жук "%" (ID: %):', v_название_жука, p_id_жука;
    RAISE NOTICE '  - Идентификаций: %', v_количество_идентификаций;
    RAISE NOTICE '  - Изображений: %', v_количество_изображений;
    RAISE NOTICE '  - Связей с биотопами: %', v_количество_биотопов;
    
    IF v_количество_идентификаций > 0 THEN
        RAISE EXCEPTION 'Нельзя удалить жука "%", так как есть % идентификаций этого вида.', 
                       v_название_жука, v_количество_идентификаций;
    END IF;
    
    IF v_количество_изображений > 0 THEN
        RAISE EXCEPTION 'Нельзя удалить жука "%", так как есть % изображений этого вида.', 
                       v_название_жука, v_количество_изображений;
    END IF;
    
    DELETE FROM ЖукЖесткокрылый WHERE id_вида = p_id_жука;
    
    DELETE FROM Вид_Биотоп WHERE id_вида = v_id_вида;
    
    DELETE FROM ВидНасекомого WHERE id_вида = v_id_вида;
    
    RAISE NOTICE 'Жук жесткокрылый "%" (ID: %) успешно удален', v_название_жука, p_id_жука;
END;
$$;

CALL пр_удалить_жука(39)

-- 4. Добавление или обновление пользователя 
CREATE OR REPLACE PROCEDURE пр_добавить_пользователя(
    p_id_пользователя INT,
    p_имя VARCHAR,
    p_фамилия VARCHAR,
    p_телефон VARCHAR,
    p_роль INT,
    OUT статус TEXT
) AS $$
DECLARE
    rows_affected INT;
BEGIN
    INSERT INTO Пользователь (id_пользователя, имя, фамилия, номер_телефона, Роль)
    VALUES (p_id_пользователя, p_имя, p_фамилия, p_телефон, p_роль)
    ON CONFLICT (id_пользователя) DO UPDATE
        SET имя = EXCLUDED.имя,
            фамилия = EXCLUDED.фамилия,
            номер_телефона = EXCLUDED.номер_телефона,
            Роль = EXCLUDED.Роль;

    GET DIAGNOSTICS rows_affected = ROW_COUNT;

    IF rows_affected = 1 THEN
        статус := 'добавлен';
    ELSE
        статус := 'обновлён';
    END IF;
END;
$$ LANGUAGE plpgsql;
 
-- 4.тест
DO $$
DECLARE
    результат TEXT;
BEGIN
    call пр_добавить_пользователя(1346765, 'Иван', 'Иванов', '+79941334567', 3, результат);
    RAISE NOTICE 'Статус: %', результат;
END $$;

