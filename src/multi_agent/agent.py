"""
Base agent framework with capabilities and state management.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
from .communication import Message, MessageBus


class AgentState(Enum):
    """Possible states of an agent."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    COMMUNICATING = "communicating"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class AgentCapability:
    """Represents a capability that an agent possesses."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    prerequisites: Set[str] = field(default_factory=set)


@dataclass
class Task:
    """Represents a task that can be assigned to an agent."""
    id: str
    description: str
    required_capabilities: Set[str]
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    deadline: Optional[float] = None
    dependencies: Set[str] = field(default_factory=set)
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False


@dataclass
class AgentMetrics:
    """Metrics tracking for agent performance."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    last_activity: Optional[float] = None


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        message_bus: Optional[MessageBus] = None
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or f"Agent-{self.agent_id[:8]}"
        self.capabilities = {cap.name: cap for cap in (capabilities or [])}
        self.state = AgentState.IDLE
        self.message_bus = message_bus
        self.metrics = AgentMetrics()
        self.memory: Dict[str, Any] = {}
        self.current_task: Optional[Task] = None
        self.task_queue: List[Task] = []
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
    
    @abstractmethod
    async def think(self, task: Task) -> Dict[str, Any]:
        """
        Analyze a task and determine the approach.
        Returns a plan or reasoning about how to proceed.
        """
        pass
    
    @abstractmethod
    async def act(self, task: Task, plan: Dict[str, Any]) -> Any:
        """
        Execute the planned action for a task.
        Returns the result of the action.
        """
        pass
    
    async def process_task(self, task: Task) -> Task:
        """Process a single task through the think-act cycle."""
        if not self.can_handle_task(task):
            task.error = f"Agent {self.name} cannot handle task requirements"
            return task
        
        self.current_task = task
        start_time = time.time()
        
        try:
            # Think phase
            self.state = AgentState.THINKING
            await self._emit_event("task_started", {"task": task})
            
            plan = await self.think(task)
            await self._emit_event("thinking_completed", {"plan": plan})
            
            # Act phase
            self.state = AgentState.ACTING
            result = await self.act(task, plan)
            
            task.result = result
            task.completed = True
            self.metrics.tasks_completed += 1
            
            await self._emit_event("task_completed", {"task": task, "result": result})
            
        except Exception as e:
            task.error = str(e)
            self.metrics.tasks_failed += 1
            self.state = AgentState.ERROR
            await self._emit_event("task_failed", {"task": task, "error": str(e)})
        
        finally:
            execution_time = time.time() - start_time
            self.metrics.total_execution_time += execution_time
            self.metrics.last_activity = time.time()
            self.current_task = None
            self.state = AgentState.IDLE
        
        return task
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task."""
        return task.required_capabilities.issubset(self.capabilities.keys())
    
    def add_capability(self, capability: AgentCapability) -> None:
        """Add a new capability to this agent."""
        self.capabilities[capability.name] = capability
    
    def remove_capability(self, capability_name: str) -> None:
        """Remove a capability from this agent."""
        self.capabilities.pop(capability_name, None)
    
    async def send_message(self, recipient: str, content: Any, message_type: str = "general") -> None:
        """Send a message to another agent."""
        if self.message_bus:
            message = Message(
                sender=self.agent_id,
                recipient=recipient,
                content=content,
                type=message_type
            )
            await self.message_bus.send_message(message)
            self.metrics.messages_sent += 1
    
    async def broadcast_message(self, content: Any, message_type: str = "broadcast") -> None:
        """Broadcast a message to all agents."""
        if self.message_bus:
            message = Message(
                sender=self.agent_id,
                recipient="*",
                content=content,
                type=message_type
            )
            await self.message_bus.broadcast_message(message)
            self.metrics.messages_sent += 1
    
    async def handle_message(self, message: Message) -> None:
        """Handle an incoming message."""
        self.metrics.messages_received += 1
        self.metrics.last_activity = time.time()
        
        # Store message in memory
        if "messages" not in self.memory:
            self.memory["messages"] = []
        self.memory["messages"].append(message)
        
        await self._emit_event("message_received", {"message": message})
    
    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    async def _emit_event(self, event: str, data: Dict[str, Any]) -> None:
        """Emit an event to registered handlers."""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self, event, data)
                    else:
                        handler(self, event, data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    async def start(self) -> None:
        """Start the agent's main loop."""
        self._running = True
        await self._emit_event("agent_started", {})
        
        while self._running:
            # Process task queue
            if self.task_queue and self.state == AgentState.IDLE:
                task = self.task_queue.pop(0)
                await self.process_task(task)
            
            # Check for messages
            if self.message_bus:
                messages = await self.message_bus.get_messages_for_agent(self.agent_id)
                for message in messages:
                    await self.handle_message(message)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
    
    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        await self._emit_event("agent_stopped", {})
    
    def add_task(self, task: Task) -> None:
        """Add a task to the agent's queue."""
        self.task_queue.append(task)
        # Sort by priority (higher first) and deadline
        self.task_queue.sort(key=lambda t: (-t.priority, t.deadline or float('inf')))


