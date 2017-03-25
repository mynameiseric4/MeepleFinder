from random import random
import matplotlib.pyplot as plt
from StringIO import StringIO
from flask import Flask
from flask import Flask, request, render_template
import json
import requests
import socket
import time
import numpy as np
from pickle import dump
import pickle
from datetime import datetime
from pymongo import MongoClient
import pandas as pd
from itertools import product
from scipy.spatial.distance import cosine
import operator
app = Flask(__name__)
board_game_index = np.load('board_game_dict.npy').item()
user_index = np.load('wa_user_dict.npy').item()
url_index = pd.read_csv('url_df.csv')
url_index = url_index.set_index('Title')
board_games = dict((y,x) for x,y in board_game_index.iteritems())
ratings_df = pd.read_csv('new_wa_ratings_data.csv', index_col='Username')
just_ranking_info = pd.read_csv('new_game_ratings.csv')
just_ranking_info.set_index('Title', inplace=True)
num_ratings = just_ranking_info['Num Ratings']
avg_ratings = just_ranking_info['Avg Rating']
num_ratings = num_ratings.sort_index()
avg_ratings = avg_ratings.sort_index()
pred_ratings_df = pd.read_csv('pred_ratings_df.csv')
pred_ratings_df = pred_ratings_df.set_index('board_game')
bg_data_sim = pd.read_csv('game_similarity_matrix.csv')
bg_data_sim = bg_data_sim.set_index('Title')


@app.route('/', methods=['GET'])
def index():
    return render_template('recommender.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('recommender_about.html')

@app.route('/how_it_works', methods=['GET'])
def how_it_works():
    return render_template('recommender_how_it_works.html')

@app.route('/predict', methods=['POST'])
def get_games():
    user_data = request.json
    game1, game2, game3 = user_data['game1'], user_data['game2'], user_data['game3']
    input_games = [game1, game2, game3]
    new_user = pd.DataFrame({'new_user': {game1:10, game2:10, game3:10}}, index=ratings_df.columns)['new_user']
    new_user.fillna(0, inplace=True)
    cos_sim_dict = {}
    for ind in ratings_df.index:
        this_user = ratings_df.loc[ind, :]
        cos_sim_dict[ind] = cosine(this_user.values, new_user.values)
    sorted_dict = sorted(cos_sim_dict.items(),
                         key=operator.itemgetter(1))
    top_3 = sorted_dict[:3]
    top_3_keys = [user_index[top_3[i][0]] for i in xrange(len(top_3))]
    user_input_df = []
    count = 0
    for user in top_3_keys:
        preds = pred_ratings_df[pred_ratings_df['user'] == user]['prediction'].sort_index()
        if count == 0:
            pred_array = preds
        else:
            pred_array += preds
        count += 1
    pred_array /= 3.
    count = 0
    sim_pred = 0
    for game in input_games:
        try:
            sim_pred += (1 - (bg_data_sim.loc[board_game_index[game], just_ranking_info.index.astype(str)].fillna(1)))
            count += 1
        except KeyError:
            continue
    if count != 0:
        sim_pred /= float(count)
        sim_pred = sim_pred.sort_index()
    else:
        sim_pred = pd.Series(0, index=sorted(just_ranking_info.index))
    new_pred_array = pd.Series(
            (pred_array.values/1.5 +
             avg_ratings.values/3. +
             sim_pred.values*20.),
            index=sorted(just_ranking_info.index))
    top_3_games = new_pred_array.sort_values(ascending=False)[:6][::-1].index
    games = []
    for ind in top_3_games:
        if board_games[ind] not in input_games:
            games.append(board_games[ind])
    new_game1 = games[0]
    new_game2 = games[1]
    new_game3 = games[2]

    return '<div class="container-fluid"><div class="row"><div class="col-sm-6 col-md-4"><div class="thumbnail"><img src='+url_index.loc[new_game1]["image"]+' alt="picture of board game" style="width:200px;"><div class="caption"><h3>'+str(new_game1)+'</h3><p>...</p><p><a href='+ "https://boardgamegeek.com{}".format(url_index.loc[new_game1]["Game URL"])+ ' class="btn btn-primary" role="button">BGG Link</a> <a href="#" class="btn btn-default" role="button">Button</a></p></div></div></div><div class="col-sm-6 col-md-4"><div class="thumbnail"><img src='+url_index.loc[new_game2]["image"]+' alt="picture of board game" style="width:200px;"><div class="caption"><h3>'+str(new_game2)+'</h3><p>...</p><p><a href='+ "https://boardgamegeek.com{}".format(url_index.loc[new_game2]["Game URL"])+ ' class="btn btn-primary" role="button">BGG Link</a> <a href="#" class="btn btn-default" role="button">Button</a></p></div></div></div><div class="col-sm-6 col-md-4"><div class="thumbnail"><img src='+url_index.loc[new_game3]["image"]+' alt="picture of board game" style="width:200px;"><div class="caption"><h3>'+str(new_game3)+'</h3><p>...</p><p><a href='+ "https://boardgamegeek.com{}".format(url_index.loc[new_game3]["Game URL"])+ ' class="btn btn-primary" role="button">BGG Link</a> <a href="#" class="btn btn-default" role="button">Button</a></p></div></div></div></div></div>'


    # <div class="row"><div class="col-md-4"><a  href="https://boardgamegeek.com{}".format(url_index.loc[new_game1]["Game URL"]) class="thumbnail"><img src ='+url_index.loc[new_game1]["image"]+' alt="some description" style="width:200px;height:200px;"/> <h3>'+str(new_game1)+'</h3><p class="text"></p></div><div class="col-md-4"><a  href="https://boardgamegeek.com{}".format(url_index.loc[new_game1]["Game URL"]) class="thumbnail"><img src ='+url_index.loc[new_game2]["image"]+' alt="some description" style="width:200px;height:200px;"/> <h3>'+str(new_game2)+'</h3><p class="text"></p><div class="col-md-4"></div><a  href="https://boardgamegeek.com{}".format(url_index.loc[new_game1]["Game URL"]) class="thumbnail"><img src ='+url_index.loc[new_game3]["image"]+' alt="some description" style="width:200px;height:200px;"/> <h3>'+str(new_game3)+'</h3><p class="text"></p></div></div>


    # <p style="font-size:20px"><b><font color="white"> Here are your potentially new favorite board games with variable accuracy: </font><table><tr><th>Game:</th><th>BGG Link:</th></tr><tr><td>'+str(new_game1)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game1]['Game URL'])+'target="_blank">'+str(new_game1)+'</a></td></tr><tr><td>'+str(new_game2)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game2]['Game URL'])+'target="_blank">'+str(new_game2)+'</a></td></tr><tr><td>'+str(new_game3)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game3]['Game URL'])+'target="_blank">'+str(new_game3)+'</a></td></tr></table>

if __name__ == '__main__':
    # Start Flask app
    app.run(host='localhost', debug=True)
