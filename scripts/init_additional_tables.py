"""
Скрипт для инициализации дополнительных таблиц с примерами данных
(СтатусТочности, Биотоп и т.д.)
"""
import sys
import os
import psycopg2

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database

def init_additional_data():
    """Инициализация дополнительных таблиц с базовыми данными"""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Добавляем статусы точности
        print("Добавление статусов точности...")
        statuses = [
            'точно',
            'вероятно',
            'возможно',
            'неопределенно'
        ]
        
        for status in statuses:
            try:
                cursor.execute(
                    'INSERT INTO "СтатусТочности" (значение) VALUES (%s) ON CONFLICT (значение) DO NOTHING',
                    (status,)
                )
            except Exception as e:
                print(f"Ошибка при добавлении статуса '{status}': {e}")
        
        # Добавляем примеры биотопов
        print("Добавление биотопов...")
        biotopes = [
            ('Лес', 'Лесные массивы, смешанные и хвойные леса'),
            ('Луг', 'Луговые пространства, поляны'),
            ('Водоем', 'Озера, пруды, реки, ручьи'),
            ('Болото', 'Болотистые местности'),
            ('Сад', 'Садовые участки, парки'),
            ('Город', 'Городские территории'),
            ('Степь', 'Степные пространства'),
        ]
        
        for name, desc in biotopes:
            try:
                cursor.execute(
                    'INSERT INTO "Биотоп" (название, описание) VALUES (%s, %s) ON CONFLICT (название) DO NOTHING',
                    (name, desc)
                )
            except Exception as e:
                print(f"Ошибка при добавлении биотопа '{name}': {e}")
        
        conn.commit()
        print("Дополнительные таблицы инициализированы успешно!")
        
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_additional_data()


