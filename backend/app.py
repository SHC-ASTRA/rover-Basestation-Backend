#!/bin/env python

# basic stuff
from typing import *
import asyncio
import traceback
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
from submodules import Submodule, Core, Arm, Auto, Bio, Antenna, Anchor, Ptz

LOG = logging.getLogger(__name__)

routes = web.RouteTableDef()
ws_connections = aiohttp_utils.WSSender()
submodules: List[Submodule] = list()

executor: MultiThreadedExecutor


async def spin_loop(executor: MultiThreadedExecutor):
    """Main ROS loop. Spins ROS asynchronously."""
    while rclpy.ok():
        executor.spin_once(timeout_sec=0)
        await asyncio.sleep(1e-4)

    LOG.info(f"ROS loop exited")


@routes.get("/api/ws")
async def handle_controller(request: web.BaseRequest) -> web.WebSocketResponse:
    # get the websocket ready to use
    ws = web.WebSocketResponse(heartbeat=3)
    await ws.prepare(request)
    ws_connections.add(ws)
    LOG.info(f"websocket connected at ip {request.remote}")

    # when we get a message
    async for msg in ws:
        LOG.debug(f"websocket message from {request.remote}: {msg.data}")

        if msg.type == aiohttp.WSMsgType.CLOSE or msg.data == "close":
            LOG.info(f"websocket connection at ip {request.remote} requested close")
            await ws.close()
            break

        # exit out if the connection errored out
        if msg.type == aiohttp.WSMsgType.ERROR:
            LOG.fatal(
                f"websocket connection at ip {request.remote} closed with exception {msg.data}"
            )
            break

        # we only accept text messages, so we can just ignore them
        if not (msg.type == aiohttp.WSMsgType.TEXT):
            LOG.error(f"{request.remote} sent message with invalid type {msg.type}")
            continue

        # if we got no data, we can ignore the message
        if msg.data is None:
            LOG.error(f"{request.remote} sent empty message")
            continue

        # process json into a websocket data object
        websocket_data: Optional[websocket_types.WebsocketData] = None
        try:
            json_data = msg.json()
            LOG.debug(f"websocket message from {request.remote} with data: {json_data}")
            data: dict = json_data["data"]
            msg_type: str = json_data["type"]
            msg_timestamp: int = json_data["timestamp"]

            # find the correct type to parse the data
            for t in websocket_types.types:
                if t.check_type(msg_type):
                    websocket_data = t.from_dict(
                        data, msg_type=msg_type, msg_timestamp=msg_timestamp
                    )
                    break
        except Exception as e:
            print(traceback.format_exc())
            # There was an error processing the data
            LOG.error(f"Websocket message from {request.remote} with invalid data")
            # Skip ahead to the next message
            continue

        if websocket_data is None:
            LOG.error(
                f"Websocket message from {request.remote} with invalid type {msg_type}"
            )
            continue

        # send the data to all submodules, they will handle it if they can
        for submodule in submodules:
            submodule.handle_ws_msg(websocket_data)
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
    executor = MultiThreadedExecutor()
    for node in [Core, Arm, Auto, Bio, Anchor, Ptz]:
        submodule = node(rclpy.create_node(f"bs_{node.name}"), ws_connections)
        submodules.append(submodule)
        executor.add_node(submodule.node)

    data_provider: Callable[[None], str | None] = None
    for submodule in submodules:
        if isinstance(submodule, Core):
            data_provider = lambda: submodule.last_sat
            break
    if data_provider is None:
        raise RuntimeError("No Core submodule found")

    antenna = Antenna(ws_connections, data_provider)
    submodules.append(antenna)

    LOG.info("Initializing webserver routes")

    loop = asyncio.get_event_loop()
    future = asyncio.wait(
        [
            spin_loop(executor),
            start_webserver(),
            ws_connections.loop(),
            antenna.send_udp_message_task(),
            antenna.listen_for_udp_messages(),
        ],
        return_when=asyncio.FIRST_EXCEPTION,
    )
    try:
        done, _ = loop.run_until_complete(future)
        for task in done:
            task.result()
    except KeyboardInterrupt:
        LOG.info("Shutting down")
