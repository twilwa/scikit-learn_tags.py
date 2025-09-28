"""
DAG Node Execution Configuration System (Dagster Pattern)

This module provides a framework for defining and executing directed acyclic graphs
of computation nodes, similar to Dagster's approach to data pipeline orchestration.
"""

from .node import *
from .dag import *
from .executor import *
from .config import *

__version__ = "0.1.0"