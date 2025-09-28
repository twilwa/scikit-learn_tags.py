"""
Feature extractors for different data types and modalities.
"""

import re
import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class Feature:
    """Represents a single extracted feature."""
    name: str
    value: Union[float, int, str, List, np.ndarray]
    feature_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "value": self.value.tolist() if isinstance(self.value, np.ndarray) else self.value,
            "feature_type": self.feature_type,
            "metadata": self.metadata
        }


@dataclass
class FeatureSet:
    """Collection of features extracted from a single input."""
    input_id: str
    features: List[Feature] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_feature(self, feature: Feature) -> None:
        """Add a feature to this set."""
        self.features.append(feature)
    
    def get_feature(self, name: str) -> Optional[Feature]:
        """Get feature by name."""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None
    
    def get_features_by_type(self, feature_type: str) -> List[Feature]:
        """Get all features of a specific type."""
        return [f for f in self.features if f.feature_type == feature_type]
    
    def to_vector(self) -> np.ndarray:
        """Convert to a single feature vector."""
        vectors = []
        for feature in self.features:
            if isinstance(feature.value, (int, float)):
                vectors.append([feature.value])
            elif isinstance(feature.value, list):
                vectors.append(feature.value)
            elif isinstance(feature.value, np.ndarray):
                vectors.append(feature.value.flatten())
        
        if vectors:
            return np.concatenate(vectors)
        return np.array([])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "input_id": self.input_id,
            "features": [f.to_dict() for f in self.features],
            "metadata": self.metadata
        }


class BaseExtractor(ABC):
    """Base class for all feature extractors."""
    
    def __init__(self, name: str):
        self.name = name
        self.metadata = {}
    
    @abstractmethod
    def extract(self, input_data: Any) -> FeatureSet:
        """Extract features from input data."""
        pass
    
    def configure(self, **kwargs) -> None:
        """Configure the extractor with parameters."""
        self.metadata.update(kwargs)


class TextFeatureExtractor(BaseExtractor):
    """Extract features from text data."""
    
    def __init__(self, name: str = "text_extractor"):
        super().__init__(name)
        self.patterns = {
            "urls": re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            "emails": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "mentions": re.compile(r'@\w+'),
            "hashtags": re.compile(r'#\w+'),
            "numbers": re.compile(r'\d+\.?\d*'),
        }
    
    def extract(self, text: str) -> FeatureSet:
        """Extract features from text."""
        feature_set = FeatureSet(input_id=str(hash(text))[:8])
        
        # Basic text statistics
        feature_set.add_feature(Feature("length", len(text), "numeric"))
        feature_set.add_feature(Feature("word_count", len(text.split()), "numeric"))
        feature_set.add_feature(Feature("sentence_count", len(text.split('.')), "numeric"))
        feature_set.add_feature(Feature("char_count", len([c for c in text if c.isalpha()]), "numeric"))
        
        # Pattern-based features
        for pattern_name, pattern in self.patterns.items():
            matches = pattern.findall(text)
            feature_set.add_feature(Feature(f"{pattern_name}_count", len(matches), "numeric"))
            if matches:
                feature_set.add_feature(Feature(f"{pattern_name}_list", matches, "categorical"))
        
        # Language-specific features
        feature_set.add_feature(Feature("avg_word_length", 
                                       np.mean([len(word) for word in text.split()]) if text.split() else 0, 
                                       "numeric"))
        
        # Character-level features
        uppercase_count = sum(1 for c in text if c.isupper())
        feature_set.add_feature(Feature("uppercase_ratio", 
                                       uppercase_count / len(text) if text else 0, 
                                       "numeric"))
        
        punctuation_count = sum(1 for c in text if c in '.,!?;:')
        feature_set.add_feature(Feature("punctuation_ratio", 
                                       punctuation_count / len(text) if text else 0, 
                                       "numeric"))
        
        return feature_set


class CodeFeatureExtractor(BaseExtractor):
    """Extract features from source code."""
    
    def __init__(self, name: str = "code_extractor"):
        super().__init__(name)
        self.language_keywords = {
            "python": ["def", "class", "import", "if", "for", "while", "try", "except", "with"],
            "javascript": ["function", "var", "let", "const", "if", "for", "while", "try", "catch"],
            "java": ["public", "private", "class", "interface", "if", "for", "while", "try", "catch"],
        }
    
    def extract(self, code: str) -> FeatureSet:
        """Extract features from source code."""
        feature_set = FeatureSet(input_id=str(hash(code))[:8])
        
        lines = code.splitlines()
        
        # Basic code metrics
        feature_set.add_feature(Feature("total_lines", len(lines), "numeric"))
        feature_set.add_feature(Feature("blank_lines", len([l for l in lines if not l.strip()]), "numeric"))
        feature_set.add_feature(Feature("comment_lines", len([l for l in lines if l.strip().startswith('#')]), "numeric"))
        feature_set.add_feature(Feature("code_lines", len([l for l in lines if l.strip() and not l.strip().startswith('#')]), "numeric"))
        
        # Complexity metrics
        complexity_indicators = ["if", "elif", "else", "for", "while", "try", "except", "with"]
        complexity_score = sum(code.lower().count(indicator) for indicator in complexity_indicators)
        feature_set.add_feature(Feature("complexity_score", complexity_score, "numeric"))
        
        # Language detection based on keywords
        for lang, keywords in self.language_keywords.items():
            keyword_count = sum(code.lower().count(keyword) for keyword in keywords)
            feature_set.add_feature(Feature(f"{lang}_keywords", keyword_count, "numeric"))
        
        # Code structure features
        feature_set.add_feature(Feature("function_count", code.count("def "), "numeric"))
        feature_set.add_feature(Feature("class_count", code.count("class "), "numeric"))
        feature_set.add_feature(Feature("import_count", code.count("import "), "numeric"))
        
        # Indentation analysis
        indentations = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
        if indentations:
            feature_set.add_feature(Feature("avg_indentation", np.mean(indentations), "numeric"))
            feature_set.add_feature(Feature("max_indentation", max(indentations), "numeric"))
        
        return feature_set


