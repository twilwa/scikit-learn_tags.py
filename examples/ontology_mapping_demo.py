"""
Demo of the ontology mapping system - sklearn/_tags.py pattern.
"""

from src.ontology_mapping.tags import TagType, create_component_tags
from src.ontology_mapping.registry import ComponentRegistry, register_component
from src.ontology_mapping.mapper import CapabilityMapper, capability_endpoint, EndpointType


# Example 1: Component registration with tags
@register_component(
    "fast_transformer",
    description="High-performance transformer implementation",
    supports_streaming=True,
    supports_batching=True,
    requires_gpu=True,
    complexity="O(n²)",
    memory_intensive=True
)
class FastTransformer:
    """Fast transformer with GPU acceleration."""
    
    def transform(self, data):
        return f"Transformed {data} with GPU acceleration"


@register_component(
    "lightweight_processor", 
    description="CPU-optimized text processor",
    supports_streaming=True,
    supports_batching=False,
    requires_gpu=False,
    complexity="O(n)",
    memory_intensive=False,
    cpu_intensive=True
)
class LightweightProcessor:
    """Lightweight CPU-based processor."""
    
    def process(self, text):
        return f"Processed {text} on CPU"


# Example 2: API endpoint mapping
@capability_endpoint("/api/transform", "POST", {"supports_streaming", "supports_batching"})
async def transform_endpoint(data: dict, stream: bool = False):
    """Transform data using appropriate component."""
    from src.ontology_mapping.registry import get_component_registry
    
    registry = get_component_registry()
    
    if stream:
        components = registry.find_by_capability("supports_streaming", True)
    else:
        components = registry.find_by_capability("supports_batching", True)
    
    if not components:
        return {"error": "No suitable component found"}
    
    # Use the first available component
    component_class = components[0].component_class
    component = component_class()
    
    if hasattr(component, 'transform'):
        result = component.transform(data)
    else:
        result = component.process(data)
    
    return {"result": result, "component_used": components[0].name}


@capability_endpoint("/api/lightweight", "POST", {"cpu_intensive"})
async def lightweight_endpoint(text: str):
    """Process text with lightweight component."""
    from src.ontology_mapping.registry import get_component_registry
    
    registry = get_component_registry()
    components = registry.find_by_criteria({
        "cpu_intensive": True,
        "memory_intensive": False
    })
    
    if components:
        component = components[0].component_class()
        return {"result": component.process(text)}
    
    return {"error": "No lightweight component available"}


def main():
    """Demonstrate the ontology mapping system."""
    from src.ontology_mapping.registry import get_component_registry
    from src.ontology_mapping.mapper import get_capability_mapper
    
    registry = get_component_registry()
    mapper = get_capability_mapper()
    
    print("=== Registered Components ===")
    for info in registry.list_all():
        print(f"- {info.name}: {info.description}")
        print(f"  Tags: {dict(info.tags.tags)}")
    
    print("\n=== Capability Search Examples ===")
    
    # Find GPU components
    gpu_components = registry.find_by_tag("requires_gpu", True)
    print(f"GPU components: {[c.name for c in gpu_components]}")
    
    # Find streaming components
    streaming_components = registry.find_by_capability("supports_streaming", True)
    print(f"Streaming components: {[c.name for c in streaming_components]}")
    
    # Find lightweight components
    lightweight = registry.find_by_criteria({
        "memory_intensive": False,
        "cpu_intensive": True
    })
    print(f"Lightweight components: {[c.name for c in lightweight]}")
    
    print("\n=== Capabilities Matrix ===")
    matrix = registry.get_capabilities_matrix()
    capabilities = set()
    for comp_caps in matrix.values():
        capabilities.update(comp_caps.keys())
    
    # Print header
    print("Component".ljust(20), end="")
    for cap in sorted(capabilities):
        print(cap[:15].ljust(16), end="")
    print()
    
    # Print matrix
    for comp_name, comp_caps in matrix.items():
        print(comp_name.ljust(20), end="")
        for cap in sorted(capabilities):
            value = comp_caps.get(cap, False)
            print(str(value)[:15].ljust(16), end="")
        print()
    
    print("\n=== API Specification ===")
    api_spec = mapper.generate_api_spec()
    print(f"API paths: {list(api_spec['paths'].keys())}")
    print(f"Capabilities: {list(api_spec['components']['capabilities'].keys())}")


if __name__ == "__main__":
    main()