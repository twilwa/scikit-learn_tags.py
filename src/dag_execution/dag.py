"""
Directed Acyclic Graph (DAG) execution system.
"""

import asyncio
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from .node import BaseNode, NodeState, ExecutionContext, ExecutionResult


class DAGState(Enum):
    """States a DAG can be in during execution."""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DAGExecutionResult:
    """Result of DAG execution."""
    dag_id: str
    state: DAGState
    node_results: Dict[str, ExecutionResult] = field(default_factory=dict)
    execution_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DAG:
    """Directed Acyclic Graph for node execution."""
    
    def __init__(self, dag_id: str):
        self.dag_id = dag_id
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, BaseNode] = {}
        self.state = DAGState.PENDING
        self.metadata = {}
    
    def add_node(self, node: BaseNode) -> None:
        """Add a node to the DAG."""
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)
    
    def add_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Add an edge between two nodes."""
        if from_node_id not in self.nodes:
            raise ValueError(f"Node {from_node_id} not found in DAG")
        if to_node_id not in self.nodes:
            raise ValueError(f"Node {to_node_id} not found in DAG")
        
        self.graph.add_edge(from_node_id, to_node_id)
        
        # Update node dependencies
        self.nodes[to_node_id].add_dependency(from_node_id)
        self.nodes[from_node_id].add_dependent(to_node_id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            # Remove the edge that created the cycle
            self.graph.remove_edge(from_node_id, to_node_id)
            self.nodes[to_node_id].dependencies.remove(from_node_id)
            self.nodes[from_node_id].dependents.remove(to_node_id)
            raise ValueError("Adding edge would create a cycle in the DAG")
    
    def remove_node(self, node_id: str) -> None:
        """Remove a node from the DAG."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.graph.remove_node(node_id)
    
    def remove_edge(self, from_node_id: str, to_node_id: str) -> None:
        """Remove an edge between two nodes."""
        if self.graph.has_edge(from_node_id, to_node_id):
            self.graph.remove_edge(from_node_id, to_node_id)
            self.nodes[to_node_id].dependencies.remove(from_node_id)
            self.nodes[from_node_id].dependents.remove(to_node_id)
    
    def get_ready_nodes(self, completed_nodes: Set[str]) -> List[BaseNode]:
        """Get nodes that are ready to execute."""
        ready = []
        for node_id, node in self.nodes.items():
            if (node.state == NodeState.PENDING and 
                node.can_execute(completed_nodes)):
                ready.append(node)
        return ready
    
    def get_topological_order(self) -> List[str]:
        """Get topological ordering of nodes."""
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError:
            raise ValueError("DAG contains cycles")
    
    def validate(self) -> List[str]:
        """Validate the DAG structure."""
        errors = []
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            errors.append("DAG contains cycles")
        
        # Check for isolated nodes (nodes with no connections)
        isolated = list(nx.isolates(self.graph))
        if isolated and len(self.nodes) > 1:
            errors.append(f"Isolated nodes found: {isolated}")
        
        # Check that all referenced nodes exist
        for node_id in self.graph.nodes():
            if node_id not in self.nodes:
                errors.append(f"Graph references non-existent node: {node_id}")
        
        # Check node dependencies match graph structure
        for node_id, node in self.nodes.items():
            graph_predecessors = set(self.graph.predecessors(node_id))
            if node.dependencies != graph_predecessors:
                errors.append(f"Node {node_id} dependencies don't match graph structure")
        
        return errors
    
    async def execute(
        self, 
        context: ExecutionContext,
        max_parallel: int = 4
    ) -> Dict[str, ExecutionResult]:
        """Execute the DAG."""
        import time
        
        start_time = time.time()
        self.state = DAGState.RUNNING
        
        try:
            # Validate DAG before execution
            validation_errors = self.validate()
            if validation_errors:
                raise ValueError(f"DAG validation failed: {validation_errors}")
            
            completed_nodes = set()
            failed_nodes = set()
            node_results = {}
            
            # Create semaphore for parallel execution
            semaphore = asyncio.Semaphore(max_parallel)
            
            async def execute_node(node: BaseNode) -> ExecutionResult:
                """Execute a single node with semaphore."""
                async with semaphore:
                    node.state = NodeState.RUNNING
                    
                    # Prepare context with upstream outputs
                    node_context = ExecutionContext(
                        run_id=context.run_id,
                        execution_time=time.time(),
                        upstream_outputs=context.upstream_outputs.copy(),
                        global_config=context.global_config,
                        resources=context.resources,
                        metadata=context.metadata
                    )
                    
                    # Add outputs from completed dependencies
                    for dep_id in node.dependencies:
                        if dep_id in node_results:
                            dep_result = node_results[dep_id]
                            node_context.upstream_outputs.update(dep_result.outputs)
                    
                    # Execute node
                    result = await node.execute(node_context)
                    return result
            
            # Execute nodes in topological order with parallelization
            while len(completed_nodes) + len(failed_nodes) < len(self.nodes):
                # Get nodes ready for execution
                ready_nodes = self.get_ready_nodes(completed_nodes)
                
                if not ready_nodes:
                    # Check if we're stuck due to failed dependencies
                    remaining_nodes = set(self.nodes.keys()) - completed_nodes - failed_nodes
                    if remaining_nodes:
                        self.state = DAGState.FAILED
                        raise RuntimeError(f"No ready nodes found, but {len(remaining_nodes)} nodes remain")
                    break
                
                # Execute ready nodes in parallel
                tasks = [execute_node(node) for node in ready_nodes]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for node, result in zip(ready_nodes, results):
                    if isinstance(result, Exception):
                        node.state = NodeState.FAILED
                        failed_nodes.add(node.node_id)
                        node_results[node.node_id] = ExecutionResult(
                            node_id=node.node_id,
                            state=NodeState.FAILED,
                            error=str(result)
                        )
                    else:
                        node.state = result.state
                        node_results[node.node_id] = result
                        if result.state == NodeState.COMPLETED:
                            completed_nodes.add(node.node_id)
                        else:
                            failed_nodes.add(node.node_id)
            
            # Determine final state
            if failed_nodes:
                self.state = DAGState.FAILED
            else:
                self.state = DAGState.COMPLETED
            
            return node_results
            
        except Exception as e:
            self.state = DAGState.FAILED
            raise e
        
        finally:
            execution_time = time.time() - start_time
            # Could emit events or update metrics here
    
    def get_execution_plan(self) -> Dict[str, Any]:
        """Get execution plan for the DAG."""
        topo_order = self.get_topological_order()
        
        execution_levels = []
        completed = set()
        
        while len(completed) < len(self.nodes):
            current_level = []
            for node_id in topo_order:
                if node_id not in completed:
                    node = self.nodes[node_id]
                    if node.dependencies.issubset(completed):
                        current_level.append(node_id)
            
            if not current_level:
                break
                
            execution_levels.append(current_level)
            completed.update(current_level)
        
        return {
            "dag_id": self.dag_id,
            "total_nodes": len(self.nodes),
            "execution_levels": execution_levels,
            "max_parallelism": max(len(level) for level in execution_levels) if execution_levels else 0,
            "estimated_steps": len(execution_levels)
        }
    
    def visualize(self) -> str:
        """Generate a text visualization of the DAG."""
        lines = [f"DAG: {self.dag_id}"]
        lines.append(f"Nodes: {len(self.nodes)}")
        lines.append(f"Edges: {len(self.graph.edges())}")
        lines.append("")
        
        # Show topological order
        try:
            topo_order = self.get_topological_order()
            lines.append("Execution Order:")
            for i, node_id in enumerate(topo_order):
                node = self.nodes[node_id]
                deps = ", ".join(node.dependencies) if node.dependencies else "None"
                lines.append(f"  {i+1}. {node_id} (deps: {deps})")
        except ValueError as e:
            lines.append(f"Invalid DAG: {e}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary representation."""
        return {
            "dag_id": self.dag_id,
            "nodes": {
                node_id: {
                    "node_type": node.__class__.__name__,
                    "config": node.config.to_dict() if hasattr(node.config, 'to_dict') else str(node.config)
                }
                for node_id, node in self.nodes.items()
            },
            "edges": list(self.graph.edges()),
            "state": self.state.value,
            "metadata": self.metadata
        }
    
    def clone(self, new_dag_id: str) -> 'DAG':
        """Create a copy of this DAG with a new ID."""
        new_dag = DAG(new_dag_id)
        
        # Copy nodes (shallow copy)
        for node in self.nodes.values():
            new_dag.add_node(node)
        
        # Copy edges
        for from_node, to_node in self.graph.edges():
            new_dag.add_edge(from_node, to_node)
        
        # Copy metadata
        new_dag.metadata = self.metadata.copy()
        
        return new_dag