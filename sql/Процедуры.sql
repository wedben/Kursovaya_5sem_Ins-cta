
-- 1. Топ N видов по частоте наблюдений в биотопе+
CREATE OR REPLACE FUNCTION а_топ_видов_в_биотопе(
    p_id_биотопа INT DEFAULT NULL,
    p_количество INT DEFAULT 10,
    p_год INT DEFAULT NULL
) 
RETURNS TABLE (
    место BIGINT,  -- Изменено с INT на BIGINT
    русское_название VARCHAR,
    научное_название VARCHAR,
    семейство VARCHAR,
    количество_наблюдений BIGINT,
    процент_от_всех NUMERIC(5,2)
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_всего_наблюдений BIGINT;
BEGIN
    -- Общее количество наблюдений в биотопе
    SELECT COUNT(*)
    INTO v_всего_наблюдений
    FROM Идентификация i
    JOIN Наблюдение n ON n.id_наблюдения = i.id_наблюдения
    JOIN МестоНаблюдения м ON м.id_места = n.id_места
    WHERE (p_id_биотопа IS NULL OR м.id_биотопа = p_id_биотопа)
      AND (p_год IS NULL OR EXTRACT(YEAR FROM n.дата) = p_год);
    
    RETURN QUERY
    WITH статистика_видов AS (
        SELECT 
            v.id_вида,
            v.русское_название,
            v.научное_название,
            v.семейство,
            COUNT(*) as наблюдений
        FROM Идентификация i
        JOIN ВидНасекомого v ON v.id_вида = i.id_вида
        JOIN Наблюдение n ON n.id_наблюдения = i.id_наблюдения
        JOIN МестоНаблюдения м ON м.id_места = n.id_места
        WHERE (p_id_биотопа IS NULL OR м.id_биотопа = p_id_биотопа)
          AND (p_год IS NULL OR EXTRACT(YEAR FROM n.дата) = p_год)
        GROUP BY v.id_вида, v.русское_название, v.научное_название, v.семейство
    )
    SELECT 
        ROW_NUMBER() OVER (ORDER BY s.наблюдений DESC)::BIGINT as место,  
        s.русское_название,
        s.научное_название,
        s.семейство,
        s.наблюдений as количество_наблюдений,
        ROUND((s.наблюдений::NUMERIC / NULLIF(v_всего_наблюдений, 0)) * 100, 2) as процент_от_всех
    FROM статистика_видов s
    ORDER BY s.наблюдений DESC
    LIMIT p_количество;
END;
$$;

DROP FUNCTION "а_топ_видов_в_биотопе"(integer,integer,integer)

select * from Биотоп
select * from а_топ_видов_в_биотопе(22)
select * from МестоНаблюдения

-- 2. Наблюдения по регионам за год+
CREATE OR REPLACE FUNCTION а_наблюдения_по_регионам(
    p_год INT DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)
) RETURNS TABLE (
    регион varchar,
    количество BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT r.название, COUNT(n.id_наблюдения)
    FROM Регион r
    JOIN МестоНаблюдения m ON m.id_региона = r.id_региона
    JOIN Наблюдение n ON n.id_места = m.id_места
    WHERE EXTRACT(YEAR FROM n.дата) = p_год
    GROUP BY r.название
    ORDER BY количество DESC;
END;
$$ LANGUAGE plpgsql;

select * from а_наблюдения_по_регионам(2025)

-- 3. Средняя точность идентификаций по видам+-
CREATE OR REPLACE FUNCTION а_статистика_групп_простая(
    p_год INT DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)
) 
RETURNS TABLE (
    группа VARCHAR(50),
    количество_идентификаций BIGINT,
    процент_от_общего NUMERIC(5,2)
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_стрекозы BIGINT := 0;
    v_жуки BIGINT := 0;
    v_бабочки BIGINT := 0;
    v_другие BIGINT := 0;
    v_всего BIGINT := 0;
BEGIN
    -- Подсчитываем все за один проход для оптимизации
    WITH статистика AS (
        SELECT 
            COUNT(*) FILTER (WHERE s.id_вида IS NOT NULL) as стрекозы,
            COUNT(*) FILTER (WHERE ж.id_вида IS NOT NULL) as жуки,
            COUNT(*) FILTER (WHERE б.id_вида IS NOT NULL) as бабочки,
            COUNT(*) as всего
        FROM Идентификация i
        JOIN Наблюдение n ON n.id_наблюдения = i.id_наблюдения
        LEFT JOIN Стрекоза s ON s.id_вида = i.id_вида
        LEFT JOIN ЖукЖесткокрылый ж ON ж.id_вида = i.id_вида
        LEFT JOIN Бабочка б ON б.id_вида = i.id_вида
        WHERE EXTRACT(YEAR FROM n.дата) = p_год
    )
    SELECT 
        стрекозы, жуки, бабочки, всего,
        всего - (стрекозы + жуки + бабочки) as другие
    INTO 
        v_стрекозы, v_жуки, v_бабочки, v_всего, v_другие
    FROM статистика;

    -- Возвращаем таблицу
    RETURN QUERY
    SELECT 
        группа,
        количество_идентификаций,
        ROUND((количество_идентификаций::NUMERIC / NULLIF(v_всего, 0)) * 100, 2) as процент_от_общего
    FROM (
        SELECT 
            'Стрекозы'::VARCHAR(50) as группа,
            v_стрекозы as количество_идентификаций
        
        UNION ALL
        
        SELECT 
            'Жуки'::VARCHAR(50),
            v_жуки
        
        UNION ALL
        
        SELECT 
            'Бабочки'::VARCHAR(50),
            v_бабочки
        
        UNION ALL
        
        SELECT 
            'Другие насекомые'::VARCHAR(50),
            v_другие
        
        UNION ALL
        
        SELECT 
            'ВСЕГО'::VARCHAR(50),
            v_всего
    ) as статистика
    ORDER BY 
        CASE группа 
            WHEN 'ВСЕГО' THEN 5
            WHEN 'Другие насекомые' THEN 4
            ELSE 1 
        END,
        количество_идентификаций DESC;
END;
$$;

select * from а_статистика_групп_простая()

-- 4. Наблюдения пользователя все+
CREATE OR REPLACE FUNCTION пр_наблюдения_пользователя(
    p_id_пользователя BIGINT
)
RETURNS TABLE (
    id_наблюдения BIGINT,
    дата DATE,
    часть_дня VARCHAR(20),
    место_наблюдения varchar(200),
    вид_насекомого varchar(200),
    статус_точности int
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.id_наблюдения,
        n.дата,
        n.часть_дня,
        m.название,
        v.русское_название,
        s.значение
    FROM Наблюдение n
    JOIN МестоНаблюдения m ON n.id_места = m.id_места
    JOIN Идентификация i ON n.id_наблюдения = i.id_наблюдения
    JOIN ВидНасекомого v ON i.id_вида = v.id_вида
    LEFT JOIN СтатусТочности s ON i.id_статуса_точности = s.id_статуса_точности
    WHERE n.id_пользователя = p_id_пользователя
    ORDER BY n.id_наблюдения DESC;
END;
$$ LANGUAGE plpgsql;

select * from Пользователь

SELECT * FROM пр_наблюдения_пользователя(123456789);

-- 5. Наблюдения по месяцам в году+
CREATE OR REPLACE FUNCTION а_наблюдения_по_месяцам(
    p_год INT DEFAULT EXTRACT(YEAR FROM CURRENT_DATE)
) RETURNS TABLE (
    месяц VARCHAR(20),
    количество BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE Наблюдение.месяц
            WHEN 1 THEN 'январь' WHEN 2 THEN 'февраль' WHEN 3 THEN 'март' WHEN 4 THEN 'апрель'
            WHEN 5 THEN 'май' WHEN 6 THEN 'июнь' WHEN 7 THEN 'июль' WHEN 8 THEN 'август'
            WHEN 9 THEN 'сентябрь' WHEN 10 THEN 'октябрь' WHEN 11 THEN 'ноябрь' WHEN 12 THEN 'декабрь'
            ELSE 'неизвестно'
        END::VARCHAR(20) as месяц,  
        COUNT(id_наблюдения)::BIGINT
    FROM Наблюдение
    WHERE EXTRACT(YEAR FROM дата) = p_год
    GROUP BY Наблюдение.месяц
    ORDER BY Наблюдение.месяц;
END;
$$ LANGUAGE plpgsql;

select * from Наблюдение

select * from а_наблюдения_по_месяцам(2025)

-- 6. Топ пользователей по активности+
CREATE OR REPLACE FUNCTION а_топ_пользователей(
    p_количество INT DEFAULT 10
) RETURNS TABLE (
    пользователь TEXT,
    наблюдений BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.имя || ' ' || COALESCE(p.фамилия, '') as пользователь,
        COUNT(n.id_наблюдения)::BIGINT as наблюдений_кол
    FROM Пользователь p
    LEFT JOIN Наблюдение n ON n.id_пользователя = p.id_пользователя
    GROUP BY p.id_пользователя, p.имя, p.фамилия
    ORDER BY COUNT(n.id_наблюдения) DESC  
    LIMIT p_количество;
END;
$$ LANGUAGE plpgsql;

select * from а_топ_пользователей()

-- 7. Точность идентификаций по регионам*
CREATE OR REPLACE FUNCTION а_точность_по_регионам(
    p_регион VARCHAR DEFAULT NULL
) RETURNS TABLE (
    регион varchar,
    средняя_точность NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT r.название, ROUND(AVG(st.значение), 2)
    FROM Регион r
    JOIN МестоНаблюдения m ON m.id_региона = r.id_региона
    JOIN Наблюдение n ON n.id_места = m.id_места
    JOIN Идентификация i ON i.id_наблюдения = n.id_наблюдения
    JOIN СтатусТочности st ON st.id_статуса_точности = i.id_статуса_точности
    WHERE p_регион IS NULL OR LOWER(r.название) LIKE '%' || LOWER(p_регион) || '%'
    GROUP BY r.название
    ORDER BY средняя_точность DESC;
END;
$$ LANGUAGE plpgsql;

select * from Регион

select * from СтатусТочности

select * from а_точность_по_регионам('Московская область')

-- 8. Самые крупные стрекозы по размаху крыльев+
CREATE OR REPLACE FUNCTION а_самые_крупные_стрекозы(
    p_пол VARCHAR DEFAULT NULL
) RETURNS TABLE (
    вид varchar,
    пол varchar,
    размах_мм SMALLINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT v.русское_название, str.пол, str.макс_размах_крыльев
    FROM ВидНасекомого v
    JOIN Стрекоза str ON str.id_вида = v.id_вида
    WHERE p_пол IS NULL OR str.пол = p_пол
    ORDER BY str.макс_размах_крыльев DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

select * from а_самые_крупные_стрекозы('самка')

-- 9. Распределение видов по семействам*
CREATE OR REPLACE FUNCTION а_виды_по_семействам(
    p_мин_количество INT DEFAULT 1
) RETURNS TABLE (
    семейство varchar,
    количество_видов BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT вд.семейство, COUNT(id_вида)
    FROM ВидНасекомого вд
    GROUP BY вд.семейство
    HAVING COUNT(id_вида) >= p_мин_количество
    ORDER BY COUNT(id_вида) DESC;
END;
$$ LANGUAGE plpgsql;

select * from а_виды_по_семействам(3)

-- 10. Активность по частям дня в месяце*
CREATE OR REPLACE FUNCTION а_активность_по_частям_дня(
    p_месяц int
) RETURNS TABLE (
    часть_дня VARCHAR(10),
    количество BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT н.часть_дня, COUNT(id_наблюдения)
    FROM Наблюдение н
    WHERE месяц = p_месяц
    GROUP BY н.часть_дня
    ORDER BY COUNT(id_наблюдения) DESC;
END;
$$ LANGUAGE plpgsql;

select * from Наблюдение

select * from а_активность_по_частям_дня(6)