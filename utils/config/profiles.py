"""Resource profile settings (RFC 004).

Profiles are operator-declared, not hardware-detected.
"""

from typing import Any


class ResourceProfile:
    """Resource profile settings (RFC 004).

    Profiles are operator-declared, not hardware-detected.
    """

    PROFILES = {
        "embedded": {
            "max_view_entries": 100,
            "max_search_results": 20,
            "fossilization_threshold": 0.80,
            "wal_checkpoint_interval": 300,
            "log_level": "warning",
        },
        "standard": {
            "max_view_entries": 1000,
            "max_search_results": 100,
            "fossilization_threshold": 0.90,
            "wal_checkpoint_interval": 60,
            "log_level": "info",
        },
    }

    @classmethod
    def get_profile(cls, name: str) -> dict[str, Any]:
        """Get resource profile settings.

        Args:
            name: Profile name (embedded or standard)

        Returns:
            Dictionary with profile settings

        Raises:
            ValueError: If profile name is unknown
        """
        if name not in cls.PROFILES:
            raise ValueError(
                f"Unknown resource profile: {name}. "
                f"Available: {list(cls.PROFILES.keys())}"
            )
        return cls.PROFILES[name].copy()
