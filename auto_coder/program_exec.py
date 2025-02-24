# -*- coding: utf-8 -*-
"""
@author: Zed
@file: program_exec.py
@time: 2025/2/19 20:09
@describe:自定义描述
"""
from typing import List
from dataclasses import dataclass
import subprocess
import threading
import time
import os
import signal
from typing import Callable, Optional, Dict
from enum import Enum



__all__ = [
    "ParallelExecutor",
    "ProgramExecutionInput",
    "ProgramExecutionFeedback",
    "ProgramCheck",
    "ProgramCheckFeedback"
]


# 其他代码...
class FeedbackStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class ProgramActionType(Enum):
    EXECUTE_COMMAND = "execute"
    TERMINATE_COMMAND = "terminate"


@dataclass
class ProgramExecutionFeedback:
    status: FeedbackStatus
    action_type: ProgramActionType
    execution_time: float
    stdout: str
    stderr: str
    returncode: str
    timeout: bool = False

    def to_dict(self):
        return {
            "status": self.status.value,
            "action": self.action_type.value,
            "exec_time": self.execution_time,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.stderr,
            "timeout": self.timeout
        }


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


class CommandExecutor:
    def __init__(self):
        self.active_process = None
        self.output_buffer = []
        self.error_buffer = []
        self.running = False
        self.lock = threading.Lock()
        self.output_callbacks = []
        self.analysis_function = None
        self.analysis_interval = 1.0  # 默认分析间隔1秒
        self.analysis_thread = None
        self.last_read = False

    def _get_remain(self):

        if self.active_process and not self.last_read:
            self.last_read = True
            self.running = False

            with self.lock:
                remaining = self.active_process.stdout.read()
                if remaining:
                    self.output_buffer.append(remaining.strip())
                err_remaining = self.active_process.stderr.read()
                if err_remaining:
                    self.error_buffer.append(err_remaining.strip())
                self.active_process = None

    def _get_last(self):
        if self.active_process and not self.last_read:
            self.last_read = True
            self.running = False

            with self.lock:
                remaining = self.active_process.stdout.readline()
                if remaining:
                    self.output_buffer.append(remaining.strip())
                self.active_process = None

    def execute(
            self,
            name: str,
            command: str,
            timeout: int = 30,
    ) -> Dict:
        """
        执行命令并捕获输出
        :param command: 要执行的命令
        :param timeout: 超时时间（秒）
        :param realtime_callback: 实时输出回调函数
        :param error_callback: 错误输出回调函数
        :return: 执行结果字典
        """
        result = {
            "output": "",
            "error": "",
            "returncode": -1,
            "timeout": False,
            "pid": None,
            "execution_time": 0.0,
            "finished": False
        }

        try:
            start_time = time.time()
            self.running = True

            # 启动子进程
            self.active_process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            result["pid"] = self.active_process.pid

            # 启动输出捕获线程（暂时不用）
            output_thread = threading.Thread(
                target=self._capture_output,
                args=()
            )
            output_thread.daemon = True
            output_thread.start()

            # 主线程等待进程结束或超时
            while self.running:
                returncode = self.active_process.poll()
                if returncode is not None:
                    result["returncode"] = returncode
                    result["finished"] = True
                    self._get_remain()
                    break

                if time.time() - start_time > timeout:
                    result["timeout"] = True
                    self._terminate_process(name, is_all=False)
                    break

                time.sleep(0.1)

            # 收集剩余输出
            with self.lock:


                MAX_LENGTH = 1000  # 约束stdout的输出缓存
                N = MAX_LENGTH // 2  # 计算前n个和后n个字符的长度
                result["output"] = "\n".join(self.output_buffer)
                result["error"] = "\n".join(self.error_buffer)
                if len(result["output"]) > MAX_LENGTH:
                    result["output"] = result["output"][:N] + '...' + result["output"][-N:]  # 取前n个和后n个字符
            result["execution_time"] = round(time.time() - start_time, 2)

        except Exception as e:
            result["error"] = str(e)
        finally:
            self.running = False
            self._cleanup()

        return result

    def _capture_output(self, realtime_callback=None):
        """实时捕获输出流的线程函数"""
        while self.running and self.active_process is not None:
            # 捕获标准输出
            while True:
                if not self.active_process:
                    break
                line = self.active_process.stdout.readline()
                if line:
                    self.output_buffer.append(line.strip())
                    if realtime_callback:
                        realtime_callback(line.strip())
                else:
                    break

            time.sleep(1)

    def _terminate_process(self, name, is_all=True):
        """终止进程的跨平台方法"""
        if self.active_process:
            if is_all:
                self._get_remain()
            else:
                get_last = threading.Thread(target=self._get_last)
                get_last.start()
                get_last.join(5)

            try:
                if os.name == 'nt':
                    # Windows系统
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.active_process.pid)])
                else:
                    # Unix系统
                    os.killpg(os.getpgid(self.active_process.pid), signal.SIGTERM)
            except:
                pass
            finally:
                self.active_process = None

    def stop(self, name, is_all=True):
        """主动停止当前执行"""
        self.running = False
        self._terminate_process(name, is_all)

    def _cleanup(self):
        """清理资源"""
        self.output_buffer.clear()
        self.error_buffer.clear()
        self.active_process = None

    def register_output_callback(self, callback: Callable[[str], None]):
        """注册实时输出回调"""
        self.output_callbacks.append(callback)



