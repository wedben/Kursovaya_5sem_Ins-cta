from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO
from database import Database
from auth import User
from validators import (
    v_trim, v_first_name, v_last_name, v_email, v_login,
    v_password, v_gender, v_age_status, v_rules_checked,
)
from recaptcha import recaptcha_enabled, recaptcha_site_key, recaptcha_verify
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

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

socketio = SocketIO(app, cors_allowed_origins="*", manage_session=True, async_mode="threading")
import socket_handlers
socket_handlers.init_socketio(socketio)

def _login_block_guard():
    # Если пользователь заблокирован, не даём авторизоваться в UI/API.
    if current_user.is_authenticated and getattr(current_user, 'blocked_until', None):
        try:
            logout_user()
        except Exception:
            pass

def _require_roles(*roles: str):
    def decorator(fn):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Требуется вход'}), 401
            if getattr(current_user, 'blocked_until', None):
                return jsonify({'error': 'Доступ временно ограничен'}), 403
            if getattr(current_user, 'blocked_permanent', False):
                return jsonify({'error': 'Доступ заблокирован'}), 403
            if current_user.role not in roles:
                return jsonify({'error': 'Доступ запрещен'}), 403
            return fn(*args, **kwargs)
        wrapped.__name__ = fn.__name__
        return wrapped
    return decorator

def _contains_profanity(text: str) -> bool:
    # Простой фильтр; модератор решает окончательно.
    if not text:
        return False
    bad = [
        r'\bсука\b', r'\bбля(ть|дь)?\b', r'\bхуй\b', r'\bпизд',
        r'\bеба', r'\bнахуй\b', r'\bидиот\b',
    ]
    t = text.lower()
    return any(re.search(p, t) for p in bad)

def theme_get() -> str:
    theme = session.get('theme', 'light')
    return 'dark' if theme == 'dark' else 'light'

def auth_context():
    return {
        'recaptcha_site_key': recaptcha_site_key(),
        'recaptcha_enabled': recaptcha_enabled(),
    }

def _verify_recaptcha(errors: dict, token: str):
    if not recaptcha_enabled():
        return
    res = recaptcha_verify(token, request.remote_addr)
    if not res['ok']:
        errors['recaptcha'] = res.get('error', 'reCAPTCHA не пройдена.')

# Путь к папке с изображениями
IMAGE_BASE_DIR = Path(__file__).parent / 'data'

OPEN_REQUEST_STATUSES = frozenset({'открыт', 'ожидает', 'в_работе', 'отвечено'})
CATALOG_TABLES = {
    'dragonfly': 'dragonflies',
    'beetle': 'beetles',
    'butterfly': 'butterflies',
    'mushroom': 'mushrooms',
    'herb': 'herbs',
}
CATALOG_TYPE_LABELS = {
    'dragonfly': 'Стрекоза',
    'beetle': 'Жук',
    'butterfly': 'Бабочка',
    'mushroom': 'Гриб',
    'herb': 'Трава',
}
CATALOG_TYPE_KEYS = tuple(CATALOG_TABLES.keys())


def parse_insect_gender(description: str) -> Optional[str]:
    """Пол из описания карточки (Пол: самец / самка)."""
    if not description:
        return None
    m = re.search(r'Пол:\s*(самец|самка)', description, re.IGNORECASE)
    return m.group(1).lower() if m else None


def catalog_gender_label(gender: Optional[str]) -> str:
    if gender == 'самец':
        return 'Самец'
    if gender == 'самка':
        return 'Самка'
    return ''


def catalog_insect_display_name(name_ru: str, gender: Optional[str]) -> str:
    label = catalog_gender_label(gender)
    if label:
        return f'{name_ru} — {label}'
    return name_ru


def catalog_card_url(insect_type: str, insect_id: int) -> str:
    """Прямая ссылка на карточку в каталоге (без url_for — нужен в WebSocket и вне HTTP-запроса)."""
    if insect_type not in CATALOG_TABLES or not insect_id:
        return ''
    return f'/catalog/{insect_type}/{int(insect_id)}'


def _index_user_data():
    if not current_user.is_authenticated:
        return None
    return {
        'id': current_user.id,
        'username': current_user.username,
        'name': current_user.name,
        'role': current_user.role,
    }


