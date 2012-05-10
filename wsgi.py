import json

import requests
import bs4
import cherrypy

def text_for_class(tag, css):
    """ BeautifulSoup helper returns the text of first element of class css in tag """

    try:
        return tag.select(".%s" % css)[0].text
    except IndexError:
        return None

def query(lastname, location, initial=None):
    """ returns the list of matches from the WhitePages for lastname and location

    initial is optional and if set should be the first letter of the firstname

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
    response = requests.get(URL, params=payload)
    soup = bs4.BeautifulSoup(response.text)
    blocks = soup.find_all('div', 'block')
    result = []
    for block in blocks:
        result.append({
            'street_line': text_for_class(block, 'street_line'),
            'locality': text_for_class(block, 'locality'),
            'state': text_for_class(block, 'state'),
            'postcode': text_for_class(block, 'postcode'),
            'phone_number': text_for_class(block, 'phone_number')
            })
    return result

class Albinos:

    @cherrypy.expose
    def index(self):
        url = cherrypy.url()
        json_ = json.dumps( query('Johnson', 'Bondi NSW' , 'M'),
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
        return query(lastname, location, initial)

application  = cherrypy.tree.mount(Albinos())

if __name__ == '__main__':
    cherrypy.quickstart(application)
