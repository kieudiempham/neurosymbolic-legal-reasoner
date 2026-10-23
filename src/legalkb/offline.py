"""Cache-only execution: refuse missing measurements before creating network clients."""
import os
from types import SimpleNamespace


class CacheMiss(RuntimeError):
    pass


def enabled():
    return os.environ.get('LEGALKB_OFFLINE', '0') == '1'


def require_online(operation):
    if enabled():
        raise CacheMiss(f'Offline cache miss: {operation}; no API request was made')


class OfflineClient:
    def __getattr__(self, name):
        raise CacheMiss(f'Offline client: {name}; no API request was made')


def extractor(model):
    if enabled():
        return SimpleNamespace(client=OfflineClient(), model=model)
    from .extract import Extractor
    return Extractor(model)
