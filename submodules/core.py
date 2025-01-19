from submodules import Submodule
from interfaces_pkg.msg import ControllerState
from generated import ProtoController
from util.ros_utils import convert_controller
import logging

LOG = logging.getLogger(__name__)


class Core(Submodule):
    """
    Core rover submodule.
    """

    def __init__(self, ws_sender):
        super().__init__("core", ws_sender)
        self._ws_map[f"type.googleapis.com/{ProtoController.DESCRIPTOR.full_name}"] = (
            self._handle_controller_msg
        )
        self._controller_publisher = self._node.create_publisher(
            ControllerState, "/astra/core/controller", 10
        )

        for ws_msg in self._ws_map.keys():
            LOG.info(f"listening for {ws_msg}")

    def _handle_controller_msg(self, ws_msg: ProtoController):
        if ws_msg.submodule == "core":
            self._controller_publisher.publish(convert_controller(ws_msg))
