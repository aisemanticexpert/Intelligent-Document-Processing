"""API Module"""
try:
    from .server import IDRAPIServer, create_api_server
    __all__ = ["IDRAPIServer", "create_api_server"]
except ImportError:
    __all__ = []
