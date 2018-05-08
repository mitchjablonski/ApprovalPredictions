# -*- coding: utf-8 -*-
"""
Created on Mon Apr 16 19:27:46 2018

@author: mitch
"""
from __future__ import division
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
import seaborn as sns

def determine_prediction_accuracy_and_plot(polling_results_df, out_dir):
    polling_results_df['SnippetAccuracy'] = (polling_results_df.loc[:,'SnippetPosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    polling_results_df['TitleAccuracy'] = (polling_results_df.loc[:,'TitlePosPred'] == polling_results_df.loc[:,'ApprovalPosChange'])
    polling_results_df['SnippetAccuracyAuto'] = (polling_results_df.loc[:,'SnippetPosPredAuto'] == polling_results_df.loc[:,'ApprovalPosChange'])
    polling_results_df['TitleAccuracyAuto'] = (polling_results_df.loc[:,'TitlePosPredAuto'] == polling_results_df.loc[:,'ApprovalPosChange'])
    snippet_col_acc = 'SnippetAccuracy'
    snippet_col_pred = 'SnippetPosPred'
    title_col_acc = 'TitleAccuracy'
    title_col_pred = 'TitlePosPred'
    pred_type = 'Manual'
    plot_accuracy_data(polling_results_df, out_dir, snippet_col_acc, snippet_col_pred, title_col_acc, title_col_pred, pred_type)
    snippet_col_acc = 'SnippetAccuracyAuto'
    snippet_col_pred = 'SnippetPosPredAuto'
    title_col_acc = 'TitleAccuracyAuto'
    title_col_pred = 'TitlePosPredAuto'
    pred_type = 'Auto'
    plot_accuracy_data(polling_results_df, out_dir, snippet_col_acc, snippet_col_pred, title_col_acc, title_col_pred, pred_type)
    
def plot_accuracy_data(polling_results_df, out_dir, snippet_col_acc, snippet_col_pred, title_col_acc, title_col_pred, pred_type):

    x = [datetime.strptime(d,'%Y-%m-%d').date() for d in polling_results_df['StartDate']]
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m/%d/%Y'))
    #plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    plt.plot(x,polling_results_df[title_col_acc], label = 'Title Change')
    plt.gcf().autofmt_xdate()
    plt.title('Using Article Title Predicted Change {}'.format(pred_type))
    plt.plot(x,polling_results_df['ApprovalPosChange'], label = 'Actual Change')
    leg = plt.legend(loc = 2)
    leg.get_frame().set_alpha(0.1)
    plt.savefig(out_dir + '//titleaccuracyplot{}.png'.format(pred_type.lower()), dpi=300)
    
    plt.clf()
    plt.plot(x,polling_results_df[title_col_acc], label = 'Title Change')
    plt.gcf().autofmt_xdate()
    plt.plot(x,polling_results_df[snippet_col_acc], label = 'Snippet Change')
    plt.title('Comparing Title and Snippet Predicted Changes {}'.format(pred_type.lower()))
    leg = plt.legend(loc = 2)
    leg.get_frame().set_alpha(0.1)
    plt.savefig(out_dir + '//snippet_and_titleaccuracyplot{}.png'.format(pred_type), dpi=300)
    
    plt.clf()
    plt.title('Using Snippet Predicted Change')
    plt.plot(x,polling_results_df[snippet_col_acc])
    plt.plot(x,polling_results_df['ApprovalPosChange'], label = 'Actual Change')
    leg = plt.legend(loc = 2)
    leg.get_frame().set_alpha(0.1)
    plt.savefig(out_dir + '//snippetaccuracyplot{}.png'.format(pred_type.lower()), dpi=300)

    plot_cols = [[snippet_col_acc, snippet_col_pred, 'Snippet'], [title_col_acc, title_col_pred, 'Title']]

    actual_pos_weeks,_ = polling_results_df.loc[polling_results_df['ApprovalPosChange'] == True].shape
    total_weeks, _ = polling_results_df.shape
    actual_neg_weeks = total_weeks - actual_pos_weeks

    for cols in plot_cols:
        plt.clf()
        fig, ax = plt.subplots()
        bar_width = 0.35
        opacity = 0.8
        n_groups = 3
        index = np.arange(n_groups)

        correct_weeks,_ = polling_results_df.loc[polling_results_df[cols[0]] == True].shape
        pred_pos_weeks,_ = polling_results_df.loc[polling_results_df[cols[1]] == True].shape
        pred_neg_weeks = total_weeks - pred_pos_weeks

        pred_data = (correct_weeks, pred_pos_weeks, pred_neg_weeks)
        actual_data = (total_weeks, actual_pos_weeks, actual_neg_weeks)

        rects1 = plt.bar(index + bar_width, actual_data, bar_width,
                         alpha=opacity,
                         color='g',
                         label='Actual Data')

        rects2 = plt.bar(index, pred_data, bar_width,
                        alpha=opacity,
                        color='b',
                        label='Predicted {} Data'.format(cols[2]))
        #plt.xlabel('')
        plt.ylabel('Weeks')
        plt.title('{} Prediction {} vs Actuals'.format(pred_type, cols[2]))
        plt.xticks(index + bar_width/2, ('Total Weeks Correct', 'Positive Weeks', 'Negative Weeks'))
        plt.legend()

        plt.tight_layout()
        plt.savefig(out_dir + '//bargraph{}{}.png'.format(pred_type, cols[2]))
        plt.clf()


    
def create_data_report(data, out_dir, acc_score, snippet_col, title_col, pred_type):
    total_rows,_ = data.shape
    pos_weeks,_ = data.loc[data['ApprovalPosChange'] == True].shape
    neg_weeks = total_rows - pos_weeks
    snippet_correct_rows,_ = data.loc[data[snippet_col] == True].shape
    title_correct_rows,_ = data.loc[data[title_col] == True].shape
    new_file = out_dir + '\\' +'output_data_overall_report{}.txt'.format(pred_type)
    with open(new_file, 'w') as curr_file:
            curr_file.write('Total_Data_Eval\tTotal_Pos_Weeks\tTotal_Neg_weeks\tTitle_Data_Raw_Correct\tTitle_Data_Accuracy\tSnippet_Data_Raw_Correct\tSnippet_Data_Accuracy\tTestTrainSplitAccuracyScore\n')
            title_accuracy = (title_correct_rows/total_rows)*100
            snippet_accuracy = (snippet_correct_rows/total_rows)*100
            curr_file.write(str(total_rows) + '\t' + str(pos_weeks) +'\t' + str(neg_weeks)  +'\t' + str(title_correct_rows) + '\t' + str(title_accuracy)
                            + '\t' + str(snippet_correct_rows) + '\t' + str(snippet_accuracy) + '\t' + str(acc_score))


def run_post_processing(polling_results_df, out_dir, acc_score):
    determine_prediction_accuracy_and_plot(polling_results_df, out_dir)
    '''
    snippet_col = 'SnippetPosPred'
    title_col = 'TitlePosPred'
    '''
    snippet_col = 'SnippetAccuracy'
    title_col = 'TitleAccuracy'
    pred_type = '_manual'
    create_data_report(polling_results_df, out_dir, acc_score, snippet_col, title_col, pred_type)
    '''
    snippet_col = 'SnippetPosPredAuto'
    title_col = 'TitlePosPredAuto'
    '''
    snippet_col = 'SnippetAccuracyAuto'
    title_col = 'TitleAccuracyAuto'
    pred_type = '_auto'
    create_data_report(polling_results_df, out_dir, acc_score, snippet_col, title_col, pred_type)