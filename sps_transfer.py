# -*- coding: utf-8 -*-
"""
Created on Tue May  6 16:27:29 2025

ISSP標準語法設定檔整理與轉換 by ChatGPT

@author: cyc
"""

import re
import pandas as pd
from typing import Dict, List

"""這個版本轉variable labels勉強OK，但missing會缺漏。
def parse_sps_content_line_by_line(sps_text: str) -> pd.DataFrame:
    variable_labels: Dict[str, str] = {}
    comments: Dict[str, str] = {}
    value_labels: Dict[str, Dict[int, str]] = {}
    missing_values: Dict[str, List[int]] = {}
    formats: Dict[str, str] = {}

    current_section = None
    current_var = None
    current_comment_var = None
    current_comment_block = []
    current_valuelabel_var = None

    rows = []
    lines = sps_text.splitlines()
    error_lines = []

    for i, line in enumerate(lines):
        if i % 50 == 0:
            print(f"處理中：第 {i} 行 / 共 {len(lines)} 行")

        line = line.strip()
        if not line:
            continue

        try:
            # VARIABLE LABELS
            if line.upper().startswith("VARIABLE LABELS"):
                current_section = "VARIABLE LABELS"
                line = line[len("VARIABLE LABELS"):].strip()

            if current_section == "VARIABLE LABELS":
                if line == ".":
                    current_section = None
                else:
                    match = re.match(r"(\w+)\s+\"([^\"]+)\"", line)
                    if match:
                        variable_labels[match.group(1)] = match.group(2)

            # COMMENT TO
            elif line.upper().startswith("COMMENT TO"):
                current_section = "COMMENT"
                match = re.match(r"COMMENT TO (\w+):\s*(.*)", line, re.IGNORECASE)
                if match:
                    current_comment_var = match.group(1)
                    rest = match.group(2)
                    current_comment_block = [rest]

            elif current_section == "COMMENT":
                if re.match(r"^(VARIABLE LABELS|VALUE LABELS|FORMATS|MISSING VALUES)", line, re.IGNORECASE):
                    comments[current_comment_var] = ' '.join(current_comment_block).strip()
                    current_section = None
                else:
                    current_comment_block.append(line)
                if i == len(lines) - 1:
                    comments[current_comment_var] = ' '.join(current_comment_block).strip()

            # VALUE LABELS
            elif line.upper().startswith("VALUE LABELS"):
                current_section = "VALUE LABELS"
                line = line[len("VALUE LABELS"):].strip()
                match = re.match(r"(\w+)", line)
                if match:
                    current_valuelabel_var = match.group(1)
                    value_labels[current_valuelabel_var] = {}

            elif current_section == "VALUE LABELS":
                if line.strip() == ".":
                    current_valuelabel_var = None
                    current_section = None
                else:
                    match = re.findall(r"(-?\d+)\s+\"([^\"]+)\"", line)
                    if match and current_valuelabel_var:
                        for code, label in match:
                            value_labels[current_valuelabel_var][int(code)] = label

            # MISSING VALUES
            elif line.upper().startswith("MISSING VALUES"):
                current_section = "MISSING VALUES"
                match = re.match(r"MISSING VALUES\s+(\w+)\s+\(([^)]+)\)\s*\.\s*", line, re.IGNORECASE)
                if match:
                    var = match.group(1)
                    value_str = match.group(2)
                    values = []
                    for val in value_str.split(','):
                        val = val.strip()
                        if 'thru' in val.lower():
                            parts = val.lower().split('thru')
                            try:
                                start = int(parts[0].strip())
                                end = int(parts[1].strip())
                                values.extend(range(start, end + 1))
                            except ValueError:
                                error_lines.append((i + 1, line))
                                continue
                        else:
                            try:
                                values.append(int(val))
                            except ValueError:
                                error_lines.append((i + 1, line))
                                continue
                    missing_values[var] = values

            # FORMATS
            elif line.upper().startswith("FORMATS"):
                current_section = "FORMATS"
                match = re.match(r"FORMATS\s+(\w+)\s+\(([^)]+)\)", line, re.IGNORECASE)
                if match:
                    formats[match.group(1)] = match.group(2)

        except Exception as e:
            error_lines.append((i + 1, line))

    # 確保變數順序依照出現順序
    seen_vars = set()
    for i, line in enumerate(lines):
        if re.match(r"^(VARIABLE LABELS|VALUE LABELS|COMMENT TO|MISSING VALUES|FORMATS)", line, re.IGNORECASE):
            var_matches = re.findall(r"\b\w+\b", line)
            for var in var_matches:
                if var.upper() in ["VARIABLE", "LABELS", "VALUE", "COMMENT", "TO", "MISSING", "VALUES", "FORMATS"]:
                    continue
                if var not in seen_vars and (
                    var in variable_labels or
                    var in comments or
                    var in value_labels or
                    var in missing_values or
                    var in formats
                ):
                    seen_vars.add(var)
                    row = {
                        "變數名稱": var,
                        "VARIABLE LABEL": variable_labels.get(var, ""),
                        "COMMENT": comments.get(var, ""),
                        "VALUE LABELS（dict）": str(value_labels.get(var, {})),
                        "MISSING VALUES": str(missing_values.get(var, [])),
                        "FORMAT": formats.get(var, "F8.0")
                    }
                    rows.append(row)

    if error_lines:
        print("\n⚠️ 偵測到無法解析的行：")
        for line_num, content in error_lines:
            print(f"  第 {line_num} 行: {content}")

    return pd.DataFrame(rows)

"""

