#!/bin/env python

"""
This file exists for testing purposes, while the frontend is still being worked on.
"""

import asyncio
from generated import ProtoController
from google.protobuf.any_pb2 import Any as ProtoAny
import aiohttp
from typing import *
import random
import logging

LOG = logging.getLogger(__name__)


def generate_random_data() -> ProtoController:
    rand_bool = lambda: random.choice([True, False])

    data = ProtoController()
    data.a = rand_bool()
    data.b = rand_bool()
    data.x = rand_bool()
    data.y = rand_bool()
    data.left_bumper = rand_bool()
    data.right_bumper = rand_bool()
    data.left_stick_press = rand_bool()
    data.right_stick_press = rand_bool()
    data.up = rand_bool()
    data.down = rand_bool()
    data.right = rand_bool()
    data.left = rand_bool()
    data.share = rand_bool()
    data.option = rand_bool()
    data.logo = rand_bool()
    data.left_trigger = random.random()
    data.right_trigger = random.random()
    data.left_stick.x = random.random()
    data.left_stick.y = random.random()
    data.right_stick.x = random.random()
    data.right_stick.y = random.random()
    data.submodule = "core"

    return data


async def send_data(ws: aiohttp.ClientWebSocketResponse):
    while not (ws.closed):
        to_send = ProtoAny()
        to_send.Pack(generate_random_data())

        await ws.send_bytes(to_send.SerializeToString())
        await asyncio.sleep(1)


async def ws_client():
    url = "ws://localhost:80/api/ws"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            LOG.info("Connected to WebSocket server")

            to_send = ProtoAny()
            to_send.Pack(generate_random_data())

            # add sender task
            asyncio.create_task(send_data(ws))

            # Receive a message
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    LOG.info(f"Message received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    LOG.info("Connection closed by the server")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    LOG.error("Error received")
                    break
