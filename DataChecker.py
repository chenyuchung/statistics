# -*- coding: utf-8 -*-
"""
Created on Wed Apr 30 09:52:48 2025

@author: cyc
"""

import pandas as pd
import os
import re
from natsort import natsorted

class DataChecker:
    def __init__(self, df, varlist, path, wave, date, survey_name='問卷組別未設定', multi_pairs=None, work_vars=None, 
                 note_exclude = [], survey_code='tscs251',handler='曉芬',appellation=None):
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
        self.handler = handler
        
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
        allowed_symbols = ['#', '-', '轉', '分機', 'ext', ' ']
        
        for idx in self.df.index:
            phones = [str(self.df.loc[idx, var]) for var in phone_vars]
            no = self.df.loc[idx, 'no']
            id_ = self.df.loc[idx, 'id']
            
            # 檢查是否完全沒有聯絡電話
            if all(p in ['0', '-8'] for p in phones):
                content = '，'.join([f"{var}={self.df.loc[idx, var]}" for var in phone_vars])
                self._add_error(no, id_, content, "完全沒有連絡電話或全拒答")
                
            
            for var in phone_vars:
                raw_val = str(self.df.loc[idx, var]).strip()
                if raw_val in ['0', '-8', '']:
                    continue

                # 去除允許的符號
                simplified = raw_val
                for sym in allowed_symbols:
                    simplified = simplified.replace(sym, '')
                simplified = simplified.strip()

                # 市話欄位：僅檢查非法字元
                if var in ['phone1', 'phone2']:
                    if not simplified.isdigit():
                        self._add_error(no, id_, f"{var}={raw_val}", f"{var}_號碼格式有誤，請確認")
                    continue

                # 手機欄位處理（cell1, cell2）
                if var in ['cell1', 'cell2']:
                    if len(simplified) < 10:
                        self._add_error(no, id_, f"{var}={raw_val}", f"{var}_號碼少於10碼")
                        continue  # 若長度不夠，略過其餘檢查

                    # 若開頭非 09 或含非法字元（非數字）
                    digit_check = simplified.isdigit()
                    starts_with_09 = simplified.startswith('09')
                    if not digit_check or not starts_with_09:
                        self._add_error(no, id_, f"{var}={raw_val}", f"{var}_號碼格式有誤，請確認")


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
        - 來源為 'skip' 工作表時，條件為變數 != -6 或 '-6'，邏輯為 or
        - 來源為 'skip2' 工作表時，條件為變數 == -6 或 '-6'，邏輯為 and
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
                    a = self.df.loc[idx, triA] if triA in self.df.columns else None
                    b = self.df.loc[idx, triB] if triB and triB in self.df.columns else ''

                    try:
                        if eval(con):
                            # 根據來源決定是 == -6 還是 != -6
                            num_checks = [
                                (self.df.loc[idx, var] == num_val if op == '==' else self.df.loc[idx, var] != num_val)
                                for var in skip_num_vars if var in self.df.columns
                            ]
                            str_checks = [
                                (self.df.loc[idx, var] == str_val if op == '==' else self.df.loc[idx, var] != str_val)
                                for var in skip_str_vars if var in self.df.columns
                            ]

                            if logic_join(num_checks + str_checks):
                                no = self.df.loc[idx, 'no']
                                id_ = self.df.loc[idx, 'id']
                                content = '，'.join(f"{col}={self.df.at[idx, col]}" for col in output_list if col in self.df.columns)
                                self._add_error(no, id_, content, desc)

                    except Exception as e:
                        print(f"❗ 跳答檢誤錯誤：check={desc}, id={self.df.loc[idx, 'id']}，原因：{e}")
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
                    
                    # ✅ 加這段 → 將 itN 傳入 eval_globals 給 lambda 用
                    eval_globals.update({k: v for k, v in local_env.items() if k.startswith("it")})
                    
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
                    #import traceback
                    #traceback.print_exc()
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


    def filter_handled_items(self):
        """
        比對歷週處理過的報表，移除重複項目並更新 self.checklist。
        條件：同一問卷代碼（self.survey_code）處理人（self.handler），依據標準報表命名規則判定。
        """
        # 設定路徑與欄位
        check_root = os.path.join(self.path, "02_check")
        current_wave = f"w{self.wave}"
        key_cols = ['訪員編號', '受訪者編號', '變項名稱原始答案', '不符合說明']
        keep_cols = key_cols + ['計畫回覆']
    
        # 初始化累積 DataFrame
        df_cpast = pd.DataFrame(columns=keep_cols)

        # 瀏覽所有資料夾，尋找過去週次的處理後報表
        for folder in sorted(os.listdir(check_root)):
            if not re.match(r"w\d{2}_檢誤報表", folder):
                continue
            if folder == current_wave:
                continue
            wave_label = folder.split("_")[0]

            subdir = os.path.join(check_root, folder)
            if not os.path.isdir(subdir):
                print(f"⚠️ 資料夾 {subdir} 不存在，略過。")
                continue

            # 搜尋符合處理人且 survey_code 相符的處理後報表
            pattern = re.compile(
                rf"{re.escape(self.survey_code)}_問卷檢誤_{wave_label}_(\d+)_({re.escape(self.handler)})(.*)\.xlsx"
            )
            matched_files = [f for f in os.listdir(subdir) if pattern.match(f)]

            if not matched_files:
                print(f"❌ 找不到處理後報表（{self.handler}）於 {folder}，略過。")
                continue

            # 多個符合就全讀進來
            for fname in matched_files:
                fpath = os.path.join(subdir, fname)
                try:
                    df_temp = pd.read_excel(fpath)
                    df_temp = df_temp[keep_cols].copy()
                    
                    # 標準化「變項名稱原始答案」的換行符號
                    df_temp['變項名稱原始答案'] = df_temp['變項名稱原始答案'].astype(str)
                    df_temp['變項名稱原始答案'] = df_temp['變項名稱原始答案'].str.replace('\r\n', '\n').str.replace('\r\r\r\n', '\n')

                    df_cpast = pd.concat([df_cpast, df_temp], ignore_index=True)
                    print(f"✅ 已讀取處理後報表：{fname}")
                except Exception as e:
                    print(f"⚠️ 讀取失敗：{fname}，錯誤原因：{e}")

        # 處理本週報表（不進行換行標準化）
        df_now = self.checklist.copy()
        df_now = df_now[keep_cols]

        # 疊合比對
        df_all = pd.concat([df_now, df_cpast], ignore_index=True)
        df_all['dup'] = df_all.duplicated(subset=key_cols, keep=False)
        df_all = df_all[(df_all['dup'] == False) & (df_all['計畫回覆'] == '')]
        df_all = df_all.drop(columns='dup').sort_values(by=['變項名稱原始答案']).reset_index(drop=True)

        # 更新 checklist
        self.checklist = df_all
        print(f"🔄 已更新 checklist，剩餘尚未處理項目：{len(self.checklist)} 筆")


    def generate_time_gap_report(self, threshold_minutes=10, output_excel=True):
        """
        掃描答題時間欄位，偵測任兩題間是否有超過 threshold_minutes 的間隔。
        僅針對完訪資料分析，並輸出報表供人工判讀。
        
        Parameters:
        - threshold_minutes: 設定時間間隔閾值（預設為10分鐘）
        - output_excel: 是否輸出 Excel 檔案
        """
        # 抽出所有欄位
        cols_all = list(self.df.columns.values)
        
        # 選出 ansTime 欄位（排除含 record 的欄位）
        cols_time = list(filter(lambda x: 'ansTime' in x and 'record' not in x, cols_all))
        cols_time = natsorted(cols_time)

        # 必要欄位（依你原始範例）
        base_cols = ['no', 'id', 'status']
        cols_sel = [col for col in base_cols if col in self.df.columns] + cols_time

        df_time = self.df[cols_sel].copy()
        df_time = df_time[df_time['status'] == '完訪: 100'].reset_index(drop=True)
        
        results = []

        for idx, row in df_time.iterrows():
            ans_times = row[cols_time]
            time_list = []

            for val in ans_times:
                try:
                    time = pd.to_datetime(val)
                except:
                    time = pd.NaT
                time_list.append(time)

            time_gaps = [None]  # 第一題沒有前一題可比
            suspicious = False
            formatted_gaps = []

            for i in range(1, len(time_list)):
                t1 = time_list[i-1]
                t2 = time_list[i]
                if pd.notnull(t1) and pd.notnull(t2):
                    delta = (t2 - t1).total_seconds() / 60
                    time_gaps.append(delta)
                    if delta > threshold_minutes:
                        suspicious = True
                        t1_str = t1.strftime("%Y/%m/%d %H:%M:%S")
                        t2_str = t2.strftime("%Y/%m/%d %H:%M:%S")
                        formatted = f"{cols_time[i-1]} = {t1_str}，{cols_time[i]} = {t2_str}"
                        formatted_gaps.append(formatted)
                else:
                    time_gaps.append(None)

            result_row = row[base_cols].to_dict()
            result_row['異常時間差存在'] = suspicious
            result_row['異常時間段明細'] = formatted_gaps
            results.append(result_row)

        df_result = pd.DataFrame(results)

        if output_excel:
            base_folder = os.path.join(self.path, f"02_check/w{self.wave}_檢誤報表")
            os.makedirs(base_folder, exist_ok=True)

            # 匯出時間異常摘要報表
            gap_path = os.path.join(base_folder, f"{self.survey_code}_w{self.wave}_ansTime_check.xlsx")
            df_result.to_excel(gap_path, index=False)
            print(f"📤 已輸出訪問時間差異報表至：{gap_path}")

            # 匯出完整時間紀錄表
            full_path = os.path.join(base_folder, f"{self.survey_code}_w{self.wave}_ansTime_data.xlsx")
            df_time.to_excel(full_path, index=False)
            print(f"📤 已輸出完整時間紀錄至：{full_path}")   


    def export_report(self, init_wave=None):
        """
        匯出本週檢誤報表，並自動排除初期週次的疊合處理。
        init_waves: 可手動指定初期週次（如 ['00','01','02']），將略過歷週報表比對。
        """
        
        if init_wave is None:
            init_wave = ['00', '01']

        # 過濾已處理過的舊報表項目
        if self.wave not in init_wave:
            self.filter_handled_items()
        
        
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
