import asyncio
from logging.handlers import RotatingFileHandler
import os
import sys
import pkg_resources
from importlib.metadata import metadata
import logging
from py_socket_server.core.logger import NoExcInfoFilter
from py_socket_server.core.context import Context
from py_socket_server.server.xmls_server import PyXmlsServer
from py_socket_server.server.ws_server import PyWsServer

class PySocketServer:
    def __init__(self, config):
        distribution = pkg_resources.get_distribution("py_socket_server")
        pkg_metadata = metadata("py_socket_server")

        self.ctx = Context(config)

        general_log_file = self.ctx.config['log_general_path'] if self.ctx.config['log_general_path'] \
            else f"logs/{self.ctx.config['name'].lower()}.log"
        errors_log_file = self.ctx.config['log_error_path'] if self.ctx.config['log_error_path'] \
            else f"logs/{self.ctx.config['name'].lower()}-errors.log"
        general_log_directory = os.path.dirname(general_log_file)
        errors_log_directory = os.path.dirname(errors_log_file)

        if not os.path.exists(general_log_directory):
            os.mkdir(general_log_directory)

        if not os.path.exists(errors_log_directory):
            os.mkdir(errors_log_directory)

        universal_handler = RotatingFileHandler(general_log_file,
                                                maxBytes=2097152, backupCount=3, encoding='utf-8')

        error_handler = logging.FileHandler(errors_log_file)
        console_handler = logging.StreamHandler(stream=sys.stdout)

        log_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        error_handler.setLevel(logging.ERROR)

        universal_handler.setFormatter(log_formatter)
        console_handler.setFormatter(log_formatter)

        self.ctx.logger.addHandler(universal_handler)
        self.ctx.logger.addHandler(console_handler)
        self.ctx.logger.addHandler(error_handler)

        level = logging.getLevelName(config['log_type'].upper())
        self.ctx.logger.setLevel(level)

        websockets_logger = logging.getLogger("websockets.server")
        websockets_logger.setLevel(logging.ERROR)
        handler = logging.StreamHandler()
        handler.setFormatter(log_formatter)
        websockets_logger.addHandler(handler)
        websockets_logger.addFilter(NoExcInfoFilter())

        self.ctx.logger.info(f"py_socket_server v{distribution.version}")
        self.ctx.logger.info(f"Homepage: {pkg_metadata['Home-page']}")
        self.ctx.logger.info(f"License: {pkg_metadata['License']}")
        self.ctx.logger.info(f"Author: {pkg_metadata['Author']}")

        self.xmls_server = PyXmlsServer(self.ctx)
        self.ws_server = PyWsServer(self.ctx)

    def clients(self):
        return list(self.ctx.sessions.values())

    async def run(self):
        tasks = []
        if self.xmls_server:
            tasks.append(self.xmls_server.run())
        if self.ws_server:
            tasks.append(self.ws_server.run())
        
        await asyncio.gather(*tasks)

    async def on(self, event_name, listener):
        self.ctx.py_event.on(event_name, listener)

    async def stop(self):
        if hasattr(self.xmls_server, 'stop'):
            await self.xmls_server.stop()
        if hasattr(self.ws_server, 'stop'):
            await self.ws_server.stop()

    def get_session(self, id):
        return self.ctx.sessions.get(id)