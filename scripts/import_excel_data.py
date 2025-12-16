"""
Скрипт для импорта данных из Excel файлов в базу данных PostgreSQL
"""
import sys
import os
import pandas as pd
import re
from typing import Dict, Any, Optional

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import Database

def parse_size_range(size_str: str) -> tuple[Optional[float], Optional[float]]:
    """Парсит строку размера вида '60–72' или '20-28' в (min, max)"""
    if pd.isna(size_str) or not str(size_str).strip():
        return None, None
    
    size_str = str(size_str).strip()
    # Заменяем различные тире на дефис
    size_str = re.sub(r'[–—−]', '-', size_str)
    
    # Ищем паттерн числа-дефис-число
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)', size_str)
    if match:
        min_val = float(match.group(1).replace(',', '.'))
        max_val = float(match.group(2).replace(',', '.'))
        return min_val, max_val
    
    # Если только одно число
    match = re.search(r'(\d+(?:[.,]\d+)?)', size_str)
    if match:
        val = float(match.group(1).replace(',', '.'))
        return val, val
    
    return None, None

def clean_text(text: Any) -> Optional[str]:
    """Очищает текст от NaN и лишних пробелов"""
    if pd.isna(text):
        return None
    text = str(text).strip()
    return text if text else None

def import_dragonflies(filename: str = None):
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'стрекозы.xlsx')
    """Импорт стрекоз из Excel файла"""
    print(f"\n🦟 Импорт стрекоз из {filename}...")
    
    df = pd.read_excel(filename)
    db = Database()
    
    imported = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Парсим размеры
            body_min, body_max = parse_size_range(row.get('Приблизительный размер (длина тела, мм)', ''))
            wingspan_min, wingspan_max = parse_size_range(row.get('Приблизительный размер (размах крыльев, мм)', ''))
            
            # Формируем данные для таблицы dragonflies
            data = {
                'name_ru': clean_text(row.get('Русское название', '')),
                'name_lat': clean_text(row.get('Латинское название', '')),
                'size_min': body_min,
                'size_max': body_max,
                'color': clean_text(row.get('Основной цвет', '')),
                'habitat': clean_text(row.get('Место нахождения', '')),
                'season': clean_text(row.get('Период', '')),
                'description': None
            }
            
            # Формируем описание из дополнительных полей
            desc_parts = []
            if clean_text(row.get('Добавочный цвет')):
                desc_parts.append(f"Добавочный цвет: {clean_text(row.get('Добавочный цвет'))}")
            if clean_text(row.get('Тип цвета')):
                desc_parts.append(f"Тип цвета: {clean_text(row.get('Тип цвета'))}")
            if clean_text(row.get('Цвет глаз')):
                desc_parts.append(f"Цвет глаз: {clean_text(row.get('Цвет глаз'))}")
            if clean_text(row.get('Среда (тип водоёма)')):
                desc_parts.append(f"Среда: {clean_text(row.get('Среда (тип водоёма)'))}")
            if clean_text(row.get('Пол')):
                desc_parts.append(f"Пол: {clean_text(row.get('Пол'))}")
            if clean_text(row.get('Семейство')):
                desc_parts.append(f"Семейство: {clean_text(row.get('Семейство'))}")
            if clean_text(row.get('Подотряд')):
                desc_parts.append(f"Подотряд: {clean_text(row.get('Подотряд'))}")
            
            if wingspan_min or wingspan_max:
                wingspan_str = f"{wingspan_min or ''}–{wingspan_max or ''}".strip('–')
                desc_parts.append(f"Размах крыльев: {wingspan_str} мм")
            
            if desc_parts:
                data['description'] = '; '.join(desc_parts)
            
            # Проверяем обязательные поля
            if not data['name_ru']:
                print(f"  ⚠️  Строка {idx + 2}: пропущена (нет русского названия)")
                errors += 1
                continue
            
            # Добавляем в базу данных
            db.add_insect('dragonfly', data)
            imported += 1
            
            if (imported + errors) % 10 == 0:
                print(f"  Обработано: {imported + errors} строк...")
                
        except Exception as e:
            print(f"  ❌ Ошибка в строке {idx + 2}: {e}")
            errors += 1
    
    print(f"✅ Импортировано стрекоз: {imported}")
    if errors > 0:
        print(f"⚠️  Ошибок: {errors}")
    return imported, errors

