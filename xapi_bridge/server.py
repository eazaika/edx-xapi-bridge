"""
HTTP-сервер для проверки работоспособности сервиса.

Мигрировано на Python 3.10 с:
- Современными импортами модулей
- Аннотациями типов
- Поддержкой Unicode
"""

import http.server
import socketserver
from typing import Tuple

from xapi_bridge import settings


class StatusOKRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Обработчик запросов для проверки статуса сервиса."""
    
    def do_GET(self) -> None:
        """
        Обрабатывает GET-запросы, всегда возвращая статус 200 OK.
        
        Поддерживает все пути запросов для упрощения мониторинга.
        """
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'Service is operational\n')

    def log_request(self, code: int = ..., size: int = ...) -> None:
        """Отключает стандартное логирование запросов."""
        pass


def run_server() -> Tuple[str, int]:
    """Запускает HTTP-сервер для мониторинга."""
    host = getattr(settings, 'HTTP_PUBLISH_IP', '0.0.0.0')
    port = getattr(settings, 'HTTP_PUBLISH_PORT', 9090)
    
    with socketserver.TCPServer((host, port), StatusOKRequestHandler) as httpd:
        print(f"Status server running on {host}:{port}")
        httpd.serve_forever()

    return host, port


# Глобальный объект сервера для управления жизненным циклом
httpd = socketserver.TCPServer(
    (getattr(settings, 'HTTP_PUBLISH_IP', '0.0.0.0'),
     getattr(settings, 'HTTP_PUBLISH_PORT', 9090)),
    StatusOKRequestHandler
)
