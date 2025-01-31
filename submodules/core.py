from submodules import Submodule

# ControllerState & CoreFeedback
import interfaces_pkg.msg
from util.ros_utils import convert_controller
from util.aiohttp_utils import WSSender
from rclpy.node import Node
import logging

LOG = logging.getLogger(__name__)

# Websocket data handling
from util import websocket_types


class Core(Submodule):
    """
    Core rover submodule.
    """

    LOG = logging.getLogger(__name__)

    def __init__(self, node: Node, ws_sender: WSSender):
        super().__init__(node, "core", ws_sender)

        self._controller_publisher = self._node.create_publisher(
            interfaces_pkg.msg.ControllerState,
            "/astra/core/controller",
            10,
        )
        self._feedback_subscriber = self._node.create_subscription(
            interfaces_pkg.msg.CoreFeedback,
            "/astra/core/telemetry",
            self._feedback_callback,
            10,
        )

        for ws_msg in self._ws_map.keys():
            self.LOG.debug(f"listening for {ws_msg}")

    def handle_ws_msg(self, ws_data: websocket_types.WebSocketData) -> bool:
        # Only handle controller data
        if (
            type(ws_data) != websocket_types.ControllerData
            or ws_data.loaded_data["submodule"] == ""
        ):
            return False

        # Handle the controller data
        self._handle_controller_msg(ws_data)

    # Process data handling from a websocket and publish it
    def _handle_controller_msg(
        self, ws_controller: websocket_types.ControllerData
    ) -> None:
        # Process controller data
        processed_controller_data = self._proc_controller(ws_controller)
        # Publish to the ROS2 topic
        self._controller_publisher.publish(processed_controller_data)

    def _feedback_callback(self, msg: interfaces_pkg.msg.CoreFeedback) -> None:
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

    # Process websocket data into a ROS2 message
    def _proc_controller(
        self,
        ws_controller: websocket_types.ControllerData,
    ) -> interfaces_pkg.msg.ControllerState:
        LOG.debug("Processing loaded data into interfaces_pkg.msg.ControllerState")
        return interfaces_pkg.msg.ControllerState(
            # triggers and bumpers
            lt=ws_controller.loaded_data["left_trigger"],
            rt=ws_controller.loaded_data["right_trigger"],
            lb=ws_controller.loaded_data["l_bumper"],
            rb=ws_controller.loaded_data["r_bumper"],
            # plus and minus
            plus=ws_controller.loaded_data["option"],
            minus=ws_controller.loaded_data["share"],
            # left stick
            ls_x=ws_controller.loaded_data["la_vector"].x,
            ls_y=ws_controller.loaded_data["la_vector"].y,
            # right stick
            rs_x=ws_controller.loaded_data["ra_vector"].x,
            rs_y=ws_controller.loaded_data["ra_vector"].y,
            # face buttons
            a=ws_controller.loaded_data["a"],
            b=ws_controller.loaded_data["b"],
            x=ws_controller.loaded_data["x"],
            y=ws_controller.loaded_data["y"],
            # dpad
            d_up=ws_controller.loaded_data["up"],
            d_down=ws_controller.loaded_data["down"],
            d_left=ws_controller.loaded_data["left"],
            d_right=ws_controller.loaded_data["right"],
        )
