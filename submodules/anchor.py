from submodules import Submodule
from util.aiohttp_utils import WSSender

from std_msgs import msg
from rclpy.node import Node
import logging

# Websocket data handling
from util import websocket_types


class Anchor(Submodule):
    """
    Anchor submodule for direct hardware control.
    """

    LOG = logging.getLogger(__name__)
    name = "anchor"

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        # register publishers
        self.publisher = self.node.create_publisher(
            msg.String,
            f"/{self.name}/relay",
            10,
        )

    # Process data handling from a websocket and publish it
    def handle_ws_msg(self, ws_data) -> bool:
        if (
            isinstance(ws_data, websocket_types.AnchorRelayData)
            and self.publisher.get_subscription_count() > 0
        ):
            self.publisher.publish(ws_data.to_ros())
            return True
        return False