def build_catalog_insect_item(insect: dict, insect_type: str) -> dict:
    desc = insect.get('description', '') or ''
    gender = parse_insect_gender(desc)
    name_ru = insect.get('name_ru', '')
    insect_id = insect.get('id')
    item = {
        'id': insect_id,
        'name_ru': name_ru,
        'name_lat': insect.get('name_lat', ''),
        'type': insect_type,
        'type_label': CATALOG_TYPE_LABELS.get(insect_type, insect_type),
        'gender': gender,
        'gender_label': catalog_gender_label(gender),
        'display_name': catalog_insect_display_name(name_ru, gender),
        'size': f"{insect.get('size_min', '')}-{insect.get('size_max', '')} мм".strip('- ') or '',
        'color': insect.get('color', ''),
        'description': desc,
        'image_url': find_insect_image(name_ru, insect_type, desc) or insect.get('image_url', ''),
        'catalog_url': catalog_card_url(insect_type, insect_id) if insect_id else '',
    }
    for field in (
        'size_min', 'size_max', 'habitat', 'season', 'body_length_min', 'body_length_max',
        'wingspan_min', 'wingspan_max', 'eye_color', 'environment', 'surface_type', 'elytra',
        'wing_pattern', 'time_of_day',
    ):
        if field in insect and insect[field] is not None:
            item[field] = insect[field]
    return item


def is_request_open(status: Optional[str]) -> bool:
    return status in OPEN_REQUEST_STATUSES


def fetch_catalog_card(card_id: int, card_type: str) -> Optional[dict]:
    table = CATALOG_TABLES.get(card_type)
    if not table or not card_id:
        return None
    from psycopg2.extras import RealDictCursor
    conn = db.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute(f'SELECT * FROM {table} WHERE id = %s', (card_id,))
        row = cur.fetchone()
        if not row:
            return None
        return build_catalog_insect_item(dict(row), card_type)
    finally:
        cur.close()
        conn.close()


def is_duplicate_request_snapshot(text: str, description: str = '') -> bool:
    """Сообщение-дубликат блока «Данные запроса» (старые записи в БД)."""
    if not text:
        return False
    t = text.strip()
    if t.startswith('Запрос пользователя'):
        return True
    if description and t == description.strip():
        return True
    return False


def filter_chat_messages(messages: list, request: dict) -> list:
    desc = (request.get('описание_насекомого') or '') if request else ''
    return [
        m for m in messages
        if not is_duplicate_request_snapshot(
            m.get('текст', '') if isinstance(m, dict) else '', desc,
        )
    ]


def enrich_expert_request(req: dict) -> dict:
    if req.get('дата_наблюдения') is not None and hasattr(req['дата_наблюдения'], 'isoformat'):
        req['дата_наблюдения'] = str(req['дата_наблюдения'])
    elif req.get('дата_наблюдения') is not None:
        req['дата_наблюдения'] = str(req['дата_наблюдения'])
    card_id = req.get('id_карточки')
    card_type = req.get('тип_карточки')
    if card_id and card_type:
        req['attached_card'] = fetch_catalog_card(int(card_id), card_type)
    else:
        req['attached_card'] = None
    return req


def user_can_view_request(req: dict, user) -> bool:
    status = req.get('статус')
    return (
        user.is_admin()
        or user.is_moderator()
        or req.get('id_пользователя') == user.id
        or req.get('id_эксперта') == user.id
        or (
            user.is_expert()
            and status not in ('закрыт', 'удален_модератором', 'на_модерации')
        )
    )


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

    folder_map = {
        'dragonfly': 'Стрекозы',
        'beetle': 'жужелицы',
        'butterfly': 'бабочки',
        'mushroom': 'Грибы',
        'herb': 'Травы',
    }

    folder_name = folder_map.get(insect_type)
    if not folder_name:
        return ''

    image_dir = IMAGE_BASE_DIR / folder_name
    if not image_dir.exists():
        return ''

    name_slug = re.sub(r'\s+', '-', insect_name.lower().strip())
    name_slug = re.sub(r'_', '-', name_slug)

    gender = ''
    if description:
        desc_lower = description.lower()
        if 'самец' in desc_lower and 'самка' not in desc_lower:
            gender = 'самец'
        elif 'самка' in desc_lower and 'самец' not in desc_lower:
            gender = 'самка'

    image_files = (
        list(image_dir.glob('*.jpg')) +
        list(image_dir.glob('*.JPG')) +
        list(image_dir.glob('*.webp')) +
        list(image_dir.glob('*.WEBP'))
    )

    def stem_base(stem: str) -> str:
        base = re.sub(r'\(самец\)|\(самка\d*\)', '', stem.lower(), flags=re.IGNORECASE)
        return base.strip('-')

    candidates = []

    for img_file in image_files:
        stem = img_file.stem.lower()
        base = stem_base(stem)

        if base == name_slug:
            priority = 100
        elif base.startswith(name_slug + '-') or name_slug.startswith(base):
            priority = 80
        else:
            name_parts = [p for p in name_slug.split('-') if len(p) > 2]
            if not name_parts or not all(part in base for part in name_parts):
                continue
            priority = len(name_parts) * 10

        if gender:
            if f'({gender})' in stem or f'({gender}' in stem:
                priority += 25
            elif 'самец' in stem or 'самка' in stem:
                priority -= 40

        candidates.append((priority, img_file))

    candidates.sort(key=lambda x: x[0], reverse=True)

    if candidates and candidates[0][0] >= 20:
        relative_path = candidates[0][1].relative_to(IMAGE_BASE_DIR)
        return f'/data/{relative_path.as_posix()}'

    return ''

