# Author: Anna Goldstein
# A different version of wok_soap, where authentication and searching are separate functions.
# This allows the same session to remain open and avoid the maximum of 5 new sessions per 5 minutes


from suds.client import Client
from suds.transport.http import HttpTransport
import urllib2
import time


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
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['search'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['search'] = Client(url['search'], transport=http)

    qparams = {'databaseId': 'WOS',
               'userQuery': query,
               'queryLanguage': 'en'}

    rparams = {'count': 100,
               'firstRecord': 1}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['search'].service.search(qparams, rparams)


def retrieveById(UID, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['retrieveById'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['retrieveById'] = Client(url['retrieveById'], transport=http)

    databaseId = "WOS"
    uid = UID
    queryLanguage = "en"

    rparams = {'count': 1,
               'firstRecord': 1}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['retrieveById'].service.retrieveById(databaseId, uid, queryLanguage, rparams)


def citingArticles(UID, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citingArticles'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citingArticles'] = Client(url['citingArticles'], transport=http)

    databaseId = "WOS"
    uid = UID
    queryLanguage = "en"

    rparams = {'count': 1,
               'firstRecord': 1}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['citingArticles'].service.citingArticles(databaseId, uid, queryLanguage, rparams)


def retrieve(queryId, SID, start_count):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['retrieve'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['retrieve'] = Client(url['retrieve'], transport=http)

    rparams = {'count': 100,
               'firstRecord': start_count}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['retrieve'].service.retrieve(queryId, rparams)


def citedReferences(UID, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citedReferences'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citedReferences'] = Client(url['citedReferences'], transport=http)

    databaseId = "WOS"
    uid = UID
    queryLanguage = "en"

    rparams = {'count': 100,
               'firstRecord': 1}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['citedReferences'].service.citedReferences(databaseId, uid, queryLanguage, rparams)


def citedReferencesRetrieve(queryId, SID, start_count):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib2.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citedReferencesRetrieve'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citedReferencesRetrieve'] = Client(url['citedReferencesRetrieve'], transport=http)

    rparams = {'count': 100,
               'firstRecord': start_count}

    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    time.sleep(wait_time)

    return client['citedReferencesRetrieve'].service.citedReferencesRetrieve(queryId, rparams)


if __name__ == '__main__':
    query = "FT = SC0004993 OR FT = SC 0004993"
    SID = auth()
    search_results = search(query, SID)
    queryId = search_results[0]
    start_count = 101
    retrieve_results = retrieve(queryId, SID, start_count)

