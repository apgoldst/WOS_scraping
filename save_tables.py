# Author: Anna Goldstein
# This script pulls data from XML files containing WOS search results

import xml.etree.ElementTree as ET
import csv
import submit_search
import wok_soap
import time
from datetime import datetime as d
import metaknowledge as mk


def process_article(record): 

    ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}" #going to this site does gives a 404 error

    # construct a dictionary to hold publication data
    paper = {"UID": "",
             "Article Title": "",
             "DOI": "",
             "Document Type": "",
             "Journal Title": "",
             "Publication Date": "",
             "Publication Year": "",
             "Authors": "",
             "Abstract": "",
             "Keywords": "",
             "Number of Pages": 0,
             "Number of Authors": 0,
             "Number of References": 0,

             "Times Cited through Search Period": 0,
             "Average Age of Reference": None,
             "Diversity Index": None}

    UID = record[0].text # the first item in "record"
    paper["UID"] = UID

    # Assign variables to segments of the record
    static_data = record[1]
    summary = static_data[0]
    fullrecord_metadata = static_data[1]
    item = static_data[2]
    dynamic_data = record[2]

    pub_info = summary.find(ns + "pub_info")
    date = pub_info.attrib['sortdate']
    paper["Publication Date"] = date

    year = pub_info.attrib['pubyear']
    paper["Publication Year"] = year

    page_count = pub_info.find(ns + "page").attrib['page_count']
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
        doi = doi.attrib['value']
    elif xref_doi is not None:
        doi = xref_doi.attrib['value']
    else:
        doi = "NONE"
    paper["DOI"] = doi

    names = summary.find(ns + "names")
    author_list = []
    author_count = 0
    for name in names:
        if name.attrib['role'] == "author":
            full_name = name.find(ns + "full_name").text
            author_list.append(full_name)
            author_count += 1

    paper["Authors"] = author_list
    paper["Number of Authors"] = author_count

    abstract = fullrecord_metadata.find(".//" + ns + "abstract_text")
    if abstract is not None:
        paper["Abstract"] = abstract[0].text

    keywords_plus = item.find(ns + "keywords_plus")
    keywords = []
    if keywords_plus is not None:
        for keyword in keywords_plus:
            keywords.append(keyword.text)
        paper["Keywords"] = keywords

    refs = fullrecord_metadata.find(ns + "refs")
    ref_count = refs.attrib['count']
    paper["Number of References"] = ref_count

    return paper


def process_cited_refs(cited_refs_record):

    cited_refs_file = cited_refs_record[0]

    with open(cited_refs_file, "rb") as h:

        tree = ET.parse(h)
        root = tree.getroot()
        cited_refs = []

        for entry in root:

            ref = {"Year": entry.find("year").text,
                   "Cited Work": ""}

            if ref["Year"] == "1000":
                ref["Year"] = ""

            citedWork = entry.find("citedWork")

            if citedWork is not None:
                ref["Cited Work"] = citedWork.text.upper()

                if citedWork.text[0:4] == "<IT>":
                    ref["Cited Work"] = citedWork.text.upper()[4:-5]

            cited_refs.append(ref)

    return cited_refs


def process_citing_articles(citing_articles_output):

    citing_articles_file = citing_articles_output[0]
    ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/Fields}"

    with open(citing_articles_file, "rb") as h:

        tree = ET.parse(h)
        root = tree.getroot()
        citing_articles = []

        for record in root:

            paper = {"Publication Date": "",
                     "Publication Year": "",
                     "Journal Title": "",
                     "Article Title": "",
                     "UID": "",
                     "DOI": ""}

            # three top level sections of a record
            UID = record[0]
            static_data = record[1]
            dynamic_data = record[2]
            
            paper["UID"] = UID.text
            
            summary = static_data[0]
            
            # pull date and year from <summary> object
            pub_info = summary.find(ns + "pub_info")
            
            date = pub_info.attrib['sortdate']
            paper["Publication Date"] = date

            year = pub_info.attrib['pubyear']
            paper["Publication Year"] = year
            
            # pull article and journal title from <summary> object
            titles = summary.find(ns + "titles")
            
            article_title = titles.find("*[@type='item']").text
            paper["Article Title"] = article_title

            journal_title = titles.find("*[@type='source']").text
            paper["Journal Title"] = journal_title
            
            #pull DOI from dynamic data section
            doi = dynamic_data.find(".//*[@type='doi']")
            xref_doi = dynamic_data.find(".//*[@type='xref_doi']")
            if doi is not None:
                doi = doi.attrib['value']
            elif xref_doi is not None:
                doi = xref_doi.attrib['value']
            else: 
                doi = "NONE"
            paper["DOI"] = doi

            citing_articles.append(paper)

    return citing_articles


