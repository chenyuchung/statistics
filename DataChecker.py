# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 09:52:48 2025

@author: cyc
"""

import pandas as pd
import os

class DataChecker:
    def __init__(self, df, varlist, path, wave, date, survey_name='問卷組別未設定', multi_pairs=None, work_vars=None, 
                 survey_code='tscs251',appellation=None):
        self.df = df
        self.varlist = varlist
        self.path = path
        self.wave = wave
        self.date = date
        self.survey_name = survey_name
        self.survey_code = survey_code
        global work  # 使用全域變數 work
        self.multi_pairs = multi_pairs if multi_pairs is not None else [('zb5a11', 'kzb5a')]
        self.work_vars = work_vars if work_vars is not None else work
        
        # ✅ 預設稱謂字典
        self.appellation = appellation if appellation is not None else {
                            
                            #明顯為男性稱呼
                            "male": ['先生','父','爸','爺','阿公','男','夫','兄','哥','弟','兒子','叔','舅','老公',
                                     '祖父','婿','公公','岳父'], 
                            
                            #明顯為女性稱呼
                            "female": ['太太','老婆','妻','女','小姐','姊','姐','妹','姨','姑','女兒','母','媽','孫女',
                                       '媳','阿嬤','婆婆','岳母','夫人'],
                            
                            #明顯為配偶稱呼
                            "spouse":['配偶','老婆','太太','夫人','妻','先生','老公','丈夫','夫'],
                            
                            #明顯為受訪者本人稱呼
                            "participant":['自己','本人','己','受訪者']
                                                                        }        
        
        self.checklist = pd.DataFrame(columns=[
            '問卷組別', '訪員編號', '受訪者編號', '變項名稱原始答案',
            '不符合說明', '計畫回覆', 'wave', '檢誤人員說明'
        ])

    def _sanitize_rule(self, rule: str) -> str:
        """清理 Excel 讀入的 check_rule 字串（處理換行、符號、空白）"""
        if isinstance(rule, str):
            return rule.replace('\n', ' ').replace('\r', ' ').strip()
        return rule

    def _add_error(self, no, id_, content, reason):
        self.checklist.loc[len(self.checklist)] = {
            '問卷組別': self.survey_name,
            '訪員編號': no,
            '受訪者編號': id_,
            '變項名稱原始答案': content,
            '不符合說明': reason,
            '計畫回覆': '',
            'wave': self.df.loc[self.df['id'] == id_, 'wave'].values[0],
            '檢誤人員說明': ''
        }

    def check_note(self):
        self.check_single_note()
        self.check_multi_note()
        self.check_work_note()
        self.check_phone_format()

    def check_single_note(self):
        note_df = pd.read_excel(self.varlist, sheet_name='note')
        for _, row in note_df.iterrows():
            main_var, open_var, valid_value = row['ori_item'], row['note_item'], row['value']
            additional_vars = str(row.get('add_output', '')).split('@') if 'add_output' in row and pd.notna(row['add_output']) else []
            for idx in self.df.index:
                main_val = self.df.loc[idx, main_var]
                open_val = self.df.loc[idx, open_var]
                no = self.df.loc[idx, 'no']
                id_ = self.df.loc[idx, 'id']
                additional_info = '，'.join(f"{var}={self.df.loc[idx, var]}" for var in additional_vars if var in self.df.columns)
                if main_val == valid_value and (pd.isna(open_val) or open_val == ''):
                    content = f"{main_var}={main_val}，{open_var}={open_val}"
                    if additional_info:
                        content += '，' + additional_info
                    self._add_error(no, id_, content, f"{main_var}_開放題未填")
                elif main_val != valid_value and pd.notna(open_val) and open_val != '':
                    content = f"{main_var}={main_val}，{open_var}={open_val}"
                    if additional_info:
                        content += '，' + additional_info
                    self._add_error(no, id_, content, f"{main_var}_所選選項不應填寫開放題")

    def check_multi_note(self):
        for idx in self.df.index:
            for multi_var, note_var in self.multi_pairs:
                multi_val = self.df.loc[idx, multi_var]
                note_val = self.df.loc[idx, note_var]
                no = self.df.loc[idx, 'no']
                id_ = self.df.loc[idx, 'id']
                if multi_val == 1 and (pd.isna(note_val) or note_val == ''):
                    content = f"{multi_var}={multi_val}，{note_var}={note_val}"
                    self._add_error(no, id_, content, f"{multi_var}_開放題未填")
                elif multi_val != 1 and pd.notna(note_val) and note_val != '':
                    content = f"{multi_var}={multi_val}，{note_var}={note_val}"
                    self._add_error(no, id_, content, f"{multi_var}_所選選項不應填開放題")

    def check_work_note(self):
        suffixes = ['a1', 'a2', 'b1', 'b2', 'b3']
        for idx in self.df.index:
            for base in self.work_vars:
                full_vars = [f"{base}{s}" for s in suffixes if f"{base}{s}" in self.df.columns]
                empty_flags = [(v, self.df.loc[idx, v]) for v in full_vars if pd.isna(self.df.loc[idx, v]) or self.df.loc[idx, v] == '']
                if empty_flags:
                    no = self.df.loc[idx, 'no']
                    id_ = self.df.loc[idx, 'id']
                    content = '，'.join(f"{v}={self.df.loc[idx, v]}" for v in full_vars)
                    reason = f"{base}_工作題開放欄位未填答"
                    self._add_error(no, id_, content, reason)
                    break  # 同一組 work 只報一次

    def check_phone_format(self):
        phone_vars = ['cell1', 'cell2', 'phone1', 'phone2']
        for idx in self.df.index:
            phones = [str(self.df.loc[idx, var]) for var in phone_vars]
            no = self.df.loc[idx, 'no']
            id_ = self.df.loc[idx, 'id']
            if all(p in ['0', '-8'] for p in phones):
                content = '，'.join([f"{var}={self.df.loc[idx, var]}" for var in phone_vars])
                self._add_error(no, id_, content, "完全沒有連絡電話或全拒答")
            for var in ['cell1', 'cell2']:
                val = str(self.df.loc[idx, var])
                if val not in ['-8', ''] and len(val) < 10:
                    self._add_error(no, id_, f"{var}={val}", f"{var}_號碼少於10碼")

    def check_range(self):
        rangelist = pd.read_excel(self.varlist, sheet_name='range')
        for _, row in rangelist.iterrows():
            var, mini, maxi, scode = row['var'], row['min'], row['max'], row['special_code']
            specialcode = [int(i) for i in str(scode).split('@') if str(i) != 'nan']
            if var not in self.df.columns:
                continue
            for idx, value in self.df[var].items():
                if pd.isna(value):
                    continue
                if (value < mini or value > maxi) and value not in specialcode:
                    no = self.df.loc[idx, 'no']
                    id_ = self.df.loc[idx, 'id']
                    content = f"{var}={value}"
                    reason = f"{var}_數值不合理"
                    self._add_error(no, id_, content, reason)

    def check_muti(self):
        df_muti = pd.read_excel(self.varlist, sheet_name='muti')
        for _, row in df_muti.iterrows():
            base_item, max_level = row['muti_item'], int(row['max'])
            item_list = [f"{base_item}{i:02d}" for i in range(1, max_level+1)]
            for idx in self.df.index:
                answers = self.df.loc[idx, item_list].fillna(0).tolist()
                if sum(answers) == 0:
                    no = self.df.loc[idx, 'no']
                    id_ = self.df.loc[idx, 'id']
                    content = '，'.join(f"{col}={self.df.loc[idx, col]}" for col in item_list)
                    reason = f"{base_item}_複選題全未勾選"
                    self._add_error(no, id_, content, reason)

    def check_skip(self):
        for sheet in ['skip', 'skip2']:
            skip_table = pd.read_excel(self.varlist, sheet_name=sheet)
            for _, row in skip_table.iterrows():
                triA, triB, con, skiped, desc, output = (
                    row['triggerA'], row['triggerB'], row['condition'], row['skip'], row['description'], row['output']
                )
                output_list = output.split('@')
                for idx in self.df.index:
                    a = self.df.loc[idx, triA]
                    b = self.df.loc[idx, triB] if pd.notna(triB) else ''
                    try:
                        if eval(con) and eval(skiped):
                            no = self.df.loc[idx, 'no']
                            id_ = self.df.loc[idx, 'id']
                            content = '，'.join(f"{col}={self.df.loc[idx, col]}" for col in output_list)
                            self._add_error(no, id_, content, desc)
                    except Exception as e:
                        print(f"❗ 跳答檢誤錯誤：check={desc}, id={self.df.loc[idx, 'id']}，原因：{e}")
                        continue

    def check_logic(self):
        logic = pd.read_excel(self.varlist, sheet_name='logic')

        def to_bool(tf):
            return True if tf == 'T' else False

        for _, row in logic.iterrows():
            check_no = row['check_no']
            var_list = str(row['var_list']).split('@')
            rule = self._sanitize_rule(row['check_rule'])  # 使用新加入的清理方法
            expected_result = to_bool(row['ToF'])
            description = row['description']
            out_vars = str(row['out_var']).split('@')
            for idx in self.df.index:
                local_env = {}
                try:
                    for i, varname in enumerate(var_list):
                        local_env[f"it{i+1}"] = self.df.loc[idx, varname]
                        
                    local_env["spouse_appellation"] = self.appellation["spouse"]
                    local_env["male_appellation"] = self.appellation["male"]
                    local_env["female_appellation"] = self.appellation["female"]
                    local_env["participant_appellation"] = self.appellation["participant"]
                        
                    if eval(rule, {}, local_env) == expected_result:
                        no = self.df.loc[idx, 'no']
                        id_ = self.df.loc[idx, 'id']
                        content = '，'.join(f"{var}={self.df.loc[idx, var]}" for var in out_vars)
                        self._add_error(no, id_, content, f"{check_no}_{description}")
                except Exception as e:
                    print(f"❗ 邏輯檢誤錯誤：check_no={check_no}, id={self.df.loc[idx, 'id']}，原因：{e}")
                    continue
    
    def export_logic_error_log(self):
        if self.logic_errors:
            df_log = pd.DataFrame(self.logic_errors)
            filename = f"{self.survey_code}_LOGIC_ERROR_w{self.wave}_{self.date}.xlsx"
            save_path = os.path.join(self.path, "02_check", filename)
            df_log.to_excel(save_path, index=False)
            print(f"⚠️ 邏輯錯誤記錄已輸出至：{save_path}")

    def check_response_notes(self):
        """
        §C-6. 併入問卷確認回報
        """
        for idx in self.df.index:
            for var in ['note1', 'note2', 'text']:
                if var in self.df.columns:
                    val = self.df.loc[idx, var]
                    if pd.notna(val) and val != '':
                        no = self.df.loc[idx, 'no']
                        id_ = self.df.loc[idx, 'id']
                        content = f"{var}={val}"
                        reason = "請確認訪員回報的內容"
                        self._add_error(no, id_, content, reason)

    def export_report(self):
        output_folder = os.path.join(self.path, f"02_check/w{self.wave}_檢誤報表")
        os.makedirs(output_folder, exist_ok=True)
        filename = f"{self.survey_code}_問卷檢誤_w{self.wave}_{self.date}.xlsx"
        save_path = os.path.join(output_folder, filename)
        self.checklist = self.checklist.drop_duplicates(
            subset=['訪員編號', '受訪者編號', '變項名稱原始答案', '不符合說明'],
            keep='first'
        ).reset_index(drop=True)
        self.checklist.to_excel(save_path, index=False)
        print(f"✅ 檢誤報表已輸出至：{save_path}")
