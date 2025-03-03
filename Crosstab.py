# -*- coding: utf-8 -*-
"""
Created on Thu Mar 17 17:10:55 2022

交叉表製作

@author: user
"""

import pandas as pd

def sum_columns(dataframe,new_col_name,sum_cols):
    
    dataframe[new_col_name] = dataframe[sum_cols].sum(axis=1)
    

def crosstab(dataframe,indexName,columnName,weight=None,colmissing=[],colpercent=False,
             sum_col={},column_sort='accending'):
    
    dfn = dataframe.loc[dataframe[columnName].isin(colmissing)==False].reset_index(drop=True).fillna(99)

    if weight != None:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName],dfn[weight],aggfunc = sum).reset_index().fillna(0)
    

    else:
        dfc = pd.crosstab(dfn[indexName],dfn[columnName]).reset_index()

    dfc[indexName] = dfc[indexName].astype(float).astype(int)

    #複選題選項順序調整
    if column_sort == 'descending_muti':
        
        ori_order = list(dfc.columns.values)
        
        if 1 not in ori_order or 0 not in ori_order:
            pass
        
        else:
            m,n = ori_order.index(0),ori_order.index(1)
            ori_order[m],ori_order[n] = ori_order[n],ori_order[m]
        
            dfc = dfc[ori_order]


   #新增總計欄位

    v = dfc.last_valid_index()
    
    dfc.loc[v+1,indexName] = indexName + '_Total'
    
   
    yitems = list(dfc.columns.values)
    yitems.remove(indexName)
    
    for i in yitems:
        
        dfc.loc[v+1,i] = dfc.loc[:v,i].sum()

    dfc['Ntemp'] = dfc[yitems].sum(axis=1)    


    #column sum
    if sum_col != {}:
        
        for i in sum_col:
            
            col_order2 = list(dfc.columns.values)
            dfc[i] = dfc[sum_col[i]].sum(axis=1)
            
            for j in sum_col[i]:
                
                index_compoare = []
                index_compoare.append(col_order2.index(j))
                
            new_order = col_order2[:max(index_compoare)+1] + [i] + col_order2[max(index_compoare)+1:]

            dfc = dfc[new_order]

    yitems2 = list(dfc.columns.values)

    
    #計算橫百分比
    for i in yitems2[1:-1]:
        
        try:
            dfc[str(int(i))+'%(R)'] = dfc[i] / dfc['Ntemp']   #row_percentage, default open
        
        except ValueError:
            dfc[str(i)+'%(R)'] = dfc[i] / dfc['Ntemp']
            
        
    if colpercent==True:
        
        for i in yitems2[1:-1]:
        
            try:
                dfc[str(int(i))+'%(C)'] = dfc[i] / dfc.loc[v+1,i]  #column_percentage
    
            except ValueError:
                dfc[str(i)+'%(C)'] = dfc[i] / dfc.loc[v+1,i]
    
    dfc['N'] = dfc[yitems].sum(axis=1)
    
    dfc.drop('Ntemp',axis=1,inplace=True)
    
    dfc.rename(index=str,columns={indexName:'level'},inplace=True)
    
    
   
    return dfc


def main_crosstab(dataframe,columnName,weight=None,party_type=1,optional_variables=[],colmissing=[],
                  colpercent=False,customer='general'):
    
    if party_type == 1: partyr = ['supporting_partyr']
    elif party_type == 2: partyr = ['supporting_partyrr']
    elif party_type == 0: partyr = []
    
    if customer == 'TPOF':
        
        main_variables = ['gender','agegp','edugp','area','supporting_party']
        
    elif customer == 'TPOF2':
        
        main_variables = ['gender','agegp','edugp','supporting_party']
        
    elif customer == 'county_mode':
        main_variables = ['gender','agegp','edugp','edugpr','area','supporting_party']+partyr
        
    elif customer == 'general':
        main_variables = ['gender','agegp','edugp','supporting_party']+partyr+['area','date']

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
        
        
        