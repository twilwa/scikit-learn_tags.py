"""
Communication system for multi-agent coordination.
"""

import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time


class MessageType(Enum):
    """Types of messages between agents."""
    GENERAL = "general"
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    BROADCAST = "broadcast"
    SYSTEM = "system"


@dataclass
class Message:
    """Message between agents."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    recipient: str = ""
    type: str = MessageType.GENERAL.value
    content: Any = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "type": self.type,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class MessageBus:
    """Message bus for agent communication."""
    
    def __init__(self):
        self._messages: Dict[str, List[Message]] = {}
        self._subscribers: Dict[str, List[str]] = {}
        self._message_history: List[Message] = []
        self._lock = asyncio.Lock()
    
    async def send_message(self, message: Message) -> None:
        """Send a message to a specific recipient."""
        async with self._lock:
            if message.recipient not in self._messages:
                self._messages[message.recipient] = []
            
            self._messages[message.recipient].append(message)
            self._message_history.append(message)
    
    async def broadcast_message(self, message: Message) -> None:
        """Broadcast a message to all agents."""
        async with self._lock:
            for agent_id in self._messages.keys():
                if agent_id != message.sender:
                    agent_message = Message(
                        sender=message.sender,
                        recipient=agent_id,
                        type=message.type,
                        content=message.content,
                        metadata=message.metadata
                    )
                    self._messages[agent_id].append(agent_message)
            
            self._message_history.append(message)
    
    async def get_messages_for_agent(self, agent_id: str) -> List[Message]:
        """Get all messages for an agent."""
        async with self._lock:
            if agent_id not in self._messages:
                self._messages[agent_id] = []
                return []
            
            messages = self._messages[agent_id].copy()
            self._messages[agent_id].clear()
            return messages
    
    def get_message_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get message history."""
        if limit:
            return self._message_history[-limit:]
        return self._message_history.copy()
    
    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            "total_messages": len(self._message_history),
            "active_agents": len(self._messages),
            "pending_messages": sum(len(msgs) for msgs in self._messages.values())
        }