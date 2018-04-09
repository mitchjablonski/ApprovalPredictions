# -*- coding: utf-8 -*-
"""
Created on Sat Apr 07 09:58:31 2018

@author: mitch
"""

import urllib2
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict


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
pollingDict = defaultdict(list)
for row in rows:
    tds = row.find_all("td")    
    pollingData.append([(str(t.get_text())) for t in tds[:]])

for currData in pollingData:
    if currData != []:
        for currNum, currHeader in enumerate(pollingHeaders):
            pollingDict[currHeader].append(currData[currNum])
pollingDF = pd.DataFrame(data=None, columns=pollingHeaders)

for headers in pollingHeaders:
    pollingDF[headers] = pollingDict[headers]
