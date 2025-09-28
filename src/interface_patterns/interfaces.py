"""
Abstract interfaces for models and components.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple, Iterator
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ModelOutput:
    """Base class for model outputs."""
    predictions: Any
    hidden_states: Optional[Any] = None
    attentions: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingOutput:
    """Output from training operations."""
    loss: float
    metrics: Dict[str, float] = field(default_factory=dict)
    model_state: Optional[Any] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class BatchInput:
    """Represents a batch of inputs for processing."""
    data: Any
    labels: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        """Get batch size."""
        if hasattr(self.data, '__len__'):
            return len(self.data)
        elif hasattr(self.data, 'shape'):
            return self.data.shape[0]
        return 1


class BaseModel(ABC):
    """Abstract base class for all models."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.is_trained = False
        self.metadata = {}
    
    @abstractmethod
    def forward(self, inputs: BatchInput) -> ModelOutput:
        """Forward pass through the model."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get model parameters."""
        pass
    
    @abstractmethod
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set model parameters."""
        pass
    
    def predict(self, inputs: BatchInput) -> ModelOutput:
        """Make predictions on inputs."""
        return self.forward(inputs)
    
    def get_config(self) -> Dict[str, Any]:
        """Get model configuration."""
        return self.config.copy()
    
    def save_pretrained(self, path: str) -> None:
        """Save model to path."""
        import json
        from pathlib import Path
        
        path = Path(path)
        path.mkdir(exist_ok=True)
        
        # Save config
        with open(path / "config.json", "w") as f:
            json.dump(self.config, f, indent=2)
        
        # Save parameters (mock implementation)
        parameters = self.get_parameters()
        with open(path / "parameters.json", "w") as f:
            json.dump(parameters, f, indent=2)
    
    @classmethod
    def from_pretrained(cls, path: str) -> 'BaseModel':
        """Load model from path."""
        import json
        from pathlib import Path
        
        path = Path(path)
        
        # Load config
        with open(path / "config.json", "r") as f:
            config = json.load(f)
        
        # Create model instance
        model = cls(config)
        
        # Load parameters
        with open(path / "parameters.json", "r") as f:
            parameters = json.load(f)
        model.set_parameters(parameters)
        
        return model


class Trainable(ABC):
    """Interface for trainable models."""
    
    @abstractmethod
    def train_step(self, batch: BatchInput) -> TrainingOutput:
        """Perform a single training step."""
        pass
    
    @abstractmethod
    def eval_step(self, batch: BatchInput) -> TrainingOutput:
        """Perform a single evaluation step."""
        pass
    
    def train(self, train_data: Iterator[BatchInput], 
              val_data: Optional[Iterator[BatchInput]] = None,
              epochs: int = 1,
              **kwargs) -> List[TrainingOutput]:
        """Train the model."""
        history = []
        
        for epoch in range(epochs):
            epoch_losses = []
            
            # Training loop
            for batch in train_data:
                output = self.train_step(batch)
                epoch_losses.append(output.loss)
            
            # Validation loop
            val_loss = None
            if val_data:
                val_losses = []
                for batch in val_data:
                    output = self.eval_step(batch)
                    val_losses.append(output.loss)
                val_loss = np.mean(val_losses)
            
            # Record epoch results
            epoch_output = TrainingOutput(
                loss=np.mean(epoch_losses),
                metrics={"val_loss": val_loss} if val_loss else {},
                logs=[f"Epoch {epoch + 1}/{epochs}: loss={np.mean(epoch_losses):.4f}"]
            )
            history.append(epoch_output)
        
        self.is_trained = True
        return history


class TextModel(BaseModel):
    """Abstract base class for text processing models."""
    
    @abstractmethod
    def tokenize(self, text: Union[str, List[str]]) -> Dict[str, Any]:
        """Tokenize input text."""
        pass
    
    @abstractmethod
    def encode(self, text: Union[str, List[str]]) -> np.ndarray:
        """Encode text to embeddings."""
        pass


class ClassificationModel(BaseModel):
    """Abstract base class for classification models."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.num_classes = config.get("num_classes", 2) if config else 2
        self.class_names = config.get("class_names", []) if config else []
    
    @abstractmethod
    def predict_proba(self, inputs: BatchInput) -> np.ndarray:
        """Predict class probabilities."""
        pass
    
    def predict_classes(self, inputs: BatchInput) -> List[int]:
        """Predict class labels."""
        probabilities = self.predict_proba(inputs)
        return np.argmax(probabilities, axis=1).tolist()


