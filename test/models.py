from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Union
import json
from datetime import datetime


# ========================
# 核心枚举类型
# ========================
class FileActionType(Enum):
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    READ_FILE = "read_file"
    REPLACE_BLOCK = "replace_block"  # 区块替换操作
    CREATE_DIR = "create_directory"
    DELETE_DIR = "delete_directory"
    LIST_DIR_TREE = "list_tree"


class ProgramActionType(Enum):
    EXECUTE_COMMAND = "execute"
    TERMINATE_COMMAND = "terminate"


class RequestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class FeedbackStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


# ========================
# 区块替换专用结构
# ========================
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


# ========================
# 操作指令数据结构
# ========================
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


@dataclass
class ProgramExecutionInput:
    name:str
    command: str
    timeout_seconds: Optional[int] = None
    request_reason: Optional[str] = None

    def to_dict(self):
        return {
            "name": self.name,
            "command": self.command,
            "timeout": self.timeout_seconds,
            "reason": self.request_reason
        }


@dataclass
class ProgramCheckInput:
    name: str
    terminal: bool  # true表示终止程序
    reason: Optional[str] = None  # 理由

    def to_dict(self):
        return {
            "name": self.name,
            "terminal": self.terminal,
            "reason": self.reason
        }


# ========================
# 反馈数据结构
# ========================
@dataclass
class FileOperationFeedback:
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
class ProgramExecutionFeedback:
    status: FeedbackStatus
    action_type: ProgramActionType
    execution_time: float
    stdout: str
    stderr: str
    returncode: str
    killed_by_timeout: bool = False

    #     print(f"输出内容: {result['output']}")
    #     print(f"错误信息: {result['error']}")
    #     print(f"返回码: {result['returncode']}")
    #     print(f"是否超时: {result['timeout']}")
    #     print(f"进程ID: {result['pid']}")
    #     print(f"执行时间: {result['execution_time']}秒")
    #     print(f"是否完成: {result['finished']}")
    def to_dict(self):
        return {
            "status": self.status.value,
            "action": self.action_type.value,
            "exec_time": self.execution_time,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.stderr,
            "timeout": self.killed_by_timeout
        }


# {
#  'program0':{
#             'name': "program0",  # program1的程序名称
#             'stdout':"xxx,xxx", #program0的过程标准输出
#             'stderr':"xxx,xxx", #program0的过程报错输出
#             'runtime':xx, #program0的当前运行时间
#             'max_limit_time':xxx, #program0的最大预期运行时间
#           },
#  'program1':{
#             'name':"program1", #program1的程序名称
#             'stdout':"xxx,xxx", #program1的过程标准输出
#             'stderr':"xxx,xxx", #program1的过程报错输出
#             'runtime':xx, #program1的当前运行时间
#             'max_limit_time':xxx, #program1的最大预期运行时间
#           }
#
#
# }
@dataclass
class ProgramCheckFeedback:
    name: str
    runtime: float
    stdout: str
    stderr: str

    def to_dict(self):
        return {
            "name": self.name,
            "runtime": self.runtime,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass
class ProgramCheckRequest:
    # 程序过程检查请求：终止/或者继续
    request_id: str
    program_operations: List[ProgramCheckInput] = None
    created_at: str = datetime.now().isoformat()

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "program_operations": self.program_operations,
            "created_at": self.created_at,
        }


@dataclass
class WorkFinishNote:
    # 工作流结束通知：对该工作内容的总结：主要包括架构，核心功能，注意事项，优点，缺点，建议等细节
    # 后续可考虑更细致的结构化
    # request_id: str
    summary: str
    created_at: str = datetime.now().isoformat()

    def to_dict(self):
        return {
            # "request_id": self.request_id,
            "summary": self.summary,
            "created_at": self.created_at,
        }


# ========================
# 顶层通信协议
# ========================
@dataclass
class OperationRequest:
    request_id: str
    reason: str
    file_operations: List[FileOperationInput] = None
    program_operations: List[ProgramExecutionInput] = None
    status: RequestStatus = RequestStatus.PENDING
    created_at: str = datetime.now().isoformat()

    def to_json(self):
        return json.dumps({
            "step_id": self.request_id,
            'reason': self.reason,
            "status": self.status.value,
            "file_operations": [op.to_dict() for op in self.file_operations] if self.file_operations else [],
            "programs_operations": [op.to_dict() for op in self.program_operations] if self.program_operations else [],
            "created": self.created_at
        }, ensure_ascii=False, indent=2)


@dataclass
class OperationResponse:
    request_id: str
    reason: str
    status: RequestStatus
    file_feedbacks: List[FileOperationFeedback] = None
    program_feedbacks: List[ProgramExecutionFeedback] = None
    completed_at: str = str(datetime.now())

    def to_json(self):
        return json.dumps({
            "request_id": self.request_id,
            'reason': self.reason,
            "status": self.status.value,
            "files": [fb.to_dict() for fb in self.file_feedbacks] if self.file_feedbacks else [],
            "programs": self.program_feedbacks if self.program_feedbacks else [],
            "completed": self.completed_at
        }, ensure_ascii=False, indent=2)


