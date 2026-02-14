"""MemoGarden Utils - Shared utilities across packages.

This package provides common utilities used by both memogarden-system
and memogarden-api.

Import patterns:

    # Import submodule (preferred for clarity):
    from utils import isodatetime, uid, secret, hash_chain, recurrence, time
    from utils.config import Settings, get_config_path, ResourceProfile

    # Then use submodule functions:
    uid.generate()
    isodatetime.now()
    secret.generate_api_key()
"""

# Export submodules for import convenience
from . import config, hash_chain, isodatetime, recurrence, secret, time, uid

__all__ = [
    "config",
    "hash_chain",
    "isodatetime",
    "recurrence",
    "secret",
    "time",
    "uid",
]
