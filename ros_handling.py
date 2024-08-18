# Main ROS2 library / bindings
import rclpy
# ROS2 node class
from rclpy.node import Node
# ROS2 standard (topic) messages
import std_msgs.msg
# ROS2 sensor (topic) messages
import sensor_msgs.msg
# ROS2 standard (service) srvs
import std_srvs.srv
# OpenCV
from cv_bridge import CvBridge
# ROS2CLI API
import ros2topic.api # get_topic_names_and_types(node=NODE_INSTANCE)

# Error handling for pinging
from rclpy._rclpy_pybind11 import RCLError
# Multithreading
import threading
# For system functionality and interaction to add directories to path
import sys
# For inspecting the call stack
import inspect

# Autonomy
from autonomy_handling import AutonomyClient

# Telemetry from Core
from core_telemetry_handler import TelemetryHandler

# Insert the installation direction into the local path
# so that message files can be imported
# Equivalent to sourcing the directory prior
sys.path.insert(1, 'ros_msgs/install/interfaces_pkg/')
# Interfaces Package
    # FaerieTelemetry
import interfaces_pkg.msg

# sys.path.insert(1, 'ros_msgs/install/astra_auto_interfaces/')
# from astra_auto_interfaces.action import NavigateRover


CHATTER_TOPIC = "/topic"
CORE_FEEDBACK = "/astra/core/feedback"
CORE_CONTROL = "/astra/core/control"
CORE_PING = "/astra/core/ping"

ARM_FEEDBACK = "/astra/arm/feedback"
ARM_CONTROL = '/astra/arm/control'
ARM_COMMAND = '/astra/arm/command'

BIO_FEEDBACK = '/astra/bio/feedback'
BIO_CONTROL = '/astra/bio/control'
FAERIE_FEEDBACK = '/astra/arm/bio/feedback'
FAERIE_CONTROL = '/astra/arm/bio/control'

AUTO_FEEDBACK = '/astra/auto/feedback'

