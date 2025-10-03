import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ToolCall:
    tool_name: str
    timestamp: datetime
    parameters: Dict[str, Any]
    result: Optional[str] = None
    success: bool = True

@dataclass
class FileOperation:
    operation_type: str
    file_path: str
    timestamp: datetime
    content_preview: Optional[str] = None

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime
    tool_calls: List[ToolCall] = field(default_factory=list)

@dataclass
class ParsedLog:
    messages: List[Message]
    tool_calls: List[ToolCall]
    file_operations: List[FileOperation]
    referenced_files: List[str]
    active_directory: Optional[str]
    total_messages: int
    conversation_duration: Optional[float]
    last_todo_items: List[str]
    recent_errors: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

class LogParser:
    def __init__(self):
        self.tool_pattern = re.compile(r'<invoke name="([^"]+)">')
        self.file_path_pattern = re.compile(r'[\'"](\/[^\'"]+\.[\w]+)[\'"]')
        self.todo_pattern = re.compile(r'(?:TODO|FIXME|XXX|HACK):\s*(.+?)$', re.MULTILINE)
        self.error_pattern = re.compile(r'(?i)(error|exception|failed|failure):\s*(.+?)(?:\n|$)')

    def parse_log(self, log_content: str) -> ParsedLog:
        messages = []
        tool_calls = []
        file_operations = []
        referenced_files = set()
        recent_errors = []
        last_todo_items = []
        current_timestamp = datetime.utcnow()

        for tool_match in self.tool_pattern.finditer(log_content):
            tool_name = tool_match.group(1)
            tool_calls.append(ToolCall(
                tool_name=tool_name,
                timestamp=current_timestamp,
                parameters={},
                success=True
            ))

            if tool_name in ['Read', 'Write', 'Edit', 'MultiEdit']:
                file_operations.append(FileOperation(
                    operation_type=tool_name,
                    file_path='',
                    timestamp=current_timestamp
                ))

        for file_match in self.file_path_pattern.finditer(log_content):
            file_path = file_match.group(1)
            referenced_files.add(file_path)

        for todo_match in self.todo_pattern.finditer(log_content):
            last_todo_items.append(todo_match.group(1))

        for error_match in self.error_pattern.finditer(log_content):
            recent_errors.append(error_match.group(2))

        lines = [line for line in log_content.split('\n') if line.strip()]

        return ParsedLog(
            messages=messages,
            tool_calls=tool_calls,
            file_operations=file_operations,
            referenced_files=list(referenced_files)[-20:],
            active_directory=self._extract_working_dir(log_content),
            total_messages=len(lines),
            conversation_duration=None,
            last_todo_items=last_todo_items[-10:],
            recent_errors=recent_errors[-10:],
            metadata={
                'total_tool_calls': len(tool_calls),
                'total_file_ops': len(file_operations),
                'total_files': len(referenced_files)
            }
        )

    def _extract_working_dir(self, log_content: str) -> Optional[str]:
        dir_pattern = re.compile(r'Working Directory:\s*(\/[^\n]+)')
        match = dir_pattern.search(log_content)
        return match.group(1) if match else None

def parse_log(log_content: str) -> ParsedLog:
    parser = LogParser()
    return parser.parse_log(log_content)
