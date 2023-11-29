# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 19:40:26 2023

@author: user
"""

import pandas as pd
import random as rd
import os, sys
path = r'D:\Dadi\公司營運相關資料\2023勞動訪視應準備資料'
os.chdir(path)

count = int(input('請輸入組數：'))

login = []
logout = []

for i in range(count):
    
    t1 = str(rd.randint(1430,1540))
    
    while int(t1[2:]) > 59:
        t1 = str(rd.randint(1430,1540))
    
    t2 = str(rd.randint(2219,2245))
    
    t1r = t1[:2] + ':' + t1[2:]
    t2r = t2[:2] + ':' + t2[2:]
    
    login.append(t1r)
    logout.append(t2r)


df = pd.DataFrame(data={'loginT':login,'logoutT':logout})

#df.to_excel('./打卡時間.xlsx')



count2 = int(input('請輸入組數：'))

login2 = []
logout2 = []

login3 = []
logout3 = []

for i in range(count2):
    
    t3 = str(rd.randint(1230,1330))
    
    while int(t3[2:]) > 59:
        t3 = str(rd.randint(1230,1330))
    
    t4 = str(rd.randint(1600,1659))
    
    t3r = t3[:2] + ':' + t3[2:]
    t4r = t4[:2] + ':' + t4[2:]
    
    login2.append(t3r)
    logout2.append(t4r)
    
for i in range(count2):
    
    t5 = str(rd.randint(1720,1800))
    
    while int(t5[2:]) > 59:
        t5 = str(rd.randint(1720,1800))
    
    t6 = str(rd.randint(2200,2215))
    
    t5r = t5[:2] + ':' + t5[2:]
    t6r = t6[:2] + ':' + t6[2:]
    
    login3.append(t5r)
    logout3.append(t6r)

df2 = pd.DataFrame(data={'loginT':login2,'logoutT':logout2})
df3 = pd.DataFrame(data={'loginT':login3,'logoutT':logout3})

with pd.ExcelWriter('./打卡時間2.xlsx') as writer:
    df2.to_excel(writer,sheet_name='任慧真')
    df3.to_excel(writer,sheet_name='陳詠觀')