def citation_analysis(paper, SID, counter):
    UID = paper["UID"]

    # search for references cited in the paper
    cited_refs_output = submit_search.search_for_cited_refs(UID, SID)
    counter += cited_refs_output[1]
    if counter >= 2499:
        SID = wok_soap.auth()
        counter = 0

    paper["__cited references"] = process_cited_refs(cited_refs_output)

    if paper["__cited references"]:
        year_list = [int(ref["Year"]) for ref in paper["__cited references"] if ref["Year"] != ""]
        average_year = sum(year_list) / float(len(year_list))
        paper["Average Age of Reference"] = int(paper["Publication Year"]) - average_year

        journal_list = [ref["Cited Work"] for ref in paper["__cited references"]]
        same_journal_list = [y for y in journal_list if y == paper["Journal Title"]]
        paper["Diversity Index"] = 1 - (len(same_journal_list) / float(len(journal_list)))

    # search for articles that cite the paper
    citing_articles_output = submit_search.search_for_citing_articles(UID, SID)
    counter += citing_articles_output[1]

    paper["__citing articles"] = process_citing_articles(citing_articles_output)

    paper["Times Cited through Search Period"] = len(paper["__citing articles"])

    # count citations in calendar years relative to the year of publication, up to year 13 inclusive
    for year in range(-1, 14):
        key = "Citations in Year " + str(year)

        paper[key] = 0
        citations = []
        
        citations = [article["Publication Year"] for article in paper["__citing articles"]
                     if int(article["Publication Year"]) - int(paper["Publication Year"]) == year]

        if citations:
            paper[key] = len(citations)

    # count citations in 12 month periods
    for year in range(4):
        date_format = "%Y-%m-%d"
        key = "Citations in month %s to %s" % (str((year-1)*12), str(year*12))

        paper[key] = 0
        citations_2 = []

        for article in paper["__citing articles"]:
            delta = d.strptime(article["Publication Date"], date_format) - d.strptime(paper["Publication Date"], date_format)
            article["Cite Time"] = delta.days / float(365)
            if year-1 < article["Cite Time"] <= year:
                citations_2.append(article["Publication Date"])

        if citations_2:
            paper[key] = len(citations_2)

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

    # start session
    SID = wok_soap.auth()
    counter = 0

    # run search to output list of grant numbers and list of search results file names
    grants_and_files = submit_search.search_by_grant(csv_file, SID)
    grant_list = grants_and_files[0]
    file_list = grants_and_files[1]

    # start new session before 2500 records have been processed
    counter += grants_and_files[2]
    if counter >= 2499:
        SID = wok_soap.auth()
        counter = 0

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

        writer = csv.writer(g, delimiter=',')

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
        example_grant = []
        for item in data:
            example_grant = item["__paper list"]
            if example_grant:
                break
            
        # Write heading for paper data from dictionary keys
        # excluding "__cited refs" and "__citing articles", which sort to the end
        example_paper = example_grant[0]
        # add a new key for the award number associated with the paper
        example_paper["Award Number"] = ""
        heading_tuples = sorted(list(example_paper.items()), key=lambda k: k[0])[:-2]
        fields = [field[0] for field in heading_tuples]
        writer.writerow(fields)

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:
                paper["Award Number"] = grant["Award Number"]
                dictionary_tuples = sorted(list(paper.items()), key=lambda k: k[0])[:-2]
                row = [field[1] for field in dictionary_tuples]
                writer.writerow(row)
                
                
def print_pub_table_from_DOIs(csv_file):

    # start session
    SID = wok_soap.auth()
    counter = 0

    # run search to output list of search results file names
    search_output = submit_search.search_by_DOI(csv_file, SID)
    file_list = search_output[0]
    counter = search_output[1]
    print("found " + str(len(file_list)) + " files")

    paper_list = []

    # loop through each entry in the list of files found
    for i, filename in enumerate(file_list):
        
        # open search results file and parse as XML
        with open(filename) as h:
            tree = ET.parse(h)
            root = tree.getroot()
        
        # if the file is not empty, process the record
        if root:
            record = root[0]
            paper = process_article(record)
            paper = citation_analysis(paper, SID, counter)
            print("parsed " + filename)
            paper_list.append(paper)
        else:
            print("no paper found")
        
    print("printing publication table")
    with open("WOS_scraping - " + csv_file[:-4] + " - " +
              time.strftime("%d %b %Y") + ".csv", "w") as g:

        writer = csv.writer(g, delimiter=',')
        
        example_paper = paper_list[0]
        heading_tuples = sorted(example_paper.items(), key=lambda k: k[0])[:-2]
        heading = [field[0] for field in heading_tuples]
        writer.writerow(heading)
        
        # Fill in values for paper data
        for paper in paper_list:
            print("writing row for " + paper["DOI"])
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
    
    csv_file = "Publication list for WOS search.csv"

    print_pub_table_from_DOIs(csv_file)

#    print_pub_table(data, csv_file)
#    print_grant_table(data, csv_file)

