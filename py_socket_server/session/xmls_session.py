import asyncio
from py_socket_server.core.context import Context
from py_socket_server.session.base_session import BaseSession
from py_socket_server.protocol.rolypoly_protocol import RolyPolyProtocol, END_MARKER

class XmlsSession(BaseSession):
    def __init__(self, ctx: Context, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        super().__init__()
        self.ctx = ctx
        self.reader = reader
        self.writer = writer
        
        try:
            self.ip = writer.get_extra_info('peername')[0] if writer else ""
        except:
            self.ip = ""
        self.is_local = self.ip in ['127.0.0.1', '::1', '::ffff:127.0.0.1']

        self.protocol = "xmls"
        self.ping_time = ctx.config[self.protocol]['ping'] * 1000 if ctx.config[self.protocol].get('ping') else self.ping_time
        self.ping_timeout = ctx.config[self.protocol]['ping_timeout'] * 1000 if ctx.config[self.protocol].get('ping_timeout') else self.ping_timeout

        self.bp = RolyPolyProtocol()

        self.ctx.sessions[self.id] = self
        self.ping_interval = None


    async def run(self):
        self.bp.on_connect_callback = self.on_connect
        self.bp.on_output_callback = self.on_output
        self.bp.on_policy_callback = self.on_policy
        self.bp.on_stop_callback = self.on_stop
        self.bp.on_event_emit_callback = self.on_event_emit

        while True:
            try:
                data = await self.reader.read(1024)
                if data:
                    await self.on_data(data)
                else:
                    break
            except ConnectionAbortedError:
                await self.stop(True)
                break
            except Exception as e:
                await self.on_error(e)
                break

        await self.on_close()

    async def stop(self, closed=False):
        if self.writer is None: 
            return

        if self.ping_interval is not None:
            self.ping_interval.cancel()
            self.ping_interval = None

        self.ctx.logger.info(f"[socket disconnect] id={self.id}")

        self.ctx.py_event.emit('doneConnect', self, self.ctx)

        if closed == False: 
            await self.bp.call_status('NetConnection.Connect.Closed', 'Connection closed.')

        if self.id in self.ctx.sessions: 
            del self.ctx.sessions[self.id]
        
        try:
            if not self.writer.is_closing():
                self.writer.close()
                await self.writer.wait_closed()
        except Exception as e:
            self.ctx.logger.error(f"Error closing writer: {e}")
        finally:
            self.writer = None

    async def on_connect(self, invoke_message):
        self.ctx.py_event.emit('preConnect', self.id, self.ctx, invoke_message)
        if self.writer is None or self.writer.is_closing(): 
            return
        
        self.connect_time = asyncio.get_event_loop().time()
        self.start_timestamp = asyncio.get_event_loop().time() * 1000
        self.ping_interval = asyncio.ensure_future(self.send_ping())

        self.ctx.logger.info(f"[socket connect] id={self.id} ip={self.ip} args={invoke_message}")
        self.ctx.py_event.emit('postConnect', self.id, self.ctx, invoke_message)

    async def send_ping(self):
        while self.writer is not None and not self.writer.is_closing():
            if self.ping_time is not None:
                try:
                    await asyncio.sleep(self.ping_time / 1000)
                    await self.bp.send_ping_request()
                except ConnectionError:
                    self.ctx.logger.warning("Connection lost during ping")
                    await self.stop()
                    break
                except Exception as e:
                    self.ctx.logger.error(f"Ping error: {e}")
                    await self.stop()
                    break
            else:
                self.ctx.logger.warning('Ping time is not set. Skipping ping request.')
                await asyncio.sleep(1)

    async def on_policy(self):
        await self.bp.send_policy_file(self.ctx.config[self.protocol]['port'])
        await self.stop(True)

    async def on_event_emit(self, event_name, *args):
        """ Emit an event with the given name and arguments. """
        self.ctx.py_event.emit(event_name, self.id, self.ctx, *args)

    async def send_buffer(self, buffer: bytes):
        """ Send a buffer through the socket. """
        if self.writer is None or self.writer.is_closing():
            return
            
        try:
            data_to_send = buffer + END_MARKER.encode('utf-8')
            self.writer.write(data_to_send)
            await self.writer.drain()
        except ConnectionResetError:
            self.ctx.logger.info('Connection reset by peer')
            await self.stop()
        except Exception as error:
            self.ctx.logger.error(f'Send buffer error: {error}')
            await self.stop()