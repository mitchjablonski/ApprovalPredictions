# -*- coding: utf-8 -*-
"""
Created on Sat Apr 07 09:58:31 2018

@author: mitch
"""
##referenced https://henryhungle.wordpress.com/2016/08/05/python-predicting-us-presidential-election/ for similar parsing
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict

def ConvertToTwoDigitDate(currDate):
    newDate = currDate
    if (int(currDate) < 10):
        newDate = '0' + currDate
    return newDate

def ConvertToDesiredFormat(year, month, day):
    return (year +'-' + month + '-' + day)

def GenerateGoogleFormatDate(year, monthAndDay):
    ##Google expects that months and days have two digits, 
    ##convert them if they arent
    newMonth = ConvertToTwoDigitDate(monthAndDay[0])
    newDay   = ConvertToTwoDigitDate(monthAndDay[1])
    return ConvertToDesiredFormat(year, newMonth, newDay)
    
def ModifyDatesForYear(dateData, latestYear):
    pollingDates = defaultdict(list)
    currYear = latestYear
    startDateLastYear = False
    endDateLastYear = False
    yearModified    = False
    ##Desired format YYYY-MM-DD
    for dates in dateData:
        dateList = dates.split()
        dateList = [dateList[0], dateList[2]]
        #item 1 in our dateList is our start poll, 2 is our end poll
        for currNum, monthDay in enumerate(dateList):
            monthDay = monthDay.split('/')
            tempYear = currYear
            ##item Last Year
            if int(monthDay[0]) == 12 and yearModified == False:
                tempYear = str(int(currYear) -1)
                if currNum == 0:
                    startDateLastYear = True
                else:
                    endDateLastYear = True
                    
            newDate = GenerateGoogleFormatDate(tempYear, monthDay)
            if currNum == 0:
                pollingDates['StartDate'].append(newDate)
            else:
                pollingDates['EndDate'].append(newDate)
                
            if startDateLastYear and endDateLastYear:
                currYear = str(int(currYear) - 1)
                yearModified = True
                startDateLastYear = False
                endDateLastYear = False
        ##We are no longer in december, we can go back another year next time
        ##we reach december
        startMonth = dateList[0].split('/')
        endMonth   = dateList[1].split('/')
        if (int(startMonth[0]) == 11 and int(endMonth[0]) == 11):
            yearModified = False
    return pollingDates

if __name__ == "__main__":
    content = urllib2.urlopen("https://www.realclearpolitics.com/epolls/other/president_trump_job_approval-6179.html")
    soup = BeautifulSoup(content,'html.parser')
    tables = soup.findAll('table', {'class': 'data'})
    
    ##1st table in page index 0 is only recent polls, 2nd table index 1 is all data.
    table = tables[1]
    
    rows = [row for row in table.find_all("tr")]
    columns = [str(col.get_text()) for col in rows[0].find_all("th")]
    pollingHeaders = [column.split('(')[0].strip() for column in columns[:]]
    
    pollingData = []
    for row in rows:
        tds = row.find_all("td")    
        pollingData.append([(str(t.get_text())) for t in tds[:]])
    
    pollingDF = pd.DataFrame(data = pollingData[1:], columns = pollingHeaders)
    
    latestYear = '2018'
    pollingDates = ModifyDatesForYear(pollingDF['Date'], latestYear)
    
    for keys in pollingDates.keys():
        pollingDF[keys] = pollingDates[keys]
    