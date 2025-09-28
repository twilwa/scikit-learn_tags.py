"""
Component registry with tag-based discovery and filtering.
"""

from typing import Dict, List, Optional, Set, Callable, Any, Type
from dataclasses import dataclass
import inspect
from .tags import ComponentTags, TagType, create_component_tags


@dataclass
class ComponentInfo:
    """Information about a registered component."""
    name: str
    component_class: Type
    tags: ComponentTags
    module_path: str
    description: Optional[str] = None


class ComponentRegistry:
    """Registry for components with tag-based discovery."""
    
    def __init__(self):
        self._components: Dict[str, ComponentInfo] = {}
        self._by_tag: Dict[str, Set[str]] = {}
    
    def register(
        self, 
        name: str, 
        component_class: Type, 
        description: Optional[str] = None,
        **tag_values
    ) -> None:
        """Register a component with tags."""
        tags = create_component_tags(name, **tag_values)
        
        info = ComponentInfo(
            name=name,
            component_class=component_class,
            tags=tags,
            module_path=f"{component_class.__module__}.{component_class.__name__}",
            description=description or component_class.__doc__
        )
        
        self._components[name] = info
        
        # Update tag index
        for tag_name in tags.tags.keys():
            if tag_name not in self._by_tag:
                self._by_tag[tag_name] = set()
            self._by_tag[tag_name].add(name)
    
    def unregister(self, name: str) -> None:
        """Unregister a component."""
        if name not in self._components:
            return
        
        info = self._components[name]
        
        # Remove from tag index
        for tag_name in info.tags.tags.keys():
            if tag_name in self._by_tag:
                self._by_tag[tag_name].discard(name)
                if not self._by_tag[tag_name]:
                    del self._by_tag[tag_name]
        
        del self._components[name]
    
    def get(self, name: str) -> Optional[ComponentInfo]:
        """Get component info by name."""
        return self._components.get(name)
    
    def list_all(self) -> List[ComponentInfo]:
        """List all registered components."""
        return list(self._components.values())
    
    def find_by_tag(self, tag_name: str, tag_value: Any = None) -> List[ComponentInfo]:
        """Find components by tag name and optionally value."""
        if tag_name not in self._by_tag:
            return []
        
        candidates = [self._components[name] for name in self._by_tag[tag_name]]
        
        if tag_value is not None:
            candidates = [
                info for info in candidates 
                if info.tags.get_tag(tag_name) == tag_value
            ]
        
        return candidates
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[ComponentInfo]:
        """Find components matching all criteria."""
        if not criteria:
            return self.list_all()
        
        # Start with components that have the first tag
        first_tag = next(iter(criteria))
        candidates = self.find_by_tag(first_tag, criteria[first_tag])
        
        # Filter by remaining criteria
        for tag_name, tag_value in list(criteria.items())[1:]:
            candidates = [
                info for info in candidates
                if info.tags.get_tag(tag_name) == tag_value
            ]
        
        return candidates
    
    def find_by_capability(self, capability: str, value: bool = True) -> List[ComponentInfo]:
        """Find components with specific capability."""
        return self.find_by_tag(capability, value)
    
    def find_compatible(self, **requirements) -> List[ComponentInfo]:
        """Find components compatible with requirements."""
        compatible = []
        
        for info in self.list_all():
            is_compatible = True
            
            # Check each requirement
            for req_name, req_value in requirements.items():
                if req_name == "min_python_version":
                    # Special handling for version comparison
                    comp_version = info.tags.get_tag("min_python_version", "3.8")
                    if comp_version > req_value:
                        is_compatible = False
                        break
                elif req_name == "max_memory_usage":
                    # Special handling for resource constraints
                    if info.tags.get_tag("memory_intensive", False):
                        is_compatible = False
                        break
                else:
                    # Direct tag matching
                    if not info.tags.matches_criteria({req_name: req_value}):
                        is_compatible = False
                        break
            
            if is_compatible:
                compatible.append(info)
        
        return compatible
    
    def get_capabilities_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Get a matrix of all components and their capabilities."""
        matrix = {}
        capability_tags = set()
        
        # Collect all capability tags
        for info in self.list_all():
            cap_tags = info.tags.get_tags_by_type(TagType.CAPABILITY)
            capability_tags.update(cap_tags.keys())
        
        # Build matrix
        for info in self.list_all():
            matrix[info.name] = {}
            for cap in capability_tags:
                matrix[info.name][cap] = info.tags.get_tag(cap, False)
        
        return matrix


# Global component registry
_component_registry = ComponentRegistry()


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry."""
    return _component_registry


def register_component(
    name: Optional[str] = None,
    description: Optional[str] = None,
    **tag_values
):
    """Decorator to register a component with tags."""
    def decorator(cls):
        component_name = name or cls.__name__
        _component_registry.register(
            component_name, 
            cls, 
            description=description,
            **tag_values
        )
        return cls
    return decorator


# Example usage and helper functions
def find_streaming_components() -> List[ComponentInfo]:
    """Find all components that support streaming."""
    return _component_registry.find_by_capability("supports_streaming", True)


def find_gpu_components() -> List[ComponentInfo]:
    """Find all components that require GPU."""
    return _component_registry.find_by_tag("requires_gpu", True)


def find_lightweight_components() -> List[ComponentInfo]:
    """Find components that are not resource intensive."""
    return _component_registry.find_by_criteria({
        "cpu_intensive": False,
        "memory_intensive": False
    })