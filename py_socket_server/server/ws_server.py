import asyncio
import ssl
import websockets
from py_socket_server.core.context import Context
from py_socket_server.session.ws_session import WsSession

class PyWsServer:
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.ws_server_instance = None
        self.wss_server_instance = None

        # HTTP WebSocket (ws) Server
        self.ws_server = None
        if ctx.config.get('ws') and ctx.config['ws'].get('port'):
            try:
                self.ws_server = websockets.serve(
                    self.handle_connection,
                    ctx.config['ws'].get('bind'),
                    ctx.config['ws'].get('port')
                )
            except Exception as e:
                self.ctx.logger.error(f'Caught Exception: {e}')

        # HTTPS WebSocket (wss) Server
        self.wss_server = None
        if ctx.config.get('wss') and ctx.config['wss'].get('port'):
            server_ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            server_ssl_context.load_cert_chain(
                ctx.config['wss'].get('cert'),
                keyfile=ctx.config['wss'].get('key')
            )

            try:
                self.wss_server = websockets.serve(
                    self.handle_connection,
                    ctx.config['wss'].get('bind'),
                    ctx.config['wss'].get('port'),
                    ssl=server_ssl_context
                )
            except Exception as e:
                self.ctx.logger.error(f'Caught Exception: {e}')

    async def run(self):
        if self.ws_server:
            self.ws_server_instance = await self.ws_server
            self.ctx.logger.info(f"WebSocket Server listening on {self.ctx.config['ws']['bind']}:{self.ctx.config['ws']['port']}")

        if self.wss_server:
            self.wss_server_instance = await self.wss_server
            self.ctx.logger.info(f"Secure WebSocket Server listening on {self.ctx.config['wss']['bind']}:{self.ctx.config['wss']['port']}")

    async def handle_connection(self, websocket: websockets.ServerConnection):
        """
        Handles a new WebSocket connection.
        Wraps the session logic in a try-except block to handle exceptions gracefully.
        """
        session = WsSession(self.ctx, websocket)
        await session.run()

    async def stop(self):
        if self.ws_server_instance:
            self.ws_server_instance.close()
            await self.ws_server_instance.wait_closed()
            self.ws_server_instance = None
            self.ctx.logger.info("WS Server closed gracefully.")

        if self.wss_server_instance:
            self.wss_server_instance.close()
            await self.wss_server_instance.wait_closed()
            self.wss_server_instance = None
            self.ctx.logger.info("WSS Server closed gracefully.")

        # Stop all sessions
        sessions_to_stop = list(self.ctx.sessions.values())
        for session in sessions_to_stop:
            if session and (session.protocol == "ws" or session.protocol == "wss"):
                try:
                    await session.stop()
                except Exception as e:
                    self.ctx.logger.error(f"Error stopping WS session: {e}")