# -*- coding: utf-8 -*-
"""
Created on Wed Apr 23 17:10:48 2025

PDF binder

@author: cyc
"""
import os
from PyPDF2 import PdfMerger

path = r'D:\tscs'
os.chdir(path)

# pass the path of the output final file.pdf and the list of paths
def merge_pdf(out_path: str, extracted_files: list [str]):
    merger   = PdfMerger()
    
    for pdf in extracted_files:
        merger.append(pdf)

    merger.write(out_path)
    merger.close()

merge_pdf('./tscs1985_2024Binder.pdf',
          ['./tscs1985_2021Binder.pdf',
           './過去資料/tscs22/download-tscs221.pdf',
           './過去資料/tscs22/download-tscs222.pdf',
           './過去資料/tscs23/download-tscs231.pdf',
           './過去資料/tscs23/download-tscs232.pdf',
           './過去資料/tscs24/00_tscs241數位社會問卷_送印_20240504_binde用.pdf',
           './過去資料/tscs24/tscs242科技與風險_正式問卷定稿_binder用.pdf'
           ])