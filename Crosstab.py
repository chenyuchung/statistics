# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 17:10:55 2022

交叉表製作

@author: user
"""

import pandas as pd

def crosstab(dataframe,indexName,columnName,weight=None,colmissing=[],colpercent=False):
    
    dfn = dataframe.loc[dataframe[columnName].isin(colmissing)==False].reset_index(drop=True).fillna(99)

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
               
        dfc[str(int(i))+'%(R)'] = dfc[i] / dfc['Ntemp']   #row_percentage, default open
        
    if colpercent==True:
        
        for i in yitems:
        
            dfc[str(int(i))+'%(C)'] = dfc[i] / dfc.loc[v+1,i]  #column_percentage
    
    dfc['N'] = dfc[yitems].sum(axis=1)
    
    dfc.drop('Ntemp',axis=1,inplace=True)
    
    dfc.rename(index=str,columns={indexName:'level'},inplace=True)
    
    return dfc


def main_crosstab(dataframe,columnName,weight=None,party_type=1,optional_variables=[],colmissing=[],
                  colpercent=False,customer=None):
    
    if party_type == 1: partyr = ['supporting_partyr']
    elif party_type == 2: partyr = ['supporting_partyrr']
    elif party_type == 0: partyr = []
    
    if customer == 'TPOF':
        
        main_variables = ['gender','agegp','edugp','area','supporting_party']
        
    elif customer == 'TPOF2':
        
        main_variables = ['gender','agegp','edugp','supporting_party']
        
    else:
        main_variables = ['gender','agegp','edugp','edugpr','area','supporting_party']+partyr

    variables = main_variables + optional_variables
    
    crosstables = []
    
    j = 1
    
    for i in variables:
    
        locals()['C'+i] = crosstab(dataframe,i,columnName,weight,colmissing,colpercent)
        
        crosstables.append('C'+i)
    
    main_crosstabale = eval(crosstables[0])
    
    while j < len(crosstables):
        
        main_crosstabale = main_crosstabale.append(eval(crosstables[j]))
        j += 1
        
    return main_crosstabale
        
        
        