# 在已有代码基础上新增以下内容
class Parser:
    # 结构化文本转类实例
    @classmethod
    def parse_request(cls, json_data: Dict) -> Union[OperationRequest, ProgramCheckRequest,WorkFinishNote]:
        """解析操作请求"""
        if json_data['type'] == 'operate':
            return OperationRequest(
                request_id=json_data["metadata"]["step_id"],
                reason=json_data["metadata"]["reason"],
                status=RequestStatus[json_data["metadata"]["status"].upper()],
                file_operations=cls._parse_file_actions(json_data.get("file_operations", [])),
                program_operations=cls._parse_program_execs(json_data.get("program_operations", [])),
                created_at=json_data["metadata"].get("timestamp")
            )
        elif json_data['type'] == 'check_program':
            # 程序检查，用于在程序过程中实时的通讯，获取反馈以及指导，正常预期继续进行，否则可以考虑中止
            return ProgramCheckRequest(
                request_id=json_data["metadata"]["step_id"],
                program_operations=json_data["program_operations"],
            )
        elif json_data['type'] == 'finish':
            # 程序执行结束，通知用户，可以给出文档，建议，总结之类的内容作为收尾
            return WorkFinishNote(summary=json_data["summary"])

    @classmethod
    def _parse_file_actions(cls, actions: List[Dict]) -> List[FileOperationInput]:
        result = []
        for action in actions:
            # print(action["modify_content"])
            action_type = FileActionType(action["action_type"])
            # print()
            blocks = [
                CodeBlock(
                    identifier=f"{mod['identifier']}",
                    old_content=mod["old_content"],
                    new_content=mod["new_content"]
                ) for mod in action.get("modify_content", [])
            ] if action_type == FileActionType.REPLACE_BLOCK else None

            result.append(FileOperationInput(
                action_type=action_type,
                path=action["path"],
                blocks=blocks,
                content=action.get("file_content"),
                request_reason=action.get("reason")
            ))
        return result

    @classmethod
    def _parse_program_execs(cls, exec_program_list: List) -> List[ProgramExecutionInput]:
        total_list = []
        for exec_program in exec_program_list:
            total_list.append(ProgramExecutionInput(
                name=exec_program["name"],
                command=exec_program["command"],
                timeout_seconds=exec_program.get("set_timeout"),
                request_reason=exec_program.get("expected_output")
            ))
        return total_list

    @classmethod
    def parse_response(cls, json_data: Dict) -> OperationResponse:
        """解析操作响应"""
        return OperationResponse(
            request_id=json_data["metadata"]["step_id"],
            reason=json_data["metadata"]["reason"],
            status=RequestStatus[json_data["metadata"]["status"].upper()],
            file_feedbacks=cls._parse_file_feedbacks(json_data.get("file_actions", [])),
            program_feedbacks=cls._parse_program_feedbacks(json_data.get("program_execs", {})),

        )

    @classmethod
    def _parse_file_feedbacks(cls, actions: List[Dict]) -> List[FileOperationFeedback]:
        # 实际实现需根据具体反馈结构调整
        return []

    @classmethod
    def _parse_program_feedbacks(cls, exec_data: Dict) -> List[ProgramExecutionFeedback]:
        # 实际实现需根据具体反馈结构调整
        return []


# 新增演示用例
if __name__ == "__main__":
    demo_json = {
        "metadata": {
            "step_id": "tetris_005",
            "reason": "Windows环境专用清理和编码最终修复",
            "status": "running"
        },
        "file_operations": [
            {
                "action_type": "replace_block",
                "path": "main.py",
                "modify_content": [
                    {
                        "identifier": "sys_import_statement",
                        "old_content": "import sys\n",
                        "new_content": "import sys\nsys.dont_write_bytecode = True\n"
                    }
                ],
                "request_reason": "防止Python生成.pyc文件"
            }
        ],
        "program_operations": [
            {
                "action_type": "execute",
                "command": "del /s /q *.pyc && python -X utf8 main.py",
                "timeout_seconds": 20,
                "request_reason": "清理构建产物并运行程序"
            }
        ]
    }
    print(demo_json)
    # 执行解析演示
    request = Parser.parse_request(demo_json)
    print(request)
    # print("\n解析后的请求对象:")
    # print(f"ID: {request.request_id}")
    # print(f"状态: {request.status.value}")
    # print(f"文件操作数: {len(request.file_operations)}")
    # print(f"首个文件操作类型: {request.file_operations}")
    # print(f"关联代码块数: {len(request.file_operations[0].blocks)}")
    # print(f"程序命令: {request.program_operations[0].command}")

    # 输出解析结果
    print("\n序列化回JSON验证:")
    print(request.to_json())
# ========================
# 使用示例
# ========================
if __name__ == "__main__":
    # 区块替换示例：更新两个函数
    replace_ops = [
        CodeBlock(
            identifier="def calculate()",
            old_content="def calculate():\n    return 1+1",
            new_content="def calculate():\n    return 2 * 2"
        ),
        CodeBlock(
            identifier="class MyProcessor",
            old_content="class MyProcessor:\n    def run(self):\n        pass",
            new_content="class MyProcessor:\n    def run(self):\n        print('processing...')"
        )
    ]

    # 创建请求
    request = OperationRequest(
        request_id="func_update_001",
        reason='优化核心函数逻辑',
        file_operations=[
            FileOperationInput(
                action_type=FileActionType.REPLACE_BLOCK,
                path="/src/main.py",
                blocks=replace_ops,
                request_reason="优化核心函数逻辑"
            )
        ]
    )
    # print("区块替换请求示例:")
    # print(request.to_json())

    # 对应反馈
    response = OperationResponse(
        request_id="func_update_001",
        reason='reason',
        status=RequestStatus.COMPLETED,
        file_feedbacks=[
            FileOperationFeedback(
                status=FeedbackStatus.SUCCESS,
                action_type=FileActionType.REPLACE_BLOCK,
                path="/src/main.py",
                replace_results=[
                    ReplaceResult(
                        identifier="def calculate()",
                        replaced=True,
                        matches_found=1,
                        verification_passed=True
                    ),
                    ReplaceResult(
                        identifier="class MyProcessor",
                        replaced=True,
                        matches_found=1,
                        verification_passed=True
                    )
                ]
            )
        ]
    )
    # print("\n区块替换反馈示例:")
    # print(response.to_json())