def import_beetles(filename: str = None):
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'жужжелицы.xlsx')
    """Импорт жуков из Excel файла"""
    print(f"\n🪲 Импорт жуков из {filename}...")
    
    df = pd.read_excel(filename)
    db = Database()
    
    imported = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Парсим размер
            size_min, size_max = parse_size_range(row.get('Размер (длина тела, мм)', ''))
            
            # Формируем данные
            data = {
                'name_ru': clean_text(row.get('Русское название', '')),
                'name_lat': None,
                'size_min': size_min,
                'size_max': size_max,
                'color': clean_text(row.get('Основной цвет', '')),
                'habitat': clean_text(row.get('Место нахождения', '')),
                'season': clean_text(row.get('Активность / Период', '')),
                'description': None
            }
            
            # Формируем латинское название из рода и вида
            genus = clean_text(row.get('Род', ''))
            species = clean_text(row.get('Вид', ''))
            if genus and species:
                data['name_lat'] = f"{genus} {species}"
            
            # Формируем описание
            desc_parts = []
            if clean_text(row.get('Добавочный цвет / Особенности')):
                desc_parts.append(f"Особенности: {clean_text(row.get('Добавочный цвет / Особенности'))}")
            if clean_text(row.get('Тип поверхности / Блеск')):
                desc_parts.append(f"Тип поверхности: {clean_text(row.get('Тип поверхности / Блеск'))}")
            if clean_text(row.get('Надкрылья')):
                desc_parts.append(f"Надкрылья: {clean_text(row.get('Надкрылья'))}")
            if clean_text(row.get('Цвет глаз')):
                desc_parts.append(f"Цвет глаз: {clean_text(row.get('Цвет глаз'))}")
            if clean_text(row.get('Среда обитания (биотоп)')):
                desc_parts.append(f"Биотоп: {clean_text(row.get('Среда обитания (биотоп)'))}")
            if clean_text(row.get('Пол')):
                desc_parts.append(f"Пол: {clean_text(row.get('Пол'))}")
            if clean_text(row.get('Семейство')):
                desc_parts.append(f"Семейство: {clean_text(row.get('Семейство'))}")
            if genus:
                desc_parts.append(f"Род: {genus}")
            
            if desc_parts:
                data['description'] = '; '.join(desc_parts)
            
            # Проверяем обязательные поля
            if not data['name_ru']:
                print(f"  ⚠️  Строка {idx + 2}: пропущена (нет русского названия)")
                errors += 1
                continue
            
            # Добавляем в базу данных
            db.add_insect('beetle', data)
            imported += 1
            
            if (imported + errors) % 10 == 0:
                print(f"  Обработано: {imported + errors} строк...")
                
        except Exception as e:
            print(f"  ❌ Ошибка в строке {idx + 2}: {e}")
            errors += 1
    
    print(f"✅ Импортировано жуков: {imported}")
    if errors > 0:
        print(f"⚠️  Ошибок: {errors}")
    return imported, errors

