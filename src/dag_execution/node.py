"""
Execution nodes with configuration and resource management.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time
import json


class NodeState(Enum):
    """States a node can be in during execution."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ResourceType(Enum):
    """Types of resources a node might need."""
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class ResourceRequirement:
    """Resource requirement specification."""
    resource_type: ResourceType
    amount: Union[int, float]
    unit: str
    optional: bool = False


@dataclass
class NodeInput:
    """Input specification for a node."""
    name: str
    data_type: type
    required: bool = True
    default_value: Any = None
    description: Optional[str] = None


@dataclass
class NodeOutput:
    """Output specification for a node."""
    name: str
    data_type: type
    description: Optional[str] = None


@dataclass
class NodeConfig:
    """Configuration for a node execution."""
    node_id: str
    node_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: List[ResourceRequirement] = field(default_factory=list)
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None
    tags: Set[str] = field(default_factory=set)
    environment: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "parameters": self.parameters,
            "resource_requirements": [
                {
                    "type": req.resource_type.value,
                    "amount": req.amount,
                    "unit": req.unit,
                    "optional": req.optional
                }
                for req in self.resource_requirements
            ],
            "retry_policy": self.retry_policy,
            "timeout": self.timeout,
            "tags": list(self.tags),
            "environment": self.environment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeConfig':
        """Create from dictionary."""
        resource_reqs = []
        for req_data in data.get("resource_requirements", []):
            resource_reqs.append(ResourceRequirement(
                resource_type=ResourceType(req_data["type"]),
                amount=req_data["amount"],
                unit=req_data["unit"],
                optional=req_data.get("optional", False)
            ))
        
        return cls(
            node_id=data["node_id"],
            node_type=data["node_type"],
            parameters=data.get("parameters", {}),
            resource_requirements=resource_reqs,
            retry_policy=data.get("retry_policy", {}),
            timeout=data.get("timeout"),
            tags=set(data.get("tags", [])),
            environment=data.get("environment", {})
        )


