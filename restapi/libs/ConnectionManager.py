import logging, json, psutil
from fastapi import WebSocket
from user_agents import parse
from datetime import datetime
from typing import List, Union
from config import settings
from pytz import timezone

tz = timezone(settings.timezone)

logger = logging.getLogger("uvicorn.info")

class ConnectionManager:
    async def connect(self, websocket: WebSocket, user_hash: str):
        await websocket.accept()

        # set state to websocket
        user_agent = websocket.headers.get('user-agent')
        websocket.state.device = str(parse(user_agent))
        websocket.state.ip = websocket.client.host
        websocket.state.user_hash = user_hash

        # remove all duplicate connection
        for connection in self.active_connections:
            if self.check_duplicate_connection(connection,websocket) is True:
                await self.disconnect(connection,'duplicate')

        self.active_connections.append(websocket)

    def check_duplicate_connection(self, connection: WebSocket, websocket: WebSocket) -> bool:
        return connection.state.device == websocket.state.device and \
            connection.state.ip == websocket.state.ip and \
            connection.state.user_hash == websocket.state.user_hash

    async def send_data(self, kind: str, connection: WebSocket, data: Union[str, bytes]) -> None:
        try:
            if kind == 'text': await connection.send_text(data)
            if kind == 'bytes': await connection.send_bytes(data)
        except Exception:
            await self.disconnect(connection,'invalid_data')

    async def disconnect(self, websocket: WebSocket, msg: str):
        try:
            logger.info(f'{tuple(websocket.client)} - "WebSocket {websocket.url.path}" [disconnect-{msg}]')
            self.active_connections.remove(websocket)
            await websocket.close()
        except Exception:
            pass

class ConnectionDashboard(ConnectionManager):
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    def get_cpu_server_info(self) -> dict:
        cpu_core = psutil.cpu_count()
        cpu_usage = psutil.cpu_percent()
        cpu_frequency = int(psutil.cpu_freq().current)

        return {
            'cpu_core': {
                'value': cpu_core,
                'format': 'core'
            },
            'cpu_usage': {
                'value': cpu_usage,
                'format': '%'
            },
            'cpu_frequency': {
                'value': cpu_frequency,
                'format': 'MHz'
            }
        }

    def get_ram_server_info(self) -> dict:
        ram_total = int(int(psutil.virtual_memory().total) / 1024 / 1024)
        ram_available = int(int(psutil.virtual_memory().available) / 1024 / 1024)
        ram_usage = ram_total - ram_available

        return {
            'ram_total': {
                'value': ram_total,
                'format': 'MB'
            },
            'ram_available': {
                'value': ram_available,
                'format': 'MB'
            },
            'ram_usage': {
                'value': ram_usage,
                'format': 'MB'
            }
        }

    def get_disk_server_info(self) -> dict:
        disk_root = psutil.disk_usage('/')
        disk_total = int(int(disk_root.total) / 1024 / 1024 / 1024)
        disk_available = int(int(disk_root.free) / 1024 / 1024 / 1024)
        disk_usage = int(int(disk_root.used) / 1024 / 1024 / 1024)

        return {
            'disk_total': {
                'value': disk_total,
                'format': 'GB'
            },
            'disk_available': {
                'value': disk_available,
                'format': 'GB'
            },
            'disk_usage': {
                'value': disk_usage,
                'format': 'GB'
            }
        }

    def get_expired_server_info(self) -> dict:
        time_now = datetime.now(tz).replace(tzinfo=None)

        vps_expired = datetime.strptime(settings.vps_expired,'%Y-%m-%d')
        domain_expired = datetime.strptime(settings.domain_expired,'%Y-%m-%d')

        return {
            'vps_expired': {
                'date': vps_expired.strftime('%d-%m-%Y'),
                'remaining': (vps_expired.date() - time_now.date()).days
            },
            'domain_expired': {
                'date': domain_expired.strftime('%d-%m-%Y'),
                'remaining': (domain_expired.date() - time_now.date()).days
            }
        }

    async def send_server_info(self, user_hash: str) -> None:
        cpu_info = self.get_cpu_server_info()
        ram_info = self.get_ram_server_info()
        disk_info = self.get_disk_server_info()
        expired_info = self.get_expired_server_info()

        result = {
            'cpu_info': cpu_info, 'ram_info': ram_info,
            'disk_info': disk_info, 'expired_info': expired_info
        }

        user_connect = next(filter(lambda x: x.state.user_hash == user_hash, self.active_connections))
        await self.send_data('text', user_connect, json.dumps(result,default=str))
