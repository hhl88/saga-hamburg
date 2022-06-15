import threading, queue
from model import Article
from adapter import *
from config import Config
from logger import log

logger = log.setup_logger(__name__)


class Notification(threading.Thread):
    def __init__(self):
        logger.info("Init notification")
        if Config.NOTIFICATION_TYPE == 'mqtt':
            self.adapter: Adapter = Mqtt()
        else:
            self.adapter: Adapter = Telegram()
        self.queue = queue.PriorityQueue()
        super().__init__()
        if Config.DEBUG:
            logger.debug("Queue joining")
        self.start()
        self.queue.join()
        if Config.DEBUG:
            logger.debug("Queue joined")

    def run(self):
        if Config.DEBUG:
            logger.debug("Notification run")

        while True:
            try:
                _, article = self.queue.get(timeout=150)
                if Config.DEBUG:
                    logger.debug("Queue article article {0} : {1}".format(article.id, article.title))
                res = self.adapter.send_notification(article=article)
                if Config.DEBUG:
                    logger.debug("Queue OK {0} article article {1} : {2}".format(res, article.id, article.title))
                if res is True:
                    if Config.DEBUG:
                        logger.debug("Notify article succeeded {0} : {1}".format(article.id, article.title))
                    self.queue.task_done()
                else:
                    self.queue.put((1, article))

            except queue.Empty:
                if Config.DEBUG:
                    logger.debug("Queue is empty")

    def notify(self, data: Article):
        if data is None:
            raise "Article is not defined"
        if Config.DEBUG:
            logger.debug("Notifying article {0} : {1} to queue".format(data.id, data.title))

        res = self.adapter.send_notification(data)
        if res is False:
            if Config.DEBUG:
                logger.debug("Notify failed, put article {0} : {1} to queue".format(data.id, data.title))
            self.queue.put((2, data))

    def stop(self):
        self.queue.empty()
        self.adapter.stop()
