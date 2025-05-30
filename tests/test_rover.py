import rclpy
from rclpy.node import Node
from util import websocket_types
from .util import *
from ros2_interfaces_pkg import msg
from enum import Enum
import argparse
from asyncio import run
import random

"""
This script generates random ROS2 messages and publishes them to a ROS2 topic.
"""


class BrokenBioNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.BioFeedback, "/bio/feedback", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_cumulative_data(
            websocket_types.BioFeedbackData.from_ros(msg.BioFeedback()),
            (0, 1),
            (0, 255),
        )
        # simulate a broken node by setting the sht data to NaN
        to_send.data["drill_temp"] = float("nan")
        to_send.data["drill_humidity"] = float("nan")
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class CoreNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.CoreFeedback, "/core/feedback", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_cumulative_data(
            websocket_types.CoreFeedbackData.from_ros(msg.CoreFeedback())
        )
        to_send.data["gps_lat"] = 38.0
        to_send.data["gps_long"] = 110.0
        to_send.data["orientation"] = random.uniform(-180, 180)

        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class AutoNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.AutoFeedback, "/auto/feedback", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_random_data(
            websocket_types.AutoFeedbackData.from_ros(msg.AutoFeedback())
        )
        # get a random coord near where the mars desert research station is
        to_send.data["target_lat"] = random.uniform(38, 39)
        to_send.data["target_long"] = random.uniform(-110, -111)
        to_send.data["orientation"] = random.uniform(-180, 180)

        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class BioNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.BioFeedback, "/bio/feedback", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_cumulative_data(
            websocket_types.BioFeedbackData.from_ros(msg.BioFeedback()),
            (0, 1),
            (0, 255),
        )
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class SocketNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(
            msg.SocketFeedback, "/arm/feedback/socket", 10
        )
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_cumulative_data(
            websocket_types.SocketFeedbackData.from_ros(msg.SocketFeedback()),
            (0, 1),
            (3, 15),
        )
        to_send.data["axis0_angle"] = 0.0
        to_send.data["axis0_temp"] = generate_random_temp()
        to_send.data["axis1_angle"] = generate_random_angle()
        to_send.data["axis1_temp"] = generate_random_temp()
        to_send.data["axis2_angle"] = generate_random_angle()
        to_send.data["axis2_temp"] = generate_random_temp()
        to_send.data["axis3_angle"] = generate_random_angle()
        to_send.data["axis3_temp"] = generate_random_temp()

        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class NodeEnum(Enum):
    brokenbio = BrokenBioNode
    core = CoreNode
    auto = AutoNode
    bio = BioNode
    socket = SocketNode

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s: str):
        try:
            return NodeEnum[s]
        except KeyError:
            raise ValueError(s)


async def main(args=None):

    # determine which node to use from args
    parser = argparse.ArgumentParser(
        description="Generate random data and publish to ROS2 topic"
    )
    parser.add_argument(
        "node",
        type=NodeEnum.from_string,
        choices=list(NodeEnum),
        help="The node to run",
    )

    # launch the node
    rclpy.init()
    args = parser.parse_args(args=args)
    node = args.node.value()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    run(main())
