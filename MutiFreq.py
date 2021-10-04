# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 11:22:15 2020

題組題次數分配表

@author: scs5
"""

import pandas as pd

def MutiFreq(DataFrame):

    df = DataFrame
    
    variables = []
    new = '1'
    
    while new != '0':
        
        new = input('請輸入變數(如已無請輸入0)：')
        if new != '0': variables.append(new)
    
    out = pd.value_counts(df[variables[0]]).to_frame().reset_index()
    out.columns = [variables[0],variables[0]+'_frequency']
    out[ variables[0]+'_percentage(%)'] = ( out[variables[0]+'_frequency'] / out[variables[0]+'_frequency'].sum() ) * 100
    out.sort_values(by=variables[0],inplace=True)
    out.reset_index(drop=True,inplace=True)
    
    out.rename(index=str,columns={variables[0]:'values'},inplace=True)
    out.set_index('values',inplace=True)
    
    for i in variables[1:]:
        
        temp = pd.value_counts(df[i]).to_frame().reset_index()
        temp.columns = [i,i+'_frequency']
        temp[i+'_percentage(%)'] = ( temp[i+'_frequency'] / temp[i+'_frequency'].sum() ) * 100
        temp.rename(index=str,columns={i:'values'},inplace=True)
        temp.set_index('values',inplace=True)
        
        out = pd.merge(out,temp,how='outer',left_index=True, right_index=True)
    
    out.fillna(0,inplace=True)
    
    freq = [str(i)+'_freq' for i in variables]
    out[freq] = out[freq].astype(int)
    
    return out
    
    

"""
#欄位名稱短版

def MutiFreq(DataFrame):

    df = DataFrame
    
    variables = []
    new = '1'
    
    while new != '0':
        
        new = input('請輸入變數(如已無請輸入0)：')
        if new != '0': variables.append(new)
    
    out = pd.value_counts(df[variables[0]]).to_frame().reset_index()
    out.columns = [variables[0],variables[0]+'_freq']
    out[ variables[0]+'_%'] = ( out[variables[0]+'_freq'] / out[variables[0]+'_freq'].sum() ) * 100
    out.sort_values(by=variables[0],inplace=True)
    out.reset_index(drop=True,inplace=True)
    
    out.rename(index=str,columns={variables[0]:'values'},inplace=True)
    out.set_index('values',inplace=True)
    
    for i in variables[1:]:
        
        temp = pd.value_counts(df[i]).to_frame().reset_index()
        temp.columns = [i,i+'_freq']
        temp[i+'_%'] = ( temp[i+'_freq'] / temp[i+'_freq'].sum() ) * 100
        temp.rename(index=str,columns={i:'values'},inplace=True)
        temp.set_index('values',inplace=True)
        
        out = pd.merge(out,temp,how='outer',left_index=True, right_index=True)

    out.fillna(0,inplace=True)
    
    freq = [str(i)+'_freq' for i in variables]
    out[freq] = out[freq].astype(int)
    
    
    return out



"""



