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

job_id = "apartment_hamburg_cron_job"


class App:
    def __init__(self, comparators=None):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.done_file_path = os.path.join(self.path, 'done.json')
        self.comparators = comparators
        self.notification = Notification()
        self.sources = {}
        print(Config.ENABLE_SAGA)
        if Config.ENABLE_SAGA:
            self.sources['saga'] = Saga()

        if Config.ENABLE_IMMOBILIEN_SCOUT_24:
            self.sources['immobilienscout24'] = ImmobilienScout24()

        if len(self.sources) == 0:
            raise "No scanning sources available"

        self.scheduler = BackgroundScheduler()
        if self.scheduler is not None:
            logger.warning("Removing cronjob")
            try:
                self.scheduler.remove_job(job_id)
                logger.info("Removed cron job")
            except Exception:
                logger.info("No cron job")
        try:
            logger.info("Adding cronjob")
            self.scheduler.add_job(self.run, "cron", day_of_week="mon-sun", minute="*", id=job_id, max_instances=3)
            logger.info("Starting cronjob")
            self.scheduler.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.error("Terminating app by keyboard")
            self.stop()

    def stop(self):
        logger.warning("Stopping app")
        self.notification.stop()
        if self.scheduler is not None:
            logger.warning("Removing cronjob")
            self.scheduler.remove_job(job_id)
            self.scheduler.shutdown()

    def run(self):
        if self.comparators is None or len(self.comparators) == 0:
            return
        today = datetime.date.today()
        done = {}
        if os.path.exists(self.done_file_path):
            with open(self.done_file_path, 'r') as f:
                json_data = json.load(f)
            for source_name in json_data:
                if source_name not in done:
                    done[source_name] = {}
                for article_id in json_data[source_name]:
                    date = datetime.datetime.strptime(json_data[source_name][article_id], '%d.%m.%Y').date()
                    diff = date - today
                    if diff.days < 4:
                        done[source_name][article_id] = date.strftime("%d.%m.%Y")

        for source_name in self.sources:
            if source_name not in done:
                done[source_name] = {}
            scanning_source = self.sources[source_name]
            articles = scanning_source.find_articles(done[source_name].keys())
            for idx, article in enumerate(articles):
                if Config.DEBUG:
                    logger.debug('{0}: {1} '.format(idx + 1, json.dumps(article.dump())))
                if article.id not in done[source_name]:
                    if article.available and any(compartor.is_match(article) for compartor in self.comparators):
                        logger.info("New apartment found {0}: {1}".format(article.id, json.dumps(article.dump())))
                        self.notification.notify(data=article)
                    done[source_name][article.id] = today.strftime("%d.%m.%Y")

        with open(self.done_file_path, 'w') as f:
            json.dump(done, f, ensure_ascii=False, indent=4)
