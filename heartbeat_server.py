from rclpy.service import Service
from rclpy import Node
from std_srvs.srv import Empty

CORE_CONNECTION = '/astra/core/heartbeat'

class HeartbeatServer(Service):
    def __init__(self, node: Node):
        self.node = node
        self.node.create_service(Empty, CORE_CONNECTION, self.heartbeat_callback)

    def heartbeat_callback(self, request, response):
        print("Heard back from the rover on heartbeat")
        return response
