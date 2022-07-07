# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 15:53:36 2022

one-way anova

@author: user
"""

import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

def onewayANOVA(dataframe,IV,DV,IVmissing=[],DVmissing=[]):
    
    data = (dataframe.loc[(dataframe[IV].isin(IVmissing)==False) 
                          & (dataframe[IV].notnull())
                          & (dataframe[DV].isin(DVmissing)==False)
                          & (dataframe[DV].notnull())
                          ].reset_index(drop=True)
            )
            
    model = ols('eval(DV) ~ C(eval(IV))', data = data).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    
    anova_table.index = ['C('+IV+')','Residual']
    
    return anova_table
    

