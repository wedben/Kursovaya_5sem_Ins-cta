from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from database import Database
from typing import Optional, Dict

class User(UserMixin):
    """Класс пользователя для Flask-Login"""
    def __init__(self, user_id: int, username: str, email: str, name: str, role: str):
        self.id = user_id
        self.user_id = user_id
        self.username = username
        self.email = email
        self.name = name
        self.role = role
    
    def is_admin(self) -> bool:
        """Проверка, является ли пользователь админом"""
        return self.role in ('админ', 'эксперт')
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """Получить пользователя по ID"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id_пользователя, username, email, имя, роль
                FROM "Пользователь"
                WHERE id_пользователя = %s
            """, (user_id,))
            
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row[0],
                    username=row[1] or '',
                    email=row[2] or '',
                    name=row[3] or '',
                    role=row[4] or 'пользователь'
                )
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def get_by_username(username: str) -> Optional['User']:
        """Получить пользователя по username"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id_пользователя, username, email, имя, роль
                FROM "Пользователь"
                WHERE username = %s
            """, (username,))
            
            row = cursor.fetchone()
            if row:
                return User(
                    user_id=row[0],
                    username=row[1] or '',
                    email=row[2] or '',
                    name=row[3] or '',
                    role=row[4] or 'пользователь'
                )
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def create_user(username: str, email: str, password: str, name: str, role: str = 'пользователь') -> Optional['User']:
        """Создать нового пользователя"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Хешируем пароль
            password_hash = generate_password_hash(password)
            
            cursor.execute("""
                INSERT INTO "Пользователь" (username, email, пароль, имя, роль)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_пользователя
            """, (username, email, password_hash, name, role))
            
            user_id = cursor.fetchone()[0]
            conn.commit()
            
            return User(
                user_id=user_id,
                username=username,
                email=email,
                name=name,
                role=role
            )
        except Exception as e:
            conn.rollback()
            print(f"Ошибка при создании пользователя: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def verify_password(username: str, password: str) -> Optional['User']:
        """Проверить пароль и вернуть пользователя"""
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id_пользователя, username, email, имя, роль, пароль
                FROM "Пользователь"
                WHERE username = %s
            """, (username,))
            
            row = cursor.fetchone()
            if row and row[5]:  # Если есть пароль
                if check_password_hash(row[5], password):
                    return User(
                        user_id=row[0],
                        username=row[1] or '',
                        email=row[2] or '',
                        name=row[3] or '',
                        role=row[4] or 'пользователь'
                    )
            return None
        finally:
            cursor.close()
            conn.close()

