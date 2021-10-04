# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:10:40 2019

@author: scs5
"""

import pandas as pd
import math

def n_round(n):
    if n-math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)

def FreqTable(dataframe,col,sort=1,weightList=[],wRound=False):
    
    origin = dataframe
    
    dff = pd.value_counts(origin[col]).to_frame().reset_index()
    dff.columns = [col,'frequency']
    dff['percentage(%)'] = ( dff['frequency'] / dff['frequency'].sum() ) * 100
    
    if   sort == 1: dff.sort_values(by=[col],inplace=True)
    elif sort == 2: dff.sort_values(by=['frequency'],ascending=False,inplace=True)
    elif sort == 3: dff.sort_values(by=['percentage(%)'],ascending=False,inplace=True)
    
    dff.reset_index(drop=True,inplace=True)
        
    v = dff.last_valid_index()
    dff.loc[v+1,dff.columns.values] = ['Total',dff['frequency'].sum(),dff['percentage(%)'].sum()]


    if weightList != []:          
        for i in weightList:
            for j in list(dff[col]):
                dff.loc[dff[col]==j,i] = origin.loc[origin[col]==j,i].sum()
            
            dff.loc[v+1,i] = dff[i].sum()
      
    if wRound==True:
        for i in weightList:
            dff[i] = dff[i].apply(n_round)
    
    return dff