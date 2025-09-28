"""
Tag system for capability and metadata management.

Based on scikit-learn's _tags.py pattern for flexible component annotation.
"""

from typing import Dict, Set, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum


class TagType(Enum):
    """Types of tags for different categorization needs."""
    CAPABILITY = "capability"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    RESOURCE = "resource"
    QUALITY = "quality"


@dataclass
class Tag:
    """A single tag with metadata."""
    name: str
    tag_type: TagType
    value: Any
    description: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.tag_type.value} tag: {self.name}"


class TagRegistry:
    """Registry for managing available tags and their definitions."""
    
    def __init__(self):
        self._tags: Dict[str, Tag] = {}
        self._by_type: Dict[TagType, Set[str]] = {t: set() for t in TagType}
        self._initialize_default_tags()
    
    def _initialize_default_tags(self):
        """Initialize with commonly used tags."""
        default_tags = [
            # Capability tags
            Tag("supports_streaming", TagType.CAPABILITY, bool, 
                "Whether component supports streaming data processing"),
            Tag("supports_batching", TagType.CAPABILITY, bool,
                "Whether component supports batch processing"),
            Tag("supports_async", TagType.CAPABILITY, bool,
                "Whether component supports asynchronous execution"),
            Tag("input_types", TagType.CAPABILITY, List[str],
                "Supported input data types"),
            Tag("output_types", TagType.CAPABILITY, List[str],
                "Supported output data types"),
            
            # Performance tags
            Tag("complexity", TagType.PERFORMANCE, str,
                "Computational complexity (O notation)"),
            Tag("memory_usage", TagType.PERFORMANCE, str,
                "Memory usage characteristics"),
            Tag("scalability", TagType.PERFORMANCE, str,
                "Scalability characteristics"),
            
            # Compatibility tags
            Tag("requires_gpu", TagType.COMPATIBILITY, bool,
                "Whether GPU is required"),
            Tag("min_python_version", TagType.COMPATIBILITY, str,
                "Minimum Python version required"),
            Tag("dependencies", TagType.COMPATIBILITY, List[str],
                "Required dependencies"),
            
            # Resource tags
            Tag("cpu_intensive", TagType.RESOURCE, bool,
                "Whether component is CPU intensive"),
            Tag("memory_intensive", TagType.RESOURCE, bool,
                "Whether component is memory intensive"),
            Tag("network_intensive", TagType.RESOURCE, bool,
                "Whether component is network intensive"),
            
            # Quality tags
            Tag("experimental", TagType.QUALITY, bool,
                "Whether component is experimental"),
            Tag("stable", TagType.QUALITY, bool,
                "Whether component is stable"),
            Tag("deprecated", TagType.QUALITY, bool,
                "Whether component is deprecated"),
        ]
        
        for tag in default_tags:
            self.register_tag(tag)
    
    def register_tag(self, tag: Tag) -> None:
        """Register a new tag definition."""
        self._tags[tag.name] = tag
        self._by_type[tag.tag_type].add(tag.name)
    
    def get_tag(self, name: str) -> Optional[Tag]:
        """Get tag definition by name."""
        return self._tags.get(name)
    
    def get_tags_by_type(self, tag_type: TagType) -> Set[str]:
        """Get all tag names of a specific type."""
        return self._by_type[tag_type].copy()
    
    def list_all_tags(self) -> List[Tag]:
        """List all registered tags."""
        return list(self._tags.values())


# Global tag registry instance
_tag_registry = TagRegistry()


def get_tag_registry() -> TagRegistry:
    """Get the global tag registry."""
    return _tag_registry


@dataclass
class ComponentTags:
    """Container for all tags associated with a component."""
    component_name: str
    tags: Dict[str, Any] = field(default_factory=dict)
    
    def set_tag(self, name: str, value: Any) -> None:
        """Set a tag value."""
        tag_def = _tag_registry.get_tag(name)
        if not tag_def:
            raise ValueError(f"Unknown tag: {name}")
        
        # Basic type validation
        if tag_def.value is not Any and not isinstance(value, tag_def.value):
            if tag_def.value == bool and isinstance(value, (int, str)):
                # Allow conversion for common cases
                value = bool(value)
            else:
                raise TypeError(f"Tag {name} expects {tag_def.value}, got {type(value)}")
        
        self.tags[name] = value
    
    def get_tag(self, name: str, default: Any = None) -> Any:
        """Get a tag value."""
        return self.tags.get(name, default)
    
    def has_tag(self, name: str) -> bool:
        """Check if component has a specific tag."""
        return name in self.tags
    
    def get_tags_by_type(self, tag_type: TagType) -> Dict[str, Any]:
        """Get all tags of a specific type."""
        type_tags = _tag_registry.get_tags_by_type(tag_type)
        return {name: value for name, value in self.tags.items() if name in type_tags}
    
    def matches_criteria(self, criteria: Dict[str, Any]) -> bool:
        """Check if component matches given tag criteria."""
        for tag_name, expected_value in criteria.items():
            actual_value = self.get_tag(tag_name)
            if actual_value != expected_value:
                return False
        return True


def create_component_tags(component_name: str, **tag_values) -> ComponentTags:
    """Create component tags with initial values."""
    tags = ComponentTags(component_name)
    for name, value in tag_values.items():
        tags.set_tag(name, value)
    return tags