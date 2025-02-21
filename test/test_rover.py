import rclpy
from rclpy.node import Node
from util import websocket_types
from .util import *
from ros2_interfaces_pkg import msg
from enum import Enum
import argparse


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
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class CoreAutoNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.AutoFeedback, "/core/auto", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_random_data(
            websocket_types.AutoFeedbackData.from_ros(msg.AutoFeedback())
        )
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class FaerieNode(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.FaerieFeedback, "/core/auto", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_cumulative_data(
            websocket_types.FaerieFeedbackData.from_ros(msg.FaerieFeedback())
        )
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


class NodeEnum(Enum):
    core = CoreNode
    core_auto = CoreAutoNode
    faerie = FaerieNode

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
