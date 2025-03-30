from typing import Any
import logging
from py_socket_server.core.spacket import SPacket
from py_socket_server.core.utils import safe_tags_replace

import json

END_MARKER = chr(0)

class BaseProtocol:
    def __init__(self):
        self.parser_packet = SPacket()
        self.custom_commands = {}

    async def on_output_callback(self, message: Any) -> None:
        """Abstract method for handling output callbacks."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def on_stop_callback(self) -> None:
        """Abstract method for handling stop callbacks."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def on_connect_callback(self, invoke_message):
        """Abstract method for handling connect callbacks."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def on_event_emit_callback(self, event_name, *args):
        """Abstract method for handling event emit callbacks."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def send_ping_request(self):
        """Abstract method for sending ping requests."""
        raise NotImplementedError("Subclasses should implement this method.")

    async def parser_data(self, message) -> Any:
        """Parses incoming data from various formats."""
        if isinstance(message, str):
            # Преобразуем строку в bytearray
            data = bytearray(message.encode('utf-8'))
        elif isinstance(message, bytes):
            # Преобразуем байты в bytearray
            data = bytearray(message)
        elif isinstance(message, bytearray):
            # Если уже bytearray, оставляем как есть
            data = message
        elif isinstance(message, list):
            # Преобразуем список в bytearray
            data = bytearray(b''.join(bytes(item) for item in message))
        else:
            raise ValueError(f"Unsupported message type")

        return await self.socket_read(data)

    async def socket_read(self, data: bytearray) -> Any:
        """Reads data from the socket and processes it."""
        self.parser_packet.data += data
        
        while END_MARKER.encode() in self.parser_packet.data:
            null_byte_index = self.parser_packet.data.index(END_MARKER.encode())
            complete_data = self.parser_packet.data[:null_byte_index]
            self.parser_packet.data = self.parser_packet.data[null_byte_index + 1:]

            invoke_data = complete_data.decode()
            if len(invoke_data) < 1:
                return 'No data received'
            
            return await self.socket_invoke_handler(invoke_data)

    async def socket_invoke_handler(self, data: str):
        """Handles invocation of data received."""
        try:
            invoke_message = json.loads(data)
        except json.JSONDecodeError as e:
            return 'Disconnected due to message parsing error'

        logging.info(invoke_message)

        command = invoke_message[0]
        if command in self.custom_commands:
            self.custom_commands[command](invoke_message)
            return
        
        if command == 'connect':
            await self.on_connect_callback(invoke_message)
        else:
            return f'Disconnected due to unimplemented cmd {command}'

    async def call(self, *args):
        """Calls a method with arguments serialized as JSON."""
        try:
            str_args = json.dumps(args)
            await self.on_output_callback(str_args.encode())
        except Exception as error:
            return f'Parse message error: {error}'

    async def call_xml(self, data, uid):
        """Calls XML response with safe tags."""
        try:
            xml = f'<root uid="{uid}" res="{safe_tags_replace(data)}" />'
            await self.on_output_callback(xml.encode())
        except Exception as error:
            return f'Parse message error: {error}'

    async def call_status(self, code, desc, error_code=None):
        """Sends a status response."""
        status_response = {
            "code": code,
            "description": desc,
        }
        if error_code is not None:
            status_response['error_code'] = error_code

        await self.call('onStatus', status_response)

    async def disconnect(self):
        """Disconnects the protocol."""
        await self.on_stop_callback()