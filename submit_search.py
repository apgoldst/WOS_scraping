# Author: Anna Goldstein
# This script searches Web of Knowledge, using IP authentication
# You must have an IP address from an institution with a WOK subscription


import csv
import os
import wok_soap
import xml.etree.ElementTree as ET


# search for publications by grant number acknowledged
# input is a CSV list of grants, with no header row and grant numbers in column A
def search_by_grant(csv_file, SID):
    directory = "grant search results xml"
    if not os.path.exists(directory): # if the directory doesn't already exist, make one
        os.makedirs(directory)

    with open(csv_file) as h:
        text = csv.reader(h)
        grant_list = [row[0] for row in text] # puts first cell in each row as a grant member in grant_list

    file_list = []
    counter = 0

    for i, cell in enumerate(grant_list): #enumerate pulls out index (i) and content (cell) in the list
       #could be- for cell in grant_list:
        # Define query
        grant_number_full = cell
        if grant_number_full[0:2] == "DE":
            prefix = grant_number_full[3:5]
            grant_number = grant_number_full[5:]
            query = "FT = " + prefix + grant_number + " OR FT = " + prefix + " " + grant_number
            filename = "grant search results xml/" + query + ".txt"
        else:
            query = "FT = " + grant_number_full
            filename = "grant search results xml/" + query.replace("/","") + ".txt"

        file_list.append(filename)

        if not os.path.exists(filename):
            print(query)

            # Search on WOS
            results = wok_soap.search(query, SID)
            [counter, SID] = counter_check(counter, SID)

            queryId = results[0]
            results_count = results[1]

            # Interpret raw search results stored in 4th line of object
            results_unicode = results[3] #actually contains results of search

            if results_count > 100:
                retrieve_count = (results_count // 100)

                if results_count % 100 == 0:
                    retrieve_count -= 1

                for hundred in range(retrieve_count):
                    start_count = (100*hundred) + 101
                    more_results = wok_soap.retrieve(queryId, SID, start_count, "FullRecord")

                    [counter, SID] = counter_check(counter, SID)
                    more_results_unicode = more_results[0].encode('utf-8')
                    results_unicode = results_unicode[:-10] + more_results_unicode[86:]

            root = ET.fromstring(results_unicode) # ET = element tree 
            length = len(root)
            if length != results_count:
                raise # throw error message

            # Write raw search results to txt file
            with open(filename, "w") as f:
                f.write(results_unicode)

    return [grant_list, file_list, counter]


# search for publications by DOI (or WOS if no DOI exists)
# input is a CSV list of publications, with no header row and DOIs in column A
def search_by_DOI(csv_file, SID):
    directory = "DOI search results xml"
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(csv_file) as h:
        text = csv.reader(h)
        doi_list = [row[0] for row in text]

    file_list = []
    counter = 0

    for i, cell in enumerate(doi_list):
       
        #remove non-printing characters
        ID = cell.strip(' \t\n\r').replace(" ","").replace(u'\u200b','')
        print("ID is " + ID)
        
        # Define query 
        if ID[0:3] == "WOS":
            query = "UT = " + ID
        else:
            query = 'DO = "' + ID + '"'
        
        # create filename without slashes or quotes
        filename = "DOI search results xml/" + query.replace("/"," ").replace('"',"") + ".txt"
        file_list.append(filename)

        if not os.path.exists(filename):
            print(query)

            # Search on WOS
            results = wok_soap.search(query, SID)
            [counter, SID] = counter_check(counter, SID)

            # Interpret raw search results stored in 4th line of object
            results_unicode = results[3]

            # Write raw search results to txt file
            with open(filename, "w") as f:
                f.write(results_unicode)

    return [file_list, counter]


def search_for_cited_refs(UID, SID):
    directory = "cited references search results xml"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = "cited references search results xml/" + UID[4:] + ".txt"
    # filename = "cited references testing/" + UID[4:] + ".txt"
    counter = 0

    # Save file of cited refs if it hasn't been saved yet
    if not os.path.exists(filename):
        print(UID + " cited refs")

        # Search on WOS
        results = wok_soap.citedReferences(UID, SID)
        [counter, SID] = counter_check(counter, SID)

        queryId = results[0]
        results_list = results[1]

        root = ET.Element("root")
        tree = ET.ElementTree(root)
        results_count = 0

        if results_list != 0:
            results_count = results[2]

            if results_count > 100:
                retrieve_count = (results_count // 100)

                if results_count % 100 == 0:
                    retrieve_count -= 1

                for hundred in range(retrieve_count):
                    start_count = (100*hundred) + 101
                    more_results = wok_soap.citedReferencesRetrieve(queryId, SID, start_count)

                    [counter, SID] = counter_check(counter, SID)
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


def search_for_citing_articles(UID, SID):
    directory = "citing articles search results xml"
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = "citing articles search results xml/" + UID[4:] + ".txt"
    counter = 0

    # Save file with citing article data if it hasn't been saved yet
    if not os.path.exists(filename):
        print(UID + " citing articles")

        # Search on WOS
        results = wok_soap.citingArticles(UID, SID)
        [counter, SID] = counter_check(counter, SID)

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
                more_results = wok_soap.retrieve(queryId, SID, start_count, "Fields")

                [counter, SID] = counter_check(counter, SID)
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
    if counter >= 2499:
        SID = wok_soap.auth()
        counter = 0

    return [counter, SID]


if __name__ == '__main__':
     
    SID = wok_soap.auth()
    
    csv_file = "example DOIs.csv"
    file_list = search_by_DOI(csv_file, SID)
    print(file_list[0])
    
#    UID = "WOS:000283490400005"
#    
#    search_for_citing_articles(UID, SID)


