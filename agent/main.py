# -*- coding: utf-8 -*-
import json
import re
import time
from typing import Any, Dict
from chat_api import ChatAPI
from file_exec import FileExecutor
from program_exec import ParallelExecutor, ProgramCheck, ProgramCheckFeedback

from data_struct import (
    Parser,
    OperationRequest,
    OperationResponse,
    FeedbackStatus,
    FileOperationInput,
    FileOperationFeedback,
    CodeBlock,
    ReplaceResult,
    FileActionType,
    WorkFinishNote,
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
    match = re.search(r'```json\s*(.*?)\s*```', ai_response, re.DOTALL)

    if match:
        json_content = match.group(1)  # 提取匹配的内容
        try:
            # 尝试将字符串解析为JSON对象
            structured_data = json.loads(json_content)
            return structured_data
        except json.JSONDecodeError:
            raise ValueError("无法解析提取的JSON内容，确保其为有效的JSON格式。")
    else:
        raise ValueError("未找到有效的JSON结构化内容。")


class AutoCoder:
    # 关于配置信息，暂时先写死，等稳定后改用config配置
    def __init__(self, work_path='', chat_content=''):
        with open('prompt.txt') as f:
            prompt = f.read()
        self.work_path = work_path
        self.chat_content = chat_content  # 需求
        self.chat_api = ChatAPI(api_key='', prompt=prompt)
        self.file_exec = FileExecutor(self.work_path)
        self.cmd_check = ProgramCheck()  # 需要api调用接口
        self.cmd_exec = ParallelExecutor()
        # self.cmd_exec = ParallelExecutor(self.cmd_check)

        # self.feedback_gen = FeedbackGenerator()

    def send_feedback(self, res):
        #     def to_dict(self):
        #         return {
        #             "name": self.name,
        #             "runtime": self.runtime,
        #             "stdout": self.stdout,
        #             "stderr": self.stderr,
        #         }
        # class ProgramCheckFeedback:
        #     name: str
        #     runtime: float
        #     stdout: str
        #     stderr: str
        print('send_feedback:', res)

        res['type'] = 'program_check'
        program_check_res = self.chat_api.chat(str(res))
        # 转字典
        # try:
        program_check_json = extract_json_content(program_check_res)
        # except ValueError as e:
        #     program_check_res = self.chat_api.chat('ValueError: '+str(e))
        # 转结构
        # {
        #             "name": self.name,
        #             "terminal": self.terminal,
        #             "reason": self.reason
        #         }

        program_check_req: ProgramCheckRequest = Parser.parse_request(program_check_json)
        program_check_list = program_check_req.program_operations
        program_check_list = [{'name': 'xxx', 'terminal': 'xxx', 'reason': 'xxx', },

                              ]
        # program_operations
        # {
        #             "name": self.name,
        #             "terminal": self.terminal,
        #             "reason": self.reason
        #         }
        # time.sleep(10)
        print('受到api')
        # 假设api交互时间10s过去了，并且截断‘模型训练’
        # return
        return ['数据采集']

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
            try:
                structured_data = extract_json_content(response)
            except ValueError as e:
                struct_res='ValueError: ' + str(e)
                continue
                # program_check_res = self.chat_api.chat('ValueError: ' + str(e))
            print()
            print('——' * 50)
            print('ai指令')
            print(json.dumps(structured_data, ensure_ascii=False, indent=4))
            # print()
            # ToDo 解析报错后，应该提供demo作为参考，重新对话
            # operate,check_program,finish

            operation_req = Parser.parse_request(structured_data)
            if operation_req.type == 'finish':
                # operation_req:WorkFinishNote
                summary = operation_req.summary
                chat_his_list = self.chat_api.req
                print('对话结束，收尾工作')
                with open(self.work_path + '/.chat_his_list.txt', 'w') as f:
                    f.write(str(chat_his_list))
                with open(self.work_path + '/.summary.txt', 'w') as f:
                    f.write(summary)
                print('对话结束，收尾工作')
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
            print('执行完动作')
            print(struct_res)

        # 继续优化模式：
        #   加载保存的上次对话过程
        #       继续描述新的需求
        # while True:
        #     接受结构化指令:任务结束/任务进行
        #     if 任务结束:
        #           存储对话历史，生成程序说明书，文档
        #          break
        #     解析为动作对象实例
        #     执行动作（创建文本，执行程序）
        #     执行完毕，获取反馈
        pass


# executor = ParallelExecutor()
#     program_check = ProgramCheck(send_feedback, 3)
#     results = executor.execute_programs(configs, program_check)

#     def send_feedback(res):
#         print('send_feedback:', res)
#         time.sleep(10)
#         print('受到api')
#         # 假设api交互时间10s过去了，并且截断‘模型训练’
#         # return
#         return ['数据采集']
#         # pass
#
#
#     # 执行程序
#     executor = ParallelExecutor()
#     program_check = ProgramCheck(send_feedback, 3)
#     results = executor.execute_programs(configs, program_check)
#     # results就是执行完的程序实例化，转给程序结束反馈对象
#     # 打印结果
#     for name, result in results.items():
#         print(f"\n程序: {name}")
#         print(f"状态: {result.status}")
#         print(f"执行时间: {result.exec_time:.2f}s")
#         print(f"返回码: {result.return_code}")
#         print(f"标准输出:\n{result.stdout[:200]}...")
#         print(f"错误输出:\n{result.stderr[:200]}...")
#     program_list = list(results.values())
#     print(program_list)
# 示例用法
if __name__ == "__main__":
    work_path = fr"\test_work"
    chat_content = f'请你帮我在指定文件夹{work_path}下编写一个图书管理系统,其中python编译器地址为xxx'
    auto_coder = AutoCoder(work_path=work_path, chat_content=chat_content)
    auto_coder.run()
