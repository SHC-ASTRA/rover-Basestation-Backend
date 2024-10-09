"""
Contains code for creating the rover communication topic and
creating new nodes on said topic.
"""
# Flask
from app import app
from flask import request # type: ignore
# ROS
from rclpy.node import Node # type: ignore

# For inspecting the call stack, a.k.a LITERAL MAGIC
import inspect

# Fake class for type spec on NodeList
class RoverCommNode:
	{}
"""
Dictionary of keys {/primary_node_name/node_name, RoverCommNode}
"""
NodeList : dict[str, RoverCommNode] = {}

class SubscriberClass:
	"""
	Encapsulation class for subscriber callbacks.
	"""
	def __init__(self, return_type : type, node_name : str, method_callback : function):
		self.return_type = return_type
		self.node_name = node_name
		self.method_callback = method_callback

		# The real init function 
		self.subscription = self.RoverCommNode.nnode.create_subscription(
			self.return_type,
			self.node_name,
			self.standard_feedback_callback,
			0
		)

	#This function is a parent that we call the sub-callbacks from.
	#Primary goal is simplification.
	def standard_feedback_callback(self, msg):
		print(f"Received data from {inspect.stack()[0][3]} node: {msg.data}")
		self.append_node_data(self.callback_name, msg)

	# Append ROS message data received on a topic to a message data storage dictionary
	def append_node_data(self, node, msg):
		# Check if the topic exists in the message data storage dictionary

		# # Should be unnecessary due to line 21 (self.message_data[callback_name] = [])
		# if node not in self.message_data.keys():
		# self.message_data[node] = []

		# Append the message data to the node of the message_data storage dictionary
		self.message_data[node].append(msg.data)

class RoverCommNode:
	"""
	Rover Communication Node class. Instantiate a copy of this to create a new node.
	
	Parameters:
	-
	node_directory: `str`
		The directory for the node to be placed in.
	subscriber: `SubscriberClass`
		Optional; used to pass in subscriber information.
		If not passed, defaults to publisher.
	
	They didn't want me to make it a good class, I don't care I'm doing it anyway you can't stop me
	"""
	def __init__(self, node_directory : str,  subscriber : SubscriberClass = 0):

		self.nnode = Node()

		NodeList.update(node_directory, self)

		if subscriber != 0:
			self.subscriber = subscriber
			# The one good thing about python...
			def node():
				try:
					return {'data': self.nnode.message_data[node_directory]}
				except KeyError:
					return {'data': 'No data was found.'}
			# This registers the node to the webserver for widget use
			# Analogous to @app.route(*)
			app.add_url_rule('/', node_directory, node)

			print(f"Subscribing to {node_directory} with interface type {str(subscriber.returnType)} and callback {str(subscriber.methodCallback)}")
			self.nnode.subscribers[node_directory] = subscriber.subscription
		else:
			def node():
				if request.method == 'POST':
					command = request.get_json()['command']
					print(f"Sending command {command} to " + node_directory)

					if node_directory not in self.nnode.publishers.keys():
						self.nnode.create_string_publisher(node_directory)

					self.nnode.publish_string_data(node_directory, command)

					return {'data': command}
				print("Invalid method on " + node_directory)
				return {'data': 0}
			app.add_url_rule('/', node_directory, node, methods = ['POST'])
