"""Configuration base module for MemoGarden packages.

This module provides settings following RFC 004 with support for
multiple deployment contexts.

Configuration Resolution Order (RFC 004):
1. Environment variables (MEMOGARDEN_*)
2. Explicit config path (--config flag)
3. Context-based defaults (serve/run/deploy verbs)
4. Built-in defaults
"""

import os
import sys
from pathlib import Path
from typing import Optional, Any

# Python 3.11+ has tomllib in stdlib, otherwise use tomli
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


def load_toml_config(config_path: Path) -> dict[str, Any]:
    """Load configuration from TOML file.

    Args:
        config_path: Path to config.toml file

    Returns:
        Dictionary with configuration sections

    Raises:
        ImportError: If tomli is not available (Python < 3.11)
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid TOML
    """
    if tomllib is None:
        raise ImportError(
            "tomli is required for Python < 3.11. "
            "Install it with: pip install tomli"
        )

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        try:
            return tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Invalid TOML in {config_path}: {e}")


def get_config_path(verb: str = "run", config_override: Optional[Path] = None) -> Path:
    """Get configuration file path based on deployment context (RFC 004).

    Args:
        verb: Deployment verb (serve, run, deploy)
        config_override: Optional explicit config path

    Returns:
        Path to configuration file

    Examples:
        >>> get_config_path("serve")
        Path('/etc/memogarden/config.toml')

        >>> get_config_path("run")
        Path('~/.config/memogarden/config.toml').expanduser()
    """
    if config_override:
        return config_override

    if verb == "serve":
        return Path("/etc/memogarden/config.toml")
    elif verb == "run":
        return Path.home() / ".config/memogarden/config.toml"
    elif verb == "deploy":
        return Path("/config/config.toml")
    else:
        # Default to user config
        return Path.home() / ".config/memogarden/config.toml"


