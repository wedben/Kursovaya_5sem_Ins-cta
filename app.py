from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import Database
from auth import User
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-12345')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))

db = Database()

# Путь к папке с изображениями
IMAGE_BASE_DIR = Path(__file__).parent / 'data'

def find_insect_image(insect_name: str, insect_type: str, description: str = '') -> str:
    """
    Находит изображение насекомого по его названию и типу
    
    Args:
        insect_name: Русское название насекомого
        insect_type: 'dragonfly', 'beetle' или 'butterfly'
        description: Описание (для определения пола)
    
    Returns:
        URL изображения или пустая строка
    """
    if not insect_name:
        return ''
    
    # Определяем папку с изображениями
    folder_map = {
        'dragonfly': 'Стрекозы',
        'beetle': 'жужелицы',  # Если есть папка для жуков
        'butterfly': 'бабочки'
    }
    
    folder_name = folder_map.get(insect_type)
    if not folder_name:
        return ''
    
    image_dir = IMAGE_BASE_DIR / folder_name
    if not image_dir.exists():
        return ''
    
    # Нормализуем название для поиска
    name_lower = insect_name.lower().strip()
    
    # Извлекаем пол из описания, если есть
    gender = ''
    if description:
        if 'самец' in description.lower() or '(самец)' in description.lower():
            gender = 'самец'
        elif 'самка' in description.lower() or '(самка)' in description.lower():
            gender = 'самка'
    
    # Получаем список всех изображений
    image_files = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.JPG')) + list(image_dir.glob('*.webp'))
    
    # Создаем список кандидатов с приоритетами
    candidates = []
    
    for img_file in image_files:
        filename_lower = img_file.stem.lower()
        
        # Убираем расширение и нормализуем
        filename_clean = filename_lower.replace('(', '').replace(')', '').replace('-', ' ').replace('_', ' ')
        name_clean = name_lower.replace('-', ' ').replace('_', ' ')
        
        # Разбиваем на слова
        filename_words = set(filename_clean.split())
        name_words = set(name_clean.split())
        
        # Проверяем совпадение
        common_words = filename_words.intersection(name_words)
        
        if common_words:
            # Приоритет: точное совпадение > частичное совпадение
            priority = len(common_words)
            
            # Учитываем пол, если указан
            if gender:
                if gender in filename_lower:
                    priority += 10  # Большой бонус за совпадение пола
                elif '(самец)' in filename_lower or '(самка)' in filename_lower:
                    priority -= 5  # Штраф, если пол не совпадает
            
            candidates.append((priority, img_file))
    
    # Сортируем по приоритету (больше = лучше)
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    if candidates:
        best_match = candidates[0][1]
        # Возвращаем относительный путь для URL
        relative_path = best_match.relative_to(IMAGE_BASE_DIR)
        return f'/data/{relative_path.as_posix()}'
    
    return ''

@app.route('/')
def index():
    """Главная страница с формой поиска"""
    user_data = None
    if current_user.is_authenticated:
        user_data = {
            'id': current_user.id,
            'username': current_user.username,
            'name': current_user.name,
            'role': current_user.role
        }
    return render_template('index.html', user=user_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Логин и пароль обязательны'}), 400
        
        user = User.verify_password(username, password)
        if user:
            login_user(user)
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role
                }
            })
        else:
            return jsonify({'error': 'Неверный логин или пароль'}), 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        name = data.get('name')
        
        if not all([username, password, email, name]):
            return jsonify({'error': 'Все поля обязательны'}), 400
        
        # Проверяем, существует ли пользователь
        if User.get_by_username(username):
            return jsonify({'error': 'Пользователь с таким логином уже существует'}), 400
        
        user = User.create_user(username, email, password, name, 'пользователь')
        if user:
            login_user(user)
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'name': user.name,
                    'role': user.role
                }
            })
        else:
            return jsonify({'error': 'Ошибка при создании пользователя'}), 500
    
    return render_template('register.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    return jsonify({'success': True})

@app.route('/admin')
@login_required
def admin_panel():
    """Админ-панель"""
    if not current_user.is_admin():
        return jsonify({'error': 'Доступ запрещен'}), 403
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'name': current_user.name,
        'role': current_user.role
    }
    return render_template('admin.html', user=user_data)

@app.route('/my-requests')
@login_required
def my_requests():
    """Страница с запросами пользователя"""
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'name': current_user.name,
        'role': current_user.role
    }
    return render_template('my_requests.html', user=user_data)

