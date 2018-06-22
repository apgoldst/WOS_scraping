# Author: Anna Goldstein
# This script pulls data from XML files containing WOS search results

import xml.etree.ElementTree as ET
import csv
import submit_search
import wok_soap
import time
#from datetime import datetime as d
#import metaknowledge as mk



# Constructs and returns a dictionary to hold publication data, given a record
# Currently attempting to combine process_article and process_citing_articles
def process_article(record):
    ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"
    # construct a dictionary to hold publication data
    paper = {"UID": "",
             "Article Title": "",
             "DOI": "",
             "Document Type": "",
             "Journal Title": "",
             "Publication Date": "",
             "Publication Year": "",
             "Authors": "",
             "Keywords": "",

             # could get rid of next 3 (not used)
             "Number of Pages": 0,
             "Number of Authors": 0,
             "Number of References": 0,

             # could be added to dict later
             "Times Cited through Search Period": 0,

             # could get rid of these
             "Average Age of Reference": None,
             "Diversity Index": None}

    UID = record[0].text # the first item in "record"
    paper["UID"] = UID

    # print("process_article UID = " + str(UID))


    # Establish static_data, summary, fullrecord_metadata, item, and dynamic_data,
    # from which we will assign various segments of the record to keys in the dictionary

    static_data = record[1] # WTF WENT WRONG?!
    summary = static_data[0]
    dynamic_data = record[2]


    # Handle if static_data[1] (fullrecord_metadata) is None
    if static_data[1] != None:
        print("yay")
        # do all the stuff that requires fullrecord_metadata
        fullrecord_metadata = static_data[1]

        # Get abstract
        abstract = fullrecord_metadata.find(".//" + ns + "abstract_text")
        if abstract is not None:
            paper["Abstract"] = abstract[0].text

        # Get number of references
        refs = fullrecord_metadata.find(ns + "refs")
        ref_count = refs.attrib['count']
        paper["Number of References"] = ref_count

    # Handle if static_data[2] ()
    if static_data[2] != None:
        item = static_data[2]
        keywords_plus = item.find(ns + "keywords_plus")
        keywords = []
        if keywords_plus is not None:
            for keyword in keywords_plus:
                keywords.append(keyword.text)
        paper["Keywords"] = keywords

    # copied from previous version from github from process_citing_articles
    UID = record[0]
    static_data = record[1]
    dynamic_data = record[2]

    pub_info = summary.find(ns + "pub_info") # can be gotten with WOS.month in metaknowledge
    date = pub_info.attrib['sortdate']
    paper["Publication Date"] = date

    year = pub_info.attrib['pubyear'] # metaknowledge: WOS.year(val)
    paper["Publication Year"] = year

    page_count = pub_info.find(ns + "page").attrib['page_count'] # can use WOS.endingPage and WOS.beginningPage
    paper["Number of Pages"] = page_count

    titles = summary.find(ns + "titles")
    article_title = titles.find("*[@type='item']").text
    paper["Article Title"] = article_title

    doctypes = summary.find(ns + "doctypes")
    doctype = doctypes[0].text
    paper["Document Type"] = doctype

    journal_title = titles.find("*[@type='source']").text
    paper["Journal Title"] = journal_title



    doi = dynamic_data.find(".//*[@type='doi']")
    xref_doi = dynamic_data.find(".//*[@type='xref_doi']")
    if doi is not None:
        doi = doi.attrib['value'] # doi.attrib is a dictionary, a field of the Element interface
    elif xref_doi is not None: # ln 72 assigns the doi to "value" key in the .attrib dictionary
        doi = xref_doi.attrib['value']
    else:
        doi = "NONE"
    paper["DOI"] = doi

    names = summary.find(ns + "names") # .find() returns a list of Element objects/interfaces
    author_list = []
    author_count = 0
    for name in names:
        if name.attrib['role'] == "author":
            full_name = name.find(ns + "full_name").text # look for the author's full name
            author_list.append(full_name) # add the full name to the list
            author_count += 1

    paper["Authors"] = author_list
    paper["Number of Authors"] = author_count

    return paper


# process forward references- more complicated than previous function because
    #WOS collects more data from forward references
def process_citing_articles(citing_articles_output):

    citing_articles_file = citing_articles_output[0] # is a filename

    # Parse citing_articles_file
    with open(citing_articles_file, "rb") as h:
        tree = ET.parse(h)
        root = tree.getroot()

    citing_articles = []

    # call process_article here?? process_article looks for a lot more dict keys
    for record in root:
            UID = record[0]
            print("The UID is: " + UID.text)

            #static_data = record[1]
            #print("The static_data is: " + str(static_data[1].text))

            paper = process_article(record)

            citing_articles.append(paper)

    return citing_articles


