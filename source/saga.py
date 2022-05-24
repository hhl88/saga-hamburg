import datetime
import os
import json
from model import Article
import requests as req
from bs4 import BeautifulSoup
from source import Source
from logger import log
from config import Config

logger = log.setup_logger(__name__)


class Saga(Source):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.saga.hamburg"
        self.base_apply_url = "https://tenant.immomio.com"
        self.base_detail_url = "https://gql-ps.immomio.com"
        self.path = os.path.dirname(os.path.abspath(__file__))

    def find_articles(self):

        soup = self._get_response(url=self.base_url + '/immobiliensuche', query_params={'type': "wohnungen"})
        # Get list of all pagination link
        pagination_links = self._get_list_pagination_link(soup)
        # Handle first page
        articles = self._find_all_articles_in_page(soup)

        # Handle each pagination link
        for idx, pagination_link in enumerate(pagination_links):
            soup = self._get_response(url=self.base_url + pagination_link)
            found = self._find_all_articles_in_page(soup)
            if Config.DEBUG:
                logger.debug('Page %d has %d articles' % (idx + 2, len(found)))
            articles = articles + found
        if Config.DEBUG:
            logger.debug('{0}: There are in total {1} articles'.format(self.__str__(), len(articles)))
        return articles

    def _get_response(self, url: str, query_params=None):
        """
        Request url for html response and parser via BeautifulSoup
        """
        if query_params is None:
            query_params = {}
        res = req.get(url, params=query_params)
        return BeautifulSoup(res.text, 'lxml')

    def _get_list_pagination_link(self, soup: BeautifulSoup):
        """
        Get all pagination links in "search" page excluding the first page
        """
        ul = soup.find('ul', {'class': 'pagination'})
        if ul is None:
            return []
        return [li.find('a', href=True)['href']
                for li in ul.find_all('li', {'class': None}) if li is not None]

    def _find_all_articles_in_page(self, soup: BeautifulSoup):
        """
        Get all articles in "search" page
        """
        articles = []
        for ele in soup.find_all('div', {'class': 'teaser3--listing'}):
            article = self._get_article_from_element(ele)
            self._fulfill_article_info(article)
            articles.append(article)
        return articles

    def _get_article_from_element(self, element: BeautifulSoup):
        """
       Get article from html element
       """
        a = element.find('a', href=True)
        article_info = a.find('div', {'class': 'teaser-content'})
        sub_info = article_info.find('p')

        # article id
        link = a['href']
        article_id = link[(link.rfind('/') + 1):]

        # title
        title = article_info.find('h3', {'class': 'teaser-h'}).text.strip()

        # img
        img = a.find('img')
        img_path = None
        if img is not None:
            img_path = a.find('img')['src']

        # street
        street = sub_info.find('span').text.strip()
        street = street.split(':')[1].strip()
        return Article(article_id=article_id,
                       title=title,
                       img_link="{0}{1}".format(self.base_url, img_path),
                       link="{0}/objekt/wohnungen/{1}".format(self.base_url, article_id),
                       apply_link="{0}/de/apply/{1}".format(self.base_apply_url, article_id),
                       street=street)

    def _fulfill_article_info(self, article: Article):
        """
       Get article from html element
       """
        with open(os.path.join(self.path, "query.txt"), "r+") as f:
            query = f.read()
        variables = {
            'id': article.id
        }
        r = req.post(url="{0}/tenant/graphql".format(self.base_detail_url),
                     json={'operationName': "property", 'variables': json.dumps(variables), 'query': query})
        if r.status_code == 200:
            json_data = json.loads(r.text)['data']['property']
            try:
                data = json_data['data']
            except TypeError:
                logger.error(
                    "Response doest not contain data: Article id: {0} - Response: {1}".format(article.id, json.dumps(
                        json.loads(r.text))))
                return
            if len(data['attachments']) > 0:
                article.img_link = data['attachments'][0]['url']
            # address
            address = data['address']
            article.address.plz = address['zipCode']
            article.address.city = address['city']

            # costs
            article.costs.base_rent = data['basePrice']
            article.costs.operating_cost = data['serviceCharge']
            article.costs.heating_cost = data['heatingCost']
            article.costs.total_rent = data['totalRentGross']
            article.costs.deposit = data['bailment']

            # article info
            article.living_space = data['size']
            article.no_rooms = data['rooms'] + (0.5 if data['halfRooms'] == 1 else 0)
            article.available = not json_data['rented']
            article.available_from = datetime.datetime.strptime(data['availableFrom']['dateAvailable'], '%Y-%m-%d')
            article.required_wbs = json_data['wbs'] if 'wbs' in json_data else False
            if 'floor' in data and data['floor'] is None:
                article.is_house = True
            else:
                article.is_house = False
                article.floor = data['floor']
                article.no_floor = data['numberOfFloors']

    def __str__(self):
        return "Source: Saga"
