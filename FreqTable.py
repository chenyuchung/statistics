# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 10:10:40 2019

@author: scs5
"""

import pandas as pd
import math
import numpy as np

def n_round(n):
    if n-math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)

def FreqTable(dataframe,col,weightList=[],wRound=False,PCTround=False,missing=[],sort=1):
    
    origin = dataframe
    
    #create basic frequency table
    dff = pd.value_counts(origin[col]).to_frame().reset_index()
    dff.columns = [col,'frequency']
    dff['percentage(%)'] = ( dff['frequency'] / len(origin) ) * 100
    dff['valid percentage(%)'] = ( dff.loc[dff[col].isin(missing)==False,'frequency'] /
                                  dff.loc[dff[col].isin(missing)==False,'frequency'].sum() ) * 100
    
    valuelist = list(dff[col])
    
    #sort
    if   sort == 1: dff.sort_values(by=[col],inplace=True)
    elif sort == 2: dff.sort_values(by=['frequency'],ascending=False,inplace=True)
    elif sort == 3: dff.sort_values(by=['percentage(%)'],ascending=False,inplace=True)
    
    dff.reset_index(drop=True,inplace=True)
    
    #set if missing value exist
    un_sum = dff['frequency'].sum()
    
    sysmissN = len(origin) - un_sum
    
    v = dff.last_valid_index()
    
    ii = 1
    
    if missing != []:
        
        dff.loc[v+1,dff.columns.values] = ['Valid Total',
                                           dff.loc[dff[col].isin(missing)==False,'frequency'].sum(),
                                           dff.loc[dff[col].isin(missing)==False,'frequency'].sum()/len(origin)*100,
                                           1/1*100]
        ii += 1

        if sysmissN != 0:

            dff.loc[v+ii,dff.columns.values] = ['System missing',sysmissN,sysmissN/len(origin)*100,np.nan]
            
            ii += 1

        dff.loc[v+ii,dff.columns.values] = ['Total',un_sum,un_sum/un_sum*100,np.nan]
        
    else: 
        
        dff.loc[v+ii,dff.columns.values] = ['Total',dff['frequency'].sum(),dff['percentage(%)'].sum(),
                                           dff['valid percentage(%)'].sum()]
    


    #count weighted value & percentage
    if weightList != []:          
        for i in weightList:
            for j in valuelist:
                dff.loc[dff[col]==j,i] = origin.loc[origin[col]==j,i].sum()
                dff.loc[dff[col]==j,i+'(%)'] = (origin.loc[origin[col]==j,i].sum()/
                                                origin[i].sum() * 100
                                                )
                
                dff.loc[dff[col]==j,i+'(valid%)'] = (
                    origin.loc[(origin[col]==j) & (origin[col].isin(missing)==False),i].sum()/
                                                origin.loc[origin[col].isin(missing)==False,i].sum() * 100
                                                )           
    
    #fill empty percentage
    iii = 1
    
    if weightList != []:          
        for i in weightList:
            if missing != []:
                
                dff.loc[v+iii,i] = origin.loc[origin[col].isin(missing)==False,i].sum()
                
                dff.loc[v+iii,i+'(%)'] = ( origin.loc[origin[col].isin(missing)==False,i].sum() /
                                        origin[i].sum() * 100
                                        )
                
                dff.loc[v+iii,i+'(valid%)'] = 1/1*100
                
                iii += 1
 
                if sysmissN != 0:
                
                    dff.loc[v+iii,i] = origin[i].sum() - origin.loc[origin[col].isin(missing)==False,i].sum()
                
                    dff.loc[v+iii,i+'(%)'] = ( (origin[i].sum() - origin.loc[origin[col].isin(missing)==False,i].sum()) /
                                            origin[i].sum() * 100
                                            )
                    
                    iii += 1
                
                dff.loc[v+iii,i] = origin[i].sum()
                dff.loc[v+iii,i+'(%)'] = origin[i].sum() / origin[i].sum() *100
                dff.loc[v+iii,i+'(valid%)'] = np.nan
                
            else:
                
                dff.loc[v+iii,i] = origin[i].sum()
                dff.loc[v+iii,i+'(%)'] = dff[i+'(%)'].sum()
                dff.loc[v+iii,i+'(valid%)'] = dff[i+'(valid%)'].sum()

    
    #rearrange row order
    if missing != []:
        missing.sort()
        ix = dff.loc[dff[col]==missing[0]].index[0]
        
        dff2 = pd.concat([dff.iloc[:ix],
                          dff.iloc[ix+len(missing):ix+len(missing)+1],
                          dff.iloc[ix:ix+len(missing)],
                          dff.iloc[ix+len(missing)+1:]]).reset_index(drop=True)



    #set if round weighted value is needed
    if wRound==True:
        for i in weightList:
            dff2[i] = dff2[i].apply(n_round)


    #set if round perecntage is needed    
    if PCTround==True:
        for i in ['percentage(%)','valid percentage(%)'] + [a+'(%)' for a in weightList]:
            dff2[i] = dff2[i].apply(n_round)    
    
    
    
    
    return dff2