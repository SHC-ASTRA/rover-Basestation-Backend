from rclpy.node import Node

import sys

sys.path.insert(1, 'ros_msgs/install/interfaces_pkg/')
from interfaces_pkg.msg import CoreFeedback

CORE_TELEMETRY = '/astra/core/telemetry'

class TelemetryHandler():
    def __init__(self, node: Node):
        self.gps_lat = None
        self.gps_long = None
        self.gps_sat = None
        self.gyro_x = None
        self.gyro_y = None
        self.gyro_z = None
        self.acc_x = None
        self.acc_y = None
        self.acc_z = None
        self.orient = None
        self.temp = None
        self.alt = None
        self.pres = None
        
        node.create_subscription(CoreFeedback, CORE_TELEMETRY, self.handle_telemetry, 0)

    def handle_telemetry(self, msg):
        self.gps_lat = msg.gpslat
        self.gps_long = msg.gpslong
        self.gps_sat = msg.gpssat
        self.gyro_x = msg.bnogyr.x
        self.gyro_y = msg.bnogyr.y
        self.gyro_z = msg.bnogyr.z
        self.acc_x = msg.bnoacc.x
        self.acc_y = msg.bnoacc.y
        self.acc_z = msg.bnoacc.z
        self.orient = msg.orient
        self.temp = msg.bmptemp
        self.alt = msg.bmpalt
        self.pres = msg.bmppres
