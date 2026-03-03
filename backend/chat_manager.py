from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

class ConnectionManager:
    """
    Управляет WebSocket-соединениями для анонимного чата.
    - Хранит пользователей в очереди ожидания.
    - Создает приватные "комнаты", связывая двух пользователей.
    - Обрабатывает подключение, отключение и пересылку сообщений.
    """
    def __init__(self):
        # Пользователи в ожидании партнера: список словарей {"user_id": int, "websocket": WebSocket}
        self.waiting_list: List[Dict] = []
        # Активные комнаты: словарь, где ключ - ID одного юзера, значение - сокет его партнера
        self.active_rooms: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Обрабатывает новое подключение: ищет партнера или ставит в очередь."""
        await websocket.accept()
        
        if self.waiting_list:
            # Если есть ожидающий, создаем пару
            partner_info = self.waiting_list.pop(0)
            partner_ws = partner_info["websocket"]
            partner_id = partner_info["user_id"]

            self.active_rooms[user_id] = partner_ws
            self.active_rooms[partner_id] = websocket

            # Уведомляем обоих о создании пары
            await websocket.send_json({"type": "match", "partner_id": partner_id})
            await partner_ws.send_json({"type": "match", "partner_id": user_id})
        else:
            # Если в очереди никого, добавляем текущего пользователя
            self.waiting_list.append({"user_id": user_id, "websocket": websocket})
            await websocket.send_json({"type": "waiting", "text": "Ищем того, кто тебя поймет..."})

    async def disconnect(self, user_id: int):
        """Обрабатывает отключение, уведомляя партнера, если он был в чате."""
        if user_id in self.active_rooms:
            partner_ws = self.active_rooms.pop(user_id)
            partner_id = next((pid for pid, ws in self.active_rooms.items() if ws == partner_ws), None)
            if partner_id:
                self.active_rooms.pop(partner_id, None)
            await partner_ws.send_json({"type": "sys_message", "text": "Собеседник покинул чат."})
        elif any(item['user_id'] == user_id for item in self.waiting_list):
            self.waiting_list = [item for item in self.waiting_list if item['user_id'] != user_id]

    async def broadcast(self, user_id: int, message: str):
        """Отправляет сообщение партнёру по чату."""
        if user_id in self.active_rooms:
            partner_ws = self.active_rooms[user_id]
            await partner_ws.send_json({"type": "message", "text": message})