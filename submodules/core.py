from submodules import Submodule

# ControllerState & CoreFeedback
from interfaces_pkg import msg
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

# Websocket data handling
from util import websocket_types


class Core(Submodule):
    """
    Core rover submodule.
    """

    LOG = logging.getLogger(__name__)

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, "core", ws_sender)

        self.core_publisher = self.node.create_publisher(
            msg.CoreControl,
            "/astra/core/controller",
            10,
        )
        self.feedback_subscriber = self.node.create_subscription(
            msg.CoreFeedback,
            "/astra/core/telemetry",
            self.feedback_callback,
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_msg: websocket_types.CoreControlData) -> bool:
        if isinstance(ws_msg, websocket_types.CoreControlData):
            self.core_publisher.publish(ws_msg.to_ros())
            return True
        return False

    def feedback_callback(self, ros_msg: msg.CoreFeedback):
        self.ws_sender.send(
            websocket_types.CoreFeedbackData.from_ros(ros_msg).to_json()
        )