class Settings:
    """System settings with RFC 004 TOML configuration support.

    Database Path Resolution (RFC-004):
    - If database_path is None, path is resolved via get_db_path('core')
    - If database_path is provided, it is used directly (backward compatible)

    Configuration Loading Precedence:
    1. Environment variables (MEMOGARDEN_*)
    2. TOML config file (if exists)
    3. Resource profile defaults
    4. Built-in defaults
    """

    # Built-in defaults (standard profile)
    DEFAULTS = {
        "max_view_entries": 1000,
        "max_search_results": 100,
        "fossilization_threshold": 0.90,
        "wal_checkpoint_interval": 60,
        "log_level": "info",
        "bind_address": "127.0.0.1",
        "bind_port": 8080,
        "encryption": "disabled",
    }

    def __init__(
        self,
        database_path: Optional[str] = None,
        default_currency: str = "SGD",
        config_path: Optional[Path] = None,
        verb: str = "run",
    ):
        """Initialize settings.

        Args:
            database_path: Path to Core database file. If None, resolved
                via get_db_path('core') using environment variables.
            default_currency: Default currency code (e.g., "SGD", "USD")
            config_path: Optional explicit path to config.toml
            verb: Deployment verb (serve, run, deploy) for config resolution
        """
        self.database_path = database_path
        self.default_currency = default_currency

        # Initialize all defaults first
        for key, value in self.DEFAULTS.items():
            setattr(self, key, value)

        # Set default resource profile
        self._resource_profile = "standard"

        # Load TOML config if available
        self._config: dict[str, Any] = {}
        self._verb = verb

        if config_path is None:
            config_path = get_config_path(verb)

        # Load TOML first (will be overridden by env vars later)
        if config_path.exists():
            try:
                self._config = load_toml_config(config_path)
                self._apply_toml_config()
            except (ImportError, ValueError) as e:
                # Log warning but continue with defaults
                import warnings
                warnings.warn(f"Failed to load config from {config_path}: {e}")

        # Apply environment variables (highest precedence)
        self._apply_env_vars()

    def _apply_toml_config(self):
        """Apply TOML configuration to settings.

        Applies settings in order:
        1. Resource profile defaults
        2. Runtime overrides
        3. Network settings
        4. Security settings
        5. Path overrides
        """
        from .profiles import ResourceProfile

        # Get resource profile
        runtime_config = self._config.get("runtime", {})
        resource_profile = runtime_config.get("resource_profile", "standard")
        self._resource_profile = resource_profile
        profile_settings = ResourceProfile.get_profile(resource_profile)

        # Apply profile settings (can be overridden by explicit values)
        for key, value in profile_settings.items():
            setattr(self, key, value)

        # Apply runtime overrides
        for key, value in runtime_config.items():
            if key != "resource_profile":
                setattr(self, key, value)

        # Apply network settings
        network_config = self._config.get("network", {})
        if "bind_address" in network_config:
            self.bind_address = network_config["bind_address"]
        if "bind_port" in network_config:
            self.bind_port = network_config["bind_port"]

        # Apply security settings
        security_config = self._config.get("security", {})
        if "encryption" in security_config:
            self.encryption = security_config["encryption"]

        # Apply path overrides (optional)
        paths_config = self._config.get("paths", {})
        if paths_config.get("data_dir"):
            self.data_dir = Path(paths_config["data_dir"])
        if paths_config.get("config_dir"):
            self.config_dir = Path(paths_config["config_dir"])
        if paths_config.get("log_dir"):
            self.log_dir = Path(paths_config["log_dir"])

    def _apply_env_vars(self):
        """Apply environment variables to settings.

        Environment variables take highest precedence.
        """
        # Runtime settings from env
        if "MEMOGARDEN_RESOURCE_PROFILE" in os.environ:
            profile = os.environ["MEMOGARDEN_RESOURCE_PROFILE"]
            self._resource_profile = profile
            from .profiles import ResourceProfile
            profile_settings = ResourceProfile.get_profile(profile)
            for key, value in profile_settings.items():
                setattr(self, key, value)

        if "MEMOGARDEN_MAX_VIEW_ENTRIES" in os.environ:
            self.max_view_entries = int(os.environ["MEMOGARDEN_MAX_VIEW_ENTRIES"])

        if "MEMOGARDEN_MAX_SEARCH_RESULTS" in os.environ:
            self.max_search_results = int(os.environ["MEMOGARDEN_MAX_SEARCH_RESULTS"])

        if "MEMOGARDEN_FOSSILIZATION_THRESHOLD" in os.environ:
            self.fossilization_threshold = float(os.environ["MEMOGARDEN_FOSSILIZATION_THRESHOLD"])

        if "MEMOGARDEN_WAL_CHECKPOINT_INTERVAL" in os.environ:
            self.wal_checkpoint_interval = int(os.environ["MEMOGARDEN_WAL_CHECKPOINT_INTERVAL"])

        if "MEMOGARDEN_LOG_LEVEL" in os.environ:
            self.log_level = os.environ["MEMOGARDEN_LOG_LEVEL"]

        # Network settings from env
        if "MEMOGARDEN_BIND_ADDRESS" in os.environ:
            self.bind_address = os.environ["MEMOGARDEN_BIND_ADDRESS"]

        if "MEMOGARDEN_BIND_PORT" in os.environ:
            self.bind_port = int(os.environ["MEMOGARDEN_BIND_PORT"])

        # Security settings from env
        if "MEMOGARDEN_ENCRYPTION" in os.environ:
            self.encryption = os.environ["MEMOGARDEN_ENCRYPTION"]

        # Path settings from env
        if "MEMOGARDEN_DATA_DIR" in os.environ:
            self.data_dir = Path(os.environ["MEMOGARDEN_DATA_DIR"])

        if "MEMOGARDEN_CONFIG_DIR" in os.environ:
            self.config_dir = Path(os.environ["MEMOGARDEN_CONFIG_DIR"])

        if "MEMOGARDEN_LOG_DIR" in os.environ:
            self.log_dir = Path(os.environ["MEMOGARDEN_LOG_DIR"])

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)
