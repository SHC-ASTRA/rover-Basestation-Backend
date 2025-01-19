#!/bin/env python

# basic stuff
from typing import *
import asyncio
import os
import logging

# http things
from aiohttp import web
import aiohttp
from util import aiohttp_utils

# protobuf things
from generated import ProtoController
from google.protobuf.any_pb2 import Any as ProtoAny

# ros things
import rclpy
from submodules import Submodule, Core

# see: https://github.com/m2-farzan/ros2-asyncio

LOG = logging.getLogger(__name__)

routes = web.RouteTableDef()
ws_connections = aiohttp_utils.WSSender()
submodules: Set[Submodule] = set()


async def ros_loop():
    """Main ROS loop. Spins ROS asynchronously."""
    while rclpy.ok():
        for submodule in submodules:
            await submodule.spin_once()
            await asyncio.sleep(1e-4)


@routes.get("/api/ws")
async def handle_controller(request: web.BaseRequest) -> web.WebSocketResponse:
    # get the websocket ready to use
    ws = web.WebSocketResponse(heartbeat=3)
    await ws.prepare(request)
    ws_connections.add(ws)

    # when we get a message
    async for msg in ws:
        # ensure we only use binary data
        if msg.type != aiohttp.WSMsgType.BINARY:
            print("invalid websocket message type")
            continue

        # at this point, we don't know what type of data the packet holds,
        # but we can load it into a ProtoAny so we can check what it is
        raw_data = ProtoAny()
        raw_data.ParseFromString(msg.data)

        data: Optional[Any] = None

        # figure out what type of data we got
        match raw_data.type_url.split("/")[-1]:
            case "astra.Controller":
                controller = ProtoController()
                raw_data.Unpack(controller)
                data = controller
            case _:
                LOG.error("unable to parse websocket data")

        # if we got no data, skip the rest
        if data is None:
            continue

        # send the data to all submodules, they will handle it if they can
        for submodule in submodules:
            submodule.handle_ws_msg(raw_data.type_url, data)


async def main():
    # initialize ROS and submodules
    LOG.info("initializing submodules")
    rclpy.init()
    submodules.add(Core(ws_connections))

    # register a static file route for each of the proto files
    LOG.info("registering proto file routes")
    for file in os.listdir("proto"):
        aiohttp_utils.file_route(routes, f"/api/proto/{file}", f"./proto/{file}")

    LOG.info("starting site")
    app = web.Application(logger=LOG)
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port="5000")
    await site.start()