# process backward references
def process_cited_refs(cited_refs_record):

    cited_refs_file = cited_refs_record[0] # first element cited_refs_record

    with open(cited_refs_file, "rb") as h: # "rb" opens file and returns file object in binary mode

        tree = ET.parse(h) # parse h, the file object
        root = tree.getroot() # root contains all of the cited references?
        cited_refs = []

        for entry in root:

            ref = {"Year": entry.find("year").text,
                   "Cited Work": ""} # constructs dictionary called ref

            if ref["Year"] == "1000": # to deal with issue of no date being returned as year 1000
                ref["Year"] = ""

            citedWork = entry.find("citedWork") # finds the work cited in the entry

            if citedWork is not None:
                ref["Cited Work"] = citedWork.text.upper() #all caps

                if citedWork.text[0:4] == "<IT>": # look for <IT> tag
                    ref["Cited Work"] = citedWork.text.upper()[4:-5] # remove <IT> tag in front and back

            cited_refs.append(ref)

    return cited_refs


def citation_analysis(paper, SID, counter): # should also refine search period
    UID = paper["UID"]

    print("UID = "+ str(UID))

    # search for references cited in the paper
    cited_refs_output = submit_search.search_for_cited_refs(UID, SID, counter)
    #print(cited_refs_output[1])
    #print("counter = " + str(counter))
    counter = cited_refs_output[1]

    paper["__cited references"] = process_cited_refs(cited_refs_output) # add key, value pair to paper dict

    if paper["__cited references"]: #!!!
        year_list = [int(ref["Year"]) for ref in paper["__cited references"] if ref["Year"] != ""]
        average_year = sum(year_list) / float(len(year_list))
        paper["Average Age of Reference"] = int(paper["Publication Year"]) - average_year

        journal_list = [ref["Cited Work"] for ref in paper["__cited references"]]
        same_journal_list = [y for y in journal_list if y == paper["Journal Title"]]
        paper["Diversity Index"] = 1 - (len(same_journal_list) / float(len(journal_list)))

    # search for articles that cite the paper
    citing_articles_output = submit_search.search_for_citing_articles(UID, SID, counter)
    counter = citing_articles_output[1]

    paper["__citing articles"] = process_citing_articles(citing_articles_output)

    paper["Times Cited through " + str(wok_soap.endDate)] = len(paper["__citing articles"]) # gets # of papers in __citing articles key

    '''
    # count citations in calendar years relative to the year of publication, up to year 13 inclusive
    for year in range(-1, 14):
        key = "Citations in Year " + str(year)

        paper[key] = 0

        citations = [] # list of articles

        citations = [entry["Publication Year"] for entry in paper["__citing articles"]
                     if int(entry["Publication Year"]) - int(paper["Publication Year"]) == year]

        if citations:
            paper[key] = len(citations)

    # count citations in 12 month periods
    # not as useful
    for year in range(4):
        date_format = "%Y-%m-%d"
        key = "Citations in month %s to %s" % (str((year-1)*12), str(year*12))

        paper[key] = 0
        citations_2 = []

        for article in paper["__citing articles"]: # strptime() converts to date_format
            delta = d.strptime(article["Publication Date"], date_format) - d.strptime(paper["Publication Date"], date_format)
            article["Cite Time"] = delta.days / float(365)
            if year-1 < article["Cite Time"] <= year:
                citations_2.append(article["Publication Date"])

        if citations_2:
            paper[key] = len(citations_2)
    '''

    # count citations in calendar years 2003-2017 inclusive
    for year in range(2003, 2018):
        key = "Citations in %s" % (str(year))

        paper[key] = 0
        citations_3 = []

        for article in paper["__citing articles"]:
            if int(article["Publication Year"]) == year:
                citations_3.append(article["Publication Year"])

        if citations_3:
            paper[key] = len(citations_3)

    return paper


def construct_data(csv_file):


    # run search to output list of grant numbers and list of search results file names
    grants_and_files = submit_search.searchByGrantOrDOI(csv_file, "grant", SID)
    grant_list = grants_and_files[0]
    file_list = grants_and_files[1]

    # construct dictionary to hold grant data
    data = [{"Award Number": grant_list[i],
             "Number of Publications": 0}
            for i in range(len(grant_list))]

    for i, filename in enumerate(file_list):

        # open search results file and parse as XML
        with open(filename, "rb") as h:
            tree = ET.parse(h)
            root = tree.getroot()
            print("parsing " + filename)

        data[i]["Number of Publications"] = len(root)
        paper_list = []

        for rec in range(len(root)):

            record = root[rec]
            paper = process_article(record)

            paper = citation_analysis(paper, SID, counter)
            paper_list.append(paper)

        data[i]["__paper list"] = paper_list

    return data


