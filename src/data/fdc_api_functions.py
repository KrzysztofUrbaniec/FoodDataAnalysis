'''
The module contains functions for fetching FDC data
'''

import re
import os

import numpy as np
import pandas as pd
import requests

def fetch_fdc_data(query: str, api_key: str, data_type: str='Foundation',page_size: int=50,page_number: int=1) -> requests.models.Response:
    '''
    Fetch single page of data from FoodData Central acquired after applying a query.
    
    Args:
        query: query passed to FDC API
        api_key: unique API key required for API request
        data_type: one of four basic data types provided by FDC. Allowed values: Foundation, Branded, Survey (FNDDS), SR Legacy
        page_size: number of results per page
        page_number: number of page to fetch
    
    Return: 
        requests.models.Response: fetched data in json format
    '''
    
    base_url = 'https://api.nal.usda.gov/fdc/v1'
    search_endpoint = '/foods/search'
    
    url_search = f'{base_url}{search_endpoint}?api_key={api_key}&query={query}&dataType={data_type}&pageSize={page_size}&pageNumber={page_number}'
    response = requests.get(url_search)
    return response.json()

def fetch_all(query: str,api_key: str,nutrients_list: list,data_type: str='Foundation',page_size: int=50,start_page: int=1,page_limit: int=None) -> pd.DataFrame:
    '''
    Fetch all available data from FDC database for given query.
    
    Args:
        query: query passed to FDC API
        api_key: unique API key required for API request
        data_type: one of four basic data types provided by FDC. Allowed values: Foundation, Branded, Survey (FNDDS), SR Legacy
        page_size: number of results per page
        start_page: first page to fetch
        page_limit: last page to fetch
    
    Return: 
        pd.DataFrame: fetched data
    '''
    
    # Fetch start_page and retrieve basic info about the query
    foods = fetch_fdc_data(query=query,api_key=api_key,data_type=data_type,page_number=start_page,page_size=page_size)
    df = get_food_info(foods,nutrients_list)
    total_pages = foods['totalPages']
    hit_threshold = 500
    
    # Fetch all pages if page_limit is not specified
    if page_limit is None:
        page_limit = total_pages
        
    total_hits = (page_limit - start_page) * page_size
    
    # Warning if user tries to fetch very large number of entries
    if  total_hits > hit_threshold:
        decision = input(f'WARNING: This query will potentially result in page size ({page_size}) * number of pages ({page_limit - start_page}) = {total_hits} total hits. Do you want to continue? (Y/N): ')
        
        if decision not in ['Y','y']:
            return None        
    
    for i in range(start_page+1,page_limit+1):
        foods = fetch_fdc_data(query=query,api_key=api_key,data_type=data_type,page_number=i)
        df_new = get_food_info(foods,nutrients_list)
        df = pd.concat([df,df_new],ignore_index=True)
    
    return df

def get_nutrients(food_entry: dict) -> dict:
    '''
    Get nutrient-value pairs for specific food.
    Important: for some foods there are two values of energy (corresponding to Atwater General and Specific
    Factors). Only those for General Factors are included in the final dictionary. Also, in some cases the energy is expressed
    both in kcal and kJ. Only values expressed in kcal are included.
    
    Args:
        food_entry: dictionary corresponding to a single food sample obtained from FDC database
    
    Return:
        dict: nutrient-value pairs
    '''
    
    nutrients = dict()
    energy_pattern = re.compile(r'\bEnergy\b')
    
    # Populate dictionary of nutirents for given food
    for nutrient in food_entry['foodNutrients']:        
        if not energy_pattern.match(nutrient['nutrientName']):
            nutrients[nutrient['nutrientName']] = nutrient.get('value',np.nan)
            
        if nutrient.get('nutrientName', '').strip() == 'Energy (Atwater General Factors)' and nutrient.get('unitName', '') == 'KCAL':
            nutrients['Energy'] = np.round(nutrient.get('value',np.nan))
        elif nutrient.get('nutrientName', '').split()[0] == 'Energy' and \
            len(nutrient.get('nutrientName', '').strip().split()) == 1 and \
            nutrient.get('unitName', '') == 'KCAL': 
            nutrients['Energy'] = np.round(nutrient.get('value',np.nan))
    
    if 'Energy' not in nutrients:
        nutrients['Energy'] = np.nan
    
    return nutrients
    
def _create_description_columns(foods):
    description_columns = ['Description']
    if 'Survey (FNDDS)' in foods['foodSearchCriteria']['dataType']:
        description_columns += ['Additional description']
    if 'Branded' in foods['foodSearchCriteria']['dataType']:
        description_columns += ['Food category','Brand owner','Brand name']
    return description_columns

def _fill_description_columns(foods,food,filtered_nutrient_list):
    filtered_nutrient_list['Description'] = food['description']
    if 'Survey (FNDDS)' in foods['foodSearchCriteria']['dataType']:
        filtered_nutrient_list['Additional description'] = food.get('additionalDescriptions',np.nan)
    if 'Branded' in foods['foodSearchCriteria']['dataType']:
        filtered_nutrient_list['Food category'] = food.get('foodCategory',np.nan)
        filtered_nutrient_list['Brand owner'] = food.get('brandOwner',np.nan)
        filtered_nutrient_list['Brand name'] = food.get('brandName',np.nan)
    return filtered_nutrient_list

def get_food_info(foods: dict, nutrients_list: list) -> pd.DataFrame:
    '''
    Convert FDC json data to pandas DataFrame containing foods with selected nutrients

    Args:
        foods: json data fetched from FDC 
        nutrients_list: list of nutrients to include in the final DataFrame. Nutrient names have to be the same as those provided by FDC.

    Return:
        pd.DataFrame: food descriptions and selected nutrients
    '''

    # Specify, which columns describing food samples should be included, based on the data type in the query result
    description_columns = _create_description_columns(foods)
        
    data = []
    for food in foods['foods']:
        # Get nutrients for each food and store them for DataFrame creation
        nutrients = get_nutrients(food)
        filtered_nutrients = {nutrient: value for nutrient, value in nutrients.items() if nutrient in nutrients_list}
        filtered_nutrients = _fill_description_columns(foods,food,filtered_nutrients)
        data.append(filtered_nutrients)

    df = pd.DataFrame(data,columns=description_columns + nutrients_list)

    return df

