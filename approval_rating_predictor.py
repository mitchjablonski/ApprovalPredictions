# -*- coding: utf-8 -*-
"""
Created on Sat Apr 07 09:58:31 2018

@author: mitch
"""
#from googleapiclient.discovery import build

#from apiclient.discovery import build
from __future__ import division
from apiclient.discovery import build
#import urllib2
#from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from string import punctuation
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import post_process_and_plot as post_process
import parse_and_clean_html_table as parse_and_clean
from sklearn.model_selection import train_test_split
from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
from nltk.classify import NaiveBayesClassifier
import nltk.classify.util
from functools import partial
from multiprocessing import Pool


config = {}
execfile("C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\config.py", config)

devKey = config["GdevKey"]
devcx = config["Gdevcx"]

def build_google_query(service, query, start_date, end_date, num_requests):
    ##This is the datrange format that the google CSE api expects it
    date_range = "date:r:" + start_date + ":" + end_date
    ##may need start to limit
    ##num requests defaults to 10 can be 1 through 10
    result = service.cse().list(q=query, cx=devcx, sort=date_range, num = num_requests).execute()
    return result

##Taken from in google1.py file
###Tony Breitzman - abreitzman@1790analytics.com
#May 1, 2013
##Start
def remove_non_ascii(s): 
    return "".join(i for i in s if ord(i)<128)

def clean_text(s):
  s = remove_non_ascii(s)
  s = ' '.join(s.split())
  return s
##End

def get_search_start_and_end_date(search_start, search_end):
    search_start = datetime.strptime(search_start, "%Y-%m-%d")
    search_end   = datetime.strptime(search_end, "%Y-%m-%d")
    delta_days   = abs(search_end - search_start).days
    search_start = str((search_start - timedelta(days = delta_days)).date())
    search_end   = str((search_end - timedelta(days = delta_days)).date())
    return search_start, search_end

def request_and_write_google_results(poll_df, out_dir, num_requests):
    rows, _ = poll_df.shape
    
    service = build("customsearch", "v1",
                    developerKey=devKey)
    
    for row in range(rows):
        new_file = (out_dir + '\\' + my_query +  poll_df.iloc[row]['StartDate']+ '_' + poll_df.iloc[row]['EndDate'] +'.txt')
        ##We should search from the the amount of days the poll lasted prior to the start, through the start
        search_start, search_end = get_search_start_and_end_date(poll_df.iloc[row]['StartDate'], poll_df.iloc[row]['EndDate'])
        ##For our purposes, there appear to be 3 important items, the title for each item, the snippet and the link (technically not important)
        with open(new_file, 'w') as curr_file:
            curr_file.write('Link\tTitle\tSnippet\n')
            results = build_google_query(service, my_query, search_start.replace('-',''), search_end.replace('-',''), num_requests)
            for items in results['items']:
                curr_file.write(items['link'] +'\t' + clean_text(items['title']) + '\t' + clean_text(items['snippet']) + '\n')

def clean_punctuation(words):
    for c in punctuation:
        if '\'' in c:
            words = words.replace(c, '')
        else:
            words= words.replace(c," ") 
    return words

def save_word_cloud(words, filename):
    wordcloud = WordCloud(
                     #font_path='C:/Tweets/cabin-sketch-v1.02/CabinSketch-Regular.ttf',
                      stopwords=STOPWORDS,
                      background_color='black',
                      width=1800,
                      height=1400
                     ).generate(words)

    #sys.stdout.write('%s\n' % words)
    plt.imshow(wordcloud)
    plt.axis('off')
    plt.savefig('./' +filename +'.png', dpi=300)
    plt.show()

def stop_words_for_wordcloud(stop_words):
    for word in stop_words:
        STOPWORDS.add(word)

def get_words_from_dataframe(data, key):
    return(clean_punctuation(data[key].add(' ').sum(axis = 0)).lower())

