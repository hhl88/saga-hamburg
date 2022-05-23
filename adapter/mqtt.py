import paho.mqtt.client as mqtt
import json
from config import Config
from model import Article
from adapter import Adapter
from logger import log
from utils import is_empty

logger = log.setup_logger(__name__)


class Mqtt(Adapter):
    def __init__(self):
        self.client = mqtt.Client('app-mqtt')
        if is_empty(Config.MQTT_BROKER_URL) or is_empty(Config.MQTT_BROKER_PORT) or is_empty(
                Config.MQTT_EVENT) or is_empty(Config.MQTT_USER) or is_empty(Config.MQTT_PASS):
            raise "MQTT_BROKER_URL, MQTT_BROKER_PORT, MQTT_EVENT, MQTT_USER, MQTT_PASS must not be empty"
        if Config.DEBUG:
            logger.debug("mqtt {0}".format(json.dumps(
                {'host': Config.MQTT_BROKER_URL, 'port': Config.MQTT_BROKER_PORT, 'user': Config.MQTT_USER,
                 'pass': Config.MQTT_PASS})))
        self.client.username_pw_set(username=Config.MQTT_USER, password=Config.MQTT_PASS)

        self.client.connect(host=Config.MQTT_BROKER_URL, port=Config.MQTT_BROKER_PORT)
        self.client.loop_start()

    def send_notification(self, article: Article):
        if self.client.is_connected():
            logger.info("Publishing to mqtt: {0}".format(article.id))
            self.client.publish(Config.MQTT_EVENT,
                                json.dumps(article.dump(), ensure_ascii=False, indent=4))
            logger.info("Published to mqtt: {0}".format(article.id))
            return True
        return False

    def stop(self):
        self.client.loop_stop()
