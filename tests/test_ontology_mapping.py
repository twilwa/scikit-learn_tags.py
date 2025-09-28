"""
Tests for the ontology mapping system.
"""

import pytest
from src.ontology_mapping.tags import TagType, Tag, ComponentTags, create_component_tags
from src.ontology_mapping.registry import ComponentRegistry, register_component


def test_tag_creation():
    """Test basic tag creation and validation."""
    tag = Tag("test_capability", TagType.CAPABILITY, bool, "Test capability")
    assert tag.name == "test_capability"
    assert tag.tag_type == TagType.CAPABILITY
    assert tag.value == bool


def test_component_tags():
    """Test component tag management."""
    tags = create_component_tags("test_component", supports_streaming=True, complexity="O(n)")
    
    assert tags.get_tag("supports_streaming") is True
    assert tags.get_tag("complexity") == "O(n)"
    assert tags.has_tag("supports_streaming")
    assert not tags.has_tag("nonexistent_tag")


def test_component_registry():
    """Test component registration and discovery."""
    registry = ComponentRegistry()
    
    class TestComponent:
        """A test component."""
        pass
    
    registry.register(
        "test_component",
        TestComponent,
        supports_streaming=True,
        requires_gpu=False
    )
    
    # Test retrieval
    info = registry.get("test_component")
    assert info is not None
    assert info.name == "test_component"
    assert info.component_class == TestComponent
    
    # Test capability search
    streaming_components = registry.find_by_capability("supports_streaming", True)
    assert len(streaming_components) == 1
    assert streaming_components[0].name == "test_component"


def test_register_decorator():
    """Test the register decorator."""
    
    @register_component("decorated_component", supports_async=True)
    class DecoratedComponent:
        """A decorated test component."""
        pass
    
    from src.ontology_mapping.registry import get_component_registry
    registry = get_component_registry()
    
    info = registry.get("decorated_component")
    assert info is not None
    assert info.tags.get_tag("supports_async") is True


if __name__ == "__main__":
    pytest.main([__file__])