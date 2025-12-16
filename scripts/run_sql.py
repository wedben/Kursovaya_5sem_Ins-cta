"""
Скрипт для выполнения SQL файла в PostgreSQL
Использование: python run_sql.py sql/create_tables.sql
"""
import sys
import os
import psycopg2

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def execute_sql_file(filename):
    """Выполнить SQL файл в базе данных"""
    try:
        # Читаем SQL файл
        with open(filename, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Подключаемся к базе данных
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        
        cursor = conn.cursor()
        
        # Выполняем SQL
        cursor.execute(sql)
        conn.commit()
        
        print(f"SQL файл {filename} успешно выполнен!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Ошибка при выполнении SQL: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Файл {filename} не найден!")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python run_sql.py <sql_file>")
        print("Пример: python run_sql.py create_tables.sql")
        sys.exit(1)
    
    execute_sql_file(sys.argv[1])

