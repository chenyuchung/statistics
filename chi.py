# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 18:44:25 2024

@author: user
"""

import pandas as pd
import scipy
import math

def n_round(n):
    if n-math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)

def chi_square_table(dataframe,var,exp_var_front,input_col=[]):
    
    total_len = len(dataframe)
    
    tb = dataframe.groupby([var]).sum()
    tb = tb[input_col]
    for i in tb.index.values.tolist():
        tb.loc[i,'counts'] = int( len(dataframe.loc[dataframe[var]==i]) )
        tb.loc[i,'exp']    = n_round( total_len * eval(exp_var_front+str(int(i))) )
        
    return tb