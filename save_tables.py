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
    paper = {"UID": 0,
             "Article Title": "",
             "DOI": "",
             "Journal Title": "",
             "Publication Date": "",
             "Authors": "",
             "Abstract": "",
             "Keywords": "",
             "Number of Pages": 0,
             "Number of Authors": 0,
             "Number of References": 0,
             "Times Cited": 0}

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


def parse_XML(csv_file):

    # start session
    SID = wok_soap.auth()

    # run search to output list of grant numbers and list of search results file names
    grants_and_files = submit_search.search_by_grant(csv_file, SID)
    grant_list = grants_and_files[0]
    file_list = grants_and_files[1]

    # start new session after 2000 records have been processed
    counter = grants_and_files[2]
    if counter > 2000:
        SID = wok_soap.auth()

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
            cited_refs_file = cited_refs_output[0]

            counter = cited_refs_output[1]
            if counter > 2000:
                SID = wok_soap.auth()

            with open(cited_refs_file, "rb") as h:

                refs_tree = ET.parse(h)
                refs_root = refs_tree.getroot()
                cited_refs = []

                for entry in refs_root:

                    ref = {"Year": entry.find("year").text, "Cited Work": ""}
                    if ref["Year"] == "1000":
                        ref["Year"] == ""

                    citedWork = entry.find("citedWork")
                    if citedWork is not None:
                        ref["Cited Work"] = citedWork.text
                    cited_refs.append(ref)

            paper["__cited references"] = cited_refs

            paper["__citing articles"] = ""

            paper_list.append(paper)

        data[i]["__paper list"] = paper_list

    return data


def print_grant_table(csv_file):

    with open("WOS_scraping - data on DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')
        data = parse_XML(csv_file)

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


def print_pub_table(csv_file):

    with open("WOS_scraping - papers citing DOE grants - " + time.strftime("%d %b %Y") + ".csv", "wb") as g:

        writer = csv.writer(g, delimiter=',')
        data = parse_XML(csv_file)

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