def import_butterflies(filename: str = None):
    if filename is None:
        filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'Бабочки.xlsx')
    """Импорт бабочек из Excel файла"""
    print(f"\n🦋 Импорт бабочек из {filename}...")
    
    # Бабочки имеют заголовок в первой строке, пропускаем её
    df = pd.read_excel(filename, header=1)
    
    # Очищаем названия колонок от лишних пробелов
    df.columns = df.columns.str.strip()
    
    db = Database()
    
    imported = 0
    errors = 0
    
    for idx, row in df.iterrows():
        try:
            # Парсим размах крыльев
            wingspan_min, wingspan_max = parse_size_range(row.get('Размах крыльев (мм)', ''))
            
            # Формируем данные
            data = {
                'name_ru': clean_text(row.get('Русское название', '')),
                'name_lat': None,
                'size_min': wingspan_min,
                'size_max': wingspan_max,
                'color': clean_text(row.get('Основной цвет крыльев (верх)', '')),
                'habitat': clean_text(row.get('Место нахождения', '')),
                'season': clean_text(row.get('Лёт (период)', '')),
                'description': None
            }
            
            # Формируем латинское название
            genus = clean_text(row.get('Род', ''))
            species = clean_text(row.get('Вид', ''))
            if genus and species:
                data['name_lat'] = f"{genus} {species}"
            
            # Формируем описание
            desc_parts = []
            if clean_text(row.get('Особенности рисунка крыльев')):
                desc_parts.append(f"Рисунок: {clean_text(row.get('Особенности рисунка крыльев'))}")
            if clean_text(row.get('Цвет тела / Опушение')):
                desc_parts.append(f"Тело: {clean_text(row.get('Цвет тела / Опушение'))}")
            if clean_text(row.get('Цвет глаз')):
                desc_parts.append(f"Цвет глаз: {clean_text(row.get('Цвет глаз'))}")
            if clean_text(row.get('Гусеница (основной цвет)')):
                desc_parts.append(f"Гусеница: {clean_text(row.get('Гусеница (основной цвет)'))}")
            if clean_text(row.get('Кормовое растение гусениц')):
                desc_parts.append(f"Кормовое растение: {clean_text(row.get('Кормовое растение гусениц'))}")
            if clean_text(row.get('Пол')):
                desc_parts.append(f"Пол: {clean_text(row.get('Пол'))}")
            if clean_text(row.get('Семейство', '')):
                desc_parts.append(f"Семейство: {clean_text(row.get('Семейство', ''))}")
            if genus:
                desc_parts.append(f"Род: {genus}")
            
            if desc_parts:
                data['description'] = '; '.join(desc_parts)
            
            # Проверяем обязательные поля
            if not data['name_ru']:
                print(f"  ⚠️  Строка {idx + 3}: пропущена (нет русского названия)")
                errors += 1
                continue
            
            # Добавляем в базу данных
            db.add_insect('butterfly', data)
            imported += 1
            
            if (imported + errors) % 10 == 0:
                print(f"  Обработано: {imported + errors} строк...")
                
        except Exception as e:
            print(f"  ❌ Ошибка в строке {idx + 3}: {e}")
            errors += 1
    
    print(f"✅ Импортировано бабочек: {imported}")
    if errors > 0:
        print(f"⚠️  Ошибок: {errors}")
    return imported, errors

def main():
    """Основная функция импорта"""
    print("=" * 60)
    print("📥 ИМПОРТ ДАННЫХ ИЗ EXCEL В БАЗУ ДАННЫХ")
    print("=" * 60)
    
    total_imported = 0
    total_errors = 0
    
    # Импорт стрекоз
    try:
        imported, errors = import_dragonflies()
        total_imported += imported
        total_errors += errors
    except Exception as e:
        print(f"❌ Критическая ошибка при импорте стрекоз: {e}")
    
    # Импорт жуков
    try:
        imported, errors = import_beetles()
        total_imported += imported
        total_errors += errors
    except Exception as e:
        print(f"❌ Критическая ошибка при импорте жуков: {e}")
    
    # Импорт бабочек
    try:
        imported, errors = import_butterflies()
        total_imported += imported
        total_errors += errors
    except Exception as e:
        print(f"❌ Критическая ошибка при импорте бабочек: {e}")
    
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    print(f"✅ Всего импортировано: {total_imported}")
    if total_errors > 0:
        print(f"⚠️  Всего ошибок: {total_errors}")
    print("=" * 60)

if __name__ == '__main__':
    main()

