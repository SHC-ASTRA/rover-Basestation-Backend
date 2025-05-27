from submodules import Submodule

from typing import *

from ros2_interfaces_pkg import msg
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

from util import websocket_types


class Bio(Submodule):
    """
    Bio rover submodule.
    """

    LOG = logging.getLogger(__name__)
    name = "bio"

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        # register publishers
        self.publisher = self.node.create_publisher(
            msg.BioControl,
            f"/{self.name}/control",
            10,
        )

        self.feedback_subscriber = self.node.create_subscription(
            msg.BioFeedback,
            f"/{self.name}/feedback",
            self.feedback_callback,
            10,
        )

    def handle_ws_msg(self, ws_data: websocket_types.WebsocketData) -> bool:
        if (
            isinstance(ws_data, websocket_types.BioControlData)
            and self.publisher.get_subscription_count() > 0
        ):
            self.publisher.publish(ws_data.to_ros())
            return True
        return False

    async def feedback_callback(self, ros_msg: msg.BioFeedback):
        await self.ws_sender.send(
            websocket_types.BioFeedbackData.from_ros(ros_msg).to_json()
        )
