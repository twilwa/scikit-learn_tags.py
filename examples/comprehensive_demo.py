"""
Comprehensive demonstration of all repo graph planning components.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all major components
from ontology_mapping.tags import create_component_tags, TagType
from ontology_mapping.registry import ComponentRegistry, register_component
from ontology_mapping.mapper import CapabilityMapper, capability_endpoint

from repo_synthesis.analyzer import CodeAnalyzer, RepositoryStructure

from multi_agent.agent import SpecializedAgent, Task, AgentCapability
from multi_agent.communication import MessageBus

from dag_execution.node import FunctionNode, CommandNode, node, NodeConfig, ExecutionContext
from dag_execution.dag import DAG

from feature_extraction.extractors import TextFeatureExtractor, CodeFeatureExtractor, CompositeExtractor

from ml_orchestration.config import ExperimentConfig, ModelConfig, TrainingConfig, ConfigManager

from nlp_capabilities.capabilities import get_capability, Document, CAPABILITY_REGISTRY

from interface_patterns.interfaces import BaseModel, ClassificationModel, BatchInput, ModelOutput

from test_plugins.hooks import create_plugin_manager, hookimpl


# Demo 1: Ontology Mapping System
def demo_ontology_mapping():
    """Demonstrate the ontology mapping system."""
    print("=== Ontology Mapping System Demo ===")
    
    # Register components with capabilities
    @register_component(
        "ml_transformer",
        description="Machine learning transformer model",
        supports_streaming=True,
        supports_batching=True,
        requires_gpu=True,
        complexity="O(n²)",
        input_types=["text", "tokens"],
        output_types=["embeddings", "classifications"]
    )
    class MLTransformer:
        def transform(self, data):
            return f"Transformed: {data}"
    
    @register_component(
        "text_processor",
        description="Lightweight text processing",
        supports_streaming=True,
        supports_batching=False,
        requires_gpu=False,
        complexity="O(n)",
        cpu_intensive=True,
        memory_intensive=False
    )
    class TextProcessor:
        def process(self, text):
            return f"Processed: {text}"
    
    # Query the registry
    from ontology_mapping.registry import get_component_registry
    registry = get_component_registry()
    
    print(f"Total components: {len(registry.list_all())}")
    
    # Find components by capability
    streaming_components = registry.find_by_capability("supports_streaming", True)
    print(f"Streaming components: {[c.name for c in streaming_components]}")
    
    gpu_components = registry.find_by_tag("requires_gpu", True)
    print(f"GPU components: {[c.name for c in gpu_components]}")
    
    # Show capabilities matrix
    matrix = registry.get_capabilities_matrix()
    print("\nCapabilities Matrix:")
    for comp_name, capabilities in matrix.items():
        print(f"  {comp_name}: {sum(1 for v in capabilities.values() if v)} capabilities")
    
    print()


# Demo 2: Repository Analysis
def demo_repo_analysis():
    """Demonstrate repository analysis."""
    print("=== Repository Analysis Demo ===")
    
    analyzer = CodeAnalyzer()
    
    # Create sample code file for analysis
    sample_code = '''
import numpy as np
from typing import List, Optional

class DataProcessor:
    """Processes data for machine learning."""
    
    def __init__(self, config: dict):
        self.config = config
        self.processed_count = 0
    
    def process(self, data: List[str]) -> np.ndarray:
        """Process input data and return processed array."""
        results = []
        for item in data:
            if item.strip():
                results.append(len(item))
            self.processed_count += 1
        return np.array(results)
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {"processed": self.processed_count}

def main():
    processor = DataProcessor({"batch_size": 32})
    data = ["hello", "world", "test"]
    result = processor.process(data)
    print(result)

if __name__ == "__main__":
    main()
'''
    
    # Write sample file and analyze
    sample_file = Path("/tmp/sample_code.py")
    sample_file.write_text(sample_code)
    
    file_info = analyzer.analyze_file(str(sample_file))
    
    print(f"File: {file_info.path}")
    print(f"Lines of code: {file_info.lines_of_code}")
    print(f"Functions: {len(file_info.functions)}")
    print(f"Classes: {len(file_info.classes)}")
    print(f"Imports: {len(file_info.imports)}")
    print(f"Complexity score: {file_info.complexity_score}")
    
    # Show function details
    for func in file_info.functions:
        print(f"  Function: {func.name}, args: {func.args}, complexity: {func.complexity}")
    
    # Show class details
    for cls in file_info.classes:
        print(f"  Class: {cls.name}, methods: {len(cls.methods)}")
    
    print()


# Demo 3: Multi-Agent System
async def demo_multi_agent():
    """Demonstrate multi-agent coordination."""
    print("=== Multi-Agent System Demo ===")
    
    # Create message bus
    message_bus = MessageBus()
    
    # Create specialized agents
    code_agent = SpecializedAgent("code_analyzer", name="CodeAnalyzer", message_bus=message_bus)
    test_agent = SpecializedAgent("test_generator", name="TestGenerator", message_bus=message_bus)
    
    # Create tasks
    analyze_task = Task(
        id="analyze_1",
        description="Analyze code structure and quality",
        required_capabilities={"analyze_code", "detect_patterns"}
    )
    
    test_task = Task(
        id="test_1", 
        description="Generate tests for analyzed code",
        required_capabilities={"generate_tests"}
    )
    
    # Process tasks
    result1 = await code_agent.process_task(analyze_task)
    result2 = await test_agent.process_task(test_task)
    
    print(f"Code analysis result: {result1.result}")
    print(f"Test generation result: {result2.result}")
    
    # Show agent metrics
    print(f"Code agent metrics: {code_agent.metrics.tasks_completed} tasks completed")
    print(f"Test agent metrics: {test_agent.metrics.tasks_completed} tasks completed")
    
    print()


# Demo 4: DAG Execution
async def demo_dag_execution():
    """Demonstrate DAG-based execution."""
    print("=== DAG Execution Demo ===")
    
    # Create function nodes
    @node("data_loader", parameters={"source": "file"})
    def load_data(source: str) -> dict:
        return {"data": f"loaded from {source}", "count": 100}
    
    @node("data_processor")
    def process_data(data: dict) -> dict:
        return {"processed_data": f"processed {data}", "status": "complete"}
    
    @node("data_saver", parameters={"destination": "output.json"})
    def save_data(processed_data: dict, destination: str) -> dict:
        return {"saved_to": destination, "success": True}
    
    # Create DAG
    dag = DAG("demo_pipeline")
    dag.add_node(load_data)
    dag.add_node(process_data)
    dag.add_node(save_data)
    
    # Add dependencies
    dag.add_edge("data_loader", "data_processor")
    dag.add_edge("data_processor", "data_saver")
    
    # Execute DAG
    context = ExecutionContext("run_1", execution_time=0.0)
    results = await dag.execute(context)
    
    print(f"DAG execution completed: {len(results)} nodes executed")
    for node_id, result in results.items():
        print(f"  {node_id}: {result.state.value} - {result.outputs}")
    
    print()


# Demo 5: Feature Extraction
def demo_feature_extraction():
    """Demonstrate feature extraction."""
    print("=== Feature Extraction Demo ===")
    
    # Text feature extraction
    text_extractor = TextFeatureExtractor()
    sample_text = "Hello world! This is a test email: test@example.com. Visit https://example.com"
    text_features = text_extractor.extract(sample_text)
    
    print(f"Text features extracted: {len(text_features.features)}")
    for feature in text_features.features[:5]:  # Show first 5
        print(f"  {feature.name}: {feature.value} ({feature.feature_type})")
    
    # Code feature extraction
    code_extractor = CodeFeatureExtractor()
    sample_code = '''
def hello_world():
    """Print hello world."""
    print("Hello, World!")
    if True:
        for i in range(3):
            print(f"Count: {i}")

class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"
'''
    code_features = code_extractor.extract(sample_code)
    
    print(f"\nCode features extracted: {len(code_features.features)}")
    for feature in code_features.features:
        print(f"  {feature.name}: {feature.value} ({feature.feature_type})")
    
    print()


# Demo 6: ML Configuration
def demo_ml_config():
    """Demonstrate ML configuration system."""
    print("=== ML Configuration Demo ===")
    
    # Create configuration manager
    config_manager = ConfigManager("/tmp/configs")
    
    # Create experiment from template
    config = config_manager.create_from_template(
        "text_classification",
        "sentiment_analysis_experiment",
        **{
            "model.hidden_size": 256,
            "training.num_epochs": 3,
            "data.batch_size": 16
        }
    )
    
    print(f"Experiment: {config.name}")
    print(f"Model architecture: {config.model.architecture}")
    print(f"Hidden size: {config.model.hidden_size}")
    print(f"Training epochs: {config.training.num_epochs}")
    print(f"Batch size: {config.data.batch_size}")
    
    # Validate configuration
    errors = config.validate()
    print(f"Validation errors: {len(errors)}")
    
    # Save configuration
    config_path = config_manager.save_config(config)
    print(f"Config saved to: {config_path}")
    
    print()


# Demo 7: NLP Capabilities
def demo_nlp_capabilities():
    """Demonstrate NLP capability system."""
    print("=== NLP Capabilities Demo ===")
    
    # Create document
    doc = Document(
        text="Apple Inc. is a great technology company. I love their products! Contact: info@apple.com",
        language="en"
    )
    
    # Apply capabilities in pipeline
    capabilities = ["tokenizer", "sentence_splitter", "ner", "sentiment_analysis"]
    
    for cap_name in capabilities:
        capability = get_capability(cap_name)
        if capability and capability.can_process(doc):
            doc = capability.process(doc)
            print(f"Applied {cap_name}: {list(doc.annotations.keys())}")
    
    # Show results  
    print(f"\nDocument annotations:")
    for name, annotation in doc.annotations.items():
        if isinstance(annotation, list) and len(annotation) > 3:
            print(f"  {name}: {annotation[:3]}... ({len(annotation)} items)")
        else:
            print(f"  {name}: {annotation}")
    
    print()


# Demo 8: Interface Patterns
def demo_interface_patterns():
    """Demonstrate interface patterns."""
    print("=== Interface Patterns Demo ===")
    
    # Create mock model implementation
    class MockClassifier(ClassificationModel):
        def __init__(self):
            super().__init__({"num_classes": 3, "class_names": ["positive", "negative", "neutral"]})
            self.parameters = {"weights": [0.1, 0.2, 0.3], "bias": 0.1}
        
        def forward(self, inputs: BatchInput) -> ModelOutput:
            # Mock forward pass
            predictions = [[0.7, 0.2, 0.1], [0.1, 0.8, 0.1]]  # Mock predictions
            return ModelOutput(predictions=predictions)
        
        def predict_proba(self, inputs: BatchInput) -> list:
            output = self.forward(inputs)
            return output.predictions
        
        def get_parameters(self) -> dict:
            return self.parameters
        
        def set_parameters(self, parameters: dict) -> None:
            self.parameters = parameters
    
    # Test the model
    model = MockClassifier()
    
    # Create batch input
    batch = BatchInput(data=["This is great!", "This is terrible!"])
    
    # Get predictions
    predictions = model.predict_proba(batch)
    classes = model.predict_classes(batch)
    
    print(f"Model predictions: {predictions}")
    print(f"Predicted classes: {classes}")
    print(f"Class names: {model.class_names}")
    
    # Test save/load
    model.save_pretrained("/tmp/mock_model")
    loaded_model = MockClassifier.from_pretrained("/tmp/mock_model")
    print(f"Model loaded successfully: {loaded_model.get_parameters()}")
    
    print()


# Main demonstration
async def main():
    """Run all demonstrations."""
    print("🚀 Repo Graph Planning Project - Comprehensive Demo\n")
    
    demo_ontology_mapping()
    demo_repo_analysis()
    await demo_multi_agent()
    await demo_dag_execution()
    demo_feature_extraction()
    demo_ml_config()
    demo_nlp_capabilities()
    demo_interface_patterns()
    
    print("✨ All demos completed successfully!")
    print("\nThis demonstrates the core patterns from:")
    print("- scikit-learn/_tags.py (ontology mapping)")
    print("- OpenHands (repo synthesis)")
    print("- AutoGPT (multi-agent loops)")
    print("- Dagster (DAG execution)")
    print("- HuggingFace TRL (ML orchestration)")
    print("- Feature extraction & vectorization")
    print("- spaCy (NLP capabilities)")
    print("- HF/Transformers (interface patterns)")
    print("- pytest/pluggy (test plugins)")


if __name__ == "__main__":
    asyncio.run(main())