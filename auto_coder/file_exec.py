# -*- coding: utf-8 -*-
"""
@author: Zed
@file: file_exec.txt
@time: 2025/2/21 12:34
@describe:自定义描述
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict
import os
import shutil
import locale
import unittest

encoding = locale.getpreferredencoding()

MAX_LENGTH = 5000  # 设置最大字符长度
N = MAX_LENGTH // 2  # 计算前n个和后n个字符的长度

__all__ = [
    "FileExecutor",
    "FileOperationInput",
    "FileActionType",
    "FileOperationFeedback",
    "ReplaceResult"
]


def is_valid_extension(filename):
    """检查文件后缀是否有效"""
    valid_extensions = ['.md', '.py', '.txt', '.log', '.csv', 'json']
    return any(filename.endswith(ext) for ext in valid_extensions)


def is_check_file(filename):
    """检查文件后缀是否有效"""
    valid_extensions = ['.txt', '.log', '.csv']
    return any(filename.endswith(ext) for ext in valid_extensions)


def read_file_with_limit(full_path):
    """读取文件内容，限制字符长度"""
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if len(content) > MAX_LENGTH:
            return content[:N] + '...' + content[-N:]  # 取前n个和后n个字符
        return content


@dataclass
class ReplaceResult:
    """单个区块替换结果"""
    identifier: str
    replaced: bool  # 是否成功替换
    matches_found: int  # 找到的匹配数量
    verification_passed: bool  # 替换后校验是否通过
    error_detail: Optional[str] = None

    def to_dict(self):
        return {
            "id": self.identifier,
            "replaced": self.replaced,
            "matches": self.matches_found,
            "verified": self.verification_passed,
            "error": self.error_detail
        }


class FileActionType(Enum):
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    READ_FILE = "read_file"
    REPLACE_FILE = "replace_file"  # 区块替换操作
    CREATE_DIR = "create_directory"
    DELETE_DIR = "delete_directory"
    LIST_DIR_TREE = "list_tree"


@dataclass
class CodeBlock:
    """代码区块标识（通过函数名/唯一标识定位）"""
    identifier: str  # 如函数名：def my_function()
    old_content: str  # 需要匹配的原始代码
    new_content: str  # 替换后的新代码

    def to_dict(self):
        return {
            "id": self.identifier,
            "old": self.old_content,
            "new": self.new_content
        }


class FeedbackStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


@dataclass
class FileOperationFeedback:
    """文件操作的反馈结果"""
    status: FeedbackStatus
    action_type: FileActionType
    path: str
    content: Optional[str] = None
    dir_tree: Optional[Dict] = None
    replace_results: Optional[List[ReplaceResult]] = None
    error_detail: Optional[str] = None

    def to_dict(self):
        return {
            "status": self.status.value,
            "action": self.action_type.value,
            "path": self.path,
            "content": self.content,
            "dir_tree": self.dir_tree,
            "replaces": [r.to_dict() for r in self.replace_results] if self.replace_results else None,
            "error": self.error_detail
        }


@dataclass
class FileOperationInput:
    action_type: FileActionType
    path: str
    blocks: Optional[List[CodeBlock]] = None  # 仅REPLACE_BLOCK时使用
    content: Optional[str] = None
    recursive: bool = False
    request_reason: Optional[str] = None

    def to_dict(self):
        return {
            "action": self.action_type.value,
            "path": self.path,
            "blocks": [b.to_dict() for b in self.blocks] if self.blocks else None,
            "content": self.content,
            "recursive": self.recursive,
            "reason": self.request_reason
        }


class FileExecutor:

    def __init__(self, workspace: str = "."):
        self.workspace = os.path.abspath(workspace)
        os.makedirs(self.workspace, exist_ok=True)

    def execute_file_operation(self, op: FileOperationInput) -> FileOperationFeedback:
        """执行单个文件操作"""
        try:
            # print(op.action_type.value,FileActionType.DELETE_DIR.value)
            full_path = os.path.join(self.workspace, op.path)

            if op.action_type.value == FileActionType.CREATE_FILE.value:
                return self.create_file(full_path, op)
            elif op.action_type.value == FileActionType.DELETE_FILE.value:
                return self.delete_file(full_path, op)
            elif op.action_type.value == FileActionType.REPLACE_FILE.value:
                return self.replace_blocks(full_path, op)
            elif op.action_type.value == FileActionType.READ_FILE.value:
                return self.read_file(full_path, op)
            elif op.action_type.value == FileActionType.CREATE_DIR.value:
                return self.create_directory(full_path, op)
            elif op.action_type.value == FileActionType.DELETE_DIR.value:
                return self.delete_directory(full_path, op)
            elif op.action_type.value == FileActionType.LIST_DIR_TREE.value:
                return self.list_dir_tree(full_path, op)
            else:
                raise ValueError(f"未知文件操作类型: {op.action_type}")

        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )

    def create_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
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

    def delete_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
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

    def read_file(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """读取指定文件内容"""
        try:
            full_path = os.path.join(self.workspace, path)
            # 验证文件存在且可读
            if not os.path.isfile(full_path):
                return FileOperationFeedback(
                    status=FeedbackStatus.FAILURE,
                    action_type=op.action_type,
                    path=op.path,
                    error_detail='文件不存在！'
                )
            is_valid = is_valid_extension(full_path)
            if not is_valid:
                return FileOperationFeedback(
                    status=FeedbackStatus.FAILURE,
                    action_type=op.action_type,
                    path=op.path,
                    error_detail='非可读文件！'
                )

            if is_check_file(full_path):
                content = read_file_with_limit(full_path)
            else:
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

    def replace_blocks(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
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

    def build_tree(self, directory: str) -> dict:
        """递归构建目录树结构，返回简洁的字典结构
        返回格式示例:
        {
            'name': 'test_directory',
            'files': ['test_file.txt'],
            'dirs': {
                'data': {
                    'files': ['d.py'],
                    'dirs': {}
                }
            }
        }
        """
        result = {
            'name': os.path.basename(directory),
            'files': [],
            'dirs': {}
        }

        try:
            for entry in sorted(os.listdir(directory)):
                full_path = os.path.join(directory, entry)
                if os.path.isfile(full_path):
                    result['files'].append(entry)
                elif os.path.isdir(full_path):
                    result['dirs'][entry] = self.build_tree(full_path)

            return result
        except PermissionError as e:
            raise RuntimeError(f"Permission denied: {directory}") from e

    def list_dir_tree(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """遍历目录并生成树形结构"""
        try:
            full_path = os.path.join(self.workspace, path)
            tree = self.build_tree(full_path)

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

    def create_directory(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """创建目录"""
        try:
            os.makedirs(path, exist_ok=True)
            return FileOperationFeedback(
                status=FeedbackStatus.SUCCESS,
                action_type=op.action_type,
                path=op.path
            )
        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )

    def delete_directory(self, path: str, op: FileOperationInput) -> FileOperationFeedback:
        """删除目录"""
        try:
            if op.recursive:
                shutil.rmtree(path)
            else:
                os.rmdir(path)
            return FileOperationFeedback(
                status=FeedbackStatus.SUCCESS,
                action_type=op.action_type,
                path=op.path
            )
        except Exception as e:
            return FileOperationFeedback(
                status=FeedbackStatus.FAILURE,
                action_type=op.action_type,
                path=op.path,
                error_detail=str(e)
            )


