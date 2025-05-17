from submodules import Submodule

from typing import *

from ros2_interfaces_pkg import msg
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

from util import websocket_types


class Arm(Submodule):
    """
    Arm rover submodule.
    """

    LOG = logging.getLogger(__name__)
    name = "arm"

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, ws_sender)

        # register publishers
        self.ik_publisher = self.node.create_publisher(
            msg.ArmIK,
            f"/{self.name}/control/ik",
            1,
        )
        self.manual_publisher = self.node.create_publisher(
            msg.ArmManual,
            f"/{self.name}/control/manual",
            1,
        )

        # register subscribers
        self.socket_feedback_subscriber = self.node.create_subscription(
            msg.SocketFeedback,
            f"/{self.name}/feedback/socket",
            self.feedback_callback,
            1,
        )
        self.bio_feedback_subscriber = self.node.create_subscription(
            msg.BioFeedback,
            f"/{self.name}/feedback",
            self.feedback_callback,
            1,
        )
        self.digit_feedback_subscriber = self.node.create_subscription(
            msg.DigitFeedback,
            f"/{self.name}/feedback/digit",
            self.feedback_callback,
            1,
        )

    def handle_ws_msg(self, ws_data: websocket_types.WebsocketData) -> bool:
        if (
            isinstance(ws_data, websocket_types.ArmIKData)
            and self.ik_publisher.get_subscription_count() > 0
        ):
            self.ik_publisher.publish(ws_data.to_ros())
            return True
        elif (
            isinstance(ws_data, websocket_types.ArmManualData)
            and self.manual_publisher.get_subscription_count() > 0
        ):
            self.manual_publisher.publish(ws_data.to_ros())
            return True
        return False

    async def feedback_callback(
        self, ros_data: Union[msg.SocketFeedback, msg.BioFeedback, msg.DigitFeedback]
    ):
        match type(ros_data):
            case msg.SocketFeedback:
                await self.ws_sender.send(
                    websocket_types.SocketFeedbackData.from_ros(ros_data).to_json()
                )
            case msg.BioFeedback:
                await self.ws_sender.send(
                    websocket_types.BioFeedbackData.from_ros(ros_data).to_json()
                )
            case msg.DigitFeedback:
                await self.ws_sender.send(
                    websocket_types.DigitFeedbackData.from_ros(ros_data).to_json()
                )
