-- 1. Проверка сезона при идентификации+
CREATE OR REPLACE FUNCTION trig_check_season() RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM ВидНасекомого v
        JOIN Сезонность s ON v.id_сезонности = s.id_сезонности
        JOIN Наблюдение n ON n.id_наблюдения = NEW.id_наблюдения
        WHERE v.id_вида = NEW.id_вида AND n.месяц BETWEEN s.первый_месяц AND s.последний_месяц
    ) THEN
        RAISE EXCEPTION 'Вид не летает в этот месяц!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_ident_season
BEFORE INSERT OR UPDATE ON Идентификация
FOR EACH ROW EXECUTE PROCEDURE trig_check_season();

select * from Идентификация
select * from ВидНасекомого

update Идентификация
set id_вида=10
where id_идентификации=16


-- 3. Запрет удаления вида с наблюдениями
CREATE OR REPLACE FUNCTION trig_prevent_delete_species() RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM Идентификация WHERE id_вида = OLD.id_вида) THEN
        RAISE EXCEPTION 'Нельзя удалить вид с существующими наблюдениями!';
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_species_delete
BEFORE DELETE ON ВидНасекомого
FOR EACH ROW EXECUTE PROCEDURE trig_prevent_delete_species();

-- Это должно вызвать исключение
DELETE FROM ВидНасекомого WHERE id_вида = 14;


-- 1. Функция триггера
CREATE OR REPLACE FUNCTION проверка_максимума_стрекоз()
RETURNS TRIGGER AS $$
BEGIN
    -- Проверяем, сколько уже есть записей для этого id_вида
    PERFORM 1
    FROM Стрекоза
    WHERE id_вида = NEW.id_вида
    HAVING COUNT(*) >= 2;


    IF FOUND THEN
        RAISE EXCEPTION 'Для вида с id_вида=% уже зарегистрированы 2 особи (самец и самка). Добавление третьей запрещено.', NEW.id_вида;
    END IF;

    RETURN NEW;  -- Разрешаем вставку, если меньше 2 записей
END;
$$ LANGUAGE plpgsql;


-- 2. Сам триггер
CREATE TRIGGER триггер_лимита_стрекоз
BEFORE INSERT ON Стрекоза
FOR EACH ROW EXECUTE PROCEDURE проверка_максимума_стрекоз();

select * from Стрекоза

INSERT INTO Стрекоза (
    id_вида, 
    пол, 
    цвет_глаз, 
    мин_длина_тела, 
    макс_длина_тела, 
    мин_размах_крыльев, 
    макс_размах_крыльев, 
    основной_цвет, 
    особенности
) VALUES (
    1,                      
    'самец',                
    'голубой',                
    35,                       
    45,                       
    65,                       
    75,                       
    'синий',                  
    'Пятна на крыльях'        
);

-- 4. Авто-обновление даты идентификации
CREATE OR REPLACE FUNCTION fn_обновить_дату_идентификации() 
RETURNS TRIGGER 
AS $$
DECLARE
    v_старая_дата DATE;
    v_обновлена_дата BOOLEAN := FALSE;
BEGIN
    -- Сохраняем старую дату для сравнения
    v_старая_дата := OLD.дата;
    
    -- Обновляем дату только при INSERT, при UPDATE меняем только если это нужно
    IF TG_OP = 'INSERT' THEN
        NEW.дата = CURRENT_DATE;
        v_обновлена_дата := TRUE;
        
        RAISE NOTICE 'Создана новая идентификация. Дата установлена: %', CURRENT_DATE;
        
    ELSIF TG_OP = 'UPDATE' THEN
        IF OLD.id_статуса_точности IS DISTINCT FROM NEW.id_статуса_точности 
           OR OLD.id_вида IS DISTINCT FROM NEW.id_вида THEN
            
            NEW.дата = CURRENT_DATE;
            v_обновлена_дата := TRUE;
            
            RAISE NOTICE 'Дата идентификации обновлена:';
            RAISE NOTICE '  Старая дата: %', v_старая_дата;
            RAISE NOTICE '  Новая дата: %', CURRENT_DATE;
            RAISE NOTICE '  Текущее время: %', CURRENT_TIMESTAMP;
            
            -- Дополнительная информация о том, что изменилось
            IF OLD.id_статуса_точности IS DISTINCT FROM NEW.id_статуса_точности THEN
                RAISE NOTICE '  Изменен статус точности: % → %', 
                            OLD.id_статуса_точности, NEW.id_статуса_точности;
            END IF;
            
            IF OLD.id_вида IS DISTINCT FROM NEW.id_вида THEN
                RAISE NOTICE '  Изменен вид: % → %', OLD.id_вида, NEW.id_вида;
            END IF;
            
            IF OLD.id_пользователя IS DISTINCT FROM NEW.id_пользователя THEN
                RAISE NOTICE '  Изменен пользователь: % → %', 
                            OLD.id_пользователя, NEW.id_пользователя;
            END IF;
        ELSE
            RAISE NOTICE 'Дата идентификации не изменена (критичные поля не изменились)';
            RAISE NOTICE '  Текущая дата: %', v_старая_дата;
            RAISE NOTICE '  Текущее время сервера: %', CURRENT_TIMESTAMP;
        END IF;
    END IF;
    
    RETURN NEW;
    
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION 'Ошибка при обновлении даты идентификации: %', SQLERRM;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_обновить_дату_идентификации
BEFORE INSERT OR UPDATE ON Идентификация
FOR EACH ROW EXECUTE FUNCTION fn_обновить_дату_идентификации();

select * from Идентификация

update Идентификация
set id_вида=4
where id_идентификации=13






