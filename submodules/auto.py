from submodules import Submodule

from interfaces_pkg import msg
from interfaces_pkg import action
from util.aiohttp_utils import WSSender
from rclpy.node import Node
from rclpy.action import ActionClient
import logging

# Websocket data handling
from util import websocket_types


class Auto(Submodule):
    """
    Autonomous rover control submodule.
    """

    LOG = logging.getLogger(__name__)

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, "auto", ws_sender)

        self.action_server = ActionClient(self.node, action.AutoCommand)

        self.feedback_subscriber = self.node.create_subscription(
            msg.AutoFeedback,
            "/auto/feedback",
            self.feedback_callback,
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_msg: websocket_types.CoreControlData) -> bool:
        if isinstance(ws_msg, websocket_types.CoreControlData):
            self.core_publisher.publish(ws_msg.to_ros())
            return True
        return False

    async def feedback_callback(self, ros_msg: msg.AutoFeedback):
        await self.ws_sender.send(
            websocket_types.AutoFeedbackData.from_ros(ros_msg).to_json()
        )
