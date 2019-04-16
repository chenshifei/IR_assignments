import json
import re
import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.blocket.se/stockholm/bilar?ca=11&cg=1020')
soup = BeautifulSoup(r.text, 'html5lib')
results = []

for item in soup.find_all('article', class_='item_row'):
    id_str = re.search(r'item_(\d+)', item['id'])
    if id_str:
        car = {}
        car['id'] = id_str.group(1)
        car['title'] = item.find('h1').find('a', class_='item_link').string
        car['post_time'] = item.find('time')['datetime']
        location = item.find(itemprop=re.compile(r'availableAtOrFrom'))
        if location:
            car['locaiton'] = location.string
        seller_name = item.find(class_='motor-li-thumb-storename')
        if seller_name:
            car['seller_name'] = seller_name.string
        desc = item.find('p', class_='motor-li-thumb-extra-info').string
        if desc:
            car['desc'] = desc
        price = item.find(itemprop='price').string
        if price:
            car['price'] = price
        results.append(car)

results = json.dumps(results)
print(results)
