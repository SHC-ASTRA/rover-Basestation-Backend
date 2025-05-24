from submodules import Submodule

# ControllerState & CoreFeedback
from ros2_interfaces_pkg import msg
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
    name = "core"

    last_sat: str | None = None

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        self.core_publisher = self.node.create_publisher(
            msg.CoreControl,
            f"/{self.name}/control",
            10,
        )
        self.feedback_subscriber = self.node.create_subscription(
            msg.CoreFeedback,
            f"/{self.name}/feedback",
            self.feedback_callback,
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_msg: websocket_types.CoreControlData) -> bool:
        if (
            isinstance(ws_msg, websocket_types.CoreControlData)
            and self.core_publisher.get_subscription_count() > 0
        ):
            self.core_publisher.publish(ws_msg.to_ros())
            return True
        return False

    async def feedback_callback(self, ros_msg: msg.CoreFeedback):
        msg: websocket_types.CoreFeedbackData = (
            websocket_types.CoreFeedbackData.from_ros(ros_msg)
        )
        gps_lat = msg.data["gps_lat"]
        gps_long = msg.data["gps_long"]
        self.last_sat = f"{gps_lat:.7f},{gps_long:.7f}\n"
        await self.ws_sender.send(msg.to_json())
