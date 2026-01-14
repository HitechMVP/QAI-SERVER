import socketio
import logging
import asyncio
import cv2
import numpy as np
import time
from src.core.factory_manager import factory_manager

logger = logging.getLogger("SocketManager")

class DeviceSocketManager:
    def __init__(self):

        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*', 
            max_http_buffer_size=10*1024*1024 
        )
        

        self.app = socketio.ASGIApp(self.sio)

        self.connected_devices = {}   # Map: { sid: device_id }
        self.device_data = {}         # Map: { device_id: { 'frame': bytes, 'stats': dict, 'status': 'online' } }

        self.user_socket = NotImplementedError

        self._register_handlers()

    def _register_handlers(self):
     
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"🔗 New connection: {sid}")

        @self.sio.event
        async def disconnect(sid):
            device_id = self.connected_devices.get(sid)
            if device_id:
                logger.warning(f"❌ Device disconnected: {device_id} ({sid})")
                
                if device_id in self.device_data:
                    self.device_data[device_id]['status'] = 'offline'
                
                del self.connected_devices[sid]
            else:
                logger.info(f"Unknown client disconnected: {sid}")

        @self.sio.event
        async def register_device(sid, device_id):
            if not factory_manager.is_allowed(device_id):
                logger.warning(f"REJECTED: Unknown device '{device_id}' tried to connect.")
                await self.sio.disconnect(sid) 
                return
            logger.info(f"Device Accepted: {device_id} (Line: {factory_manager.device_to_line.get(device_id)})")
            
            self.connected_devices[sid] = device_id
            
            if device_id not in self.device_data:
                self.device_data[device_id] = {
                    'frame': self._create_black_frame(),
                    'stats': {},
                    'configs': {},
                    'status': 'online',
                    'last_seen': 0
                }
            else:
                self.device_data[device_id]['status'] = 'online'
            await self.send_command(device_id,'get_config')
            await self.send_command(device_id,'resend_datalog')

        @self.sio.event
        async def video_frame(sid, data):
            device_id = data.get('id')
            image_bytes = data.get('image')

            if not device_id or not image_bytes:
                return

            if device_id not in self.device_data:
                return
            
            self.device_data[device_id]['frame'] = image_bytes
            self.device_data[device_id]['status'] = 'online' 
            self.device_data[device_id]['last_seen'] = time.time()

            if self.user_socket:
                await self.user_socket.broadcast_frame(device_id, image_bytes)

        @self.sio.event
        async def telemetry(sid, data):
            device_id = data.get('id')
            mode = data.get('mode')
            data = data.get('data')
            if device_id and device_id in self.device_data:
                self.device_data[device_id][mode].update(data)

    def _create_black_frame(self):
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(img, "NO SIGNAL", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        _, buf = cv2.imencode('.jpg', img)
        return buf.tobytes()

    async def get_stream_generator(self, device_id):
        while True:
            data = self.device_data.get(device_id)
            
            if data:
                frame = data.get('frame')
                if frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(1.0)
            
            await asyncio.sleep(0.03)

    async def send_command(self, device_id, command, payload=None):
        target_sid = None
        for sid, dev_id in self.connected_devices.items():
            if dev_id == device_id:
                target_sid = sid
                break
        
        if target_sid:
            data = {'command': command, 'payload': payload}
            await self.sio.emit('server_command', data, to=target_sid)
            return True
        return False
    
    def bind_user_socket(self, user_socket):
        self.user_socket = user_socket


device_socket_manager = DeviceSocketManager()