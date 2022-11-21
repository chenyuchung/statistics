# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 17:10:55 2022

交叉表製作

@author: user
"""

import pandas as pd

def crosstab_rolling(dataframe,indexName,columnName,weight=None,
                     calculate=None,calculate_col1=None,calculate_col2=None,
                     colmissing=[],
                     colpercent=False):
    
    dfn = dataframe.loc[dataframe[columnName].isin(colmissing)==False].reset_index(drop=True).fillna(99)

    if weight != None:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName],dfn[weight],aggfunc = sum).reset_index().fillna(0)
    

    else:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName]).reset_index()

    
    if dfc[indexName].dtype != 'object':

        dfc[indexName] = dfc[indexName].astype(float).astype(int)

    v = dfc.last_valid_index()
    
    dfc.loc[v+1,indexName] = indexName + '_Total'
    
    yitems = list(dfc.columns.values)
    yitems.remove(indexName)
    
    for i in yitems:
        
        dfc.loc[v+1,i] = dfc.loc[:v,i].sum()

    dfc['N'] = dfc[yitems].sum(axis=1)   
    
    if calculate == None: pass
    
    elif calculate == 'add':
        dfc[calculate] = (dfc[calculate_col1] + dfc[calculate_col2]) / dfc['N']
        
    elif calculate == 'minus':
        dfc[calculate] = (dfc[calculate_col1] - dfc[calculate_col2]) / dfc['N']


    for i in yitems:
               
        dfc[str(int(i))+'%(R)'] = dfc[i] / dfc['N']   #row_percentage, default open
        
    if colpercent==True:
        
        for i in yitems:
        
            dfc[str(int(i))+'%(C)'] = dfc[i] / dfc.loc[v+1,i]  #column_percentage
    
    dfc['Ncopy'] = dfc[yitems].sum(axis=1)
      
    dfc.rename(index=str,columns={indexName:'level'},inplace=True)
    
    return dfc


def main_crosstab_rolling(dataframe,columnName,weight=None,party_type=1,optional_variables=[],colmissing=[],
                  colpercent=False):
    
    if party_type == 1: partyr = ['supporting_partyr']
    elif party_type == 2: partyr = ['supporting_partyrr']
    elif party_type == 0: partyr = []
    
    main_variables = ['gender','agegp2','edugp','edugpr','area','arear','supporting_party']+partyr

    variables = main_variables + optional_variables
    
    crosstables = []
    
    j = 1
    
    for i in variables:
    
        locals()['C'+i] = crosstab_rolling(dataframe,i,columnName,weight,'minus',1,2,colmissing,colpercent)
        
        crosstables.append('C'+i)
    
    main_crosstabale = eval(crosstables[0])
    
    while j < len(crosstables):
        
        main_crosstabale = main_crosstabale.append(eval(crosstables[j]))
        j += 1
        
    return main_crosstabale
        
        
        