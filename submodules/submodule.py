from typing import *
import rclpy
from util.aiohttp_utils import WSSender


class Submodule:
    """
    Class to handle communication between ROS and Websockets.

    :param ros_node: Node
        The ROS node to use for communication.
    """

    def __init__(self, name: str, ws_sender: WSSender):
        self.name = name
        self._node = rclpy.create_node(name)
        self._ws_sender = ws_sender
        self._ws_map: Dict[str, Callable] = {}

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

    async def spin_once(self, timeout_sec: float = 0):
        """
        Spin the ROS node once.

        :param timeout_sec: float
            The timeout for the spin.
        """
        rclpy.spin_once(self._node, timeout_sec=timeout_sec)
