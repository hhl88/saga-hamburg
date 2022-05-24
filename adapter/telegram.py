import requests
from config import Config
from model import Article
from adapter import Adapter
from logger import log
from utils import is_empty

logger = log.setup_logger(__name__)


class Telegram(Adapter):
    def __init__(self):
        super().__init__()
        if is_empty(Config.TELEGRAM_TOKEN) or is_empty(Config.TELEGRAM_CHAT_ID):
            raise "TELEGRAM_TOKEN, TELEGRAM_CHAT_ID must not be empty"
        self.token = Config.TELEGRAM_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID

    def stop(self):
        pass

    def send_notification(self, article: Article):
        caption = """
A new apartment '{0}' was found on Saga.

  -  Address: {1}
  
  -  Type: {2}
  
  -  Rooms: {3} - Size: {4} m2
  
  -  Costs: {5} Base  -  {6} Total  -  {7} Deposit
  
  -  Available: {8}
  
  -  Link: {9}
  
  - Apply link: {10}
""".format(article.title,
           article.address.__str__(),
           article.type(),
           article.no_rooms, article.living_space,
           '{:,}'.format(article.costs.base_rent), '{:,}'.format(article.costs.total_rent),
           '{:,}'.format(article.costs.deposit),
           article.available_from.strftime("%d.%m.%Y") if article.available_from is not None else None,
           article.link,
           article.apply_link)
        params = {
            'chat_id': self.chat_id,
            'photo': article.img_link,
            'caption': caption
        }
        logger.info("SENDING message")
        res = requests.post('https://api.telegram.org/bot{0}/sendPhoto'.format(self.token), params=params, timeout=5)
        if Config.DEBUG:
            logger.debug("SENT message: {0}".format(res.status_code))
        return res.status_code == 200
