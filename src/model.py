'''
This file contains the code used to create the two components of the recommender system, the Collaborative-Filtering part (using Spark's ALS model) and the Content-Based part (using a cosine similarity matrix on the board-game data)
'''

import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform, cosine
from scipy.cluster.hierarchy import linkage, dendrogram
from sklearn import preprocessing
from itertools import product
import operator
from pyspark.sql import SparkSession
from pyspark.mllib.recommendation import ALS

# Initiate SparkSession on local computer
spark = SparkSession.builder.master('local[4]').getOrCreate()

# Get dictionary to convert board game names to ints
board_game_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/board_game_dict.npy').item()
# Make dictionary to convert ints to board game names
board_games = dict((y,x) for x,y in board_game_index.iteritems())
# Get dictionary to convert usernames to ints
user_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/wa_user_dict.npy').item()
# Make dictionary to convert ints to usernames
users = dict((y,x) for x,y in user_index.iteritems())
# Get ratings data that is ready for sprak ALS model
als_data = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/als_ready_wa_ratings_data.csv')
als_data.drop('Unnamed: 0', axis=1, inplace=True)

# Convert pandas df to spark df
als_spark_df = spark.createDataFrame(als_data)
als_spark_df.cache()
# Make spark ALS model
als_model = ALS(
    itemCol='board_game',
    userCol='user',
    ratingCol='rating',
    nonnegative=True,
    regParam=0.1,
    rank=100,
    maxIter=10
    )
als_fit_model = als_model.fit(als_spark_df)
als_fit_model.save('als_model')

# Get board game ranking df to use to make sure predictions are made for every game
just_ranking_info = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/data/just_ranking_info.csv')
just_ranking_info = just_ranking_info.set_index('Title')
# Create list of tuples for every (user, board game) pair
predictions_array = list(product(als_data.loc[:, 'user'].unique(), just_ranking_info.index))
# Convert to pandas df
predictions_df = pd.DataFrame(predictions_array, columns=['user', 'board_game'])
# Convert to spark df
spark_pre_predictions_df = spark.createDataFrame(predictions_df)
spark_predictions_df = als_fit_model.transform(spark_pre_predictions_df)
pred_ratings_df = spark_predictions_df.toPandas()
# Replace any nulls with 0
pred_ratings_df.fillna(0, inplace=True)
pred_ratings_df.to_csv('pred_ratings_df.csv')

# Get cleaned board game data with features such as publisher, complexity, etc.
bg_data_with_dummies = pd.read_csv('model_ready_bg_data.csv')
bg_data_with_dummies = bg_data_with_dummies.set_index('Title')
# Rename board game names to match ints use din ALS model
bg_data_with_dummies_als = bg_data_with_dummies.rename(index=board_game_index)
x = bg_data_with_dummies_als.values # returns a numpy array
min_max_scaler = preprocessing.MinMaxScaler() # normalizes data
x_scaled = min_max_scaler.fit_transform(x)
normalized_als_df = pd.DataFrame(x_scaled,
                                 index=bg_data_with_dummies_als.index,
                                 columns=bg_data_with_dummies_als.columns)

# Make sure there are no games in similarity matrix that there are no ranking data for
for game in normalized_als_df.index:
    if game not in just_ranking_info.index:
        normalized_als_df.drop(game, inplace=True)

# Make cosine similarity matrix
Y = pdist(normalized_als_df, 'cosine')
Y = squareform(Y)
bg_data_sim = pd.DataFrame(Y, index=normalized_als_df.index, columns=normalized_als_df.index)
bg_data_sim.to_csv('game_similarity_matrix.csv')
