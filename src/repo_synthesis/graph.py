"""
Repository graph analysis and visualization tools.
"""

import networkx as nx
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from .analyzer import RepositoryStructure


@dataclass
class GraphMetrics:
    """Metrics for repository graph analysis."""
    total_nodes: int
    total_edges: int
    connected_components: int
    average_degree: float
    clustering_coefficient: float


class RepositoryGraph:
    """Graph representation of repository structure."""
    
    def __init__(self, repo_structure: RepositoryStructure):
        self.repo_structure = repo_structure
        self.graph = self._build_graph()
    
    def _build_graph(self) -> nx.DiGraph:
        """Build dependency graph from repository structure."""
        graph = nx.DiGraph()
        
        # Add nodes for each file
        for file_path in self.repo_structure.files.keys():
            graph.add_node(file_path)
        
        # Add edges for dependencies
        for file_path, dependencies in self.repo_structure.dependencies.items():
            for dep in dependencies:
                if dep in self.repo_structure.files:
                    graph.add_edge(file_path, dep)
        
        return graph
    
    def get_metrics(self) -> GraphMetrics:
        """Calculate graph metrics."""
        return GraphMetrics(
            total_nodes=self.graph.number_of_nodes(),
            total_edges=self.graph.number_of_edges(),
            connected_components=nx.number_weakly_connected_components(self.graph),
            average_degree=sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            clustering_coefficient=nx.average_clustering(self.graph.to_undirected()) if self.graph.number_of_nodes() > 0 else 0
        )
    
    def find_central_files(self, top_k: int = 5) -> List[str]:
        """Find most central files in the dependency graph."""
        centrality = nx.betweenness_centrality(self.graph)
        return sorted(centrality.keys(), key=centrality.get, reverse=True)[:top_k]