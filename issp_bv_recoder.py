# -*- coding: utf-8 -*-
"""
Created on Tue May 20 17:01:44 2025

@author: cyc
"""

import numpy as np
import pandas as pd
import inspect

class RecodeEngine:
    def __init__(self, df, bv_mapping, log_file=None):
        self.df = df
        self.bv = bv_mapping
        self.log = []  # 儲存偵錯訊息
        self.report_log = []
        self.log_file = log_file  # 日誌檔路徑
        self.tc_country_dict = {
            '中國': 156, '俄羅斯': 643, '加拿大': 124, '北韓': 408, '南非': 710,
            '印尼': 360, '台灣': 158, '墨西哥': 484, '奧地利': 40, '孟加拉': 50,
            '德國': 276, '挪威': 578, '新加坡': 702, '日本': 392, '比利時': 56, '法國': 250, 
            '泰國': 764, '澳大利亞': 36, '澳洲': 36,'緬甸':104,'香港':158,'澳門':158,
            '瑞典': 752, '瑞士': 756, '美國': 840, '英國': 826, '荷蘭': 528, '西班牙': 724, '越南': 704,
            '阿富汗': 4, '阿根廷': 32, '韓國': 410, '南韓': 410,'馬來西亞': 458
            }
    
    def log_print(self, content, func_name=None):
        
        if func_name is None:
            # 自動找出呼叫 log_print 的上一層函式名（即「實際使用者」）
            stack = inspect.stack()
            if len(stack) >= 3:
                func_name = stack[2].function
            else:
                func_name = 'unknown'
        
        if isinstance(content, pd.DataFrame):
            output = content.to_string(index=False)
        else:
            output = str(content)

        timestamp = pd.Timestamp('today').strftime('%Y/%m/%d %H:%M:%S')
        header = f"\n=== [{timestamp}] Output from [{func_name}] ===\n"
        full_output = header + output + "\n"

        # 印出到畫面
        print(full_output)

        # 同步寫入檔案
        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(full_output)

        
    def report_invalid(self, label, source_cols=None):
        mask = self.df[label] == -90
        if mask.any():
            cols = ['id']
            if source_cols:
                if isinstance(source_cols, str):
                    cols.append(source_cols)
                elif isinstance(source_cols, list):
                    cols += source_cols
            cols.append(label)
            cols = [c for c in cols if c in self.df.columns]
            
            df_out = self.df.loc[mask, cols]
            message = f'⚠️ [{label}] recode = -90 的樣本：'
            self.log_print(message)
            self.log_print(df_out)
            

    def report_other_text(self, label, other_codes=[]):
        """
        額外列出 recode 結果為「其他」類別的開放文字內容（id + text_col）
        label：recode 後欄位名稱
        other_codes：對應 recode 的「其他」代碼值（如 [6, 10]）
        """
        if not other_codes:
            return  # 沒有指定「其他」代碼就不做事
        
        text_col = 'k' + self.bv.get(label, '')
        if text_col not in self.df.columns or 'id' not in self.df.columns:
            return

        mask = self.df[label].isin(other_codes)
        df_other = self.df.loc[mask, ['id', text_col]].dropna()

        if not df_other.empty:
            print(f'📌 來自「{label}」的 recode=其他 之開放文字內容如下（共 {len(df_other)} 筆）：')
            print(df_other)


    def generate_birth_age(self, survey_year=114, col_y='a2y', col_r='a2r', col_m='a2m', col_sdt='sdt1', col_year='year'):
        # 出生年（民國轉西元）
        self.df['BIRTH'] = self.df[col_y] + 1911
        
        # 若 a2y 為 [-7,-8]，使用 a2r（114 為預設調查年）
        mask_missing = self.df[col_y].isin([-7, -8])
        self.df.loc[mask_missing, 'BIRTH'] = survey_year - self.df.loc[mask_missing, col_r] + 1911
        
        # 推算年齡（年）
        self.df['AGE'] = self.df[col_year] - self.df['BIRTH']
        
        # 從 sdt1 擷取月份（民國年月四碼）
        self.df['month'] = self.df[col_sdt].astype(int).astype(str).str.zfill(4).str[:2].astype(int)
        
        # 若出生月未到，年齡 +1
        self.df['AGE'] = np.where(self.df[col_m] < self.df['month'], self.df['AGE'] + 1, self.df['AGE'])
        
        # 顯示 recode 結果
        print(self.df[['BIRTH', col_y, col_r]].describe())
        print(self.df[['AGE', 'BIRTH', col_m, col_sdt]].describe())




    def recode_tw_iscd(self, col_level='b1', col_status='b2'):
        def logic(row):
            level = row[col_level]
            status = row[col_status]
            if level in [1]: return 10   #010 "Less than primary: Never attended an education programme 無/不識字"1
            elif level in [2]: return 20 #020 "Less than primary: Some early childhood education 自修/識字/私塾" 2
            elif level in [3] and status in [2]: return 30  #030 "Less than primary: Some primary education (excl. level completion) 小學"3
            elif level in [3] and status in [1]: return 100 #100 "Primary education 小學"3
            elif level in [4] and status in [2, 3]: return 242 #242 "Lower sec general: Partial level completion, excl. direct access to upper sec educ 國（初）中"4
            elif level in [4] and status in [1]: return 243    #243 "Lower sec general: Level completion, excl. direct access to upper sec educ 國（初）中"4
            elif level in [5] and status in [2]: return 252    #252 "Lower sec voc: Partial level completion, excl. direct access to upper sec educ 初職"5
            elif level in [5] and status in [1]: return 253    #253 "Lower sec voc: Level completion, excl. direct access to upper sec educ 初職" 5
            elif level in [6] and status in [2, 3]: return 342 #342 "Upper sec general: Partial level completion, excl. direct access to tert educ 高中普通科"6
            elif level in [6] and status in [1]: return 343    #343 "Upper sec general: Level completion, excl. direct access to tert educ 高中普通科" 6
            elif level in [7, 8, 9] and status in [2, 3]: return 352 #352 "Upper sec voc: Partial level completion, excl. direct access to tert educ 高中職業科/高職/士官學校"789
            elif level in [7, 8, 9] and status in [1]: return 353    #353 "Upper sec voc: Level completion, excl.  direct access to tert educ 高中職業科/高職/士官學校" 789
            elif level in [10] and status in [2, 3]: return 450 #450 "Post-secondary non-tertiary education: Vocational 五專" 10
            elif level in [10] and status in [1]: return 453    #453 "Post-sec non-tert educ voc: Level completion, excl. direct access to tert educ 五專" 10
            elif level in [11, 12, 13, 14, 15]: return 550      #550 "Short-cycle tertiary education: Vocational 二專/三專/軍警校專修班/軍警校專科班/空中行專/商專 "11 12 13 14 15
            elif level in [16]: return 600                      #600 "Bachelor’s or equivalent level 空中大學"16
            elif level in [19] and status in [2, 3]: return 343 #大學肄業或就讀中，歸入高中普通科
            elif level in [19] and status in [1]: return 640    #640 "Bachelor’s or equivalent level: Academic 大學"19
            elif level in [17, 18]: return 650                  #650 "Bachelor’s or equivalent level: Professional 軍警官校/軍警官大學/技術學院、科大"17 18"
            elif level in [20]: return 740 #740 "Master’s or equivalent level: Academic 碩士"20
            elif level in [21]: return 840 #840 "Doctoral or equivalent level: Academic 博士"21
            elif level in [-8]: return -9  # -9 "No answer"
            else: return -90

        self.df['TW_ISCD'] = self.df.apply(logic, axis=1)
        self.report_invalid('TW_ISCD', [col_level,'k'+col_level, col_status, 'k'+col_status])

    """
    【教育程度編碼】
    
    010 "Less than primary: Never attended an education programme 無/不識字"1
    020 "Less than primary: Some early childhood education 自修/識字/私塾" 2
    030 "Less than primary: Some primary education (excl. level completion) 小學"3
    100 "Primary education 小學"3
    242 "Lower sec general: Partial level completion, excl. direct access to upper sec educ 國（初）中"4
    243 "Lower sec general: Level completion, excl. direct access to upper sec educ 國（初）中"4
    252 "Lower sec voc: Partial level completion, excl. direct access to upper sec educ 初職"5
    253 "Lower sec voc: Level completion, excl. direct access to upper sec educ 初職" 5
    342 "Upper sec general: Partial level completion, excl. direct access to tert educ 高中普通科"6
    343 "Upper sec general: Level completion, excl. direct access to tert educ 高中普通科" 6
    352 "Upper sec voc: Partial level completion, excl. direct access to tert educ 高中職業科/高職/士官學校"789
    353 "Upper sec voc: Level completion, excl.  direct access to tert educ 高中職業科/高職/士官學校" 789
    450 "Post-secondary non-tertiary education: Vocational 五專" 10
    453 "Post-sec non-tert educ voc: Level completion, excl. direct access to tert educ 五專" 10
    550 "Short-cycle tertiary education: Vocational 二專/三專/軍警校專修班/軍警校專科班/空中行專/商專 "11 12 13 14 15
    600 "Bachelor’s or equivalent level 空中大學"16
    640 "Bachelor’s or equivalent level: Academic 大學"19
    650 "Bachelor’s or equivalent level: Professional 軍警官校/軍警官大學/技術學院、科大"17 18"
    740 "Master’s or equivalent level: Academic 碩士"20
    840 "Doctoral or equivalent level: Academic 博士"21
    900 "Not elsewhere classified"
    - 9 "No answer"

    010 "小學以下：從未參加教育計劃 無/不識字"
    020 "小學以下：某些早期兒童教育 自修/識字/私塾"
    030 "小學以下：部分小學教育（不包括完成該等級） 小學"
    100 "小學教育 小學"
    242 "初中普通教育：部分等級完成，不包括直接進入高中教育 國（初）中"
    243 "初中普通教育：等級完成，不包括直接進入高中教育 國（初）中"
    252 "初中職業教育：部分等級完成，不包括直接進入高中教育 初職"
    253 "初中職業教育：等級完成，不包括直接進入高中教育 初職"
    342 "高中普通教育：部分等級完成，不包括直接進入高等教育 高中普通科"
    343 "高中普通教育：等級完成，不包括直接進入高等教育 高中普通科"
    352 "高中職業教育：部分等級完成，不包括直接進入高等教育 高中職業科/高職/士官學校"
    353 "高中職業教育：等級完成，不包括直接進入高等教育 高中職業科/高職/士官學校"
    450 "中等後非高等教育：職業教育 五專"
    453 "中等後非高等教育職業教育：等級完成，不包括直接進入高等教育 五專"
    550 "短期高等教育：職業教育 二專/三專/軍警校專修班/軍警校專科班/空中行專/商專"
    600 "學士或同等程度 空中大學"
    640 "學士或同等程度：學術類 大學"
    650 "學士或同等程度：專業類 軍警官校/軍警官大學/技術學院、科大"
    740 "碩士或同等程度：學術類 碩士"
    840 "博士或同等程度：學術類 博士"
    900 "未分類"
    -9 "無答案"
    """

    def compute_partliv(self, type=1):
        """
        根據配對欄位自動產生 PARTLIV 欄位。
        type=1 表示有問伴侶狀況，type=2 表示僅問婚姻狀況。
        """
        marital_col = self.bv.get('MARITAL')
        partner_col = self.bv.get('PARTLIV')

        def partliv_logic(row):
            item1 = row[marital_col]
            item2 = row.get(partner_col, None)

            if type == 1:
                if item1 in [2, 3] or item2 == 1: return 1
                elif item2 == 2:                  return 2
                elif item1 == 5 and item2 == 3:   return 2 #分居且沒有伴侶者，應歸入「有配偶但未同居」
                elif item2 == 3:                  return 3
                elif item2 == -8:                 return -7
                else:                             return -90
            elif type == 2:
                if item1 == 2:           return 1
                elif item1 in [3, 5]:    return 2
                elif item1 in [1, 4, 6]: return 3
                else:                    return -90

        self.df['PARTLIV'] = self.df.apply(partliv_logic, axis=1)
        self.report_invalid('PARTLIV', [marital_col, partner_col])

    def ensure_partliv(self):
        if 'PARTLIV' not in self.df.columns:
            self.compute_partliv()

    def log_if_sp_issue(self, row, wk_val, plv_val, label):
        if label.startswith('SP') and wk_val != -6 and plv_val == 3:
            self.log.append(f"⚠️ [{label}] 觸發異常：index={row.name}, wk={wk_val}, plv={plv_val}")
            return True
        return False

    def recode_work(self, label):
        item_col = self.bv[label]
        self.ensure_partliv()
        mainstat_col = self.bv['MAINSTAT'] if label == 'WORK' else self.bv['SPMAINST']

        def logic(row):
            item = row[item_col]
            plv = row['PARTLIV']
            mainstat = row.get(mainstat_col, None)

            # WORK recode 規則
            if item in [1, 2, 3]: 
                alt = 1
                if mainstat == 10: alt = 2   # 🔁 若 MAINSTAT 來源為 10(退休)，則強制改為 2  --> 參秋玲2023recode語法
            elif item in [4, 5]: alt = 2
            elif item == 6: alt = 3
            elif item in [-7,-8]: alt = -9   #配偶WORK有可能為-7
            elif item == -6: alt = -4
            else: alt = item

            # 特殊配偶狀況：wk != -6 但 plv = 3 → 失格，改為 -4
            if self.log_if_sp_issue(row, item, plv, label):
                alt = -4  # wk為-6應為沒有伴侶
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])

    def recode_workhrs(self, label):
        item_col = self.bv[label]
        wk_col = self.bv['SPWORK'] if label.startswith('SP') else self.bv['WORK']
        self.ensure_partliv()

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]
            plv = row['PARTLIV']

            # WORKHRS recode 規則
            if 96 <= item <= 168: alt = 96
            elif item in [-2, -8]: alt = -9  #work hrs ==-2 should recode to -9 (2022 .py file & 2023 do file)
            elif item == [-7]: alt = -8   #ISSP ARCHIVE告知 'time various'要歸入不知道 (from 2019 do file)
            elif item == -6: alt = -4   # workhr為-6應為wk==6或沒有伴侶
            else: alt = item
            
            if wk in [4,5,6]: alt = -4  #-4. NAP (Code 2 or 3 in WORK)
            
            if self.log_if_sp_issue(row, item, plv, label):
                alt = -4
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])

    def recode_emprel(self, label, type=1, item2_alt_col=None):
        item1_col = self.bv[label]
        item2_col = item2_alt_col or (self.bv[label] + 'a')
        wk_col = self.bv['SPWORK'] if label.startswith('SP') else self.bv['WORK']
        self.ensure_partliv()

        def logic(row):
            item1 = row[item1_col]
            item2 = row[item2_col]
            wk = row[wk_col]
            plv = row['PARTLIV']

            # EMPREL recode 規則
            if type == 1:
                if item1 in [5, 6, 7, 8, 9, 10]: alt = 1
                elif item1 == 2: alt = 2
                elif item1 == 1 and item2 in range(1, 10): alt = 3
                elif item1 == 1 and item2 >= 10: alt = 4
                elif item1 in [3, 4]: alt = 5
                elif wk in [6, -6]: alt = -4  # wk為-6應為沒有伴侶
                elif item1 in [-6, -7, -8]: alt = -9
                else: alt = -90
            elif type == 2:   #note: 配偶雇用人數不一定有問，若沒問改用公司人數推論
                if item1 in [5, 6, 7, 8, 9, 10]: alt = 1
                elif item1 == 2: alt = 2
                elif item1 == 1 and item2 == 1: alt = 3
                elif item1 == 1 and item2 > 1: alt = 4
                elif item1 in [3, 4]: alt = 5
                elif wk in [6, -6]: alt = -4  # wk為-6應為沒有伴侶
                elif item1 in [-6, -7, -8]: alt = -9
                else: alt = -90

            if self.log_if_sp_issue(row, wk, plv, label):
                alt = -4
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item1_col, item2_col, wk_col])
        
        """
        1 "Employee"
        2 "Self-employed without employees"
        3 "Self-employed with 1 to 9 employees"
        4 "Self-employed with 10 employees or more"
        5 "Working for own family's business"
        -4 "NAP (Code 3 in WORK)"
        -9 "No answer"       
        """
        

    def recode_wrksup(self, label, type=1):
        item_col = self.bv[label]
        wk_col = self.bv['SPWORK'] if label.startswith('SP') else self.bv['WORK']
        self.ensure_partliv()

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]
            plv = row['PARTLIV']

            # WRKSUP recode 規則
            if type == 1:  #直接填管理人數
                if item > 0: alt = 1
                elif item == 0: alt = 2
                elif item == -6 and wk != -6: alt = 2  #emprel就選沒僱人
                elif wk == 6: alt = -4
                elif item in [-2, -7, -8]: alt = -9
                else: alt = -90
            elif type == 2:  #只選有沒有管人 (1=有，2=沒有)
                if wk in [6, -6]: alt = -4  # wk為-6應為沒有伴侶
                elif item == -6 and wk != -6: alt = 2  #emprel就選沒僱人
                elif item == -7: alt = -8
                elif item in [-2, -8]: alt = -9
                else: alt = item

            if self.log_if_sp_issue(row, wk, plv, label):
                alt = -4
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, wk_col])

    def recode_nsup(self, label='NSUP'):
        item_col = self.bv[label]
        wk_col = self.bv['WORK']

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]

            # NSUP recode 規則
            if item in range(1, 9995): alt = item
            elif item >= 9995: alt = 9995
            elif wk == 6 or item == 0: alt = -4  # wk沒有工作過或本題沒管人
            elif item == -6 and wk != -6: alt = -4  #emprel就選沒僱人
            elif item in [-2, -7, -8]: alt = -9
            else: alt = -90
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, wk_col])

    def recode_typorg1(self, label='TYPORG1'):
        item_col = self.bv[label]
        wk_col = self.bv['WORK']

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]

            # TYPORG1 recode 規則
            if item in [1,2,3,4,5,6,9,10]: alt = 1
            elif item in [7,8]: alt = 2
            elif item == -8: alt = -9
            elif item == -7: alt = -8
            elif wk == 6: alt = -4
            else: alt = -90
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, wk_col])

    def recode_typorg2(self, label='TYPORG2'):
        item_col = self.bv[label]
        wk_col = self.bv['WORK']

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]

            # TYPORG2 recode 規則
            if item in [6,7]: alt = 1
            elif item in [1,2,3,4,5,8,9,10]: alt = 2
            elif item == -8: alt = -9
            elif item == -7: alt = -8
            elif wk == 6: alt = -4
            else: alt = -90
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, wk_col])

    def recode_isco08(self, label):
        item_col = self.bv[label]
        wk_col = self.bv['SPWORK'] if label.startswith('SP') else self.bv['WORK']
        self.ensure_partliv()

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]
            plv = row['PARTLIV']

            # ISCO08 recode 規則
            if wk in [6, -6]: alt = -4  # wk為-6應為沒有伴侶
            elif item == -8: alt = -9
            elif item == -7: alt = -8
            elif 1500 < item < 1599: alt = 3341
            elif item in [111, 112]: alt = 110
            else: alt = item

            if self.log_if_sp_issue(row, wk, plv, label):
                alt = -4
            return alt

        self.df[label] = self.df.apply(logic, axis=1)

    def recode_mainstat(self, label):
        item_col = self.bv[label]
        wk_col = self.bv['SPWORK'] if label.startswith('SP') else self.bv['WORK']
        self.ensure_partliv()

        def logic(row):
            item = row[item_col]
            wk = row[wk_col]
            plv = row['PARTLIV']

            # MAINSTAT recode 規則
            if wk == -6: alt = -4  # wk為-6應為沒有伴侶
            elif item in [1,2,3,4,5,8,14,15]: alt = 1  #In paid work
            elif item == 6: alt = 2
            elif item == 7: alt = 3
            elif item == 9: alt = 4
            elif item == 12: alt = 5
            elif item == 10: alt = 6
            elif item == 11: alt = 7
            elif item == 13: alt = 8
            elif item == 16: alt = 9
            elif item in [-6, -7, -8]: alt = -9
            else: alt = -90

            if self.log_if_sp_issue(row, wk, plv, label):
                alt = -4
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, wk_col])

    def work_x_mainstat_check(self,work,mainstat):
        work_col = self.bv['SPWORK'] if work.startswith('SP') else self.bv['WORK']
        mainstat_col = self.bv['SPMAINST'] if mainstat.startswith('SP') else self.bv['MAINSTAT']
        mainstat_text = 'k' + mainstat_col
        
        mask = ((self.df[work] == 2) & (self.df[mainstat] == 1)) | ((self.df[work] == 1) & (self.df[mainstat] != 1))

        if mask.any():
            print('')
            print(f'⚠️ {work} 與 {mainstat} recode 結果矛盾的樣本：')
            
            # ➤ 基本欄位
            cols = ['id', mainstat_col, mainstat_text, work_col, work, mainstat]
            
            # ➤ 加入受訪者本人才有的 TW_RINC 欄
            if work == 'WORK':
                income_col = self.bv['TW_RINC']
                cols.append(income_col)
                
            # ➤ ISCO 附加欄位
            isco_base = self.bv['SPISCO08'] if work.startswith('SP') else self.bv['ISCO08']
            prefix = isco_base[:-2]
            isco_related = [prefix + suffix for suffix in ['a1', 'a2', 'b1', 'b2', 'b3', 'c']]
            cols += [col for col in isco_related if col in self.df.columns]
            
            
            # ➤ 顯示結果
            result = self.df.loc[mask, cols]
            print(result)
            
        """
        note. 
        mainstat 為 (09)學徒 (According to 2020 do file)
                或  (10)退休 (According to 2023 do file)
        ，但 WORK == 1者，基本上會recode WORK = 2。
        
        """
                

    def recode_tw_relig(self, label, buddhism_item=2):
        item_col = self.bv[label]
        text_col = 'k' + item_col

        def logic(row):
            item = row[item_col]
            if buddhism_item == 1:
                if 0 < item < 9: alt = item
                elif item == 8: alt = 0
                elif item == 9: alt = 8
                elif item == -8: alt = -7
                elif item == -7: alt = -8
                else: alt = -90
            else:
                if 2 < item < 9: alt = item - 1
                elif item in [1, 2]: alt = 1
                elif item == 9: alt = 0
                elif item == 10: alt = 8
                elif item == -8: alt = -7
                elif item == -7: alt = -8
                else: alt = -90
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, text_col])
        
        # 額外列出「其他」類別的開放欄位（供人工判斷是否需要細分類）
        self.report_other_text(label, other_codes=[8])
        
        
    def religgrp(self,label,buddhism_item=2):
        item_col = self.bv[label]
        text_col = 'k' + item_col        
        
        def logic(row):
            item =  row[item_col]
            if buddhism_item == 1:
                if item == 8: alt = 0       #沒有宗教信仰
                elif item == 6: alt = 1
                elif item == 7: alt = 2
                elif item == 5: alt = 6
                elif item in [1]: alt = 7    #Buddhism
                elif item in [2,3,4]: alt = 9  #Other Asian religions
                elif item == 8: alt = 10    #Other religions
                elif item == -8: alt = -7   #Refuse
                elif item == -7: alt = -9   #"Don't know" to "No answer"
                else: alt = -90        
            
            else:
                if item == 9: alt = 0       #沒有宗教信仰
                elif item == 7: alt = 1
                elif item == 8: alt = 2
                elif item == 6: alt = 6
                elif item in [1,2]: alt = 7    #Buddhism
                elif item in [3,4,5]: alt = 9  #Other Asian religions
                elif item == 10: alt = 10    #Other religions
                elif item == -8: alt = -7   #Refuse
                elif item == -7: alt = -9   #"Don't know" to "No answer"
                else: alt = -90
        
            return alt
        
        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, text_col])        

        # 額外列出「其他」類別的開放欄位（供人工判斷是否需要細分類）
        self.report_other_text(label, other_codes=[8,10])
    
    """
    RELIGGRP values
    
    0 "No religion"
    1 "Catholic" 天主教
    2 "Protestant"新教
    3 "Orthodox"正統
    4 "Other Christian"其他基督徒
    5 "Jewish"猶太人
    6 "Islamic"伊斯蘭
    7 "Buddhist"佛系
    8 "Hindu"印度教
    9 "Other Asian Religions"
    10 "Other Religions"
    -7 "Refused"
    -8 "Information insufficient"資訊不足
    -9 "No answer"
    """
        
    def recode_tw_ethn(self, label):
        item_col = self.bv[label]
        text_col = 'k' + item_col

        def logic(row):
            item = row[item_col]
            if item == 1: alt = 1         #台灣閩南人
            elif item ==2: alt = 2        #台灣客家人
            elif item in [3,8]: alt = 3   #大陸/外省人
            elif item in [4]: alt = 4     #原住民
            elif item in [5,6]: alt = 5   #大陸/中國籍
            elif item == 7: alt = 6       #東南亞籍
            elif item in [9,10]: alt = 7  #根據過去紀錄，平埔族歸入其他
            elif item == -8: alt = -7
            elif item == -7: alt = -8
            else: alt = -90
            return alt

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, text_col])      
        
        # 額外列出「其他」類別的開放欄位（供人工判斷是否需要細分類）
        # 特殊處理：只抓 recode=7 且原始 item != 9 的狀況
        mask = (self.df[label] == 7) & (self.df[item_col] != 9)
        if not self.df.loc[mask].empty:
            print(f'📌 「{label}」為 7 且原始 item 非 9 者如下：')
            print(self.df.loc[mask, ['id', item_col, text_col, label]])

        

    def recode_vote_le(self, label, num_candidates=3):
        item_col = self.bv[label]
        candidate_codes = list(range(1, num_candidates + 1))
        
        def logic(row):
            item = row[item_col]
            if item in candidate_codes or item in [num_candidates + 1, num_candidates + 2]: return 1   #有去投票
            elif item == num_candidates + 3: return 2                            #沒去投票
            elif item in [num_candidates + 4,num_candidates + 5]: return -4      #沒有投票權
            elif item in [-7,-8]: return -7    #拒答
            else: return -90

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])
        

    def recode_tw_prty(self, label, num_candidates=3):
        item_col = self.bv[label]
        candidate_codes = list(range(1, num_candidates + 1))

        def logic(row):
            item = row[item_col]
            if item in candidate_codes: return item
            elif item == candidate_codes + 1: return 96  #廢票
            elif item == candidate_codes + 2: return -7  #拒答
            elif item in list(range(num_candidates + 3, num_candidates + 6)) + [-7, -8]: return -4  #未投票、無資格或投票狀態不明
            else: return -90

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])

               
    def recode_hhadult(self):
        child_col = self.bv['HHTODD']
        youth_col = self.bv['HHCHILDR']
        total_col = self.bv['HOMPOP']

        def logic(row):
            item1 = row[child_col]
            item2 = row[youth_col]
            hh = row[total_col]
            if hh == -8:  return -9
            elif hh == 1: return 1
            elif hh > 0 and item1 > 0 and item2 > 0: return hh - item1 - item2
            else:         return -9

        self.df['HHADULT'] = self.df.apply(logic, axis=1)


    def recode_tw_rinc(self, label):  #23items
        item_col = self.bv[label]
        
        def logic(row):
            item = row[item_col]
            if item == 1: return 0
            elif item == 22: return 250000
            elif item == 23: return 300000
            elif item == -9: return -9
            elif item == -8: return -7
            elif item == -7: return -8
            elif 2 <= item <= 21: return (item - 2) * 10000 + 5000   #選項(02)~(21)皆為1萬區間
            else: return -90

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])


    def recode_tw_inc(self, label):  #26items
        item_col = self.bv[label]

        def logic(row):
            item = row[item_col]
            if item == 1:    return 0
            elif item == 22: return 250000
            elif item == 23: return 350000
            elif item == 24: return 450000
            elif item == 25: return 750000
            elif item == 26: return 1000000
            elif item == -9: return -9
            elif item == -8: return -7
            elif item == -7: return -8
            elif 2 <= item <= 21: return (item - 2) * 10000 + 5000
            else:            return -90

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col])


    def recode_marital(self):
        item1_col = self.bv['MARITAL']
        item2_col = self.bv['PARTLIV']
        text_col = 'k' + item1_col
        
        def logic(row):
            item1 = row[item1_col]
            item2 = row[item2_col]
            if item1 in [2, 3]: return 1
            elif item1 in [1, 4, 5, 6] and item2 in [1, 2]: return 2
            elif item1 == 5:    return 3
            elif item1 == 4:    return 4
            elif item1 == 6:    return 5
            elif item1 == 1:    return 6
            elif item1 == -8:   return -7
            else:               return -90

        self.df['MARITAL'] = self.df.apply(logic, axis=1)
        self.report_invalid('MARITAL', [item1_col, text_col, item2_col])


    def recode_born(self, label):
        item_col = self.bv[label]
        text_col = 'k' + item_col  # 對應開放欄位

        # 初始化記錄使用過的國名
        self.used_tc_countries = set()

        def logic(row):
            item = row[item_col]
            text_val = row.get(text_col, None)
            
            # 若已有明確國碼，直接使用
            if item == 1: return 158
            elif item == 2: return 156
            elif item == -8: return -7
            elif item == -7: return -9
                       
            # 若代碼為其他或缺失，再查詢 text_col 進行 recode
            if isinstance(text_val, str):
                text_val = text_val.strip()
                #print(f"text_val 原始: {repr(text_val)} / 比對結果: {text_val in self.tc_country_dict}")
                
                if text_val in self.tc_country_dict:
                    alt = self.tc_country_dict[text_val]
                    self.used_tc_countries.add(text_val)
                    #print(f"[MATCHED] text_val = {text_val} → {alt}")
                    return alt
                #else:
                    #print(f"❌ 無法比對 text_val: {repr(text_val)}")
                
            return -90
        

        self.df[label] = self.df.apply(logic, axis=1)
        self.report_invalid(label, [item_col, text_col])      
        
        # 輸出實際使用到的國名清單
        if self.used_tc_countries:
            print(f"✅ recode_born：以下透過 text_col 成功 recode 的國名（共 {len(self.used_tc_countries)} 筆）：")
            print(sorted(self.used_tc_countries))


    def recode_tw_region(self):
        # fallback：zipr 不存在時使用 zip
        source_col = 'zipr' if 'zipr' in self.df.columns else 'zip'
        
        def logic(zipcode):
            if 200 <= zipcode <= 206: return 1
            if 100 <= zipcode <= 116: return 2
            if 220 <= zipcode <= 253: return 3
            if 320 <= zipcode <= 338: return 4
            if 3001 <= zipcode <= 3003 or zipcode == 300: return 5
            if 302 <= zipcode <= 315: return 6
            if 350 <= zipcode <= 369: return 7
            if 400 <= zipcode <= 439: return 8
            if 540 <= zipcode <= 558: return 10
            if 500 <= zipcode <= 530: return 11
            if 630 <= zipcode <= 655: return 12
            if 6001 <= zipcode <= 6002 or zipcode == 600: return 13
            if 602 <= zipcode <= 625: return 14
            if 700 <= zipcode <= 745: return 15
            if 800 <= zipcode <= 852: return 17
            if 900 <= zipcode <= 947: return 19
            if 260 <= zipcode <= 290: return 20
            if 970 <= zipcode <= 983: return 21
            if 950 <= zipcode <= 966: return 22
            if 880 <= zipcode <= 885: return 23
            return -90

        self.df['TW_REG'] = self.df[source_col].apply(logic)
        self.report_invalid('TW_REG', [source_col])


    def generate_dweight_hh(self):
        # 條件對應值表
        condition_value_map = {
            (1, '唯一合格者'): 8 / 48,
            (2, '最年輕者'):   5 / 48, (2, '最年長者'):   3 / 48,
            (3, '最年輕者'):   3 / 48, (3, '第二年輕者'): 3 / 48, (3, '最年長者'):   2 / 48,
            (4, '最年輕者'):   3 / 48, (4, '第二年輕者'): 2 / 48, (4, '第三年輕者'): 2 / 48, (4, '最年長者'):   1 / 48,
            (5, '最年輕者'):   1 / 48, (5, '第二年輕者'): 1 / 48, (5, '第三年輕者'): 2 / 48,
            (5, '第四年輕者'): 3 / 48, (5, '最年長者'):   1 / 48,
            (6, '最年輕者'):   1 / 48, (6, '第二年輕者'): 1 / 48, (6, '第三年輕者'): 2 / 48,
            (6, '第四年輕者'): 2 / 48, (6, '第五年輕者'): 1 / 48, (6, '最年長者'):   1 / 48
                                }

        # household_r = 有上限的 household 數
        self.df['household_r'] = self.df['household']
        self.df.loc[self.df['household_r'] >= 6, 'household_r'] = 6

        # 轉換選樣目標文字敘述
        def sample_target_str(hh, ruleN):
            if ruleN == 1:
                return '唯一合格者' if hh == 1 else '最年輕者'
            elif ruleN == 2:
                if hh == 1: return '唯一合格者'
                elif hh < 5: return '最年輕者'
                else: return '第二年輕者'
            elif ruleN == 3:
                if hh == 1: return '唯一合格者'
                elif hh < 5: return '最年輕者'
                else: return '第三年輕者'
            elif ruleN == 4:
                if hh == 1: return '唯一合格者'
                elif hh == 2: return '最年輕者'
                elif hh < 5: return '第二年輕者'
                else: return '第三年輕者'
            elif ruleN == 5:
                if hh == 1: return '唯一合格者'
                elif hh == 2: return '最年輕者'
                elif hh < 5: return '第二年輕者'
                else: return '第四年輕者'
            elif ruleN == 6:
                if hh == 1: return '唯一合格者'
                elif hh == 2: return '最年長者'
                elif hh == 3: return '第二年輕者'
                elif hh == 4: return '第三年輕者'
                else: return '第四年輕者'
            elif ruleN == 7:
                if hh == 1: return '唯一合格者'
                elif hh == 2: return '最年長者'
                elif hh == 3: return '第二年輕者'
                elif hh == 4: return '第三年輕者'
                elif hh == 5: return '第四年輕者'
                else: return '第五年輕者'
            elif ruleN == 8:
                return '唯一合格者' if hh == 1 else '最年長者'
            else:
                return '未定義'

        # 若尚未有 result_txt，則自動計算建立
        if 'result_txt' not in self.df.columns:
            self.df['result_txt'] = self.df.apply(
                lambda row: sample_target_str(row['household_r'], row['sample_rule']),
                axis=1
                )
            print("🔧 自動產出 result_txt 欄位。")
        else:
            print("ℹ️ 偵測到既有 result_txt 欄位，將直接使用不覆蓋。")
                                                

        # 指定 DWEIGHT_HH
        self.df['DWEIGHT_HH'] = np.nan
        for (hh, label), value in condition_value_map.items():
            mask = (self.df['household_r'] == hh) & (self.df['result_txt'] == label)
            self.df.loc[mask, 'DWEIGHT_HH'] = value

        unmatched = self.df[self.df['DWEIGHT_HH'].isna()]
        if not unmatched.empty:
            print("⚠️ 以下樣本無法對應到 DWEIGHT_HH 權重條件：")
            print(unmatched[['id', 'household_r', 'sample_rule', 'result_txt']])
        else:
            print("✅ DWEIGHT_HH 欄位計算完成，所有樣本皆成功配對。")


    def recode_mode(self, col_za2='za2', col_zb4='zb4', col_zb604='zb604'):
        def logic(row):
            item1 = row[col_za2]
            item2 = row[col_zb4]
            item3 = row[col_zb604]
            
            # 明確不合理條件先行處理
            if (item1 == 1 and item2 == 4 and item3 == 1) or (item1 in [2, 3] and item2 == 4 and item3 == 1):
                return -90

            if item1 in [2, 3] and item2 == 2 and item3 == 0:        return 10  #10.F2f/PAPI, no visuals
            elif item1 in [2, 3] and item2 in [1, 3] and item3 == 0: return 11  #11.F2f/PAPI, visuals
            elif item1 in [2, 3] and item2 == 4 and item3 == 0:      return 12  #12.F2f/PAPI, respondent reading questionnaire
            elif item1 in [2, 3] and item2 == 2 and item3 == 1:      return 13  #13.F2f/PAPI, interpreter or translator – no visuals
            elif item1 in [2, 3] and item2 in [1, 3] and item3 == 1: return 14  #14.F2f/PAPI, interpreter or translator – visuals
            elif item1 == 1 and item2 in [1, 3] and item3 == 0:      return 21  #21.CAPI, visuals
            elif item1 == 1 and item2 == 4 and item3 == 0:           return 22  #22.CAPI, respondent reading questionnaire (paper or on monitor)
            elif item1 == 1 and item2 == 2 and item3 == 1:           return 23  #23.CAPI, interpreter or translator – no visuals
            elif item1 == 1 and item2 in [1, 3] and item3 == 1:      return 24  #24.CAPI, interpreter or translator – visuals
            elif item1 == 4:                                         return -90
            else:                                                    return 20  #20. CAPI, no visuals

        self.df['MODE'] = self.df.apply(logic, axis=1)
        self.report_invalid('MODE', [col_za2, 'k'+col_za2, col_zb4, 'k'+col_zb4, col_zb604])
        print(self.df['MODE'].value_counts(dropna=False))