class GenerativeModel(BaseModel):
    """Abstract base class for generative models."""
    
    @abstractmethod
    def generate(self, 
                 prompt: Union[str, BatchInput],
                 max_length: int = 100,
                 temperature: float = 1.0,
                 **kwargs) -> Union[str, List[str]]:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def get_generation_config(self) -> Dict[str, Any]:
        """Get generation configuration."""
        pass


class Processor(ABC):
    """Abstract base class for data processors."""
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process input data."""
        pass
    
    @abstractmethod
    def inverse_process(self, data: Any) -> Any:
        """Inverse process (decode) data."""
        pass


class Tokenizer(Processor):
    """Abstract base class for tokenizers."""
    
    def __init__(self, vocab_size: int = 30000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.special_tokens = {
            "pad_token": "[PAD]",
            "unk_token": "[UNK]",
            "cls_token": "[CLS]",
            "sep_token": "[SEP]",
            "mask_token": "[MASK]"
        }
    
    @abstractmethod
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into tokens."""
        pass
    
    @abstractmethod
    def encode(self, text: str, max_length: Optional[int] = None) -> Dict[str, Any]:
        """Encode text to token IDs."""
        pass
    
    @abstractmethod
    def decode(self, token_ids: List[int]) -> str:
        """Decode token IDs to text."""
        pass
    
    def batch_encode(self, texts: List[str], max_length: Optional[int] = None) -> Dict[str, Any]:
        """Encode multiple texts."""
        encoded_inputs = []
        for text in texts:
            encoded = self.encode(text, max_length)
            encoded_inputs.append(encoded)
        
        # Combine batch
        batch = {}
        for key in encoded_inputs[0].keys():
            batch[key] = [item[key] for item in encoded_inputs]
        
        return batch


class Pipeline(ABC):
    """Abstract base class for processing pipelines."""
    
    def __init__(self, model: BaseModel, processor: Optional[Processor] = None):
        self.model = model
        self.processor = processor
        self.components = []
    
    @abstractmethod
    def __call__(self, inputs: Any, **kwargs) -> Any:
        """Process inputs through the pipeline."""
        pass
    
    def add_component(self, component: Any, name: str) -> None:
        """Add a component to the pipeline."""
        self.components.append((name, component))
    
    def remove_component(self, name: str) -> None:
        """Remove a component from the pipeline."""
        self.components = [(n, c) for n, c in self.components if n != name]


class MetricInterface(ABC):
    """Interface for evaluation metrics."""
    
    @abstractmethod
    def compute(self, predictions: Any, references: Any) -> Dict[str, float]:
        """Compute metric scores."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get metric name."""
        pass


class CallbackInterface(ABC):
    """Interface for training callbacks."""
    
    def on_train_begin(self, model: BaseModel, **kwargs) -> None:
        """Called at the beginning of training."""
        pass
    
    def on_train_end(self, model: BaseModel, **kwargs) -> None:
        """Called at the end of training."""
        pass
    
    def on_epoch_begin(self, epoch: int, model: BaseModel, **kwargs) -> None:
        """Called at the beginning of each epoch."""
        pass
    
    def on_epoch_end(self, epoch: int, model: BaseModel, logs: Dict[str, float], **kwargs) -> None:
        """Called at the end of each epoch."""
        pass
    
    def on_batch_begin(self, batch: int, model: BaseModel, **kwargs) -> None:
        """Called at the beginning of each batch."""
        pass
    
    def on_batch_end(self, batch: int, model: BaseModel, logs: Dict[str, float], **kwargs) -> None:
        """Called at the end of each batch."""
        pass


class ConfigurableInterface(ABC):
    """Interface for configurable components."""
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get component configuration."""
        pass
    
    @abstractmethod
    def from_config(self, config: Dict[str, Any]) -> 'ConfigurableInterface':
        """Create component from configuration."""
        pass
    
    def update_config(self, **kwargs) -> None:
        """Update configuration parameters."""
        current_config = self.get_config()
        current_config.update(kwargs)
        # Subclasses should implement config application


class VersionedInterface(ABC):
    """Interface for versioned components."""
    
    @abstractmethod
    def get_version(self) -> str:
        """Get component version."""
        pass
    
    @abstractmethod
    def is_compatible(self, other_version: str) -> bool:
        """Check if compatible with another version."""
        pass


class CacheableInterface(ABC):
    """Interface for cacheable components."""
    
    @abstractmethod
    def get_cache_key(self, inputs: Any) -> str:
        """Get cache key for inputs."""
        pass
    
    @abstractmethod
    def cache_output(self, key: str, output: Any) -> None:
        """Cache output for key."""
        pass
    
    @abstractmethod
    def get_cached_output(self, key: str) -> Optional[Any]:
        """Get cached output for key."""
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear all cached outputs."""
        pass