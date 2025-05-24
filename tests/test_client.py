#!/bin/env python

"""
This file is used to generate random websocket data and send it to the server.
"""

import asyncio
import aiohttp
from typing import *
from .util import generate_random_data
import logging
from util import websocket_types
from ros2_interfaces_pkg.msg import ArmManual

LOG = logging.getLogger(__name__)


async def send_data(ws: aiohttp.ClientWebSocketResponse):
    while not (ws.closed):
        await ws.send_str(
            generate_random_data(
                websocket_types.ArmManualData.from_ros(ArmManual())
            ).to_json()
        )
        await asyncio.sleep(1)


async def main():
    url = "ws://localhost:80/api/ws"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            LOG.info("Connected to WebSocket server")

            # add sender task
            asyncio.create_task(send_data(ws))

            # Receive a message
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    LOG.info(f"Message received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    LOG.info("Connection closed by the server")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    LOG.error("Error received")
                    break
