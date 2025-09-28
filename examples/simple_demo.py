"""
Simple demonstration of core repo graph planning components.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import core components (avoiding heavy dependencies)
from ontology_mapping.tags import create_component_tags, TagType
from ontology_mapping.registry import ComponentRegistry, register_component

from feature_extraction.extractors import TextFeatureExtractor, CodeFeatureExtractor

from nlp_capabilities.capabilities import get_capability, Document


def main():
    """Run core demonstrations."""
    print("🚀 Repo Graph Planning Project - Simple Demo\n")
    
    # Demo 1: Ontology Mapping
    print("=== Ontology Mapping System ===")
    
    @register_component(
        "simple_processor",
        description="A simple text processor",
        supports_streaming=True,
        complexity="O(n)",
        input_types=["text"]
    )
    class SimpleProcessor:
        def process(self, text):
            return f"Processed: {text}"
    
    from ontology_mapping.registry import get_component_registry
    registry = get_component_registry()
    
    print(f"Registered components: {len(registry.list_all())}")
    streaming_components = registry.find_by_capability("supports_streaming", True)
    print(f"Streaming components: {[c.name for c in streaming_components]}")
    print()
    
    # Demo 2: Feature Extraction
    print("=== Feature Extraction ===")
    
    text_extractor = TextFeatureExtractor()
    sample_text = "Hello world! Visit https://example.com or email test@example.com"
    features = text_extractor.extract(sample_text)
    
    print(f"Extracted {len(features.features)} features:")
    for feature in features.features[:5]:
        print(f"  {feature.name}: {feature.value}")
    print()
    
    # Demo 3: Code Analysis
    print("=== Code Feature Extraction ===")
    
    code_extractor = CodeFeatureExtractor()
    sample_code = '''
def hello():
    """Say hello."""
    print("Hello, World!")
    for i in range(3):
        print(f"Count: {i}")

class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"
'''
    
    code_features = code_extractor.extract(sample_code)
    print(f"Code features extracted: {len(code_features.features)}")
    for feature in code_features.features:
        print(f"  {feature.name}: {feature.value}")
    print()
    
    # Demo 4: NLP Capabilities
    print("=== NLP Capabilities ===")
    
    doc = Document(text="Apple Inc. is great! I love their products.")
    
    # Apply basic capabilities
    tokenizer = get_capability("tokenizer")
    sentiment = get_capability("sentiment_analysis")
    
    if tokenizer:
        doc = tokenizer.process(doc)
        print(f"Tokens: {doc.get_annotation('tokens')}")
    
    if sentiment:
        doc = sentiment.process(doc)
        print(f"Sentiment: {doc.get_annotation('sentiment')}")
    
    print()
    
    # Demo 5: Component Tags
    print("=== Component Tags System ===")
    
    tags = create_component_tags(
        "demo_component",
        supports_streaming=True,
        requires_gpu=False,
        complexity="O(n)",
        memory_intensive=False
    )
    
    print(f"Component: {tags.component_name}")
    print(f"Tags: {dict(tags.tags)}")
    print(f"Supports streaming: {tags.get_tag('supports_streaming')}")
    print(f"GPU required: {tags.get_tag('requires_gpu')}")
    print()
    
    print("✨ Simple demo completed successfully!")
    print("\nThis demonstrates core patterns from:")
    print("- scikit-learn/_tags.py (ontology mapping)")
    print("- Feature extraction & vectorization")
    print("- spaCy (NLP capabilities)")
    print("- Component registry and discovery")


if __name__ == "__main__":
    main()