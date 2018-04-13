# -*- coding: utf-8 -*-
"""
Created on Sat Apr 07 09:58:31 2018

@author: mitch
"""
#from googleapiclient.discovery import build

#from apiclient.discovery import build
from __future__ import division
from apiclient.discovery import build
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from string import punctuation
from wordcloud import WordCloud, STOPWORDS
import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

config = {}
execfile("C:\Users\mitch\Desktop\Masters\DataMiningI\DataMiningProject\config.py", config)

devKey = config["GdevKey"]
devcx = config["Gdevcx"]

def convert_to_two_digit_date(curr_date):
    new_date = curr_date
    if (int(curr_date) < 10):
        new_date = '0' + curr_date
    return new_date

def convert_to_desired_date_format(year, month, day):
    return (year +'-' + month + '-' + day)
    ##The Google CSE does not like the 
    ##return (year + month + day)
    
def generate_google_format_date(year, month, day):
    ##Google expects that months and days have two digits, 
    ##convert them if they arent
    new_month = convert_to_two_digit_date(month)
    new_day   = convert_to_two_digit_date(day)
    return convert_to_desired_date_format(year, new_month, new_day)
    
def modify_dates_to_contain_year(date_data, latest_year):
    polling_dates = defaultdict(list)
    curr_year = latest_year
    start_date_last_year = False
    end_date_last_year = False
    year_modified    = False
    ##Desired format YYYY-MM-DD
    for dates in date_data:
        #date_list = dates.split()
        #date_list = [date_list[0], date_list[2]]
        ##Replace the - between our data, and split the data.
        date_list = dates.replace('-','').split()
        #item 1 in our dateList is our start poll, 2 is our end poll
        for curr_num, month_day in enumerate(date_list):
            month_day = month_day.split('/')
            temp_year = curr_year
            ##item Last Year
            if int(month_day[0]) == 12 and year_modified == False:
                temp_year = str(int(curr_year) -1)
                if curr_num == 0:
                    start_date_last_year = True
                else:
                    end_date_last_year = True
                    
            new_date = generate_google_format_date(temp_year, month_day[0], month_day[1])
            if curr_num == 0:
                polling_dates['StartDate'].append(new_date)
            else:
                polling_dates['EndDate'].append(new_date)
                
            if start_date_last_year and end_date_last_year:
                curr_year = str(int(curr_year) - 1)
                year_modified = True
                start_date_last_year = False
                end_date_last_year = False
        ##We are no longer in december, we can go back another year next time
        ##we reach december
        start_month = date_list[0].split('/')
        end_month   = date_list[1].split('/')
        if (int(start_month[0]) == 11 and int(end_month[0]) == 11):
            year_modified = False
    return polling_dates

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

##referenced https://henryhungle.wordpress.com/2016/08/05/python-predicting-us-presidential-election/ for similar parsing                
def parse_html_for_table(url, table_index):
    content = urllib2.urlopen(url)
    soup = BeautifulSoup(content,'html.parser')
    tables = soup.findAll('table', {'class': 'data'})
    ##1st table in page index 0 is only recent polls, 2nd table index 1 is all data.
    table = tables[table_index]
    
    rows = [row for row in table.find_all("tr")]
    columns = [str(col.get_text()) for col in rows[0].find_all("th")]
    polling_headers = [column.split('(')[0].strip() for column in columns[:]]
    
    polling_data = []
    for row in rows:
        tds = row.find_all("td")    
        polling_data.append([(str(t.get_text())) for t in tds[:]])
    
    polling_df = pd.DataFrame(data = polling_data[1:], columns = polling_headers)
    return polling_df

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
        #snippet_words += data['Snippet'].add(' ').sum(axis = 0)
        #title_words += data['Title'].add(' ').sum(axis = 0)
        snippet_words += get_words_from_dataframe(data, 'Snippet')
        title_words   +=get_words_from_dataframe(data, 'Title')
    
    #snippet_words = clean_punctuation(snippet_words)
    #title_words = clean_punctuation(title_words)    
    save_word_cloud(snippet_words, 'snippet_word_cloud')
    save_word_cloud(title_words, 'title_word_cloud')
'''
def load_my_csv(filepath, delimiter):
    return pd.read_csv(filepath, delimiter="\t")
'''
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

