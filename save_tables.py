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
    data = [{"DOE Grant Number": grant_list[i],
             "Number of Publications": 0}
            for i in range(len(grant_list))]

    for i, filename in enumerate(file_list):
        with open(filename, "r+") as f:
            tree = ET.parse(f)

        root = tree.getroot()
        data[i]["Number of Publications"] = len(root)
        paper_list = []

        for rec in range(len(root)):
            paper = {"UID": 0,
                     "Article Title": 0,
                     "DOI": 0,
                     "Journal Title": 0,
                     "Publication Date": 0,
                     "Authors": 0,
                     "Abstract": 0,
                     "Keywords": 0,
                     "Number of Pages": 0,
                     "Number of Authors": 0,
                     "Number of References": 0,
                     "Times Cited": 0}

            record = root[rec]
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

            # titles = static_data.find(".//" + ns + "titles")
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

            paper_list.append(paper)

        data[i]["__paper list"] = paper_list

    return data


def print_grant_table(csv_file, ns):

    with open("WOS_scraping - data on DOE grants.csv", "wb") as g:
        writer = csv.writer(g, delimiter=',')
        data = parse_XML(csv_file, ns)

        # Write heading for grant data from dictionary keys, excluding "__paper list"
        example_grant = data[0]
        heading = sorted(example_grant.items(), key=lambda (k, v): k)[:-1]
        fields = [field[0] for field in heading]
        writer.writerow(fields)

        # Fill in values for grant data
        for grant in data:
            dictionary = sorted(grant.items(), key=lambda (k, v): k)[:-1]
            row = [field[1] for field in dictionary]
            writer.writerow(row)


def print_pub_table(csv_file, ns):

    with open("WOS_scraping - papers citing DOE grants.csv", "wb") as g:
        writer = csv.writer(g, delimiter=',')
        data = parse_XML(csv_file, ns)

        # Write heading for paper data
        example_paper = data[1]["__paper list"][0]
        heading = sorted(example_paper.items(), key=lambda (k, v): k)
        fields = [field[0] for field in heading]
        writer.writerow(fields)

        for i in range(len(data)):
            # Fill in values for paper data
            for paper in data[i]["__paper list"]:
                dictionary = sorted(paper.items(), key=lambda (k, v): k)
                row = [field[1] for field in dictionary]
                row.append(data[i]["DOE Grant Number"])
                writer.writerow(row)

