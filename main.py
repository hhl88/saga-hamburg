import os
from dateutil.rrule import rrule, MONTHLY
import requests as req
from bs4 import BeautifulSoup
import re
import datetime
from unidecode import unidecode
import copy
import json

base_url = 'http://congbao.chinhphu.vn'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/89.0.4389.90 Safari/537.36',
    'Cookie': 'D0N=f44b94f1c5ae6da939b2147d74193383'
}

session = req.Session()
session.headers.update(headers)

params = {
    'coquanbanhanh': '12',
    'tungay': '01/06/2021',
    'loaivanban': '2',
}
diff_moth = 3
app = flask.Flask(__name__)


def update_cookies(cookies):
    if cookies is not None:
        cookie_string_to_dict = lambda c: dict(
            map(lambda x: x.split('='), map(lambda x: x.replace(' ', ''), c.split(';'))))
        old_cookies = cookie_string_to_dict(headers['Cookie'])
        new_cookies = cookie_string_to_dict(cookies)

        old_cookies.update(new_cookies)
        headers['Cookie'] = "; ".join([str(x) + "=" + str(y) for x, y in old_cookies.items()])
        session.headers.update(headers)


def make_hash(o, timestamp=None):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """

    if isinstance(o, (set, tuple, list)):
        return tuple([make_hash(e, timestamp) for e in o])

    elif not isinstance(o, dict):

        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = make_hash(v, timestamp)
    if timestamp is not None:
        new_o['timestamp'] = timestamp

    return hash(tuple(frozenset(sorted(new_o.items()))))


# def _get_cookie()

def get_response(url, query_params={}):
    """
    Request url for html response and parser via BeautifulSoup
    """
    res = session.get(url, params=query_params)
    cookies = re.findall(r'.*cookie=\"(D0N=[a-zA-Z0-9]+)\"', res.text, re.M)
    if len(cookies) > 0:
        update_cookies(cookies[0])
        res = session.get(url, params=query_params)
        soup = BeautifulSoup(res.text, 'lxml')
        return soup
    soup = BeautifulSoup(res.text, 'lxml')
    return soup


def get_articles_in_search_page(html):
    """
    Get all available articles in "search" page
    """
    articles = []
    for article in html.find_all('article', {'class': 'cong-bao-list'}):
        a = article.find('a', href=True)
        articles.append({'title': a.text.strip(), 'link': a['href']})
    return articles


def get_list_pagination_link(html):
    """
    Get all pagination links in "search" page excluding the first page
    """
    ul = html.find('ul', {'class': 'pagination'})
    if ul is None:
        return []
    return [li.find('a', href=True)['href']
            for li in ul.find_all('li', {'class': None}) if li is not None]


def find_all_links_in_page(html):
    """
    Get all pagination links in "search" page excluding the first page
    """
    links = []
    for article in get_articles_in_search_page(html):
        soup = get_response(url=base_url + article['link'])
        div = soup.find('div', {'class': 'dropdown div-inline'})
        links.append({'title': article['title'], 'link': base_url + div.find('a', href=True)['href']})

    return links


def handle_article(article, infos, file_path):
    """
    Handle an article by downloading file and find persons based on information
    """

    download_file(url=article['link'], file_path=file_path)
    persons = extract_persons(file_path=file_path)
    return find_persons(persons=persons, infos=infos, title=article['title'])


def download_file(url, file_path):
    """
    Download article pdf file
    """
    with session.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def extract_persons(file_path):
    """
    Extract all persons found in file. Only 2 cases includes:
    1. Person found in text starting with Điều and containing day of birth
    2. Person found in text starting with number (1. 2. 3. ...)
    """
    raw = parser.from_file(file_path, requestOptions={'timeout': 120})
    content = raw['content']
    persons = re.findall(r'^\d+\.(?:[^\d+\.].*\n+)+', content, re.M)

    special_persons = re.findall(r'Điều\s\d+\.(?:[^Điều].*\n+)+', content, re.M)
    for person in special_persons:
        match = re.search(r'\d+\/\d+\/\d+', person)
        if match:
            persons.append(person)

    return [re.sub(r'\s+', ' ', re.sub(r'\n+', ' ', re.sub(r'\r+', ' ', p))).strip() for p in persons]


def find_persons(persons, infos, title):
    """
    Find persons matching information requirements (name and day of birth).
    Day of birth can lead to 3 different cases:
    9/1/1990
    09/1/1990
    9/01/1990
    09/01/1990
    """
    for info in infos:
        matching = persons
        if 'year' in info and 'month' in info and 'day' in info:
            day = info['day']
            month = info['month']
            dob = '%d/%d/%d' % (day, month, info['year'])

            matching = [s.strip() for s in matching if dob in s]

            if day < 10:
                dob = '%s/%d/%d' % ('0%d' % day, month, info['year'])
                matching = [s.strip() for s in persons if dob in s] + matching

                if month < 10:
                    dob = '%d/%s/%d' % (day, '0%d' % month, info['year'])
                    matching = [s.strip() for s in persons if dob in s] + matching

                    dob = '%s/%s/%d' % ('0%d' % day, '0%d' % month, info['year'])
                    matching = [s.strip() for s in persons if dob in s] + matching
            elif month < 10:
                dob = '%d/%s/%d' % (day, '0%d' % month, info['year'])
                matching = [s.strip() for s in persons if dob in s] + matching

        if 'name' in info:
            matching = [s.strip() for s in matching if unidecode(info['name'].casefold()) in unidecode(s.casefold())]
        if 'results' not in info:
            info['results'] = []
        if len(matching) > 0:
            info['results'].append({'title': title, 'persons': matching})

    return infos


def handle_request(infos=[], query_params={}):
    if infos is None or len(infos) == 0:
        return {}

    new_infos = []
    for info in infos:
        if 'name' in info:
            info['name'] = info['name'].strip()
            if ('year' not in info or 'month' not in info or 'day' not in info) and len(info['name']) == 0:
                continue
        elif 'year' not in info or 'month' not in info or 'day' not in info:
            continue
        if 'year' in info and 'month' in info and 'day' in info:
            info['day'] = int(info['day'])
            info['month'] = int(info['month'])
            info['year'] = int(info['year'])
            if not validate_date(year=info['year'], month=info['month'], day=info['day']):
                continue
            if not validate_date_of_birth(year=info['year'], month=info['month'], day=info['day'], diff=diff_moth):
                continue

        new_infos.append(info)

    if len(new_infos) == 0:
        return []

    try:
        with open('cookie.txt', 'r+') as f:
            cookies = f.read()
            update_cookies(cookies)
    except:
        pass

    hash = make_hash(new_infos, int(datetime.datetime.now(pytz.utc).timestamp() * 1000000))
    file_path = 'download-%s.pdf' % hash[0]
    soup = get_response(url=base_url + '/tim-kiem-van-ban', query_params=query_params)
    # Get list of all pagination link
    pagination_links = get_list_pagination_link(soup)
    print('There are %d pages' % (len(pagination_links) + 1))
    # Handle first page
    articles = find_all_links_in_page(html=soup)
    print('Page 1 has %d articles' % len(articles))

    # Handle each pagination link
    for idx, pagination_link in enumerate(pagination_links):
        soup = get_response(url=base_url + pagination_link)
        found = find_all_links_in_page(html=soup)
        print('Page %d has %d articles' % (idx + 2, len(found)))
        articles = articles + found
    print('There are in total %d articles' % len(articles), '\n')

    for idx, article in enumerate(articles):
        print('%d : Downloading ' % (idx + 1), article['title'])
        new_infos = handle_article(article=article, infos=new_infos, file_path=file_path)

    try:
        os.remove(file_path)
    except OSError:
        pass

    return new_infos


def validate_date(year, month, day):
    """
    Validate date
    """
    try:
        datetime.datetime(year=int(year), month=int(month), day=int(day))
    except ValueError:
        return False
    return True


def validate_date_of_birth(year, month, day, diff):
    """
    Validate date of birth. Only valid if its month gap  until now greater than given amount.
    """
    try:
        dob = datetime.datetime(year=int(year), month=int(month), day=int(day))
        first_day_of_dob = dob.replace(day=1)

        today = datetime.datetime.now()
        first_day_of_month = today.replace(day=1)

        dates = [dt for dt in rrule(MONTHLY, dtstart=first_day_of_dob, until=first_day_of_month)]
        return len(dates) - 1 >= diff
    except ValueError:
        return False


@app.route('/find', methods=['GET'])
def find():
    data = flask.request.get_json(force=True)

    if len(data) == 0:
        return 'Invalid data', 400

    for d in data:

        if 'year' in d and 'month' in d and 'day' in d:
            if not validate_date(year=d['year'], month=d['month'], day=d['day']):
                return 'Invalid date', 400
            if not validate_date_of_birth(year=d['year'], month=d['month'], day=d['day'], diff=diff_moth):
                return 'Date of birth should be lower %d months counting until now' % diff_moth, 400

        if 'name' in d:
            d['name'] = d['name'].strip()

    # limit starting from previous month
    today = datetime.datetime.today()
    first = today.replace(day=1)
    last_month = first - datetime.timedelta(days=1)
    last_month = last_month.replace(day=1)

    params['tungay'] = last_month.strftime('%d/%m/%Y')
    result = handle_request(data, query_params=params)

    return flask.jsonify(result), 200


# app.run(host='0.0.0.0', debug=True)
infos = [
    {"name": "Hong Hai"},
    {"year": 1988, "month": 10, "day": 20}
]
params['tungay'] = '01/12/2021'
result = handle_request(infos=infos, query_params=params)
print(json.dumps(result, indent=4, sort_keys=True, ensure_ascii=False))
# res = session.get(url=base_url + '/tim-kiem-van-ban', params=params)
# res = session.get(url='http://congbao.chinhphu.vn/tim-kiem-van-ban?coquanbanhanh=12&tungay=01%2F04%2F2021&loaivanban=2')
# print('res', res.text)
# cookies = re.findall(r'.*cookie=\"(D0N=[a-zA-Z0-9]+)\"', res.text, re.M)
# print(cookies)
# update_cookies(cookies[0])
# res = session.get(url=base_url + '/tim-kiem-van-ban', params=params)

# print(res.text)