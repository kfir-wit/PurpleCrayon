"""
Generation model configuration and management.

This module manages text-to-image generation models using a JSON configuration file
that can be updated dynamically to add new models or modify existing ones.
"""

import json
import os
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests


class ModelProvider(Enum):
    """Available model providers."""
    GEMINI = "gemini"
    REPLICATE = "replicate"


@dataclass
class ModelConfig:
    """Configuration for a generation model."""
    name: str
    provider: ModelProvider
    model_id: str
    display_name: str
    description: str
    priority: int  # Lower number = higher priority
    enabled: bool = True
    cost_tier: str = "standard"  # free, standard, premium
    max_resolution: str = "1024x1024"
    supported_formats: List[str] = None
    api_documentation: str = ""
    api_key_env: str = ""
    capabilities: Dict[str, Any] = None
    parameters: Dict[str, str] = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["png", "jpg", "jpeg"]
        if self.capabilities is None:
            self.capabilities = {"text_to_image": True, "image_to_image": False}
        if self.parameters is None:
            self.parameters = {"prompt": "string"}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create ModelConfig from dictionary."""
        return cls(
            name=data["name"],
            provider=ModelProvider(data["provider"]),
            model_id=data["model_id"],
            display_name=data["display_name"],
            description=data["description"],
            priority=data["priority"],
            enabled=data.get("enabled", True),
            cost_tier=data.get("cost_tier", "standard"),
            max_resolution=data.get("max_resolution", "1024x1024"),
            supported_formats=data.get("supported_formats", ["png", "jpg", "jpeg"]),
            api_documentation=data.get("api_documentation", ""),
            api_key_env=data.get("api_key_env", ""),
            capabilities=data.get("capabilities", {"text_to_image": True, "image_to_image": False}),
            parameters=data.get("parameters", {"prompt": "string"})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ModelConfig to dictionary."""
        data = asdict(self)
        data["provider"] = self.provider.value
        return data


