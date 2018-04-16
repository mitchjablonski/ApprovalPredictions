# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 19:27:46 2018

@author: mitch
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def determine_prediction_accuracy_and_plot(polling_results_df, out_dir):
    polling_results_df['SnippetAccuracy'] = (polling_results_df.loc[:,'SnippetPosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    polling_results_df['TitleAccuracy'] = (polling_results_df.loc[:,'TitlePosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    plot_accuracy_data(polling_results_df, out_dir)
    
def plot_accuracy_data(polling_results_df, out_dir):
    x = [datetime.strptime(d,'%Y-%m-%d').date() for d in polling_results_df['StartDate']]
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    #plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(x,polling_results_df['TitleAccuracy'], label = 'Title Accuracy')
    plt.gcf().autofmt_xdate()
    plt.title('Using Article Title Prediction Accuracy')
    plt.savefig(out_dir + '//titleaccuracyplot.png', dpi=300)
    plt.plot(x,polling_results_df['SnippetAccuracy'], label = 'Snippet Accuracy')
    plt.title('Comparing Title and Snippet Prediction Accuracy')
    leg = plt.legend(loc = 2)
    leg.get_frame().set_alpha(0.1)
    plt.savefig(out_dir + '//snippet_and_titleaccuracyplot.png', dpi=300)
    plt.clf()
    plt.title('Using Snippet Prediction Accuracy')
    plt.plot(x,polling_results_df['SnippetAccuracy'])
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


def run_post_processing(polling_results_df, out_dir):
    determine_prediction_accuracy_and_plot(polling_results_df, out_dir)
    create_data_report(polling_results_df, out_dir)