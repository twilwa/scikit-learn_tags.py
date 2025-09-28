"""
Feature extraction pipelines.
"""

from typing import List, Any
from .extractors import BaseExtractor, FeatureSet
from .vectorizers import FeatureVectorizer
import numpy as np


class FeaturePipeline:
    """Pipeline for feature extraction and vectorization."""
    
    def __init__(self, extractors: List[BaseExtractor], vectorizer: FeatureVectorizer = None):
        self.extractors = extractors
        self.vectorizer = vectorizer or FeatureVectorizer()
        self.is_fitted = False
    
    def fit(self, data: List[Any]) -> None:
        """Fit the pipeline."""
        feature_sets = []
        for item in data:
            fs = self._extract_features(item)
            feature_sets.append(fs)
        
        self.vectorizer.fit(feature_sets)
        self.is_fitted = True
    
    def transform(self, data: List[Any]) -> np.ndarray:
        """Transform data to vectors."""
        if not self.is_fitted:
            raise ValueError("Pipeline must be fitted first")
        
        feature_sets = []
        for item in data:
            fs = self._extract_features(item)
            feature_sets.append(fs)
        
        return self.vectorizer.transform(feature_sets)
    
    def _extract_features(self, data: Any) -> FeatureSet:
        """Extract features using all extractors."""
        combined_fs = FeatureSet(input_id=str(hash(str(data)))[:8])
        
        for extractor in self.extractors:
            try:
                fs = extractor.extract(data)
                combined_fs.features.extend(fs.features)
            except Exception as e:
                print(f"Error in {extractor.name}: {e}")
        
        return combined_fs