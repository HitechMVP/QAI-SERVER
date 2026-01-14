import socketio
import logging
import base64
logger = logging.getLogger("UserSocket")

class UserSocketManager:
    def __init__(self):
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins="*"
        )
        self.app = socketio.ASGIApp(self.sio)

        self._register()

    def _register(self):

        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"👤 User connected: {sid}")

        @self.sio.event
        async def disconnect(sid):
            logger.info(f"👋 User disconnected: {sid}")

        @self.sio.event
        async def join_device(sid, device_id: str):
            logger.info(f"👁 User {sid} watching {device_id}")
            await self.sio.enter_room(sid, f"device_{device_id}")

        @self.sio.event
        async def leave_device(sid, device_id: str):
            await self.sio.leave_room(sid, f"device_{device_id}")

    async def broadcast_frame(self, device_id: str, image_bytes: bytes):
        base64_str = base64.b64encode(image_bytes).decode('utf-8')
        await self.sio.emit(
            "video_frame",
            {
                "device_id": device_id,
                "image": base64_str 
            },
            room=f"device_{device_id}"
        )

user_socket_manager = UserSocketManager()