@app.route('/')
def index():
    """Главная страница с формой поиска"""
    catalog = request.args.get('catalog')
    card_id = request.args.get('card_id') or request.args.get('id')
    if catalog in CATALOG_TABLES and card_id:
        try:
            cid = int(card_id)
            if fetch_catalog_card(cid, catalog):
                return redirect(url_for('catalog_card_view', insect_type=catalog, insect_id=cid))
        except (TypeError, ValueError):
            pass
    return render_template('index.html', user=_index_user_data())


@app.route('/catalog/<insect_type>/<int:insect_id>')
def catalog_card_view(insect_type, insect_id):
    """Страница каталога с открытой карточкой насекомого."""
    if insect_type not in CATALOG_TABLES:
        return redirect(url_for('index'))
    if not fetch_catalog_card(insect_id, insect_type):
        return redirect(url_for('index'))
    return render_template(
        'index.html',
        user=_index_user_data(),
        catalog_deep_link={'type': insect_type, 'id': insect_id},
    )

@app.route('/theme_toggle')
def theme_toggle():
    """Переключение светлой/тёмной темы (как theme_toggle.php)."""
    session['theme'] = 'light' if theme_get() == 'dark' else 'dark'
    return redirect(request.referrer or url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа по логину и паролю + reCAPTCHA."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    login_value = ''

    if request.method == 'POST':
        _login_block_guard()
        login_value = v_trim(request.form.get('login', ''))
        password = request.form.get('password', '')
        recaptcha_token = request.form.get('g-recaptcha-response', '')

        if not login_value:
            errors['login'] = 'Логин обязателен.'
        if not password:
            errors['password'] = 'Пароль обязателен.'

        _verify_recaptcha(errors, recaptcha_token)

        if not errors:
            user = User.verify_password(login_value, password)
            if not user:
                errors['common'] = 'Неверный логин или пароль.'
            else:
                if getattr(user, 'blocked_permanent', False):
                    errors['common'] = 'Доступ заблокирован.'
                    ctx = auth_context()
                    ctx.update({'errors': errors, 'login': login_value})
                    return render_template('login.html', **ctx), 403
                if getattr(user, 'blocked_until', None):
                    errors['common'] = 'Доступ временно ограничен.'
                    ctx = auth_context()
                    ctx.update({'errors': errors, 'login': login_value})
                    return render_template('login.html', **ctx), 403
                login_user(user)
                session['theme'] = user.theme
                return redirect(url_for('index'))

    ctx = auth_context()
    ctx.update({'errors': errors, 'login': login_value})
    return render_template('login.html', **ctx)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации с полной валидацией (как register.php)."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    errors = {}
    old = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'login': '',
        'age_status': '18plus',
        'gender': 'male',
        'rules': False,
    }
    old_passwords = {'password': '', 'password_confirm': ''}

    if request.method == 'POST':
        first = request.form.get('first_name', '')
        last = request.form.get('last_name', '')
        email = request.form.get('email', '')
        login_val = request.form.get('login', '')
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        gender = request.form.get('gender', '')
        age = request.form.get('age_status', '')
        rules = request.form.get('rules')
        recaptcha_token = request.form.get('g-recaptcha-response', '')

        old_passwords = {
            'password': password,
            'password_confirm': password_confirm,
        }
        old = {
            'first_name': v_trim(first),
            'last_name': v_trim(last),
            'email': v_trim(email),
            'login': v_trim(login_val),
            'age_status': age,
            'gender': gender,
            'rules': bool(rules),
        }

        for field, msg in [
            ('first_name', v_first_name(first)),
            ('last_name', v_last_name(last)),
            ('email', v_email(email)),
            ('login', v_login(login_val)),
            ('password', v_password(password)),
        ]:
            if msg:
                errors[field] = msg

        if password != password_confirm:
            errors['password_confirm'] = 'Подтверждение пароля не совпадает.'
        if msg := v_gender(gender):
            errors['gender'] = msg
        if msg := v_age_status(age):
            errors['age_status'] = msg
        if msg := v_rules_checked(rules):
            errors['rules'] = msg

        _verify_recaptcha(errors, recaptcha_token)

        if not errors:
            unique = User.check_unique(old['email'], old['login'])
            if unique['email_exists']:
                errors['email'] = 'Пользователь с такой почтой уже существует.'
            if unique['login_exists']:
                errors['login'] = 'Пользователь с таким логином уже существует.'

        if not errors:
            theme = theme_get()
            user = User.create_user(
                login=old['login'],
                email=old['email'],
                password=password,
                first_name=old['first_name'],
                last_name=old['last_name'],
                gender=old['gender'],
                age_status=old['age_status'],
                theme=theme,
            )
            if not user:
                errors['common'] = 'Не удалось зарегистрироваться. Попробуйте ещё раз.'
            else:
                login_user(user)
                session['theme'] = theme
                return redirect(url_for('index'))

    ctx = auth_context()
    ctx.update({'errors': errors, 'old': old, 'old_passwords': old_passwords})
    return render_template('register.html', **ctx)

