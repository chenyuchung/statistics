# -*- coding: utf-8 -*-
"""
Created on Sun May 12 18:46:28 2024

@author: user
"""

import pandas as pd

def avg_calculator(dataframe,col,weight=None,missing=[]):
    
    dfn = dataframe.loc[(dataframe[col].isin(missing)==False) & (dataframe[col].notnull())].reset_index(drop=True)
    
    if weight == None:
        
        avgN = dfn[col].mean()
        
    else:
        
        dfn['weighted'] = dfn[col] * dfn[weight]
        avgN = dfn['weighted'].sum() / dfn[weight].sum()
        
    return avgN