"""
Configuration system for ML training workflows.
"""

import yaml
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum


class OptimizationType(Enum):
    """Types of optimization objectives."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class SchedulerType(Enum):
    """Types of learning rate schedulers."""
    LINEAR = "linear"
    COSINE = "cosine"
    EXPONENTIAL = "exponential"
    STEP = "step"
    PLATEAU = "plateau"


@dataclass
class OptimizerConfig:
    """Configuration for optimizers."""
    name: str = "adam"
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    betas: tuple = (0.9, 0.999)
    eps: float = 1e-8
    amsgrad: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulerConfig:
    """Configuration for learning rate schedulers."""
    type: SchedulerType = SchedulerType.LINEAR
    warmup_steps: int = 0
    total_steps: Optional[int] = None
    num_cycles: int = 1
    step_size: int = 100
    gamma: float = 0.1
    patience: int = 10
    factor: float = 0.5
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass  
class DataConfig:
    """Configuration for data loading and processing."""
    train_path: Optional[str] = None
    validation_path: Optional[str] = None
    test_path: Optional[str] = None
    batch_size: int = 32
    num_workers: int = 4
    shuffle: bool = True
    drop_last: bool = False
    pin_memory: bool = True
    preprocessing: List[str] = field(default_factory=list)
    augmentations: List[str] = field(default_factory=list)
    max_length: Optional[int] = None
    tokenizer_name: Optional[str] = None
    format: str = "json"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelConfig:
    """Configuration for model architecture and parameters."""
    name: str = "base_model"
    architecture: str = "transformer"
    pretrained_path: Optional[str] = None
    num_layers: int = 12
    hidden_size: int = 768
    num_attention_heads: int = 12
    intermediate_size: int = 3072
    dropout: float = 0.1
    activation: str = "gelu"
    max_position_embeddings: int = 512
    vocab_size: int = 30000
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingConfig:
    """Configuration for training parameters."""
    num_epochs: int = 10
    max_steps: Optional[int] = None
    eval_steps: int = 500
    save_steps: int = 1000
    logging_steps: int = 100
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    fp16: bool = False
    bf16: bool = False
    gradient_checkpointing: bool = False
    dataloader_drop_last: bool = False
    eval_accumulation_steps: Optional[int] = None
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CallbackConfig:
    """Configuration for training callbacks."""
    name: str
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Set default parameters based on callback type
        if self.name == "early_stopping" and not self.parameters:
            self.parameters = {
                "patience": 3,
                "min_delta": 0.001,
                "restore_best_weights": True
            }
        elif self.name == "model_checkpoint" and not self.parameters:
            self.parameters = {
                "save_best_only": True,
                "monitor": "val_loss",
                "mode": "min"
            }


@dataclass
class ExperimentConfig:
    """Complete configuration for an ML experiment."""
    name: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Component configurations
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    optimizer: OptimizerConfig = field(default_factory=OptimizerConfig)
    scheduler: Optional[SchedulerConfig] = None
    callbacks: List[CallbackConfig] = field(default_factory=list)
    
    # Infrastructure
    output_dir: str = "./outputs"
    logging_dir: Optional[str] = None
    seed: int = 42
    device: str = "auto"
    distributed: bool = False
    
    # Hyperparameter search
    hyperparameter_search: Optional[Dict[str, Any]] = None
    
    # Custom parameters
    custom_parameters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentConfig':
        """Create from dictionary."""
        # Handle nested dataclass conversion
        if 'model' in data and isinstance(data['model'], dict):
            data['model'] = ModelConfig(**data['model'])
        if 'data' in data and isinstance(data['data'], dict):
            data['data'] = DataConfig(**data['data'])
        if 'training' in data and isinstance(data['training'], dict):
            data['training'] = TrainingConfig(**data['training'])
        if 'optimizer' in data and isinstance(data['optimizer'], dict):
            data['optimizer'] = OptimizerConfig(**data['optimizer'])
        if 'scheduler' in data and isinstance(data['scheduler'], dict):
            data['scheduler'] = SchedulerConfig(**data['scheduler'])
        if 'callbacks' in data and isinstance(data['callbacks'], list):
            data['callbacks'] = [
                CallbackConfig(**cb) if isinstance(cb, dict) else cb 
                for cb in data['callbacks']
            ]
        
        return cls(**data)
    
    def save(self, path: Union[str, Path]) -> None:
        """Save configuration to file."""
        path = Path(path)
        config_dict = self.to_dict()
        
        if path.suffix == '.yaml' or path.suffix == '.yml':
            with open(path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        elif path.suffix == '.json':
            with open(path, 'w') as f:
                json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    @classmethod
    def load(cls, path: Union[str, Path]) -> 'ExperimentConfig':
        """Load configuration from file."""
        path = Path(path)
        
        if path.suffix in ['.yaml', '.yml']:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        elif path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        return cls.from_dict(data)
    
    def override(self, **kwargs) -> 'ExperimentConfig':
        """Create a new config with overridden parameters."""
        config_dict = self.to_dict()
        
        # Handle nested parameter overrides
        for key, value in kwargs.items():
            if '.' in key:
                # Handle nested keys like "model.hidden_size"
                parts = key.split('.')
                current = config_dict
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                config_dict[key] = value
        
        return self.from_dict(config_dict)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate required fields
        if not self.name:
            errors.append("Experiment name is required")
        
        # Validate data configuration
        if not self.data.train_path:
            errors.append("Training data path is required")
        
        if self.data.batch_size <= 0:
            errors.append("Batch size must be positive")
        
        # Validate model configuration
        if self.model.hidden_size <= 0:
            errors.append("Model hidden size must be positive")
        
        if self.model.num_layers <= 0:
            errors.append("Number of model layers must be positive")
        
        # Validate training configuration
        if self.training.num_epochs <= 0 and not self.training.max_steps:
            errors.append("Either num_epochs or max_steps must be positive")
        
        if self.training.gradient_accumulation_steps <= 0:
            errors.append("Gradient accumulation steps must be positive")
        
        # Validate optimizer configuration
        if self.optimizer.learning_rate <= 0:
            errors.append("Learning rate must be positive")
        
        return errors


class ConfigManager:
    """Manages experiment configurations and templates."""
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._templates = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load configuration templates."""
        self._templates = {
            "text_classification": ExperimentConfig(
                name="text_classification_template",
                description="Template for text classification tasks",
                model=ModelConfig(
                    architecture="transformer",
                    num_layers=6,
                    hidden_size=512,
                    num_attention_heads=8
                ),
                data=DataConfig(
                    batch_size=32,
                    max_length=128,
                    preprocessing=["tokenize", "truncate"]
                ),
                training=TrainingConfig(
                    num_epochs=5,
                    eval_steps=100,
                    save_steps=500
                ),
                callbacks=[
                    CallbackConfig("early_stopping"),
                    CallbackConfig("model_checkpoint")
                ]
            ),
            
            "language_modeling": ExperimentConfig(
                name="language_modeling_template",
                description="Template for language modeling tasks",
                model=ModelConfig(
                    architecture="gpt",
                    num_layers=12,
                    hidden_size=768,
                    num_attention_heads=12
                ),
                data=DataConfig(
                    batch_size=16,
                    max_length=512,
                    preprocessing=["tokenize"]
                ),
                training=TrainingConfig(
                    num_epochs=10,
                    gradient_accumulation_steps=4,
                    eval_steps=500
                ),
                optimizer=OptimizerConfig(
                    learning_rate=5e-5,
                    weight_decay=0.01
                )
            ),
            
            "fine_tuning": ExperimentConfig(
                name="fine_tuning_template", 
                description="Template for fine-tuning pre-trained models",
                model=ModelConfig(
                    pretrained_path="bert-base-uncased"
                ),
                data=DataConfig(
                    batch_size=16,
                    max_length=256
                ),
                training=TrainingConfig(
                    num_epochs=3,
                    eval_steps=100
                ),
                optimizer=OptimizerConfig(
                    learning_rate=2e-5
                ),
                scheduler=SchedulerConfig(
                    type=SchedulerType.LINEAR,
                    warmup_steps=100
                )
            )
        }
    
    def get_template(self, template_name: str) -> Optional[ExperimentConfig]:
        """Get a configuration template."""
        return self._templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List available templates."""
        return list(self._templates.keys())
    
    def create_from_template(self, template_name: str, experiment_name: str, **overrides) -> ExperimentConfig:
        """Create a new configuration from a template."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        config = template.override(name=experiment_name, **overrides)
        return config
    
    def save_config(self, config: ExperimentConfig, filename: Optional[str] = None) -> Path:
        """Save configuration to the config directory."""
        if not filename:
            filename = f"{config.name}.yaml"
        
        filepath = self.config_dir / filename
        config.save(filepath)
        return filepath
    
    def load_config(self, filename: str) -> ExperimentConfig:
        """Load configuration from the config directory."""
        filepath = self.config_dir / filename
        return ExperimentConfig.load(filepath)
    
    def list_configs(self) -> List[str]:
        """List saved configurations."""
        configs = []
        for file_path in self.config_dir.glob("*.yaml"):
            configs.append(file_path.name)
        for file_path in self.config_dir.glob("*.json"):
            configs.append(file_path.name)
        return configs