# -*- coding: utf-8 -*-
"""
Created on Sat Apr 07 09:58:31 2018

@author: mitch
"""
##referenced https://henryhungle.wordpress.com/2016/08/05/python-predicting-us-presidential-election/ for similar parsing
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
#from collections import defaultdict


content = urllib2.urlopen("https://www.realclearpolitics.com/epolls/other/president_trump_job_approval-6179.html")
soup = BeautifulSoup(content,'html.parser')
#print(soup)
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

#pollingDict = defaultdict(list)
#for currData in pollingData:
#    if currData != []:
#        for currNum, currHeader in enumerate(pollingHeaders):
#            pollingDict[currHeader].append(currData[currNum])
#pollingDF = pd.DataFrame(data=None, columns=pollingHeaders)
#
#for headers in pollingHeaders:
#    pollingDF[headers] = pollingDict[headers]
def ConvertToTwoDigitDate(currDate):
    newDate = currDate
    if (int(currDate) < 10):
        '0' + currDate
    return newDate

def ConvertToDesiredFormat(year, month, day):
    return (year +'-' + month + '-' + day)

def GenerateGoogleFormatDate(year, monthAndDay):
    ##Google expects that months and days have two digits, 
    ##convert them if they arent
    newMonth = ConvertToTwoDigitDate(monthAndDay[0])
    newDay   = ConvertToTwoDigitDate(monthAndDay[1])
    return ConvertToDesiredFormat(year, newMonth, newDay)
    
def ModifyDatesForYear(dateData):
    dateDF = pd.DataFrame(data=None, columns = ['StartDate', 'EndDate'])
    pollingDates = defaultdict(list)
    currYear = '2018'
    startDateLastYear = False
    endDateLastYear = False
    ##Desired format YYYY-MM-DD
    for dates in dateData:
        dateList = dates.split()
        dateList = [dateList[0], dateList[2]]
        #item 1 in our dateList is our start poll, 2 is our end poll
        for currNum, monthDay in enumerate(dateList):
            ##item Last Year
            if currNum == 1 & int(monthDay[0]) == 12:
                tempYear = str(int(currYear) -1)
                monthDay = monthDay.split('/')
                newDate = GenerateGoogleFormatDate(tempYear, monthDay)
                #newMonth = ConvertToTwoDigitDate(currItem[0])
                #newDay   = ConvertToTwoDigitDate(currItem[1])
                #newDate = ConvertToDesiredFormat(tempYear, newMonth, newDay)
                pollingDates['StartDate'].append(newDate)
                startDateLastYear = True
            elif currNum == 2 & int(monthDay[0]) == 12:
                tempYear = str(int(currYear) -1)
                monthDay = monthDay.split('/')
                newDate = GenerateGoogleFormatDate(tempYear, monthDay)
                pollingDates['EndDate'].append(newDate)
                endDateLastYear = True
            if startDateLastYear & endDateLastYear:
                currYear = str(int(currYear) - 1)
            
        
        '''
        ##We went back a year
        if (int(dateList[0][0]) == 12 & int(dateList[1][0] == 12)):
            currYear = str(int(currYear) - 1)
            
        if (int(dateList[0][0]) <= 12 & int(dateList[1][0]) == 1):
            currYear = '2017'
        elif (int(dateList[0][0]) <= 12 & int(dateList[1][0]) <= 12):
            pass
        '''
        
        