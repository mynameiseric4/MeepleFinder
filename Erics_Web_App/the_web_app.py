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
from pyspark.sql import SparkSession
import pyspark as ps
from pyspark.ml.recommendation import ALS, ALSModel
from itertools import product
from scipy.spatial.distance import cosine
import operator
app = Flask(__name__)
board_game_index = np.load('board_game_dict.npy').item()
user_index = np.load('wa_user_dict.npy').item()
url_index = pd.read_csv('just_urls.csv')
url_index = url_index.set_index('Title')
als_data = pd.read_csv('als_ready_wa_ratings_data.csv')
board_games = dict((y,x) for x,y in board_game_index.iteritems())
ratings_df = pd.read_csv('new_wa_ratings_data.csv', index_col='Username')
just_ranking_info = pd.read_csv('just_ranking_info.csv')
just_ranking_info.set_index('Title', inplace=True)
num_ratings = just_ranking_info['Num Ratings']
avg_ratings = just_ranking_info['Avg Rating']


@app.route('/', methods=['GET'])
def index():
    return render_template('recommender.html')


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
    for user in top_3_keys:
        user_df = pd.DataFrame(list(product([user], just_ranking_info.index)))
        user_df = user_df.rename(columns={0:'user', 1:'board_game'})
        user_input_df.append(spark.createDataFrame(user_df))
    count = 0
    for user in user_input_df:
        preds = als_model.transform(user).toPandas()
        preds.set_index('board_game', inplace=True)
        if count == 0:
            pred_array = preds['prediction']
        else:
            pred_array += preds['prediction']
        count += 1
    pred_array *= (2./3.)
    pred_array += (avg_ratings/3.)
    top_3_games = pred_array.sort_values(ascending=False)[:6][::-1].index
    games = []
    for ind in top_3_games:
        if board_games[ind] not in input_games:
            games.append(board_games[ind])
    new_game1 = games[0]
    new_game2 = games[1]
    new_game3 = games[2]

    return '<p style="font-size:20px"><b><font color="white"> Here are your potentially new favorite board games with variable accuracy: </font><table><tr><th>Game:</th><th>BGG Link:</th></tr><tr><td>'+str(new_game1)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game1]['Game URL'])+'target="_blank">'+str(new_game1)+'</a></td></tr><tr><td>'+str(new_game2)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game2]['Game URL'])+'target="_blank">'+str(new_game2)+'</a></td></tr><tr><td>'+str(new_game3)+'</td><td><a href='"https://boardgamegeek.com{}".format(url_index.loc[new_game3]['Game URL'])+'target="_blank">'+str(new_game3)+'</a></td></tr></table>'

if __name__ == '__main__':
    # Start Flask app
    spark = SparkSession.builder.master('local[4]').getOrCreate()
    als_model = ALSModel.load('als_model')
    app.run(host='localhost', debug=True)
