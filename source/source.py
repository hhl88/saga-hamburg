from abc import abstractmethod


class Source:

    @abstractmethod
    def find_articles(self, ignored_ids=None):
        """
        Get all available articles
        """
        pass
