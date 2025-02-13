import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from util.websocket_types import CoreFeedbackData
from test import generate_random_data
from ros2_interfaces_pkg import msg


class TestPublisher(Node):
    def __init__(self):
        super().__init__("test_publisher")
        self.publisher_ = self.create_publisher(msg.CoreFeedback, "/core/feedback", 10)
        timer_period = 1.0  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        to_send = generate_random_data(CoreFeedbackData.from_ros(msg.CoreFeedback()))
        self.publisher_.publish(to_send.to_ros())
        self.get_logger().info('Publishing: "%s"' % to_send.data)


async def main(args=None):
    rclpy.init(args=args)
    node = TestPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
