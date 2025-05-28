# -*- coding: utf-8 -*-
"""
Created on Mon May 26 10:35:52 2025

QR code 產生器

@author: cyc
"""

#pip install qrcode[pil]

import qrcode
import sys, os

path = input('請輸入QRcode輸出路徑：')
filename = input('請輸入圖檔名：')

os.chdir(path)

# 要轉成 QR Code 的資料
data = input('請輸入要轉成QRcode的網址：')

# 建立 QR Code 物件
qr = qrcode.QRCode(
    version=1,  # 控制大小（1~40），數字越大越密
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # 容錯率（L/M/Q/H）
    box_size=10,  # 每個「點」的像素數
    border=4  # 邊框寬度（最少 4）
)

qr.add_data(data)
qr.make(fit=True)

# 產生圖片
img = qr.make_image(fill_color="black", back_color="white")

# 儲存檔案
img.save('./' + filename + '.png')