def Main(my_query, url, out_dir, polling_data_framename, 
         num_requests, collect_new_data, populate_wordcloud, 
         positive_words, negative_words, stop_words, table_index, latest_year):
    
    if collect_new_data:
        polling_df = parse_html_for_table(url, table_index)
        polling_df.to_csv(path_or_buf = out_dir + '\\' + polling_data_framename)
    else:
        polling_df = pd.DataFrame.from_csv(path = out_dir + '\\' + polling_data_framename)
        
    polling_dates = modify_dates_to_contain_year(polling_df['Date'], latest_year)
    
    for keys in polling_dates.keys():
        polling_df[keys] = polling_dates[keys]
    
    pollsters = set(polling_df['Poll'])
    ##Reuters is most common Pollster
    reuters_df = polling_df[polling_df['Poll'] == 'Reuters/IpsosReuters']
    if collect_new_data:
        request_and_write_google_results(reuters_df, out_dir, num_requests)
    
    if populate_wordcloud:
        build_word_cloud(reuters_df, out_dir, stop_words)
    
    reuters_df['ApprovalChange'] = reuters_df.loc[:,'Approve'].diff().fillna(0)
    reuters_df['ApprovalPosChange'] = (reuters_df.loc[:,'ApprovalChange'] >= 0)
    #reuters_df['SnippetPred'] = 0
    #reuters_df['TitlePred'] = 0
    #temp_df = 
    sentiment_values = predict_approval_rating_change(reuters_df, out_dir, positive_words, negative_words)
    reuters_df['SnippetChange'] = sentiment_values['snippet_words']
    reuters_df['SnippetPosPred'] = (reuters_df.loc[:,'SnippetChange'] >= 0)
    reuters_df['TitleChange'] = sentiment_values['title_words']
    reuters_df['TitlePosPred'] = (reuters_df.loc[:,'TitleChange'] >= 0)
    determine_prediction_accuracy_and_plot(reuters_df, out_dir)
    create_data_report(reuters_df, out_dir)
    return reuters_df #predict_approval_rating_change(reuters_df, out_dir, positive_words, negative_words)

def determine_prediction_accuracy_and_plot(polling_results_df, out_dir):
    polling_results_df['SnippetAccuracy'] = (polling_results_df.loc[:,'SnippetPosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    polling_results_df['TitleAccuracy'] = (polling_results_df.loc[:,'TitlePosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    plot_accuracy_data(polling_results_df, out_dir)
    
def plot_accuracy_data(polling_results_df, out_dir):
    x = [datetime.strptime(d,'%Y-%m-%d').date() for d in polling_results_df['StartDate']]
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    #plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(x,modified_polling_df['TitleAccuracy'])
    plt.gcf().autofmt_xdate()
    plt.title('Using Article Title Prediction Accuracy')
    plt.savefig(out_dir + '//titleaccuracyplot.png', dpi=300)
    plt.plot(x,modified_polling_df['SnippetAccuracy'])
    plt.title('Comparing Title and Snippet Prediction Accuracy')
    plt.savefig(out_dir + '//snippet_and_titleaccuracyplot.png', dpi=300)
    plt.clf()
    plt.title('Using Snippet Prediction Accuracy')
    plt.plot(x,modified_polling_df['SnippetAccuracy'])
    plt.savefig(out_dir + '//snippetaccuracyplot.png', dpi=300)
    
def create_data_report(data,out_dir):
    total_rows,_ = data.shape
    snippet_correct_rows,_ = data[data['SnippetPosPred'] == True].shape
    title_correct_rows,_ = data[data['TitlePosPred'] == True].shape
    new_file = out_dir + '\\' +'output_data_overall_report.txt'
    with open(new_file, 'w') as curr_file:
            curr_file.write('Total_Data_Eval\tTitle_Data_Raw_Correct\tTitle_Data_Accuracy\tSnippet_Data_Raw_Correct\tSnippet_Data_Accuracy\n')
            title_accuracy = (title_correct_rows/total_rows)*100
            snippet_accuracy = (snippet_correct_rows/total_rows)*100
            curr_file.write(str(total_rows) +'\t' + str(title_correct_rows) + '\t' + str(title_accuracy)
                            + '\t' + str(snippet_correct_rows) + '\t' + str(snippet_accuracy))
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
    
    modified_polling_df = Main(my_query, url, out_dir, polling_data_framename, 
                               num_requests, collect_new_data, populate_wordcloud, 
                               positive_words, negative_words, stop_words, table_index, latest_year)

              
    
    ## to read back in the data we write: data = pd.read_csv(filepath, delimiter="\t")
    