class RosNode(Node):

    # Dictionary of Publishers
    publishers = {}
    # Dictionary of Subscribers
    subscribers = {}
    
    # Dictionary of Image Subscribers and other data

    # This is cleaned as disconnects are processed
    # Stores who is listening to these subscribers
    image_subscribers = {}
    # ROS Topic names are used as the key for another dictionary
    # that stores the callback, sockets who have requested the subscriber,
    # and the ROS instance of the subscriber 
    """
    {
        topic: {
            callback: subscriber_callback
            socket_ids: [ids of sockets using this callback]
            subscriber: subscriber_instance
        }
    }"""

    def __init__(self):
        super().__init__('astra_base')
        
        def autonomy_result_callback():
            print("Finished and received callback")
            pass
        # Initalize the autonomy client
        # self.autonomy_client = AutonomyClient(self, autonomy_result_callback)

        self.telemetry_handler = TelemetryHandler(self)

        # Services
        self.ping_client = self.create_client(std_srvs.srv.Empty, CORE_PING)
        self.services_started = False

        # Autonomy Handling

        threading.Thread(target=self.connect_to_ping_service).start()
        threading.Thread(target=self.connect_to_autonomy_action).start()

        # Used to store feedback topic message data
        self.message_data = {}

        # OpenCV Bridge
        self.opencv_bridge = CvBridge()

        ACTIVE_SUBSCRIBERS = [
            (std_msgs.msg.String, CORE_FEEDBACK, self.core_feedback_callback),
            (std_msgs.msg.String, ARM_FEEDBACK, self.arm_feedback_callback),
            (std_msgs.msg.String,  BIO_FEEDBACK, self.bio_feedback_callback),
            (interfaces_pkg.msg.FaerieTelemetry, FAERIE_FEEDBACK, self.faerie_feedback_callback),
            (std_msgs.msg.String, AUTO_FEEDBACK, self.autonomy_feedback_callback)
        ]

        ## Feedback Subscribers
        for [interface, topic_name, callback] in ACTIVE_SUBSCRIBERS:
            print(f"Subscribing to {topic_name} with interface type {str(interface)} and callback {callback.__name__}")
            self.subscribers[topic_name] = self.create_subscription(interface, topic_name, callback, 0)

    ## Subscriber Callbacks

    # Primary ROS topic feedback topics
    # String-based topics
    # They use of a dictionary of topic names as keys, storing the message data in arrays 

    def core_feedback_callback(self, msg):
        print(f"Received data from {inspect.stack()[0][3]} topic: {msg.data}")
        self.append_topic_data(CORE_FEEDBACK, msg)

    def bio_feedback_callback(self, msg):
        print(f"Received data from {inspect.stack()[0][3]} feedback topic: {msg.data}")
        self.append_topic_data(BIO_FEEDBACK, msg)

    def arm_feedback_callback(self, msg):
        print(f"Received data from {inspect.stack()[0][3]} feedback topic: {msg.data}")
        self.append_topic_data(ARM_FEEDBACK, msg)

    def faerie_feedback_callback(self, msg):
        print(f"Received data from {inspect.stack()[0][3]} feedback topic: {msg.humidity}, {msg.temperature}")
        # Check if key is in dictionary
        try:
            self.message_data[FAERIE_FEEDBACK]
        except KeyError:
            self.message_data[FAERIE_FEEDBACK] = []
        # Append to the key's list
        self.message_data[FAERIE_FEEDBACK].append(msg)

    def autonomy_feedback_callback(self, msg):
        print(f"Received data from {inspect.stack()[0][3]} feedback topic: {msg.data}")
        self.append_topic_data(AUTO_FEEDBACK, msg)

    
    # Send a ping
    def send_ping(self):
        self.future = self.ping_client.call_async(std_srvs.srv.Empty.Request())
        rclpy.spin_until_future_complete(self, self.future, timeout_sec=5.0)
        return self.future.result()

    ## Helper Functions
    # Connect to all services
    def connect_to_ping_service(self):
        print("Waiting for ping service to connect...")
        try:
            while not self.ping_client.wait_for_service(timeout_sec=10.0):
                continue
            print("The ping service has connected.")
            self.services_started = True
        except RCLError:
            print("Service thread did not completely connect.")

    def connect_to_autonomy_action(self):
        print("Waiting for autonomy action to connect...")
        # try:
        #     while not self.autonomy_client.wait_for_server(timeout_sec=5.0):
        #         print("CANNOT CONNECT TO AUTONOMY SERVICE")
        #         continue
        #     print("All action servers have connected.")
        #     self.autonomy_client.actions_started = True
        # except RCLError:
        #     print("Action thread did not completely connect.")


    # Create a ROS publisher of String type
    def create_string_publisher(self, topic_name):
        self.publishers[topic_name] = self.create_publisher(
            std_msgs.msg.String,
            topic_name,
            0
        )
        return self.publishers[topic_name]

    # Publish data to a String topic
    def publish_string_data(self, topic_name, str_data):
        ros_msg = std_msgs.msg.String()
        ros_msg.data = str_data
        self.publishers[topic_name].publish(ros_msg)
        print(f"Publishing data to \"{topic_name}\": {str_data}")

    # Create a subscriber with a given callback
    def create_string_subscriber(self, topic_name: str, callback):
        self.create_subscription(
            std_msgs.msg.String,
            topic_name,
            callback,
            0
        )

    ## Make use of the ROS2 CLI API to perform some actions
    # The command interface is implemented almost solely (97% in Python on the repository), making 
    # it possible to use the exposed commands to not reimplement functionality provided
    # GITHUB: https://github.com/ros2/ros2cli/tree/humble

    def get_topics(self):
        return ros2topic.api.get_topic_names_and_types(node=self)

    # Append ROS message data received on a topic to a message data storage dictionary
    def append_topic_data(self, topic, msg):
        # Check if the topic exists in the message data storage dictionary
        if topic not in self.message_data.keys():
            self.message_data[topic] = []
        # Append the message data to the topic of the message_data storage dictionary
        self.message_data[topic].append(msg.data)

    

    # Health Packet Service

    def initalize_health_packets(self, service_callback):
        self.core_health_service = self.create_service(
            std_srvs.srv.Trigger,
            '/astra/core/health',
            service_callback
        )
        self.arm_health_service = self.create_service(
            std_srvs.srv.Trigger,
            '/astra/arm/health',
            service_callback
        )

    # Subscribe to a COMPRESSED IMAGE topic
    # Called when a camera (widget) is initalized as well as when
    # a camera widget changes the focused camera
    def create_image_subscriber(self, subscriber_callback, image_topic, socket_id):
        if image_topic in self.image_subscribers.keys():
            # If the socket exists, update this list of socket ids that are connected
            self.image_subscribers[image_topic]["socket_ids"].append(socket_id)
        else:
            # Create an image subscriber for the image topic if the subscriber does not already exist
            self.image_subscribers[image_topic] = {
                # Callback should be passed by the caller
                'callback': subscriber_callback,
                'socket_ids': [socket_id],
                # The subscriber is created if it doesn't already exist
                'subscriber': self.create_subscription(
                    sensor_msgs.msg.CompressedImage,
                    image_topic,
                    subscriber_callback,
                    10
                )
            }

    # Handle when a widget topic is modified on the front end
    # Called each time to ensure that subscribers are not left hanging until the socket disconnects
    def handle_connection_change(self, socket_id, old_topic, new_topic):
        # Handle when the widget changes the focused camera
        print(f"Handling socket {socket_id} swapping from \"{old_topic}\" to \"{new_topic}\"")
        # If this socket is the only one subscribed to this video topic
        if len(self.image_subscribers[old_topic]["socket_ids"]) == 1:
            # Kill the subscriber
            self.kill_image_subscriber(old_topic)
        # If there are multiple sockets subscribed to this video topic
        else:
            # Remove this socket specifically from the list
            self.image_subscribers[old_topic]["socket_ids"].remove(socket_id)

    # Handle when a widget topic is killed on the front end
    def handle_connection_end(self, socket_id, old_topic):
        if len(self.image_subscribers[old_topic]["socket_ids"]) == 1:
            # Kill the subscriber
            self.kill_image_subscriber(old_topic);
        # If there are multiple sockets subscribed to this video topic
        else:
            # Remove this socket specifically from the list
            self.image_subscribers[old_topic]["socket_ids"].remove(socket_id);

    # Handle complete socket disconnections
    def handle_disconnect(self, socket_id):
        # Handle disconnections by removing the connection from subscriptions
        # with more than one user, and delete subscriptions
        # where the connection was the only user
        print(f"Handling disconnect for socket: {socket_id}")
        for topic_name in list(self.image_subscribers.keys()):
            # If this socket uses this subscriber
            if socket_id in self.image_subscribers[topic_name]["socket_ids"]:
                # Kill the subscription if this is the last socket
                # that is making use of this subscriber
                if len(self.image_subscribers[topic_name]["socket_ids"]) == 1:
                    self.kill_image_subscriber(topic_name)
                # If there are multiple sockets using this subscriber,
                # remove the socket's id from the list
                else:
                    self.image_subscribers[topic_name]["socket_ids"].remove(socket_id)

    # If all of the request makers are gone, handle deleting
    def kill_image_subscriber(self, image_topic):
        # Destroy the ROS subscription to conserve resources
        self.destroy_subscription(self.image_subscribers[image_topic]['subscriber'])
        # Remove the key entry for the subscription
        # so that it may be recreated in the future
        del self.image_subscribers[image_topic]

# Thread worker that spins the node
def ros2_thread(node): 
    print('Entering Ros2 thread')
    rclpy.spin(node)
    print('Leaving Ros2 thread')