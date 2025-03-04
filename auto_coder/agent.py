# -*- coding: utf-8 -*-
import json
import re

from typing import Any, Dict
from chat_api import ChatAPI
from file_exec import FileExecutor
from program_exec import ParallelExecutor, ProgramCheck, ProgramCheckFeedback
import os
from data_struct import (
    Parser,
    OperationResponse,
    FileOperationFeedback,
    ProgramCheckRequest

)


def extract_json_content(ai_response: str) -> Dict[str, Any]:
    """
    提取AI返回的结构化JSON内容。

    参数:
    ai_response (str): AI返回的内容，包含JSON格式的结构化文本。

    返回:
    Dict[str, Any]: 提取的结构化字段字典。
    """
    # 使用正则表达式提取JSON内容
    match = re.search(r'#####--\s*(.*?)\s*--#####', ai_response, re.DOTALL)

    if match:
        json_content = match.group(1)  # 提取匹配的内容
        try:
            # 尝试将字符串解析为JSON对象
            structured_data = json.loads(json_content)
            return structured_data
        except json.JSONDecodeError:
            raise ValueError("无法正确解析提取的JSON内容，确保其为有效的JSON格式（####--json内容--####）。")
    else:
        raise ValueError("未找到有效的JSON结构化内容，确保其为有效的JSON格式（####--json内容--####）。")


class AutoCoder:
    # 关于配置信息，暂时先写死，等稳定后改用config配置
    def __init__(self, work_path='', chat_content='', chat_api_config: dict = None, chat_path='', task_name=''):
        self.task_name = task_name
        self.work_path = work_path
        self.chat_content = chat_content  # 需求
        self.chat_api = ChatAPI(**chat_api_config)
        self.chat_path = chat_path
        self.file_exec = FileExecutor(self.work_path)
        self.cmd_check = ProgramCheck()  # 需要api调用接口
        self.cmd_exec = ParallelExecutor()

    def load_his_chat(self):

        with open(self.chat_path + '\\' + self.task_name, errors='ignore') as f:
            res = f.read()
        self.chat_api.req = eval(res)

    def save_chat_his(self):
        chat_his_list = self.chat_api.req

        base_chat_path = self.chat_path + '\\' + self.task_name
        # print('对话结束，收尾工作')
        if not os.path.exists(base_chat_path):
            os.makedirs(base_chat_path)
        with open(base_chat_path + '\\' + 'chat_his_list.txt', 'w', errors='ignore') as f:
            f.write(str(chat_his_list))

    def save_tail(self, chat_his_list, summary):
        print('对话结束，收尾工作')
        base_chat_path = self.chat_path + '\\' + self.task_name
        # print('对话结束，收尾工作')
        if not os.path.exists(base_chat_path):
            os.makedirs(base_chat_path)
        with open(base_chat_path + '\\' + 'chat_his_list.txt', 'w', errors='ignore') as f:
            f.write(str(chat_his_list))
        with open(base_chat_path + '\\' + 'summary.txt', 'w', errors='ignore') as f:
            f.write(summary)

    def run(self):
        # 开始构建模式：
        # 读取prompt
        # 描述需求
        # while True:
        #     接受结构化指令:任务结束/任务进行
        #     if 任务结束:
        #           存储对话历史，生成程序说明书，文档
        #          break
        #     解析为动作对象实例
        #     执行动作（创建文本，执行程序）
        #     执行完毕，获取反馈
        struct_res = self.chat_content
        while True:
            response = self.chat_api.chat(struct_res)
            self.save_chat_his()
            try:
                structured_data = extract_json_content(response)
            except ValueError as e:
                print('error:start', response, 'error_end')
                struct_res = 'ValueError: ' + str(
                    e) + '''[系统报错]：你通过api传输的结构化文本形式错误，没有按照指定的文本格式返回结构化数据（#####--结构化文本内容xxx--#####）（系统解析结构化json文本的方式：match = re.search(r'#####--\s*(.*?)\s*--#####', ai_response, re.DOTALL)
    if match:
        json_content = match.group(1)  # 提取匹配的内容）！系统无法读取'''
                print('结构化输出报错：', struct_res)
                continue
            print()
            print('——' * 50)
            print('ai指令:')
            try:
                print(json.dumps(structured_data, ensure_ascii=False, indent=4))
            except UnicodeEncodeError as e:
                pass

            operation_req = Parser.parse_request(structured_data)
            if operation_req.type == 'finish' or operation_req.type == 'completed':
                summary = operation_req.summary
                chat_his_list = self.chat_api.req
                self.save_tail(chat_his_list, summary)
                # 保存对话历史，文档
                break
            file_actions = operation_req.file_operations
            file_results = []
            for action in file_actions:
                file_operation_feed: FileOperationFeedback = self.file_exec.execute_file_operation(action)
                file_results.append(file_operation_feed)

            program_operations = operation_req.program_operations
            program_results = list(self.cmd_exec.execute_programs(program_operations).values())
            operation_res = OperationResponse(
                request_id=operation_req.request_id,
                reason=operation_req.reason,
                file_actions_result=file_results,
                program_execs_result=program_results
            )
            struct_res = operation_res.to_structured_text()
            print()
            print('——' * 50)
            print('动作执行完毕')
            try:
                print(struct_res)
            except UnicodeEncodeError as e:
                pass


#
if __name__ == "__main__":
    work_path = fr"\task_xxx"

    chat_content = fr"""请你在{work_path}文件夹下xxx"""
    chat_path = fr"\chat_path"
    prompt_path = '.\prompt.txt'
    task_name = 'task_xxx'
    with open(prompt_path) as f:
        prompt = f.read()

    chat_api_config = dict(api_key='sk-',
                           base_url='https://',
                           model='claude-3-7-sonnet-20250219',
                           prompt=prompt)

    auto_coder = AutoCoder(
        work_path=work_path,
        chat_content=chat_content,
        chat_api_config=chat_api_config,
        chat_path=chat_path,
        task_name=task_name, )
    # auto_coder.load_his_chat()  # 加载历史对话，继续上次对话
    auto_coder.run()
