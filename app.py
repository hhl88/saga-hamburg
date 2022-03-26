import datetime
import os
import json
import requests as req
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt
from config import Config
from article import Article


class App:
    def __init__(self, comparators=None):
        self.path = os.path.dirname(os.path.abspath(__file__))
        self.done_file_path = os.path.join(self.path, 'done.json')
        self.mqtt = mqtt.Client('app-saga-hamburg', clean_session=True)
        self.mqtt.username_pw_set(username=Config.MQTT_USER, password=Config.MQTT_PASS)

        self.comparators = comparators

    def run(self):
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

        soup = self._get_response(url=Config.BASE_URL + '/immobiliensuche', query_params={'type': "wohnungen"})
        # Get list of all pagination link
        pagination_links = self._get_list_pagination_link(soup)
        print('There are %d pages' % (len(pagination_links) + 1))
        # Handle first page
        articles = self._find_all_articles_in_page(soup)
        print('Page 1 has %d articles' % len(articles))

        # Handle each pagination link
        # for idx, pagination_link in enumerate(pagination_links):
        #     soup = get_response(url=base_url + pagination_link)
        #     found = find_all_links_in_page(html=soup)
        #     print('Page %d has %d articles' % (idx + 2, len(found)))
        #     articles = articles + found
        print('There are in total %d articles' % len(articles), '\n')
        if not self.mqtt.is_connected():
            print("Connect to MQTT")
            self.mqtt.connect(host=Config.MQTT_BROKER_URL)
            print("is connected", self.mqtt.is_connected())
        for idx, article in enumerate(articles):
            print('%d: ' % (idx + 1), article.title)
            if article.id not in done and article.available and any(
                    compartor.is_match(article) for compartor in self.comparators):
                if self.mqtt.is_connected():
                    print("Publish event")
                    self.mqtt.publish('saga/events', article.dump())
                done[article.id] = today.strftime("%d.%m.%Y")

        with open(self.done_file_path, 'w') as f:
            json.dump(done, f, ensure_ascii=False, indent=4)

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
        img_path = a.find('img')['src']

        # street
        street = sub_info.find('span').text.strip()
        street = street.split(':')[1].strip()
        return Article(article_id=article_id, title=title, img_path=img_path, street=street)

    def _fulfill_article_info(self, article: Article):
        """
       Get article from html element
       """
        with open(os.path.join(self.path, "query.txt"), "r+") as f:
            query = f.read()
        r = req.post(url="{0}/tenant/graphql".format(Config.BASE_DETAIL_URL),
                     json={'operationName': 'property', 'variables': '{"id": "146863417"}', 'query': query})
        if r.status_code == 200:
            json_data = json.loads(r.text)['data']['property']
            data = json_data['data']

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
            print(data['availableFrom']['dateAvailable'])
            article.available_from = datetime.datetime.strptime(data['availableFrom']['dateAvailable'], '%Y-%m-%d')
            article.required_wbs = json_data['wbs'] if 'wbs' in json_data else False
            if 'floor' in data and data['floor'] is None:
                article.is_house = True
            else:
                article.is_house = False
                article.floor = data['floor']
                article.no_floor = data['numberOfFloors']