@dataclass
class ProgramExecutionInput:
    name: str
    command: str
    timeout: int
    realtime_callback: Optional[Callable[[str], None]] = None
    error_callback: Optional[Callable[[str], None]] = None


@dataclass
class ProgramResult:
    name: str
    stdout: str
    stderr: str
    exec_time: float
    return_code: int
    status: str  # completed, timeout, aborted


class ProgramCheck:
    # 负责接受程序执行过程中的缓存输出，并将缓存转为结构化文本反馈给api
    # 每次执行程序，都需要重新实例化一个
    #
    def __init__(self, send_feedback=None, set_check_interval=10):
        self.program_dict = {}
        self.start_time = time.time()
        self.last_end_time = time.time()
        self.set_check_interval = set_check_interval  # 检查时间
        self.send_feedback = send_feedback  # 发送反馈函数

    # 分析函数示例
    def __call__(self, output_dict: dict):
        # 过程监控函数+终止控制
        if time.time() - self.last_end_time > self.set_check_interval:
            self.last_end_time = time.time()
            program_check_dict = {}
            for name, out_err_dict in output_dict.items():
                program_check = ProgramCheckFeedback(name,
                                                     runtime=round(time.time() - self.start_time, 2),
                                                     stdout=out_err_dict['output'],
                                                     stderr=out_err_dict['errors'],
                                                     )
                program_check_dict[name] = program_check.to_dict()
            if program_check_dict:
                res = self.send_feedback(program_check_dict)
                return res


class ParallelExecutor:
    def __init__(self, program_check: ProgramCheck = None):
        self.executors: Dict[str, CommandExecutor] = {}
        self.results: Dict[str, ProgramResult] = {}
        self.lock = threading.Lock()
        self.analysis_interval = 0.5
        self.output_dict = {}
        self.program_check = program_check

    def execute_programs(
            self,
            configs: List[ProgramExecutionInput],

    ) -> Dict[str, ProgramResult]:
        """
        执行多个程序并收集结构化结果
        :param configs: 程序配置列表
        :param analysis_func: 分析函数（返回需要中止的程序名称列表）
        """
        # 初始化执行器
        for config in configs:
            executor = CommandExecutor()
            self.executors[config.name] = executor
            self.results[config.name] = ProgramResult(
                name=config.name,
                stdout="",
                stderr="",
                exec_time=0.0,
                return_code=-1,
                status="pending"
            )

        # 启动所有程序
        threads = []
        for config in configs:
            thread = threading.Thread(
                target=self._run_single_program,
                args=(config,)
            )
            threads.append(thread)
            thread.start()

        # 启动分析线程
        if self.program_check:
            analysis_thread = threading.Thread(
                target=self._monitor_programs,
                args=(self.program_check,)
            )
            analysis_thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        return self.results

    def _run_single_program(self, config: ProgramExecutionInput):
        """执行单个程序"""
        executor = self.executors[config.name]
        result = executor.execute(
            name=config.name,
            command=config.command,
            timeout=config.timeout,
        )

        with self.lock:
            if result["timeout"]:
                status = 'timeout'
            elif result["finished"]:
                status = 'finished'
            else:
                status = 'aborted'

            self.results[config.name] = ProgramResult(
                name=config.name,
                stdout=result["output"],
                stderr=result["error"],
                exec_time=result["execution_time"],
                return_code=result["returncode"],
                status=status
            )

    def _monitor_programs(self, program_check: Callable):
        """监控线程"""
        # 将实时输出推送给api，再由api决定是否终止的模块
        while any(e.running for e in self.executors.values()):
            # 获取当前输出

            for name, executor in self.executors.items():

                if executor.active_process:
                    line = executor.active_process.stdout.readline()
                    if line:
                        executor.output_buffer.append(line.strip())
                    self.output_dict[name] = {'output': "\n".join(executor.output_buffer),
                                              'errors': "\n".join(executor.error_buffer),
                                              }

            # 执行分析：
            #     这里会将outputs, errors反馈给api，根据api判断是否执行终止动作
            abort_list = program_check(self.output_dict)
            if abort_list:
                for name in abort_list:
                    if name in self.executors and self.executors[name].running:
                        print(f"[监控] 中止程序 {name}")
                        self.executors[name].stop(name, is_all=False)
            time.sleep(0.1)


