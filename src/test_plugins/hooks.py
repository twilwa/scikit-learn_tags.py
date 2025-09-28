"""
Hook specifications for the test plugin system.
"""

from typing import Any, Dict, List, Optional, Callable
import pluggy

# Create hook specification namespace
hookspec = pluggy.HookspecMarker("testplugin")
hookimpl = pluggy.HookimplMarker("testplugin")


class TestHookSpec:
    """Hook specifications for test lifecycle events."""
    
    @hookspec
    def pytest_configure(self, config):
        """Called after command line options have been parsed."""
        pass
    
    @hookspec
    def pytest_collection_modifyitems(self, session, config, items):
        """Called after test collection is completed."""
        pass
    
    @hookspec
    def pytest_runtest_setup(self, item):
        """Called before each test item is executed."""
        pass
    
    @hookspec
    def pytest_runtest_call(self, item):
        """Called during test execution."""
        pass
    
    @hookspec
    def pytest_runtest_teardown(self, item):
        """Called after each test item is executed."""
        pass
    
    @hookspec(firstresult=True)
    def pytest_runtest_makereport(self, item, call):
        """Called to create test reports."""
        pass
    
    @hookspec
    def pytest_sessionstart(self, session):
        """Called at the start of test session."""
        pass
    
    @hookspec
    def pytest_sessionfinish(self, session, exitstatus):
        """Called at the end of test session."""
        pass


class PromptHookSpec:
    """Hook specifications for prompt optimization."""
    
    @hookspec
    def prompt_generate(self, context: Dict[str, Any]) -> str:
        """Generate a prompt for the given context."""
        pass
    
    @hookspec
    def prompt_optimize(self, prompt: str, feedback: Dict[str, Any]) -> str:
        """Optimize a prompt based on feedback."""
        pass
    
    @hookspec
    def prompt_validate(self, prompt: str) -> Dict[str, Any]:
        """Validate a generated prompt."""
        pass
    
    @hookspec
    def prompt_template_load(self, template_name: str) -> Optional[str]:
        """Load a prompt template by name."""
        pass
    
    @hookspec
    def prompt_context_prepare(self, raw_context: Any) -> Dict[str, Any]:
        """Prepare context for prompt generation."""
        pass


class CodeGenHookSpec:
    """Hook specifications for code generation testing."""
    
    @hookspec
    def codegen_analyze_requirements(self, requirements: str) -> Dict[str, Any]:
        """Analyze code generation requirements."""
        pass
    
    @hookspec
    def codegen_generate_tests(self, code: str, requirements: Dict[str, Any]) -> List[str]:
        """Generate tests for given code."""
        pass
    
    @hookspec
    def codegen_validate_output(self, generated_code: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated code against requirements."""
        pass
    
    @hookspec
    def codegen_optimize_prompt(self, prompt: str, generation_result: Dict[str, Any]) -> str:
        """Optimize code generation prompts based on results."""
        pass


class DataHookSpec:
    """Hook specifications for test data management."""
    
    @hookspec
    def data_fixture_create(self, fixture_name: str, config: Dict[str, Any]) -> Any:
        """Create test data fixtures."""
        pass
    
    @hookspec
    def data_fixture_cleanup(self, fixture_name: str, data: Any) -> None:
        """Clean up test data fixtures."""
        pass
    
    @hookspec
    def data_mock_generate(self, schema: Dict[str, Any]) -> Any:
        """Generate mock data based on schema."""
        pass
    
    @hookspec
    def data_validate_schema(self, data: Any, schema: Dict[str, Any]) -> bool:
        """Validate data against schema."""
        pass


class MetricsHookSpec:
    """Hook specifications for test metrics and reporting."""
    
    @hookspec
    def metrics_collect(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Collect metrics from test results."""
        pass
    
    @hookspec
    def metrics_aggregate(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate collected metrics."""
        pass
    
    @hookspec
    def metrics_report(self, aggregated_metrics: Dict[str, Any]) -> str:
        """Generate metrics report."""
        pass
    
    @hookspec
    def performance_measure(self, operation: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Measure performance of operations."""
        pass


class AllHookSpecs(
    TestHookSpec, 
    PromptHookSpec, 
    CodeGenHookSpec, 
    DataHookSpec, 
    MetricsHookSpec
):
    """Combined hook specifications."""
    pass


# Create plugin manager
def create_plugin_manager():
    """Create and configure plugin manager."""
    pm = pluggy.PluginManager("testplugin")
    pm.add_hookspecs(AllHookSpecs)
    return pm