import threading


class Singleton(object):
    _instance = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Create a new instance"""
        if not cls._instance:
            with cls._lock:
                cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the instance"""
        if self._initialized is False:
            self._initialized = True
