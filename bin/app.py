#!/usr/bin/env python3

import os
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent / 'py_socket_server'))

from index import PySocketServer

async def main():
    with open(r'config.json') as config_file:
        config = json.load(config_file)

    if 'wss' in config:
        if 'key' in config['wss'] and not os.path.exists(config['wss']['key']):
            config['wss']['key'] = str(Path(__file__).parent.parent / config['wss']['key'])
        
        if 'cert' in config['wss'] and not os.path.exists(config['wss']['cert']):
            config['wss']['cert'] = str(Path(__file__).parent.parent / config['wss']['cert'])

    pss = PySocketServer(config)
    await pss.run()

if __name__ == "__main__":
    import asyncio
    import logging
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger = logging.getLogger('py-socket-server')
        logger.info('Shutting down...')