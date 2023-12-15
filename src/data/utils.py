'''Utility functions used in ExploratoryDataAnalysis.ipynb'''

import copy
import os

import pandas as pd

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
        if category in ['fruit','vegetable','fish']:
            data_copy[category] = dataframe[dataframe['Description'].str.contains(', raw', regex=True, case=False) & ~(dataframe['Description'].str.contains(f'Alaska Native',regex=True))]
        if category == 'cheese':
            data_copy[category] = dataframe[dataframe['Description'].str.contains('^Cheese,',regex=True) & ~(dataframe['Description'].str.contains(f'American',regex=True))]
        if category == 'nut':
            data_copy[category] = dataframe[(dataframe['Description'].str.contains('^Nuts,',regex=True)) & ~(dataframe['Description'].str.contains(f'formulated',regex=True))]
        if category == 'bean':
            data_copy[category] = dataframe[(dataframe['Description'].str.contains('^Beans',regex=True))]
        if category == 'egg':
            data_copy[category] = dataframe[((dataframe['Description'].str.contains("^Egg,",regex=True, case=False)) |
                                (dataframe['Description'].str.contains("^Yogurt,",regex=True, case=False)) |
                                (dataframe['Description'].str.contains("^Milk,",regex=True, case=False))) &
                                ~(dataframe['Description'].str.contains('dried | frozen | human',regex=True, case=False))]
        if category == 'grain':
            data_copy[category] = dataframe[(dataframe['Description'].str.contains('^Wheat',regex=True,case=False)) |
                                (dataframe['Description'].str.contains('^Cornmeal',regex=True,case=False)) |
                                (dataframe['Description'].str.contains('^Noodles',regex=True,case=False)) |
                                (dataframe['Description'].str.contains('^Rice',regex=True,case=False))]
                                
    return data_copy

def save_final_datasets(data, dirpath):
    files = os.listdir(dirpath)
    for category, dataframe in data.items():
        filename = category + '_final' + '.csv'
        if filename not in files:
            dataframe.to_csv(os.path.join(dirpath,filename))