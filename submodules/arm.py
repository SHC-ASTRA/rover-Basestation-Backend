from submodules import Submodule

from typing import *

from interfaces_pkg import msg
from util.websocket_types import ArmFeedbackData, ControllerStateData
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

from util import websocket_types


class Arm(Submodule):
    """
    Arm rover submodule.
    """

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, "arm", ws_sender)

        # register publishers
        self.ik_publisher = self.node.create_publisher(
            msg.ArmIK,
            "/arm/control/ik",
            10,
        )
        self.manual_publisher = self.node.create_publisher(
            msg.ArmManual,
            "/arm/control/manual",
            10,
        )

        # register subscribers
        self.socket_feedback_subscriber = self.node.create_subscription(
            msg.SocketFeedback,
            "/arm/feedback/socket",
            self.feedback_callback,
            10,
        )
        self.faerie_feedback_subscriber = self.node.create_subscription(
            msg.FaerieFeedback,
            "/arm/feedback/faerie",
            self.feedback_callback,
            10,
        )
        self.digit_feedback_subscriber = self.node.create_subscription(
            msg.DigitFeedback,
            "/arm/feedback/digit",
            self.feedback_callback,
            10,
        )

        for ws_msg in self._ws_map.keys():
            self.LOG.debug(f"listening for {ws_msg}")

    def handle_ws_msg(self, ws_data: websocket_types.WebSocketData) -> bool:
        if isinstance(ws_data, websocket_types.ArmIKData):
            self.ik_publisher.publish(ws_data.to_ros())
            return True
        elif isinstance(ws_data, websocket_types.ArmManualData):
            self.manual_publisher.publish(ws_data.to_ros())
            return True
        return False

    def feedback_callback(
        self, ros_data: Union[msg.SocketFeedback, msg.FaerieFeedback, msg.DigitFeedback]
    ):
        match type(ros_data):
            case msg.SocketFeedback:
                self.ws_sender.send(
                    websocket_types.SocketFeedbackData.from_ros(ros_data).to_json()
                )
            case msg.FaerieFeedback:
                self.ws_sender.send(
                    websocket_types.FaerieFeedbackData.from_ros(ros_data).to_json()
                )
            case msg.DigitFeedback:
                self.ws_sender.send(
                    websocket_types.DigitFeedbackData.from_ros(ros_data).to_json()
                )
