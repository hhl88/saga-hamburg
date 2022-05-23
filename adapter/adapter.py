from abc import abstractmethod
from model import Article


class Adapter:
    @abstractmethod
    def send_notification(self, article: Article):
        pass

    @abstractmethod
    def stop(self):
        pass
