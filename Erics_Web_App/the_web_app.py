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
als_data = pd.read_csv('als_ready_wa_ratings_data.csv')
board_games = dict((y,x) for x,y in board_game_index.iteritems())
ratings_df = pd.read_csv('new_wa_ratings_data.csv', index_col='Username')
just_ranking_info = pd.read_csv('just_ranking_info.csv')
just_ranking_info.drop('Unnamed: 0', axis=1, inplace=True)

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
        user_df = pd.DataFrame(list(product([user], als_data['board_game'].unique())))
        user_df = user_df.rename(columns={0:'user', 1:'board_game'})
        user_input_df.append(spark.createDataFrame(user_df))
    pred_array = np.zeros((1, len(als_data['board_game'].unique())))
    for user in user_input_df:
        preds = als_model.transform(user).toPandas()
        preds.sort_values('board_game', inplace=True)
        pred_array += preds['prediction'].values
    pred_array = pred_array[0]
    for i, game in enumerate(pred_array):
        try:
            pred_array[i] *= ((just_ranking_info[just_ranking_info['Title'] == board_games[i]]['Num Ratings'].values[0]/66420.)/2+1)
        except IndexError:
            pred_array[i] = 0
    top_3_games = pred_array.argsort()[-6:][::-1]
    games = []
    for ind in top_3_games:
        if board_games[ind] not in input_games:
            games.append(board_games[ind])
    new_game1 = games[0]
    new_game2 = games[1]
    new_game3 = games[2]

    return '<table><tr><th>Game</th></tr><tr><td>'+str(new_game1)+'</td></tr><tr><td>'+str(new_game2)+'</td></tr><tr><td>'+str(new_game3)+'</td></tr></table>'

if __name__ == '__main__':
    # Start Flask app
    spark = SparkSession.builder.master('local[4]').getOrCreate()
    als_model = ALSModel.load('als_model')
    app.run(host='localhost', debug=True)
