import save_tables
import submit_search
import wok_soap
import xml.etree.ElementTree as ET
import csv
import os
import time



filename = "DOI search results xml/DO = ﻿10.1002 2013WR014607.txt"

with open(filename) as h:
    tree = ET.parse(h)
    root = tree.getroot()

record = root[0]

paper = save_tables.process_article(record) # process_article is defined above
print(paper["Article Title"])



citing_articles_file = "citing articles search results xml/000216886900006.txt"

with open(citing_articles_file, "rb") as h:
        tree = ET.parse(h)
        root = tree.getroot()

record = root[0]

paper = save_tables.process_article(record) # process_article is defined above
print(paper["Article Title"])

#UID = "WOS:000216886900006"

#results = submit_search.search_for_citing_articles(UID, SID)
#
#with open("citing articles full results.txt", "w") as f:
#    f.write(str(results))

#results2 = wok_soap.search("UT = WOS:000216886900006", SID)
#with open("regular search full results.txt", "w") as f:
#    f.write(str(results2))

#results3 = wok_soap.search("FT = AR0000006", SID)
#print(results3)
#
#with open("grant search full results.txt", "w") as f:
#    f.write(str(results3))

#SID = wok_soap.auth()
#print(SID)
#
#csv_file = "example DOIs.csv"
#SID="8BIaALTznDdvcPRBWqF"
#
#save_tables.print_pub_table_from_DOIs(csv_file)




#
#filename = "DOI search results xml/DO = 10.1002 9781118877517.ch7.txt"
#
## open search results file and parse as XML
#with open(filename) as h:
#    tree = ET.parse(h)
#    print(str(tree))
#    root = tree.getroot()
#
#if root:
#    print(root[0])
#
#
#
#record = root[0]
#paper = save_tables.process_article(record)
#paper = save_tables.citation_analysis(paper, SID, counter)
