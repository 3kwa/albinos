"""
Simple DotCloud Environment loader
"""

import json

import yaml


class Redis:
    """ common development parameters for Redis server """
    host = u'localhost'
    port = 6379
    password = None

class Mongodb:
    """ common development parameters for MongoDB server """
    host = u'localhost'
    port = 22017
    login = None
    password = None
    url = None


class Environment(object):

    dotcloud_yaml = 'dotcloud.yml'
    dotcloud_json = '/home/dotcloud/environment.json'

    def __init__(self):
        self.dotcloud = {}
        self._load()

    def _load(self):
        try:
            with open(self.dotcloud_json) as f:
                self._json(f)
        except IOError:
            with open(self.dotcloud_yaml) as f:
                self._yaml(f)

    def _yaml(self, file_):
        """
        >>> import StringIO
        >>> f = StringIO.StringIO(yaml.dump({'cache': {'type': 'redis'}}))
        >>> env = Environment()
        >>> env._yaml(f)
        >>> env.cache.host
        u'localhost'
        """
        for service_name, service_property in yaml.load(file_).items():
            service_type = service_property['type']
            try:
                self.dotcloud[service_name] = globals()[service_type.capitalize()]()
            except KeyError:
                # unknown service_type
                pass

    def _json(self, file_):
        """
        >>> import StringIO
        >>> f = StringIO.StringIO(
        ...     json.dumps({'DOTCLOUD_CACHE_REDIS_HOST': 'dotcloud',
        ...                 'DOTCLOUD_CACHE_REDIS_PORT': 1234,
        ...                 'DOTCLOUD_CACHE_REDIS_PASSWORD': 'secret',
        ...                 'DOTCLOUD_MONGO_MONGODB_PASSWORD': 'secret',
        ...                 'DOTCLOUD_WWW_HTTP_URL': 'url'}))
        >>> env = Environment()
        >>> env._json(f)
        >>> env.cache.host
        u'dotcloud'
        >>> env.cache.port
        1234
        >>> env.cache.password
        u'secret'
        """
        environment_json = json.load(file_)
        services  = {}
        for key,service_value in environment_json.items():
            ignore, service_name, service_type, service_var = key.lower().split('_')
            # dynamically instantiating a class based on service_type
            try:
                self.dotcloud[service_name] = globals()[service_type.capitalize()]()
            except KeyError:
                # no service class for service_type
                break
            man = services.setdefault(service_name, {})
            man[service_var] = service_value

        for service_name, service_property in services.items():
            service = self.dotcloud[service_name]
            for service_var, service_value in service_property.items():
                setattr(service, service_var, service_value)

    def __getattr__(self, name):
        return self.dotcloud[name]
