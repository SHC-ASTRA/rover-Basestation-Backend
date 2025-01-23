from typing import *
from std_srvs.srv import Empty
from rclpy.node import Node, SrvTypeRequest, SrvTypeResponse
from rclpy.service import Service
from time import time
from util.aiohttp_utils import WSSender
import logging


class Submodule:
    """
    Class to handle communication between ROS and Websockets.

    :param ros_node: Node
        The ROS node to use for communication.
    """

    name: str
    _node: Node

    _ws_sender: WSSender
    _ws_map: Dict[str, Callable] = {}

    _ping_server: Service = None
    last_ping: float = 0.0

    LOG: logging.Logger

    def __init__(
        self,
        node: Node,
        name: str,
        ws_sender: WSSender,
    ):
        self.LOG.info(f"Initializing node {name}")
        self.name = name
        self._node = node
        self._ws_sender = ws_sender
        self._ping_server = self._node.create_service(
            Empty, f"/astra/{name}/ping", self.handle_ping
        )

    def handle_ws_msg(self, type_url: str, ws_msg: Any):
        """
        Handle a message from a websocket.

        :param type_url: str
            The type of the message.
        :param ws_msg: Any
            The message to handle.
        """
        for msg_type, handler in self._ws_map.items():
            if type_url == msg_type:
                handler(ws_msg)
                break

    def handle_ping(self, _: SrvTypeRequest, response: SrvTypeResponse):
        """
        Handle a ping request.

        :param request: SrvTypeRequest
            The request.
        :param response: SrvTypeResponse
            The response.
        :return: SrvTypeResponse
        """
        self.LOG.debug(f"Received ping from {self.name}")
        self.last_ping = time()
