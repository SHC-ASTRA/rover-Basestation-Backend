import asyncio
import rclpy
import typing


class Subscription:
    message_queue = asyncio.Queue()

    def __init__(self, node, type: typing.Any, topic: str, qos: int):
        node.create_subscription(type, topic, self.callback, qos)

    async def callback(self, msg):
        await self.message_queue.put(msg)

    async def messages(self):
        while True:
            yield await self.message_queue.get()
