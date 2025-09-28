"""
Core NLP capabilities and component definitions.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import uuid


class CapabilityLevel(Enum):
    """Hierarchical levels of NLP capabilities."""
    CORE = "core"           # Basic text processing
    LINGUISTIC = "linguistic"   # Language-specific analysis
    SEMANTIC = "semantic"   # Meaning and understanding
    PRAGMATIC = "pragmatic" # Context and usage
    DOMAIN = "domain"       # Domain-specific capabilities


class ProcessingStage(Enum):
    """Stages in the NLP pipeline."""
    PREPROCESSING = "preprocessing"
    TOKENIZATION = "tokenization"
    ANALYSIS = "analysis"
    ANNOTATION = "annotation"
    POSTPROCESSING = "postprocessing"


@dataclass
class CapabilityMetadata:
    """Metadata for NLP capabilities."""
    name: str
    description: str
    level: CapabilityLevel
    stage: ProcessingStage
    languages: Set[str] = field(default_factory=lambda: {"en"})
    dependencies: Set[str] = field(default_factory=set)
    outputs: Set[str] = field(default_factory=set)
    quality_score: float = 1.0
    computational_cost: int = 1  # 1-10 scale
    memory_usage: int = 1       # 1-10 scale


@dataclass
class Document:
    """Represents a document with annotations."""
    text: str
    id: Optional[str] = None
    language: str = "en"
    annotations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]
    
    def add_annotation(self, capability_name: str, annotation: Any) -> None:
        """Add an annotation from a capability."""
        self.annotations[capability_name] = annotation
    
    def get_annotation(self, capability_name: str) -> Optional[Any]:
        """Get annotation from a specific capability."""
        return self.annotations.get(capability_name)
    
    def has_annotation(self, capability_name: str) -> bool:
        """Check if document has annotation from capability."""
        return capability_name in self.annotations


class BaseCapability(ABC):
    """Base class for all NLP capabilities."""
    
    def __init__(self, metadata: CapabilityMetadata):
        self.metadata = metadata
        self.is_loaded = False
        self.config = {}
        self._cache = {}
    
    @abstractmethod
    def process(self, doc: Document) -> Document:
        """Process a document and add annotations."""
        pass
    
    def can_process(self, doc: Document) -> bool:
        """Check if this capability can process the document."""
        return doc.language in self.metadata.languages
    
    def load(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Load the capability with optional configuration."""
        self.config = config or {}
        self.is_loaded = True
    
    def unload(self) -> None:
        """Unload the capability to free resources."""
        self.is_loaded = False
        self._cache.clear()
    
    def configure(self, **kwargs) -> None:
        """Configure capability parameters."""
        self.config.update(kwargs)
    
    def clear_cache(self) -> None:
        """Clear internal cache."""
        self._cache.clear()


# Core Level Capabilities

class TokenizerCapability(BaseCapability):
    """Tokenizes text into words/subwords."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="tokenizer",
            description="Splits text into tokens",
            level=CapabilityLevel.CORE,
            stage=ProcessingStage.TOKENIZATION,
            outputs={"tokens", "token_spans"}
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Tokenize the document text."""
        # Simple whitespace tokenization (in practice would use more sophisticated methods)
        tokens = doc.text.split()
        token_spans = []
        
        current_pos = 0
        for token in tokens:
            start = doc.text.find(token, current_pos)
            end = start + len(token)
            token_spans.append((start, end, token))
            current_pos = end
        
        doc.add_annotation("tokens", tokens)
        doc.add_annotation("token_spans", token_spans)
        return doc


