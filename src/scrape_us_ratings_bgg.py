import time
import selenium.webdriver
from bs4 import BeautifulSoup
import itertools
import pandas as pd
import numpy as np
import re
import boto3
from selenium.common.exceptions import NoSuchElementException

s3_client = boto3.client('s3')
s3_client.download_file('capstone-eric', 'data/us_users_urls.csv')

with open('data/us_users_urls.csv') as f:
    for line in f:
        us_user_urls = line.split(',')
for i, user in enumerate(us_user_urls):
    us_user_urls[i] = str(user.strip('\"'))


def get_boardgamegeek_user_info(query, browser, delay=5):
    user_info = []
    search_url = "https://boardgamegeek.com/collection{}?rated=1&subtype=boardgame&ff=1".format(query)
    browser.get(search_url)
    while True:
        html = browser.page_source
        soup = BeautifulSoup(html, 'html.parser')
        product_tags = soup.find_all('tr', {"id": lambda x: x and x.startswith('row')})
        user_info.append([get_user_info(t) for t in product_tags])
        try:
            browser.find_element_by_link_text('»').click()
        except NoSuchElementException:
            html = browser.page_source
            soup = BeautifulSoup(html, 'html.parser')
            product_tags = soup.find_all('tr', {"id": lambda x: x and x.startswith('row')})
            user_info.append([get_user_info(t) for t in product_tags])
            break
    time.sleep(delay)
    ratings = []
    for i in xrange(1, len(user_info)):
        ratings += user_info[i]
    return list(set(ratings))


def get_user_info(product_tag):
    title_elements = product_tag.find_all("div")
    if title_elements:
        rated_games = title_elements[1].text.split()[:-1]
        rated_games = ' '.join(rated_games)
        if rated_games == u'':
            rated_games = title_elements[1].text.split()
            rated_games = ' '.join(rated_games)
        ratings = title_elements[7].text.split()[0]
        date = ' '.join(title_elements[8].text.split()[0:2])
        date = date.strip('*')
        return rated_games, float(ratings), date


browser = selenium.webdriver.PhantomJS(executable_path='/Users/ericyatskowitz/galvanize_work/capstone/phantomjs-2.1.1-macosx/bin/phantomjs')
user_info = {}
count = 0
for url in us_user_urls:
    user = url.split('/')[2]
    user_ratings = get_boardgamegeek_user_info(url, browser)
    user_info[user] = user_ratings
    time.sleep(5)
    count += 1
    if count % 3000 == 0:
        s3_client.upload_file('capstone-eric', 'data/us_ratings_data.npy')
browser.quit()

s3_client.upload_file('capstone-eric', 'data/us_ratings_data.npy')