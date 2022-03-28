import logging

from apscheduler.schedulers.background import BackgroundScheduler
from comparator import SupportedComparator
from app import App
from log import log
import time

print(__name__)
logger = log.setup_logger(__name__)
log.setup_logger("apscheduler").setLevel(logging.INFO)
log.setup_logger("urllib3").setLevel(logging.WARNING)
infos = [
    SupportedComparator(min_rooms=4, max_total_rent=1300),
    SupportedComparator(min_rooms=3, max_total_rent=1300, is_house=True),
    SupportedComparator(min_rooms=3, max_total_rent=1300, is_house=False, max_floor=1, min_living_space=80),
]

if __name__ == "__main__":
    logger.info("---------------------------------START--------------------------------------")
    app = App(comparators=infos)
    scheduler = BackgroundScheduler()
    job_id = "saga_hamburg_cron_job"
    try:
        logger.info("Adding cronjob")
        scheduler.add_job(app.run, "cron", day_of_week="mon-sun", minute="*", id=job_id)
        logger.info("Starting cronjob")
        scheduler.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.error("Terminating app by keyboard")

        if app is not None and app.mqtt is not None:
            logger.warning("Stopping mqtt client")
            app.mqtt.loop_stop()
        if scheduler is not None:
            logger.warning("Removing cronjob")
            scheduler.remove_job(job_id)
            scheduler.shutdown()
