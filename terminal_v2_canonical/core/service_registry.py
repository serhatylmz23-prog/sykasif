class ServiceRegistry:

    def __init__(self):
        self._services={}

    def register(self,name,service):
        self._services[name]=service

    def get(self,name):
        return self._services.get(name)

    def exists(self,name):
        return name in self._services

    def remove(self,name):
        if name in self._services:
            del self._services[name]

    def clear(self):
        self._services.clear()

    def names(self):
        return sorted(self._services.keys())
