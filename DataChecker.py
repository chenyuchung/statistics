# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 09:52:48 2025

@author: cyc
"""

import pandas as pd
import os

class DataChecker:
    def __init__(self, df, varlist, path, wave, date, survey_name='問卷組別未設定', multi_pairs=None, work_vars=None, 
                 note_exclude = [], survey_code='tscs251',appellation=None):
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
        self.note_exclude = note_exclude       # 排除不需審查的開放題變項
        
        # ✅ 預設稱謂字典
        self.appellation = appellation if appellation is not None else {
                            
                            #明顯為男性稱呼
                            "male": ['先生','父','爸','爺','阿公','男','丈夫','兄','哥','弟','兒子','叔','舅','老公',
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
        self.check_filled_notes()

    def check_single_note(self):
        
        """
        檢查封閉題與對應開放題的邏輯關係：
        - 若主題選特定選項時應填開放題，卻沒填 → 錯誤
        - 若主題未選這些選項卻填了開放題 → 錯誤
        - 特例：x3c開頭的開放題欄位，填-6視為空白
        """
        
        note_df = pd.read_excel(self.varlist, sheet_name='note')
        
        # 建立每個主題變項對應所有允許填寫開放題的 value 清單
        value_map = {}
        for _, row in note_df.iterrows():
            main_var = row['ori_item']
            val = row['value']
            if main_var not in value_map:
                value_map[main_var] = set()
            value_map[main_var].add(val)
        
        for _, row in note_df.iterrows():
            main_var, open_var, valid_value = row['ori_item'], row['note_item'], row['value']
            additional_vars = str(row.get('add_output', '')).split('@') if 'add_output' in row and pd.notna(row['add_output']) else []
            
            for idx in self.df.index:
                main_val = self.df.loc[idx, main_var]
                open_val = self.df.loc[idx, open_var]
                no = self.df.loc[idx, 'no']
                id_ = self.df.loc[idx, 'id']
                          
                # 判斷開放題是否「實際沒填」
                if main_var.startswith('x3c') and open_val == -6:
                    is_empty_note = True
                else:
                    is_empty_note = pd.isna(open_val) or str(open_val).strip() == ''

               
                # 錯誤情境一：應填卻沒填
                if main_val == valid_value and is_empty_note:
                    content = f"{main_var}={main_val}，{open_var}={open_val}"
                    additional_info = '，'.join(f"{var}={self.df.at[idx, var]}" for var in additional_vars if var in self.df.columns)
                    if additional_info:
                        content += '，' + additional_info
                    self._add_error(no, id_, content, f"{main_var}_開放題未填")

                # 錯誤情境二：不應填卻填了（考慮多個合法 value）
                elif main_val not in value_map.get(main_var, set()) and not is_empty_note:
                    content = f"{main_var}={main_val}，{open_var}={open_val}"
                    additional_info = '，'.join(f"{var}={self.df.at[idx, var]}" for var in additional_vars if var in self.df.columns)
                    if additional_info:
                        content += '，' + additional_info
                    self._add_error(no, id_, content, f"{main_var}_所選選項不應填答開放題")

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
                    self._add_error(no, id_, content, f"{multi_var}_所選選項不應填答開放題")

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
                if val not in ['-8', '', '0'] and len(val) < 10:
                    self._add_error(no, id_, f"{var}={val}", f"{var}_號碼少於10碼")


    def check_filled_notes(self):
        """
        列出當前 wave 中所有已填寫的開放題內容，供人工判斷是否可歸入選項。
        - 資料來源：note + muti_note 工作表中的 note_item 欄位
        - 排除條件：
        - note_item 含 'x' 或 'z'
        - note_item 為 'email'
        - ori_item 為 'connect'
        - 手動排除變數 self.note_exclude
        - 對每一個 note_item，從 lookup dict 自動補出對應主題欄位值
        - 結果寫入 self.checklist（非錯誤項目，僅供人工審閱）
        """
        # 讀取設定資料
        note_df = pd.read_excel(self.varlist, sheet_name='note')
        muti_note_df = pd.read_excel(self.varlist, sheet_name='muti_note')

        # 建立 note_item → ori_item 的對應字典
        note_lookup = {row['note_item']: row['ori_item'] for _, row in note_df.iterrows()}
        for _, row in muti_note_df.iterrows():
            note_item = row['note_item']
            ori_item = row['ori_item']
            if ori_item != 'connect' and 'z' not in note_item:
                note_lookup[note_item] = ori_item

        # 自動排除變數
        auto_exclude = [col for col in self.df.columns if 'x' in col or 'z' in col or col == 'email']
        user_exclude = getattr(self, 'note_exclude', [])
        exclude_vars = set(auto_exclude + user_exclude)

        # 最終檢查變數：從 note_lookup 中剔除排除名單
        note_out = [var for var in note_lookup if var not in exclude_vars]

        current_wave = getattr(self, 'wave', None)

        for idx in self.df.index:
            row_wave = self.df.at[idx, 'wave'] if 'wave' in self.df.columns else None
            if current_wave is not None and row_wave != current_wave:
                continue

            for var in note_out:
                if var not in self.df.columns:
                    continue

                val = self.df.at[idx, var]
                if pd.isna(val) or str(val).strip() == '':
                    continue

                # 自動補出主題變項值
                main_var = note_lookup.get(var)
                if main_var and main_var in self.df.columns:
                    main_val = self.df.at[idx, main_var]
                    content = f"{main_var}={main_val}，{var}={val}"
                else:
                    content = f"{var}={val}"

                self._add_error(
                    no=self.df.at[idx, 'no'],
                    id_=self.df.at[idx, 'id'],
                    content=content,
                    reason=f"{var}_請確認答案是否可以歸類"
                )



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
        """
        檢查跳答邏輯：
        - 來源為 'skip' 工作表時，條件為變數 == -6 或 '-6'，邏輯為 and
        - 來源為 'skip2' 工作表時，條件為變數 != -6 或 '-6'，邏輯為 or
        """
        for sheet in ['skip', 'skip2']:
            try:
                skip_table = pd.read_excel(self.varlist, sheet_name=sheet)
            except Exception as e:
                print(f"⚠️ 無法讀取工作表 {sheet}：{e}")
                continue

            for _, row in skip_table.iterrows():
                triA = row.get('triggerA', '')
                triB = row.get('triggerB', '')
                con = row.get('condition', '')
                desc = row.get('description', '')
                output = row.get('output', '')

                # 解析 skip_num 與 skip_str 欄位（若為空則為空列表）
                skip_num = str(row.get('skip_num', '')).strip()
                skip_num_vars = skip_num.split('@') if skip_num else []
                
                skip_str = str(row.get('skip_str', '')).strip()
                skip_str_vars = skip_str.split('@') if skip_str else []
                
                output_list = output.split('@') if pd.notna(output) else []

                # 根據來源工作表決定檢查邏輯與運算符
                is_skip_sheet = (sheet == 'skip2')
                num_val = -6
                str_val = '-6'
                op = '==' if is_skip_sheet else '!='
                logic_join = all if is_skip_sheet else any

                for idx in self.df.index:
                    a = self.df.at[idx, triA] if triA in self.df.columns else None
                    b = self.df.at[idx, triB] if triB and triB in self.df.columns else ''

                    try:
                        if eval(con):
                            # 根據來源決定是 == -6 還是 != -6
                            num_checks = [
                                (self.df.at[idx, var] == num_val if op == '==' else self.df.at[idx, var] != num_val)
                                for var in skip_num_vars if var in self.df.columns
                            ]
                            str_checks = [
                                (self.df.at[idx, var] == str_val if op == '==' else self.df.at[idx, var] != str_val)
                                for var in skip_str_vars if var in self.df.columns
                            ]

                            if logic_join(num_checks + str_checks):
                                no = self.df.at[idx, 'no']
                                id_ = self.df.at[idx, 'id']
                                content = '，'.join(f"{col}={self.df.at[idx, col]}" for col in output_list if col in self.df.columns)
                                self._add_error(no, id_, content, desc)

                    except Exception as e:
                        print(f"❗ 跳答檢誤錯誤：check={desc}, id={self.df.at[idx, 'id']}，原因：{e}")
                        continue


    def check_logic(self):
        #print("🧪 稱謂字典：", self.appellation)
        
        logic = pd.read_excel(self.varlist, sheet_name='logic')

        def to_bool(tf):
            return True if tf == 'T' else False

        safe_builtins = {'any': any, 'all': all, 'isinstance': isinstance, 'str': str,
                         'int': int, 'float': float, 'len': len, 'set': set, 'list': list,
                         'dict': dict, 'sum': sum
                         }


        for _, row in logic.iterrows():
            check_no = row['check_no']
            var_list = str(row['var_list']).split('@')
            rule = self._sanitize_rule(row['check_rule'])  # 使用新加入的清理方法
            expected_result = to_bool(row['TorF'])
            description = row['description']
            out_vars = str(row['out_var']).split('@')
            for idx in self.df.index:
                local_env = {}
                try:
                    for i, varname in enumerate(var_list):
                        local_env[f"it{i+1}"] = self.df.loc[idx, varname]
                       
                    # 強制觸發dict的內部資料建構
                    for k, v in local_env.items():
                        if isinstance(v, dict):
                            _ = v.keys()
                       
                    # ✅ 一次注入所有稱謂群組
                    eval_globals = dict(safe_builtins)
                    eval_globals.update({
                        "spouse_appellation": self.appellation.get("spouse", []),
                        "male_appellation": self.appellation.get("male", []),
                        "female_appellation": self.appellation.get("female", []),
                        "participant_appellation": self.appellation.get("participant", [])
                    })
                    """
                    local_env.update({
                        "spouse_appellation": self.appellation.get("spouse", []),
                        "male_appellation": self.appellation.get("male", []),
                        "female_appellation": self.appellation.get("female", []),
                        "participant_appellation": self.appellation.get("participant", [])
                    })
                    """
                    #print("💡 local_env keys =", local_env.keys())
                    #print("💡 eval rule =", rule)
                        
                    if eval(rule, eval_globals, local_env) == expected_result:
                        no = self.df.loc[idx, 'no']
                        id_ = self.df.loc[idx, 'id']
                        content = '，'.join(f"{var}={self.df.loc[idx, var]}" for var in out_vars)
                        self._add_error(no, id_, content, f"{check_no}_{description}")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    print(f"❗ 邏輯檢誤錯誤：check_no={check_no}, id={self.df.loc[idx, 'id']}，原因：{e}")
                    continue
    
    def export_logic_error_log(self):
        if self.logic_errors:
            df_log = pd.DataFrame(self.logic_errors)
            filename = f"{self.survey_code}_LOGIC_ERROR_w{self.wave}_{self.date}.xlsx"
            save_path = os.path.join(self.path, "02_check", filename)
            df_log.to_excel(save_path)
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
        self.checklist.to_excel(save_path)
        print(f"✅ 檢誤報表已輸出至：{save_path}")
