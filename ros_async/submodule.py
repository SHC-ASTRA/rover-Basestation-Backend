from typing import *


class Submodule:
    """
    Class to handle communication between ROS and Websockets.

    :param websocket_types: List[type]
        The types of messages that the submodule should receive from the websocket.
    :param ros_types: List[type]
        The types of messages that the submodule should receive from ROS.
    """

    def __init__(self, websocket_types: List[type], ros_types: List[type]):
        self.websocket_types = dict.fromkeys(websocket_types, None)
        self.ros_types = dict.fromkeys(ros_types, None)

    def websocket(self, msg_type: type) -> Callable:
        """
        Decorator for registering websocket message handlers.

        :param msg_type: type
            The type of message to be handled.
        :raises TypeError:
            If the msg_type is not in the websocket_types.
        :return: Callable
            A decorator that wraps the coroutine to handle the specified message type.
        """
        if msg_type not in self.websocket_types.keys():
            raise TypeError("this submodule cannot handle this type of message")

        def wrapper(coroutine):
            self.websocket_types[msg_type] = coroutine
            return coroutine

        return wrapper

    def ros(self, msg_type: type) -> Callable:
        """
        Decorator for registering ROS message handlers.

        :param msg_type: type
            The type of message to be handled.
        :raises TypeError:
            If the msg_type is not in the ros_types.
        :return: Callable
            A decorator that wraps the coroutine to handle the specified message type.
        """
        if msg_type not in self.ros_types.keys():
            raise TypeError("this submodule cannot handle this type of message")

        def wrapper(coroutine):
            self.ros_types[msg_type] = coroutine
            return coroutine

        return wrapper

    def handle_websocket(self, msg: Any) -> None:
        """
        Handles a websocket message.

        :param msg: Any
            The message to be handled.
        """

        if type(msg) not in self.websocket_types.keys():
            raise TypeError("this submodule cannot handle this type of message")
        self.websocket_types[type(msg)](msg)

    def handle_ros(self, msg: Any) -> None:
        """
        Handles a ROS message.

        :param msg: Any
            The message to be handled.
        """

        if type(msg) not in self.ros_types.keys():
            raise TypeError("this submodule cannot handle this type of message")
        self.ros_types[type(msg)](msg)