@app.route('/api/search', methods=['POST'])
def search_insects():
    """API endpoint для поиска насекомых по параметрам"""
    try:
        data = request.json
        
        insect_type = data.get('type')  # 'dragonfly', 'beetle', 'butterfly'
        params = data.get('params', {})
        
        if not insect_type:
            return jsonify({'error': 'Тип насекомого не указан'}), 400
        
        # Валидация типа
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        # Поиск в базе данных
        results = db.search_insects(insect_type, params)
        
        # Добавляем URL изображений к результатам
        for result in results:
            if not result.get('image_url'):
                image_url = find_insect_image(
                    result.get('name_ru', ''),
                    insect_type,
                    result.get('description', '')
                )
                if image_url:
                    result['image_url'] = image_url
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/all/<insect_type>', methods=['GET'])
def get_all_insects(insect_type):
    """Получить все насекомые определенного типа"""
    try:
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        results = db.get_all_insects(insect_type)
        
        # Добавляем URL изображений и тип насекомого к результатам
        for result in results:
            if not result.get('image_url'):
                image_url = find_insect_image(
                    result.get('name_ru', ''),
                    insect_type,
                    result.get('description', '')
                )
                if image_url:
                    result['image_url'] = image_url
            # Добавляем тип насекомого для фильтрации на фронтенде
            result['insect_type'] = insect_type
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter-options/<insect_type>', methods=['GET'])
def get_filter_options(insect_type):
    """Получить уникальные значения для фильтров"""
    try:
        valid_types = ['dragonfly', 'beetle', 'butterfly']
        if insect_type not in valid_types:
            return jsonify({'error': 'Неверный тип насекомого'}), 400
        
        options = db.get_filter_options(insect_type)
        return jsonify({
            'success': True,
            'options': options
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expert-request', methods=['POST'])
@login_required
def create_expert_request():
    """Создать запрос к эксперту"""
    try:
        data = request.json
        description = data.get('description')
        location = data.get('location', '')
        observation_date = data.get('observation_date', '')
        additional_data = data.get('additional_data', '')
        
        if not description:
            return jsonify({'error': 'Описание насекомого обязательно'}), 400
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO "ЗапросЭксперту" 
                (id_пользователя, описание_насекомого, место_наблюдения, дата_наблюдения, дополнительные_данные, статус)
                VALUES (%s, %s, %s, %s, %s, 'ожидает')
                RETURNING id_запроса
            """, (current_user.id, description, location, observation_date or None, additional_data))
            
            request_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                'success': True,
                'request_id': request_id,
                'message': 'Запрос отправлен эксперту'
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expert-requests', methods=['GET'])
@login_required
def get_expert_requests():
    """Получить запросы к эксперту"""
    try:
        from psycopg2.extras import RealDictCursor
        conn = db.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            if current_user.is_admin():
                # Админ видит все запросы
                cursor.execute("""
                    SELECT 
                        z.id_запроса,
                        z.описание_насекомого,
                        z.место_наблюдения,
                        z.дата_наблюдения,
                        z.дополнительные_данные,
                        z.статус,
                        z.дата_создания,
                        z.дата_ответа,
                        z.ответ_эксперта,
                        z.изображение_ответа,
                        z.id_вида_насекомого,
                        u.имя as имя_пользователя,
                        u.email as email_пользователя
                    FROM "ЗапросЭксперту" z
                    LEFT JOIN "Пользователь" u ON z.id_пользователя = u.id_пользователя
                    ORDER BY z.дата_создания DESC
                """)
            else:
                # Обычный пользователь видит только свои запросы
                cursor.execute("""
                    SELECT 
                        z.id_запроса,
                        z.описание_насекомого,
                        z.место_наблюдения,
                        z.дата_наблюдения,
                        z.дополнительные_данные,
                        z.статус,
                        z.дата_создания,
                        z.дата_ответа,
                        z.ответ_эксперта,
                        z.изображение_ответа,
                        z.id_вида_насекомого,
                        u.имя as имя_пользователя,
                        u.email as email_пользователя
                    FROM "ЗапросЭксперту" z
                    LEFT JOIN "Пользователь" u ON z.id_пользователя = u.id_пользователя
                    WHERE z.id_пользователя = %s
                    ORDER BY z.дата_создания DESC
                """, (current_user.id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            # Преобразуем даты в строки
            for result in results:
                if result.get('дата_создания'):
                    result['дата_создания'] = result['дата_создания'].isoformat()
                if result.get('дата_ответа'):
                    result['дата_ответа'] = result['дата_ответа'].isoformat()
                if result.get('дата_наблюдения'):
                    result['дата_наблюдения'] = str(result['дата_наблюдения'])
            
            return jsonify({
                'success': True,
                'requests': results
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/insects-for-selection', methods=['GET'])
@login_required
def get_insects_for_selection():
    """Получить список всех насекомых для выбора при ответе на запрос"""
    try:
        if not current_user.is_admin():
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        all_insects = []
        
        # Получаем стрекоз
        dragonflies = db.get_all_insects('dragonfly')
        for insect in dragonflies:
            all_insects.append({
                'id': insect.get('id'),
                'name_ru': insect.get('name_ru', ''),
                'name_lat': insect.get('name_lat', ''),
                'type': 'dragonfly',
                'type_label': 'Стрекоза',
                'size': f"{insect.get('size_min', '')}-{insect.get('size_max', '')} мм" if insect.get('size_min') or insect.get('size_max') else '',
                'color': insect.get('color', ''),
                'image_url': find_insect_image(
                    insect.get('name_ru', ''),
                    'dragonfly',
                    insect.get('description', '')
                ) or insect.get('image_url', '')
            })
        
        # Получаем жуков
        beetles = db.get_all_insects('beetle')
        for insect in beetles:
            all_insects.append({
                'id': insect.get('id'),
                'name_ru': insect.get('name_ru', ''),
                'name_lat': insect.get('name_lat', ''),
                'type': 'beetle',
                'type_label': 'Жук',
                'size': f"{insect.get('size_min', '')}-{insect.get('size_max', '')} мм" if insect.get('size_min') or insect.get('size_max') else '',
                'color': insect.get('color', ''),
                'image_url': find_insect_image(
                    insect.get('name_ru', ''),
                    'beetle',
                    insect.get('description', '')
                ) or insect.get('image_url', '')
            })
        
        # Получаем бабочек
        butterflies = db.get_all_insects('butterfly')
        for insect in butterflies:
            all_insects.append({
                'id': insect.get('id'),
                'name_ru': insect.get('name_ru', ''),
                'name_lat': insect.get('name_lat', ''),
                'type': 'butterfly',
                'type_label': 'Бабочка',
                'size': f"{insect.get('size_min', '')}-{insect.get('size_max', '')} мм" if insect.get('size_min') or insect.get('size_max') else '',
                'color': insect.get('color', ''),
                'image_url': find_insect_image(
                    insect.get('name_ru', ''),
                    'butterfly',
                    insect.get('description', '')
                ) or insect.get('image_url', '')
            })
        
        return jsonify({
            'success': True,
            'insects': all_insects
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def find_insect_id_in_vid_nasekomogo(insect_id: int, insect_type: str) -> Optional[int]:
    """
    Находит соответствующий ID в таблице ВидНасекомого по ID из таблиц dragonflies/beetles/butterflies
    
    Args:
        insect_id: ID из таблицы dragonflies/beetles/butterflies
        insect_type: 'dragonfly', 'beetle' или 'butterfly'
    
    Returns:
        ID из таблицы ВидНасекомого или None
    """
    if not insect_id:
        return None
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Определяем таблицу
        table_map = {
            'dragonfly': 'dragonflies',
            'beetle': 'beetles',
            'butterfly': 'butterflies'
        }
        table_name = table_map.get(insect_type)
        if not table_name:
            return None
        
        # Получаем название насекомого
        cursor.execute(f"""
            SELECT name_ru, name_lat FROM {table_name} WHERE id = %s
        """, (insect_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        name_ru, name_lat = row
        
        # Определяем тип для таблицы ВидНасекомого
        type_map = {
            'dragonfly': 'стрекоза',
            'beetle': 'жук',
            'butterfly': 'бабочка'
        }
        vid_type = type_map.get(insect_type)
        
        # Ищем в таблице ВидНасекомого
        cursor.execute("""
            SELECT id_вида FROM "ВидНасекомого"
            WHERE название_русское = %s AND тип_насекомого = %s
            LIMIT 1
        """, (name_ru, vid_type))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        
        return None
    except Exception as e:
        print(f"Ошибка при поиске ID в ВидНасекомого: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

@app.route('/api/expert-request/<int:request_id>/answer', methods=['POST'])
@login_required
def answer_expert_request(request_id):
    """Ответить на запрос эксперта"""
    try:
        if not current_user.is_admin():
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        data = request.json
        answer = data.get('answer', '')
        image_url = data.get('image_url', '')
        insect_id = data.get('insect_id') or data.get('insectId')
        insect_type = data.get('insect_type')  # Тип насекомого для поиска в ВидНасекомого
        
        if not answer:
            return jsonify({'error': 'Ответ обязателен'}), 400
        
        # Если указан ID насекомого, пытаемся найти соответствующий ID в ВидНасекомого
        vid_insect_id = None
        if insect_id and insect_type:
            vid_insect_id = find_insect_id_in_vid_nasekomogo(insect_id, insect_type)
            # Если не нашли, просто не устанавливаем это поле (оно опциональное)
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE "ЗапросЭксперту"
                SET ответ_эксперта = %s,
                    изображение_ответа = %s,
                    id_вида_насекомого = %s,
                    id_эксперта = %s,
                    статус = 'отвечено',
                    дата_ответа = CURRENT_TIMESTAMP
                WHERE id_запроса = %s
            """, (answer, image_url or None, vid_insect_id, current_user.id, request_id))
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Запрос не найден'}), 404
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ответ отправлен'
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        import traceback
        print(f"Ошибка при отправке ответа: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/data/<path:filename>')
def serve_image(filename):
    """Отдача изображений из папки data"""
    try:
        # Безопасность: проверяем, что путь не выходит за пределы data
        file_path = IMAGE_BASE_DIR / filename
        if not str(file_path.resolve()).startswith(str(IMAGE_BASE_DIR.resolve())):
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        if not file_path.exists():
            return jsonify({'error': 'Файл не найден'}), 404
        
        return send_from_directory(IMAGE_BASE_DIR, filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

