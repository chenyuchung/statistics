# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 17:39:37 2025

@author: cyc
"""

import pandas as pd
from scipy.stats import chisquare
from datetime import datetime

class RakingWeighter:
    def __init__(self, df, pop_df, init_weight=1, final_weight_name='final_weight',
                 project_name='project', date_str=None):
        self.df = df.copy()
        self.pop_df = pop_df.copy()
        self.variables = pop_df['variable'].unique().tolist()
        self.init_weight = init_weight
        self.final_weight_name = final_weight_name
        self.project_name = project_name
        self.date_str = date_str or datetime.today().strftime('%Y%m%d')
        self.iteration = 0
        self.history = []
        self.last_trimming_bounds = None
        self.log_filename = f"{self.project_name}_{self.final_weight_name}_{self.date_str}.txt"
        self.log_f = open(f"/mnt/data/{self.log_filename}", "w", encoding="utf-8")

        if init_weight == 1:
            self.df["wt0"] = 1
        elif isinstance(init_weight, str) and init_weight in df.columns:
            self.df["wt0"] = df[init_weight]
        else:
            raise ValueError("初始權重設定錯誤")

        print(f"加權：初始權值為{init_weight}，以變項 {self.variables} 進行加權", file=self.log_f)
        print("\n", file=self.log_f)

    def get_pop_dict(self, var):
        sub = self.pop_df[self.pop_df['variable'] == var]
        return dict(zip(sub['category'], sub['proportion']))

    def chi_report(self, var, wt_col):
        pop_dist = self.get_pop_dict(var)
        total_n = len(self.df)
        group = self.df.groupby(var)[wt_col].sum().round()
        expected = {k: round(v * total_n) for k, v in pop_dist.items()}
        obs = group.reindex(expected.keys()).fillna(0).astype(int)
        exp = pd.Series(expected)
        table = pd.DataFrame({'Weighted': obs, 'Expected': exp})
        result = chisquare(obs, f_exp=exp, axis=0, ddof=0, nan_policy='propagate', sum_check=False)

        print(f"[ 卡方檢定：{var} ]", file=self.log_f)
        print(table, file=self.log_f)
        print("", file=self.log_f)
        print(result, file=self.log_f)
        print("", file=self.log_f)

        print(f"[ 卡方檢定：{var} ]")
        print(table)
        print(result)
        print("")

    def rake_once(self):
        prev_col = f"wt{self.iteration}"

        for var in self.variables:
            next_col = f"wt{self.iteration + 1}"
            self.df[next_col] = self.df[prev_col]
            pop_dist = self.get_pop_dict(var)
            total_sum = self.df[prev_col].sum()

            for cat, prop in pop_dist.items():
                mask = self.df[var] == cat
                group_sum = self.df.loc[mask, prev_col].sum()
                if group_sum > 0:
                    factor = (total_sum * prop) / group_sum
                    self.df.loc[mask, next_col] = self.df.loc[mask, prev_col] * factor

            self.iteration += 1
            self.history.append(next_col)

            print("", file=self.log_f)
            print("************ 第 " + str(self.iteration) + " 輪加權 ************", file=self.log_f)
            print("")
            print("************ 第 " + str(self.iteration) + " 輪加權 ************")

            self.chi_report(var, next_col)
            prev_col = next_col

    def raking(self):
        cont = 'y'
        while cont.lower() == 'y':
            self.rake_once()
            cont = input("是否繼續下一輪加權？(y/n)：")

        final_wt = self.history[-1]
        total_sample = len(self.df)
        correction = total_sample / self.df[final_wt].sum()
        self.df[self.final_weight_name] = self.df[final_wt] * correction

        print(f"\n加權完成。最終權重欄位：{self.final_weight_name}")
        print(f"完整記錄寫入：{self.log_filename}")
        self.log_f.close()

    def weight_trimming(self, base_weight_col, trimmed_col_name, min_w=None, max_w=None, auto_skip_threshold=None):
        var = self.df[base_weight_col].var()
        mean = self.df[base_weight_col].mean()
        wl = var / (mean ** 2)

        print("", file=self.log_f)
        print(f"===== 權重削減流程（來源：{base_weight_col}）====", file=self.log_f)
        print(f"初始 weighting loss：{wl:.4f}\n", file=self.log_f)

        if auto_skip_threshold is not None and wl < auto_skip_threshold:
            print(f"weighting loss < {auto_skip_threshold}，跳過 trimming。", file=self.log_f)
            print(f"weighting loss < {auto_skip_threshold}，跳過 trimming。")
            return

        cont = input("是否進行權重削減？(y/n)：")
        if cont.lower() != 'y':
            print("使用者選擇跳過 trimming。", file=self.log_f)
            print("使用者選擇跳過 trimming。")
            return

        self.trim_weights(weight_col=base_weight_col, min_w=min_w, max_w=max_w, final_trimmed_name=trimmed_col_name)

        cont2 = input("是否對削減結果進行加權？(y/n)：")
        if cont2.lower() == 'y':
            self.init_weight = trimmed_col_name
            self.final_weight_name = trimmed_col_name + '_raked'
            self.df[self.final_weight_name] = None
            self.raking()

    def trim_weights(self, weight_col=None, min_w=None, max_w=None, final_trimmed_name='trimmed', reuse_last=False):
        import numpy as np

        weight_col = weight_col or self.final_weight_name
        total_sample = len(self.df)
        var = self.df[weight_col].var()
        mean = self.df[weight_col].mean()
        wl = var / (mean ** 2)

        print("", file=self.log_f)
        print(f"===== Trimming（使用 {weight_col}）=====", file=self.log_f)
        print(f"初始 weighting loss 為：{wl:.4f}", file=self.log_f)
        print("", file=self.log_f)

        if reuse_last and self.last_trimming_bounds:
            min_w, max_w = self.last_trimming_bounds
        else:
            min_w = float(input("請輸入最小值：")) if min_w is None else min_w
            max_w = float(input("請輸入最大值（不超過最小值*10）：")) if max_w is None else max_w
            self.last_trimming_bounds = (min_w, max_w)

        print(f"使用 trimming 上下限：min={min_w}, max={max_w}", file=self.log_f)

        w = self.df[weight_col].copy()
        round_count = 0

        while w.max() > max_w:
            capped = w.clip(lower=min_w, upper=max_w)
            loss = w.sum() - capped.sum()
            n_uncapped = (capped < max_w).sum()
            compensation = loss / n_uncapped if n_uncapped > 0 else 0
            w = capped + (capped < max_w) * compensation
            round_count += 1

        self.df[final_trimmed_name] = w
        wl_after = w.var() / (w.mean() ** 2)

        print("", file=self.log_f)
        print(f"完成 trimming，共處理 {round_count} 輪。", file=self.log_f)
        print(f"trimming 後 weighting loss 為：{wl_after:.4f}", file=self.log_f)
        print("", file=self.log_f)

        print(f"完成 trimming，共處理 {round_count} 輪。")
        print(f"trimming 後 weighting loss 為：{wl_after:.4f}")

        for var in self.variables:
            self.chi_report(var, final_trimmed_name)

    def weight_description(self, var_weight):
        print(f'=== 權值 {var_weight} 描述性統計 ===', file=self.log_f)
        print(f'樣本數：{len(self.df)}', file=self.log_f)
        print(f'最大值：{self.df[var_weight].max():.4f}', file=self.log_f)
        print(f'最小值：{self.df[var_weight].min():.4f}', file=self.log_f)
        print(f'中位數：{self.df[var_weight].median():.4f}', file=self.log_f)
        print(f'平均數：{self.df[var_weight].mean():.4f}', file=self.log_f)
        print(f'變異數：{self.df[var_weight].var():.4f}', file=self.log_f)
        print(f'標準差：{self.df[var_weight].std():.4f}', file=self.log_f)

        print(f'=== 權值 {var_weight} 描述性統計 ===')
        print(f'樣本數：{len(self.df)}')
        print(f'最大值：{self.df[var_weight].max():.4f}')
        print(f'最小值：{self.df[var_weight].min():.4f}')
        print(f'中位數：{self.df[var_weight].median():.4f}')
        print(f'平均數：{self.df[var_weight].mean():.4f}')
        print(f'變異數：{self.df[var_weight].var():.4f}')
        print(f'標準差：{self.df[var_weight].std():.4f}')

    def get_weights(self):
        return self.df[self.final_weight_name]

    def save_log_path(self):
        return f"/mnt/data/{self.log_filename}"

    def export_weight_tables(self, weight_col=None, file_path=None):
        df = self.df
        pop_df = self.pop_df
        weight_col = weight_col or self.final_weight_name
        variables = self.variables
        file_path = file_path or f"/mnt/data/{self.project_name}_{weight_col}_{self.date_str}.xlsx"

        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

        for mode in ["unweighted", "weighted"]:
            all_records = []

            for var in variables:
                sub_df = df[df[var].notna()].copy()
                pop_dist = pop_df[pop_df['variable'] == var].set_index('category')['proportion'].to_dict()
                categories = sorted(set(sub_df[var].unique()) | set(pop_dist.keys()))

                if mode == "unweighted":
                    count = sub_df[var].value_counts().reindex(categories).fillna(0)
                    valid_total = count.sum()
                    percent = count / valid_total
                    expected = pd.Series({k: v * valid_total for k, v in pop_dist.items()}).reindex(categories).fillna(0)
                    try:
                        chi2, p = chisquare(count, f_exp=expected, sum_check=False)
                    except TypeError:
                        chi2, p = chisquare(count, f_exp=expected)
                else:
                    count = sub_df.groupby(var)[weight_col].sum().reindex(categories).fillna(0)
                    valid_total = count.sum()
                    percent = count / valid_total
                    expected = pd.Series({k: v * valid_total for k, v in pop_dist.items()}).reindex(categories).fillna(0)
                    try:
                        chi2, p = chisquare(count, f_exp=expected, sum_check=False)
                    except TypeError:
                        chi2, p = chisquare(count, f_exp=expected)

                print(f"[{mode}] variable: {var} 有效樣本數：{valid_total:.0f}", file=self.log_f)
                print(f"[{mode}] variable: {var} 有效樣本數：{valid_total:.0f}")

                for cat in categories:
                    all_records.append({
                        "variable": var,
                        "category": cat,
                        "count": count[cat],
                        "percent": percent[cat] * 100,
                        "pop%": pop_dist.get(cat, 0) * 100,
                        "chi2": "",
                        "p_value": ""
                    })

                all_records.append({
                    "variable": var,
                    "category": "Chi-square result",
                    "count": "",
                    "percent": "",
                    "pop%": "",
                    "chi2": chi2,
                    "p_value": p
                })

            pd.DataFrame(all_records).to_excel(writer, sheet_name=mode, index=False)

        writer.close()
        print(f"報表已輸出至：{file_path}")

