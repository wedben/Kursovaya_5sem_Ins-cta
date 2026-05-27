"""Google reCAPTCHA v2 — серверная проверка (аналог includes/recaptcha.php)."""
import os
import urllib.parse
import urllib.request
import json
import ssl
from typing import Optional

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()


def recaptcha_enabled() -> bool:
    return bool(os.getenv('RECAPTCHA_SITE_KEY') and os.getenv('RECAPTCHA_SECRET_KEY'))


def recaptcha_site_key() -> str:
    return os.getenv('RECAPTCHA_SITE_KEY', '')


def recaptcha_verify(token: str, remote_ip: Optional[str] = None) -> dict:
    secret = os.getenv('RECAPTCHA_SECRET_KEY', '')
    if not secret:
        return {'ok': False, 'error': 'reCAPTCHA не настроена на сервере.'}
    if not token:
        return {'ok': False, 'error': 'Подтвердите, что вы не робот.'}

    payload = urllib.parse.urlencode({
        'secret': secret,
        'response': token,
        'remoteip': remote_ip or '',
    }).encode('utf-8')

    try:
        req = urllib.request.Request(
            'https://www.google.com/recaptcha/api/siteverify',
            data=payload,
            method='POST',
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
        )
        with urllib.request.urlopen(req, timeout=5, context=SSL_CONTEXT) as resp:
            raw = resp.read().decode('utf-8')
    except Exception:
        return {'ok': False, 'error': 'Не удалось проверить reCAPTCHA. Повторите попытку.'}

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {'ok': False, 'error': 'reCAPTCHA не пройдена.'}

    if not data.get('success'):
        return {'ok': False, 'error': 'reCAPTCHA не пройдена.'}

    return {'ok': True}
