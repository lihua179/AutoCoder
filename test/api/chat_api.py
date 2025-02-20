# -*- coding: utf-8 -*-
"""
@author: Zed
@file: main.py
@time: 2024/11/13 0:46
@describe:自定义描述
"""
import os
import time

import openai
import os
import dashscope
from datetime import datetime

import sys
import re
from time import sleep


class CharPrinter:
    def __init__(self, max_width=80):
        self.max_width = max_width
        self.buffer = []  # 缓存当前行的字符列表
        self.visible_length = 0  # 当前行可见字符长度

    def _is_ansi(self, char):
        """判断是否是ANSI控制符"""
        return '\x1b' <= char <= '\x1f' or (char == '\\' and len(self.buffer) > 0 and self.buffer[-1] == '\\')

    def add_char(self, char):
        """添加单个字符到输出缓冲区"""
        if char in ('\n', '\r'):
            self.flush()
            self.buffer.append(char)
            return

        # 计算新增字符的可见长度
        add_len = 1 if not self._is_ansi(char) else 0
        new_visible = self.visible_length + add_len

        # 处理自动换行
        if new_visible > self.max_width:
            self.flush()

        self.buffer.append(char)
        self.visible_length = new_visible

    def flush(self):
        """强制刷新当前行"""
        if self.buffer:
            sys.stdout.write(''.join(self.buffer))
            sys.stdout.flush()
            self.buffer = []
            self.visible_length = 0

    def dynamic_single_callback(self, c):
        self.add_char(c)
        self.flush()


printer = CharPrinter(max_width=20)  # 设置每行最大40字符
printer2 = CharPrinter(max_width=20)  # 设置每行最大40字符


def reason_callback(reason):
    printer.dynamic_single_callback(reason)


def ask(ask_info, req, callback_stream_single=None, callback_stream_continue=None, callback_result_total=None,
        reason_callback=None):
    #     req = [
    #         {'role': 'system', 'content': 'you are a helpful assistant'},
    #         {'role': 'user', 'content': '你是谁？'}
    #     ]
    req.append({'role': 'user', 'content': ask_info})
    responses = dashscope.Generation.call(
        # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
        api_key='sk-xxx',
        model="deepseek-r1",
        messages=req,
        result_format='message',
        stream=True,
        incremental_output=True
    )
    #
    res_total = ''
    for response in responses:
        reason = response.output.choices[0].message.reasoning_content
        if reason_callback:
            reason_callback(reason)
        res = response.output.choices[0].message.content
        if res:
            res_total += res
            if callback_stream_single:
                callback_stream_single(res)
            if callback_stream_continue:
                callback_stream_continue(res_total)
        if callback_result_total:
            callback_result_total(res_total)

    req.append({
        "role": 'assistant',
        "content": res_total
    }, )
    return req


count = 0


def callback_stream_single(res: str):
    printer2.dynamic_single_callback(res)


# callback_result_total = None
#

def init_req(prompt):
    return [{"role": 'system', "content": prompt}]


def main():
    # ask_info0 = r'请你模拟整个过程，假装帮我在指定的文件夹下通过pygame创建贪吃蛇游戏，指定文件目录：C:\Users\admin\PycharmProjects\Work2024\AProject\A\aaa世界规律\期货认知\程序\ai\code_agent\test，' \
    #             r'指定的python编译器：C:\Users\admin\.conda\envs\quant\python.exe，然后模拟计算出api2user,user2api的结果'
    with open('prompt2.txt') as f:
        ask0 = f.read()
    with open('struct_string.py', encoding='utf-8') as f:
        ask1 = f.read()
    ask_info = ask0 + r'上面时是我给你的结构化文本的文档，现在我要利用这个结构化文本与大语言模型的api进行交互，让api提供结构指令，本地模块识别指令然后执行，以及将执行结构转为结构化文本并反馈于api，从而' \
                      r'实现api-system的沟通交互，来协同完成自动化代码开发，现在我需要你帮助我完成system的开发工作，我已经完成一部分代码了，但是我觉得代码有bug，不能' \
                      r'完美的跑起来，你帮我重新编写，重构代码，符合文档要求：' + ask1
    ask_total = ''
    print(ask_info)
    # for a in ask_info0:
    #     ask_total += a
    #     print(f'\r[{datetime.now()}] result stream:', ask_total, end=' ')
    #     time.sleep(0.01)
    print()
    prompt = '你是一名协助用户共同完成代码全流程自动化开发的工程师'
    req = init_req(prompt)
    # print(f'[{datetime.now()}] ask:{ask_info0}')
    while True:
        req = ask(ask_info, req, callback_stream_single,
                  reason_callback=reason_callback)
        ask_info = input('input content:')
        ask_info1 = input('input content:')
    # req = ask(ask_info1, req, callback_stream_single, callback_stream_continue, callback_result_total)


if __name__ == '__main__':
    main()
