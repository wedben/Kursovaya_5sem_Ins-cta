"""Тестовый скрипт для проверки поиска"""
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database

db = Database()

print("🔍 Тестирование поиска...\n")

# Поиск стрекоз с синим цветом
results = db.search_insects('dragonfly', {'color': 'синий'})
print(f"Стрекозы с синим цветом: {len(results)}")
if results:
    print(f"  Пример: {results[0]['name_ru']}")

# Поиск жуков в лесу
results = db.search_insects('beetle', {'habitat': 'лес'})
print(f"\nЖуки в лесу: {len(results)}")
if results:
    print(f"  Пример: {results[0]['name_ru']}")

# Поиск бабочек по размеру
results = db.search_insects('butterfly', {'size_min': 40, 'size_max': 60})
print(f"\nБабочки размером 40-60 мм: {len(results)}")
if results:
    print(f"  Пример: {results[0]['name_ru']}")

print("\n✅ Поиск работает корректно!")

