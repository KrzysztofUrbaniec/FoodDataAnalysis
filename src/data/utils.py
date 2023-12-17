'''Utility functions used in ExploratoryDataAnalysis.ipynb'''

import copy
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def load_data(dirpath):
    dfs = {}
    for filename in os.listdir(dirpath):
        if filename.endswith('.csv'):
            df_name = filename.split('.')[0]
            dfs[df_name] = pd.read_csv(os.path.join(dirpath,filename))
    return dfs

def merge_data(data):
    columns = data['fruit'].columns
    final_df = pd.DataFrame(columns=columns)
    for food in data.values():
        final_df = pd.concat([final_df,food],ignore_index=True)
    final_df = final_df.drop_duplicates()
    return final_df

def add_food_type(data):
    data_copy = copy.copy(data)
    for category, dataframe in data_copy.items():
        dataframe['Category'] = category
    return data_copy

def choose_foods(data):
    data_copy = copy.copy(data)
    for category, dataframe in data_copy.items():
        if category == 'fruit':
            data_copy[category] = dataframe[dataframe['Description'].str.contains(', raw|Raisins|, dried|Dates', regex=True, case=False)]
        if category == 'vegetable':
            data_copy[category] = dataframe[dataframe['Description'].str.contains(', raw', regex=True, case=False) &
                                            ~dataframe['Description'].str.contains('Pizza|mixed|macaroni', regex=True, case=False)]
    return data_copy

def save_final_datasets(data, dirpath):
    files = os.listdir(dirpath)
    for category, dataframe in data.items():
        filename = category + '_final' + '.csv'
        if filename not in files:
            dataframe.to_csv(os.path.join(dirpath,filename))

def make_distribution_plot(df,type='box',nrows=4,figsize=(8,6)):
    df_numeric = df.select_dtypes('number')
    ncols = int(np.ceil(len(df_numeric.columns) / nrows))
    fig, ax = plt.subplots(figsize=figsize,ncols=ncols,nrows=nrows)
    for i,axes in enumerate(ax.flatten()):
        if i < len(df_numeric.columns):
            if type == 'box':
                sns.boxplot(data=df_numeric,y=df_numeric.columns[i],ax=axes)
                axes.set_xticks([])
            if type == 'hist':
                sns.histplot(data=df_numeric,x=df_numeric.columns[i],ax=axes)
        else:
            axes.axis('off')
    fig.tight_layout()
    return ax

def find_IQR_outliers(df):
    outlier_indices = dict()
    df_numeric = df.select_dtypes('number')
    for quantity in df_numeric.columns:
        q1 = df_numeric[quantity].quantile(0.25)
        q3 = df_numeric[quantity].quantile(0.75)
        IQR = q3 - q1
        lower_bound = q1 - 1.5 * IQR
        upper_bound = q3 + 1.5 * IQR
        outlier_indices[quantity] = df[(df[quantity] < lower_bound) | (df[quantity] > upper_bound)].index
    return outlier_indices

def count_outlier_dried_fruits(df,outlier_indices):
    data = dict()
    for quantity, indices in outlier_indices.items():
        filtered_df = df.loc[indices]
        n_dried_fruits = len(filtered_df[filtered_df['Description'].str.contains('dried|Rasins')])
        data[quantity] = [n_dried_fruits, np.round((n_dried_fruits/len(filtered_df)) * 100,1)]
    final_df = pd.DataFrame(data).transpose().rename({0:'#Dried',1:'%Dried'},axis=1)
    return final_df

def find_top_n_percent_of_samples(df,n,drop_cols=None):
    results = dict()
    df_copy = df.copy()
    if drop_cols is not None:
        df_copy = df_copy.drop(columns=drop_cols)   
    df_numeric = df_copy.select_dtypes('number')
    
    for column in df_numeric.columns:
        percentile_rank = df[column].rank(pct=True) * 100
        results[column] = df[percentile_rank >= (100-n)]
    return results