#這個版本轉missingOK，但沒有label
def parse_sps_content_line_by_line(sps_text: str) -> pd.DataFrame:
    variable_labels: Dict[str, str] = {}
    comments: Dict[str, str] = {}
    value_labels: Dict[str, Dict[int, str]] = {}
    missing_values: Dict[str, List[int]] = {}
    formats: Dict[str, str] = {}

    current_section = None
    current_var = None
    current_valuelabel_var = None
    current_valuelabel_block = []
    current_comment_var = None
    current_comment_block = []

    rows = []
    lines = sps_text.splitlines()

    for i, line in enumerate(lines):
        if i % 50 == 0:
            print(f"處理中：第 {i} 行 / 共 {len(lines)} 行")

        line = line.strip()
        if not line:
            continue

        # VARIABLE LABELS 開頭
        if line.upper().startswith("VARIABLE LABELS"):
            current_section = "VARIABLE LABELS"
            line = line[len("VARIABLE LABELS"):].strip()

        elif line.upper().startswith("COMMENT TO"):
            current_section = "COMMENT"
            match = re.match(r"COMMENT TO (\w+):\s*(.*)", line, re.IGNORECASE)
            if match:
                current_comment_var = match.group(1)
                rest = match.group(2)
                current_comment_block = [rest]

        elif line.upper().startswith("VALUE LABELS"):
            current_section = "VALUE LABELS"
            line = line[len("VALUE LABELS"):].strip()

        elif line.upper().startswith("MISSING VALUES"):
            current_section = "MISSING VALUES"
            match = re.match(r"MISSING VALUES\s+(\w+)\s+\(([^)]+)\)\s*\.", line, re.IGNORECASE)
            if match:
                var = match.group(1)
                value_str = match.group(2)
                values = []
                for val in value_str.split(','):
                    val = val.strip()
                    if 'thru' in val.lower():
                        parts = val.lower().split('thru')
                        try:
                            start = int(parts[0].strip())
                            end = int(parts[1].strip())
                            values.extend(range(start, end + 1))
                        except ValueError:
                            continue
                    else:
                        try:
                            values.append(int(val))
                        except ValueError:
                            continue
                missing_values[var] = values

        elif line.upper().startswith("FORMATS"):
            current_section = "FORMATS"
            match = re.match(r"FORMATS\s+(\w+)\s+\(([^)]+)\)", line, re.IGNORECASE)
            if match:
                formats[match.group(1)] = match.group(2)

        # 處理 VARIABLE LABELS
        elif current_section == "VARIABLE LABELS":
            match = re.match(r"(\w+)\s+\"([^\"]+)\"", line)
            if match:
                variable_labels[match.group(1)] = match.group(2)

        # 處理 COMMENT 區塊
        elif current_section == "COMMENT":
            if re.match(r"^(VARIABLE LABELS|VALUE LABELS|FORMATS|MISSING VALUES)", line, re.IGNORECASE):
                comments[current_comment_var] = ' '.join(current_comment_block).strip()
                current_section = None
            else:
                current_comment_block.append(line)

        # 處理 VALUE LABELS 區塊
        elif current_section == "VALUE LABELS":
            match_start = re.match(r"(\w+)\s+(-?\d+)\s+\"([^\"]+)\"", line)
            if match_start:
                current_valuelabel_var = match_start.group(1)
                value_labels.setdefault(current_valuelabel_var, {})
                value_labels[current_valuelabel_var][int(match_start.group(2))] = match_start.group(3)
            else:
                match_pair = re.findall(r"(-?\d+)\s+\"([^\"]+)\"", line)
                for code, label in match_pair:
                    if current_valuelabel_var:
                        value_labels.setdefault(current_valuelabel_var, {})
                        value_labels[current_valuelabel_var][int(code)] = label

        # 結束 COMMENT 區塊收尾
        if current_section == "COMMENT" and i == len(lines) - 1:
            comments[current_comment_var] = ' '.join(current_comment_block).strip()

    # 確保變數順序依照出現順序
    seen_vars = set()
    for i, line in enumerate(lines):
        var_matches = re.findall(r"\b\w+\b", line)
        for var in var_matches:
            if var not in seen_vars and (
                var in variable_labels or
                var in comments or
                var in value_labels or
                var in missing_values or
                var in formats
            ):
                seen_vars.add(var)
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
df = parse_sps_content_line_by_line(sps_text)

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
