# Main ROS2 library / bindings
import rclpy
# ROS2 node class
from rclpy.node import Node as RosNode
# ROS2 standard (topic) msgs
import std_msgs.msg
# ROS2 standard (service) srvs
import std_srvs.srv
# ROS2CLI API
import ros2topic.api # get_topic_names_and_types(node=NODE_INSTANCE)

# Interface submodule ROS2 package
import interfaces_pkg.msg

# Topic definitions
from ros_definitions import AstraTopics

# Multithreading
import threading

# Sqlite3 database
import sqlite3

# Communicates with a service hosted on the Core Rover node
# in order to confirm communication with the rover
class StatusNode(Rosnode):
    def __init__(self):       
        super().__init__('PingClient')

        # Initalize the service client
        self.ping_client = self.create_client(
            std_srvs.srv.Empty, 
            AstraTopics.CORE_PING
        )

        # Initalize the value of the service connection status
        self.service_started = False


    # Initalize the connection to the service hosted on the core
    # Must be called from a separate thread
    # otherwise acts as a blocker
    def connect_to_ping_service(self):
        print("Waiting for ping service to connect...")
        try:
            # wait_for_service returns false until a successful
            # connection to the service
            # Loop until the service is connected
            while not self.ping_client.wait_for_service(timeout_sec=10.0):
                continue
            # The loop has been exited because the service connected
            print("The ping service has connected.")
            self.service_started = True
        # In the event that there is a ROS-related error thrown
        except RCLError:
            print("Service thread did not completely connect.")

    # Send a ping
    # Must be called from a multithreaded executor,
    # otherwise acts as a blocker
    def send_ping(self):
        self.future = self.ping_client.call_async(std_srvs.srv.Empty.Request())
        rclpy.spin_until_future_complete(self, self.future, timeout_sec=5.0)
        return self.future.result()


class SubmoduleNode(RosNode):

    # The ROS2 class provides a property of publishers that is exposed
    # to the user
    # https://docs.ros2.org/latest/api/rclpy/api/node.html#rclpy.node.Node.publishers

    def __init__(self, name, database_con):
        # Call the parent ROS2 node class constructor
        # in order to 
        super().__init__(name)
        # Sqlite3 database connection in order to
        # log the topic data during the course of the
        # process
        self.db_connection = database_con

    