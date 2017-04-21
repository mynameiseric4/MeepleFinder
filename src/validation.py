'''
This file contains the code that I used to validate the model I use for my web app and determine the most effective weights for each part of the model.
'''

import boto3
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine
import operator
from itertools import product

als_data = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/als_ready_wa_ratings_data.csv')
als_data.drop('Unnamed: 0', axis=1, inplace=True)
board_game_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/board_game_dict.npy').item()
user_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/wa_user_dict.npy').item()
board_games = dict((y,x) for x,y in board_game_index.iteritems())
ratings_df = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/new_wa_ratings_data.csv', index_col='Username')
just_ranking_info = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/new_game_ratings.csv')
just_ranking_info.set_index('Title', inplace=True)
avg_ratings = just_ranking_info['Avg Rating']
avg_ratings = avg_ratings.sort_index()
pred_validation_df = pd.read_csv('pred_validation_df.csv')
pred_validation_df = pred_validation_df.set_index('board_game')
client = boto3.client('s3')
bg_sim = client.get_object(Bucket='ericyatskowitz', Key='data/game_similarity_matrix.csv')['Body']
bg_data_sim = pd.read_csv(bg_sim)
bg_data_sim = bg_data_sim.set_index('Title')
als_test_data = als_data.iloc[120849:]

num_users =  range(1, 8)
item_weights = [0., 2.5, 5., 7.5, 10., 12.5, 15., 17.5, 20.]
cf_weights = [1., 1.5, 2., 2.5, 3., 3.5, 4.]
avg_weights = [1., 1.5, 2., 2.5, 3., 3.5, 4.]
for num_user, i_w, cf_w, avg_w in product(num_users, item_weights, cf_weights, avg_weights):
    predictions = []
    for pred_user in xrange(1100, 1171):
        data = als_test_data[als_test_data['user'] == pred_user]
        input_games = data.sort_values('rating')['board_game'][-3:].values
        new_user = pd.DataFrame({'new_user':
                                 {board_games[input_games[0]]:10,
                                  board_games[input_games[1]]:10,
                                  board_games[input_games[2]]:10}},
                                index=ratings_df.columns).T
        new_user.fillna(0, inplace=True)
        cos_sim_dict = {}
        for ind in ratings_df.index[0:1100]:
            cos_sim_dict[ind] = cosine(ratings_df.loc[ind, :], new_user)
        sorted_dict = sorted(cos_sim_dict.items(), key=operator.itemgetter(1))
        top_3 = sorted_dict[:num_user]
        top_3_keys = [user_index[top_3[i][0]] for i in xrange(len(top_3))]
        user_input_df = []
        count = 0
        for user in top_3_keys:
            preds = pred_validation_df[pred_validation_df['user'] == user]['prediction'].sort_index()
            if count == 0:
                pred_array = preds
            else:
                pred_array += preds
            count += 1
        pred_array /= num_user
        count = 0
        sim_pred = 0
        for game in input_games:
            try:
                sim_pred += (1 - (bg_data_sim.loc[game, just_ranking_info.index.astype(str)].fillna(1)))
                count += 1
            except KeyError:
                continue
        if count != 0:
            sim_pred /= float(count)
            sim_pred = sim_pred.sort_index()
        else:
            sim_pred = pd.Series(0, index=sorted(just_ranking_info.index))
        new_pred_array = pd.Series(
            (pred_array.values/cf_w +
             avg_ratings.values/avg_w +
             sim_pred.values*i_w),
            index=sorted(just_ranking_info.index))
        top_games = new_pred_array.sort_values(ascending=False)[:20].index
        games = []
        for ind in top_games:
            if ind not in input_games:
                games.append(ind)
        pred = []
        for new_game in games:
            try:
                pred.append(data[data['board_game'] == new_game]['rating'].values[0])
            except IndexError:
                pred.append(0)
        predictions.append(sum(pred)/float(len(games)))
    validation = np.array(predictions).mean()
    print 'The validation score for {} users, {} item-item weight, {} cf weight, and {} avg_weight is: {}'.format(num_user, i_w, cf_w, avg_w, validation)
    validation_analysis.append((num_user, i_w, cf_w, avg_w, validation))

validation_df = pd.DataFrame(validation_analysis, columns=['Num Users', 'Item-Item Weight', 'CF Weight', 'Avg Weight', 'Validation Score'])
validation_df.to_csv('validation_df.csv', encoding='utf-8')
