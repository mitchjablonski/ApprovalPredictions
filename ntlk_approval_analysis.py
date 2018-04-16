# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 19:39:05 2018

@author: mitch
"""
import ntlk
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.model_selection import train_test_split

def format_sentence_for_nltk(sent):
    return({word: True for word in nltk.word_tokenize(sent)})

def determine_pos_neg_split_for_nltk(data, data_result):
    snippet_pos = []
    snippet_neg = []
    title_pos   = []
    title_neg   = []
    rows,_ = data.shape
    for row in range(rows):
        filepath = (out_dir + '\\' + my_query +  data.iloc[row]['StartDate']+ '_' + data.iloc[row]['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words = get_words_from_dataframe(data, 'Snippet')
        title_words   = get_words_from_dataframe(data, 'Title')
        if data_result.iloc[row]:
            snippet_pos.append(format_sentence_for_nltk(snippet_words), 'pos')
            title_pos.append(format_sentence_for_nltk(title_words), 'pos')
        else:
            snippet_neg.append(format_sentence_for_nltk(snippet_words), 'neg')
            title_neg.append(format_sentence_for_nltk(title_words), 'neg')
    return ((title_pos+title_neg), (snippet_pos+snippet_neg))

def nltk_sentiment_analysis(polling_df, out_dir):
    X_train, X_test, y_train, y_test = train_test_split(polling_df[['StartDate','EndDate']], polling_df['ApprovalPosChange'])
    title_train_data, snippet_train_data = determine_pos_neg_split_for_nltk(X_train, y_train)
    snippet_class = NaiveBayesClassifier.train(snippet_train_data)
    title_class   = NaiveBayesClassifier.train(title_train_data)
    title_test_data, snippet_test_data = determine_pos_neg_split_for_nltk(X_test, y_test)
    print(snippet_class.classify(format_sentence_for_nltk(snippet_test_data)))
    print(title_class.classify(format_sentence_for_nltk(title_test_data)))