class SentenceSplitterCapability(BaseCapability):
    """Splits text into sentences."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="sentence_splitter",
            description="Splits text into sentences",
            level=CapabilityLevel.CORE,
            stage=ProcessingStage.TOKENIZATION,
            outputs={"sentences", "sentence_spans"}
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Split document into sentences."""
        # Simple sentence splitting (in practice would be more sophisticated)
        import re
        
        sentence_endings = re.compile(r'[.!?]+')
        sentences = sentence_endings.split(doc.text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate spans
        sentence_spans = []
        current_pos = 0
        for sentence in sentences:
            start = doc.text.find(sentence, current_pos)
            end = start + len(sentence)
            sentence_spans.append((start, end, sentence))
            current_pos = end
        
        doc.add_annotation("sentences", sentences)
        doc.add_annotation("sentence_spans", sentence_spans)
        return doc


# Linguistic Level Capabilities

class POSTaggerCapability(BaseCapability):
    """Part-of-speech tagging."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="pos_tagger",
            description="Tags parts of speech",
            level=CapabilityLevel.LINGUISTIC,
            stage=ProcessingStage.ANALYSIS,
            dependencies={"tokenizer"},
            outputs={"pos_tags"}
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Add POS tags to document."""
        tokens = doc.get_annotation("tokens")
        if not tokens:
            raise ValueError("POS tagger requires tokenization")
        
        # Mock POS tagging (in practice would use trained models)
        pos_tags = []
        for token in tokens:
            if token.lower() in ["the", "a", "an"]:
                pos_tags.append("DET")
            elif token.lower() in ["is", "are", "was", "were"]:
                pos_tags.append("VERB")
            elif token.isalpha():
                pos_tags.append("NOUN")
            else:
                pos_tags.append("PUNCT")
        
        doc.add_annotation("pos_tags", pos_tags)
        return doc


class NERCapability(BaseCapability):
    """Named Entity Recognition."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="ner",
            description="Identifies named entities",
            level=CapabilityLevel.LINGUISTIC,
            stage=ProcessingStage.ANALYSIS,
            dependencies={"tokenizer"},
            outputs={"entities"},
            computational_cost=3
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Extract named entities."""
        # Mock NER (in practice would use trained models)
        import re
        
        entities = []
        
        # Simple pattern-based entity extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, doc.text):
            entities.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "EMAIL"
            })
        
        # Mock person names (simple capitalized words)
        person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        for match in re.finditer(person_pattern, doc.text):
            entities.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "label": "PERSON"
            })
        
        doc.add_annotation("entities", entities)
        return doc


# Semantic Level Capabilities

