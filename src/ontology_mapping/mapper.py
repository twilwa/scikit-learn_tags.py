"""
API capability mapper for dynamic service discovery and routing.
"""

from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import inspect
from .registry import ComponentRegistry, get_component_registry
from .tags import TagType


class EndpointType(Enum):
    """Types of API endpoints."""
    REST = "rest"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    WEBSOCKET = "websocket"
    FUNCTION = "function"


@dataclass
class APIEndpoint:
    """Represents an API endpoint with capabilities."""
    path: str
    method: str
    endpoint_type: EndpointType
    handler: Callable
    capabilities: Set[str] = field(default_factory=set)
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class ServiceMapping:
    """Maps capabilities to service implementations."""
    capability: str
    service_name: str
    endpoint: APIEndpoint
    component_name: str
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CapabilityMapper:
    """Maps ontology capabilities to API endpoints and services."""
    
    def __init__(self, component_registry: Optional[ComponentRegistry] = None):
        self.registry = component_registry or get_component_registry()
        self._mappings: Dict[str, List[ServiceMapping]] = {}
        self._endpoints: Dict[str, APIEndpoint] = {}
        self._reverse_map: Dict[str, Set[str]] = {}
    
    def register_endpoint(
        self,
        path: str,
        method: str,
        handler: Callable,
        endpoint_type: EndpointType = EndpointType.REST,
        capabilities: Optional[Set[str]] = None,
        description: Optional[str] = None
    ) -> APIEndpoint:
        """Register an API endpoint with its capabilities."""
        endpoint_id = f"{method}:{path}"
        
        if capabilities is None:
            capabilities = self._infer_capabilities(handler)
        
        endpoint = APIEndpoint(
            path=path,
            method=method,
            endpoint_type=endpoint_type,
            handler=handler,
            capabilities=capabilities,
            parameters=self._extract_parameters(handler),
            description=description or handler.__doc__
        )
        
        self._endpoints[endpoint_id] = endpoint
        
        # Update reverse mapping
        for capability in capabilities:
            if capability not in self._reverse_map:
                self._reverse_map[capability] = set()
            self._reverse_map[capability].add(endpoint_id)
        
        return endpoint
    
    def map_capability_to_service(
        self,
        capability: str,
        service_name: str,
        endpoint_path: str,
        method: str = "POST",
        component_name: Optional[str] = None,
        priority: int = 0,
        **metadata
    ) -> None:
        """Map a capability to a specific service endpoint."""
        endpoint_id = f"{method}:{endpoint_path}"
        endpoint = self._endpoints.get(endpoint_id)
        
        if not endpoint:
            raise ValueError(f"Endpoint {endpoint_id} not registered")
        
        mapping = ServiceMapping(
            capability=capability,
            service_name=service_name,
            endpoint=endpoint,
            component_name=component_name or service_name,
            priority=priority,
            metadata=metadata
        )
        
        if capability not in self._mappings:
            self._mappings[capability] = []
        
        self._mappings[capability].append(mapping)
        # Sort by priority (higher first)
        self._mappings[capability].sort(key=lambda x: x.priority, reverse=True)
    
    def find_services_for_capability(self, capability: str) -> List[ServiceMapping]:
        """Find all services that provide a specific capability."""
        return self._mappings.get(capability, [])
    
    def find_best_service_for_capability(self, capability: str) -> Optional[ServiceMapping]:
        """Find the best service for a capability (highest priority)."""
        services = self.find_services_for_capability(capability)
        return services[0] if services else None
    
    def find_endpoints_for_capability(self, capability: str) -> List[APIEndpoint]:
        """Find all endpoints that provide a specific capability."""
        endpoint_ids = self._reverse_map.get(capability, set())
        return [self._endpoints[eid] for eid in endpoint_ids]
    
    def get_capability_coverage(self) -> Dict[str, int]:
        """Get coverage statistics for capabilities."""
        coverage = {}
        for capability, mappings in self._mappings.items():
            coverage[capability] = len(mappings)
        return coverage
    
    def generate_api_spec(self) -> Dict[str, Any]:
        """Generate API specification with capability mappings."""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Capability-Based API",
                "version": "1.0.0",
                "description": "Auto-generated API based on capability mappings"
            },
            "paths": {},
            "components": {
                "schemas": {},
                "capabilities": {}
            }
        }
        
        # Group endpoints by path
        path_groups = {}
        for endpoint in self._endpoints.values():
            if endpoint.path not in path_groups:
                path_groups[endpoint.path] = []
            path_groups[endpoint.path].append(endpoint)
        
        # Generate path specifications
        for path, endpoints in path_groups.items():
            spec["paths"][path] = {}
            for endpoint in endpoints:
                method_spec = {
                    "summary": endpoint.description or f"{endpoint.method} {endpoint.path}",
                    "operationId": f"{endpoint.method.lower()}_{path.replace('/', '_').strip('_')}",
                    "tags": list(endpoint.capabilities),
                    "parameters": self._generate_parameter_spec(endpoint.parameters),
                    "responses": {
                        "200": {"description": "Success"},
                        "400": {"description": "Bad Request"},
                        "500": {"description": "Internal Server Error"}
                    }
                }
                spec["paths"][path][endpoint.method.lower()] = method_spec
        
        # Add capability definitions
        for capability, mappings in self._mappings.items():
            spec["components"]["capabilities"][capability] = {
                "description": f"Capability: {capability}",
                "services": [
                    {
                        "name": mapping.service_name,
                        "endpoint": f"{mapping.endpoint.method} {mapping.endpoint.path}",
                        "priority": mapping.priority,
                        "metadata": mapping.metadata
                    }
                    for mapping in mappings
                ]
            }
        
        return spec
    
    def _infer_capabilities(self, handler: Callable) -> Set[str]:
        """Infer capabilities from function signature and docstring."""
        capabilities = set()
        
        # Analyze function name
        func_name = handler.__name__.lower()
        if "stream" in func_name:
            capabilities.add("supports_streaming")
        if "batch" in func_name:
            capabilities.add("supports_batching")
        if "async" in func_name:
            capabilities.add("supports_async")
        
        # Analyze docstring
        if handler.__doc__:
            doc = handler.__doc__.lower()
            if "stream" in doc:
                capabilities.add("supports_streaming")
            if "batch" in doc:
                capabilities.add("supports_batching")
            if "gpu" in doc:
                capabilities.add("requires_gpu")
        
        # Analyze function signature
        sig = inspect.signature(handler)
        for param_name, param in sig.parameters.items():
            if "stream" in param_name.lower():
                capabilities.add("supports_streaming")
            if "batch" in param_name.lower():
                capabilities.add("supports_batching")
        
        return capabilities
    
    def _extract_parameters(self, handler: Callable) -> Dict[str, Any]:
        """Extract parameter specifications from function signature."""
        sig = inspect.signature(handler)
        parameters = {}
        
        for param_name, param in sig.parameters.items():
            param_info = {
                "name": param_name,
                "required": param.default == inspect.Parameter.empty,
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any"
            }
            
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            parameters[param_name] = param_info
        
        return parameters
    
    def _generate_parameter_spec(self, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate OpenAPI parameter specifications."""
        specs = []
        for param_name, param_info in parameters.items():
            spec = {
                "name": param_name,
                "in": "query",
                "required": param_info.get("required", False),
                "schema": {"type": self._python_type_to_openapi(param_info.get("type", "any"))}
            }
            specs.append(spec)
        return specs
    
    def _python_type_to_openapi(self, python_type: str) -> str:
        """Convert Python type annotation to OpenAPI type."""
        type_mapping = {
            "str": "string",
            "int": "integer", 
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "any": "string"
        }
        return type_mapping.get(python_type.lower(), "string")


# Global capability mapper instance
_capability_mapper = CapabilityMapper()


def get_capability_mapper() -> CapabilityMapper:
    """Get the global capability mapper."""
    return _capability_mapper


def capability_endpoint(
    path: str,
    method: str = "POST",
    capabilities: Optional[Set[str]] = None,
    endpoint_type: EndpointType = EndpointType.REST
):
    """Decorator to register a function as a capability endpoint."""
    def decorator(func):
        _capability_mapper.register_endpoint(
            path=path,
            method=method,
            handler=func,
            endpoint_type=endpoint_type,
            capabilities=capabilities
        )
        return func
    return decorator