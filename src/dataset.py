# !/usr/bin/python
# -*- coding:utf-8 -*-  
# @author: Shengjia Yan
# @date: 2018-06-06 Wednesday
# @email: i@yanshengjia.com
# Copyright @ Shengjia Yan. All Rights Reserved.
"""
This module implements data process strategies.
"""

import csv
import yaml
import json
import numpy as np
from sklearn import preprocessing


import logging
logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] (%(asctime)s) (%(name)s) %(message)s',
        handlers=[
            logging.FileHandler('../data/log/hc.log', encoding='utf8'),
            logging.StreamHandler()
        ])
logger = logging.getLogger('dataset')


class HCDataset(object):
    """
    This module implements the APIs for loading and using dataset
    """
    def __init__(self, config_path, data_files=[], train_files=[], dev_files=[], test_files=[]):
        self.feature_config = self.read_feature_config(config_path)

        self.data_set, self.train_set, self.dev_set, self.test_set = [], [], [], []
        if data_files:
            for data_file in data_files:
                self.data_set += self._load_dataset(data_file)
            self.dataset_size = len(self.data_set)
            logger.info('Data set size: {} essays.'.format(self.dataset_size))

        if train_files:
            for train_file in train_files:
                self.train_set += self._load_dataset(train_file)
            self.trainset_size = len(self.train_set)
            logger.info('Train set size: {} essays.'.format(self.trainset_size))
            self.standardize()
            logger.info('Build feature scalers on train set.')

        if dev_files:
            for dev_file in dev_files:
                self.dev_set += self._load_dataset(dev_file)
            self.devset_size = len(self.dev_set)
            logger.info('Dev set size: {} essays.'.format(self.devset_size))

        if test_files:
            for test_file in test_files:
                self.test_set += self._load_dataset(test_file)
            self.testset_size = len(self.test_set)
            logger.info('Test set size: {} essays.'.format(self.testset_size))

    def read_feature_config(self, config_path):
        """
        Read the feature.config
        Args:
            config_path: the config file to load
        """
        with open(config_path, 'r') as stream:
            try:
                feature_config = yaml.load(stream)
                logger.info('Feature config loaded.')
                self.full_feature_types = list(feature_config.keys())
                self.feature_types = list(feature_config.keys())
                self.feature_types.remove('basic')
                logger.info('Feature types: ' + str(self.feature_types))

                self.feature_dim = {}
                for feature_type in self.full_feature_types:
                    self.feature_dim[feature_type] = len(feature_config[feature_type])
                
                self.feature_dim['sum'] = 0
                for feature_type in self.feature_types:
                    self.feature_dim['sum'] += self.feature_dim[feature_type]

                logger.info('Basic info dim: {}'.format(self.feature_dim['basic']))
                logger.info('Feature dim: {}'.format(self.feature_dim['sum']))
                for feature_type in self.feature_types:
                    logger.info('  {} feature dim: {}'.format(feature_type, self.feature_dim[feature_type]))
                return feature_config
            except yaml.YAMLError as exc:
                logger.error(exc)
    
    def _load_dataset(self, data_path):
        """
        Loads the dataset
        Args:
            data_path: the data file to load
        """
        with open(data_path, 'r') as in_file:
            data_set = []
            reader = csv.DictReader(in_file)
            for line in reader:
                data_set.append(line)
        return data_set
    
    def _gen_input(self, data, feature_type=''):
        """
        Generate the feature matrix and corresponding label vector based on the feature type
        Args:
            data: the list of features and labels
            feature_type: one of ['lexical', 'grammar', 'sentence', 'structure', 'content']
        Rtype:
            features: {array-like, sparse matrix}, shape (n_samples, n_features)
            labels: array-like, shape (n_samples,)
        """
        if feature_type not in self.feature_types:
            raise NotImplementedError('The dataset doesn\'t contain {} features.'.format(feature_type))
        
        features, labels = [], []
        for sample in data:
            s = []
            for key, val in sample.items():
                if key in self.feature_config[feature_type]:
                    s.append(float(val))
            features.append(s)
            labels.append(float(sample['score']))
        features = np.matrix(features)
        features = self.scalers[feature_type].transform(features)
        labels = np.array(labels)
        assert features[0].size == len(self.feature_config[feature_type]), 'The {} feature dim in dataset is incorrect!'.format(feature_type)
        return features, labels

    def standardize(self):
        """
        Z standardization, or mean removal and variance scaling
        """
        self.scalers = {}

        for feature_type in self.feature_types:
            train_x = []
            for sample in self.train_set:
                s = []
                for key, val in sample.items():
                    if key in self.feature_config[feature_type]:
                        s.append(float(val))
                train_x.append(s)
            train_x = np.matrix(train_x)
            self.scalers[feature_type] = preprocessing.StandardScaler().fit(train_x)

    def bucketize(self, labels):
        """
        Move labels into 5 buckets.
        Args:
            labels: array-like, shape (n_samples,)
        """
        new_labels = []
        for label in labels:
            if label <= 3:
                new_label = 1
            elif 4 <= label <= 6:
                new_label = 2
            elif 7 <= label <= 10:
                new_label = 3
            elif 11 <= label <= 13:
                new_label = 4
            else:
                new_label = 5
            new_labels.append(new_label)
        new_labels = np.array(new_labels)
        return new_labels

