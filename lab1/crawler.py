import json
import re
import requests
from bs4 import BeautifulSoup

r = requests.get('https://www.blocket.se/stockholm/bilar?ca=11&cg=1020')
soup = BeautifulSoup(r.text, 'html5lib')
results = []

# Catch the article first instead of calling find_all() all the way
# so that it's easier to track individual item an assemble them into json
# objects
for item in soup.find_all('article', class_='item_row'):
    # regex to catch the id numbers
    id_str = re.search(r'item_(\d+)', item['id'])
    if id_str:
        car = {}
        car['id'] = id_str.group(1)
        # Title is an a tag inside a h1 tag
        car['title'] = item.find('h1').find('a', class_='item_link').string
        car['post_time'] = item.find('time')['datetime']
        # itemprop is a custom tag attribute so BeautifulSoup can't catch its
        # multiple values
        # Using regex again to fix it
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
        # It's weird but price really can be null
        if price:
            car['price'] = price
        results.append(car)

results = json.dumps(results)
print(results)
