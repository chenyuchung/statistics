# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 17:10:55 2022

交叉表製作

@author: user
"""

import pandas as pd

def crosstab(dataframe,indexName,columnName,weight=None,colmissing=[]):
    
    dfn = dataframe.loc[dataframe[columnName].isin(colmissing)==False].reset_index(drop=True).fillna(0)

    if weight != None:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName],dfn[weight],aggfunc = sum).reset_index().fillna(0)
    

    else:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName]).reset_index()

    dfc[indexName] = dfc[indexName].astype(float).astype(int)

    v = dfc.last_valid_index()
    
    dfc.loc[v+1,indexName] = indexName + '_Total'
    
    yitems = list(dfc.columns.values)
    yitems.remove(indexName)
    
    for i in yitems:
        
        dfc.loc[v+1,i] = dfc.loc[:v,i].sum()

    dfc['Ntemp'] = dfc[yitems].sum(axis=1)    

    for i in yitems:
               
        dfc[str(int(i))+'%'] = dfc[i] / dfc['Ntemp']   #row_percentage
        
        #dfc[str(int(i))+'%'] = dfc[i] / dfc.loc[v+1,i]  #column_percentage
    
    dfc['N'] = dfc[yitems].sum(axis=1)
    
    dfc.drop('Ntemp',axis=1,inplace=True)
    
    dfc.rename(index=str,columns={indexName:'level'},inplace=True)
    
    return dfc

