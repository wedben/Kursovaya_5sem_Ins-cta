"""Уведомления пользователей."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from database import Database

NOTIFICATION_TYPES = ('moderator_warning', 'request_rejected', 'expert_response')


def _row_to_dict(row) -> Dict[str, Any]:
    return {
        'id_уведомления': row[0],
        'id_пользователя': row[1],
        'id_запроса': row[2],
        'тип': row[3],
        'заголовок': row[4],
        'текст': row[5],
        'прочитано': row[6],
        'дата_создания': row[7].isoformat() if row[7] else None,
    }


def create_notification(
    user_id: int,
    ntype: str,
    title: str,
    text: str,
    request_id: Optional[int] = None,
    conn=None,
) -> Optional[Dict[str, Any]]:
    if ntype not in NOTIFICATION_TYPES:
        raise ValueError(f'Unknown notification type: {ntype}')

    own_conn = conn is None
    if own_conn:
        conn = Database().get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO "УведомлениеПользователя"
                (id_пользователя, id_запроса, тип, заголовок, текст)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_уведомления, id_пользователя, id_запроса, тип,
                      заголовок, текст, прочитано, дата_создания
            """,
            (user_id, request_id, ntype, title, text),
        )
        row = cur.fetchone()
        if own_conn:
            conn.commit()
        return _row_to_dict(row)
    except Exception:
        if own_conn:
            conn.rollback()
        raise
    finally:
        cur.close()
        if own_conn:
            conn.close()


def push_notification(user_id: int, notification: Dict[str, Any]):
    try:
        import socket_handlers
        if socket_handlers.socketio:
            socket_handlers.socketio.emit(
                'new_notification',
                notification,
                room=f'user_{user_id}',
            )
    except Exception:
        pass


def notify_user(
    user_id: int,
    ntype: str,
    title: str,
    text: str,
    request_id: Optional[int] = None,
    conn=None,
) -> Optional[Dict[str, Any]]:
    note = create_notification(user_id, ntype, title, text, request_id, conn=conn)
    if note:
        push_notification(user_id, note)
    return note


def get_notifications(user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    conn = Database().get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT id_уведомления, id_пользователя, id_запроса, тип,
                   заголовок, текст, прочитано, дата_создания
            FROM "УведомлениеПользователя"
            WHERE id_пользователя = %s
            ORDER BY дата_создания DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return [_row_to_dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def count_unread(user_id: int) -> int:
    conn = Database().get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT COUNT(*) FROM "УведомлениеПользователя"
            WHERE id_пользователя = %s AND прочитано = FALSE
            """,
            (user_id,),
        )
        return int(cur.fetchone()[0])
    finally:
        cur.close()
        conn.close()


def mark_read(notification_id: int, user_id: int) -> bool:
    conn = Database().get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE "УведомлениеПользователя"
            SET прочитано = TRUE
            WHERE id_уведомления = %s AND id_пользователя = %s
            """,
            (notification_id, user_id),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        cur.close()
        conn.close()


def mark_all_read(user_id: int) -> int:
    conn = Database().get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE "УведомлениеПользователя"
            SET прочитано = TRUE
            WHERE id_пользователя = %s AND прочитано = FALSE
            """,
            (user_id,),
        )
        conn.commit()
        return cur.rowcount
    finally:
        cur.close()
        conn.close()


def notify_moderator_warning(
    user_id: int,
    request_id: Optional[int],
    reason: str,
    conn=None,
):
    if request_id:
        title = f'Предупреждение по запросу #{request_id}'
        text = reason.strip() or 'Модератор выставил предупреждение за нарушение правил при оформлении запроса.'
    else:
        title = 'Предупреждение модератора'
        text = reason.strip() or 'Модератор выставил предупреждение.'
    return notify_user(user_id, 'moderator_warning', title, text, request_id, conn=conn)


def notify_request_rejected(user_id: int, request_id: int, reason: str, conn=None):
    title = f'Запрос #{request_id} отклонён модератором'
    text = reason.strip() or 'Запрос был удалён модератором.'
    return notify_user(user_id, 'request_rejected', title, text, request_id, conn=conn)


def notify_expert_response(
    user_id: int,
    request_id: int,
    message: str,
    conn=None,
):
    title = f'Эксперт ответил на запрос #{request_id}'
    text = message.strip() or 'Эксперт ответил на ваш запрос. Откройте чат, чтобы просмотреть ответ.'
    return notify_user(user_id, 'expert_response', title, text, request_id, conn=conn)
