"""AGS-side CCOS client — never imports CCOS kernel internals beyond the adapter."""
from .client import CCOSClient
__all__ = ["CCOSClient"]