class SentimentAnalysisCapability(BaseCapability):
    """Sentiment analysis capability."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="sentiment_analysis",
            description="Analyzes sentiment of text",
            level=CapabilityLevel.SEMANTIC,
            stage=ProcessingStage.ANALYSIS,
            outputs={"sentiment"},
            computational_cost=2
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Analyze sentiment of document."""
        # Mock sentiment analysis
        text = doc.text.lower()
        
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic"]
        negative_words = ["bad", "terrible", "awful", "horrible", "worst", "hate"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = {"label": "positive", "score": 0.8}
        elif negative_count > positive_count:
            sentiment = {"label": "negative", "score": 0.8}
        else:
            sentiment = {"label": "neutral", "score": 0.5}
        
        doc.add_annotation("sentiment", sentiment)
        return doc


class TopicModelingCapability(BaseCapability):
    """Topic modeling capability."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="topic_modeling",
            description="Identifies topics in text",
            level=CapabilityLevel.SEMANTIC,
            stage=ProcessingStage.ANALYSIS,
            outputs={"topics"},
            computational_cost=4,
            memory_usage=3
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Extract topics from document."""
        # Mock topic modeling
        text = doc.text.lower()
        
        topic_keywords = {
            "technology": ["computer", "software", "code", "programming", "tech", "digital"],
            "business": ["company", "market", "sales", "profit", "business", "customer"],
            "sports": ["game", "team", "player", "score", "match", "sport"],
            "health": ["health", "medical", "doctor", "patient", "treatment", "medicine"]
        }
        
        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                topic_scores[topic] = score / len(keywords)
        
        # Get top topic
        if topic_scores:
            top_topic = max(topic_scores, key=topic_scores.get)
            topics = [{"topic": top_topic, "score": topic_scores[top_topic]}]
        else:
            topics = [{"topic": "general", "score": 0.1}]
        
        doc.add_annotation("topics", topics)
        return doc


# Domain Level Capabilities

class CodeAnalysisCapability(BaseCapability):
    """Code-specific analysis capability."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="code_analysis",
            description="Analyzes source code",
            level=CapabilityLevel.DOMAIN,
            stage=ProcessingStage.ANALYSIS,
            outputs={"code_metrics", "functions", "classes"},
            computational_cost=3
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Analyze code in document."""
        text = doc.text
        
        # Basic code metrics
        lines = text.splitlines()
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        metrics = {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "blank_lines": len([line for line in lines if not line.strip()]),
            "comment_lines": len([line for line in lines if line.strip().startswith('#')])
        }
        
        # Extract functions and classes (simple pattern matching)
        import re
        
        functions = []
        for match in re.finditer(r'def\s+(\w+)\s*\(([^)]*)\):', text):
            functions.append({
                "name": match.group(1),
                "args": match.group(2),
                "line": text[:match.start()].count('\n') + 1
            })
        
        classes = []
        for match in re.finditer(r'class\s+(\w+)(?:\([^)]*\))?:', text):
            classes.append({
                "name": match.group(1),
                "line": text[:match.start()].count('\n') + 1
            })
        
        doc.add_annotation("code_metrics", metrics)
        doc.add_annotation("functions", functions)
        doc.add_annotation("classes", classes)
        return doc


class LegalTextCapability(BaseCapability):
    """Legal document analysis capability."""
    
    def __init__(self):
        metadata = CapabilityMetadata(
            name="legal_analysis",
            description="Analyzes legal documents",
            level=CapabilityLevel.DOMAIN,
            stage=ProcessingStage.ANALYSIS,
            outputs={"legal_entities", "clauses", "obligations"},
            computational_cost=4
        )
        super().__init__(metadata)
    
    def process(self, doc: Document) -> Document:
        """Analyze legal text."""
        text = doc.text
        
        # Extract legal entities (mock patterns)
        import re
        
        legal_entities = []
        
        # Contract parties
        party_pattern = r'Party\s+[A-Z]|(?:The\s+)?(?:Company|Corporation|LLC|Ltd\.?|Inc\.?)'
        for match in re.finditer(party_pattern, text):
            legal_entities.append({
                "text": match.group(),
                "type": "party",
                "start": match.start(),
                "end": match.end()
            })
        
        # Legal references
        ref_pattern = r'Section\s+\d+(?:\.\d+)*|Article\s+[IVX]+|\d+\s+U\.S\.C\.\s+§\s+\d+'
        for match in re.finditer(ref_pattern, text):
            legal_entities.append({
                "text": match.group(),
                "type": "reference",
                "start": match.start(),
                "end": match.end()
            })
        
        # Extract clauses (sentences with legal keywords)
        legal_keywords = ["shall", "must", "required", "obligated", "liable", "warranty", "indemnify"]
        clauses = []
        
        sentences = doc.get_annotation("sentences") or [text]
        for i, sentence in enumerate(sentences):
            if any(keyword in sentence.lower() for keyword in legal_keywords):
                clauses.append({
                    "text": sentence,
                    "index": i,
                    "type": "obligation" if any(word in sentence.lower() for word in ["shall", "must", "required"]) else "general"
                })
        
        doc.add_annotation("legal_entities", legal_entities)
        doc.add_annotation("clauses", clauses)
        return doc


# Registry of all available capabilities
CAPABILITY_REGISTRY = {
    "tokenizer": TokenizerCapability,
    "sentence_splitter": SentenceSplitterCapability,
    "pos_tagger": POSTaggerCapability,
    "ner": NERCapability,
    "sentiment_analysis": SentimentAnalysisCapability,
    "topic_modeling": TopicModelingCapability,
    "code_analysis": CodeAnalysisCapability,
    "legal_analysis": LegalTextCapability,
}


def get_capability(name: str) -> Optional[BaseCapability]:
    """Get a capability instance by name."""
    capability_class = CAPABILITY_REGISTRY.get(name)
    if capability_class:
        return capability_class()
    return None


def list_capabilities() -> List[str]:
    """List all available capability names."""
    return list(CAPABILITY_REGISTRY.keys())


def get_capabilities_by_level(level: CapabilityLevel) -> List[str]:
    """Get capabilities filtered by level."""
    capabilities = []
    for name, capability_class in CAPABILITY_REGISTRY.items():
        instance = capability_class()
        if instance.metadata.level == level:
            capabilities.append(name)
    return capabilities