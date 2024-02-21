import logging
import time

from bridge.worker import MqttListener, clients, mqtt_pr


if __name__ == "__main__":
    for name, config in mqtt_pr.items():
        logging.info("Creating Thread for %s", name)
        clients[name] = MqttListener(mqtt_pr[name], name)
        clients[name].start()
    while True:
        for name in mqtt_pr:
            if not clients[name].is_alive():
                logging.info("Restarting Thread for %s", name)
                clients[name] = MqttListener(mqtt_pr[name], name)
                clients[name].start()
        time.sleep(60)
