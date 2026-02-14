"""Configuration management for MemoGarden packages.

This module provides settings following RFC 004 with support for
multiple deployment contexts.

Import patterns:
    from utils.config import Settings, get_config_path, ResourceProfile
"""

from .base import Settings, get_config_path, load_toml_config
from .profiles import ResourceProfile

__all__ = ["Settings", "get_config_path", "load_toml_config", "ResourceProfile"]

# Default settings instance
default_settings = Settings()
