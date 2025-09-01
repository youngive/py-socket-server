import asyncio
import websockets

from py_socket_server.core.context import Context
from py_socket_server.session.base_session import BaseSession
from py_socket_server.protocol.rolypoly_protocol import RolyPolyProtocol, END_MARKER

class WsSession(BaseSession):
    def __init__(self, ctx: Context, socket: websockets.ServerConnection):
        super().__init__()
        self.ctx = ctx
        self.socket = socket
        self.ip = socket.remote_address[0]
        self.is_local = self.ip in ['127.0.0.1', '::1', '::ffff:127.0.0.1']


        self.protocol = "wss" if ctx.config.get('wss') is not None else "ws"
        self.ping_time = ctx.config[self.protocol]['ping'] * 1000 if ctx.config[self.protocol].get('ping') else self.ping_time
        self.ping_timeout = ctx.config[self.protocol]['ping_timeout'] * 1000 if ctx.config[self.protocol].get('ping_timeout') else self.ping_timeout

        self.bp = RolyPolyProtocol()

        self.ctx.sessions[self.id] = self

    async def run(self):
        self.bp.on_connect_callback = self.on_connect
        self.bp.on_output_callback = self.on_output
        self.bp.on_stop_callback = self.on_stop
        self.bp.on_event_emit_callback = self.on_event_emit

        if self.socket is None: return

        while True:
            try:
                message = await self.socket.recv()
                if message:
                    await self.on_data(message)
                else:
                    break
            except (
                websockets.exceptions.ConnectionClosedError, websockets.exceptions.InvalidHandshake, websockets.exceptions.InvalidURI,
                websockets.exceptions.InvalidState, websockets.exceptions.ProtocolError
            ) as e:
                await self.on_error(e)
                break
            except websockets.exceptions.ConnectionClosedOK as e:
                await self.on_stop(True)
                break
            except Exception as e:
                await self.on_error(e)
                break

        await self.on_close()

    async def stop(self, closed=False):
        if self.socket is None: return
            
        if hasattr(self, 'ping_interval') and self.ping_interval is not None:
            self.ping_interval.cancel()
            self.ping_interval = None

        self.ctx.logger.info(f"[socket disconnect] id={self.id} closed={closed}")

        self.ctx.py_event.emit('doneConnect', self, self.ctx)

        if closed == False: await self.bp.call_status('NetConnection.Connect.Closed', 'Connection closed.')

        if self.id in self.ctx.sessions: del self.ctx.sessions[self.id]

        await self.socket.close()
        self.socket = None


    async def on_close(self):
        self.ctx.logger.info(f"Session {self.id} close")
        await self.stop()

    async def on_connect(self, invoke_message):
        self.ctx.py_event.emit('preConnect', self.id, self.ctx, invoke_message)
        if not self.socket: return
        
        self.connect_time = asyncio.get_event_loop().time()
        self.start_timestamp = asyncio.get_event_loop().time()
        self.ping_interval = asyncio.create_task(self.ping())

        self.ctx.logger.info(f"[socket connect] id={self.id} ip={self.ip} args={invoke_message}")
        self.ctx.py_event.emit('postConnect', self.id, self.ctx, invoke_message)

    async def ping(self):
        while self.socket:
            await asyncio.sleep(self.ping_time / 1000)
            await self.bp.send_ping_request()

    async def on_event_emit(self, event_name, *args):
        self.ctx.py_event.emit(event_name, self.id, self.ctx, *args)

    async def send_buffer(self, buffer):
        try:
            data_to_send = buffer + END_MARKER.encode()
            if self.socket:
                await self.socket.send(data_to_send)
        except (websockets.exceptions.ConnectionClosed, Exception) as error:
            self.ctx.logger.error(f'Send buffer error: {error}')
            await self.stop(True)