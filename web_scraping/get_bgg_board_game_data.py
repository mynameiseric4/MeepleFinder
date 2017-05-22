import selenium.webdriver
from bs4 import BeautifulSoup
import itertools
import pandas as pd

def first_search_boardgamegeek(query, browser):
    '''
    This function gets the html from a page that lists 50 board games at a time

    input:
        query: str
        browser: selenium object (webdriver)
    output:
        browser.page_source: html string
    '''
    search_url = "https://boardgamegeek.com/browse/boardgame/page/{}".format(query)
    browser.get(search_url)
    return browser.page_source

def get_game_url(product_tag):
    '''
    This function searches for an individual board game url

    input:
        product_tag: html string
    output:
        product_title: str
    '''
    title_elements = product_tag.select('a')
    if title_elements:
        product_title = title_elements[1].get('href')
        return product_title

def get_boardgamegeek_product_details(query, browser):
    '''
    This function gets all of the urls for individual games

    input:
        query: str
        browser: selenium object
    output:
        list of strings
    '''
    html = first_search_boardgamegeek(query, browser)
    soup = BeautifulSoup(html, 'html.parser')
    product_tags = soup.find_all("tr", id="row_")
    product_tags.extend(soup.find_all("tr", id="row_"))
    return [get_game_url(t) for t in product_tags]

# Initiate browser
browser = selenium.webdriver.Firefox()
product_details = []
# Get info from first 135 pages, all with boardgamegeek ratings
for i in xrange(1, 136):
    product_details.append(get_boardgamegeek_product_details(i, browser)[:100])
browser.quit()

# Turns list of lists into single list
product_details = list(itertools.chain.from_iterable(product_details))

def second_search_boardgamegeek(query, browser):
    '''
    This function gets the html from an individual board game page

    input:
        query: str
        browser: selenium object (webdriver)
    output:
        browser.page_source: html string
    '''
    search_url = "https://boardgamegeek.com{}".format(query)
    browser.get(search_url)
    return browser.page_source

def get_game_title(product_tag):
    '''
    This function searches for an individual board game title and year it was published

    input:
        product_tag: html string
    output:
        game_title: str
        year_published: str
    '''
    title_elements = product_tag.find_all("div", class_="game-header-title-info")
    if title_elements:
        game_title = title_elements[1].find_all('h1')
        year_published = game_title[0].text.split()[-1:]
        game_title = ' '.join(game_title[0].text.split()[:-1])
        return game_title, year_published

def get_secondary_game_info(product_tag):
    '''
    This function searches for an secondary board game info such as minimum and maximum players, best number of players, how long the game takes, how old someone should be to play, and complexity

    input:
        product_tag: html string
    output:
        min_players: str
        max_players: str
        best_players: str
        play_time: list
        age: str
        complexity: str
    '''
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
    '''
    This function searches for the rest of the useful board game info such as designers, artists, publishers, categories, and game mechanics

    input:
        product_tag: html string
    output:
        designers: list
        artists: list
        publishers: list
        categories: list
        mechanisms: list
    '''
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

def get_boardgamegeek_game_details(query, browser):
    '''
    This function gets all of the various board game data for individual games

    input:
        query: str
        browser: selenium object
    output:
        list of strings
    '''
    html = second_search_boardgamegeek(query, browser)
    soup = BeautifulSoup(html, 'html.parser')
    product_tags = soup.find_all("div", class_="content")
    return [(get_game_title(t),
             get_secondary_game_info(t),
             get_the_rest(t)) for t in product_tags]

# Initiate browser
browser = selenium.webdriver.Firefox()
game_details = []
# Iterate through all urls obtained from previous scraping
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

# Put info in pandas df
board_game_data = pd.DataFrame\
(game_details, index=range(1, 13501), columns=[ \
                         'Title', 'Year Published',\
                         'Min Players', 'Max Players', 'Best Players',\
                         'Play Time', 'Age', 'Complexity', 'Designers',\
                         'Artists', 'Publishers', 'Categories',\
                         'Mechanisms'])

# Save df
board_game_data.to_csv('boardgame_data.csv', encoding='utf-8')
