# Main ROS2 library / bindings
import rclpy
# Actions
from rclpy.action import ActionClient
# For system functionality and interaction to add directories to path
import sys

# Insert the installation direction into the local path
# so that message files can be imported
# Equivalent to sourcing the directory prior
sys.path.insert(1, 'ros_msgs/install/astra_auto_interfaces/')
from astra_auto_interfaces.action import NavigateRover

AUTO_NAME = '/astra/auto/navigate_rover'

class AutonomyClient(ActionClient):

    # Constructor
    def __init__(self, node, end_callback):
        super().__init__(
            # Reference to the Node to bind the client to
            node,
            # The type of action, as imported
            NavigateRover, 
            # Action
            AUTO_NAME
        )
        print(AUTO_NAME)
        # Callback specified by the node that created the client
        self.node_result_callback = end_callback
        # Flag to confirm that the action server has initialized and was seen
        self.actions_started = False
    
    # Send a goal to the autonomy 
    def send_autonomy_goal(self, navigation_type, lat, long, period):
        goal_msg = NavigateRover.Goal()
        goal_msg.navigate_type = navigation_type
        goal_msg.gps_lat_target = lat
        goal_msg.gps_long_target = long
        goal_msg.period = period

        if not self.actions_started:
            print("Could not handle autonomy goal sending, actions not started")
            return
        
        # Returned future to a ClientGoalHandle when the goal is adknowleged
        self.goal_future = self.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )

        self.goal_future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            print('The autonomy goal was rejected.')
            return
        
        print('The autonomy goal has been accepted by the server.')

        self.get_result_future = goal_handle.get_result_async()
        self.get_result_future.add_done_callback(self.result_callback)

    def result_callback(self, future):
        # Get the "result" (Action File) of the future
        # Get the result section of the Action File
        result = future.result().result
        # Print the final_result property from the Action File
        print(f"Autonomy RESULT: {result.final_result}")
        self.node_result_callback()
            # self.message_data[AUTO_FEEDBACK].append(f"Final autonomy result: {result.final_result}")

    def feedback_callback(self, feedback_data):
        print(f"Received autonomy FEEDBACK: {feedback_data}")
