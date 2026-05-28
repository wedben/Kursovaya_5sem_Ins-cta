"""WebSocket-чат по запросам (комната на каждый id_запроса)."""
from datetime import datetime
from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from auth import User
from database import Database

# Импортируется после создания app и login_manager
socketio = None


def init_socketio(sio):
    global socketio
    socketio = sio
    register_handlers()


def register_handlers():
    if socketio is None:
        return

    @socketio.on('connect')
    def on_connect():
        if not current_user.is_authenticated:
            return False
        emit('connected', {'user_id': current_user.id, 'username': current_user.username})

    @socketio.on('join_request')
    def on_join_request(data):
        if not current_user.is_authenticated:
            emit('chat_error', {'message': 'Требуется вход в систему'})
            return False
        request_id = data.get('request_id')
        if not request_id:
            emit('chat_error', {'message': 'Не указан запрос'})
            return False
        room = f'request_{request_id}'
        join_room(room)

        conn = Database().get_connection()
        cur = conn.cursor()
        messages = []
        req_info = None
        try:
            cur.execute(
                """SELECT id_пользователя, id_эксперта, статус, id_карточки, тип_карточки,
                          описание_насекомого, место_наблюдения, дата_наблюдения,
                          дополнительные_данные, дата_создания
                   FROM "ЗапросЭксперту" WHERE id_запроса=%s""",
                (request_id,),
            )
            row = cur.fetchone()
            if not row:
                leave_room(room)
                emit('chat_error', {'message': 'Запрос не найден'})
                return False
            (
                owner_id, expert_id, status, card_id, card_type,
                description, location, obs_date, additional, created_at,
            ) = row
            allowed = (
                current_user.is_moderator()
                or current_user.is_admin()
                or owner_id == current_user.id
                or expert_id == current_user.id
                or (
                    current_user.is_expert()
                    and status not in ('закрыт', 'удален_модератором', 'на_модерации')
                )
            )
            if not allowed:
                leave_room(room)
                emit('chat_error', {'message': 'Доступ запрещен'})
                return False

            cur.execute(
                """
                SELECT id_сообщения, id_отправителя, текст, дата_создания
                FROM "СообщениеЗапроса"
                WHERE id_запроса=%s
                ORDER BY дата_создания ASC
                """,
                (request_id,),
            )
            for r in cur.fetchall():
                messages.append({
                    'id_сообщения': r[0],
                    'id_отправителя': r[1],
                    'текст': r[2],
                    'дата_создания': r[3].isoformat() if r[3] else None,
                })

            req_info = {
                'id_запроса': request_id,
                'id_пользователя': owner_id,
                'id_эксперта': expert_id,
                'статус': status,
                'id_карточки': card_id,
                'тип_карточки': card_type,
                'описание_насекомого': description,
                'место_наблюдения': location,
                'дата_наблюдения': str(obs_date) if obs_date else None,
                'дополнительные_данные': additional,
                'дата_создания': created_at.isoformat() if created_at else None,
            }
            try:
                from app import enrich_expert_request, filter_chat_messages
                req_info = enrich_expert_request(req_info)
                messages = filter_chat_messages(messages, req_info)
            except Exception:
                if req_info is not None:
                    req_info['attached_card'] = None
        except Exception as e:
            emit('chat_error', {'message': str(e)})
            return False
        finally:
            cur.close()
            conn.close()

        if req_info is not None:
            emit('chat_history', {
                'request_id': request_id,
                'request': req_info,
                'messages': messages,
            })
        return True

    @socketio.on('leave_request')
    def on_leave_request(data):
        request_id = data.get('request_id') if data else None
        if request_id:
            leave_room(f'request_{request_id}')

    @socketio.on('send_message')
    def on_send_message(data):
        if not current_user.is_authenticated:
            return
        request_id = data.get('request_id')
        text = (data.get('text') or '').strip()
        if not request_id or not text:
            emit('error', {'message': 'Пустое сообщение'})
            return

        conn = Database().get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """SELECT id_пользователя, id_эксперта, статус FROM "ЗапросЭксперту" WHERE id_запроса=%s""",
                (request_id,),
            )
            row = cur.fetchone()
            if not row:
                emit('error', {'message': 'Запрос не найден'})
                return
            owner_id, expert_id, status = row
            if status in ('закрыт', 'удален_модератором'):
                emit('error', {'message': 'Запрос закрыт'})
                return

            allowed = (
                current_user.is_moderator()
                or current_user.is_admin()
                or owner_id == current_user.id
                or expert_id == current_user.id
                or (
                    current_user.is_expert()
                    and status not in ('закрыт', 'удален_модератором', 'на_модерации')
                )
            )
            if not allowed:
                emit('error', {'message': 'Доступ запрещен'})
                return

            cur.execute(
                """INSERT INTO "СообщениеЗапроса" (id_запроса, id_отправителя, текст)
                 VALUES (%s, %s, %s) RETURNING id_сообщения, дата_создания""",
                (request_id, current_user.id, text),
            )
            msg_id, created = cur.fetchone()
            if current_user.is_expert() and expert_id is None:
                cur.execute(
                    """UPDATE "ЗапросЭксперту" SET id_эксперта=%s WHERE id_запроса=%s""",
                    (current_user.id, request_id),
                )
            conn.commit()

            payload = {
                'id_сообщения': msg_id,
                'id_отправителя': current_user.id,
                'текст': text,
                'дата_создания': created.isoformat() if created else datetime.utcnow().isoformat(),
            }
            room = f'request_{request_id}'
            emit('new_message', payload, room=room, broadcast=True)
            emit('request_activity', {
                'request_id': request_id,
                'last_message': text[:80],
                'status': 'открыт',
            }, broadcast=True)
            return {'ok': True}
        except Exception as e:
            conn.rollback()
            emit('error', {'message': str(e)})
            return {'ok': False, 'error': str(e)}
        finally:
            cur.close()
            conn.close()

    @socketio.on('typing')
    def on_typing(data):
        request_id = data.get('request_id')
        if request_id and current_user.is_authenticated:
            emit(
                'user_typing',
                {'request_id': request_id, 'user_id': current_user.id},
                room=f'request_{request_id}',
                include_self=False,
            )
