# -*- coding: utf-8 -*-
"""
@author: Zed
@file: data_collector.py.py
@time: 2025/2/20 14:13
@describe:自定义描述
"""
import time

if __name__ == '__main__':
    count = 0
    while True:
        count += 1
        print(f'数据采集-{count}')
        time.sleep(1)
        if count > 40:
            print(f'退出程序')
            raise ValueError('error???')
            # break
