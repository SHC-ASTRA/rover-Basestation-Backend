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
from rclpy.executors import MultiThreadedExecutor
from submodules import Submodule, Core

LOG = logging.getLogger(__name__)

routes = web.RouteTableDef()
ws_connections = aiohttp_utils.WSSender()
submodules: Set[Submodule] = set()


async def spin_submodule(submodule: Submodule):
    """Main ROS loop. Spins ROS asynchronously."""
    while rclpy.ok():
        executor = MultiThreadedExecutor()
        executor.add_node(submodule._node)
        executor.spin_once(timeout_sec=0)
        await asyncio.sleep(1e-4)
    LOG.info(f"ROS loop exited for {submodule.name}")


@routes.get("/api/ws")
async def handle_controller(request: web.BaseRequest) -> web.WebSocketResponse:
    # get the websocket ready to use
    ws = web.WebSocketResponse(heartbeat=3)
    await ws.prepare(request)
    ws_connections.add(ws)
    LOG.debug(f"websocket connected at ip {request.remote}")

    # when we get a message
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.ERROR:
            LOG.error(
                f"websocket connection at ip {request.remote} closed with exception {msg.data}"
            )
            break
        if msg.type == aiohttp.WSMsgType.CLOSE:
            LOG.info(f"websocket connection at ip {request.remote} closed")
            break
        # ensure we only use binary data
        if msg.type != aiohttp.WSMsgType.BINARY:
            LOG.error(f"invalid websocket message type at ip {request.remote}")
            continue

        # at this point, we don't know what type of data the packet holds,
        # but we can load it into a ProtoAny so we can check what it is
        raw_data = ProtoAny()
        raw_data.ParseFromString(msg.data)

        data: Optional[Any] = None

        LOG.debug(
            f"received websocket message from ip {request.remote} with type {raw_data.type_url}"
        )

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
    return ws


async def start_webserver():
    app = web.Application(logger=LOG)
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port="5000")
    await site.start()


def main():
    # initialize ROS and submodules
    LOG.info("Initializing ROS")
    rclpy.init()
    submodules.add(Core(rclpy.create_node("core"), ws_connections))

    # register a static file route for each of the proto files
    LOG.info("Initializing webserver routes")
    for file in os.listdir("proto"):
        aiohttp_utils.file_route(routes, f"/api/proto/{file}", f"./proto/{file}")

    loop = asyncio.get_event_loop()
    future = asyncio.wait(
        [spin_submodule(submodule) for submodule in submodules]
        + [start_webserver(), ws_connections.loop()],
        return_when=asyncio.FIRST_EXCEPTION,
    )
    try:
        done, _ = loop.run_until_complete(future)
        for task in done:
            task.result()
    except KeyboardInterrupt:
        LOG.info("Shutting down")
