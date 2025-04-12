from pyee.asyncio import AsyncIOEventEmitter
import logging

default = {
    "name": "py_socket_server",
    "log_general_path": "logs/py_socket_server.log",
    "log_error_path": "logs/py_socket_server-errors.log",
	"log_type": "critical",
    "xmls": {
        "bind": "0.0.0.0",
        "port": 1935,
		"ping": 60,
		"ping_timeout": 30
    },
    "wss": {
        "bind": "0.0.0.0",
        "port": 8080,
        "key": "./key.pem",
        "cert": "./cert.pem",
		"ping": 60,
		"ping_timeout": 30
    },
    "ws": {
        "bind": "0.0.0.0",
        "port": 8000,
		"ping": 60,
		"ping_timeout": 30
    }
}

class Context:
    def __init__(self, config=default):
        self.config = config

        self.sessions = {}

        self.py_event = AsyncIOEventEmitter()

        self.logger = logging.getLogger('py-socket-server')