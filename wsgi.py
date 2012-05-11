import json
import os.path

import requests
import bs4
import cherrypy
from cherrypy.lib.static import serve_file
import redis

from spot import Dotcloud


def text_for_class(tag, css):
    """ BeautifulSoup helper returns the text of first element of class css in tag """

    try:
        return tag.select(".%s" % css)[0].text
    except IndexError:
        return None

class Query(object):

    def __init__(self, cache=None):
        self.cache = cache

    def __call__(self, lastname, location, initial=None):
        """ returns the list of matches from the WhitePages for lastname and location

        initial is optional and if set should be the first letter of the firstname
        >>> query = Query()
        >>> query('Kidd', 'Manly NSW')
        [{'phone_number': u'(02) 9976 6759', 'state': u'NSW', 'postcode': u'2095', 'street_line': u'104 Pittwater Rd', 'locality': u'Manly'}, {'phone_number': u'(02) 9977 0795', 'state': u'NSW', 'postcode': u'2095', 'street_line': u'63 Pittwater Rd', 'locality': u'Manly'}, {'phone_number': u'(02) 9977 2809', 'state': u'NSW', 'postcode': u'2095', 'street_line': u'53 Quinton Rd', 'locality': u'Manly'}]
        >>> query('Kidd', 'Manly NSW', 'E')
        [{'phone_number': u'(02) 9976 6759', 'state': u'NSW', 'postcode': u'2095', 'street_line': u'104 Pittwater Rd', 'locality': u'Manly'}]
        """

        URL = "http://www.whitepages.com.au/resSearch.do"
        payload = {
                'subscriberName': lastname,
                'givenName': initial,
                'location': location
                }
        hash_ = hash(frozenset(payload.items()))

        result = self.cache.get(hash_)
        if result is None:
            result = []
            response = requests.get(URL, params=payload)
            soup = bs4.BeautifulSoup(response.text)
            blocks = soup.find_all('div', 'block')
            for block in blocks:
                result.append({
                    'street_line': text_for_class(block, 'street_line'),
                    'locality': text_for_class(block, 'locality'),
                    'state': text_for_class(block, 'state'),
                    'postcode': text_for_class(block, 'postcode'),
                    'phone_number': text_for_class(block, 'phone_number')
                    })
            self.cache.set(hash_, json.dumps(result))

        return result

class Cache(object):
    """ Redis basic caching for 30 days """

    def __init__(self, redis, days=30):
        self.redis =  redis
        self.days=30

    def set(self, key, value):
        try:
            self.redis.setex(key, self.days * 24 * 60 * 60, json.dumps(value))
        except (AttributeError, redis.ConnectionError):
            pass

    def get(self, key):
        try:
            return json.loads(self.redis.get(key))
        except (TypeError, AttributeError, redis.ConnectionError):
            return None



# spot.Dotcloud environment helper
dotcloud = Dotcloud()
# using redis to cache the resul of whitepages queries
cache = Cache(dotcloud.cache.server)


class Albinos:

    query = Query(cache)

    @cherrypy.expose
    def index(self):
        url = cherrypy.url()
        json_ = json.dumps( self.query('Johnson', 'Bondi NSW' , 'M'),
                            sort_keys=True,
                            indent=4 )
        return """
        <p><strong>Albinos - <a href="http://www.whitepages.com.au">WhitePages</a> API for developers</strong></p>
        <p>Parameters:
        <ul>
        <li>lastname</li>
        <li>location</li>
        <li>(<em>firstname initial</em>)</li>
        </ul>
        </p>
        <pre>curl -d "lastname=Johnson&location=Bondi%20NSW" {url}v1</pre>
        <pre>curl <a href="{url}v1/Johnson/Bondi NSW">{url}v1/Johnson/Bondi%20NSW</a></pre>
        <pre>curl <a href="{url}v1?lastname=Johnson&location=Bondi%20NSW">{url}v1?lastname=Johnson&location=Bondi%20NSW</a></pre>
        <p><a href="http://json.org">JSON</a> response e.g. <a href="{url}v1/Johnson/Bondi NSW/M">Johnson M in Bondi NSW</a>:</p>
        <pre>{json}</pre>
        """.format( url=url, json=json_)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def v1(self, lastname, location, initial=None):
        return self.query(lastname, location, initial)

    cwd = os.path.dirname(os.path.abspath(__file__))

    @cherrypy.expose
    def environment(self):
        return serve_file(Dotcloud.environment_json)

    @cherrypy.expose
    def dotcloud(self):
        return serve_file(os.path.join(self.cwd, 'dotcloud.yml'))


application  = cherrypy.tree.mount(Albinos())

if __name__ == '__main__':
    cherrypy.quickstart(application)
