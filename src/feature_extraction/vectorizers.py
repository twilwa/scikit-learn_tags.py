"""
Vectorizers for converting features to numerical representations.
"""

import numpy as np
from typing import Dict, List, Any, Optional
from .extractors import FeatureSet


class FeatureVectorizer:
    """Converts feature sets to numerical vectors."""
    
    def __init__(self):
        self.feature_vocab = {}
        self.is_fitted = False
    
    def fit(self, feature_sets: List[FeatureSet]) -> None:
        """Fit vectorizer to feature sets."""
        all_features = set()
        for fs in feature_sets:
            for feature in fs.features:
                if feature.feature_type == "numeric":
                    all_features.add(feature.name)
        
        self.feature_vocab = {name: i for i, name in enumerate(sorted(all_features))}
        self.is_fitted = True
    
    def transform(self, feature_sets: List[FeatureSet]) -> np.ndarray:
        """Transform feature sets to vectors."""
        if not self.is_fitted:
            raise ValueError("Vectorizer must be fitted first")
        
        vectors = []
        for fs in feature_sets:
            vector = np.zeros(len(self.feature_vocab))
            for feature in fs.features:
                if feature.name in self.feature_vocab and feature.feature_type == "numeric":
                    idx = self.feature_vocab[feature.name]
                    vector[idx] = float(feature.value)
            vectors.append(vector)
        
        return np.array(vectors)