#!/bin/env python

"""
This file exists for testing purposes, while the frontend is still being worked on.
"""

from controller_pb2 import Controller as ProtoController
from vector_pb2 import Vector as ProtoVector
from google.protobuf.any_pb2 import Any as ProtoAny
import asyncio
import aiohttp
from typing import *
import random


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
    data.id = 1

    return data


async def ws_client():
    url = "ws://localhost:8080/api/ws"

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            print("Connected to WebSocket server")

            to_send = ProtoAny()
            to_send.Pack(generate_random_data())

            # Send a message
            await ws.send_bytes(to_send.SerializeToString())

            # Receive a message
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    print(f"Message received: {msg.data}")
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    print("Connection closed by the server")
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("Error received")
                    break


if __name__ == "__main__":
    asyncio.run(ws_client())
