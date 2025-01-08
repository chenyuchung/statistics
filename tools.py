# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 14:27:35 2024

@author: user
"""

import pandas as pd
import sys,os


## 檢視columns內項目內容清單
def col_content(dataframe,col_name):
    
    content_list = list(set(list(dataframe[col_name])))
    
    return content_list

