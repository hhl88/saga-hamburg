import datetime
import os
import json
from logger import log
from config import Config
from notification import Notification
from apscheduler.schedulers.background import BackgroundScheduler
import time
from source import *

logger = log.setup_logger(__name__)


class App:
    def __init__(self, comparators=None):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.done_file_path = os.path.join(self.path, 'done.json')
        self.comparators = comparators
        self.notification = Notification()
        self.sources = []
        if Config.ENABLE_SAGA:
            self.sources.append(Saga())

        if len(self.sources) == 0:
            raise "No scanning sources available"

        scheduler = BackgroundScheduler()
        job_id = "apartment_hamburg_cron_job"
        try:
            logger.info("Adding cronjob")
            scheduler.add_job(self.run, "cron", day_of_week="mon-sun", minute="*", id=job_id)
            logger.info("Starting cronjob")
            scheduler.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.error("Terminating app by keyboard")

            logger.warning("Stopping app")
            self.stop()
            if scheduler is not None:
                logger.warning("Removing cronjob")
                scheduler.remove_job(job_id)
                scheduler.shutdown()

    def stop(self):
        self.notification.stop()

    def run(self):
        logger.info("App running")
        if self.comparators is None or len(self.comparators) == 0:
            return
        today = datetime.date.today()
        done = {}
        if os.path.exists(self.done_file_path):
            with open(self.done_file_path, 'r') as f:
                json_data = json.load(f)
            for article_id in json_data:
                date = datetime.datetime.strptime(json_data[article_id], '%d.%m.%Y').date()
                diff = date - today
                if diff.days < 4:
                    done[article_id] = date.strftime("%d.%m.%Y")

        for scanning_source in self.sources:
            logger.info("App scanning_source: {0}".format(scanning_source))
            articles = scanning_source.find_articles()

            for idx, article in enumerate(articles):
                if Config.DEBUG:
                    logger.debug('{0}: {1} '.format(idx + 1, json.dumps(article.dump())))
                if article.id not in done:
                    if article.available and any(compartor.is_match(article) for compartor in self.comparators):
                        logger.info("New apartment found {0}: {1}".format(article.id, json.dumps(article.dump())))
                        self.notification.notify(data=article)

                    done[article.id] = today.strftime("%d.%m.%Y")

        with open(self.done_file_path, 'w') as f:
            json.dump(done, f, ensure_ascii=False, indent=4)
