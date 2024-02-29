import logging
import sys
import time
import typing as t

import google.protobuf.json_format as json_format
from meshtastic import mqtt_pb2 as mqtt_pb2
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class CappedQueue:
    def __init__(self, size: int = 10):
        self.max_size = size
        self._q = list()
        self.updated_at: int = 0

    def add(self, item: t.Any) -> bool:
        as_set = set(self._q)
        q_size = len(as_set)
        if item not in self._q and q_size < self.max_size:
            self._q.append(item)
        elif item not in self._q and q_size >= self.max_size:
            self._q.pop(0)
            self._q.append(item)
        else:
            return False

        self.updated_at = int(time.time())
        return True

    @classmethod
    def create_with(cls, item: t.Any) -> "CappedQueue":
        queue = cls()
        queue.add(item)
        return queue

    def __str__(self):
        return f"<CappedQueue(size={self.max_size}) ids: {self._q}, updated at: {self.updated_at}>"


class MqttListener:
    # Time between packets when forwarding is blocked
    PACKET_BLOCK_TIME = 1800
    # Queue text packets to check duplicates
    PACKET_BLOCK_QUEUE = 10
    # Node and packets main database
    storage_msg: dict[str, t.Any] = dict()

    def __init__(self, configuration: dict):
        self.config: dict = configuration
        self.clients: dict[str, Client] = dict()

    def broadcast(self, from_client, msg, id: int):
        """#Publish to MQTT"""
        for server_name, client_instance in self.clients.items():
            if client_instance is from_client:
                continue
            topic = f"{self.config[server_name]['topic']}/{self.config[server_name]['id']}"
            logging.info("Re-broadcasted %d for %s", id, server_name)
            result = client_instance.publish(topic, msg)
            if result[0] != 0:
                logging.info("%s send status %s", server_name, result[0])

    # Check recived packet function
    def check_recived_pack(self, client, msg):
        unix_now = int(time.time())
        try:
            message = mqtt_pb2.ServiceEnvelope().FromString(msg.payload)
            asDict = json_format.MessageToDict(message)
            logging.info("Recieved: %s", asDict)

            portnum = asDict['packet']['decoded']['portnum']
            id = asDict['packet']['id']
            from_node = asDict['packet']['from']

            if from_node not in self.storage_msg.keys():
                self.storage_msg[from_node] = {portnum: CappedQueue.create_with(id)}
                self.broadcast(client, msg.payload, id)
            else:
                if portnum in self.storage_msg[from_node].keys():
                    node_messages: CappedQueue = self.storage_msg[from_node][portnum]
                    if portnum in ['TEXT_MESSAGE_APP', 'TRACEROUTE_APP', 'ROUTING_APP'] and node_messages.add(id):
                        self.broadcast(msg.payload, id)
                    elif (unix_now - node_messages.updated_at) > self.PACKET_BLOCK_TIME and node_messages.add(id):
                        self.broadcast(msg.payload, id)
                else:
                    self.storage_msg[from_node][portnum] = CappedQueue.create_with(id)
                    self.broadcast(msg.payload, id)
        except Exception as err:
            logging.error("MQTT store & forward failed: %s", err)
            return

    def on_connect(self, server_name):
        """Connection callback"""
        def wrapped(client, userdata, flags, reason_code, properties):
            client.subscribe(f"{self.config[server_name]['topic']}/#")
            logging.info("Connected to %s with result code %s", server_name, reason_code)

        return wrapped

    def on_message(self, client, userdata, msg):
        """Received MQTT message callback"""
        self.check_recived_pack(client, msg)

    def run(self):
        for server_name, client_settings in self.config.items():
            client = Client(CallbackAPIVersion.VERSION2)
            client.on_connect = self.on_connect(server_name)
            client.on_message = self.on_message
            client.username_pw_set(client_settings["username"], client_settings["password"])
            client.connect(client_settings["address"], 1883, 60)
            client.enable_logger()
            client.loop_start()
            self.clients[server_name] = client

        while True:
            for server_name, client in self.clients.items():
                if not client.is_connected():
                    logging.info("Disconnected from %s", server_name)
            time.sleep(15)