class ImageFeatureExtractor(BaseExtractor):
    """Extract features from image data (placeholder - would need PIL/OpenCV)."""
    
    def __init__(self, name: str = "image_extractor"):
        super().__init__(name)
    
    def extract(self, image_path: str) -> FeatureSet:
        """Extract features from image (mock implementation)."""
        feature_set = FeatureSet(input_id=str(hash(image_path))[:8])
        
        # Mock features - in real implementation would use image processing
        feature_set.add_feature(Feature("file_size", Path(image_path).stat().st_size if Path(image_path).exists() else 0, "numeric"))
        feature_set.add_feature(Feature("file_extension", Path(image_path).suffix, "categorical"))
        
        # Mock image properties (would extract from actual image)
        feature_set.add_feature(Feature("width", 800, "numeric"))  # Mock
        feature_set.add_feature(Feature("height", 600, "numeric"))  # Mock
        feature_set.add_feature(Feature("aspect_ratio", 800/600, "numeric"))  # Mock
        feature_set.add_feature(Feature("channels", 3, "numeric"))  # Mock
        
        return feature_set


class StructuredDataExtractor(BaseExtractor):
    """Extract features from structured data (JSON, CSV, etc.)."""
    
    def __init__(self, name: str = "structured_extractor"):
        super().__init__(name)
    
    def extract(self, data: Union[Dict, List, str]) -> FeatureSet:
        """Extract features from structured data."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                data = {"raw_string": data}
        
        feature_set = FeatureSet(input_id=str(hash(str(data)))[:8])
        
        if isinstance(data, dict):
            self._extract_dict_features(data, feature_set)
        elif isinstance(data, list):
            self._extract_list_features(data, feature_set)
        
        return feature_set
    
    def _extract_dict_features(self, data: Dict, feature_set: FeatureSet, prefix: str = "") -> None:
        """Extract features from dictionary."""
        feature_set.add_feature(Feature(f"{prefix}key_count", len(data), "numeric"))
        
        # Analyze value types
        type_counts = {}
        for value in data.values():
            value_type = type(value).__name__
            type_counts[value_type] = type_counts.get(value_type, 0) + 1
        
        for type_name, count in type_counts.items():
            feature_set.add_feature(Feature(f"{prefix}{type_name}_count", count, "numeric"))
        
        # Analyze nested structures
        nested_dicts = sum(1 for v in data.values() if isinstance(v, dict))
        nested_lists = sum(1 for v in data.values() if isinstance(v, list))
        
        feature_set.add_feature(Feature(f"{prefix}nested_dict_count", nested_dicts, "numeric"))
        feature_set.add_feature(Feature(f"{prefix}nested_list_count", nested_lists, "numeric"))
        
        # Extract key patterns
        key_lengths = [len(str(k)) for k in data.keys()]
        if key_lengths:
            feature_set.add_feature(Feature(f"{prefix}avg_key_length", np.mean(key_lengths), "numeric"))
    
    def _extract_list_features(self, data: List, feature_set: FeatureSet, prefix: str = "") -> None:
        """Extract features from list."""
        feature_set.add_feature(Feature(f"{prefix}list_length", len(data), "numeric"))
        
        if data:
            # Analyze element types
            type_counts = {}
            for item in data:
                item_type = type(item).__name__
                type_counts[item_type] = type_counts.get(item_type, 0) + 1
            
            for type_name, count in type_counts.items():
                feature_set.add_feature(Feature(f"{prefix}element_{type_name}_count", count, "numeric"))
            
            # Homogeneity
            unique_types = len(type_counts)
            feature_set.add_feature(Feature(f"{prefix}type_homogeneity", 1.0 / unique_types if unique_types > 0 else 1.0, "numeric"))


class CompositeExtractor(BaseExtractor):
    """Combines multiple extractors for comprehensive feature extraction."""
    
    def __init__(self, extractors: List[BaseExtractor], name: str = "composite_extractor"):
        super().__init__(name)
        self.extractors = extractors
    
    def extract(self, input_data: Any) -> FeatureSet:
        """Extract features using all configured extractors."""
        composite_set = FeatureSet(input_id=str(hash(str(input_data)))[:8])
        
        for extractor in self.extractors:
            try:
                extractor_features = extractor.extract(input_data)
                for feature in extractor_features.features:
                    # Prefix feature names with extractor name to avoid conflicts
                    prefixed_feature = Feature(
                        name=f"{extractor.name}_{feature.name}",
                        value=feature.value,
                        feature_type=feature.feature_type,
                        metadata=feature.metadata
                    )
                    composite_set.add_feature(prefixed_feature)
            except Exception as e:
                # Log error but continue with other extractors
                print(f"Error in {extractor.name}: {e}")
        
        return composite_set


def create_text_extractor() -> TextFeatureExtractor:
    """Create a configured text feature extractor."""
    return TextFeatureExtractor()


def create_code_extractor() -> CodeFeatureExtractor:
    """Create a configured code feature extractor."""
    return CodeFeatureExtractor()


def create_universal_extractor() -> CompositeExtractor:
    """Create a universal extractor that handles multiple data types."""
    extractors = [
        TextFeatureExtractor("text"),
        CodeFeatureExtractor("code"),
        StructuredDataExtractor("structured")
    ]
    return CompositeExtractor(extractors, "universal")