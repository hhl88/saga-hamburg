import logging

from model.comparator import SupportedComparator
from app import App
from logger.logger import log

logger = log.setup_logger(__name__)
log.setup_logger("apscheduler").setLevel(logging.INFO)
log.setup_logger("urllib3").setLevel(logging.WARNING)
infos = [
    SupportedComparator(min_rooms=4,  min_living_space=80),
]

if __name__ == "__main__":
    logger.info("---------------------------------START--------------------------------------")
    app = App(comparators=infos)
