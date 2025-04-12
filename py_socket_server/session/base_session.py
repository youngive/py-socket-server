import os
import math
import traceback
from typing import Any

from py_socket_server.core.context import Context
from py_socket_server.protocol.base_protocol import BaseProtocol

POOL_SIZE_MULTIPLIER = 128
pool = None
pool_offset = 0

def fill_pool(bytes):
    global pool, pool_offset
    if pool is None or len(pool) < bytes:
        pool = os.urandom(bytes * POOL_SIZE_MULTIPLIER)
        pool_offset = 0
    elif pool_offset + bytes > len(pool):
        pool = os.urandom(len(pool))
        pool_offset = 0
    pool_offset += bytes

def random_bytes(bytes):
    global pool_offset
    fill_pool(bytes)
    
    if pool is None or len(pool) == 0:
        raise ValueError("Random pool has not been initialized properly.")
    
    return pool[pool_offset - bytes:pool_offset]

def custom_random(alphabet, default_size, get_random):
    mask = (2 << (31 - (alphabet_length := len(alphabet)) - 1).bit_length()) - 1
    step = math.ceil((1.6 * mask * default_size) / alphabet_length)

    def generate(size=default_size):
        id_str = ""
        while True:
            bytes_data = get_random(step)
            for i in range(step):
                char_index = bytes_data[i] & mask
                if char_index < alphabet_length:
                    id_str += alphabet[char_index]
                if len(id_str) >= size:
                    return id_str
    return generate

random_id = custom_random("1234567890abcdefghijklmnopqrstuvwxyz", 16, random_bytes)
SOCKET_PING_TIME = 60000
SOCKET_PING_TIMEOUT = 30000

class BaseSession:
    SOCKET_PING_TIME = 60000
    SOCKET_PING_TIMEOUT = 30000

    def __init__(self):
        self.ctx = Context()
        self.id = random_id()
        self.ip = ""
        self.protocol = ""
        self.host = ""

        self.ping_time = self.SOCKET_PING_TIME
        self.ping_timeout = self.SOCKET_PING_TIMEOUT
        self.ping_interval = None

        self.bp = BaseProtocol()

    def send_buffer(self, buffer):
        raise NotImplementedError("Subclasses should implement this!")

    async def on_output(self, message: Any) -> None:
        await self.send_buffer(message)

    async def on_stop(self, closed=False) -> None:
        await self.stop(closed)

    async def on_close(self):
        self.ctx.logger.info(f"Session {self.id} close")
        await self.stop()

    async def on_data(self, data):
        err = await self.bp.parser_data(data)
        if err is not None:
            self.ctx.logger.error(f"Session {self.id} {self.ip} parserData error, {err}")
            await self.stop()

    async def on_error(self, error):
        tb = traceback.extract_tb(error.__traceback__)
        filename, lineno, funcname, text = tb[-1]

        self.ctx.logger.error(f"Session {self.id} socket error, {error.__class__.__name__}: {str(error)}")
        self.ctx.logger.error(f"Error occurred in file: {filename}, line: {lineno}, function: {funcname}, text: {text}")
        
        await self.stop(True)

    async def on_timeout(self):
        self.ctx.logger.info(f"Session {self.id} socket timeout")
        await self.stop()

    async def accept_connection(self):
        await self.bp.call_status('NetConnection.Connect.Success', 'Connection succeeded.')

    async def reject_connection(self, error_code = None):
        await self.bp.call_status('NetConnection.Connect.Rejected', 'Connection rejected.', error_code)
        await self.reject()

    async def disconnect(self):
        await self.bp.disconnect()

    async def call(self, *args):
        await self.bp.call(*args)

    async def call_xml(self, data, uid):
        await self.bp.call_xml(data, uid)

    async def send_policy_file(self):
        pass

    async def run(self):
        raise NotImplementedError("Subclasses should implement this!")

    async def stop(self, closed=False):
        raise NotImplementedError("Subclasses should implement this!")

    async def reject(self):
        self.ctx.logger.info(f"[socket reject] id={self.id}")
        await self.stop()

    async def register_command(self, command_name, handler):
        # self.ctx.logger.info(f"registerCommand: {command_name}")
        self.bp.custom_commands[command_name] = handler
        # self.ctx.logger.info(f"customCommands: {self.bp.custom_commands}")