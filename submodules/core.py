from submodules import Submodule
from interfaces_pkg.msg import ControllerState, CoreFeedback
from util.ros_utils import convert_controller
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging


class Core(Submodule):
    """
    Core rover submodule.
    """

    LOG = logging.getLogger(__name__)

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, "core", ws_sender)

        self._controller_publisher = self._node.create_publisher(
            ControllerState, "/astra/core/controller", 10
        )
        self._feedback_subscriber = self._node.create_subscription(
            CoreFeedback, "/astra/core/telemetry", self._feedback_callback, 10
        )

        for ws_msg in self._ws_map.keys():
            self.LOG.debug(f"listening for {ws_msg}")

    def _handle_controller_msg(self, ws_msg):
        if ws_msg.submodule == "core":
            self._controller_publisher.publish(convert_controller(ws_msg))

    def _feedback_callback(self, msg: CoreFeedback):
        """
        Convert CoreFeedback message to ProtoCoreFeedback and send it to the websockets.
        """
        ws_msg = {}
        ws_msg.gps_latitude = msg.gpslat
        ws_msg.gps_longitude = msg.gpslon
        ws_msg.gps_altitude = msg.gpsalt
        ws_msg.bno_gyroscope.x = msg.bnogr.x
        ws_msg.bno_gyroscope.y = msg.bnogr.y
        ws_msg.bno_gyroscope.z = msg.bnogr.z
        ws_msg.bno_accelerometer.x = msg.bnoacc.x
        ws_msg.bno_accelerometer.y = msg.bnoacc.y
        ws_msg.bno_accelerometer.z = msg.bnoacc.z
        ws_msg.orientation = msg.orient
        ws_msg.bmp_temperature = msg.bmptemp
        ws_msg.bmp_altitude = msg.bmpalt
        ws_msg.bmp_pressure = msg.bmppres

        self._ws_sender.send(ws_msg.SerializeToString())
