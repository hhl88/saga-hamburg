from abc import abstractmethod


class Source:

    @abstractmethod
    def find_articles(self):
        """
        Get all available articles
        """
        pass
