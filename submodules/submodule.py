from typing import *
from std_srvs.srv import Empty
from rclpy.node import Node, SrvTypeRequest, SrvTypeResponse
from rclpy.service import Service
from time import time
from util.aiohttp_utils import WSSender
import logging
from abc import ABC, abstractmethod
from util.websocket_types import WebsocketData


class Submodule(ABC):
    """
    Class to handle communication between ROS and Websockets.

    :param ros_node: Node
        The ROS node to use for communication.
    """

    name: str
    node: Node | None

    ws_sender: WSSender

    _ping_server: Service
    last_ping: float = 0.0

    LOG: logging.Logger

    def __init__(
        self,
        node: Node | None,
        ws_sender: WSSender,
    ):
        self.LOG = logging.getLogger(__name__)

        self.node = node
        self.ws_sender = ws_sender
        if node:
            self.LOG.info(f"Initializing node {self.name}")
            self._ping_server = self.node.create_service(
                Empty, f"/{self.name}/ping", self.handle_ping
            )

    def handle_ping(
        self, _: SrvTypeRequest, response: SrvTypeResponse
    ) -> SrvTypeResponse:
        """
        Handle a ping request.

        TODO: ensure this actually works

        :param request: SrvTypeRequest
            The request.
        :param response: SrvTypeResponse
            The response.
        :return: SrvTypeResponse
        """
        self.LOG.debug(f"Received ping from {self.name}")
        self.last_ping = time()

        return response

    @abstractmethod
    def handle_ws_msg(self, ws_data: WebsocketData) -> bool: ...
