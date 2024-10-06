"""
Contains code for creating the rover communication topic and
creating new nodes on said topic.
"""
# Flask
from app import app
from flask import request
# ROS
from rclpy.node import Node

class SubscriberClass:
    """
    Encapsulation class for subscriber callbacks.
    Kinda extranous, but simplifies things when creating a node
    """
    def __init__(self, return_type, node_name, method_callback):
        """
        Bruh
        """
        self.return_type = return_type
        self.node_name = node_name
        self.method_callback = method_callback

class RoverCommTopic:
    """
    Rover Communication Topic class. Instantiate a copy of this to create a new node.
    """
    def __init__(self, primary_node_name: str, node_names : list, publisher : bool, subscriber : SubscriberClass):
        """
        How are you even able to read this?
        Anyway, this function does the heavy
        lifting to create your node, depending on passed in params,
        as either a listenerer or publisher.
        """
        self.primary_node_name = primary_node_name
        self.node_name = node_names
        self.publisher = publisher
        self.nnode = Node()

        if ~publisher:
            self.subscriber = subscriber

        nname = ""

        for node_name in node_names:
            # The name of the topic we're creating
            nname : str = '/' + primary_node_name + '/' + node_name

            if publisher:
                def node():
                    try:
                        return {'data': self.nnode.message_data[nname]}
                    except KeyError:
                        return {'data': 'No data was found.'}
                app.add_url_rule('/', nname, node)
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
                print(f"Subscribing to {subscriber.nodeName} with interface type {str(subscriber.returnType)} and callback {subscriber.methodCallback}")
                self.nnode.subscribers[subscriber.nodeName] = self.nnode.create_subscription(subscriber.returnType, subscriber.nodeName, subscriber.methodCallback, 0)
