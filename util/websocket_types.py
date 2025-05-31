from typing import *

import logging
from abc import ABC
from ros2_interfaces_pkg import msg
from geometry_msgs.msg import Vector3
from std_msgs.msg import String
import json
import datetime
from numbers import Number

LOG = logging.getLogger(__name__)

T = TypeVar("T", bound=Type["WebsocketData"])


class SpecField:
    __slots__ = "field", "ros_property", "field_type"

    def __init__(
        self,
        json_field: str,
        ros_property: str,
        field_type: Union[type, T],
    ):
        self.field = json_field
        self.ros_property = ros_property
        self.field_type = field_type

    @classmethod
    def build_spec(cls, spec: Set[Tuple[str, str, type]]) -> Set["SpecField"]:
        return {cls(*s) for s in spec}

    @classmethod
    def build_spec_dict(cls, spec: Dict[str, type]) -> Set["SpecField"]:
        return {cls(s, s, t) for s, t in spec.items()}


class WebsocketData(ABC, Generic[T]):
    """
    Abstract class for websocket data types.
    """

    msg_type: Optional[str]
    msg_timestamp: int

    ros_type: T
    spec: Set[SpecField]
    data: Dict[str, Any] = {}

    @classmethod
    def check_type(cls, to_check: str) -> bool:
        """
        Check if the type of the data is correct.
        """
        return to_check == cls.msg_type

    def __init__(
        self,
        data: Dict[str, Any],
        *,
        msg_type: Optional[str] = None,
        msg_timestamp: Optional[int] = None,
    ):
        """
        Construct a WebsocketData from a Dict.
        """
        if msg_type:
            self.msg_type = msg_type
        if msg_timestamp:
            self.msg_timestamp = msg_timestamp
        else:
            self.msg_timestamp = int(datetime.datetime.now().timestamp() * 1000)

        # ensure all fields are present and of the correct type
        for entry in self.spec:
            # check presence
            # we can immediately error out of parsing if data is missing
            if entry.field not in data:
                raise ValueError(f"Field '{entry.field}' missing from input: {data}")

            # TODO: remove this stupid hack
            if isinstance(data[entry.field], Number) and entry.field_type == float:
                data[entry.field] = float(data[entry.field])

            # check that the type matches the spec
            # this is because the data is technically untrusted, as it comes from the client
            if not isinstance(data[entry.field], entry.field_type):
                raise TypeError(
                    f"Field '{entry.field}' is not of type {entry.field_type}: {data}"
                )

            # if it passed all of the checks, we can add it to the data dictionary
            self.data[entry.field] = data[entry.field]

        # warn for any extra fields
        for field in data.keys():
            if field not in [spec.field for spec in self.spec]:
                LOG.warning(
                    f"Field '{field}' not in spec for {self.msg_type if self.msg_type else 'unknown'}!"
                )

    @classmethod
    def from_dict(
        cls,
        dict_data: Dict[str, Any],
        *,
        msg_type: Optional[str] = None,
        msg_timestamp: Optional[int] = None,
    ) -> "WebsocketData":
        """
        Convert a Dict into a WebsocketType object.
        """

        # shallow copy is fine because we're going to be parsing nested dictionaries
        out_data = dict_data.copy()

        # convert nested dicts to WebsocketData (if the spec calls for it)
        for entry in cls.spec:
            if issubclass(entry.field_type, WebsocketData):
                out_data[entry.field] = entry.field_type.from_dict(
                    out_data[entry.field]
                )

        # initializing here does spec checking for us
        return cls(out_data, msg_type=msg_type, msg_timestamp=msg_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the data to a Dict.
        """
        out = {}

        for entry in self.spec:
            # if the data is a WebsocketData, we need to convert it to a dict
            if issubclass(entry.field_type, WebsocketData):
                out[entry.field] = self.data[entry.field].to_dict()
                continue

            # we need to check if it's nan, in which case we set it to dummy data
            if isinstance(self.data[entry.field], float) and (
                self.data[entry.field] != self.data[entry.field]
            ):
                out[entry.field] = -69420.0
            else:
                # otherwise we can just copy it over. this effectively deep copies
                out[entry.field] = self.data[entry.field]

        return out

    def to_json(self) -> str:
        """
        Convert the data to a JSON string.
        """
        return json.dumps(
            {
                "type": self.msg_type,
                "timestamp": self.msg_timestamp,
                "data": self.to_dict(),
            }
        )

    @classmethod
    def from_ros(cls, ros_data: T) -> "WebsocketData":
        """
        Convert a ROS2 message to a WebsocketType object.
        """
        to_return = {}

        # populate the data dictionary with the ROS2 message data
        for entry in cls.spec:
            to_parse = getattr(ros_data, entry.ros_property)

            # manage nested ros message types
            if isinstance(to_parse, Vector3):
                to_return[entry.field] = Vector3Data.from_ros(to_parse)
                continue

            to_return[entry.field] = to_parse
        return cls(to_return)

    def to_ros(self) -> T:
        """
        Convert the data to a ROS2 message.
        """
        # instantiate the ROS2 message type
        ros_data = self.ros_type()

        # populate the ROS2 message with the data dictionary
        for entry in self.spec:
            # different behavior for nested objects
            if issubclass(entry.field_type, WebsocketData):
                setattr(
                    ros_data,
                    entry.ros_property,
                    self.data[entry.field].to_ros(),
                )
                continue

            setattr(ros_data, entry.ros_property, self.data[entry.field])

        return ros_data


class Vector3Data(WebsocketData):
    """
    Vector3 data type.
    """

    msg_type = "vector3"
    ros_type = Vector3
    spec = SpecField.build_spec_dict(
        {
            "x": float,
            "y": float,
            "z": float,
        }
    )


class ArmIKData(WebsocketData):
    """
    Arm's Inverse Kinematics control data type.
    """

    msg_type = "/arm/control/ik"
    ros_type = msg.ArmIK
    spec = SpecField.build_spec_dict(
        {
            "movement_vector": Vector3Data,
            "gripper": int,
            "linear_actuator": int,
            "laser": int,
            "effector_roll": int,
            "effector_yaw": int,
        }
    )


class ArmManualData(WebsocketData):
    """
    Arm's Manual control data type.
    """

    msg_type = "/arm/control/manual"
    ros_type = msg.ArmManual
    spec = SpecField.build_spec_dict(
        {
            "axis0": int,
            "axis1": int,
            "axis2": int,
            "axis3": int,
            "brake": bool,
            "effector_roll": int,
            "effector_yaw": int,
            "gripper": int,
            "linear_actuator": int,
            "laser": int,
        }
    )


class ControllerStateData(WebsocketData):
    """
    Controller data type.
    """

    @classmethod
    def check_type(cls, to_check):
        return to_check.startswith(cls.msg_type)

    msg_type = "/basestation/controller"
    ros_type = msg.ControllerState
    spec = SpecField.build_spec_dict(
        {
            "lt": float,
            "rt": float,
            "lb": bool,
            "rb": bool,
            "plus": bool,
            "minus": bool,
            "ls_x": float,
            "ls_y": float,
            "rs_x": float,
            "rs_y": float,
            "a": bool,
            "b": bool,
            "x": bool,
            "y": bool,
            "d_up": bool,
            "d_down": bool,
            "d_left": bool,
            "d_right": bool,
            "home": bool,
        }
    )


class CoreControlData(WebsocketData):
    """
    Core's control data type.
    """

    msg_type = "/core/control"
    ros_type = msg.CoreControl
    spec = SpecField.build_spec_dict(
        {
            "left_stick": float,
            "right_stick": float,
            "max_speed": int,
            "brake": bool,
            "turn_to_enable": bool,
            "turn_to": float,
            "turn_to_timeout": float,
        }
    )


class AutoFeedbackData(WebsocketData):
    """
    Auto's feedback data type.
    """

    msg_type = "/auto/feedback"
    ros_type = msg.AutoFeedback
    spec = SpecField.build_spec_dict(
        {
            "mission_type": int,
            "target_lat": float,
            "target_long": float,
            "distance": float,
            "update": str,
            "current": str,
            "warn": str,
        }
    )


class CoreFeedbackData(WebsocketData):
    """
    Core feedback data type.
    """

    msg_type = "/core/feedback"
    ros_type = msg.CoreFeedback
    spec = SpecField.build_spec_dict(
        {
            # GPS Data
            "gps_lat": float,
            "gps_long": float,
            "gps_sats": int,
            "gps_alt": float,
            # BNO055 Sensor Data
            "bno_gyro": Vector3Data,
            "bno_accel": Vector3Data,
            # Rover Orientation
            "orientation": float,
            "imu_calib": int,
            # BMP Sensor Data
            "bmp_temp": float,
            "bmp_alt": float,
            "bmp_pres": float,
            # Voltage Readings
            "bat_voltage": float,
            "voltage_12": float,
            "voltage_5": float,
            "voltage_3": float,
            # REV Motor Feedback
            ## Front Left (1)
            "fl_temp": float,
            "fl_voltage": float,
            "fl_current": float,
            ## Back Left (2)
            "bl_temp": float,
            "bl_voltage": float,
            "bl_current": float,
            ## Front Right (3)
            "fr_temp": float,
            "fr_voltage": float,
            "fr_current": float,
            ## Back Right (4)
            "br_temp": float,
            "br_voltage": float,
            "br_current": float,
        }
    )


class DigitFeedbackData(WebsocketData):
    """
    Digit Feedback data type.
    """

    msg_type = "/arm/feedback/digit"
    ros_type = msg.DigitFeedback
    spec = SpecField.build_spec_dict(
        {
            "wrist_angle": float,
            "bat_voltage": float,
            "voltage_12": float,
            "voltage_5": float,
        }
    )


class BioFeedbackData(WebsocketData):
    """
    Bio Feedback data type.
    """

    msg_type = "/bio/feedback"
    ros_type = msg.BioFeedback
    spec = SpecField.build_spec_dict(
        {
            "bat_voltage": float,
            "voltage_12": float,
            "voltage_5": float,
            "drill_temp": float,
            "drill_humidity": float,
        }
    )


class SocketFeedbackData(WebsocketData):
    """
    Socket Feedback data type.
    """

    msg_type = "/arm/feedback/socket"
    ros_type = msg.SocketFeedback
    spec = SpecField.build_spec_dict(
        {
            "axis0_angle": float,
            "axis0_temp": float,
            "axis0_voltage": float,
            "axis0_current": float,
            "axis1_angle": float,
            "axis1_temp": float,
            "axis1_voltage": float,
            "axis1_current": float,
            "axis2_angle": float,
            "axis2_temp": float,
            "axis2_voltage": float,
            "axis2_current": float,
            "axis3_angle": float,
            "axis3_temp": float,
            "axis3_voltage": float,
            "axis3_current": float,
            "bat_voltage": float,
            "voltage_12": float,
            "voltage_5": float,
            "voltage_3": float,
        }
    )


class BioControlData(WebsocketData):
    """
    Bio control data type.
    """

    msg_type = "/bio/control"
    ros_type = msg.BioControl
    spec = SpecField.build_spec_dict(
        {
            "pump_id": int,
            "pump_amount": float,
            "fan_id": int,
            "fan_duration": int,
            "servo_id": int,
            "servo_state": bool,
            "bio_arm": int,
            "laser": int,
            "drill": int,
            "drill_arm": int,
            "vibration_motor": int,
        }
    )


class AnchorRelayData(WebsocketData):
    """
    Anchor control data type.
    """

    msg_type = "/anchor/relay"
    ros_type = String
    spec = SpecField.build_spec_dict({"data": str})


class PtzControlData(WebsocketData):
    """
    PTZ control data type.
    """

    msg_type = "/ptz/control"
    ros_type = msg.PtzControl
    spec = SpecField.build_spec_dict(
        {
            "control_mode": int,
            "turn_yaw": int,
            "turn_pitch": int,
            "yaw": float,
            "pitch": float,
            "axis_id": int,
            "angle": float,
            "zoom_level": float,
            "stream_type": int,
            "stream_freq": int,
            "reset": bool,
        }
    )


class AntennaResetData(WebsocketData):
    msg_type = "antenna"
    ros_type = None
    spec = SpecField.build_spec_dict(
        {
            "message": str,
        }
    )


class AntennaFeedbackData(WebsocketData):
    msg_type = "antenna/feedback"
    ros_type = None
    spec = SpecField.build_spec_dict(
        {
            "lat": float,
            "lon": float,
            "sat": int,
            "heading": float,
            "calib": int,
        }
    )


types: Set[WebsocketData] = {
    ArmIKData,
    ArmManualData,
    ControllerStateData,
    CoreControlData,
    AutoFeedbackData,
    CoreFeedbackData,
    DigitFeedbackData,
    BioFeedbackData,
    SocketFeedbackData,
    BioControlData,
    AnchorRelayData,
    PtzControlData,
    AntennaResetData,
    AntennaFeedbackData,
}
