# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 19:34:19 2018

@author: mitch
"""

def request_and_write_google_results(poll_df, out_dir, num_requests):
    rows, _ = poll_df.shape
    
    service = build("customsearch", "v1",
                    developerKey=devKey)
    
    for row in range(rows):
        new_file = (out_dir + '\\' + my_query +  reuters_df.iloc[row]['StartDate']+ '_' + reuters_df.iloc[row]['EndDate'] +'.txt')
        ##We should search from the the amount of days the poll lasted prior to the start, through the start
        search_start, search_end = get_search_start_and_end_date(reuters_df.iloc[row]['StartDate'], reuters_df.iloc[row]['EndDate'])
        ##For our purposes, there appear to be 3 important items, the title for each item, the snippet and the link (technically not important)
        with open(new_file, 'w') as curr_file:
            curr_file.write('Link\tTitle\tSnippet\n')
            results = build_google_query(service, my_query, search_start.replace('-',''), search_end.replace('-',''), num_requests)
            for items in results['items']:
                curr_file.write(items['link'] +'\t' + clean_text(items['title']) + '\t' + clean_text(items['snippet']) + '\n')
        '''
        local_requests = num_requests
        with open(new_file, 'w') as curr_file:
            curr_file.write('Link\tTitle\tSnippet\n')
            curr_req_count = 0
            start_req = 1
            while local_requests >= 1:
                curr_req_count += 1
                local_requests -= 1
                if local_requests == 0 or curr_req_count == 10:
                    results = build_google_query(service, my_query, search_start.replace('-',''), search_end.replace('-',''), start_req)
                    start_req += curr_req_count
                    curr_req_count = 0
                    #if we have not found at least 25 results dont try to find more results
                    
                    #When trying to specify finding more than 10 results, sometimes not returning items and crashing
                    if (results['queries']['request'][0]['totalResults'] < 50):
                        print('true')
                        local_requests = 0
                    for items in results['items']:
                        curr_file.write(items['link'] +'\t' + clean_text(items['title']) + '\t' + clean_text(items['snippet']) + '\n
        '''