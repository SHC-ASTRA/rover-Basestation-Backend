#!/bin/env python

# basic stuff
from typing import *
import asyncio
import os

# http things
from aiohttp import web
import aiohttp
import aiohttp_utils

# protobuf things
from google.protobuf.any_pb2 import Any as ProtoAny
from controller_pb2 import Controller as ProtoController

# ros things
import rclpy
from std_msgs import msg as std_msgs
import interfaces_pkg.msg as astra_msgs
import ros_utils

# see: https://github.com/m2-farzan/ros2-asyncio

rclpy.init()
node = rclpy.create_node("async_subscriber")

basestation_node = rclpy.create_node("basestation")
controller_a_publisher = basestation_node.create_publisher(
    astra_msgs.ControllerState, "/astra/basestation/controller/a", 10
)
controller_b_publisher = basestation_node.create_publisher(
    astra_msgs.ControllerState, "/astra/basestation/controller/b", 10
)

node_subscription = ros_utils.AsyncSubscription(node, std_msgs.String, "/test", 10)

subscriptions = {node_subscription}


async def ros_loop():
    """Main ROS loop. Spins ROS asynchronously."""
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0)
        # quit blocking the thread so other things (like aiohttp can work)
        await asyncio.sleep(1e-4)


routes = web.RouteTableDef()
ws_connections = aiohttp_utils.WSHandler()


@routes.get("/api/ws")
async def handle_controller(request: web.BaseRequest) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=3)
    await ws.prepare(request)

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

        if raw_data.Is(ProtoController.DESCRIPTOR):
            # if it's controller data, we can unpack it into such
            controller = ProtoController()
            raw_data.Unpack(controller)

            # now we need to send it to ros
            converted = ros_utils.convert_controller(controller)
            if controller.id == 0:
                controller_a_publisher.publish(converted)
            elif controller.id == 1:
                controller_b_publisher.publish(converted)
        else:
            print("unable to parse websocket data")


# register a static file route for each of the proto files
for file in os.listdir("proto"):
    aiohttp_utils.file_route(routes, f"/api/proto/{file}", f"./proto/{file}")

app = web.Application()
app.add_routes(routes)


async def main():
    print("node started")

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port="5000")
    await site.start()


if __name__ == "__main__":
    future = asyncio.wait([ros_loop(), main()], return_when=asyncio.FIRST_EXCEPTION)
    done, _ = asyncio.get_event_loop().run_until_complete(future)
    for task in done:
        task.result()  # raises exceptions if any
