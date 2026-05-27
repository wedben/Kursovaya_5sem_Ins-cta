"""Серверная валидация полей регистрации и входа (аналог includes/validators.php)."""
import re
from typing import Optional


def v_trim(s: str) -> str:
    return s.strip()


_LETTERS = r'A-Za-zА-Яа-яЁё'


def v_first_name(s: str) -> Optional[str]:
    s = v_trim(s)
    if not re.match(rf'^[{_LETTERS}]{{2,15}}$', s):
        return 'Имя: только текст (буквы), 2–15 символов.'
    return None


def v_last_name(s: str) -> Optional[str]:
    s = v_trim(s)
    if not re.match(rf'^[{_LETTERS}]{{2,15}}(-[{_LETTERS}]{{1,15}})?$', s):
        return 'Фамилия: 2–15 букв, можно двойную через дефис (например, Иванов-Петров или User-U).'
    return None


def v_email(s: str) -> Optional[str]:
    s = v_trim(s)
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', s):
        return 'Email: неверный формат.'
    return None


def v_login(s: str) -> Optional[str]:
    s = v_trim(s)
    if len(s) < 6:
        return 'Логин: минимум 6 символов.'
    return None


def v_password(s: str) -> Optional[str]:
    if len(s) < 8:
        return 'Пароль: минимум 8 символов.'
    if re.search(r'\s', s):
        return 'Пароль: пробелы недопустимы.'
    if not re.search(r'[a-z]', s):
        return 'Пароль: добавьте строчные буквы.'
    if not re.search(r'[A-Z]', s):
        return 'Пароль: добавьте прописные буквы.'
    if not re.search(r'\d', s):
        return 'Пароль: добавьте цифры.'
    if not re.search(r'[^a-zA-Z0-9]', s):
        return 'Пароль: добавьте спецсимвол.'
    return None


def v_gender(s: str) -> Optional[str]:
    return None if s in ('male', 'female') else 'Пол: выберите значение.'


def v_age_status(s: str) -> Optional[str]:
    return None if s in ('18plus', 'under18') else 'Возраст: выберите значение.'


def v_rules_checked(s: Optional[str]) -> Optional[str]:
    return None if s == '1' else 'Нужно принять правила (чекбокс).'
