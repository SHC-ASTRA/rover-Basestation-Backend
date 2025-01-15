import asyncio
from typing import *
from rclpy import qos, node
from . import controller_pb2 as ProtoController
import interfaces_pkg.msg as astra_msgs

T = TypeVar("T")


class AsyncSubscription(Generic[T]):
    message_queue = asyncio.Queue()

    def __init__(
        self,
        node: node.Node,
        msg_type: T,
        topic: str,
        qos_profile: Union[qos.QoSProfile, int],
    ):
        self._subscription = node.create_subscription(
            msg_type, topic, self._callback, qos_profile
        )
        self.msg_type: T = msg_type
        self.topic = topic
        self.qos_profile = qos_profile

    def destroy(self):
        self._subscription.destroy()

    async def _callback(self, msg: T):
        await self.message_queue.put(msg)

    async def messages(self):
        while True:
            yield await self.message_queue.get()


def convert_controller(data: ProtoController) -> astra_msgs.ControllerState:
    return astra_msgs.ControllerState(
        # triggers and bumpers
        lt=data.left_trigger,
        rt=data.right_trigger,
        lb=data.left_bumper,
        rb=data.right_bumper,
        # plus and minus
        plus=data.option,
        minus=data.share,
        # left stick
        ls_x=data.left_stick.x,
        ls_y=data.left_stick.y,
        # right stick
        rs_x=data.right_stick.x,
        rs_y=data.right_stick.y,
        # face buttons
        a=data.a,
        b=data.b,
        x=data.x,
        y=data.y,
        # dpad
        d_up=data.up,
        d_down=data.down,
        d_left=data.left,
        d_right=data.right,
    )
