"""
Test Plugin Customization & Prompt Optimization (pytest/pluggy Pattern)

This module provides a plugin system for test customization and optimization,
similar to pytest's plugin architecture with pluggy.
"""

from .hooks import *
from .plugins import *
from .manager import *
from .fixtures import *

__version__ = "0.1.0"