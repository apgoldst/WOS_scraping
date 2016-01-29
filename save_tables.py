# Author: Anna Goldstein
# This script pulls data from XML files containing WOS search results

import xml.etree.ElementTree as ET
import csv
import submit_search
import wok_soap
import time


def process_article(record):

    ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"

    # construct a dictionary to hold publication data
    paper = {"UID": "",
             "Article Title": "",
             "DOI": "",
             "Journal Title": "",
             "Publication Date": "",
             "Publication Year": "",
             "Authors": "",
             "Abstract": "",
             "Keywords": "",
             "Number of Pages": 0,
             "Number of Authors": 0,
             "Number of References": 0,

             "Times Cited through 12-31-2015": 0,
             "Average Age of Reference": None,
             "Diversity Index": None}

    UID = record[0].text
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

    journal_title = titles.find("*[@type='source']").text
    paper["Journal Title"] = journal_title

    doi = dynamic_data.find(".//*[@type='doi']")
    if doi is not None:
        doi = doi.attrib['value']
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

            cited_refs.append(ref)

    return cited_refs


def process_citing_articles(citing_articles_output):

    citing_articles_file = citing_articles_output[0]

    with open(citing_articles_file, "rb") as h:

        tree = ET.parse(h)
        root = tree.getroot()
        citing_articles = []

        for record in root:

            paper = {"Publication Date": "",
                     "Publication Year": "",
                     "Journal Title": "",
                     "Article Title": "",
                     "UID": ""}

            UID = record[0].text
            static_data = record[1]
            summary = static_data[0]

            paper["UID"] = UID

            pub_info = summary.find(ns + "pub_info")
            date = pub_info.attrib['sortdate']
            paper["Publication Date"] = date

            year = pub_info.attrib['pubyear']
            paper["Publication Year"] = year

            titles = summary.find(ns + "titles")
            article_title = titles.find("*[@type='item']").text
            paper["Article Title"] = article_title

            journal_title = titles.find("*[@type='source']").text
            paper["Journal Title"] = journal_title

            citing_articles.append(paper)

    return citing_articles


def parse_XML(csv_file):

    # start session
    SID = wok_soap.auth()
    counter = 0

    # run search to output list of grant numbers and list of search results file names
    grants_and_files = submit_search.search_by_grant(csv_file, SID)
    grant_list = grants_and_files[0]
    file_list = grants_and_files[1]

    # start new session after 2000 records have been processed
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
        with open(filename, "r+") as h:
            tree = ET.parse(h)
            root = tree.getroot()

        data[i]["Number of Publications"] = len(root)
        paper_list = []

        for rec in range(len(root)):

            record = root[rec]
            paper = process_article(record)

            UID = paper["UID"]
            cited_refs_output = submit_search.search_for_cited_refs(UID, SID)
            citing_articles_output = submit_search.search_for_citing_articles(UID, SID)

            counter += cited_refs_output[1]
            counter += citing_articles_output[1]
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

            paper["__citing articles"] = process_citing_articles(citing_articles_output)


            paper["Times Cited through 12-31-2015"] = len(paper["__citing articles"])

            # # under development
            # for year in range(4):
            #     citations = [article["Publication Year"] for article in paper["__citing articles"]
            #                  if int(article["Publication Year"]) == int(paper["Publication Year"])]
            #     paper["Citations in Year " + str(year)] = len(citations)

            paper_list.append(paper)

        data[i]["__paper list"] = paper_list

    return data


def print_grant_table(data):

    with open("WOS_scraping - data on DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        # Write heading for grant data from dictionary keys, excluding "__paper list"
        example_grant = data[0]
        heading_tuples = sorted(example_grant.items(), key=lambda (k, v): k)[:-1]
        fields = [field[0] for field in heading_tuples]
        writer.writerow(fields)

        # Fill in values for grant data
        for grant in data:

            dictionary_tuples = sorted(grant.items(), key=lambda (k, v): k)[:-1]
            row = [field[1] for field in dictionary_tuples]
            writer.writerow(row)


def print_pub_table(data):

    with open("WOS_scraping - papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        # Write heading for paper data from dictionary keys, excluding "__cited refs" and "__citing articles"
        example_grant = []
        for item in data:
            example_grant = item["__paper list"]
            if example_grant:
                break

        example_paper = example_grant[0]
        example_paper["Award Number"] = ""
        heading_tuples = sorted(example_paper.items(), key=lambda (k, v): k)[:-2]
        fields = [field[0] for field in heading_tuples]
        writer.writerow(fields)

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:
                paper["Award Number"] = grant["Award Number"]
                dictionary_tuples = sorted(paper.items(), key=lambda (k, v): k)[:-2]
                row = [field[1] for field in dictionary_tuples]
                writer.writerow(row)


def print_cited_refs_table(data):

    with open("WOS_scraping - cited refs in papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        writer.writerow(["Citing Article UID", "Year", "Cited Work"])

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:

                for ref in paper["__cited references"]:
                    ref["Citing Article UID"] = paper["UID"]
                    row = [ref["Citing Article UID"], ref["Year"], ref["Cited Work"]]
                    writer.writerow(row)


def print_citing_articles_table(data):

    with open("WOS_scraping - articles citing papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')

        writer.writerow(["Cited Article UID", "Year", "Citing Journal"])

        for grant in data:

            # Fill in values for paper data
            for paper in grant["__paper list"]:

                for ref in paper["__cited references"]:
                    ref["Citing Article UID"] = paper["UID"]
                    row = [ref["Citing Article UID"], ref["Year"], ref["Cited Work"]]
                    writer.writerow(row)


csv_file = "DOE grant short list.csv"
ns = "{http://scientific.thomsonreuters.com/schema/wok5.4/public/FullRecord}"

if __name__ == '__main__':
    data = parse_XML(csv_file)
    print_pub_table(data)
    print_grant_table(data)
    print_cited_refs_table(data)
