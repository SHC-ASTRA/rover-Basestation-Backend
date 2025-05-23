from submodules import Submodule

from ros2_interfaces_pkg import msg
from ros2_interfaces_pkg import action
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

# Websocket data handling
from util import websocket_types


class Auto(Submodule):
    """
    Autonomous rover control submodule.
    """

    LOG = logging.getLogger(__name__)
    name = "auto"

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        self.auto_command = self.node.create_publisher(
            msg.AutoFeedback,
            f"/{self.name}/control",
            10,
        )

        self.feedback_subscriber = self.node.create_subscription(
            msg.AutoFeedback,
            f"/{self.name}/feedback",
            self.feedback_callback,
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_msg: websocket_types.AutoCommandData) -> bool:
        if isinstance(ws_msg, websocket_types.AutoCommandData):
            self.auto_command.publish(ws_msg.to_ros())
            return True
        return False

    async def feedback_callback(self, ros_msg: msg.AutoFeedback):
        await self.ws_sender.send(
            websocket_types.AutoFeedbackData.from_ros(ros_msg).to_json()
        )
