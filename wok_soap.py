# Author: Anna Goldstein
# A different version of wok_soap, where authentication and searching are separate functions.
# This allows the same session to remain open and avoid the maximum of 5 new sessions per 5 minutes


from suds.client import Client
from suds.transport.http import HttpTransport
import urllib2


class HTTPSudsPreprocessor(urllib2.BaseHandler):
    def __init__(self, SID):
        self.SID = SID

    def http_request(self, req):
        req.add_header('cookie', 'SID="'+self.SID+'"')
        return req

    https_request = http_request


def auth():
    url = client = {}

    url['auth'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WOKMWSAuthenticate?wsdl'
    client['auth'] = Client(url['auth'])
    SID = client['auth'].service.authenticate()
    return SID

def search(query, SID):
    url = client = {}

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['search'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['search'] = Client(url['search'], transport = http)

    qparams = {
                'databaseId' : 'WOS',
                'userQuery' : query,
                'queryLanguage' : 'en'
            }

    rparams = {
                'count' : 100, # 1-100
                'firstRecord' : 1
            }

    return client['search'].service.search(qparams, rparams)






