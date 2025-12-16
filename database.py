import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Optional
import re
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.config = DB_CONFIG
        # Не создаем таблицы автоматически - они должны быть созданы через SQL скрипт
    
    def get_connection(self):
        """Получить подключение к PostgreSQL"""
        return psycopg2.connect(
            host=self.config['host'],
            port=self.config['port'],
            database=self.config['database'],
            user=self.config['user'],
            password=self.config['password']
        )
    
    def search_insects(self, insect_type: str, params: Dict) -> List[Dict]:
        """
        Поиск насекомых по параметрам
        
        Args:
            insect_type: 'dragonfly', 'beetle' или 'butterfly'
            params: словарь с параметрами поиска (size, color, habitat, season и т.д.)
        
        Returns:
            Список найденных насекомых
        """
        # Правильные имена таблиц
        table_names = {
            'dragonfly': 'dragonflies',
            'beetle': 'beetles',
            'butterfly': 'butterflies'
        }
        table_name = table_names.get(insect_type)
        if not table_name:
            raise ValueError(f"Неверный тип насекомого: {insect_type}")
        
        conn = self.get_connection()
        # Используем RealDictCursor для получения результатов в виде словарей
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Формируем запрос с условиями
        query = f"SELECT * FROM {table_name} WHERE 1=1"
        conditions = []
        values = []
        
        # Общие параметры
        if params.get('size_min'):
            conditions.append("size_max >= %s")
            values.append(float(params['size_min']))
        
        if params.get('size_max'):
            conditions.append("size_min <= %s")
            values.append(float(params['size_max']))
        
        if params.get('color'):
            conditions.append("color ILIKE %s")
            values.append(f"%{params['color']}%")
        
        if params.get('habitat'):
            conditions.append("habitat ILIKE %s")
            values.append(f"%{params['habitat']}%")
        
        if params.get('season'):
            conditions.append("season ILIKE %s")
            values.append(f"%{params['season']}%")
        
        # Специфичные параметры для стрекоз
        if insect_type == 'dragonfly':
            if params.get('body_length_min'):
                conditions.append("size_max >= %s")
                values.append(float(params['body_length_min']))
            
            if params.get('body_length_max'):
                conditions.append("size_min <= %s")
                values.append(float(params['body_length_max']))
            
            if params.get('wingspan_min') or params.get('wingspan_max'):
                # Ищем в описании размах крыльев
                if params.get('wingspan_min'):
                    conditions.append("description ILIKE %s")
                    values.append(f"%размах%{params['wingspan_min']}%")
                if params.get('wingspan_max'):
                    conditions.append("description ILIKE %s")
                    values.append(f"%размах%{params['wingspan_max']}%")
            
            if params.get('eye_color'):
                conditions.append("description ILIKE %s")
                values.append(f"%цвет глаз%{params['eye_color']}%")
            
            if params.get('environment'):
                conditions.append("description ILIKE %s")
                values.append(f"%среда%{params['environment']}%")
            
            if params.get('gender'):
                conditions.append("description ILIKE %s")
                values.append(f"%пол%{params['gender']}%")
        
        # Специфичные параметры для жуков
        elif insect_type == 'beetle':
            if params.get('surface_type'):
                conditions.append("description ILIKE %s")
                values.append(f"%{params['surface_type']}%")
            
            if params.get('elytra'):
                conditions.append("description ILIKE %s")
                values.append(f"%надкрылья%{params['elytra']}%")
        
        # Специфичные параметры для бабочек
        elif insect_type == 'butterfly':
            if params.get('wing_pattern'):
                conditions.append("description ILIKE %s")
                values.append(f"%рисунок%{params['wing_pattern']}%")
            
            if params.get('time_of_day'):
                # Ищем в описании информацию о времени суток
                time_keywords = {
                    'день': ['дневн', 'днем', 'днём', 'дневная'],
                    'ночь': ['ночн', 'ночью', 'ночная']
                }
                if params['time_of_day'] in time_keywords:
                    time_conditions = []
                    for keyword in time_keywords[params['time_of_day']]:
                        time_conditions.append("description ILIKE %s")
                        values.append(f"%{keyword}%")
                    if time_conditions:
                        conditions.append("(" + " OR ".join(time_conditions) + ")")
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        
        cursor.execute(query, values)
        
        # Получаем результаты в виде словарей
        results = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        return results
    
    def get_all_insects(self, insect_type: str) -> List[Dict]:
        """Получить все насекомые определенного типа"""
        # Правильные имена таблиц
        table_names = {
            'dragonfly': 'dragonflies',
            'beetle': 'beetles',
            'butterfly': 'butterflies'
        }
        table_name = table_names.get(insect_type)
        if not table_name:
            raise ValueError(f"Неверный тип насекомого: {insect_type}")
        
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute(f"SELECT * FROM {table_name}")
        
        # Получаем результаты в виде словарей
        results = [dict(row) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        return results
    
    def add_insect(self, insect_type: str, data: Dict):
        """Добавить насекомое в базу данных"""
        # Правильные имена таблиц
        table_names = {
            'dragonfly': 'dragonflies',
            'beetle': 'beetles',
            'butterfly': 'butterflies'
        }
        table_name = table_names.get(insect_type)
        if not table_name:
            raise ValueError(f"Неверный тип насекомого: {insect_type}")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        columns = ', '.join(data.keys())
        # PostgreSQL использует %s для параметров
        placeholders = ', '.join(['%s' for _ in data])
        values = list(data.values())
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)
        
        conn.commit()
        cursor.close()
        conn.close()
    
    def get_filter_options(self, insect_type: str) -> Dict:
        """Получить уникальные значения для фильтров из базы данных"""
        table_names = {
            'dragonfly': 'dragonflies',
            'beetle': 'beetles',
            'butterfly': 'butterflies'
        }
        table_name = table_names.get(insect_type)
        if not table_name:
            raise ValueError(f"Неверный тип насекомого: {insect_type}")
        
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        options = {}
        
        if insect_type == 'dragonfly':
            # Базовые цвета для быстрого поиска
            basic_colors = [
                'синий', 'голубой', 'зелёный', 'жёлтый', 'красный', 
                'коричневый', 'чёрный', 'белый', 'оранжевый', 'фиолетовый',
                'бронзовый', 'металлический', 'серый'
            ]
            options['basic_colors'] = basic_colors
            
            # Получаем уникальные основные цвета из поля color
            cursor.execute(f"""
                SELECT DISTINCT color
                FROM {table_name}
                WHERE color IS NOT NULL AND color != ''
                ORDER BY color
            """)
            main_colors = []
            for row in cursor.fetchall():
                color_str = row['color']
                if color_str:
                    # Разбиваем цвета, если они разделены запятыми
                    colors = [c.strip() for c in color_str.split(',')]
                    main_colors.extend(colors)
            
            # Очищаем странные значения
            cleaned_colors = []
            exclude_patterns = [
                'более', 'менее', 'чем у', 'вариа', 'светл', 'тускл',
                'чем у самца', 'чем у S.', 'sanguineum', 'торокс', 'брюшко',
                'сегмент', 'отметин', 'пятно', 'полос', 'рисунок', 'фон',
                'пруинов', 'отлив', 'блеск', 'грудь', 'U-образн'
            ]
            
            for color in main_colors:
                if color and len(color) > 2:
                    color_lower = color.lower()
                    # Пропускаем цвета с исключающими паттернами
                    if not any(pattern in color_lower for pattern in exclude_patterns):
                        # Ограничиваем длину
                        if len(color) < 80:
                            cleaned_colors.append(color)
            
            # Убираем дубликаты и сортируем
            options['colors'] = sorted(list(set(cleaned_colors)))
            
            # Базовые цвета глаз для быстрого поиска
            basic_eye_colors = [
                'зелёные', 'коричневые', 'чёрные', 'синие', 'голубые',
                'красные', 'жёлтые', 'серые'
            ]
            options['basic_eye_colors'] = basic_eye_colors
            
            # Получаем уникальные цвета глаз из описания
            cursor.execute(f"""
                SELECT description
                FROM {table_name}
                WHERE description IS NOT NULL AND description ILIKE '%цвет глаз%'
            """)
            eye_colors_set = set()
            for row in cursor.fetchall():
                desc = row['description']
                # Ищем паттерн "Цвет глаз: ..."
                matches = re.findall(r'Цвет глаз:\s*([^;]+)', desc, re.IGNORECASE)
                for match in matches:
                    color = match.strip()
                    if color and len(color) < 100:
                        eye_colors_set.add(color)
            
            # Очищаем странные значения для цветов глаз
            cleaned_eye_colors = []
            exclude_patterns_eye = [
                'сверху', 'снизу', 'пятно', 'отлив', 'или', '/', 'вариа'
            ]
            
            for color in eye_colors_set:
                if color and len(color) > 2:
                    color_lower = color.lower()
                    # Пропускаем слишком сложные описания
                    if not any(pattern in color_lower for pattern in exclude_patterns_eye):
                        if len(color) < 50:
                            cleaned_eye_colors.append(color)
                    else:
                        # Если содержит "или", берем первую часть
                        if ' или ' in color_lower or ' / ' in color_lower:
                            first_part = color.split(' или ')[0].split(' / ')[0].strip()
                            if first_part and len(first_part) < 30:
                                cleaned_eye_colors.append(first_part)
                        else:
                            # Берем основную часть до запятой
                            main_part = color.split(',')[0].strip()
                            if main_part and len(main_part) < 50:
                                cleaned_eye_colors.append(main_part)
            
            # Убираем дубликаты и сортируем
            options['eye_colors'] = sorted(list(set(cleaned_eye_colors)))
            
            # Базовые места нахождения для быстрого поиска
            basic_habitats = [
                'лес', 'луг', 'водоем', 'сад', 'поле', 'болото', 
                'река', 'озеро', 'пруд', 'ручей', 'берег', 'опушка'
            ]
            options['basic_habitats'] = basic_habitats
            
            # Получаем все уникальные места нахождения
            cursor.execute(f"""
                SELECT DISTINCT habitat
                FROM {table_name}
                WHERE habitat IS NOT NULL AND habitat != ''
                ORDER BY habitat
            """)
            all_habitats = [row['habitat'] for row in cursor.fetchall()]
            options['habitats'] = all_habitats
            options['all_habitats'] = all_habitats  # Для совместимости
            
            # Получаем уникальные среды (тип водоёма) из описания
            cursor.execute(f"""
                SELECT description
                FROM {table_name}
                WHERE description IS NOT NULL AND description ILIKE '%среда%'
            """)
            environments_set = set()
            for row in cursor.fetchall():
                desc = row['description']
                # Ищем паттерн "Среда: ..."
                matches = re.findall(r'Среда:\s*([^;]+)', desc, re.IGNORECASE)
                for match in matches:
                    env = match.strip()
                    if env and len(env) < 150:
                        environments_set.add(env)
            options['environments'] = sorted(list(environments_set))
            
            # Получаем уникальные периоды
            cursor.execute(f"""
                SELECT DISTINCT season
                FROM {table_name}
                WHERE season IS NOT NULL AND season != ''
                ORDER BY season
            """)
            options['seasons'] = [row['season'] for row in cursor.fetchall()]
        
        elif insect_type == 'beetle':
            # Базовые цвета для жуков
            basic_colors = [
                'чёрный', 'бронзовый', 'зелёный', 'коричневый', 'красный',
                'синий', 'фиолетовый', 'золотистый', 'медный', 'металлический'
            ]
            options['basic_colors'] = basic_colors
            
            # Получаем уникальные основные цвета
            cursor.execute(f"""
                SELECT DISTINCT color
                FROM {table_name}
                WHERE color IS NOT NULL AND color != ''
                ORDER BY color
            """)
            main_colors = []
            for row in cursor.fetchall():
                color_str = row['color']
                if color_str:
                    colors = [c.strip() for c in color_str.split(',')]
                    main_colors.extend(colors)
            
            # Очищаем странные значения
            cleaned_colors = []
            exclude_patterns = [
                'более', 'менее', 'чем у', 'вариа', 'светл', 'тускл',
                'отлив', 'блеск', 'блестящ', 'матов', 'голова', 'переднеспинка',
                'верх', 'низ', 'часто', 'выражен', 'сильн', 'слаб'
            ]
            
            for color in main_colors:
                if color and len(color) > 2:
                    color_lower = color.lower()
                    if not any(pattern in color_lower for pattern in exclude_patterns):
                        if len(color) < 60:
                            cleaned_colors.append(color)
            
            options['colors'] = sorted(list(set(cleaned_colors)))
            
            # Базовые типы поверхности/блеска для жуков
            basic_surface_types = [
                'глянцевый', 'матовый', 'блестящий', 'металлический',
                'полуматовый', 'тусклый', 'яркий'
            ]
            options['basic_surface_types'] = basic_surface_types
            
            # Получаем все типы поверхности из описания
            cursor.execute(f"""
                SELECT description
                FROM {table_name}
                WHERE description IS NOT NULL AND (description ILIKE '%тип поверхности%' OR description ILIKE '%блеск%')
            """)
            surface_types_set = set()
            for row in cursor.fetchall():
                desc = row['description']
                # Ищем паттерн "Тип поверхности / Блеск: ..." или "Тип поверхности: ..."
                matches = re.findall(r'Тип поверхности[^:]*:\s*([^;]+)', desc, re.IGNORECASE)
                if not matches:
                    # Пробуем найти просто "блеск" или "блестящ"
                    matches = re.findall(r'[Бб]леск[^:]*:\s*([^;]+)', desc, re.IGNORECASE)
                for match in matches:
                    surface = match.strip()
                    if surface and len(surface) < 100:
                        surface_types_set.add(surface)
            
            # Очищаем значения
            cleaned_surface_types = []
            for surface in surface_types_set:
                if surface and len(surface) > 2:
                    cleaned_surface_types.append(surface)
            options['all_surface_types'] = sorted(list(set(cleaned_surface_types)))
            
            # Базовые типы надкрылий
            basic_elytra = [
                'гладкие', 'зернистые', 'морщинистые', 'точечные',
                'бороздчатые', 'ребристые', 'ямчатые'
            ]
            options['basic_elytra'] = basic_elytra
            
            # Получаем все типы надкрылий из описания
            cursor.execute(f"""
                SELECT description
                FROM {table_name}
                WHERE description IS NOT NULL AND description ILIKE '%надкрыль%'
            """)
            elytra_set = set()
            for row in cursor.fetchall():
                desc = row['description']
                # Ищем паттерн "Надкрылья: ..."
                matches = re.findall(r'Надкрыль[^:]*:\s*([^;]+)', desc, re.IGNORECASE)
                for match in matches:
                    elytra = match.strip()
                    if elytra and len(elytra) < 100:
                        elytra_set.add(elytra)
            
            cleaned_elytra = []
            for elytra in elytra_set:
                if elytra and len(elytra) > 2:
                    cleaned_elytra.append(elytra)
            options['all_elytra'] = sorted(list(set(cleaned_elytra)))
            
            # Базовые места нахождения для жуков
            basic_habitats = [
                'лес', 'луг', 'сад', 'поле', 'болото', 'берег',
                'опушка', 'поляна', 'парк', 'огород'
            ]
            options['basic_habitats'] = basic_habitats
            
            # Получаем все места нахождения
            cursor.execute(f"""
                SELECT DISTINCT habitat
                FROM {table_name}
                WHERE habitat IS NOT NULL AND habitat != ''
                ORDER BY habitat
            """)
            all_habitats = [row['habitat'] for row in cursor.fetchall()]
            options['habitats'] = all_habitats
            options['all_habitats'] = all_habitats
            
            # Базовые периоды активности
            basic_seasons = [
                'весна', 'лето', 'осень', 'зима',
                'май', 'июнь', 'июль', 'август'
            ]
            options['basic_seasons'] = basic_seasons
            
            # Получаем все периоды
            cursor.execute(f"""
                SELECT DISTINCT season
                FROM {table_name}
                WHERE season IS NOT NULL AND season != ''
                ORDER BY season
            """)
            all_seasons = [row['season'] for row in cursor.fetchall()]
            options['seasons'] = all_seasons
            options['all_seasons'] = all_seasons
        
        elif insect_type == 'butterfly':
            # Базовые цвета для бабочек
            basic_colors = [
                'белый', 'жёлтый', 'коричневый', 'красный', 'синий',
                'чёрный', 'оранжевый', 'розовый', 'фиолетовый', 'серый'
            ]
            options['basic_colors'] = basic_colors
            
            # Получаем уникальные основные цвета
            cursor.execute(f"""
                SELECT DISTINCT color
                FROM {table_name}
                WHERE color IS NOT NULL AND color != ''
                ORDER BY color
            """)
            main_colors = []
            for row in cursor.fetchall():
                color_str = row['color']
                if color_str:
                    colors = [c.strip() for c in color_str.split(',')]
                    main_colors.extend(colors)
            
            # Очищаем странные значения
            cleaned_colors = []
            exclude_patterns = [
                'основной цвет', 'крыльев', 'передние', 'задние',
                'мраморн', 'ажурн', 'волнист', 'линии', 'рисунок',
                'оттенок', 'отлив', 'или', 'желтовато', 'красновато'
            ]
            
            for color in main_colors:
                if color and len(color) > 2:
                    color_lower = color.lower()
                    if not any(pattern in color_lower for pattern in exclude_patterns):
                        if len(color) < 50:
                            cleaned_colors.append(color)
                    else:
                        # Если содержит "или", берем первую часть
                        if ' или ' in color_lower or ' / ' in color_lower:
                            first_part = color.split(' или ')[0].split(' / ')[0].strip()
                            if first_part and len(first_part) < 30:
                                cleaned_colors.append(first_part)
            
            options['colors'] = sorted(list(set(cleaned_colors)))
            
            # Базовые особенности рисунка крыльев
            basic_wing_patterns = [
                'пятна', 'полосы', 'точки', 'кружки', 'глазки',
                'кайма', 'перевязи', 'мраморный', 'сетчатый'
            ]
            options['basic_wing_patterns'] = basic_wing_patterns
            
            # Получаем все особенности рисунка крыльев из описания
            cursor.execute(f"""
                SELECT description
                FROM {table_name}
                WHERE description IS NOT NULL AND description ILIKE '%рисунок%'
            """)
            wing_patterns_set = set()
            for row in cursor.fetchall():
                desc = row['description']
                # Ищем паттерн "Рисунок: ..." (как хранится в БД)
                matches = re.findall(r'Рисунок[^:]*:\s*([^;]+)', desc, re.IGNORECASE)
                for match in matches:
                    pattern = match.strip()
                    if pattern and len(pattern) < 150:
                        wing_patterns_set.add(pattern)
            
            # Очищаем значения
            cleaned_wing_patterns = []
            exclude_patterns = ['крыльев', 'верх', 'низ', 'передние', 'задние']
            for pattern in wing_patterns_set:
                if pattern and len(pattern) > 2:
                    pattern_lower = pattern.lower()
                    if not any(exc in pattern_lower for exc in exclude_patterns):
                        cleaned_wing_patterns.append(pattern)
            options['all_wing_patterns'] = sorted(list(set(cleaned_wing_patterns)))
            
            # Базовые места нахождения для бабочек
            basic_habitats = [
                'лес', 'луг', 'сад', 'поле', 'болото', 'берег',
                'опушка', 'поляна', 'парк', 'лужайка', 'лесополоса'
            ]
            options['basic_habitats'] = basic_habitats
            
            # Получаем все места нахождения
            cursor.execute(f"""
                SELECT DISTINCT habitat
                FROM {table_name}
                WHERE habitat IS NOT NULL AND habitat != ''
                ORDER BY habitat
            """)
            all_habitats = [row['habitat'] for row in cursor.fetchall()]
            options['habitats'] = all_habitats
            options['all_habitats'] = all_habitats
            
            # Базовые периоды лёта
            basic_seasons = [
                'весна', 'лето', 'осень',
                'май', 'июнь', 'июль', 'август', 'сентябрь'
            ]
            options['basic_seasons'] = basic_seasons
            
            # Получаем все периоды лёта
            cursor.execute(f"""
                SELECT DISTINCT season
                FROM {table_name}
                WHERE season IS NOT NULL AND season != ''
                ORDER BY season
            """)
            all_seasons = [row['season'] for row in cursor.fetchall()]
            options['seasons'] = all_seasons
            options['all_seasons'] = all_seasons
        
        cursor.close()
        conn.close()
        return options

