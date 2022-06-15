import datetime
import os
import re
from model import Article
import requests as req
from bs4 import BeautifulSoup
from source import Source
from logger import log
from config import Config

logger = log.setup_logger(__name__)

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'referer': 'https://www.immobilienscout24.de/Suche/de/hamburg/hamburg/wohnung-mieten?exclusioncriteria=swapflat&pricetype=rentpermonth',
}
session = req.Session()
session.cookies.set('reese84', Config.IMMOBILIEN_SCOUT_24_REESE_84_API_KEY)
session.headers.update(headers)


class ImmobilienScout24(Source):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.immobilienscout24.de"
        self.base_apply_url = "https://www.immobilienscout24.de"
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.query_params = {'exclusioncriteria': "swapflat", "pricetype": "rentpermonth", "numberofrooms": "3.0-",
                             "livingspace": "60.0-", "price": "-1500.0"}

    def find_articles(self, ignored_ids: list = None):

        soup = self._get_response(url=self.base_url + '/Suche/de/hamburg/hamburg/wohnung-mieten',
                                  query_params=self.query_params)
        # Get list of all pagination link
        pagination_numbers = self._get_list_pagination_number(soup)
        # Handle first page
        articles = self._find_all_articles_in_page(soup)

        # Handle each pagination link
        for idx, pagination_number in enumerate(pagination_numbers):
            new_query_params = self.query_params.copy()
            new_query_params['pagenumber'] = pagination_number
            soup = self._get_response(url=self.base_url + '/Suche/de/hamburg/hamburg/wohnung-mieten',
                                      query_params=new_query_params)
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
        res = session.get(url, params=query_params)
        return BeautifulSoup(res.text, 'lxml')

    def _get_list_pagination_number(self, soup: BeautifulSoup):
        """
        Get all pagination links in "search" page excluding the first page
        """
        ul = soup.find('ul', {'class': 'reactPagination'})
        if ul is None:
            return []
        numbers = [li.find('a').text.strip()
                   for li in ul.find_all('li', {'class': 'p-items'}) if li is not None and len(li["class"]) == 1]
        if len(numbers) > 2:
            numbers = list(range(int(numbers[0]), int(numbers[-1]) + 1))
        return numbers

    def _find_all_articles_in_page(self, soup: BeautifulSoup, ignored_ids: list = None):
        """
        Get all articles in "search" page
        """
        articles = []
        ul = soup.find('ul', {'id': 'resultListItems'})
        if ul is None:
            return []
        for ele in ul.find_all('li', {'class': 'result-list__listing'}, recursive=False):
            article = self._get_article_from_element(ele)
            if 'html' in article.id:
                continue
            if ignored_ids is not None and article.id in ignored_ids:
                continue
            self._fulfill_article_info(article)
            articles.append(article)
        return articles

    def _get_article_from_element(self, element: BeautifulSoup):
        """
       Get article from html element
       """
        article = element.find('article', {'class': 'result-list-entry'})
        article_info = article.find('div', {'class': 'result-list-entry__data'})

        # article id
        a = article_info.find('a', href=True)
        link = a['href']
        article_id = link[(link.rfind('/') + 1):]

        # title
        h5 = a.find('h5', {'class': 'result-list-entry__brand-title'})
        title = ''
        if h5 is not None:
            for span in h5.find_all('span'):
                span.decompose()
            title = h5.text.strip()

        # img
        gallery = article.find('div', {'class': 'gallery-responsive'})
        gallery_info = gallery.find('div', {'class': 'gallery-container'})
        img_path = None
        if gallery_info is not None:
            a = gallery_info.find('a', href=True)
            img = a.find('img')
            if img is not None:
                if 'src' in img:
                    img_path = img['src']
                elif 'data-lazy-src' in img:
                    img_path = img['data-lazy-src']

        # street
        street_info = article_info.find('div', {'class': 'result-list-entry__address'})
        street = None
        if street_info is not None:
            street = street_info.text.strip()

        sub_info = article_info.find('div', {'class': 'result-list-entry__criteria'})
        sub_info = sub_info.find('a', href=True)
        area = None
        rooms = None
        for idx, dl in enumerate(sub_info.find_all('dl')):
            if idx == 0:
                price = dl.find('dd').text.strip()
                price = float(price[:price.find(' ')].replace('.', '').replace(',', '.'))
            elif idx == 1:
                area = dl.find('dd').text.strip()
                area = float(area[:area.find(' ')].replace('.', '').replace(',', '.'))
            elif idx == 2:
                rooms = dl.find('dd').find('span', {'class': 'onlyLarge'})
                if rooms is not None:
                    rooms = float(rooms.text.strip().replace(',', '.'))

        return Article(article_id=article_id,
                       title=title,
                       img_link=img_path,
                       link="{0}/expose/{1}".format(self.base_url, article_id),
                       apply_link="{0}/expose/{1}".format(self.base_apply_url, article_id),
                       living_space=area,
                       no_rooms=rooms,
                       street=street)

    def _fulfill_article_info(self, article: Article):
        """
       Get article from html element
       """
        soup = self._get_response(url=article.link)
        if soup is not None:

            gallery = soup.find('div', {'class': 'first-gallery-picture-container'})
            if gallery is not None:
                article.img_link = gallery.find('img')['src']
            # address
            address = soup.find('div', {'class': 'address-with-map-link'})
            if address is not None:
                zip_and_city = address.find('span', {'class': 'zip-region-and-country'})
                if zip_and_city is not None:
                    zip_and_city = zip_and_city.text.strip()
                    article.address.plz = zip_and_city[:zip_and_city.find(' ')]
                    article.address.city = zip_and_city[zip_and_city.find(' '):]

            info = soup.find('div', {'class': 'criteria-group--spacing'})
            if info is not None:
                sub_info = info.find('div', {'class': 'criteriagroup'}, recursive=False)
                if sub_info is not None:
                    for dl in sub_info.find_all('dl', recursive=False):
                        if 'Bezugsfrei ab' in dl.find('dt').text.strip():
                            date = dl.find('dd').text.strip()
                            if re.match(r'^\d{2}\.\d{2}\.\d{4}$', date):
                                article.available_from = datetime.datetime.strptime(date, '%d.%m.%Y')
                        elif 'Etage' in dl.find('dt').text.strip():
                            floor = dl.find('dd').text.strip()
                            arr = floor.split(' ')
                            if len(arr) > 1:
                                article.floor = int(arr[0].strip())
                                article.no_floor = int(arr[-1].strip())
                            else:
                                article.floor = int(floor.strip())
                h4_cost_label = info.find('h4', {'data-qa': 'is24qa-kosten-label'}, recursive=False)
                if h4_cost_label is not None:
                    sub_info = h4_cost_label.find_next('div', {'class': 'criteriagroup'}, recursive=False)
                    for div in sub_info.find('div').find_all('div', {'class': 'grid-item'}, recursive=False):
                        for dl in div.find_all('dl', recursive=False):
                            if 'Kaltmiete' in dl.find('dt').text.strip():
                                price = dl.find('dd').text.strip()
                                article.costs.base_rent = float(get_number_from_string(price))
                            elif 'Nebenkosten' in dl.find('dt').text.strip():
                                price = dl.find('dd').text.strip()
                                article.costs.operating_cost = float(get_number_from_string(price))
                            elif 'Heizkosten' in dl.find('dt').text.strip():
                                price = dl.find('dd').text.strip()
                                article.costs.heating_cost = float(get_number_from_string(price))
                            elif 'Gesamtmiete' in dl.find('dt').text.strip():
                                price = dl.find('dd').text.strip()
                                article.costs.total_rent = float(get_number_from_string(price))
                            elif 'Kaution' in dl.find('dt').text.strip():
                                price = dl.find('dd').text.strip()
                                article.costs.deposit = float(get_number_from_string(price))
            else:
                logger.error("No info found for article {0}".format(article.link))

    def __str__(self):
        return "Source: ImmobilienScout24"


def get_number_from_string(str):
    if str is not None:
        found = re.findall(r'(\d+(\.\d+)?)', str.replace('.', '').replace(',', '.'))
        return found[0][0] if len(found) > 0 else 0
    else:
        return 0