@dataclass
class ExecutionContext:
    """Context information for node execution."""
    run_id: str
    execution_time: float
    upstream_outputs: Dict[str, Any] = field(default_factory=dict)
    global_config: Dict[str, Any] = field(default_factory=dict)
    resources: Dict[ResourceType, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of node execution."""
    node_id: str
    state: NodeState
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[ResourceType, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


class BaseNode(ABC):
    """Base class for all execution nodes."""
    
    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[NodeConfig] = None,
        inputs: Optional[List[NodeInput]] = None,
        outputs: Optional[List[NodeOutput]] = None
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.config = config or NodeConfig(self.node_id, self.__class__.__name__)
        self.inputs = {inp.name: inp for inp in (inputs or [])}
        self.outputs = {out.name: out for out in (outputs or [])}
        self.state = NodeState.PENDING
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the node's computation."""
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []
        
        for input_name, input_spec in self.inputs.items():
            if input_spec.required and input_name not in inputs:
                errors.append(f"Required input '{input_name}' is missing")
            elif input_name in inputs:
                value = inputs[input_name]
                if not isinstance(value, input_spec.data_type):
                    errors.append(
                        f"Input '{input_name}' should be {input_spec.data_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        return errors
    
    def get_resource_requirements(self) -> List[ResourceRequirement]:
        """Get resource requirements for this node."""
        return self.config.resource_requirements
    
    def add_dependency(self, node_id: str) -> None:
        """Add a dependency on another node."""
        self.dependencies.add(node_id)
    
    def add_dependent(self, node_id: str) -> None:
        """Add a node that depends on this one."""
        self.dependents.add(node_id)
    
    def can_execute(self, completed_nodes: Set[str]) -> bool:
        """Check if this node can execute given completed dependencies."""
        return self.dependencies.issubset(completed_nodes)
    
    def on_event(self, event: str, handler: Callable) -> None:
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


class FunctionNode(BaseNode):
    """A node that wraps a function for execution."""
    
    def __init__(
        self,
        func: Callable,
        node_id: Optional[str] = None,
        config: Optional[NodeConfig] = None
    ):
        self.func = func
        # Auto-detect inputs and outputs from function signature
        inputs, outputs = self._analyze_function(func)
        super().__init__(node_id, config, inputs, outputs)
    
    def _analyze_function(self, func: Callable) -> tuple[List[NodeInput], List[NodeOutput]]:
        """Analyze function signature to determine inputs and outputs."""
        import inspect
        
        sig = inspect.signature(func)
        inputs = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'context':
                continue  # Skip context parameter
            
            data_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            required = param.default == inspect.Parameter.empty
            default_value = param.default if not required else None
            
            inputs.append(NodeInput(
                name=param_name,
                data_type=data_type,
                required=required,
                default_value=default_value
            ))
        
        # For now, assume single output - could be enhanced
        return_type = sig.return_annotation if sig.return_annotation != inspect.Parameter.empty else Any
        outputs = [NodeOutput(name="result", data_type=return_type)]
        
        return inputs, outputs
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the wrapped function."""
        start_time = time.time()
        result = ExecutionResult(node_id=self.node_id, state=NodeState.RUNNING)
        
        try:
            # Prepare arguments
            import inspect
            sig = inspect.signature(self.func)
            args = {}
            
            for param_name in sig.parameters.keys():
                if param_name == 'context':
                    args[param_name] = context
                elif param_name in context.upstream_outputs:
                    args[param_name] = context.upstream_outputs[param_name]
                elif param_name in self.config.parameters:
                    args[param_name] = self.config.parameters[param_name]
            
            # Execute function
            if asyncio.iscoroutinefunction(self.func):
                output = await self.func(**args)
            else:
                output = self.func(**args)
            
            result.outputs = {"result": output}
            result.state = NodeState.COMPLETED
            
        except Exception as e:
            result.error = str(e)
            result.state = NodeState.FAILED
        
        result.execution_time = time.time() - start_time
        return result


class CommandNode(BaseNode):
    """A node that executes a system command."""
    
    def __init__(
        self,
        command: str,
        node_id: Optional[str] = None,
        config: Optional[NodeConfig] = None
    ):
        self.command = command
        inputs = [NodeInput("command_args", dict, required=False, default_value={})]
        outputs = [
            NodeOutput("stdout", str),
            NodeOutput("stderr", str),
            NodeOutput("return_code", int)
        ]
        super().__init__(node_id, config, inputs, outputs)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute the system command."""
        start_time = time.time()
        result = ExecutionResult(node_id=self.node_id, state=NodeState.RUNNING)
        
        try:
            # Format command with parameters
            formatted_command = self.command.format(**self.config.parameters)
            
            # Add any command args from upstream
            if "command_args" in context.upstream_outputs:
                args = context.upstream_outputs["command_args"]
                for key, value in args.items():
                    formatted_command = formatted_command.replace(f"{{{key}}}", str(value))
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                formatted_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**self.config.environment}
            )
            
            stdout_data, stderr_data = await process.communicate()
            
            result.outputs = {
                "stdout": stdout_data.decode(),
                "stderr": stderr_data.decode(),
                "return_code": process.returncode
            }
            
            if process.returncode == 0:
                result.state = NodeState.COMPLETED
            else:
                result.state = NodeState.FAILED
                result.error = f"Command failed with return code {process.returncode}"
            
        except Exception as e:
            result.error = str(e)
            result.state = NodeState.FAILED
        
        result.execution_time = time.time() - start_time
        return result


class ConditionalNode(BaseNode):
    """A node that executes conditionally based on upstream results."""
    
    def __init__(
        self,
        condition_func: Callable[[Dict[str, Any]], bool],
        true_node: BaseNode,
        false_node: Optional[BaseNode] = None,
        node_id: Optional[str] = None,
        config: Optional[NodeConfig] = None
    ):
        self.condition_func = condition_func
        self.true_node = true_node
        self.false_node = false_node
        
        inputs = [NodeInput("condition_data", dict)]
        outputs = [NodeOutput("result", Any)]
        super().__init__(node_id, config, inputs, outputs)
    
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Execute conditional logic."""
        start_time = time.time()
        result = ExecutionResult(node_id=self.node_id, state=NodeState.RUNNING)
        
        try:
            condition_data = context.upstream_outputs.get("condition_data", {})
            should_execute_true = self.condition_func(condition_data)
            
            if should_execute_true:
                if self.true_node:
                    node_result = await self.true_node.execute(context)
                    result.outputs = node_result.outputs
                else:
                    result.outputs = {"result": True}
            else:
                if self.false_node:
                    node_result = await self.false_node.execute(context)
                    result.outputs = node_result.outputs
                else:
                    result.outputs = {"result": False}
            
            result.state = NodeState.COMPLETED
            
        except Exception as e:
            result.error = str(e)
            result.state = NodeState.FAILED
        
        result.execution_time = time.time() - start_time
        return result


def node(
    node_id: Optional[str] = None,
    inputs: Optional[List[NodeInput]] = None,
    outputs: Optional[List[NodeOutput]] = None,
    **config_kwargs
):
    """Decorator to create a FunctionNode from a function."""
    def decorator(func):
        config = NodeConfig(
            node_id=node_id or func.__name__,
            node_type="function",
            **config_kwargs
        )
        return FunctionNode(func, node_id, config)
    return decorator