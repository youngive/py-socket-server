import asyncio
from py_socket_server.core.context import Context
from py_socket_server.session.xmls_session import XmlsSession

class PyXmlsServer:
    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.tcp_server = None
        self.server_instance = None

        if ctx.config.get('xmls') and ctx.config['xmls'].get('port'):
            self.tcp_server = asyncio.start_server(
                self.handle_request, 
                ctx.config['xmls'].get('bind'), 
                ctx.config['xmls'].get('port')
            )

    async def run(self):
        if self.tcp_server:
            server = await self.tcp_server
            self.server_instance = server
            self.ctx.logger.info(f"XMLSocket Server listening on {self.ctx.config['xmls'].get('bind')}:{self.ctx.config['xmls'].get('port')}")
            try:
                async with server:
                    await server.serve_forever()
            except asyncio.CancelledError:
                self.ctx.logger.info("Server has been cancelled.")
            except Exception as e:
                self.ctx.logger.error(f"XMLSocket Server unexpected error: {e}")
        else:
            self.ctx.logger.error("No port found in XML configuration.")

    async def stop(self):
        if self.server_instance:
            self.ctx.logger.info("Closing the server...")
            self.server_instance.close()
            await self.server_instance.wait_closed()
            self.ctx.logger.info("Server closed gracefully.")
            self.server_instance = None

        # Stop all sessions
        session_ids = list(self.ctx.sessions.keys())
        for session_id in session_ids:
            session = self.ctx.sessions.get(session_id)
            if session and session.protocol == "xmls":
                try:
                    await session.stop()
                except Exception as e:
                    self.ctx.logger.error(f"Error stopping session {session_id}: {e}")

    async def handle_request(self, reader, writer):
        session = XmlsSession(self.ctx, reader, writer)
        await session.run()