class ModelManager:
    """Manages text-to-image generation models and their selection."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize ModelManager with JSON configuration.
        
        Args:
            config_path: Path to models.json file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/models.json relative to this file
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config" / "models.json"
        
        self.config_path = Path(config_path)
        self.models: Dict[str, ModelConfig] = {}
        self.fallback_order: Dict[str, List[str]] = {}
        self.model_types: Dict[str, Dict[str, Any]] = {}
        self.last_updated: Optional[datetime] = None
        self.config_version: str = "1.0.0"
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load model configuration from JSON file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Load models
                self.models = {}
                for name, model_data in config_data.get("models", {}).items():
                    self.models[name] = ModelConfig.from_dict(model_data)
                
                # Load fallback order (can be dict or list for backward compatibility)
                fallback_data = config_data.get("fallback_order", [])
                if isinstance(fallback_data, dict):
                    self.fallback_order = fallback_data
                else:
                    # Convert old format to new format
                    self.fallback_order = {"text_to_image": fallback_data}
                
                # Load model types
                self.model_types = config_data.get("model_types", {})
                self.config_version = config_data.get("version", "1.0.0")
                
                # Parse last updated timestamp
                last_updated_str = config_data.get("last_updated")
                if last_updated_str:
                    self.last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
                
                print(f"✅ Loaded {len(self.models)} models from {self.config_path}")
            else:
                print(f"⚠️ Config file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create default configuration if none exists."""
        self.models = {}
        self.fallback_order = []
        print("⚠️ Using empty model configuration")
    
    def _save_config(self) -> None:
        """Save current configuration to JSON file."""
        try:
            config_data = {
                "version": self.config_version,
                "last_updated": datetime.now().isoformat() + "Z",
                "models": {name: model.to_dict() for name, model in self.models.items()},
                "fallback_order": self.fallback_order,
                "update_check": {
                    "enabled": True,
                    "check_interval_hours": 24,
                    "remote_url": "https://raw.githubusercontent.com/kfir-wit/PurpleCrayon/main/purplecrayon/config/models.json"
                }
            }
            
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Saved configuration to {self.config_path}")
        except Exception as e:
            print(f"❌ Error saving config: {e}")
    
    def check_for_updates(self, force: bool = False) -> bool:
        """Check for model configuration updates.
        
        Args:
            force: If True, check for updates even if recently checked
            
        Returns:
            True if updates were found and applied, False otherwise
        """
        try:
            # Check if we should update
            if not force and self.last_updated:
                time_since_update = datetime.now() - self.last_updated.replace(tzinfo=None)
                if time_since_update < timedelta(hours=24):  # Check every 24 hours
                    return False
            
            # Try to fetch remote configuration
            remote_url = "https://raw.githubusercontent.com/kfir-wit/PurpleCrayon/main/purplecrayon/config/models.json"
            response = requests.get(remote_url, timeout=10)
            response.raise_for_status()
            
            remote_config = response.json()
            remote_version = remote_config.get("version", "1.0.0")
            
            # Check if remote version is newer
            if remote_version != self.config_version:
                print(f"🔄 Found newer model configuration: {remote_version}")
                
                # Backup current config
                backup_path = self.config_path.with_suffix('.json.backup')
                if self.config_path.exists():
                    self.config_path.rename(backup_path)
                
                # Save remote config
                with open(self.config_path, 'w') as f:
                    json.dump(remote_config, f, indent=2)
                
                # Reload configuration
                self._load_config()
                return True
            else:
                print("✅ Model configuration is up to date")
                return False
                
        except Exception as e:
            print(f"⚠️ Could not check for updates: {e}")
            return False
    
    def list_models(self, enabled_only: bool = True) -> List[ModelConfig]:
        """List available models.
        
        Args:
            enabled_only: If True, only return enabled models
            
        Returns:
            List of model configurations
        """
        models = list(self.models.values())
        if enabled_only:
            models = [m for m in models if m.enabled]
        return sorted(models, key=lambda m: m.priority)
    
    def get_model(self, name: str) -> Optional[ModelConfig]:
        """Get a specific model by name.
        
        Args:
            name: Model name
            
        Returns:
            Model configuration or None if not found
        """
        return self.models.get(name)
    
    def get_models_by_provider(self, provider: ModelProvider) -> List[ModelConfig]:
        """Get all models from a specific provider.
        
        Args:
            provider: Model provider
            
        Returns:
            List of model configurations from the provider
        """
        return [m for m in self.models.values() if m.provider == provider and m.enabled]
    
    def get_available_models(self, 
                           model_type: str = "text_to_image",
                           with_models: Optional[List[str]] = None,
                           exclude_models: Optional[List[str]] = None) -> List[ModelConfig]:
        """Get available models based on inclusion/exclusion criteria and model type.
        
        Args:
            model_type: Type of model (text_to_image, image_to_image, image_to_text)
            with_models: Specific models to include (if None, include all)
            exclude_models: Models to exclude
            
        Returns:
            List of available model configurations that support the specified type
        """
        available = []
        
        if with_models:
            # Only include specified models
            for model_name in with_models:
                if model_name in self.models and self.models[model_name].enabled:
                    # Check if model supports the requested type
                    if self.models[model_name].capabilities.get(model_type, False):
                        available.append(self.models[model_name])
        else:
            # Include all enabled models that support the type
            available = [m for m in self.models.values() 
                        if m.enabled and m.capabilities.get(model_type, False)]
        
        # Remove excluded models
        if exclude_models:
            available = [m for m in available if m.name not in exclude_models]
        
        return sorted(available, key=lambda m: m.priority)
    
    def get_models_by_type(self, model_type: str) -> List[ModelConfig]:
        """Get all models that support a specific type.
        
        Args:
            model_type: Type of model (text_to_image, image_to_image, image_to_text)
            
        Returns:
            List of models that support the specified type
        """
        return [m for m in self.models.values() 
                if m.enabled and m.capabilities.get(model_type, False)]
    
    def get_fallback_models(self, 
                          model_type: str = "text_to_image",
                          exclude_models: Optional[List[str]] = None) -> List[ModelConfig]:
        """Get models in fallback order for a specific model type.
        
        Args:
            model_type: Type of model (text_to_image, image_to_image, image_to_text)
            exclude_models: Models to exclude from fallback
            
        Returns:
            List of models in fallback priority order for the specified type
        """
        # Get fallback order for the specific model type
        if hasattr(self, 'fallback_order') and isinstance(self.fallback_order, dict):
            fallback_order = self.fallback_order.get(model_type, [])
        else:
            # Fallback to old format
            fallback_order = self.fallback_order if hasattr(self, 'fallback_order') else []
        
        fallback = []
        for model_name in fallback_order:
            if model_name in self.models and self.models[model_name].enabled:
                # Check if model supports the requested type
                if self.models[model_name].capabilities.get(model_type, False):
                    if not exclude_models or model_name not in exclude_models:
                        fallback.append(self.models[model_name])
        return fallback
    
    def enable_model(self, name: str) -> bool:
        """Enable a model.
        
        Args:
            name: Model name
            
        Returns:
            True if model was enabled, False if not found
        """
        if name in self.models:
            self.models[name].enabled = True
            return True
        return False
    
    def disable_model(self, name: str) -> bool:
        """Disable a model.
        
        Args:
            name: Model name
            
        Returns:
            True if model was disabled, False if not found
        """
        if name in self.models:
            self.models[name].enabled = False
            return True
        return False
    
    def set_fallback_order(self, order: List[str]) -> bool:
        """Set custom fallback order.
        
        Args:
            order: List of model names in priority order
            
        Returns:
            True if order was set successfully, False if invalid models included
        """
        # Validate that all models in order exist
        for model_name in order:
            if model_name not in self.models:
                return False
        
        self.fallback_order = order.copy()
        return True
    
    def get_model_info(self) -> Dict[str, any]:
        """Get comprehensive model information.
        
        Returns:
            Dictionary with model information
        """
        return {
            "total_models": len(self.models),
            "enabled_models": len([m for m in self.models.values() if m.enabled]),
            "providers": list(set(m.provider.value for m in self.models.values())),
            "fallback_order": self.fallback_order,
            "models": {
                name: {
                    "display_name": config.display_name,
                    "provider": config.provider.value,
                    "priority": config.priority,
                    "enabled": config.enabled,
                    "cost_tier": config.cost_tier,
                    "max_resolution": config.max_resolution,
                    "supported_formats": config.supported_formats
                }
                for name, config in self.models.items()
            }
        }


# Global model manager instance
model_manager = ModelManager()
