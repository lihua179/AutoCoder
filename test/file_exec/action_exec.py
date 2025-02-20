# -*- coding: utf-8 -*-
"""
@author: Zed
@file: action_exec.py
@time: 2025/2/19 17:43
@describe:自定义描述
"""
# action_exec.py
import os
import shutil
import subprocess
import time
from datetime import datetime
from typing import List
from dataclasses import asdict
from models import (
    FileOperationInput,
    ProgramExecutionInput,
    FileOperationFeedback,
    ProgramExecutionFeedback,
    FeedbackStatus,
    ReplaceResult,
    CodeBlock,
    FileActionType,
    RequestStatus,
    OperationResponse,
    OperationRequest
)
from typing import Dict, List, Any
import json
import locale

encoding = locale.getpreferredencoding()


class ActionExecutor:
    def __init__(self, workspace: str = "."):
        self.workspace = os.path.abspath(workspace)
        os.makedirs(self.workspace, exist_ok=True)

    def execute_request(self, request:OperationRequest) -> OperationResponse:
        """执行完整请求并生成响应"""
        file_feedbacks = []
        program_feedbacks = []

        # 执行文件操作
        if request.file_operations:
            for op in request.file_operations:
                feedback = self._execute_file_operation(op)
                file_feedbacks.append(feedback)

        # 执行程序操作
        if request.program_operations:
            for op in request.program_operations:
                feedback = self._execute_program(op)
                program_feedbacks.append(feedback)

        #         request_id: str
        #     reason: str
        #     status: RequestStatus
        #     file_feedbacks: List[FileOperationFeedback] = None
        #     program_feedbacks: List[ProgramExecutionFeedback] = None
        #     completed_at: str = str(datetime.now())
        #
        return OperationResponse(request.request_id,
                                 request.reason,
                                 RequestStatus.COMPLETED.value,
                                 file_feedbacks,
                                 program_feedbacks,
                                 str(datetime.now())
                                 )


    def _execute_file_operation(self, op: FileOperationInput) -> FileOperationFeedback:
        """执行单个文件操作"""
        try:
            full_path = os.path.join(self.workspace, op.path)

            if op.action_type == FileActionType.CREATE_FILE:
                return self._create_file(full_path, op)
            elif op.action_type == FileActionType.DELETE_FILE:
                return self._delete_file(full_path, op)
            elif op.action_type == FileActionType.REPLACE_BLOCK:
                return self._replace_blocks(full_path, op)
            elif op.action_type == FileActionType.READ_FILE:
                return self._read_file(full_path, op)
            elif op.action_type == FileActionType.DELETE_DIR:
                return self._delete_file(full_path, op)
            elif op.action_type == FileActionType.LIST_DIR_TREE:
                return self._list_dir_tree(full_path, op)
            else:
                raise ValueError(f"未知文件操作类型: {op.action_type}")

        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )

    def _create_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        if os.path.exists(path):
            raise FileExistsError(f"文件已存在: {path}")

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            if op.content:
                f.write(op.content)

        return FileOperationFeedback(
            status=FeedbackStatus.SUCCESS,
            action_type=op.action_type,
            path=op.path
        )

    def _delete_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        if not os.path.exists(path):
            raise FileNotFoundError(f"路径不存在: {path}")

        if os.path.isdir(path):
            if op.recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
        else:
            os.remove(path)

        return FileOperationFeedback(
            status=FeedbackStatus.SUCCESS,
            action_type=op.action_type,
            path=op.path
        )

    def _read_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """读取指定文件内容"""
        try:
            full_path = os.path.join(self.workspace, path)

            # 验证文件存在且可读
            if not os.path.isfile(full_path):
                raise FileNotFoundError(f"文件不存在: {full_path}")

            # 使用UTF-8编码读取文件
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return FileOperationFeedback(
                status=FeedbackStatus.SUCCESS,
                action_type=op.action_type,
                path=op.path,
                content=content
            )

        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )

    def _replace_blocks(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        if not os.path.isfile(path):
            raise FileNotFoundError(f"文件不存在: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        results = []
        original_content = content
        for block in op.blocks:
            match_count = content.count(block.old_content)
            if match_count == 0:
                results.append(ReplaceResult(
                    identifier=block.identifier,
                    replaced=False,
                    matches_found=0,
                    verification_passed=False,
                    error_detail="未找到匹配内容"
                ))
                continue

            new_content = content.replace(
                block.old_content,
                block.new_content
            )
            verification = block.new_content in new_content

            content = new_content
            results.append(ReplaceResult(
                identifier=block.identifier,
                replaced=True,
                matches_found=match_count,
                verification_passed=verification
            ))

        # 写入修改后的内容
        if original_content != content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

        return FileOperationFeedback(
            status=FeedbackStatus.SUCCESS,
            action_type=op.action_type,
            path=op.path,
            replace_results=results
        )

    def _list_dir_tree(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """遍历目录并生成树形结构"""
        try:
            full_path = os.path.join(self.workspace, path)
            tree = self._build_tree(full_path)

            return FileOperationFeedback(
                status=FeedbackStatus.SUCCESS,
                action_type=op.action_type,
                path=op.path,
                dir_tree=tree
            )

        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )

    def _build_tree(self, directory: str) -> Dict[str, Any]:
        """递归构建目录树结构"""
        tree = {
            "name": os.path.basename(directory),
            "type": "directory",
            "children": []
        }

        try:
            for entry in os.listdir(directory):
                full_entry = os.path.join(directory, entry)
                if os.path.isfile(full_entry):
                    tree["children"].append({
                        "name": entry,
                        "type": "file"
                    })
                elif os.path.isdir(full_entry):
                    child_tree = self._build_tree(full_entry)
                    tree["children"].append(child_tree)
        except PermissionError as e:
            # 处理权限异常
            raise RuntimeError(f"Permission denied: {directory}") from e

        return tree



# 使用示例
if __name__ == "__main__":
    from models import OperationRequest, FileOperationInput, CodeBlock

    # 创建测试请求
    # request = OperationRequest(
    #     request_id="test_001",
    #     file_operations=[
    #         FileOperationInput(
    #             action_type=FileActionType.REPLACE_BLOCK,
    #             path="test.py",
    #             blocks=[
    #                 CodeBlock(
    #                     identifier="main_func",
    #                     old_content="print('hello')",
    #                     new_content="print('你好')"
    #                 )
    #             ]
    #         )
    #     ],
    #     program_operations=[
    #         ProgramExecutionInput(
    #             command="python test.py",
    #             timeout_seconds=5
    #         )
    #     ]
    # )
    # 创建目录树遍历请求
    executor = ActionExecutor(workspace="test_project")

    # 创建测试目录结构
    # os.makedirs("test_project/src/utils/config.py", exist_ok=True)
    # os.makedirs("test_project/src/utils/logger.py", exist_ok=True)
    # C:\Users\admin\.conda\envs\quant\python.exe
    # 执行目录遍历
    request = OperationRequest(
        request_id="dir_tree_001",
        reason='reason',
        file_operations=[
            FileOperationInput(
                action_type=FileActionType.LIST_DIR_TREE,
                path="src/",
                recursive=True
            )
        ]
    )
    # print(request.to_json())
    response = executor.execute_request(request)
    # 发送结束结构化文本给api
    response.to_json()
    # # print(response)
    # # 输出目录树结构
    # print(json.dumps(response, indent=2, ensure_ascii=False))
