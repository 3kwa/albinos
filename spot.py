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
    environment_json = '/home/dotcloud/environment.json'

    def __init__(self):
        self.dotcloud = {}
        self._load()

    def _load(self):
        try:
            with open(self.environment_json) as f:
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
        ...                 'DOTCLOUD_CACHE_REDIS_PASSWORD': 'secret' }))
        >>> env = Environment()
        >>> env._json(f)
        >>> env.cache.host
        u'dotcloud'
        >>> env.cache.port
        1234
        >>> env.cache.password
        u'secret'
        >>> f = StringIO.StringIO('{ "DOTCLOUD_WWW_HTTP_URL": "http://albinos-3kwa.dotcloud.com/", "DOTCLOUD_CACHE_REDIS_URL": "redis://root:kXM98OBWall4hRKFquGO@albinos-3kwa.dotcloud.com:28088", "DOTCLOUD_WWW_SSH_PORT": "28073", "DOTCLOUD_CACHE_SSH_URL": "ssh://redis@albinos-3kwa.dotcloud.com:28086", "DOTCLOUD_WWW_SSH_URL": "ssh://dotcloud@albinos-3kwa.dotcloud.com:28073", "DOTCLOUD_MONGO_SSH_HOST": "albinos-3kwa-mongo-0.dotcloud.com", "DOTCLOUD_WWW_SSH_HOST": "albinos-3kwa.dotcloud.com", "DOTCLOUD_CACHE_SSH_HOST": "albinos-3kwa.dotcloud.com", "DOTCLOUD_PROJECT": "albinos", "DOTCLOUD_SERVICE_NAME": "www", "DOTCLOUD_MONGO_SSH_PORT": "28161", "DOTCLOUD_CACHE_REDIS_PORT": "28088", "PORT_SSH": 22, "DOTCLOUD_WWW_HTTP_HOST": "albinos-3kwa.dotcloud.com", "PORT_HTTP": 80, "DOTCLOUD_ENVIRONMENT": "default", "DOTCLOUD_MONGO_MONGODB_PORT": "28162", "DOTCLOUD_MONGO_SSH_URL": "ssh://mongodb@albinos-3kwa-mongo-0.dotcloud.com:28161", "DOTCLOUD_CACHE_REDIS_HOST": "albinos-3kwa.dotcloud.com", "DOTCLOUD_MONGO_MONGODB_PASSWORD": "sCBUnzSxW0ej7D7kxZeD", "DOTCLOUD_MONGO_MONGODB_LOGIN": "root", "DOTCLOUD_MONGO_MONGODB_URL": "mongodb://root:sCBUnzSxW0ej7D7kxZeD@albinos-3kwa-mongo-0.dotcloud.com:28162", "DOTCLOUD_CACHE_REDIS_LOGIN": "root", "DOTCLOUD_CACHE_REDIS_PASSWORD": "kXM98OBWall4hRKFquGO", "DOTCLOUD_SERVICE_ID": "0", "DOTCLOUD_MONGO_MONGODB_HOST": "albinos-3kwa-mongo-0.dotcloud.com", "DOTCLOUD_CACHE_SSH_PORT": "28086" }')
        >>> env._json(f)
        >>> env.mongo.url
        u'mongodb://root:sCBUnzSxW0ej7D7kxZeD@albinos-3kwa-mongo-0.dotcloud.com:28162'
        """
        environment_json = json.load(file_)
        services  = {}
        for key,service_value in environment_json.items():
            try:
                ignore, service_name, service_type, service_var = key.lower().split('_')
            except ValueError:
                # key not service related
                continue
            # dynamically instantiating a class based on service_type
            try:
                self.dotcloud[service_name] = globals()[service_type.capitalize()]()
            except KeyError:
                # no service class for service_type
                continue
            man = services.setdefault(service_name, {})
            man[service_var] = service_value

        for service_name, service_property in services.items():
            service = self.dotcloud[service_name]
            for service_var, service_value in service_property.items():
                setattr(service, service_var, service_value)

    def __getattr__(self, name):
        return self.dotcloud[name]
