# -*- coding: utf-8 -*-
"""
Created on Thu Jan  2 09:47:54 2020

@author: scs5
"""

#原始資料查詢

import pandas as pd

def MutiSearch(DataFrame,SearchType=2,ConvertEncoding=0):
    
    df = DataFrame
    
    if SearchType == 1:
        
        path = input(r'請輸入檔案路徑：')
        sheet = input('請輸入工作表名稱：')
        
        SearchList_raw = pd.read_excel(path,sheet_name=sheet)
        
        SearchList = list(zip(*[SearchList_raw[k].values.tolist() for k in SearchList_raw]))
        
    elif SearchType == 2:
        
        conti = 'y'
        SearchList = []
        count = 1
        
        while conti == 'y':
            
            SampleID = int(input('請輸入樣本編號 '+str(count).zfill(2)+' ：'))
            variable = input('請輸入變數名稱 '+str(count).zfill(2)+' ：')
            
            SearchList.append((SampleID,variable))
            
            conti = input('是否繼續下一筆查詢(y/n)：')
            count += 1
    
    SearchResults = pd.DataFrame(SearchList,columns=['id','item'])
    
    for x in range(len(SearchResults.index)):
        SearchResults.loc[x,'value'] = df.loc[df.id==SearchResults.loc[x,'id'],SearchResults.loc[x,'item']].to_string(index=False)
    
    
    if ConvertEncoding == 0: 
        return SearchResults

    elif ConvertEncoding == 1:
        
        Encoding = input('請輸入編碼：')
        SearchResults['value_'+Encoding] = SearchResults['value'].str.encode(Encoding,'replace').str.decode(Encoding)
        
        return SearchResults
    
    
"""
#找出含有「?」的樣本
df.loc[df.var.str.contains('?',regex=False),'id']


"""
        
        
        