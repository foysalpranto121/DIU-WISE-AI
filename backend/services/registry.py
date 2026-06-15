class ServiceRegistry:
    """Dependency Injection / Service Locator container for decoupling AI engines and services."""
    _services = {}

    @classmethod
    def register(cls, name: str, service):
        cls._services[name] = service

    @classmethod
    def get(cls, name: str):
        service = cls._services.get(name)
        if service is None:
            raise KeyError(f"Service '{name}' is not registered in the ServiceRegistry.")
        return service

    @classmethod
    def clear(cls):
        cls._services.clear()
