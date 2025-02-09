from typing import *

import logging
from abc import ABC
from interfaces_pkg import msg
from geometry_msgs.msg import Vector3
import json
import datetime

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
                LOG.warning(f"Field '{field}' not in spec for {self.__name__}!")

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
    spec = SpecField.build_spec(
        {
            # fmt: off
            #json_field ros_prop field_type
            ("x",       "x",     float),
            ("y",       "y",     float),
            ("z",       "z",     float),
            # fmt: on
        }
    )


class ArmIKData(WebsocketData):
    """
    Arm's Inverse Kinematics control data type.
    """

    msg_type = "control:arm/socket_ik"
    ros_type = msg.ArmIK
    spec = SpecField.build_spec(
        {
            ("gripper", "gripper", int),
            ("linear_actuator", "linear_actuator", int),
            ("laser", "laser", int),
            ("effector_roll", "effector_roll", int),
            ("effector_yaw", "effector_yaw", int),
        }
    )


class ArmManualData(WebsocketData):
    """
    Arm's Manual control data type.
    """

    msg_type = "control:arm/socket_manual"
    ros_type = msg.ArmManual
    spec = SpecField.build_spec(
        {
            ("axis0", "axis0", int),
            ("axis1", "axis2", int),
            ("axis2", "axis2", int),
            ("axis3", "axis3", int),
            ("effector_roll", "effector_roll", int),
            ("effector_yaw", "effector_yaw", int),
            ("gripper", "gripper", int),
            ("linear_actuator", "linear_actuator", int),
            ("laser", "laser", int),
        }
    )


class ControllerStateData(WebsocketData):
    """
    Controller data type.
    """

    @classmethod
    def check_type(cls, to_check):
        return to_check.startswith(cls.msg_type)

    msg_type = "control:controller/"
    ros_type = msg.ControllerState
    spec = SpecField.build_spec(
        {
            # fmt: off
            #json_field       ros_prop   field_type
            ("left_trigger",  "lt",      float),
            ("right_trigger", "rt",      float),

            ("left_bumper",   "lb",      bool),
            ("right_bumper",  "rb",      bool),
            
            ("plus",          "plus",    bool),
            ("minus",         "minus",   bool),

            ("left_stick_x",  "ls_x",    float),
            ("left_stick_y",  "ls_y",    float),
            ("right_stick_x", "rs_x",    float),
            ("right_stick_y", "rs_y",    float),

            ("a",             "a",       bool),
            ("b",             "b",       bool),
            ("x",             "x",       bool),
            ("y",             "y",       bool),

            ("up",            "d_up",    bool),
            ("down",          "d_down",  bool),
            ("left",          "d_left",  bool),
            ("right",         "d_right", bool),

            ("home",          "home",    bool),
            # fmt: on
        }
    )


class CoreControlData(WebsocketData):
    """
    Core's control data type.
    """

    msg_type = "control:core/driving"
    ros_type = msg.CoreControl
    spec = SpecField.build_spec(
        {
            ("left_power", "left_stick", float),
            ("right_power", "right_stick", float),
            ("max_speed", "max_speed", int),
            ("brake", "brake", bool),
        }
    )


class AutoFeedbackData(WebsocketData):
    """
    Auto's feedback data type.
    """

    msg_type = "feedback:core/auto"
    ros_type = msg.AutoFeedback
    spec = SpecField.build_spec(
        {
            # fmt: off
            #json_field            ros_prop        field_type
            ("mission_type",       "mission_type", int),
            ("target_latitude",    "target_lat",   float),
            ("target_longitude",   "target_long",  float),
            ("remaining_distance", "distance",     float),
            ("update",             "update",       str),
            ("current_job",        "current",      str),
            ("warning",            "warn",         str),
            # fmt: on
        }
    )


class CoreFeedbackData(WebsocketData):
    """
    Core feedback data type.
    """

    msg_type = "feedback:core"
    ros_type = msg.CoreFeedback
    spec = SpecField.build_spec(
        {
            # fmt: off
            #json_field              ros_prop       field_type
            ("gps_latitude",         "gps_lat",     float),
            ("gps_longitude",        "gps_long",    float),
            ("gps_satellites",       "gps_sats",    int),
            ("gyroscope",            "bno_gyro",    Vector3Data),
            ("acceleration",         "bno_accel",   Vector3Data),
            ("orientation",          "orientation", float),
            ("temperature",          "bmp_temp",    float),
            ("altitude",             "bmp_alt",     float),
            ("atmospheric_pressure", "bmp_pres",    float),
            ("voltage_battery",      "bat_voltage", float),
            ("voltage_12v",          "voltage_12",  float),
            ("voltage_5v",           "voltage_5",   float),
            ("voltage_5v",           "voltage_5",   float),
            ("voltage_3v",           "voltage_3",   float),
            # fmt: on
        }
    )


class DigitFeedbackData(WebsocketData):
    """
    Digit Feedback data type.
    """

    msg_type = "feedback:arm/digit"
    ros_type = msg.DigitFeedback
    spec = SpecField.build_spec(
        {
            ("wrist_angle", "wrist_angle", float),
            ("voltage_battery", "bat_voltage", float),
            ("voltage_12v", "voltage_12", float),
            ("voltage_5v", "voltage_5", float),
        }
    )


class FaerieFeedbackData(WebsocketData):
    """
    Faerie Feedback data type.
    """

    msg_type = "feedback:arm/faerie"
    ros_type = msg.FaerieFeedback
    spec = SpecField.build_spec(
        {
            ("voltage_battery", "bat_voltage", float),
            ("voltage_12v", "voltage_12", float),
            ("voltage_5v", "voltage_5", float),
            ("sht_temperature", "sht_temp", float),
            ("sht_humidity", "sht_humidity", float),
            ("lux_1", "lux_1", float),
            ("lux_2", "lux_2", float),
            ("lux_3", "lux_3", float),
            ("lux_4", "lux_4", float),
            ("lux_5", "lux_5", float),
            ("lux_6", "lux_6", float),
            ("lux_7", "lux_7", float),
        }
    )


class SocketFeedbackData(WebsocketData):
    """
    Socket Feedback data type.
    """

    msg_type = "feedback:arm/socket"
    ros_type = msg.SocketFeedback
    spec = SpecField.build_spec(
        {
            # fmt: off
            #json_field           ros_prop         field_type
            ("axis0_angle",       "axis0_angle",   float),
            ("axis0_temperature", "axis0_temp",    float),
            ("axis0_voltage",     "axis0_voltage", float),
            ("axis0_current",     "axis0_current", float),

            ("axis1_angle",       "axis1_angle",   float),
            ("axis1_temperature", "axis1_temp",    float),
            ("axis1_voltage",     "axis1_voltage", float),
            ("axis1_current",     "axis1_current", float),

            ("axis2_angle",       "axis2_angle",   float),
            ("axis2_temperature", "axis2_temp",    float),
            ("axis2_voltage",     "axis2_voltage", float),
            ("axis2_current",     "axis2_current", float),

            ("axis3_angle",       "axis3_angle",   float),
            ("axis3_temperature", "axis3_temp",    float),
            ("axis3_voltage",     "axis3_voltage", float),
            ("axis3_current",     "axis3_current", float),

            ("voltage_battery",   "bat_voltage",   float),
            ("voltage_12v",       "voltage_12",    float),
            ("voltage_5v",        "voltage_5",     float),
            ("voltage_3v",        "voltage_3",     float),
            # fmt: on
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
    FaerieFeedbackData,
    SocketFeedbackData,
}