def build_word_cloud(polling_df, out_dir, stop_words):
    stop_words_for_wordcloud(stop_words)
    snippet_words = ''
    title_words = ''
    rows, _ = polling_df.shape
    for row in range(rows):
        filepath = (out_dir + '\\' + my_query +  polling_df.iloc[row]['StartDate']+ '_' + polling_df.iloc[row]['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words += get_words_from_dataframe(data, 'Snippet')
        title_words   += get_words_from_dataframe(data, 'Title')
    save_word_cloud(snippet_words, 'snippet_word_cloud')
    save_word_cloud(title_words, 'title_word_cloud')
    save_word_cloud("".join(stem_words(snippet_words)), 'stemmed_snippet_cloud')
    save_word_cloud("".join(stem_words(title_words)), 'stemmed_title_cloud')

def determine_sentiment_from_words(pos_words, neg_words, words_to_check):
    ##Less negative words count as positive for trump
    #overall_sentiment = 1
    overall_sentiment = 0
    for word in words_to_check:
        if word in pos_words:
            overall_sentiment += 1
        elif word in neg_words:
            overall_sentiment -= 1
    return overall_sentiment

def stem_words(words_to_stem):
    stemmer = SnowballStemmer("english")
    words_ret = []
    for words in words_to_stem:
        words_ret.append(stemmer.stem(words))
    return words_ret

def gather_words_train_set(polling_df, out_dir, junk_words, X_train):
    positive_counter = Counter()
    negative_counter = Counter()
    all_pos_words = []
    all_neg_words = []
    for index, row in X_train.iterrows():
        filepath = (out_dir + '\\' + my_query +  row['StartDate']+ '_' + row['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words = get_words_from_dataframe(data, 'Snippet')
        title_words   = get_words_from_dataframe(data, 'Title')
        #test_stem = (stem_words(snippet_words.split()))
        all_words = stem_words(snippet_words.split() + title_words.split())
        if polling_df.loc[index, 'ApprovalPosChange'] == 1:
            for word in all_words:
                all_pos_words.append(word)
                if word not in junk_words:
                    positive_counter[word] += 1
        else:
            for word in all_words:
                all_neg_words.append(word)
                ##If we don't add all -1 will be weighted equally in most_common
                if word not in junk_words:
                    negative_counter[word] += 1    
    return positive_counter, negative_counter, all_pos_words, all_neg_words

def determine_pos_neg_word_split(positive_counter, negative_counter, num_words_to_use):
    positive_words = []
    negative_words = []
    tot_words_sentiment = []
    all_words = [words for words,_ in positive_counter.most_common(num_words_to_use)]
    all_words += [words for words, _ in negative_counter.most_common(num_words_to_use)]
    for word in all_words:
        if positive_counter[word] - negative_counter[word] > 0:
            positive_words.append(word)
            tot_words_sentiment.append((word, 'pos'))
        else:
            negative_words.append(word)
            tot_words_sentiment.append((word,'neg'))
    return positive_words, negative_words, tot_words_sentiment

def perform_analysis_test_set(polling_df, out_dir, pos_words, neg_words, X_test):
    sentiment_values = defaultdict(list)
    for index, row in X_test.iterrows():
        filepath = (out_dir + '\\' + my_query +  row['StartDate']+ '_' + row['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words = stem_words(get_words_from_dataframe(data, 'Snippet').split())
        title_words   = stem_words(get_words_from_dataframe(data, 'Title').split())
        sentiment_values['snippet_words_auto'].append(determine_sentiment_from_words(pos_words, neg_words, snippet_words)) 
        sentiment_values['title_words_auto'].append(determine_sentiment_from_words(pos_words, neg_words, title_words)) 
    return sentiment_values

def get_word_features(all_words):
    wordlist = nltk.FreqDist(all_words)
    features = wordlist.keys()
    return features

def extract_features(w_features, wordset):
    docwords = set(wordset)
    features = {}
    for word in w_features:
        features['constains'.format(word)] = (word in words)

def determine_sentiment_auto(polling_df, out_dir, junk_words, test_train_split_word_count, num_iters_auto):
    accuracy_list = []
    for iters in range(num_iters_auto):
        X_train, X_test, y_train, y_test = train_test_split(polling_df[['StartDate','EndDate']], polling_df['ApprovalPosChange'])
        positive_counter, negative_counter, all_pos_words, all_neg_words = gather_words_train_set(polling_df, out_dir, junk_words, X_train)
        pos_words, neg_words, tot_words_sentiment = determine_pos_neg_word_split(positive_counter, negative_counter, test_train_split_word_count)
        '''
        Attempt to use classifier...
        '''
        #all_words = all_pos_words + all_neg_words
        #w_features = get_word_features(all_words)
        #partial_extract = partial(extract_features, w_features)
        #training_set = nltk.classify.apply_features(partial_extract, tot_words_sentiment)
        #classifier = nltk.NaiveBayesClassifier.train(training_set)
        sentiment_values = perform_analysis_test_set(polling_df, out_dir, pos_words, neg_words, X_test)
        temp_df = pd.DataFrame()
        temp_df['SnippetChangeAuto'] = sentiment_values['snippet_words_auto']
        temp_df['SnippetPosPredAuto'] = (temp_df.loc[:,'SnippetChangeAuto'] >= 0)
        temp_df['TitleChangeAuto'] = sentiment_values['title_words_auto']
        temp_df['TitlePosPredAuto'] = (temp_df.loc[:,'TitleChangeAuto'] >= 0)
        print(accuracy_score(y_test, temp_df['SnippetPosPredAuto']))
        acc_score = accuracy_score(y_test, temp_df['SnippetPosPredAuto'])
        accuracy_list.append(acc_score)

    mean_acc = reduce(lambda x,y: x+y, accuracy_list) / len(accuracy_list)
    print('Mean Accuracy {}'.format(mean_acc))

    #count_vect = CountVectorizer(count_vect_filelist)
    #print(count_vect)
    #X_train_counts = count_vect.fit_transform(X_train)
    '''
    pos_dict = dict([(word, True) for word in all_pos_words])
    neg_dict = dict([(word, True) for word in all_neg_words])
    pos_feats = (pos_dict, 'pos')
    neg_feats = (neg_dict, 'neg')
    #pos_feats = [(str(words), 'pos') for words in all_pos_words]
    #neg_feats = [(str(words), 'neg') for words in all_neg_words]

    negcutoff = len(neg_feats)*3//4
    poscutoff = len(pos_feats)*3//4
    train_feats = neg_feats[:negcutoff] + pos_feats[:poscutoff]
    test_feats = neg_feats[negcutoff:] + pos_feats[poscutoff:]
    classifier = NaiveBayesClassifier.train(train_feats)
    print 'accuracy:', nltk.classify.util.accuracy(classifier, test_feats)
    classifier.show_most_important_features()
    #print(pos_feats)
    '''
    return (positive_counter, negative_counter, mean_acc)

def determine_sentiment_full_set(polling_df, out_dir, junk_words, full_set_word_count):
    ##We should be able to provide the polling df as the test set and have this work...
    positive_counter, negative_counter, all_pos_words, all_neg_words = gather_words_train_set(polling_df, out_dir, junk_words, polling_df)
    pos_words, neg_words,_ = determine_pos_neg_word_split(positive_counter, negative_counter, full_set_word_count)
    sentiment_values = perform_analysis_test_set(polling_df, out_dir, pos_words, neg_words, polling_df)
    polling_df['SnippetChangeAuto'] = sentiment_values['snippet_words_auto']
    polling_df['SnippetPosPredAuto'] = (polling_df.loc[:,'SnippetChangeAuto'] >= 0)
    polling_df['TitleChangeAuto'] = sentiment_values['title_words_auto']
    polling_df['TitlePosPredAuto'] = (polling_df.loc[:,'TitleChangeAuto'] >= 0)
    '''
    msk = np.random.rand(len(polling_df)) < 0.8
    train = polling_df.loc[msk]
    test = polling_df.loc[~msk]
    '''

    return polling_df

def predict_approval_rating_change(polling_data, out_dir, pos_words, neg_words):
    rows, _ = polling_data.shape
    sentiment_values = defaultdict(list)
    for row in range(rows):
        filepath = (out_dir + '\\' + my_query +  polling_data.iloc[row]['StartDate']+ '_' + polling_data.iloc[row]['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words = get_words_from_dataframe(data, 'Snippet').split()
        title_words   = get_words_from_dataframe(data, 'Title').split()
        sentiment_values['snippet_words'].append(determine_sentiment_from_words(pos_words, neg_words, snippet_words))
        sentiment_values['title_words'].append(determine_sentiment_from_words(pos_words, neg_words, title_words))
    return sentiment_values
    
def personal_sentiment_analysis(reuters_df, out_dir, positive_words, negative_words):
    reuters_df['ApprovalChange']    = reuters_df.loc[:,'Approve'].diff(-1).fillna(0)
    reuters_df['ApprovalPosChange'] = (reuters_df.loc[:,'ApprovalChange'] >= 0)
    
    sentiment_values = predict_approval_rating_change(reuters_df, out_dir, positive_words, negative_words)

    reuters_df['SnippetChange']  = sentiment_values['snippet_words']
    reuters_df['SnippetPosPred'] = (reuters_df.loc[:,'SnippetChange'] >= 0)
    reuters_df['TitleChange']    = sentiment_values['title_words']
    reuters_df['TitlePosPred']   = (reuters_df.loc[:,'TitleChange'] >= 0)
    return reuters_df

def _main(my_query, url, out_dir, polling_data_framename, 
         num_requests, collect_new_data, populate_wordcloud, 
         positive_words, negative_words, stop_words, table_index, 
         latest_year, junk_words, num_iters_auto, test_train_split_word_count,
         full_set_word_count):
    
    if collect_new_data:
        polling_df = parse_and_clean.parse_html_for_table(url, table_index)
        polling_df.to_csv(path_or_buf = out_dir + '\\' + polling_data_framename)
    else:
        #polling_df = pd.DataFrame.from_csv(path = out_dir + '\\' + polling_data_framename)
        polling_df = pd.read_csv(out_dir + '\\' + polling_data_framename)
        
    polling_dates = parse_and_clean.modify_dates_to_contain_year(polling_df['Date'], latest_year)
    
    for keys in polling_dates.keys():
        polling_df[keys] = polling_dates[keys]
    
    #pollsters = set(polling_df['Poll'])
    ##Reuters is most common Pollster
    reuters_df = polling_df.loc[polling_df['Poll'] == 'Reuters/IpsosReuters'].copy()
    if collect_new_data:
        request_and_write_google_results(reuters_df, out_dir, num_requests)
    
    if populate_wordcloud:
        build_word_cloud(reuters_df, out_dir, stop_words)

    reuters_df = personal_sentiment_analysis(reuters_df, out_dir, positive_words, negative_words)

    pos_count, neg_count, acc_score = determine_sentiment_auto(reuters_df, out_dir, junk_words, test_train_split_word_count, num_iters_auto)
    #iter_list = [i for i in range(num_iters_auto)]
    #partial_auto = partial(determine_sentiment_auto, reuters_df, out_dir, junk_words, test_train_split_word_count)
    #pool = Pool()
    #accuracy_list = pool.map(partial_auto, iter_list)
    #acc_score = reduce(lambda x,y: x+y, accuracy_list) / len(accuracy_list)
    #print('Mean Accuracy {}'.format(acc_score))

    reuters_df = determine_sentiment_full_set(reuters_df, out_dir, junk_words, full_set_word_count)
    #nltk_sentiment_analysis(reuters_df, out_dir)
    post_process.run_post_processing(reuters_df, out_dir, acc_score)

    return reuters_df 
            
if __name__ == "__main__":
    my_query = 'Donald Trump'
    url = "https://www.realclearpolitics.com/epolls/other/president_trump_job_approval-6179.html"
    #out_dir = "C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\ApprovalPredictions\GoogleRequests"
    out_dir = "C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\ApprovalPredictions\TestExtraRequests"
    polling_data_framename = 'polling_dataframe.txt'

    num_requests = 10
    collect_new_data = False
    populate_wordcloud = False
    positive_words = ['deal', 'iran', 'rally', 
                      'aid', 'won', 'top', 'mexico', 
                      'taxes', 'tax', 'plan', 'korea', 'military',
                      'leader', 'presidential', 'clinton', 'china', 
                      'trade', 'health','war', 'international', 'global', 'credit']

    negative_words = ['investigation', 'porn', 'russia', 
                      'russian', 'fbi', 'counsel', 'special', 'russian',
                      'putin', 'election', 'attorney', 'mueller',
                      'twitter', 'palm', 'probe', 'flordia',
                      'comey', 'fact', 'lawyer', 'stormy', 'flynn', 'tweet']
    
    stop_words = ['Donald', 'Trump', 'President', 'Washington', 
                  'President', 'York', 'Jr', 'AP', 'White', 'House',
                  'Monday', 'Tuesday', 'Wednesday', 
                  'Thursday', 'Friday', 'Saturday', 'Sunday',
                  'Jan', 'Feb', 'Mar', 'Apr', 'May', 
                  'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 
                  'Nov', 'Dec', 'say', 'said', 'talk', 
                  'latest', 'sign', 'first', 'wants', 
                  'day', 'tell', 'second', 'Associated', 
                  'Press', 'new', 'will', 'call', 
                  'times', 'local', 'one', 'says', 'calls']

    #junk_words = set(stopwords.words('english'))
    #Words should come from NLTK stopwords
    junk_words = []
    
    junk_words = ['ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there', 
                  'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they', 'own', 'an', 'be', 'some', 
                  'for', 'do', 'its', 'yours', 'such', 'into', 'of', 'most', 'itself', 'other', 'off', 'is', 's', 
                  'am', 'or', 'who', 'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below', 'are', 'we', 
                  'these', 'your', 'his', 'through', 'don', 'nor', 'me', 'were', 'her', 'more', 'himself', 'this',
                   'down', 'should', 'our', 'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had',
                    'she', 'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and', 'been', 'have', 
                    'in', 'will', 'on', 'does', 'yourselves', 'then', 'that', 'because', 'what', 'over', 'why',
                     'so', 'can', 'did', 'not', 'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 
                     'too', 'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't', 'being', 'if', 
                     'theirs', 'my', 'against', 'a', 'by', 'doing', 'it', 'how', 'further', 'was', 'here', 'than']
    
    junk_words += [words.lower() for words in stop_words]
    stemmer = SnowballStemmer("english")
    junk_words = [stemmer.stem(words) for words in junk_words]
    addtl_years = ['2018', '2017']
    junk_words += addtl_years
    ##1st table in page index 0 is only recent polls, 2nd table index 1 is all data.
    table_index = 1
    latest_year = '2018'
    num_iters_auto = 100
    test_train_split_word_count = 500
    full_set_word_count = 25
    
    modified_polling_df = _main(my_query, url, out_dir, polling_data_framename, 
                                num_requests, collect_new_data, populate_wordcloud, 
                                positive_words, negative_words, stop_words, table_index, 
                                latest_year, junk_words, num_iters_auto, test_train_split_word_count,
                                full_set_word_count)
