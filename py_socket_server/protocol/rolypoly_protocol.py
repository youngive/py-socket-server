import json
import defusedxml.cElementTree as Et
#import logging
from py_socket_server.protocol.base_protocol import BaseProtocol, END_MARKER
from py_socket_server.core.spacket import SPacket

class RolyPolyProtocol(BaseProtocol):
    def __init__(self):
        super().__init__()
        self.parser_packet = SPacket()
        self.custom_commands = {}
        self.pong = None

    async def send_ping_request(self):
        """Sends a ping request."""
        if self.pong is None or self.pong is True:
            self.pong = False
            await self.call('_NSF')
        else:
            await self.disconnect()

    async def disconnect(self):
        """Disconnects the protocol."""
        await self.call("_RCD")
        await self.on_stop_callback()

    async def respond_cmd(self, data, callback_uid):
        """Responds to a command with data."""
        arr = data if isinstance(data, list) else [data]

        result = {'callback_uid': callback_uid}
        for i, value in enumerate(arr):
            result[str(i)] = value
        result['length'] = len(arr)

        await self.call("_B", result)

    async def socket_invoke_handler(self, data: str):
        """
        Handles invocation of received data.
        Returns status message about the processing result.
        """
        if not data:
            return 'Disconnected - empty message received'
        
        if data.startswith('<'):
            try:
                element_tree = Et.fromstring(data)

                if element_tree.tag == 'policy-file-request':
                    await self.on_policy_callback()
                    return
                    
                return 'Disconnected - unexpected XML message'
            except Et.ParseError as xml_error:
                return 'Disconnected due to XML parsing error'
        else:
            try:
                invoke_message = json.loads(data)
            except json.JSONDecodeError as e:
                return 'Disconnected due to message parsing error'

        #logging.info(invoke_message)

        command = invoke_message[0]
        if command in self.custom_commands:
            await self.custom_commands[command](self, invoke_message)
            return

        handlers = {
            'connect': self.on_connect_callback,
            '_SOO': self.on_SOO,
            '__resolve': self.on_resolve,
            '_P': self.on_P,
            '_LS': self.on_LS,
            '_LG': self.on_LG,
            '_S': self.on_S,
            '_SS': self.on_SS,
            '_SCA': self.on_SCA,
            '_NSF': self.on_NSF,
            '$': self.on_sigil,
            '_SCD': self.on_SCD,
            '_RCD': self.on_RCD,
            '_SCT': self.on_SCT,
            '_G': self.on_G,
        }

        handler = handlers.get(command)
        if handler:
            await handler(invoke_message)
        else:
            return f'Disconnected due to unimplemented cmd {command}'

    async def on_SOO(self, invoke_message):
        await self.on_event_emit_callback('_SOO', invoke_message)

    async def on_resolve(self, invoke_message):
        await self.on_event_emit_callback('__resolve', invoke_message)

    async def on_P(self, invoke_message):
        await self.on_event_emit_callback('_P', invoke_message)

    async def on_LS(self, invoke_message):
        #logging.info(json.dumps(invoke_message))
        await self.on_event_emit_callback('_LS', invoke_message, lambda result: self.call("_LS", result))

    async def on_LG(self, invoke_message):
        #logging.info(json.dumps(invoke_message))
        await self.on_event_emit_callback('_LG', invoke_message, self.respond_cmd)

    async def on_S(self, invoke_message):
        await self.on_event_emit_callback('_S', invoke_message)

    async def on_SS(self, invoke_message):
        await self.on_event_emit_callback('_SS', invoke_message)

    async def on_SCA(self, invoke_message):
        await self.on_event_emit_callback('_SCA', invoke_message, self.respond_cmd)

    async def on_NSF(self, invoke_message):
        await self.on_event_emit_callback('_NSF')

    async def on_sigil(self, invoke_message):
        #logging.info(json.dumps(invoke_message))
        await self.on_event_emit_callback('$', invoke_message, self.respond_cmd)

    async def on_SCD(self, invoke_message):
        await self.on_event_emit_callback('_SCD', invoke_message, self.respond_cmd)

    async def on_RCD(self, invoke_message):
        await self.on_event_emit_callback('_RCD', self.respond_cmd)

    async def on_SCT(self, invoke_message):
        await self.on_event_emit_callback('_SCT', invoke_message, self.respond_cmd)

    async def on_G(self, invoke_message):
        #logging.info(json.dumps(invoke_message))
        await self.on_event_emit_callback('_G', invoke_message, lambda result: self.call("_G", result))