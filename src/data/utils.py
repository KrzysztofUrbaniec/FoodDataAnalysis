'''Utility functions used in ExploratoryDataAnalysis.ipynb'''

import copy
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def load_data(dirpath):
    '''Loads the data from .csv files and saves them in a dictionary with keys corresponding to file names.'''
    dfs = {}
    for filename in os.listdir(dirpath):
        if filename.endswith('.csv'):
            df_name = filename.split('.')[0]
            dfs[df_name] = pd.read_csv(os.path.join(dirpath,filename))
    return dfs

def merge_data(data):
    '''Merges individual dataframes stored in a dictionary into one.'''
    columns = data['fruit'].columns
    final_df = pd.DataFrame(columns=columns)
    for food in data.values():
        final_df = pd.concat([final_df,food],ignore_index=True)
    final_df = final_df.drop_duplicates()
    return final_df

def add_food_type(data):
    '''Adds category to particular products for easier classification and data extraction.'''
    data_copy = copy.copy(data)
    for category, dataframe in data_copy.items():
        dataframe['Category'] = category
    return data_copy

def choose_foods(data):
    '''Extracts only products that meet specific criteria from fetched FDC product/nutrition data.'''
    data_copy = copy.copy(data)
    for category, dataframe in data_copy.items():
        if category == 'fruit':
            data_copy[category] = dataframe[dataframe['Description'].str.contains(', raw|Raisins|, dried|Dates', regex=True, case=False)]
        if category == 'vegetable':
            data_copy[category] = dataframe[dataframe['Description'].str.contains(', raw', regex=True, case=False) &
                                            ~dataframe['Description'].str.contains('Pizza|mixed|macaroni|fruit|Beans', regex=True, case=False)]
    return data_copy

def save_final_datasets(data, dirpath):
    '''Saves processed datasets with _final suffix.'''
    files = os.listdir(dirpath)
    for category, dataframe in data.items():
        filename = category + '_final' + '.csv'
        if filename not in files:
            dataframe.to_csv(os.path.join(dirpath,filename))

def make_distribution_plot(df,type='box',nrows=4,figsize=(8,6)):
    '''Creates a grid of histograms or boxplots displaying distributions of all numerical columns from the dataframe. Returns Axes class instance (subplots).'''
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

def find_unique_food_types(df):
    '''Attempts to find food types based on sample names and FDC's naming convention.'''
    return df['Description'].apply(lambda x: x.split(',')[0]).unique()

def find_IQR_outliers(df):
    '''Finds outliers in numericals columns of the dataframe according to +- 1.5 * IQR rule, commonly used for boxplots.
    Returns a dictionary with keys corresponding to column names and values corresponding to indices of samples from the original dataframe.'''
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
    '''Computes % of dried fruits among outliers in particular nutrient.'''
    data = dict()
    for quantity, indices in outlier_indices.items():
        filtered_df = df.loc[indices]
        n_dried_fruits = len(filtered_df[filtered_df['Description'].str.contains('dried|Rasins')])
        data[quantity] = [n_dried_fruits, np.round((n_dried_fruits/len(filtered_df)) * 100,1)]
    final_df = pd.DataFrame(data).transpose().rename({0:'#Dried',1:'%Dried'},axis=1)
    return final_df

def create_comparison_boxplot(df,columns_to_compare):
    '''Creates a set of boxplots to compare selected nutrients between raw and dried fruits.'''
    df_copy = df.copy()
    columns_to_drop = df_copy.columns.drop(['fruit_type'] + columns_to_compare) 
    df_melted = pd.melt(frame=df_copy.drop(columns_to_drop,axis=1),id_vars='fruit_type',var_name='Nutrient',value_name='Value')
    fig, ax = plt.subplots(figsize=(10,8))
    sns.boxplot(df_melted,x='Nutrient',y='Value',hue='fruit_type',ax=ax)
    ax.legend(title='Type')
    return ax

def find_top_n_percent_of_samples(df,n,drop_cols=None):
    '''Allows to find top n % of samples in the set dataframe's numerical columns, potentially reduced by drop_cols.
    Returns a dictionary with keys corresponding to column names and values corresponding to filtered versions of original dataframe.'''
    results = dict()
    df_copy = df.copy()
    if drop_cols is not None:
        df_copy = df_copy.drop(columns=drop_cols)   
    df_numeric = df_copy.select_dtypes('number')
    
    for column in df_numeric.columns:
        percentile_rank = df[column].rank(pct=True) * 100
        results[column] = df[percentile_rank >= (100-n)].sort_values(by=column,ascending=False)
    return results

def ntile(df, column, n, reverse_rank=False):
    '''Divides a set of values into n approximately equal parts and assigns successive ranks to each part.
    Analogous to SQL's NTILE(n) function. Highest values are ranked with 1 if reverse_rank=False.'''
    
    values = df[column].sort_values(ascending=False)
    nan_mask = values.isna()
    nan_count = nan_mask.sum()
    
    # Calculate bin sizes 
    total_values = len(values) - nan_count
    bin_sizes = np.full(n, total_values // n) # Create n bins of equal sizes
    bin_sizes[:total_values % n] += 1 # Distribute the remainder evenly between the bins
    
    if reverse_rank is False:
        bins = np.concatenate([np.full(size, i + 1) for i, size in enumerate(bin_sizes)])
    else:
        bins = np.concatenate([np.full(size, n - i) for i, size in enumerate(bin_sizes)])

    lowest_rank = bins.max() if reverse_rank is False else 1
    
    ranks = pd.Series(np.nan, index=values.index) # Create Series initially full of NaNs
    ranks[~nan_mask] = bins[:total_values]  # Assign ranks to non-NaN values
    ranks[nan_mask] = lowest_rank # Always set lowest rank for NaN values
    
    return ranks.astype(int)