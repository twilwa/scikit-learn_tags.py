"""
Config-based Modular ML Training Orchestration (HuggingFace TRL Pattern)

This module provides a framework for configurable, modular machine learning
training workflows, similar to HuggingFace TRL's approach to training orchestration.
"""

from .config import *
from .trainers import *
from .workflows import *
from .callbacks import *

__version__ = "0.1.0"