@app.route('/api/check_unique', methods=['POST'])
def check_unique():
    """AJAX: проверка уникальности email/login."""
    email = v_trim(request.form.get('email', ''))
    login_val = v_trim(request.form.get('login', ''))

    if not email and not login_val:
        return jsonify({'ok': True, 'email_exists': False, 'login_exists': False})

    try:
        unique = User.check_unique(email, login_val)
    except Exception:
        return jsonify({'ok': False, 'error': 'Сервис временно недоступен'}), 503

    resp = make_response(jsonify({
        'ok': True,
        'email_exists': unique['email_exists'],
        'login_exists': unique['login_exists'],
    }))
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return resp

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Выход из системы."""
    logout_user()
    session.clear()
    if request.method == 'POST' or request.is_json:
        return jsonify({'success': True})
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_panel():
    """Панель эксперта / админа (список запросов)"""
    if not current_user.can_manage_requests():
        return jsonify({'error': 'Доступ запрещен'}), 403
    if current_user.is_moderator() and not current_user.is_admin() and not current_user.is_expert():
        return redirect(url_for('moderation_panel'))

    if current_user.is_expert() and not current_user.is_admin():
        page_title = 'Запросы пользователей'
        page_subtitle = 'Отвечайте пользователям в чате по каждому запросу'
    else:
        page_title = 'Админ-панель'
        page_subtitle = 'Управление запросами к эксперту'

    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'name': current_user.name,
        'role': current_user.role
    }
    return render_template(
        'admin.html',
        user=user_data,
        is_expert=current_user.is_expert(),
        page_title=page_title,
        page_subtitle=page_subtitle,
    )

@app.route('/moderation')
@login_required
def moderation_panel():
    """Панель модерации (очередь запросов)"""
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    return render_template('moderation.html')

@app.route('/users')
@login_required
def users_panel():
    """Управление пользователями (для модератора)"""
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    return render_template('users.html')

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

@app.route('/api/whoami', methods=['GET'])
def whoami():
    if not current_user.is_authenticated:
        return jsonify({'authenticated': False}), 200
    return jsonify({
        'authenticated': True,
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'name': current_user.name,
            'role': current_user.role
        }
    })

@app.route('/api/users', methods=['GET'])
@login_required
def list_users():
    """Список пользователей для панели модератора"""
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    from psycopg2.extras import RealDictCursor
    conn = db.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id_пользователя, username, email, имя, роль, warnings_count, blocked_until, дата_регистрации
            FROM "Пользователь"
            ORDER BY id_пользователя DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        for r in rows:
            if r.get('blocked_until'):
                r['blocked_until'] = r['blocked_until'].isoformat()
            if r.get('дата_регистрации'):
                r['дата_регистрации'] = str(r['дата_регистрации'])
        return jsonify({'success': True, 'users': rows})
    finally:
        cur.close()
        conn.close()

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
        valid_types = list(CATALOG_TYPE_KEYS)
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
        valid_types = list(CATALOG_TYPE_KEYS)
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
        valid_types = list(CATALOG_TYPE_KEYS)
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

        if getattr(current_user, 'blocked_until', None):
            return jsonify({'error': 'Доступ временно ограничен'}), 403
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO "ЗапросЭксперту" 
                (id_пользователя, описание_насекомого, место_наблюдения, дата_наблюдения, дополнительные_данные, статус)
                VALUES (%s, %s, %s, %s, %s, 'на_модерации')
                RETURNING id_запроса
            """, (current_user.id, description, location, observation_date or None, additional_data))
            
            request_id = cursor.fetchone()[0]
            conn.commit()
            
            return jsonify({
                'success': True,
                'request_id': request_id,
                'message': 'Запрос отправлен на проверку'
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/request/<int:request_id>')
@login_required
def request_chat(request_id: int):
    """Страница чата по запросу"""
    if current_user.is_expert() and not current_user.is_admin():
        list_url, list_label = '/admin', 'Все запросы'
    elif current_user.is_admin():
        list_url, list_label = '/admin', 'Админ-панель'
    elif current_user.is_moderator():
        list_url, list_label = '/moderation', 'Модерация'
    else:
        list_url, list_label = '/my-requests', 'Все мои запросы'

    return render_template(
        'request_chat.html',
        request_id=request_id,
        user_id=current_user.id,
        is_expert=current_user.is_expert(),
        list_url=list_url,
        list_label=list_label,
    )

@app.route('/api/expert-request/<int:request_id>', methods=['GET'])
@login_required
def get_expert_request_details(request_id: int):
    """Детали запроса + сообщения"""
    from psycopg2.extras import RealDictCursor
    conn = db.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""SELECT * FROM "ЗапросЭксперту" WHERE id_запроса=%s""", (request_id,))
        req = cur.fetchone()
        if not req:
            return jsonify({'error': 'Запрос не найден'}), 404

        if not user_can_view_request(dict(req), current_user):
            return jsonify({'error': 'Доступ запрещен'}), 403

        cur.execute("""
            SELECT id_сообщения, id_отправителя, текст, дата_создания
            FROM "СообщениеЗапроса"
            WHERE id_запроса=%s
            ORDER BY дата_создания ASC
        """, (request_id,))
        msgs = [dict(r) for r in cur.fetchall()]
        for m in msgs:
            if m.get('дата_создания'):
                m['дата_создания'] = m['дата_создания'].isoformat()

        # сериализация дат
        for k in ('дата_создания', 'дата_ответа', 'дата_закрытия'):
            if req.get(k):
                req[k] = req[k].isoformat() if hasattr(req[k], 'isoformat') else str(req[k])
        if req.get('дата_наблюдения'):
            req['дата_наблюдения'] = str(req['дата_наблюдения'])

        req = enrich_expert_request(dict(req))
        msgs = filter_chat_messages(msgs, req)
        return jsonify({'success': True, 'request': req, 'messages': msgs})
    finally:
        cur.close()
        conn.close()

@app.route('/api/expert-request/<int:request_id>/message', methods=['POST'])
@login_required
def post_request_message(request_id: int):
    """Добавить сообщение в чат"""
    data = request.json or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'Текст сообщения обязателен'}), 400
    if getattr(current_user, 'blocked_until', None):
        return jsonify({'error': 'Доступ временно ограничен'}), 403

    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""SELECT id_пользователя, id_эксперта, статус FROM "ЗапросЭксперту" WHERE id_запроса=%s""", (request_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Запрос не найден'}), 404
        owner_id, expert_id, status = row

        allowed = (owner_id == current_user.id) or (expert_id == current_user.id) or current_user.is_moderator()
        if not allowed:
            return jsonify({'error': 'Доступ запрещен'}), 403
        if status in ('закрыт', 'удален_модератором'):
            return jsonify({'error': 'Запрос закрыт'}), 400

        cur.execute("""INSERT INTO "СообщениеЗапроса" (id_запроса, id_отправителя, текст) VALUES (%s,%s,%s)""",
                    (request_id, current_user.id, text))

        if current_user.is_expert() and expert_id is None:
            cur.execute(
                """UPDATE "ЗапросЭксперту" SET id_эксперта=%s
                   WHERE id_запроса=%s AND статус IN ('открыт', 'ожидает', 'в_работе', 'отвечено')""",
                (current_user.id, request_id),
            )

        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/expert-request/<int:request_id>/close', methods=['POST'])
@login_required
def close_request(request_id: int):
    """Закрыть запрос пользователем"""
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""SELECT id_пользователя, статус FROM "ЗапросЭксперту" WHERE id_запроса=%s""", (request_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Запрос не найден'}), 404
        owner_id, status = row
        if owner_id != current_user.id:
            return jsonify({'error': 'Доступ запрещен'}), 403
        if status == 'удален_модератором':
            return jsonify({'error': 'Запрос удален'}), 400
        if status == 'закрыт':
            return jsonify({'error': 'Запрос уже закрыт'}), 400
        if not is_request_open(status):
            return jsonify({'error': 'Закрыть можно только открытый запрос'}), 400
        cur.execute("""UPDATE "ЗапросЭксперту" SET статус='закрыт', дата_закрытия=CURRENT_TIMESTAMP WHERE id_запроса=%s""", (request_id,))
        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/moderation/requests', methods=['GET'])
@login_required
def moderation_queue():
    """Очередь модерации"""
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    from psycopg2.extras import RealDictCursor
    conn = db.get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT z.*, u.username, u.email
            FROM "ЗапросЭксперту" z
            LEFT JOIN "Пользователь" u ON u.id_пользователя = z.id_пользователя
            WHERE z.статус = 'на_модерации'
            ORDER BY z.дата_создания DESC
        """)
        items = [dict(r) for r in cur.fetchall()]
        for it in items:
            if it.get('дата_создания'):
                it['дата_создания'] = it['дата_создания'].isoformat()
        return jsonify({'success': True, 'requests': items})
    finally:
        cur.close()
        conn.close()

@app.route('/api/moderation/request/<int:request_id>/approve', methods=['POST'])
@login_required
def moderation_approve(request_id: int):
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE "ЗапросЭксперту"
            SET статус='открыт', id_модератора=%s
            WHERE id_запроса=%s AND статус='на_модерации'
        """, (current_user.id, request_id))
        if cur.rowcount == 0:
            return jsonify({'error': 'Запрос не найден'}), 404
        cur.execute("""
            INSERT INTO "МодерацияЛог"(id_модератора, id_запроса, действие, детали)
            VALUES (%s, %s, 'approve_request', '')
        """, (current_user.id, request_id))
        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/moderation/request/<int:request_id>/delete', methods=['POST'])
@login_required
def moderation_delete_request(request_id: int):
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json or {}
    reason = (data.get('reason') or '').strip()
    if not reason:
        reason = 'Удалено модератором'
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""SELECT id_пользователя FROM "ЗапросЭксперту" WHERE id_запроса=%s""", (request_id,))
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Запрос не найден'}), 404
        user_id = row[0]
        cur.execute("""
            UPDATE "ЗапросЭксперту"
            SET статус='удален_модератором', id_модератора=%s, причина_удаления=%s
            WHERE id_запроса=%s
        """, (current_user.id, reason, request_id))
        cur.execute("""
            INSERT INTO "МодерацияЛог"(id_модератора, id_пользователя, id_запроса, действие, детали)
            VALUES (%s, %s, %s, 'delete_request', %s)
        """, (current_user.id, user_id, request_id, reason))
        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/moderation/user/<int:user_id>/set-role', methods=['POST'])
@login_required
def moderation_set_role(user_id: int):
    # Менять роли может только админ
    if not current_user.is_admin():
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json or {}
    role = data.get('role')
    if role not in ('пользователь', 'эксперт', 'модератор'):
        return jsonify({'error': 'Неверная роль'}), 400
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""UPDATE "Пользователь" SET роль=%s WHERE id_пользователя=%s""", (role, user_id))
        if cur.rowcount == 0:
            return jsonify({'error': 'Пользователь не найден'}), 404
        cur.execute("""
            INSERT INTO "МодерацияЛог"(id_модератора, id_пользователя, действие, детали)
            VALUES (%s, %s, 'set_role', %s)
        """, (current_user.id, user_id, f'role={role}'))
        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/moderation/user/<int:user_id>/warn-block', methods=['POST'])
@login_required
def moderation_warn_block(user_id: int):
    if not (current_user.is_moderator() or current_user.is_admin()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json or {}
    warn = bool(data.get('warn', True))
    minutes = int(data.get('block_minutes') or 0)
    permanent = bool(data.get('permanent', False))
    unblock = bool(data.get('unblock', False))
    reason = (data.get('reason') or '').strip()
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        if warn:
            cur.execute("""UPDATE "Пользователь" SET warnings_count = warnings_count + 1 WHERE id_пользователя=%s""", (user_id,))

        # Права: модератор только временно (minutes > 0), админ может временно/бессрочно/снять блокировку
        if current_user.is_moderator():
            permanent = False
            unblock = False
            if minutes <= 0:
                return jsonify({'error': 'Модератор может блокировать только на время'}), 400

        if unblock and current_user.is_admin():
            cur.execute("""UPDATE "Пользователь" SET blocked_until = NULL, blocked_permanent = FALSE WHERE id_пользователя=%s""", (user_id,))
        elif permanent and current_user.is_admin():
            cur.execute("""UPDATE "Пользователь" SET blocked_permanent = TRUE, blocked_until = NULL WHERE id_пользователя=%s""", (user_id,))
        elif minutes > 0:
            cur.execute("""UPDATE "Пользователь" SET blocked_until = CURRENT_TIMESTAMP + (%s || ' minutes')::interval, blocked_permanent = FALSE WHERE id_пользователя=%s""", (minutes, user_id))
        if cur.rowcount == 0:
            return jsonify({'error': 'Пользователь не найден'}), 404
        action = 'block_user' if (minutes > 0 or permanent or unblock) else 'warn_user'
        cur.execute("""
            INSERT INTO "МодерацияЛог"(id_модератора, id_пользователя, действие, детали)
            VALUES (%s, %s, %s, %s)
        """, (current_user.id, user_id, action, reason))
        cur.connection.commit()
        return jsonify({'success': True})
    finally:
        cur.close()
        conn.close()

@app.route('/api/insects', methods=['POST'])
@login_required
def add_insect_api():
    """Добавление нового вида насекомого (эксперт/модератор)."""
    if not (current_user.is_expert() or current_user.is_moderator()):
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json or {}
    insect_type = data.get('type')
    params = data.get('data') or {}
    if insect_type not in CATALOG_TYPE_KEYS:
        return jsonify({'error': 'Неверный тип'}), 400
    try:
        ok = db.add_insect(insect_type, params)
        return jsonify({'success': True, 'result': ok})
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
            if current_user.is_expert() or current_user.is_moderator():
                # Эксперт и модератор видят все запросы
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
                        z.id_карточки,
                        z.тип_карточки,
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
                        z.id_карточки,
                        z.тип_карточки,
                        u.имя as имя_пользователя,
                        u.email as email_пользователя
                    FROM "ЗапросЭксперту" z
                    LEFT JOIN "Пользователь" u ON z.id_пользователя = u.id_пользователя
                    WHERE z.id_пользователя = %s
                    ORDER BY z.дата_создания DESC
                """, (current_user.id,))
            
            results = [dict(row) for row in cursor.fetchall()]
            for result in results:
                if result.get('дата_создания'):
                    result['дата_создания'] = result['дата_создания'].isoformat()
                if result.get('дата_ответа'):
                    result['дата_ответа'] = result['дата_ответа'].isoformat()
                if result.get('дата_наблюдения'):
                    result['дата_наблюдения'] = str(result['дата_наблюдения'])
                enrich_expert_request(result)
            
            return jsonify({
                'success': True,
                'requests': results
            })
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/catalog/<insect_type>/<int:insect_id>', methods=['GET'])
def get_catalog_insect(insect_type, insect_id):
    """Одна карточка каталога (для прямой ссылки и предпросмотра)."""
    if insect_type not in CATALOG_TABLES:
        return jsonify({'error': 'Неверный тип насекомого'}), 400
    card = fetch_catalog_card(insect_id, insect_type)
    if not card:
        return jsonify({'error': 'Насекомое не найдено'}), 404
    return jsonify({'success': True, 'insect': card})