class SpecializedAgent(BaseAgent):
    """A specialized agent with predefined capabilities and behavior."""
    
    def __init__(self, specialization: str, **kwargs):
        self.specialization = specialization
        capabilities = self._get_default_capabilities(specialization)
        super().__init__(capabilities=capabilities, **kwargs)
    
    def _get_default_capabilities(self, specialization: str) -> List[AgentCapability]:
        """Get default capabilities based on specialization."""
        capability_sets = {
            "code_analyzer": [
                AgentCapability("analyze_code", "Analyze code structure and quality"),
                AgentCapability("detect_patterns", "Detect code patterns and anti-patterns"),
                AgentCapability("suggest_improvements", "Suggest code improvements")
            ],
            "test_generator": [
                AgentCapability("generate_tests", "Generate unit tests for code"),
                AgentCapability("analyze_coverage", "Analyze test coverage"),
                AgentCapability("create_fixtures", "Create test fixtures and data")
            ],
            "documentation_writer": [
                AgentCapability("write_docs", "Write technical documentation"),
                AgentCapability("generate_examples", "Generate code examples"),
                AgentCapability("create_tutorials", "Create tutorials and guides")
            ],
            "refactoring_expert": [
                AgentCapability("refactor_code", "Refactor and improve code structure"),
                AgentCapability("extract_methods", "Extract methods and classes"),
                AgentCapability("optimize_performance", "Optimize code performance")
            ],
            "integration_specialist": [
                AgentCapability("integrate_apis", "Integrate external APIs"),
                AgentCapability("handle_data_flow", "Handle data flow between systems"),
                AgentCapability("ensure_compatibility", "Ensure system compatibility")
            ]
        }
        
        return capability_sets.get(specialization, [])
    
    async def think(self, task: Task) -> Dict[str, Any]:
        """Default thinking implementation based on specialization."""
        plan = {
            "approach": f"Using {self.specialization} methodology",
            "steps": [],
            "resources_needed": [],
            "estimated_time": 0
        }
        
        # Add specialization-specific thinking
        if self.specialization == "code_analyzer":
            plan["steps"] = [
                "Parse code structure",
                "Analyze complexity",
                "Check for patterns",
                "Generate report"
            ]
        elif self.specialization == "test_generator":
            plan["steps"] = [
                "Analyze target code",
                "Identify test cases",
                "Generate test code",
                "Verify test coverage"
            ]
        # Add more specializations as needed
        
        return plan
    
    async def act(self, task: Task, plan: Dict[str, Any]) -> Any:
        """Default action implementation - should be overridden."""
        # This is a basic implementation that should be specialized
        result = {
            "status": "completed",
            "approach_used": plan.get("approach"),
            "steps_executed": plan.get("steps", []),
            "task_description": task.description
        }
        
        # Simulate some work
        await asyncio.sleep(1)
        
        return result