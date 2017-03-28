import time
from urllib import urlencode
import selenium.webdriver
from bs4 import BeautifulSoup
import itertools
import pandas as pd

def first_search_boardgamegeek(query, browser, delay=10):
    search_url = "https://boardgamegeek.com/browse/boardgame/page/{}".format(query)
    browser.get(search_url)
    #time.sleep(delay)  # Delay is unnecessary for this site
    return browser.page_source

def get_game_url(product_tag):
    title_elements = product_tag.select('a')
    if title_elements:
        product_title = title_elements[1].get('href')
        return product_title
    
def get_boardgamegeek_product_details(query, browser):
    html = first_search_boardgamegeek(query, browser)
    soup = BeautifulSoup(html, 'html.parser')
    product_tags = soup.find_all("tr", id="row_")
    product_tags.extend(soup.find_all("tr", id="row_"))
    return [get_game_url(t) for t in product_tags]

browser = selenium.webdriver.Firefox()
product_details = []
for i in xrange(1, 136):
    product_details.append(get_boardgamegeek_product_details(i, browser)[:100])
browser.quit()

product_details = list(itertools.chain.from_iterable(product_details))

def second_search_boardgamegeek(query, browser, delay=10):
    search_url = "https://boardgamegeek.com{}".format(query)
    browser.get(search_url)
    #time.sleep(delay)  # Wait a few seconds before getting the HTML source
    return browser.page_source

def get_boardgamegeek_game_details(query, browser):
    html = second_search_boardgamegeek(query, browser)
    soup = BeautifulSoup(html, 'html.parser')
    product_tags = soup.find_all("div", class_="content")
    return [(get_game_title(t), get_secondary_game_info(t), get_the_rest(t)) for t in product_tags]

def get_game_title(product_tag):
    title_elements = product_tag.find_all("div", class_="game-header-title-info")
    if title_elements:
        game_title = title_elements[1].find_all('h1')
        year_published = game_title[0].text.split()[-1:]
        game_title = ' '.join(game_title[0].text.split()[:-1])
        return game_title, year_published
    
def get_secondary_game_info(product_tag):
    title_elements = product_tag.find_all('li', attrs={'class':'gameplay-item'})
    if title_elements:
        game_info = title_elements
        num_players = game_info[0].text.split()
        min_players = num_players[0][0]
        max_players = num_players[0][2:]
        best_players = num_players[-1]
        play_time = game_info[1].text.split()[0].split(u'\u2013')
        age = game_info[2].text.split()[1].strip('+')
        complexity = game_info[3].text.split()[2]
        return min_players, max_players, best_players, play_time, age, complexity
    
def get_the_rest(product_tag):
    title_elements = product_tag.find_all('li', attrs={'class':'outline-item'})
    if title_elements:
        game_title = title_elements
        designers = game_title[3].find_all('a')[1:]
        for i, designer in enumerate(designers):
            designers[i] = designer.text
        artists = game_title[4].find_all('a')[1:]
        for i, artist in enumerate(artists):
            artists[i] = artist.text
        publishers = game_title[5].find_all('a')[1:]
        for i, publisher in enumerate(publishers):
            publishers[i] = publisher.text
        categories = game_title[6].find_all('a')[1:]
        for i, categorie in enumerate(categories):
            categories[i] = categorie.text
        mechanisms = game_title[7].find_all('a')[1:]
        for i, mechanism in enumerate(mechanisms):
            mechanisms[i] = mechanism.text
        return designers, artists, publishers, categories, mechanisms
    
browser = selenium.webdriver.Firefox()
game_details = []
for i in product_details:
    new_search = '{}/credits'.format(i)
    game_info = get_boardgamegeek_game_details(new_search, browser)[0]
    all_info = [game_info[0][0], game_info[0][1][0], game_info[1][0], \
                    game_info[1][1], game_info[1][2], game_info[1][3], game_info[1][4], game_info[1][5], \
                   game_info[2][0], game_info[2][1], game_info[2][2], game_info[2][3], game_info[2][4]]
    if all_info[3] == '':
        all_info[3] = all_info[2]
    try:
        all_info[5][1]
    except IndexError:
        all_info[5].append(all_info[5][0])
    game_details.append(all_info)
browser.quit()

board_game_data = pd.DataFrame\
(game_details, index=range(1, 13501), columns=[ \
                         'Title', 'Year Published',\
                         'Min Players', 'Max Players', 'Best Players',\
                         'Play Time', 'Age', 'Complexity', 'Designers',\
                         'Artists', 'Publishers', 'Categories',\
                         'Mechanisms'])

board_game_data.to_csv('boardgame_data.csv', encoding='utf-8')

#GAME CALLED ¥€$ SHOULD SEARCH https://boardgamegeek.com////credits, NOT WHATEVER IS IN product_details[13107]. NEED TO FIX THIS LATER.
#IMPORTED ¥€$ DATA MANUALLY