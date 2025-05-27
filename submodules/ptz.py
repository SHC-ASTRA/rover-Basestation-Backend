from submodules import Submodule
from util.aiohttp_utils import WSSender

from ros2_interfaces_pkg import msg
from rclpy.node import Node
import logging

# Websocket data handling
from util import websocket_types


class Ptz(Submodule):
    """
    PTZ submodule for direct hardware control.
    """

    LOG = logging.getLogger(__name__)
    name = "ptz"

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        # register publishers
        self.publisher = self.node.create_publisher(
            msg.PtzControl,
            f"/{self.name}/control",
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_data) -> bool:
        if (
            isinstance(ws_data, websocket_types.PtzControlData)
            and self.publisher.get_subscription_count() > 0
        ):
            self.publisher.publish(ws_data.to_ros())
            return True
        return False
