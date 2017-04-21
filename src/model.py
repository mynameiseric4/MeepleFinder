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

spark = SparkSession.builder.master('local[4]').getOrCreate()

ratings_df = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/data/wa_ratings_data.csv')
ratings_df = ratings_df.rename(columns={'Unnamed: 0':'Username'})
ratings_df = ratings_df.set_index('Username')
ratings_df.drop('Unnamed: 1', axis=1, inplace=True)
ind = []
for index in ratings_df.index:
    if ratings_df.loc[index, :].isnull().all() == True:
        ind.append(index)
ratings_df.drop(ind, inplace=True)
ratings_df.fillna(0, inplace=True)
board_game_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/board_game_dict.npy').item()
board_games = dict((y,x) for x,y in board_game_index.iteritems())
user_index = np.load('/Users/ericyatskowitz/galvanize_work/MeepleFinder/Erics_Web_App/wa_user_dict.npy').item()
users = dict((y,x) for x,y in user_index.iteritems())
als_data = pd.read_csv('/Users/ericyatskowitz/galvanize_work/MeepleFinder/als_ready_wa_ratings_data.csv')
als_data.drop('Unnamed: 0', axis=1, inplace=True)

als_spark_df = spark.createDataFrame(als_data)
als_spark_df.cache()
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

predictions_array = list(product(als_data.loc[:, 'user'].unique(), game_rankings.index))
predictions_df = pd.DataFrame(predictions_array, columns=['user', 'board_game'])
spark_pre_predictions_df = spark.createDataFrame(predictions_df)
spark_predictions_df = als_fit_model.transform(spark_pre_predictions_df)
pred_ratings_df = spark_predictions_df.toPandas()
pred_ratings_df.fillna(0, inplace=True)
pred_ratings_df = to_csv('pred_ratings_df.csv')

bg_data_with_dummies = pd.read_csv('model_ready_bg_data.csv')
bg_data_with_dummies = bg_data_with_dummies.set_index('Title')
bg_data_with_dummies_als = bg_data_with_dummies.rename(index=board_game_index)
x = bg_data_with_dummies_als.values #returns a numpy array
min_max_scaler = preprocessing.MinMaxScaler()
x_scaled = min_max_scaler.fit_transform(x)
normalized_als_df = pd.DataFrame(x_scaled,
                                 index=bg_data_with_dummies_als.index,
                                 columns=bg_data_with_dummies_als.columns)

Y = pdist(normalized_als_df, 'cosine')
Y = squareform(Y)
bg_data_sim = pd.DataFrame(Y, index=normalized_als_df.index, columns=normalized_als_df.index)
bg_data_sim.to_csv('game_similarity_matrix.csv')
