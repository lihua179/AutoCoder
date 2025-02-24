# -*- coding: utf-8 -*-
"""
@author: Zed
@file: main.py
@time: 2025/2/24 19:18
@describe:自定义描述
"""
from auto_coder import AutoCoder

if __name__ == "__main__":

    work_path = fr"C:\ai_work"
    chat_content = fr'请你在{work_path}文件夹下用python编写一个贪吃蛇游戏'

    with open('prompt.txt') as f:
        prompt = f.read()
    chat_api_config = dict(api_key='sk-xxx',
                           base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
                           model='deepseek-r1',
                           prompt=prompt)

    auto_coder = AutoCoder(work_path=work_path, chat_content=chat_content, chat_api_config=chat_api_config)
    # auto_coder.load_his_chat() #加载历史对话，继续上次对话
    auto_coder.run()
