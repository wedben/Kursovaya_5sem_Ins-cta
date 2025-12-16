"""
Скрипт для инициализации базы данных с примерами данных
"""
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database

def init_sample_data():
    db = Database()
    
    # Примеры стрекоз
    dragonflies = [
        {
            'name_ru': 'Стрекоза обыкновенная',
            'name_lat': 'Libellula quadrimaculata',
            'size_min': 40.0,
            'size_max': 50.0,
            'color': 'коричневый, желтый',
            'habitat': 'водоемы, пруды, озера',
            'season': 'лето',
            'description': 'Среднего размера стрекоза с характерными темными пятнами на крыльях. Обитает вблизи стоячих водоемов.'
        },
        {
            'name_ru': 'Стрекоза коромысло большое',
            'name_lat': 'Aeshna grandis',
            'size_min': 70.0,
            'size_max': 85.0,
            'color': 'синий, коричневый',
            'habitat': 'леса, водоемы',
            'season': 'лето',
            'description': 'Крупная стрекоза с размахом крыльев до 10 см. Обитает в лесных водоемах.'
        },
        {
            'name_ru': 'Стрекоза стрелка-девушка',
            'name_lat': 'Calopteryx virgo',
            'size_min': 45.0,
            'size_max': 50.0,
            'color': 'синий, металлический',
            'habitat': 'реки, ручьи',
            'season': 'лето',
            'description': 'Красивая стрекоза с металлическим синим блеском. Предпочитает проточные воды.'
        }
    ]
    
    # Примеры жуков
    beetles = [
        {
            'name_ru': 'Жук-олень',
            'name_lat': 'Lucanus cervus',
            'size_min': 30.0,
            'size_max': 75.0,
            'color': 'коричневый, черный',
            'habitat': 'леса, дубравы',
            'season': 'лето',
            'description': 'Крупный жук с характерными рогами у самцов. Обитает в старых лесах, особенно дубовых.'
        },
        {
            'name_ru': 'Божья коровка семиточечная',
            'name_lat': 'Coccinella septempunctata',
            'size_min': 5.0,
            'size_max': 8.0,
            'color': 'красный, черный',
            'habitat': 'луга, сады, поля',
            'season': 'весна, лето, осень',
            'description': 'Небольшой жук с семью черными точками на красных надкрыльях. Полезен для садоводов.'
        },
        {
            'name_ru': 'Майский жук',
            'name_lat': 'Melolontha melolontha',
            'size_min': 20.0,
            'size_max': 30.0,
            'color': 'коричневый, черный',
            'habitat': 'леса, парки, сады',
            'season': 'весна, май',
            'description': 'Среднего размера жук, появляющийся в мае. Личинки могут вредить корням растений.'
        }
    ]
    
    # Добавляем данные в базу
    print("Добавление примеров стрекоз...")
    for dragonfly in dragonflies:
        db.add_insect('dragonfly', dragonfly)
    
    print("Добавление примеров жуков...")
    for beetle in beetles:
        db.add_insect('beetle', beetle)
    
    print("База данных инициализирована успешно!")
    print(f"Добавлено стрекоз: {len(dragonflies)}")
    print(f"Добавлено жуков: {len(beetles)}")

if __name__ == '__main__':
    init_sample_data()

