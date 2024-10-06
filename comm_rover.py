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

"""
Dictionary of keys {/primary_node_name/node_name, RoverCommNode}
"""
NodeList : dict = {}

class SubscriberClass:
	"""
	Encapsulation class for subscriber callbacks.
	"""
	def __init__(self, return_type : type, node_name : str, method_callback : function):
		"""
		Bruh
		"""
		self.return_type = return_type
		self.node_name = node_name
		self.method_callback = method_callback

		self.subscription = self.RoverCommNode.nnode.create_subscription(
			self.return_type,
			self.node_name,
			self.feedback_callback,
			0
		)

		
	def feedback_callback(self, msg):
		#Honestly this function is a bit extraneous but whatever. see if I care.
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
	primary_node_name: `str`
		"Directory" for the node to be placed in
	node_name: `str`
		The name for the node to have
	publisher: `bool`
		If this node is a publisher or subscriber
	subscriber: `SubscriberClass`
		Optional; used to pass in subscriber information.
		only used if publisher is False
	
	"""
	def __init__(self, primary_node_name, node_name : list, publisher : bool, subscriber : SubscriberClass = 0):
		"""
		How are you even able to read this?
		Anyway, this function does the heavy
		lifting to create your node, depending on passed in params,
		as either a listenerer or publisher.
		"""
		self.publisher = publisher
		self.nnode = Node()

		if ~publisher:
			self.subscriber = subscriber

		# The name of the topic we're creating
		nname : str = '/' + primary_node_name + '/' + node_name

		NodeList.update(nname, self)

		if ~publisher:
			def node():
				try:
					return {'data': self.nnode.message_data[nname]}
				except KeyError:
					return {'data': 'No data was found.'}
			app.add_url_rule('/', nname, node)

			print(f"Subscribing to {nname} with interface type {str(subscriber.returnType)} and callback {str(subscriber.methodCallback)}")
			self.nnode.subscribers[nname] = subscriber.subscription
		else:
			def node():
				if request.method == 'POST':
					command = request.get_json()['command']
					print(f"Sending command {command} to " + nname)

					if nname not in self.nnode.publishers.keys():
						self.nnode.create_string_publisher(nname)

					self.nnode.publish_string_data(nname, command)

					return {'data': command}
				print("Invalid method on " + nname)
				return {'data': 0}
			app.add_url_rule('/', nname, node, methods = ['POST'])
