# BB-8 and R2-D2 are best friends.

import sys
sys.path.insert(0, '../FM')
sys.path.insert(0, '../yelp')

import random
import torch
import torch.nn as nn
import json
import pickle
import numpy as np
from sklearn.metrics import roc_auc_score
import time
from torch.nn.utils import clip_grad_value_, clip_grad_norm_
from torch.nn.utils.rnn import pad_sequence
from config_3 import global_config as cfg
from sklearn.metrics.pairwise import cosine_similarity
import argparse
import sys

from FM_old import FactorizationMachine
v = 0.01
d = 64

def item_score(mini_ui_pair, static_preference_index):
    # TODO: We are using user embedding
    total_result = list()
    result_dict = dict()
    [userID, itemID] = mini_ui_pair[0, :]
    userID = int(userID)
    preference_matrix_all = cfg.user_emb[[userID]]
    preference_matrix_all = np.random.multivariate_normal(mean=cfg.user_emb[[userID]].reshape(d),cov=v * v * cfg.user_TS_matrix_inv[userID])
    preference_matrix_all = preference_matrix_all.reshape(1, d)

    if len(static_preference_index) > 0:
            if len(static_preference_index) == 1:
                preference_matrix = cfg.emb_matrix[static_preference_index].reshape(1, d)
            else:
                preference_matrix = cfg.emb_matrix[static_preference_index]

            preference_matrix_all = np.concatenate((preference_matrix, preference_matrix_all), axis=0)

    for index in range(len(mini_ui_pair)):
        [userID, itemID] = mini_ui_pair[index, :]
        userID = int(userID)
        itemID = int(itemID)

        cosine_result = np.dot(preference_matrix_all, cfg.user_emb[[itemID]].T)
        cosine_result = np.sum(cosine_result, axis=0)
        # print(cosine_result)

        total_result.append(cosine_result)
        # result_dict[big_feature] = np.sum(cosine_result[: 8]) / (len(given_preference) + 1)  # choose top 5, normalization

    return total_result


def feature_similarity_micro(given_preference, residual, userID):
    # TODO: We are using user embedding
    preference_matrix_all = cfg.user_emb[[userID]]
    if len(given_preference) > 0:
        preference_matrix = cfg.emb_matrix[given_preference]
        preference_matrix_all = np.concatenate((preference_matrix, preference_matrix_all), axis=0)

    base = cfg.star_count + cfg.price_count + cfg.city_count
    right = cfg.feature_count

    given_preference_ = [item - cfg.category_count for item in given_preference if item > base]

    to_test_feature = list(set(range(cfg.category_count)) - set(given_preference_))

    the_dict = dict()
    for item in to_test_feature:
        to_test_matrix = cfg.emb_matrix[[item + base]]
        cosine_result = cosine_similarity(to_test_matrix, preference_matrix_all)
        cosine_result = np.sum(cosine_result, axis=1)
        the_dict[item] = cosine_result

    value = sorted([v for k, v in the_dict.items()], reverse=True)
    position = [value.index(the_dict[big_f]) for big_f in residual]

    return position
