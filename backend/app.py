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

# websocket data
from util import websocket_types

# ros things
import rclpy
from rclpy.executors import MultiThreadedExecutor
from submodules import Submodule, Core

# Stack inspection
import inspect

LOG = logging.getLogger(__name__)

routes = web.RouteTableDef()
ws_connections = aiohttp_utils.WSSender()
submodules: List[Submodule] = list()


async def spin_submodule(submodule: Submodule):
    """Main ROS loop. Spins ROS asynchronously."""
    while rclpy.ok():
        executor = MultiThreadedExecutor()
        executor.add_node(submodule._node)
        executor.spin_once(timeout_sec=0)
        await asyncio.sleep(1e-4)
    LOG.info(f"ROS loop exited for {submodule.name}")


@routes.get("/api/ws/controller")
async def handle_controller(request: web.BaseRequest) -> web.WebSocketResponse:
    # get the websocket ready to use
    ws = web.WebSocketResponse(heartbeat=3)
    await ws.prepare(request)
    ws_connections.add(ws)
    LOG.debug(f"websocket connected at ip {request.remote}")

    # when we get a message
    async for msg in ws:
        if msg.data == "close":
            LOG.info(f"websocket connection at ip {request.remote} requested close")
            await ws.close()
            break

        # The websocket is closed or has errored
        # BREAK out of the FOR and stop processing

        if msg.type == aiohttp.WSMsgType.ERROR:
            LOG.fatal(
                f"websocket connection at ip {request.remote} closed with exception {msg.data}"
            )
            break

        # Type checks
        # If the check is failed, skip this particular message
        # and CONTINUE to the next message

        if not (msg.type == aiohttp.WSMsgType.TEXT):
            LOG.error(
                f"ControllerData endpoint from {request.remote} with invalid type {msg.type}"
            )
            continue

        # if we got no data, skip the rest
        if msg.data is None:
            continue

        # Process into controller data
        websocket_cont_data = websocket_types.ControllerData
        try:
            websocket_cont_data = websocket_types.ControllerData(msg.data)
        except:
            # There was an error processing the data
            LOG.error(
                f"ControllerData endpoint from {request.remote} with invalid controller data"
            )
            # Skip ahead to the next message
            continue

        # send the data to all submodules, they will handle it if they can
        for submodule in submodules:
            submodule.handle_ws_msg(websocket_cont_data)
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
    submodules.append(Core(rclpy.create_node("core"), ws_connections))

    LOG.info("Initializing webserver routes")

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
