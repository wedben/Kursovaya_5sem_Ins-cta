"""
Скрипт для полной настройки базы данных
Создает базу данных, таблицы и добавляет тестовые данные
"""
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def check_postgresql():
    """Проверка доступности PostgreSQL"""
    try:
        # Пытаемся подключиться к серверу PostgreSQL (без указания базы данных)
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'  # Подключаемся к системной базе
        )
        conn.close()
        return True
    except psycopg2.Error as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("\n💡 Убедитесь, что:")
        print("   1. PostgreSQL установлен и запущен")
        print("   2. Параметры в .env файле правильные")
        print("   3. Пользователь имеет права на создание баз данных")
        return False

def create_database():
    """Создание базы данных, если её нет"""
    try:
        # Подключаемся к системной базе postgres
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Проверяем, существует ли база данных
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_CONFIG['database'],)
        )
        
        if cursor.fetchone():
            print(f"✅ База данных '{DB_CONFIG['database']}' уже существует")
        else:
            # Создаем базу данных
            cursor.execute(f'CREATE DATABASE {DB_CONFIG["database"]}')
            print(f"✅ База данных '{DB_CONFIG['database']}' создана")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка при создании базы данных: {e}")
        return False

def create_tables():
    """Создание таблиц из SQL файла"""
    try:
        # Читаем SQL файл
        sql_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'create_tables.sql')
        if not os.path.exists(sql_file):
            print(f"❌ Файл {sql_file} не найден!")
            return False
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Подключаемся к нашей базе данных
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
        
        print("✅ Таблицы созданы успешно")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def add_sample_data():
    """Добавление тестовых данных"""
    try:
        # Импортируем из текущей директории scripts
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from init_db import init_sample_data
        from init_additional_tables import init_additional_data
        
        print("\n📝 Добавление тестовых данных...")
        init_sample_data()
        init_additional_data()
        print("✅ Тестовые данные добавлены")
        return True
    except Exception as e:
        print(f"⚠️  Ошибка при добавлении тестовых данных: {e}")
        print("   Продолжаем без тестовых данных...")
        return False

def main():
    """Основная функция настройки"""
    print("🚀 Настройка базы данных для проекта 'Определитель насекомых'\n")
    
    # Проверка подключения
    print("1️⃣  Проверка подключения к PostgreSQL...")
    if not check_postgresql():
        sys.exit(1)
    
    # Создание базы данных
    print("\n2️⃣  Создание базы данных...")
    if not create_database():
        sys.exit(1)
    
    # Создание таблиц
    print("\n3️⃣  Создание таблиц...")
    if not create_tables():
        sys.exit(1)
    
    # Добавление тестовых данных
    print("\n4️⃣  Добавление тестовых данных...")
    add_sample_data()
    
    print("\n" + "="*50)
    print("✅ База данных успешно настроена!")
    print("="*50)
    print(f"\n📊 Параметры подключения:")
    print(f"   Хост: {DB_CONFIG['host']}")
    print(f"   Порт: {DB_CONFIG['port']}")
    print(f"   База данных: {DB_CONFIG['database']}")
    print(f"   Пользователь: {DB_CONFIG['user']}")
    print("\n🎉 Теперь можно запускать приложение: python app.py")

if __name__ == '__main__':
    main()

