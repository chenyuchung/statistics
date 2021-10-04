# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:10:40 2019

@author: scs5
"""

import pandas as pd

def FreqTable(dataframe,col,sort=1):
    
    origin = dataframe
    
    df = pd.value_counts(origin[col]).to_frame().reset_index()
    df.columns = [col,'frequency']
    df['percentage(%)'] = ( df['frequency'] / df['frequency'].sum() ) * 100
    
    if   sort == 1: df.sort_values(by=[col],inplace=True)
    elif sort == 2: df.sort_values(by=['frequency'],ascending=False,inplace=True)
    elif sort == 3: df.sort_values(by=['percentage(%)'],ascending=False,inplace=True)
    
    df.reset_index(drop=True,inplace=True)
    
    v = df.last_valid_index()
    df.loc[v+1,df.columns.values] = ['Total',df['frequency'].sum(),df['percentage(%)'].sum()]
    
    return df