def print_grant_table(data, csv_file):

    print("printing grant table")
    with open("WOS_scraping - grant data - " + csv_file[:-4] + " - " +
              time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',') # create writer object which converts csv to delimited strings

        # Write heading for grant data from dictionary keys, excluding "__paper list"
        example_grant = data[0]
        heading_tuples = sorted(list(example_grant.items()), key=lambda k: k[0])[:-1]
        fields = [field[0] for field in heading_tuples]
        writer.writerow(fields)

        # Fill in values for grant data
        for grant in data:

            dictionary_tuples = sorted(list(grant.items()), key=lambda k: k[0])[:-1]
            row = [field[1] for field in dictionary_tuples]
            writer.writerow(row)


def print_pub_table(data, csv_file):

    print("printing publication table")
    with open("WOS_scraping - paper data - " + csv_file[:-4] + " - " +
              time.strftime("%d %b %Y") + ".csv", "w") as g:

        writer = csv.writer(g, delimiter=',')

       # select one example grant
        example_grant = [] #

        for item in data:
            example_grant = item["__paper list"] # example_grant = list of papers
            if example_grant: # check if example_grant is not empty
                break

        # Write heading for paper data from dictionary keys
        # excluding "__cited refs" and "__citing articles", which sort to the end
        example_paper = example_grant[0] # sets example_paper = to first paper in __paper list
        # add a new key for the award number associated with the paper
        example_paper["Award Number"] = ""
        heading_tuples = sorted(list(example_paper.items()), key=lambda k: k[0])[:-2]
        fields = [field[0] for field in heading_tuples] # whaaaaa
        writer.writerow(fields)

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:
                paper["Award Number"] = grant["Award Number"]
                dictionary_tuples = sorted(list(paper.items()), key=lambda k: k[0])[:-2]
                row = [field[1] for field in dictionary_tuples]
                writer.writerow(row)


def print_pub_table_from_DOIs(csv_file):

    # run search to output list of search results file names
    search_output = submit_search.searchByGrantOrDOI(csv_file, "doi", SID)
    file_list = search_output[1]
    counter = search_output[2]
    print("found " + str(len(file_list)) + " files")


    paper_list = []
    iterations=0
    # loop through each entry in the list of files found

    for filename in file_list:

        print(filename)

        # open search results file and parse as XML
        with open(filename) as h:
            tree = ET.parse(h)
            root = tree.getroot()

        if root: # if the root is not Null
            iterations += 1
            print(iterations)
            record = root[0]

            paper = process_article(record) # process_article is defined above
            print(paper["Article Title"])

            paper = citation_analysis(paper, SID, counter)
            # print("parsed " + filename)
            paper_list.append(paper)

        else:
            print("no paper found")

    '''
    for paper in paper_list:
        print("blah")
        print(paper["Article Title"])
    '''

    # print("printing publication table")

    with open("WOS_scraping - " + csv_file[:-4] + " - " +
              time.strftime("%d %b %Y") + ".csv", "w") as g:

        writer = csv.writer(g, delimiter=',')

        # Use example paper to establish heading tuples for the csv file

        example_paper = paper_list[0]
        heading_tuples = sorted(example_paper.items(), key=lambda k: k[0])[:-2] # lambda creates in-line function
        heading = [field[0] for field in heading_tuples]
        writer.writerow(heading)

        # Fill in values for paper data
        for paper in paper_list:

            # print("writing row for " + paper["Article Title"])
            dictionary_tuples = sorted(paper.items(), key=lambda k: k[0])[:-2]
            row = [field[1] for field in dictionary_tuples]
            writer.writerow(row)


def print_cited_refs_table(data):

    print("printing cited references table")
    with open("WOS_scraping - cited refs in papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        writer.writerow(["Citing Article UID", "Year", "Cited Work"])

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:

                for ref in paper["__cited references"]:
                    ref["Citing Article UID"] = paper["UID"]
                    row = [ref["Citing Article UID"], ref["Year"], ref["Cited Work"].encode('utf-8')]
                    writer.writerow(row)


def print_citing_articles_table(data):

    print("printing citing articles table")
    with open("WOS_scraping - papers citing papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        writer.writerow(["Cited Article UID", "Publication Date", "Publication Year", "Journal Title", "Article Title", "Time of Citation"])

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:

                for cit in paper["__citing articles"]:
                    cit["Citing Article UID"] = paper["UID"]
                    row = [cit["Citing Article UID"], cit["Publication Date"], cit["Publication Year"],
                           cit["Journal Title"], cit["Article Title"], cit["Cite Time"]]
                    writer.writerow(row)



if __name__ == '__main__':

    csv_file = "example dois.csv" # contains two DOIs, so should have two papers
    # data = construct_data(csv_file)

    print_pub_table_from_DOIs(csv_file)

    # data = construct_data(csv_file)
    # print_pub_table(data, csv_file)

