# Author: Anna Goldstein
# This script pulls data from XML files containing WOS search results

import xml.etree.ElementTree as ET
import csv
import submit_search


def parse_XML(csv_file, ns):
    grants_and_files = submit_search.search_records(csv_file)
    grant_list = grants_and_files[0]
    file_list = grants_and_files[1]

    # data = []
    data = [{"grant number": grant_list[i], "number of papers": 0} for i in range(len(grant_list))]

    for i, filename in enumerate(file_list):
        with open(filename, "r+") as f:
            tree = ET.parse(f)

        root = tree.getroot()
        data[i]["number of papers"] = len(root)
        grant_number = grant_list[i]
        paper_list = []

        for rec in range(len(root)):
            record = root[rec]
            UID = record[0].text
            static_data = record[1]
            dynamic_data = record[2]
            pub_info = static_data.find(".//" + ns + "pub_info")
            titles = static_data.find(".//" + ns + "titles")
            article_title = titles.find("*[@type='item']").text
            journal_title = titles.find("*[@type='source']").text
            doi = dynamic_data.find(".//*[@type='doi']")
            if doi is not None:
                doi = doi.attrib['value']
            else:
                doi = ""

            paper = {"UID": UID,
                     "article title": article_title,
                     "journal title": journal_title,
                     "DOI": doi}
            paper_list.append(paper)

        data[i]["paper list"] = paper_list

    return data


def print_grant_table(csv_file, ns):

    with open("grant table - publications.csv", "wb") as g:
        writer = csv.writer(g, delimiter=',')
        writer.writerow(["DOE Grant Number", "Number of Publications"])
        data = parse_XML(csv_file, ns)

        for row in data:
            writer.writerow([row["grant number"],
                            row["number of papers"]])


def print_pub_table(csv_file, ns):

    with open("publication table.csv", "wb") as g:
        writer = csv.writer(g, delimiter=',')
        writer.writerow(["UID", "Article Title", "Journal Name", "DOI", "DOE Grant Number"])
        data = parse_XML(csv_file, ns)

        for i in range(len(data)):
            for paper in data[i]["paper list"]:
                writer.writerow([paper["UID"],
                                paper["article title"],
                                paper["journal title"],
                                paper["DOI"],
                                data[i]["grant number"]])
