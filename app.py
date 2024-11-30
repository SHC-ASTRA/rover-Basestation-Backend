#!/bin/env python

from aiohttp import web
import aiohttp
import asyncio
import rclpy
from std_msgs.msg import String
from ros_async import Subscription
from typing import List

rclpy.init()
node = rclpy.create_node("async_subscriber")


async def ros_loop():
    while rclpy.ok():
        rclpy.spin_once(node, timeout_sec=0)
        await asyncio.sleep(1e-4)


routes = web.RouteTableDef()


@routes.get("/api/hello")
async def handle_hello(_):
    text = "Hello, world!"
    return web.Response(text=text)


@routes.get("/api/test")
async def hande_test(_):
    return web.Response("test success")


ws_queue = asyncio.Queue()


# TODO: make this send to ALL open websockets instead of just one random one
@routes.get("/api/ws")
async def handle_ws(request: web.BaseRequest):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async def producer():
        try:
            while True:
                message = await ws_queue.get()
                await ws.send_str(message)
        except asyncio.CancelledError:
            pass

    producer_task = asyncio.create_task(producer())

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    resp = msg.data + "/resp"
                    print("sending %s" % resp)
                    await ws.send_str(resp)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print("ws closed with exception %s" % ws.exception())
    finally:
        producer_task.cancel()
        await ws.close()

    print("websocket closed")

    return ws


app = web.Application()
app.add_routes(routes)


async def ros_main():
    print("node started")

    async def msg_callback(msg):
        await ws_queue.put(msg.data)
        print(msg)

    node.create_subscription(String, "/test", msg_callback, 10)
    print("listening to /test")


async def web_main():
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host="0.0.0.0", port="8080")
    await site.start()


if __name__ == "__main__":
    future = asyncio.wait([ros_main(), web_main(), ros_loop()])
    asyncio.get_event_loop().run_until_complete(future)
