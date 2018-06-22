# Author: Anna Goldstein
# This script searches Web of Knowledge, using IP authentication
# You must have an IP address from an institution with a WOK subscription


import csv
import os
import wok_soap
import xml.etree.ElementTree as ET



def searchByGrantOrDOI(csv_file, searchType):
    directory = "search by grant or doi xml/"
    if not os.path.exists(directory): # Check for and create a directory
        os.makedirs(directory)

    column1List = []

    with open(csv_file) as h: # Open a CSV file
        text = csv.reader(h)
        column1List = [row[0].replace(u'\ufeff','') for row in text] # gets rid of '\ufeff' at beginning of csv

    counter = 0
    SID = ""

    # define queryList, a list of queries
    queryList = []
    file_list = []

    # === Handle second argument, searchType ====
    searchType = searchType.lower() # converts the string to lowercase
    acceptableSearchTypes = ["grant", "doi"] # later can add author, etc
    if searchType not in acceptableSearchTypes: # raise error if grantOrDOI is not a grant or a doi
        raise Exception("Second argument of searchByGrantOrDOI must be 'grant' or 'doi'")


    # CREATE QUERY
    if searchType == "grant": # === Create grant query ===
        for fullNumber in column1List:

            if fullNumber[0:2] == "DE":
                prefix = fullNumber[3:5]
                grantNumber = fullNumber[5:]
                query = "FT = " + prefix + grantNumber + " OR FT = " + prefix + " " + grantNumber
            else:
                query = "FT = " + str(fullNumber)

            queryList.append(query)


    elif searchType == "doi": #=== Create DOI query ===
        for result in column1List:
            print(result)
            ID = result.strip(' \t\n\r').replace(" ","").replace(u'\u200b','') #remove non-printing characters
            print("ID is " + ID)
            if ID[0:3] == "WOS": # Define query
                query = "UT = " + ID
                print("query = " + str(query))
            else:
                query = 'DO = "' + ID + '"'
                print("query = " + str(query))

            queryList.append(query)



    for q in queryList:

        # create filename without slashes or quotes
        filename = directory + q.replace("/"," ").replace('"',"") + ".txt"
        # Add each file to file list

        file_list.append(filename)


        # Search on WOS
        if not os.path.exists(filename):

            [counter, SID] = counter_check(counter, SID)
            results = wok_soap.search(q, SID)

            queryId = results[0]
            results_count = results[1]
            results_unicode = results[3]



            # Handling throttle problems - can't get more than 100 at once
            if results_count > 100:
                retrieve_count = (results_count // 100)

                if results_count % 100 == 0:
                    retrieve_count -= 1

                for hundred in range(retrieve_count):
                    start_count = (100*hundred) + 101

                    [counter, SID] = counter_check(counter, SID)
                    more_results = wok_soap.retrieve(queryId, SID, start_count, "FullRecord")

                    more_results_unicode = more_results[0].encode('utf-8')

                    results_unicode = str(results_unicode[:-10]) + str(more_results_unicode[86:])

                root = ET.fromstring(results_unicode) # ET = element tree. results_unicode is the object that contains all the search results
                length = len(root)

                if length != results_count:
                    raise Exception("length does not equal results_count")# throw error message

            # Write raw search results to txt file
            with open(filename, "w") as f:
                f.write(results_unicode)

    print(file_list)

    return [column1List, file_list, counter] #subscription allows only 2500 records/session.
#returning counter allows us to see if we are reaching limit per session so we can start new session


def search_for_cited_refs(UID, SID, counter): # Searches for all the references cited in one paper given that paper's UID
    directory = "cited references search results xml" #Creates another directory again
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = "cited references search results xml/" + UID[4:] + ".txt"
    # filename = "cited references testing/" + UID[4:] + ".txt"

    # Save file of cited refs if it hasn't been saved yet
    if not os.path.exists(filename):
        print(UID + " cited refs")

        [counter, SID] = counter_check(counter, SID)
        # Search on WOS
        results = wok_soap.citedReferences(UID, SID)

        queryId = results[0]
        results_list = results[1]

        root = ET.Element("root") # creates a root Element object
        tree = ET.ElementTree(root) # creates a tree using the root Element
        results_count = 0

        if results_list != 0:
            results_count = results[2] # number of results is in the third index of results

            if results_count > 100: # all of this is necessary because we can only go through 100 records at a time
                retrieve_count = (results_count // 100)

                if results_count % 100 == 0:
                    retrieve_count -= 1

                for hundred in range(retrieve_count):
                    start_count = (100*hundred) + 101

                    [counter, SID] = counter_check(counter, SID)
                    more_results = wok_soap.citedReferencesRetrieve(queryId, SID, start_count)

                    results_list = results_list + more_results

            # Put search results in XML format
            for item in results_list:
                ref = ET.SubElement(root, "cited_ref")
                ET.SubElement(ref, "year").text = item.year
                if hasattr(item, "citedWork"):
                    ET.SubElement(ref, "citedWork").text = item.citedWork

        length = len(root)
        if length != results_count:
            raise
        tree.write(filename)

    return [filename, counter]




def search_for_citing_articles(UID, SID, counter):
    directory = "citing articles search results xml"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = "citing articles search results xml/" + UID[4:] + ".txt"

    # Save file with citing article data if it hasn't been saved yet
    if not os.path.exists(filename):
        print(UID + " citing articles")

        [counter, SID] = counter_check(counter, SID)
        # Search on WOS
        results = wok_soap.citingArticles(UID, SID)

        queryId = results[0]
        results_count = results[1]

        # Interpret raw search results stored in 5th line of object
        results_unicode = results[4]

        if results_count > 100:
            retrieve_count = (results_count // 100)

            if results_count % 100 == 0:
                retrieve_count -= 1

            for hundred in range(retrieve_count):
                start_count = (100*hundred) + 101

                [counter, SID] = counter_check(counter, SID)
                more_results = wok_soap.retrieve(queryId, SID, start_count, "Fields")

                more_results_unicode = more_results[0]
                results_unicode = results_unicode[:-10] + more_results_unicode[82:]

        root = ET.fromstring(results_unicode)
        length = len(root)
        if length != results_count:
            raise Exception

        # Write raw search results to txt file
        with open(filename, "w") as f:
            f.write(results_unicode)

    return [filename, counter]


def counter_check(counter, SID):
    counter += 1
    if counter >= 2499 or SID == "": # Because can only get 2500 records in a given session
        SID = wok_soap.auth()
        counter = 0

    return [counter, SID]


if __name__ == '__main__':

    SID = wok_soap.auth()

    '''
    csv_file = "example DOIs.csv"
    file_list = search_by_DOI(csv_file, SID)
    print(file_list[0])

    csv_2 = "example grants.csv"
    fileList2 = search_by_grant(csv_2, SID)
    print("example grants and " + str(fileList2[0]))
    '''

    csv_file = "example dois.csv"
    file_list = searchByGrantOrDOI(csv_file, "doi", SID)
    print(file_list[0])

#    UID = "WOS:000283490400005"
#
#    search_for_citing_articles(UID, SID)


