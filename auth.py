from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from typing import Optional, Dict

_USER_COLUMNS = """
    id_пользователя, username, email, имя, роль,
    COALESCE(фамилия, ''), COALESCE(пол, ''), COALESCE(возраст, ''), COALESCE(тема, 'light'),
    blocked_until, COALESCE(warnings_count, 0), COALESCE(blocked_permanent, FALSE)
"""


class User(UserMixin):
    """Класс пользователя для Flask-Login"""

    def __init__(
        self,
        user_id: int,
        username: str,
        email: str,
        name: str,
        role: str,
        last_name: str = '',
        gender: str = '',
        age_status: str = '',
        theme: str = 'light',
        blocked_until=None,
        warnings_count: int = 0,
        blocked_permanent: bool = False,
    ):
        self.id = user_id
        self.user_id = user_id
        self.username = username
        self.email = email
        self.name = name
        self.first_name = name
        self.last_name = last_name
        self.role = role
        self.gender = gender
        self.age_status = age_status
        self.theme = theme if theme in ('light', 'dark') else 'light'
        self.blocked_until = blocked_until
        self.warnings_count = warnings_count or 0
        self.blocked_permanent = bool(blocked_permanent)

    def is_admin(self) -> bool:
        return self.role == 'админ'

    def is_expert(self) -> bool:
        return self.role == 'эксперт'

    def is_moderator(self) -> bool:
        return self.role == 'модератор'

    def can_manage_requests(self) -> bool:
        return self.is_admin() or self.is_expert() or self.is_moderator()

    def can_create_expert_request(self) -> bool:
        return self.role == 'пользователь'

    def is_blocked(self) -> bool:
        return bool(self.blocked_permanent) or bool(self.blocked_until)

    @staticmethod
    def _from_row(row) -> 'User':
        return User(
            user_id=row[0],
            username=row[1] or '',
            email=row[2] or '',
            name=row[3] or '',
            role=row[4] or 'пользователь',
            last_name=row[5] or '',
            gender=row[6] or '',
            age_status=row[7] or '',
            theme=row[8] or 'light',
            blocked_until=row[9],
            warnings_count=row[10] or 0,
            blocked_permanent=bool(row[11]),
        )

    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT {_USER_COLUMNS}
                FROM "Пользователь"
                WHERE id_пользователя = %s
            """, (user_id,))

            row = cursor.fetchone()
            return User._from_row(row) if row else None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_username(username: str) -> Optional['User']:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT {_USER_COLUMNS}
                FROM "Пользователь"
                WHERE username = %s
            """, (username,))

            row = cursor.fetchone()
            return User._from_row(row) if row else None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def check_unique(email: str = '', login: str = '') -> Dict[str, bool]:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT email, username
                FROM "Пользователь"
                WHERE (LOWER(email) = LOWER(%s) AND %s <> '')
                   OR (username = %s AND %s <> '')
                LIMIT 1
            """, (email, email, login, login))

            row = cursor.fetchone()
            email_exists = False
            login_exists = False
            if row:
                if email and row[0] and row[0].lower() == email.lower():
                    email_exists = True
                if login and row[1] == login:
                    login_exists = True

            return {'email_exists': email_exists, 'login_exists': login_exists}
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def create_user(
        login: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        gender: str,
        age_status: str,
        theme: str = 'light',
        role: str = 'пользователь',
    ) -> Optional['User']:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            password_hash = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO "Пользователь" (
                    username, email, пароль, имя, фамилия, пол, возраст, тема, роль
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id_пользователя
            """, (
                login, email, password_hash, first_name, last_name,
                gender, age_status, theme, role,
            ))

            user_id = cursor.fetchone()[0]
            conn.commit()

            return User(
                user_id=user_id,
                username=login,
                email=email,
                name=first_name,
                last_name=last_name,
                role=role,
                gender=gender,
                age_status=age_status,
                theme=theme,
            )
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при создании пользователя: {e}")
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def verify_password(login: str, password: str) -> Optional['User']:
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(f"""
                SELECT {_USER_COLUMNS}, пароль
                FROM "Пользователь"
                WHERE username = %s
            """, (login,))

            row = cursor.fetchone()
            # row: user columns (12) + пароль at index 12
            if row and row[12] and check_password_hash(row[12], password):
                return User._from_row(row[:12])
            return None
        finally:
            cursor.close()
            conn.close()
