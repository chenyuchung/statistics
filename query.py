# -*- coding: utf-8 -*-
"""
Created on Wed Sep  2 10:39:20 2020

@author: scs5
"""

import pandas as pd

def query(idn,item,dataframe=df,col='id'):
    
    return dataframe.loc[dataframe[col]==idn,item]
