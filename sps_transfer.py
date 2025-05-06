# -*- coding: utf-8 -*-
"""
Created on Tue May  6 16:27:29 2025

ISSP標準語法設定檔整理與轉換 by ChatGPT

@author: cyc
"""

import re
from typing import Dict, List, Tuple
import pandas as pd

def parse_sps_content(sps_text: str) -> pd.DataFrame:
    # 正則表達式模板
    variable_label_pattern = re.compile(r'VARIABLE LABELS\s+(\w+)\s+"([^"]+)"', re.IGNORECASE)
    comment_pattern = re.compile(r'COMMENT TO (\w+):\s+((?:.|\n)*?)(?=(?:VARIABLE LABELS|VALUE LABELS|FORMATS|MISSING VALUES|$))', re.IGNORECASE)
    value_labels_pattern = re.compile(r'VALUE LABELS\s+(\w+)\s+((?:\s*-?\d+\s+"[^"]+"\s*)+)\.', re.IGNORECASE)
    missing_values_pattern = re.compile(r'MISSING VALUES\s+(\w+)\s+\((-?\d+(?:,\s*-?\d+)*)\)', re.IGNORECASE)
    formats_pattern = re.compile(r'FORMATS\s+(\w+)\s+\(([^)]+)\)', re.IGNORECASE)

    # 暫存字典
    variable_labels = dict(variable_label_pattern.findall(sps_text))
    comments = {var: text.replace('\n', ' ').strip() for var, text in comment_pattern.findall(sps_text)}
    value_labels = {}
    for var, labels_block in value_labels_pattern.findall(sps_text):
        label_pairs = re.findall(r'(-?\d+)\s+"([^"]+)"', labels_block)
        value_labels[var] = {int(code): label for code, label in label_pairs}

    missing_values = {
        var: [int(v.strip()) for v in values.split(',')]
        for var, values in missing_values_pattern.findall(sps_text)
    }

    formats = dict(formats_pattern.findall(sps_text))

    # 整合所有變數
    all_vars = set(variable_labels) | set(comments) | set(value_labels) | set(missing_values) | set(formats)

    rows = []
    for var in sorted(all_vars):
        row = {
            "變數名稱": var,
            "VARIABLE LABEL": variable_labels.get(var, ""),
            "COMMENT": comments.get(var, ""),
            "VALUE LABELS（dict）": str(value_labels.get(var, {})),
            "MISSING VALUES": str(missing_values.get(var, [])),
            "FORMAT": formats.get(var, "F8.0")
        }
        rows.append(row)

    return pd.DataFrame(rows)

# 示例用法：
# with open("yourfile.sps", "r", encoding="utf-8") as f:
#     sps_text = f.read()
# df = parse_sps_content(sps_text)
# df.to_excel("parsed_output.xlsx", index=False)


import os

print('')
path = input('請輸入sps檔所在資料夾路徑：')
input_path = r'' + path
os.chdir(input_path)

print('')
input_file = input('請輸入sps檔名 (含副檔名)：')

start_time = pd.Timestamp('today')
start_time_str = pd.Timestamp('today').strftime('%Y/%m/%d %H:%M:%S')

print('轉換開始時間：',start_time_str)


with open('./' + input_file, 'r', encoding='utf-8') as f:
    sps_text = f.read()
df = parse_sps_content(sps_text)

print('')
same_path = input('輸出路徑是否與sps所在位置相同 (y/n)：')
if same_path =='n':
    print('')
    out_path = input('請輸入輸出資料夾路徑：')
    os.chdir(r'' + out_path)

end_time = pd.Timestamp('today')
end_time_str = pd.Timestamp('today').strftime('%Y/%m/%d %H:%M:%S')
lasting_time = end_time - start_time

print('轉換結束時間：',end_time_str)
print('共耗時 ',lasting_time)
print('')


df.to_excel('./sps變數資訊整理.xlsx', index=False)
