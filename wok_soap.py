# Author: Anna Goldstein
# A version of wok_soap with separate functions for authentication and searching
# This script allows the same session to remain open and avoids being limited by the maximum of 5 new sessions per 5 minutes


from suds.client import Client
from suds.transport.http import HttpTransport
import urllib.request, urllib.error, urllib.parse
import time


class HTTPSudsPreprocessor(urllib.request.BaseHandler):
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

    #print(SID)
    return SID


# perform search using any query and return a query ID
def search(query, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID)) #build_opener returns an OpenerDirector instance
    http.urlopener = opener
    url['search'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['search'] = Client(url['search'], transport=http)

    qparams = {'databaseId': 'WOS',
               'userQuery': query,
               'queryLanguage': 'en'} # parameters of our query. there are optional parameters such as time etc

    rparams = {'count': 100,
               'firstRecord': 1}

    check_time(start_time)

    return client['search'].service.search(qparams, rparams) # constructs query and returns list ish thing with id as first element, result, etc.


# perform search on one or more database identifiers and return the record(s)
def retrieveById(UID, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID)) #build_opener returns OpenerDirector object
    http.urlopener = opener #hands OpenerDirector object to http
    url['retrieveById'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['retrieveById'] = Client(url['retrieveById'], transport=http)

    databaseId = "WOS" # qparams?!
    uid = UID
    queryLanguage = "en"

    rparams = {'count': 1, # retrieve 1 result instead of 100
               'firstRecord': 1}

    check_time(start_time) #where does this come from?!

    return client['retrieveById'].service.retrieveById(databaseId, uid, queryLanguage, rparams)


# search for citing articles in a given time period
def citingArticles(UID, SID, endDate):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citingArticles'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citingArticles'] = Client(url['citingArticles'], transport=http)

    databaseId = "WOS"
    uid = UID
    queryLanguage = "en"
    editions = None
    timeSpan = {'begin': "1900-01-01",
                'end': endDate} # 2017-12-31

    rparams = {'count': 100,
               'firstRecord': 1,
               'viewField': {'collectionName': 'WOS',
                             'fieldName': ['pub_info', 'titles']}}

    check_time(start_time)

    return client['citingArticles'].service.citingArticles(databaseId, uid, editions, timeSpan, queryLanguage, rparams)


# retrieve records from a previous search
def retrieve(queryId, SID, start_count, namespace):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['retrieve'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['retrieve'] = Client(url['retrieve'], transport=http)

    if namespace == "FullRecord":
        rparams = {'count': 100,
                   'firstRecord': start_count} # eg, whether to start at record 1, 101, 201, to fetch extra records

    else:
        rparams = {'count': 100,
                   'firstRecord': start_count,
                   'viewField': {'collectionName': 'WOS',
                                 'fieldName': ['pub_info', 'titles']}}

    check_time(start_time) # check_time() is defined below

    return client['retrieve'].service.retrieve(queryId, rparams)


# Returns records of all references cited within a paper with a given UID.
def citedReferences(UID, SID):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citedReferences'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citedReferences'] = Client(url['citedReferences'], transport=http)

    databaseId = "WOS"
    uid = UID
    queryLanguage = "en"

    rparams = {'count': 100,
               'firstRecord': 1}

    check_time(start_time)

    return client['citedReferences'].service.citedReferences(databaseId, uid, queryLanguage, rparams)


def citedReferencesRetrieve(queryId, SID, start_count):
    url = client = {}
    start_time = time.time()

    http = HttpTransport()
    opener = urllib.request.build_opener(HTTPSudsPreprocessor(SID))
    http.urlopener = opener
    url['citedReferencesRetrieve'] = 'http://search.webofknowledge.com/esti/wokmws/ws/WokSearch?wsdl'
    client['citedReferencesRetrieve'] = Client(url['citedReferencesRetrieve'], transport=http)

    rparams = {'count': 100,
               'firstRecord': start_count}

    check_time(start_time)

    return client['citedReferencesRetrieve'].service.citedReferencesRetrieve(queryId, rparams)


def check_time(start_time):
    end_time = time.time()
    wait_time = 0.5 - (end_time - start_time)
    if wait_time > 0:
        time.sleep(wait_time)



endDate = "2017-12-31"


if __name__ == '__main__':

#test script with example search

    SID = auth()

    UID = "WOS:000283490400005"
    
    # random dates input by neosha
    #begDate = "2004-07-09"
    
    citing_articles = citingArticles(UID, SID, endDate)

    queryId = citing_articles[0]
    print(citing_articles)

#    with open("citing articles result_2.txt", "wb") as f:
#        f.write(str(citing_articles))
#
#    retrieve = retrieve(queryId, SID, start_count=101)
#
#    with open("retrieve result_2.txt", "wb") as f:
#        f.write(str(retrieve))
#    query = "FT = SC0004993 OR FT = SC 0004993"