@app.route('/api/insects-for-selection', methods=['GET'])
@login_required
def get_insects_for_selection():
    """Получить список всех насекомых для выбора при ответе на запрос"""
    try:
        if not current_user.is_expert():
            return jsonify({'error': 'Доступ только для эксперта'}), 403
        
        all_insects = []
        for insect_type in CATALOG_TYPE_KEYS:
            for insect in db.get_all_insects(insect_type):
                all_insects.append(build_catalog_insect_item(insect, insect_type))

        all_insects.sort(key=lambda x: (x['name_ru'].lower(), x.get('gender') or '', x['id']))

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
        table_map = dict(CATALOG_TABLES)
        table_name = table_map.get(insect_type)
        if not table_name:
            return None
        
        # Получаем название
        cursor.execute(f"""
            SELECT name_ru, name_lat FROM {table_name} WHERE id = %s
        """, (insect_id,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        name_ru, name_lat = row
        
        type_map = {
            'dragonfly': 'стрекоза',
            'beetle': 'жук',
            'butterfly': 'бабочка',
            'mushroom': 'гриб',
            'herb': 'трава',
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

@app.route('/api/expert-request/<int:request_id>/attach-card', methods=['POST'])
@login_required
def attach_card_to_request(request_id: int):
    """Прикрепить карточку насекомого из каталога к запросу (эксперт)."""
    if not current_user.is_expert():
        return jsonify({'error': 'Доступ запрещен'}), 403
    data = request.json or {}
    insect_id = data.get('insect_id') or data.get('insectId')
    insect_type = data.get('insect_type') or data.get('insectType')
    if not insect_id or not insect_type:
        return jsonify({'error': 'Укажите насекомое из каталога'}), 400
    if insect_type not in CATALOG_TABLES:
        return jsonify({'error': 'Неверный тип насекомого'}), 400

    card = fetch_catalog_card(int(insect_id), insect_type)
    if not card:
        return jsonify({'error': 'Насекомое не найдено в каталоге'}), 404

    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id_пользователя, статус, id_карточки FROM "ЗапросЭксперту" WHERE id_запроса=%s""",
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Запрос не найден'}), 404
        _, status, prev_card_id = row
        if status in ('закрыт', 'удален_модератором', 'на_модерации'):
            return jsonify({'error': 'Нельзя прикрепить карточку к этому запросу'}), 400

        vid_insect_id = find_insect_id_in_vid_nasekomogo(int(insect_id), insect_type)
        image_url = card.get('image_url') or ''
        cur.execute(
            """
            UPDATE "ЗапросЭксперту"
            SET id_карточки=%s, тип_карточки=%s, id_вида_насекомого=%s,
                id_эксперта=%s, изображение_ответа=%s,
                статус='открыт'
            WHERE id_запроса=%s
            """,
            (int(insect_id), insect_type, vid_insect_id, current_user.id, image_url or None, request_id),
        )
        card_title = card.get('display_name') or card['name_ru']
        action = 'заменил' if prev_card_id else 'прикрепил'
        msg_text = f'Эксперт {action} карточку: {card_title} ({card["type_label"]})'
        cur.execute(
            """INSERT INTO "СообщениеЗапроса" (id_запроса, id_отправителя, текст) VALUES (%s,%s,%s)""",
            (request_id, current_user.id, msg_text),
        )
        conn.commit()

        payload = {'request_id': request_id, 'attached_card': card, 'статус': 'открыт'}
        try:
            socket_handlers.socketio.emit('card_attached', payload, room=f'request_{request_id}')
            socket_handlers.socketio.emit('new_message', {
                'id_сообщения': None,
                'id_отправителя': current_user.id,
                'текст': msg_text,
                'дата_создания': datetime.utcnow().isoformat(),
            }, room=f'request_{request_id}')
        except Exception:
            pass

        return jsonify({'success': True, 'attached_card': card})
    finally:
        cur.close()
        conn.close()


@app.route('/api/expert-request/<int:request_id>/detach-card', methods=['POST'])
@login_required
def detach_card_from_request(request_id: int):
    """Открепить карточку каталога от запроса (эксперт)."""
    if not current_user.is_expert():
        return jsonify({'error': 'Доступ запрещен'}), 403

    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """SELECT id_карточки, статус FROM "ЗапросЭксперту" WHERE id_запроса=%s""",
            (request_id,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({'error': 'Запрос не найден'}), 404
        card_id, status = row
        if status in ('закрыт', 'удален_модератором', 'на_модерации'):
            return jsonify({'error': 'Нельзя изменить карточку у этого запроса'}), 400
        if not card_id:
            return jsonify({'error': 'К карточке ничего не прикреплено'}), 400

        cur.execute(
            """
            UPDATE "ЗапросЭксперту"
            SET id_карточки=NULL, тип_карточки=NULL,
                id_вида_насекомого=NULL, изображение_ответа=NULL
            WHERE id_запроса=%s
            """,
            (request_id,),
        )
        msg_text = 'Эксперт открепил карточку из каталога'
        cur.execute(
            """INSERT INTO "СообщениеЗапроса" (id_запроса, id_отправителя, текст) VALUES (%s,%s,%s)""",
            (request_id, current_user.id, msg_text),
        )
        conn.commit()

        payload = {'request_id': request_id, 'attached_card': None}
        try:
            socket_handlers.socketio.emit('card_detached', payload, room=f'request_{request_id}')
            socket_handlers.socketio.emit('new_message', {
                'id_сообщения': None,
                'id_отправителя': current_user.id,
                'текст': msg_text,
                'дата_создания': datetime.utcnow().isoformat(),
            }, room=f'request_{request_id}')
        except Exception:
            pass

        return jsonify({'success': True, 'attached_card': None})
    finally:
        cur.close()
        conn.close()


@app.route('/api/expert-request/<int:request_id>/answer', methods=['POST'])
@login_required
def answer_expert_request(request_id):
    """Ответить на запрос эксперта"""
    try:
        if not current_user.is_expert():
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
        
        card_id = int(insect_id) if insect_id and insect_type else None
        card_type = insect_type if card_id else None
        if card_id and card_type and not image_url:
            c = fetch_catalog_card(card_id, card_type)
            if c:
                image_url = c.get('image_url') or image_url

        try:
            cursor.execute("""
                UPDATE "ЗапросЭксперту"
                SET ответ_эксперта = %s,
                    изображение_ответа = %s,
                    id_вида_насекомого = %s,
                    id_карточки = %s,
                    тип_карточки = %s,
                    id_эксперта = %s,
                    статус = 'открыт',
                    дата_ответа = CURRENT_TIMESTAMP
                WHERE id_запроса = %s
            """, (answer, image_url or None, vid_insect_id, card_id, card_type, current_user.id, request_id))
            
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
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)

