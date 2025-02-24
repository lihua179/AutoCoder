# -*- coding: utf-8 -*-
"""
@author: Zed
@file: chat_api.txt
@time: 2024/11/13 0:46
@describe: 提供与外部对话的回调函数接口
"""

import sys
from openai import OpenAI



__all__ = [
    "ChatAPI",
    "CharPrinter"
]


# 其他代码...
class CharPrinter:
    def __init__(self, max_width=40):
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
            try:
                sys.stdout.write(''.join(self.buffer))
                sys.stdout.flush()
            except UnicodeEncodeError as e:
                print(e)
                pass
            self.buffer = []
            self.visible_length = 0

    def dynamic_single_callback(self, c):
        self.add_char(c)
        self.flush()


class ChatAPI:
    def __init__(self, api_key, model="deepseek-r1",
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 callback_content=None, callback_reason_content=None, prompt=''):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.req = [{"role": 'system', "content": prompt}]
        self.printer = CharPrinter(max_width=20)  # 初始化打印机
        self.callback_content = callback_content
        self.callback_reason_content = callback_reason_content

    def add_assistant_message(self, assistant_response=None):
        """添加助手的回答"""
        self.req.append({'role': 'assistant', 'content': assistant_response})

    def add_user_message(self, message):
        """添加用户消息到请求中，并可选地添加助手的回答"""
        self.req.append({'role': 'user', 'content': message})

    def get_response(self):
        client = OpenAI(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key=self.api_key,
            # 如何获取API Key：https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key
            base_url=self.base_url
        )
        responses = client.chat.completions.create(
            model=self.model,  # 此处以 deepseek-r1 为例，可按需更换模型名称。
            messages=self.req,
            stream=True,
        )
        #     for chunk in stream:
        #         # chunk_message = chunk.choices[0].delta
        #         #     if not chunk_message.content:
        #         #         continue
        #         if chunk.choices[0].delta.content is not None:
        #             text += str(chunk.choices[0].delta.content)
        #             print(chunk.choices[0].delta.content, end="")
        res_total = ''
        for response in responses:
            try:
                reason = response.choices[0].delta.reasoning_content
                if reason:
                    self.reason_callback(reason)  # 调用reason_callback
            except Exception as e:
                pass

            res = response.choices[0].delta.content
            if res:
                res_total += res
                self.callback_stream_single(res)  # 调用callback_stream_single
        return res_total

    def chat(self, user_message):
        """与外部进行对话的接口"""
        self.add_user_message(user_message)
        assistant_response = self.get_response()
        self.add_assistant_message(assistant_response)  # 添加助手的回答
        return assistant_response

    def callback_stream_single(self, res: str):
        """打印单个响应"""
        # try:
        self.printer.dynamic_single_callback(res)
        # except UnicodeEncodeError as e:
        #     pass
        if self.callback_content:
            self.callback_content(res)

    def reason_callback(self, reason):
        """打印推理内容"""
        # try:
        self.printer.dynamic_single_callback(reason)
        # except UnicodeEncodeError as e:
        #     pass
        if self.callback_reason_content:
            self.callback_reason_content(reason)


