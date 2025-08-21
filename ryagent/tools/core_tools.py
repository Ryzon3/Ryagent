import asyncio
import os
import subprocess
import aiofiles
from pathlib import Path
from typing import Dict, Any, List, Literal

from .base import Tool, ToolSpec


class ShellRunTool(Tool):
    def __init__(self, allowed_commands: List[str] = None, denied_commands: List[str] = None, workspace: str = None):
        self.allowed_commands = allowed_commands or ["python", "uv", "ls", "cat", "rg", "git", "pytest"]
        self.denied_commands = denied_commands or ["rm", "shutdown", "reboot", "mkfs", "dd", "fdisk"]
        self.workspace = Path(workspace) if workspace else Path.cwd()

    @property
    def spec(self) -> ToolSpec:
        return {
            "name": "shell_run",
            "description": "Execute shell commands with safety restrictions",
            "schema": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "The command to execute"
                    },
                    "timeout_s": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 60
                    }
                },
                "required": ["cmd"]
            },
            "dangerous": True
        }

    def _is_command_allowed(self, cmd: str) -> bool:
        cmd_parts = cmd.strip().split()
        if not cmd_parts:
            return False
        
        base_cmd = cmd_parts[0]
        
        if base_cmd in self.denied_commands:
            return False
        
        if self.allowed_commands and base_cmd not in self.allowed_commands:
            return False
        
        return True

    async def run(self, cmd: str, timeout_s: int = 60) -> Dict[str, Any]:
        if not self._is_command_allowed(cmd):
            return {
                "error": f"Command not allowed: {cmd.split()[0] if cmd.split() else 'empty'}",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }

        try:
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_s
            )

            return {
                "stdout": stdout.decode('utf-8', errors='replace')[:4096],
                "stderr": stderr.decode('utf-8', errors='replace')[:4096],
                "returncode": process.returncode,
                "error": None
            }

        except asyncio.TimeoutError:
            if process:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    process.kill()
            
            return {
                "error": f"Command timed out after {timeout_s} seconds",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }

        except Exception as e:
            return {
                "error": f"Command execution failed: {str(e)}",
                "stdout": "",
                "stderr": "",
                "returncode": -1
            }


class FileReadTool(Tool):
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()

    @property
    def spec(self) -> ToolSpec:
        return {
            "name": "fs_read",
            "description": "Read file contents with size limits",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    },
                    "bytes": {
                        "type": "integer",
                        "description": "Maximum bytes to read",
                        "default": 65536
                    }
                },
                "required": ["path"]
            },
            "dangerous": False
        }

    def _is_path_safe(self, path: str) -> bool:
        try:
            file_path = (self.workspace / path).resolve()
            workspace_path = self.workspace.resolve()
            return str(file_path).startswith(str(workspace_path))
        except Exception:
            return False

    async def run(self, path: str, bytes: int = 65536) -> Dict[str, Any]:
        if not self._is_path_safe(path):
            return {
                "error": f"Path outside workspace: {path}",
                "content": "",
                "size": 0,
                "truncated": False
            }

        file_path = self.workspace / path

        try:
            if not file_path.exists():
                return {
                    "error": f"File not found: {path}",
                    "content": "",
                    "size": 0,
                    "truncated": False
                }

            if not file_path.is_file():
                return {
                    "error": f"Not a file: {path}",
                    "content": "",
                    "size": 0,
                    "truncated": False
                }

            file_size = file_path.stat().st_size
            truncated = file_size > bytes

            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = await f.read(bytes)

            return {
                "content": content,
                "size": file_size,
                "truncated": truncated,
                "error": None
            }

        except Exception as e:
            return {
                "error": f"Failed to read file: {str(e)}",
                "content": "",
                "size": 0,
                "truncated": False
            }


class FileWriteTool(Tool):
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()

    @property
    def spec(self) -> ToolSpec:
        return {
            "name": "fs_write",
            "description": "Write content to files with safety checks",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "Content to write to the file"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["create", "overwrite"],
                        "description": "Write mode: create (fail if exists) or overwrite",
                        "default": "create"
                    }
                },
                "required": ["path", "content"]
            },
            "dangerous": True
        }

    def _is_path_safe(self, path: str) -> bool:
        try:
            file_path = (self.workspace / path).resolve()
            workspace_path = self.workspace.resolve()
            return str(file_path).startswith(str(workspace_path))
        except Exception:
            return False

    async def run(self, path: str, content: str, mode: Literal["create", "overwrite"] = "create") -> Dict[str, Any]:
        if not self._is_path_safe(path):
            return {
                "error": f"Path outside workspace: {path}",
                "bytes_written": 0
            }

        file_path = self.workspace / path

        try:
            if mode == "create" and file_path.exists():
                return {
                    "error": f"File already exists: {path}",
                    "bytes_written": 0
                }

            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)

            return {
                "bytes_written": len(content.encode('utf-8')),
                "error": None
            }

        except Exception as e:
            return {
                "error": f"Failed to write file: {str(e)}",
                "bytes_written": 0
            }