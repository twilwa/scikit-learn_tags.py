"""
Interface & Model Implementation Patterns (HF/Transformers Pattern)

This module provides abstract interfaces and implementation patterns
similar to HuggingFace Transformers' architecture for model abstractions.
"""

from .interfaces import *
from .implementations import *
from .registry import *
from .factory import *

__version__ = "0.1.0"