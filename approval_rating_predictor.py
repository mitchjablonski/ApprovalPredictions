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
from collections import defaultdict
from datetime import datetime, timedelta
from string import punctuation
from wordcloud import WordCloud, STOPWORDS
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import post_process_and_plot as post_process
import parse_and_clean_html_table as parse_and_clean

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
        title_words   +=get_words_from_dataframe(data, 'Title')
        
    save_word_cloud(snippet_words, 'snippet_word_cloud')
    save_word_cloud(title_words, 'title_word_cloud')

def determine_sentiment_from_words(pos_words, neg_words, words_to_check):
    ##Less negative words count as positive for trump
    overall_sentiment = 1
    for word in words_to_check.split():
        if word in pos_words:
            overall_sentiment += 1
        elif word in neg_words:
            overall_sentiment -= 1
    #print(overall_sentiment)
    return overall_sentiment

def predict_approval_rating_change(polling_data, out_dir, pos_words, neg_words):
    rows, _ = polling_data.shape
    sentiment_values = defaultdict(list)
    for row in range(rows):
        filepath = (out_dir + '\\' + my_query +  polling_data.iloc[row]['StartDate']+ '_' + polling_data.iloc[row]['EndDate'] +'.txt')
        data = pd.read_csv(filepath, delimiter="\t")
        snippet_words = get_words_from_dataframe(data, 'Snippet')
        title_words   = get_words_from_dataframe(data, 'Title')
        #polling_data.iloc[row]['SnippetPred'] = determine_sentiment_from_words(pos_words, neg_words, snippet_words)
        sentiment_values['snippet_words'].append(determine_sentiment_from_words(pos_words, neg_words, snippet_words))
        #polling_data.iloc[row]['TitlePred'] = determine_sentiment_from_words(pos_words, neg_words, title_words)
        sentiment_values['title_words'].append(determine_sentiment_from_words(pos_words, neg_words, title_words))
    return sentiment_values
    
def personal_sentiment_analysis(reuters_df, out_dir, positive_words, negative_words):
    #reuters_df['ApprovalChange'] = reuters_df.loc[:,'Approve'].diff().fillna(0)
    approval_change_series = reuters_df.loc[:,'Approve'].diff().fillna(0)
    reuters_df['ApprovalChange'] = approval_change_series
    reuters_df['ApprovalPosChange'] = (reuters_df.loc[:,'ApprovalChange'] >= 0)
    sentiment_values = predict_approval_rating_change(reuters_df, out_dir, positive_words, negative_words)
    reuters_df['SnippetChange'] = sentiment_values['snippet_words']
    reuters_df['SnippetPosPred'] = (reuters_df.loc[:,'SnippetChange'] >= 0)
    reuters_df['TitleChange'] = sentiment_values['title_words']
    reuters_df['TitlePosPred'] = (reuters_df.loc[:,'TitleChange'] >= 0)
    return reuters_df

def main(my_query, url, out_dir, polling_data_framename, 
         num_requests, collect_new_data, populate_wordcloud, 
         positive_words, negative_words, stop_words, table_index, latest_year):
    
    if collect_new_data:
        polling_df = parse_and_clean.parse_html_for_table(url, table_index)
        polling_df.to_csv(path_or_buf = out_dir + '\\' + polling_data_framename)
    else:
        polling_df = pd.DataFrame.from_csv(path = out_dir + '\\' + polling_data_framename)
        
    polling_dates = parse_and_clean.modify_dates_to_contain_year(polling_df['Date'], latest_year)
    
    for keys in polling_dates.keys():
        polling_df[keys] = polling_dates[keys]
    
    #pollsters = set(polling_df['Poll'])
    ##Reuters is most common Pollster
    reuters_df = polling_df[polling_df['Poll'] == 'Reuters/IpsosReuters']
    if collect_new_data:
        request_and_write_google_results(reuters_df, out_dir, num_requests)
    
    if populate_wordcloud:
        build_word_cloud(reuters_df, out_dir, stop_words)
    
    reuters_df = personal_sentiment_analysis(reuters_df, out_dir, positive_words, negative_words)
    #nltk_sentiment_analysis(reuters_df, out_dir)
    post_process.run_post_processing(reuters_df, out_dir)

    return reuters_df 
            
if __name__ == "__main__":
    my_query = 'Donald Trump'
    url = "https://www.realclearpolitics.com/epolls/other/president_trump_job_approval-6179.html"
    #out_dir = "C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\ApprovalPredictions\GoogleRequests"
    out_dir = "C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\ApprovalPredictions\TestExtraRequests"
    polling_data_framename = 'polling_dataframe.txt'
    #num_requests = 10
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
    ##1st table in page index 0 is only recent polls, 2nd table index 1 is all data.
    table_index = 1
    latest_year = '2018'
    
    modified_polling_df = main(my_query, url, out_dir, polling_data_framename, 
                               num_requests, collect_new_data, populate_wordcloud, 
                               positive_words, negative_words, stop_words, table_index, latest_year)

              
    
    ## to read back in the data we write: data = pd.read_csv(filepath, delimiter="\t")
    