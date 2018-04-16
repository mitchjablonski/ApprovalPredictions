# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 19:51:40 2018

@author: mitch
"""
import urllib2
from bs4 import BeautifulSoup
from collections import defaultdict
import pandas as pd

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

def convert_to_two_digit_date(curr_date):
    new_date = curr_date
    if (int(curr_date) < 10):
        new_date = '0' + curr_date
    return new_date

def convert_to_desired_date_format(year, month, day):
    return (year +'-' + month + '-' + day)
    
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